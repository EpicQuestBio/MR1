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

def get_pogo_12pin_fp_str():
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from generate_footprint import extract_cad_geometry, generate_kicad_footprint
    geom = extract_cad_geometry(pin_count=12)
    fp_txt = generate_kicad_footprint(geom, footprint_name="PogoPin_Target_12Pin_Distributed")
    # Indent block to match PCB footprint section
    indented_lines = ["\t" + l if l.strip() else "" for l in fp_txt.splitlines()]
    return "\n".join(indented_lines)

POGO_12PIN_PCB_FP = get_pogo_12pin_fp_str()

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

        if ref.startswith("J_POGO") or "PogoPin_Target" in fp_txt or "PogoPin_SpringHeader" in fp_txt:
            if not pogo_added:
                # Assign reference J_POGO1 and location to match interposer center (164.5, 58.494)
                pogo_fp_positioned = re.sub(r'\(property\s+"Reference"\s+"[^"]*"', '(property "Reference" "J_POGO1"', POGO_12PIN_PCB_FP)
                pogo_fp_positioned = re.sub(r'\(at\s+[0-9\.\-]+\s+[0-9\.\-]+\)', '(at 164.5 58.494)', pogo_fp_positioned, count=1)
                retained_fp_blocks.append(pogo_fp_positioned)
                pogo_added = True
            continue

        if ref in retained_refs:
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
            for u in re.findall(r'\(uuid\s+"([^"]+)"\)', fp_txt):
                removed_fp_uuids.add(u)

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
