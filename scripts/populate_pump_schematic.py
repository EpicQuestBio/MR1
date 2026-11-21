# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# SPDX-License-Identifier: CC0-1.0
"""
Populate the hierarchical Pump schematic sheets with the support parts that the
pump controller needs, as UNWIRED symbols, so a human can wire them in Eeschema.

- Symbols are taken from the installed KiCad standard libraries and embedded
  (flattened, including `extends` parents) into each sheet's `lib_symbols`.
- Parts are placed in a band at the bottom of each sheet (sheet is promoted to
  A3 so nothing overlaps existing work). A text note lists each part's role.
- Idempotent: a part is skipped if its reference already exists in the sheet.
- Refuses to run while Eeschema holds a lock on the project (use --force to
  override) because Eeschema would overwrite the changes on its next save.

Usage:
    python scripts/populate_pump_schematic.py [--dry-run] [--out-dir DIR] [--force]
"""

import argparse
import re
import shutil
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUMP = REPO / "Pump"
SYMLIB = Path("/usr/share/kicad/symbols")

# ---------------------------------------------------------------------------
# Part plan. (ref, lib_id, value, footprint or None for library default, role)
# Values marked "verify" need a datasheet check before release.
# ---------------------------------------------------------------------------
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"

PLAN = {
    "Power_PD.kicad_sch": [
        ("U101", "Interface_USB:STUSB4500QTR", "STUSB4500QTR", None, "USB-PD sink controller (replaces placeholder U2)"),
        ("C101", "Device:C", "100nF 50V", C0603, "STUSB4500 VDD (pin 24) decoupling; VDD tied to VBUS"),
        ("C102", "Device:C", "1uF", C0402, "STUSB4500 VREG_1V2 (pin 21) to GND"),
        ("C103", "Device:C", "1uF", C0402, "STUSB4500 VREG_2V7 (pin 23) to GND"),
        ("R101", "Device:R", "1k (verify)", R0402, "VBUS -> VBUS_VS_DISCH (pin 18) sense/discharge series R"),
        ("R102", "Device:R", "10k", R0402, "ALERT (pin 19) open-drain pull-up to +3V3"),
        ("R103", "Device:R", "10k", R0402, "ATTACH (pin 11) open-drain pull-up to +3V3"),
        ("Q101", "Transistor_FET:DMP3099L", "DMP3099L", None, "VBUS power-path PMOS, gate driven by VBUS_EN_SNK (pin 16)"),
        ("R104", "Device:R", "100k", R0402, "Q101 gate-source pull-up (keeps switch off when idle)"),
        ("R105", "Device:R", "47k", R0402, "Q101 gate series R: with R104 limits Vgs to -13.6V at 20V PD"),
        ("U102", "Regulator_Switching:TPS54302", "TPS54302", None, "Buck VBUS_SNK -> +5V 3A (SOT-23-6; replaces SOIC-8 placeholder U3)"),
        ("C104", "Device:C", "10uF 50V X7R", C1206, "Buck input bulk"),
        ("C105", "Device:C", "10uF 50V X7R", C1206, "Buck input bulk"),
        ("C106", "Device:C", "100nF 50V", C0603, "Buck input HF, close to VIN/GND"),
        ("C107", "Device:C", "100nF", C0402, "Buck BOOT-SW bootstrap"),
        ("L101", "Device:L", "10uH SRP7028A-100M", "Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm",
         "Buck inductor: 20V->5V @400kHz gives ~0.94A ripple (4.7uH gives ~2A, too high)"),
        ("C108", "Device:C", "22uF 10V", C0805, "Buck output"),
        ("C109", "Device:C", "22uF 10V", C0805, "Buck output"),
        ("R106", "Device:R", "100k 1%", R0402, "FB top: Vout = 0.596*(1+R106/R107) = 4.95V"),
        ("R107", "Device:R", "13.7k 1%", R0402, "FB bottom (placeholder R2=32.4k would give 2.43V)"),
        ("U103", "Power_Management:TPS22917DBV", "TPS22917DBV", None, "MR1 +5V load switch (TPS22916 is not in the KiCad lib)"),
        ("C110", "Device:C", "1uF", C0402, "TPS22917 VIN decoupling"),
        ("C111", "Device:C", "1nF", C0402, "TPS22917 CT slew-rate cap (sets soft-start)"),
        ("U104", "Regulator_Linear:TLV70233_SOT23-5", "TLV70233", None, "+3V3 LDO for MCU/sensors (LD39050 is DFN-6, not SOT-23-5)"),
        ("C112", "Device:C", "1uF", C0402, "TLV70233 input"),
        ("C113", "Device:C", "1uF", C0402, "TLV70233 output"),
    ],
    "MCU_STM32.kicad_sch": [
        ("C201", "Device:C", "100nF", C0402, "U11 VDD decoupling (one per VDD pin)"),
        ("C202", "Device:C", "100nF", C0402, "U11 VDD decoupling"),
        ("C203", "Device:C", "100nF", C0402, "U11 VDD decoupling"),
        ("C204", "Device:C", "100nF", C0402, "U11 VREF+ decoupling"),
        ("C205", "Device:C", "4.7uF", C0603, "+3V3 bulk at MCU"),
        ("FB201", "Device:FerriteBead_Small", "600R@100MHz", "Inductor_SMD:L_0603_1608Metric", "VDDA filter from +3V3"),
        ("C206", "Device:C", "1uF", C0402, "VDDA decoupling"),
        ("C207", "Device:C", "10nF", C0402, "VDDA decoupling"),
        ("C208", "Device:C", "100nF", C0402, "NRST to GND"),
        ("R201", "Device:R", "10k", R0402, "PB8-BOOT0 pull-down (boot from flash)"),
        ("Y201", "Device:Crystal_GND24", "8MHz CL=10pF", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "HSE crystal (PF0/PF1)"),
        ("C209", "Device:C", "12pF C0G (verify CL)", C0402, "HSE load cap: 2*(CL - Cstray)"),
        ("C210", "Device:C", "12pF C0G (verify CL)", C0402, "HSE load cap"),
        ("J201", "Connector_Generic:Conn_01x05", "SWD", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
         "SWD: 3V3, SWDIO(PA13), SWCLK(PA14), NRST, GND (replaces 4-pin J5)"),
        ("D201", "Device:LED", "GREEN", "LED_SMD:LED_0603_1608Metric", "Status LED"),
        ("R202", "Device:R", "1k", R0402, "Status LED current limit"),
    ],
    "Pressure_Sensors.kicad_sch": [
        ("U301", "Sensor_Pressure:ABPxxxxxxxxx0", "ABPDANN015PG2A3", "Sensor_Pressure:Honeywell_ABPDAN",
         "Cis pressure, I2C addr 0x28 ('2' in P/N). Placeholder footprint Honeywell_ABP_SMD does not exist"),
        ("U302", "Sensor_Pressure:ABPxxxxxxxxx0", "ABPDANN005PG3A3", "Sensor_Pressure:Honeywell_ABPDAN",
         "Trans pressure, I2C addr 0x38 ('3' in P/N) so both share one bus"),
        ("C301", "Device:C", "100nF", C0402, "U301 VCC decoupling"),
        ("C302", "Device:C", "100nF", C0402, "U302 VCC decoupling"),
        ("R301", "Device:R", "4.7k", R0402, "PRESS_I2C_SCL pull-up to +3V3"),
        ("R302", "Device:R", "4.7k", R0402, "PRESS_I2C_SDA pull-up to +3V3"),
    ],
    "Motor_Drivers.kicad_sch": [
        ("U401", "Driver_Motor:DRV8837C", "DRV8837C", "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm",
         "Second H-bridge (pump 2 / stepper coil B)"),
        ("C401", "Device:C", "10uF 16V", C0805, "U12 VM bulk"),
        ("C402", "Device:C", "100nF", C0402, "U12 VM HF"),
        ("C403", "Device:C", "100nF", C0402, "U12 VCC (logic) decoupling"),
        ("C404", "Device:C", "10uF 16V", C0805, "U401 VM bulk"),
        ("C405", "Device:C", "100nF", C0402, "U401 VM HF"),
        ("C406", "Device:C", "100nF", C0402, "U401 VCC (logic) decoupling"),
        ("C407", "Device:C", "47uF 10V", C1206, "VMOTOR shared bulk"),
        ("J401", "Connector_Generic:Conn_01x02", "PUMP1_MOTOR", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "Pump 1 DC motor (U12 OUT1/OUT2)"),
        ("J402", "Connector_Generic:Conn_01x02", "PUMP2_MOTOR", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical", "Pump 2 DC motor (U401 OUT1/OUT2)"),
        ("J403", "Connector_Generic:Conn_01x04", "STEPPER_A1A2B1B2", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
         "Optional bipolar stepper: A=U12 OUT1/2, B=U401 OUT1/2 (no current regulation)"),
    ],
    "USB_Interconnect.kicad_sch": [
        ("U501", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", None, "ESD on J6 (host) D+/D-, VBUS pin to VBUS"),
        ("U502", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", None, "ESD on J7 (MR1) D+/D-, VBUS pin to +5V"),
        ("U503", "Interface_USB:TS3USB30EDGSR", "TS3USB30EDGSR", None, "USB 2.0 1:2 switch (TS3USB221 is not in the KiCad lib)"),
        ("C501", "Device:C", "100nF", C0402, "U503 VCC decoupling"),
        ("R501", "Device:R", "22k", R0402, "J7 CC1 Rp to +5V (advertises 1.5A source)"),
        ("R502", "Device:R", "22k", R0402, "J7 CC2 Rp to +5V"),
    ],
}

# ---------------------------------------------------------------------------
# Minimal S-expression parser / writer
# ---------------------------------------------------------------------------
TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')


def parse(text):
    stack, cur = [], []
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    return cur


def dump(node, indent=1):
    if not isinstance(node, list):
        return node
    if all(not isinstance(c, list) for c in node):
        return "(" + " ".join(node) + ")"
    pad = "\t" * indent
    parts = [node[0]] + [c for c in node[1:] if not isinstance(c, list)]
    head = "(" + " ".join(parts)
    kids = [c for c in node[1:] if isinstance(c, list)]
    return head + "".join("\n" + pad + dump(k, indent + 1) for k in kids) + "\n" + "\t" * (indent - 1) + ")"


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def unq(s):
    return s[1:-1] if s.startswith('"') else s


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


# ---------------------------------------------------------------------------
# Library symbol loading (flattening `extends`)
# ---------------------------------------------------------------------------
_lib_cache = {}


def lib_symbols(lib):
    if lib not in _lib_cache:
        tree = parse((SYMLIB / f"{lib}.kicad_sym").read_text(encoding="utf-8"))[0]
        _lib_cache[lib] = {unq(s[1]): s for s in find(tree, "symbol")}
    return _lib_cache[lib]


def flat_symbol(lib, name):
    syms = lib_symbols(lib)
    sym = syms[name]
    ext = find(sym, "extends")
    if not ext:
        out = [x for x in sym]
    else:
        parent = flat_symbol(lib, unq(ext[0][1]))
        pname = unq(parent[1])
        # Child props override parent props; graphics/pins come from parent.
        child_props = {unq(p[1]): p for p in find(sym, "property")}
        out = ["symbol", q(name)]
        for c in parent[2:]:
            if isinstance(c, list) and c[0] == "property":
                out.append(child_props.pop(unq(c[1]), c))
            elif isinstance(c, list) and c[0] == "symbol":
                sub = list(c)
                sub[1] = q(unq(c[1]).replace(pname, name, 1))
                out.append(sub)
            else:
                out.append(c)
        out[2:2] = []  # keep order
        for p in child_props.values():
            out.append(p)
    return out


def embedded_symbol(lib_id):
    lib, name = lib_id.split(":", 1)
    s = flat_symbol(lib, name)
    s = list(s)
    s[1] = q(lib_id)
    return s


def symbol_pins(sym):
    pins = []

    def walk(n):
        for c in n:
            if isinstance(c, list):
                if c and c[0] == "pin":
                    num = find(c, "number")
                    if num:
                        pins.append(unq(num[0][1]))
                walk(c)

    walk(sym)
    seen, out = set(), []
    for p in pins:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# Instance construction
# ---------------------------------------------------------------------------
def u():
    return str(uuid.uuid4())


def prop(name, value, x, y, hide=False, justify=None):
    eff = ["effects", ["font", ["size", "1.27", "1.27"]]]
    if justify:
        eff.append(["justify", justify])
    p = ["property", q(name), q(value), ["at", f"{x:.2f}", f"{y:.2f}", "0"]]
    if hide:
        p.append(["hide", "yes"])
    p += [["show_name", "no"], ["do_not_autoplace", "no"], eff]
    return p


def instance(lib_id, ref, value, footprint, role, x, y, emb, inst_path):
    props = {unq(p[1]): unq(p[2]) for p in find(emb, "property")}
    fp = footprint or props.get("Footprint", "")
    sym = [
        "symbol",
        ["lib_id", q(lib_id)],
        ["at", f"{x:.2f}", f"{y:.2f}", "0"],
        ["unit", "1"],
        ["body_style", "1"],
        ["exclude_from_sim", "no"],
        ["in_bom", "yes"],
        ["on_board", "yes"],
        ["in_pos_files", "yes"],
        ["dnp", "no"],
        ["uuid", q(u())],
        prop("Reference", ref, x + 2.54, y - 1.27, justify="left"),
        prop("Value", value, x + 2.54, y + 1.27, justify="left"),
        prop("Footprint", fp, x, y, hide=True),
        prop("Datasheet", props.get("Datasheet", "~"), x, y, hide=True),
        prop("Description", props.get("Description", ""), x, y, hide=True),
        prop("MR1_Role", role, x, y, hide=True),
    ]
    for pn in symbol_pins(emb):
        sym.append(["pin", q(pn), ["uuid", q(u())]])
    sym.append(["instances", ["project", q("Pump"), ["path", q(inst_path), ["reference", q(ref)], ["unit", "1"]]]])
    return sym


def note(text, x, y):
    return ["text", q(text), ["exclude_from_sim", "no"], ["at", f"{x:.2f}", f"{y:.2f}", "0"],
            ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", "left", "top"]], ["uuid", q(u())]]


def sheet_paths():
    root = parse((PUMP / "Pump.kicad_sch").read_text(encoding="utf-8"))[0]
    root_uuid = unq(find(root, "uuid")[0][1])
    out = {}
    for sh in find(root, "sheet"):
        props = {unq(p[1]): unq(p[2]) for p in find(sh, "property")}
        out[props["Sheetfile"]] = f"/{root_uuid}/{unq(find(sh, 'uuid')[0][1])}"
    return out


def existing_refs(tree):
    refs = set()
    for s in find(tree, "symbol"):
        for p in find(s, "property"):
            if unq(p[1]) == "Reference":
                refs.add(unq(p[2]))
    return refs


def populate(sheet_file, parts, inst_path, out_dir):
    path = PUMP / sheet_file
    tree = parse(path.read_text(encoding="utf-8"))[0]
    have = existing_refs(tree)
    todo = [p for p in parts if p[0] not in have]
    if not todo:
        print(f"{sheet_file}: nothing to add")
        return 0

    # Promote to A3 and place in a band below existing A4 content.
    for pp in find(tree, "paper"):
        pp[1] = q("A3")
    libsyms = find(tree, "lib_symbols")[0]
    present = {unq(s[1]) for s in find(libsyms, "symbol")}

    ics = [p for p in todo if p[0][0] in "UQY" or p[0].startswith("J")]
    small = [p for p in todo if p not in ics]
    placed = []
    x, y = 30.48, 228.60
    for p in ics:
        placed.append((p, x, y))
        x += 45.72
        if x > 380:
            x, y = 30.48, y + 30.48
    rows = [251.46, 266.70, 281.94]
    for i, p in enumerate(small):
        r, c = divmod(i, 22)
        placed.append((p, 30.48 + c * 15.24, rows[min(r, 2)] + (r // 3) * 0))

    lines = [f"AUTO-POPULATED (unwired) by scripts/populate_pump_schematic.py - {sheet_file}"]
    for (ref, lib_id, value, fp, role), px, py in placed:
        if lib_id not in present:
            libsyms.append(embedded_symbol(lib_id))
            present.add(lib_id)
        emb = next(s for s in find(libsyms, "symbol") if unq(s[1]) == lib_id)
        tree.append(instance(lib_id, ref, value, fp, role, px, py, emb, inst_path))
        lines.append(f"{ref}: {value} - {role}")
    tree.append(note("\n".join(lines), 300.0, 20.0))

    (out_dir / sheet_file).write_text(dump(tree) + "\n", encoding="utf-8")
    print(f"{sheet_file}: added {len(placed)} parts ({', '.join(p[0][0] for p in placed)})")
    return len(placed)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="write into a temp copy and report only")
    ap.add_argument("--out-dir", type=Path, default=None, help="write modified sheets here instead of Pump/")
    ap.add_argument("--force", action="store_true", help="ignore Eeschema lock file")
    a = ap.parse_args()

    out_dir = a.out_dir or PUMP
    if a.dry_run:
        import tempfile
        out_dir = Path(tempfile.mkdtemp(prefix="pump_sch_"))
        for f in PUMP.glob("*.kicad_*"):
            shutil.copy2(f, out_dir / f.name)
    elif out_dir == PUMP and (PUMP / "~Pump.kicad_sch.lck").exists() and not a.force:
        sys.exit("Eeschema has Pump.kicad_sch open (~Pump.kicad_sch.lck). Save and close it, then re-run.")
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = sheet_paths()
    total = sum(populate(f, parts, paths[f], out_dir) for f, parts in PLAN.items())
    print(f"Total parts added: {total} -> {out_dir}")


if __name__ == "__main__":
    main()
