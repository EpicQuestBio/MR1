# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
build_interposer_kicad.py

Generates the adapted Interposer KiCad PCB and Schematic:
1. Strips all active components (U2 LMP7721, U16 LTC6268, R1..R9, C1..C20, NT3..NT5, J9).
2. Retains Edge.Cuts (55.0 x 51.962 mm hexagon, central wafer aperture, fluid pass-throughs).
3. Retains H1, H2, H3, H4 (Fluid pass-through / mounting holes) and J1, J2, J10, J11 (Ag/AgCl ribbon electrode pads).
4. Adds J_POGO1 (PogoPin_Target_12Pin_Distributed) with 12 ultra-low-leakage ENIG landing pads.
5. Adds guarded, low-leakage routing tracks connecting Pogo targets to electrodes.
6. Builds a clean, valid Interposer schematic (Interposer.kicad_sch).
"""

import argparse
import re
import sys
import uuid
from pathlib import Path

def new_uuid():
    return str(uuid.uuid4())

POGO_12PIN_PCB_FP = """\t(footprint "footprints:PogoPin_Target_12Pin_Distributed"
\t\t(layer "F.Cu")
\t\t(uuid "95e44bea-e0b1-4001-93da-f59cd86b29fe")
\t\t(at 164.5 73.5)
\t\t(descr "12-Pin Low-Leakage ENIG Pogo Pin Landing Array for Nanopore Microfluidic Interposer (Mill-Max 821/824 series, 0.8N spring force, Guarded Cis/Trans lines)")
\t\t(tags "pogo landing array target enig rogers ptfe nanopore mill-max")
\t\t(property "Reference" "J_POGO1"
\t\t\t(at 0 -3.0 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "5071002a-544f-43d6-9041-68a3e337c985")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Value" "PogoPin_Target_12Pin_Distributed"
\t\t\t(at 0 3.0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "72307f13-d969-4bef-8aad-4ed6011d84fb")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Footprint" "footprints:PogoPin_Target_12Pin_Distributed"
\t\t\t(at 0 0 0)
\t\t\t(hide yes)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "37d4001f-ee66-4f8d-afb1-c1ddc2c4dcce")
\t\t)
\t\t(attr smd)
\t\t(fp_line (start -13.0 -2.0) (end 13.0 -2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "6236d4d7-584f-47b5-b90e-61affb2055f1"))
\t\t(fp_line (start 13.0 -2.0) (end 13.0 2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "ee37fc2f-ecf3-4c13-9e83-f662e883a919"))
\t\t(fp_line (start 13.0 2.0) (end -13.0 2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "dea243f5-a37c-4514-af83-78410423bc5b"))
\t\t(fp_line (start -13.0 2.0) (end -13.0 -2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "80ae3807-bbb7-49c6-a801-491623e724c2"))
\t\t(fp_text user "WE_POS" (at -11.0 -2.5 0) (layer "F.SilkS") (uuid "cbda5245-07c6-4dc8-8dbf-6bb9a017ce97") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t\t(fp_text user "WS_CIS" (at -9.0 -2.5 0) (layer "F.SilkS") (uuid "64e0f5bf-e8a8-4cb7-89b7-274d57147ee2") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t\t(fp_text user "RE_TRANS" (at -7.0 -2.5 0) (layer "F.SilkS") (uuid "ddca3a31-2046-435c-aa92-73078c08fae5") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t\t(fp_text user "CE_GNDA" (at -5.0 -2.5 0) (layer "F.SilkS") (uuid "b7883da3-140b-4e9f-98b9-898ef55de3a0") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t\t(fp_text user "GNDA" (at -3.0 -2.5 0) (layer "F.SilkS") (uuid "e8f675fb-73bd-4da5-aeb6-693bdd3c64da") (effects (font (size 0.5 0.5) (thickness 0.08))))
		(fp_text user "WEEP_SENSE" (at -1.0 -2.5 0) (layer "F.SilkS") (uuid "d46c3848-83b3-479d-83b5-936c55527a16") (effects (font (size 0.5 0.5) (thickness 0.08))))
\t\t(pad "1" smd circle (at -11.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "WE_POS") (uuid "284159ec-87de-4484-a301-3ab5b484e376"))
\t\t(pad "2" smd circle (at -9.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "WS_CIS") (uuid "571aea81-d3b8-43f7-a8a9-27bc4e899387"))
\t\t(pad "3" smd circle (at -7.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "RE_TRANS") (uuid "31fcb213-610f-416f-b2c2-5175c6d344d2"))
\t\t(pad "4" smd circle (at -5.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "CE_GNDA") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2170"))
\t\t(pad "5" smd circle (at -3.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GNDA") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2171"))
		(pad "6" smd circle (at -1.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "WEEP_SENSE") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2172"))
		(pad "7" smd circle (at 1.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD_TRANS") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2173"))
\t\t(pad "8" smd circle (at 3.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2174"))
\t\t(pad "9" smd circle (at 5.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2175"))
\t\t(pad "10" smd circle (at 7.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2176"))
\t\t(pad "11" smd circle (at 9.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2177"))
\t\t(pad "12" smd circle (at 11.0 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "GUARD") (uuid "8038bb30-4feb-4c87-9c7f-95c3f8bd2178"))
\t)"""

def build_interposer_pcb(out_dir: Path = Path("Interposer")):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_pcb"
    src_pcb_path = Path("Amplifier/Amplifier.kicad_pcb")
    src_pcb = src_pcb_path.read_text(encoding="utf-8")
    lines = src_pcb.splitlines()

    active_refs = {
        "U2", "U16", "J9",
        "R1", "R3", "R4", "R5", "R6", "R8", "R9",
        "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
        "NT3", "NT4", "NT5", "E1"
    }

    retained_refs = {"H1", "H2", "H3", "H4", "J1", "J2", "J10", "J11", "J_POGO1"}

    out_lines = []
    i = 0

    # 1. Header
    while i < len(lines):
        line = lines[i]
        if line.startswith("\t(footprint "):
            break
        out_lines.append(line)
        i += 1

    # 2. Footprints
    retained_fp_blocks = []
    removed_fp_uuids = set()

    pogo_added = False

    while i < len(lines):
        line = lines[i]
        if not line.startswith("\t(footprint "):
            break
        start = i
        depth = line.count("(") - line.count(")")
        block = [line]
        i += 1
        while i < len(lines) and depth > 0:
            block.append(lines[i])
            depth += lines[i].count("(") - lines[i].count(")")
            i += 1
        fp_txt = "\n".join(block)
        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', fp_txt)
        ref = ref_m.group(1) if ref_m else ""

        if ref.startswith("J_POGO") or "PogoPin_Target" in fp_txt:
            if not pogo_added:
                retained_fp_blocks.append(POGO_12PIN_PCB_FP)
                pogo_added = True
            continue

        if ref in active_refs:
            for u in re.findall(r'\(uuid\s+"([^"]+)"\)', fp_txt):
                removed_fp_uuids.add(u)
        elif ref in retained_refs:
            if ref in ("J1", "J2"):
                fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt)
                fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1">PORE_AMP"', fp_txt)
                fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD"', fp_txt)
            elif ref in ("J10", "J11"):
                fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt)
                fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1"Vbias"', fp_txt)
                fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD_TRANS"', fp_txt)
            retained_fp_blocks.append(fp_txt)
        else:
            retained_fp_blocks.append(fp_txt)

    if not pogo_added:
        retained_fp_blocks.append(POGO_12PIN_PCB_FP)

    for fp in retained_fp_blocks:
        out_lines.append(fp)

    # 3. Process drawings, segments, vias, zones, groups
    while i < len(lines):
        line = lines[i]
        
        if line.startswith("\t(segment"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            continue

        if line.startswith("\t(via"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            continue

        if line.startswith("\t(zone"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            continue

        if line.startswith("\t(group"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            grp_txt = "\n".join(block)
            members = re.findall(r'"([0-9a-f\-]{36})"', grp_txt)
            active_m = [m for m in members if m not in removed_fp_uuids]
            if active_m:
                m_str = " ".join(f'"{m}"' for m in active_m)
                grp_id = re.search(r'\(uuid\s+"([^"]+)"\)', grp_txt).group(1)
                locked = "\t\t(locked yes)\n" if "(locked yes)" in grp_txt else ""
                out_lines.append(f'\t(group ""\n\t\t(uuid "{grp_id}")\n{locked}\t\t(members {m_str})\n\t)')
            continue

        out_lines.append(line)
        i += 1

    # 4. Add new Interposer Routing Segments and Copper Flood Zones
    new_segments = [
        f'\t(segment (start 153.5 73.5) (end 153.5 68) (width 0.4) (layer "F.Cu") (net "WE_POS") (uuid "{new_uuid()}"))',
        f'\t(segment (start 153.5 68) (end 150.37866 65.488975) (width 0.4) (layer "F.Cu") (net "WE_POS") (uuid "{new_uuid()}"))',

        f'\t(segment (start 155.5 73.5) (end 158.103349 61.072276) (width 0.4) (layer "F.Cu") (net "WS_CIS") (uuid "{new_uuid()}"))',

        f'\t(segment (start 157.5 73.5) (end 170.855 61.077276) (width 0.4) (layer "B.Cu") (net "RE_TRANS") (uuid "{new_uuid()}"))',

        f'\t(segment (start 159.5 73.5) (end 159.5 68) (width 0.4) (layer "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',
        f'\t(segment (start 159.5 68) (end 178.595144 65.541773) (width 0.4) (layer "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',

        # WEEP_SENSE moat trace and vias
        f'\t(segment (start 163.5 73.5) (end 163.5 68) (width 0.4) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163.5 68) (end 165.9 60.9) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 165.9 60.9) (end 183.2 50.9) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        f'\t(via (at 159.5 73.5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',
        f'\t(via (at 157.5 73.5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "RE_TRANS") (uuid "{new_uuid()}"))',
        f'\t(via (at 163.5 68) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        f'\t(zone (net "GNDA") (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (connect_pads (clearance 0.25)) (min_thickness 0.2) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 0)) (polygon (pts (xy 149.51 84.48) (xy 137.55 84.48) (xy 136.55 83.48) (xy 136.55 32.84) (xy 137.89 31.5) (xy 192.23 31.5) (xy 195.2 34.47) (xy 195.2 85.22) (xy 150.25 85.22))))',
    ]

    insert_idx = len(out_lines) - 1
    while insert_idx >= 0 and out_lines[insert_idx].strip() != ")":
        insert_idx -= 1

    final_lines = out_lines[:insert_idx] + new_segments + out_lines[insert_idx:]
    out_path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    print(f"Successfully built {out_path}!")

def build_interposer_sch(out_dir: Path = Path("Interposer")):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_sch"
    int_sch_src = Path("Interposer/Interposer.kicad_sch")

    if int_sch_src.exists():
        out_path.write_text(int_sch_src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Successfully synchronized {out_path}!")
        return

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="MR1 Interposer KiCad Synchronization Utility."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly allow overwriting authoritative files in Interposer/."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory to write generated output files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing any files."
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)

    if args.dry_run or (not args.write and args.out_dir is None):
        print("Dry-run mode: Interposer design assets protected. No files written.")
        return 0

    out_dir = args.out_dir if args.out_dir is not None else Path("Interposer")
    out_dir.mkdir(parents=True, exist_ok=True)
    build_interposer_pcb(out_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
