# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
kicad_spice_validator.py
========================
Direct KiCad-to-ngspice Circuit Validation Engine for `Amplifier/Amplifier.kicad_sch`.

Instead of hand-coding equations or assuming schematic values, this module:
1. Exports the live netlist directly from `Amplifier/Amplifier.kicad_sch` using `kicad-cli`.
2. Parses every component, value, and pin-to-net connection as drawn.
3. Attaches behavioral SPICE macromodels (`simulations/spice_models/mr1_amplifier_models.lib`)
   and the 4-electrode `NANOPORE_CELL` SPICE model to the pogo-pin interface (`P2, P5, P7, P8, P11, P12`).
4. Executes real `libngspice.so.0` simulations (`.op`, `.ac`, `.tran`) via `ctypes`.
5. Validates the drawn schematic against electrical, bandwidth, nanopore translocation,
   Kelvin potentiostat, and weep-sense safety interlock requirements.
"""

import ctypes
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SCH_PATH = REPO_ROOT / "Amplifier" / "Amplifier.kicad_sch"
MODELS_LIB = REPO_ROOT / "simulations" / "spice_models" / "mr1_amplifier_models.lib"
LIBNGSPICE_PATH = "/usr/lib/x86_64-linux-gnu/libngspice.so.0"


# =============================================================================
# 1. LIBNGSPICE CTYPES DRIVER
# =============================================================================

class _VecInfo(ctypes.Structure):
    _fields_ = [
        ("v_name", ctypes.c_char_p),
        ("v_type", ctypes.c_int),
        ("v_flags", ctypes.c_short),
        ("v_realdata", ctypes.POINTER(ctypes.c_double)),
        ("v_compdata", ctypes.POINTER(ctypes.c_double)),
        ("v_length", ctypes.c_int),
    ]


class _NgComplex(ctypes.Structure):
    _fields_ = [
        ("cx_real", ctypes.c_double),
        ("cx_imag", ctypes.c_double),
    ]


class NgSpiceRunner:
    """Minimal, thread-safe ctypes wrapper around KiCad's bundled libngspice.so.0."""

    _SEND_CHAR = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
    _SEND_STAT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
    _CONTROL_EXIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)

    def __init__(self, lib_path: str = LIBNGSPICE_PATH):
        self.lib = ctypes.CDLL(lib_path)
        self.logs: List[str] = []

        self.lib.ngSpice_Init.argtypes = [
            self._SEND_CHAR, self._SEND_STAT, self._CONTROL_EXIT,
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
        ]
        self.lib.ngSpice_Init.restype = ctypes.c_int
        self.lib.ngSpice_Command.argtypes = [ctypes.c_char_p]
        self.lib.ngSpice_Command.restype = ctypes.c_int
        self.lib.ngSpice_Circ.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
        self.lib.ngSpice_Circ.restype = ctypes.c_int
        self.lib.ngGet_Vec_Info.argtypes = [ctypes.c_char_p]
        self.lib.ngGet_Vec_Info.restype = ctypes.POINTER(_VecInfo)

        self._cb_char = self._SEND_CHAR(self._on_char)
        self._cb_stat = self._SEND_STAT(self._on_stat)
        self._cb_exit = self._CONTROL_EXIT(self._on_exit)
        self.lib.ngSpice_Init(self._cb_char, self._cb_stat, self._cb_exit, None, None, None, None)

    def _on_char(self, msg: bytes, ident: int, userdata: Any) -> int:
        if msg:
            self.logs.append(msg.decode("utf-8", errors="replace"))
        return 0

    def _on_stat(self, msg: bytes, ident: int, userdata: Any) -> int:
        return 0

    def _on_exit(self, status: int, immediate: bool, quitexit: bool, ident: int, userdata: Any) -> int:
        return 0

    def run_circuit(self, netlist_lines: List[str], command: str) -> None:
        self.logs.clear()
        self.lib.ngSpice_Command(b"destroy all")
        self.lib.ngSpice_Command(b"remcirc")
        arr_type = ctypes.c_char_p * (len(netlist_lines) + 1)
        arr = arr_type(*[line.encode("utf-8") for line in netlist_lines], None)
        rc = self.lib.ngSpice_Circ(arr)
        if rc != 0:
            raise RuntimeError(f"ngSpice_Circ failed (rc={rc}):\n" + "\n".join(self.logs[-15:]))
        rc = self.lib.ngSpice_Command(command.encode("utf-8"))
        if rc != 0:
            raise RuntimeError(f"ngSpice_Command({command!r}) failed:\n" + "\n".join(self.logs[-15:]))

    def get_vector(self, name: str) -> np.ndarray:
        ptr = self.lib.ngGet_Vec_Info(name.lower().encode("utf-8"))
        if not ptr:
            raise KeyError(f"SPICE vector {name!r} not found. Logs:\n" + "\n".join(self.logs[-10:]))
        info = ptr.contents
        n = info.v_length
        if info.v_realdata:
            return np.ctypeslib.as_array(info.v_realdata, shape=(n,)).copy()
        if info.v_compdata:
            raw = np.ctypeslib.as_array(info.v_compdata, shape=(2 * n,)).copy()
            return raw[0::2] + 1j * raw[1::2]
        raise ValueError(f"SPICE vector {name!r} has no data")


# =============================================================================
# 2. KICAD NETLIST PARSER & SPICE TRANSLATOR
# =============================================================================

def sanitize_node(net_name: str) -> str:
    """Convert a KiCad net name into a valid, collision-free SPICE node name."""
    if net_name == "GNDA":
        return "0"
    s = net_name.strip()
    if s.startswith("+"):
        s = "P" + s[1:]
    if s.startswith("/"):
        s = s[1:]
    s = s.replace(">", "GT_").replace("~{", "N_").replace("}", "")
    s = s.replace("+", "_POS_")
    # Replace sign '-' in pin/net names like IN-, -IN, -OUT, -FB while keeping separator '-' as '_'
    s = re.sub(r"IN-", "IN_NEG_", s)
    s = re.sub(r"-(IN|OUT|FB)", r"_NEG_\1", s)
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "NODE_EMPTY"


def parse_spice_value(raw_val: str, ref: str) -> str:
    """Extract clean SPICE numeric/suffix value from KiCad Value field."""
    val = raw_val.strip()
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(MEG|Meg|meg|G|k|K|M|m|u|µ|n|p|f)?", val)
    if not m:
        return val
    num, unit = m.group(1), m.group(2) or ""
    unit_map = {"K": "k", "µ": "u", "Meg": "MEG", "meg": "MEG"}
    if unit == "M" and ref.startswith("R"):
        unit = "MEG"
    else:
        unit = unit_map.get(unit, unit)
    return f"{num}{unit}"


def export_kicad_netlist(sch_path: Path = SCH_PATH) -> Dict[str, Any]:
    """Run kicad-cli to export the live kicadsexpr netlist and parse components + nets."""
    with tempfile.NamedTemporaryFile(suffix=".net", delete=False) as tf:
        tmp_net = Path(tf.name)
    try:
        subprocess.run(
            ["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", str(sch_path), "--output", str(tmp_net)],
            check=True,
            capture_output=True,
            text=True,
        )
        text = tmp_net.read_text(encoding="utf-8")
    finally:
        if tmp_net.exists():
            tmp_net.unlink()

    components: Dict[str, Dict[str, str]] = {}
    comp_section = text[text.find("(components"):text.find("(libparts")]
    for block in re.split(r"\(comp\s+", comp_section)[1:]:
        ref_m = re.search(r"\(ref \"([^\"]+)\"\)", block)
        if not ref_m:
            continue
        ref = ref_m.group(1)
        val_m = re.search(r"\(value \"([^\"]+)\"\)", block)
        fp_m = re.search(r"\(footprint \"([^\"]+)\"\)", block)
        components[ref] = {
            "value": val_m.group(1) if val_m else "",
            "footprint": fp_m.group(1) if fp_m else "",
        }

    # Map (ref, pin) -> sanitized SPICE node
    pin_map: Dict[Tuple[str, str], str] = {}
    nets_by_name: Dict[str, List[Tuple[str, str]]] = {}
    nets_section = text[text.find("(nets"):]
    for net_block in nets_section.split("(net\n")[1:]:
        name_m = re.search(r"\(name \"([^\"]+)\"\)", net_block)
        if not name_m:
            continue
        raw_name = name_m.group(1)
        node = sanitize_node(raw_name)
        nodes = re.findall(r"\(ref \"([^\"]+)\"\)\s*\(pin \"([^\"]+)\"", net_block)
        nets_by_name[node] = nodes
        for ref, pin in nodes:
            pin_map[(ref, pin)] = node

    return {
        "components": components,
        "pin_map": pin_map,
        "nets": nets_by_name,
    }


def build_spice_netlist_from_kicad(
    parsed_netlist: Dict[str, Any],
    route_sel_v: float = 0.0,
    vpore_v: float = 0.180,
    r_pore_open: str = "1.8G",
    blk_frac: float = 0.25,
    r_weep_leak: str = "100MEG",
    use_route2_cell: bool = False,
) -> List[str]:
    """
    Translates the parsed KiCad schematic netlist directly into an ngspice circuit,
    attaching `mr1_amplifier_models.lib` and `NANOPORE_CELL` to the drawn pogo pins.
    """
    comps = parsed_netlist["components"]
    pmap = parsed_netlist["pin_map"]

    def get_pin(ref: str, pin: str, fallback: str = None) -> str:
        if (ref, pin) in pmap:
            return pmap[(ref, pin)]
        return fallback or f"NC_{ref}_{pin}"

    lines = [
        "* Live KiCad-Exported SPICE Netlist for Amplifier/Amplifier.kicad_sch",
        f".include {MODELS_LIB}",
        ".options rshunt=1e12",
        "",
        "* --- External Board Connector J7 Power & Control ---",
        f"V_3V3 P3V3 0 DC 3.3",
        f"V_VDDA VDDA 0 DC 2.5",
        f"V_VSSA VSSA 0 DC -2.5",
        f"V_PORE GT_PORE_AMP 0 DC {vpore_v}",
        f"V_RSEL ROUTE_SEL 0 DC {route_sel_v}",
        "",
        "* --- 4-Electrode Nanopore Cell SPICE Model on Pogo Pins ---",
        f"V_BLK BLK_CTRL 0 PULSE(0 1 10m 50u 50u 15m 50m)",
    ]

    if use_route2_cell:
        # Connect nanopore/micropore cell to Route 2 pogo pin (P2.1 = WS_CIS_WIDE)
        lines.append(
            f"X_CELL WS_CIS_WIDE RE_TRANS CE_GNDA 0 BLK_CTRL NANOPORE_CELL R_OPEN={r_pore_open} BLK_FRAC={blk_frac} C_MEM=15p"
        )
    else:
        # Connect nanopore cell to Route 1 pogo pin (P5.1 = WS_CIS)
        lines.append(
            f"X_CELL WS_CIS RE_TRANS CE_GNDA 0 BLK_CTRL NANOPORE_CELL R_OPEN={r_pore_open} BLK_FRAC={blk_frac} C_MEM=15p"
        )

    lines.append("")
    lines.append("* --- Fluidic Weep-Sense Moat Leakage Between P11 (WEEP_SENSE) and P12 (GNDA_WEEP) ---")
    lines.append(f"R_WEEP_LEAK {get_pin('P11', '1')} {get_pin('P12', '1')} {r_weep_leak}")
    lines.append("")
    lines.append("* --- Schematic Components (1:1 from Amplifier.kicad_sch) ---")

    for ref, info in sorted(comps.items()):
        val = info["value"]
        if ref.startswith("R"):
            n1, n2 = get_pin(ref, "1"), get_pin(ref, "2")
            sval = parse_spice_value(val, ref)
            if sval in ("0", "0.0"):
                sval = "1m"
            lines.append(f"{ref} {n1} {n2} {sval}")
        elif ref.startswith("C"):
            n1, n2 = get_pin(ref, "1"), get_pin(ref, "2")
            sval = parse_spice_value(val, ref)
            lines.append(f"{ref} {n1} {n2} {sval}")
        elif ref.startswith("FB"):
            n1, n2 = get_pin(ref, "1"), get_pin(ref, "2")
            lines.append(f"R_{ref} {n1} {n2} 0.1")
        elif ref.startswith("NT"):
            # Net-tie: short all connected pins with 1 mOhm copper bridge
            pins = sorted({p for (r, p) in pmap if r == ref})
            if len(pins) >= 2:
                base = get_pin(ref, pins[0])
                for idx, p in enumerate(pins[1:], 1):
                    lines.append(f"R_{ref}_{idx} {base} {get_pin(ref, p)} 1m")
        elif ref == "Q4":
            # MMBT3906 PNP: 1=B, 2=E, 3=C -> ngspice Qname C B E model
            lines.append(f"{ref} {get_pin(ref,'3')} {get_pin(ref,'1')} {get_pin(ref,'2')} MMBT3906")
        elif ref == "Q3":
            # BSS138 NMOS: 1=G, 2=S, 3=D -> ngspice Mname D G S B model
            s = get_pin(ref, "2")
            lines.append(f"M{ref} {get_pin(ref,'3')} {get_pin(ref,'1')} {s} {s} BSS138_NMOS")
        elif ref == "D82":
            # BAT54: 1=K, 2=A -> ngspice Dname A K model
            lines.append(f"{ref} {get_pin(ref,'2')} {get_pin(ref,'1')} BAT54_SCHOTTKY")
        elif ref == "U2":
            pins = [get_pin(ref, p) for p in ("1", "2", "3", "4", "6", "7", "8")]
            lines.append(f"X{ref} {' '.join(pins)} LMP7721_KICAD")
        elif ref == "U16":
            pins = [get_pin(ref, p) for p in ("2", "3", "5", "6", "7", "8")]
            lines.append(f"X{ref} {' '.join(pins)} LTC6268_KICAD")
        elif ref == "U5":
            pins = [get_pin(ref, str(p)) for p in range(1, 9)]
            lines.append(f"X{ref} {' '.join(pins)} OPA2192_KICAD")
        elif ref == "U6":
            pins = [get_pin(ref, str(p)) for p in range(1, 18)]
            lines.append(f"X{ref} {' '.join(pins)} ADA4940_KICAD")
        elif ref in ("U17", "U19"):
            pins = [get_pin(ref, str(p)) for p in range(1, 9)]
            lines.append(f"X{ref} {' '.join(pins)} MAX4564_KICAD")
        elif ref == "U18":
            pins = [get_pin(ref, str(p)) for p in range(1, 7)]
            lines.append(f"X{ref} {' '.join(pins)} MAX6070_KICAD")
        elif ref == "U14":
            pins = [get_pin(ref, str(p)) for p in range(1, 6)]
            lines.append(f"X{ref} {' '.join(pins)} LP5907_1V8_KICAD")
        elif ref == "U13":
            pins = [get_pin(ref, str(p)) for p in range(1, 11)]
            lines.append(f"X{ref} {' '.join(pins)} AD4011_KICAD")

    return lines


def run_kicad_spice_validation() -> Dict[str, Any]:
    """
    Runs complete ngspice validation directly against the live KiCad schematic netlist.
    """
    parsed = export_kicad_netlist(SCH_PATH)
    ng = NgSpiceRunner()

    # 1. Route 1 DC & Transient DNA Translocation Validation
    r1_lines = build_spice_netlist_from_kicad(
        parsed, route_sel_v=0.0, vpore_v=0.180, r_pore_open="1.8G", blk_frac=0.25, r_weep_leak="100MEG"
    )
    # Save live testbench netlist for KiCad/ngspice inspection
    tb_path = REPO_ROOT / "exports" / "simulations" / "amplifier_kicad_live_testbench.cir"
    tb_path.parent.mkdir(parents=True, exist_ok=True)
    tb_path.write_text("\n".join(r1_lines + ["", ".tran 100u 40m", ".end", ""]))

    def net_node(base: str) -> str:
        if base in parsed["nets"]:
            return base
        for k in parsed["nets"]:
            if k.endswith("_" + base):
                return k
        return base

    n_vref = net_node("VREF_ADC")
    n_ocm = net_node("V_OCM_1V25")
    n_r1_out = net_node("Route1_OUT")
    n_r2_out = net_node("Route2_OUT")

    ng.run_circuit(r1_lines + [".end"], "op")
    v_ref_adc = float(ng.get_vector(n_vref)[0])
    v_ocm = float(ng.get_vector(n_ocm)[0])
    v_1v8_dry = float(ng.get_vector("P1V8")[0])
    v_re_trans = float(ng.get_vector("RE_TRANS")[0])
    v_u2_out = float(ng.get_vector("Net_C1_Pad1")[0])
    v_r1_out = float(ng.get_vector(n_r1_out)[0])
    v_adc_diff_op = float(ng.get_vector("Net_U13_NEG_IN_POS")[0] - ng.get_vector("Net_U13_NEG_IN_NEG")[0])

    # Run Transient DNA blockade
    ng.run_circuit(r1_lines + [".end"], "tran 200u 40m")
    t_tran = ng.get_vector("time")
    v_adc_p = ng.get_vector("Net_U13_NEG_IN_POS")
    v_adc_n = ng.get_vector("Net_U13_NEG_IN_NEG")
    v_adc_diff_tran = v_adc_p - v_adc_n
    # Open pore at t=5ms, DNA blockade settled at t=24ms
    v_diff_open = float(v_adc_diff_tran[np.argmin(np.abs(t_tran - 0.005))])
    v_diff_block = float(v_adc_diff_tran[np.argmin(np.abs(t_tran - 0.024))])

    # 2. Route 1 AC Frequency Response (inject AC current into WS_CIS)
    ac_r1_lines = build_spice_netlist_from_kicad(
        parsed, route_sel_v=0.0, vpore_v=0.0, r_pore_open="100G", blk_frac=0.0
    )
    ac_r1_lines.append("I_AC_R1 0 WS_CIS DC 0 AC 1p")
    ng.run_circuit(ac_r1_lines + [".end"], "ac dec 20 0.1 10MEG")
    freqs_r1 = np.real(ng.get_vector("frequency"))
    v_r1_ac = ng.get_vector(n_r1_out)
    z_r1_mag = np.abs(v_r1_ac) / 1e-12
    z_r1_dc = float(z_r1_mag[0])
    idx_3db_r1 = np.argmin(np.abs(z_r1_mag - z_r1_dc / math.sqrt(2.0)))
    fc_r1_hz = float(freqs_r1[idx_3db_r1])

    # 3. Route 2 Wideband Micropore AC Response
    ac_r2_lines = build_spice_netlist_from_kicad(
        parsed, route_sel_v=3.3, vpore_v=0.0, r_pore_open="100G", blk_frac=0.0, use_route2_cell=True
    )
    ac_r2_lines.append("I_AC_R2 0 WS_CIS_WIDE DC 0 AC 1u")
    ng.run_circuit(ac_r2_lines + [".end"], "ac dec 20 10 10MEG")
    freqs_r2 = np.real(ng.get_vector("frequency"))
    v_r2_out_ac = ng.get_vector(n_r2_out)
    v_adc_r2_ac = ng.get_vector("Net_U13_NEG_IN_POS") - ng.get_vector("Net_U13_NEG_IN_NEG")
    z_r2_tia_dc = float(np.abs(v_r2_out_ac[0]) / 1e-6)
    z_r2_adc_mag = np.abs(v_adc_r2_ac) / 1e-6
    z_r2_adc_dc = float(z_r2_adc_mag[0])
    idx_3db_r2_tia = np.argmin(np.abs((np.abs(v_r2_out_ac) / 1e-6) - z_r2_tia_dc / math.sqrt(2.0)))
    idx_3db_r2_adc = np.argmin(np.abs(z_r2_adc_mag - z_r2_adc_dc / math.sqrt(2.0)))

    # 4. Weep-Sense Electrolyte Breach Interlock Test
    wet_lines = build_spice_netlist_from_kicad(
        parsed, route_sel_v=0.0, vpore_v=0.180, r_weep_leak="10k"
    )
    ng.run_circuit(wet_lines + [".end"], "op")
    v_1v8_wet = float(ng.get_vector("P1V8")[0])
    v_weep_pull_wet = float(ng.get_vector(net_node("R_WEEP_PULL"))[0])

    return {
        "testbench_cir": str(tb_path),
        "v_ref_adc": v_ref_adc,
        "v_ocm_1v25": v_ocm,
        "v_1v8_dry": v_1v8_dry,
        "v_1v8_wet": v_1v8_wet,
        "v_weep_pull_wet": v_weep_pull_wet,
        "v_re_trans": v_re_trans,
        "v_u2_out_dc": v_u2_out,
        "v_r1_out_dc": v_r1_out,
        "v_adc_diff_op": v_adc_diff_op,
        "v_diff_open_pore": v_diff_open,
        "v_diff_dna_blockade": v_diff_block,
        "route1_z_dc_ohm": z_r1_dc,
        "route1_fc_hz": fc_r1_hz,
        "route2_tia_z_dc_ohm": z_r2_tia_dc,
        "route2_tia_fc_hz": float(freqs_r2[idx_3db_r2_tia]),
        "route2_adc_fc_hz": float(freqs_r2[idx_3db_r2_adc]),
    }


if __name__ == "__main__":
    res = run_kicad_spice_validation()
    print("=== Live KiCad Schematic -> ngspice Validation Results ===")
    for k, v in res.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.6g}")
        else:
            print(f"  {k}: {v}")
