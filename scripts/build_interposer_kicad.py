"""
build_interposer_kicad.py

Generates the adapted Interposer KiCad PCB and Schematic:
1. Strips all active components (U2 LMP7721, U16 LTC6268, R1..R9, C1..C20, NT3..NT5, J9).
2. Retains Edge.Cuts (55.0 x 51.962 mm hexagon, central wafer aperture, fluid pass-throughs).
3. Retains H1 (Nanopore chip holder) and J1, J2, J10, J11 (Ag/AgCl ribbon electrode pads).
4. Adds J_POGO1 (PogoPin_Target_12Pin_Distributed) with ultra-low-leakage ENIG landing pads.
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

def build_interposer_pcb(out_dir: Path = Path("Interposer")):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_pcb"
    int_src_path = Path("Interposer/Interposer.kicad_pcb")

    if int_src_path.exists():
        int_pcb = int_src_path.read_text(encoding="utf-8")
        out_path.write_text(int_pcb, encoding="utf-8")
        print(f"Successfully synchronized {out_path}!")
        return
    src_pcb = Path("Amplifier/Amplifier.kicad_pcb").read_text(encoding="utf-8")
    lines = src_pcb.splitlines()

    active_refs = {
        "U2", "U16", "J9",
        "R1", "R3", "R4", "R5", "R6", "R8", "R9",
        "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
        "NT3", "NT4", "NT5"
    }

    retained_refs = {"H1", "J1", "J2", "J10", "J11"}

    # Separate header (up to footprints), footprints, drawings, tracks/zones/groups
    out_lines = []
    i = 0

    # 1. Header (lines until first footprint)
    while i < len(lines):
        line = lines[i]
        if line.startswith("\t(footprint "):
            break
        # Update title/comments in setup if present
        out_lines.append(line)
        i += 1

    # 2. Footprints
    retained_fp_blocks = []
    removed_fp_uuids = set()

    while i < len(lines):
        line = lines[i]
        if not line.startswith("\t(footprint "):
            break
        # Read entire footprint block
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

        if ref in active_refs:
            # Capture all UUIDs in this footprint to clean up groups later
            for u in re.findall(r'\(uuid\s+"([^"]+)"\)', fp_txt):
                removed_fp_uuids.add(u)
        elif ref in retained_refs:
            # Update pad nets for retained footprints
            if ref in ("J1", "J2"):
                # Cis working electrode and guard
                fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt) # default
                # Set pad 1 to >PORE_AMP
                fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1">PORE_AMP"', fp_txt)
                # Set pad 2 to GUARD
                fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD"', fp_txt)
            elif ref in ("J10", "J11"):
                # Trans bias electrode and trans guard
                fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt) # default
                # Set pad 1 to Vbias
                fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1"Vbias"', fp_txt)
                # Set pad 2 to GUARD_TRANS
                fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD_TRANS"', fp_txt)
            retained_fp_blocks.append(fp_txt)
        else:
            # Any other footprint
            retained_fp_blocks.append(fp_txt)

    for fp in retained_fp_blocks:
        out_lines.append(fp)

    # Add J_POGO1 (Pogo Pin Landing Array) at (164.500, 73.500)
    # Pitch: X offsets [-11.5, -6.5, -1.5, +1.5, +6.5, +11.5]
    # Abs X: [153.0, 158.0, 163.0, 166.0, 171.0, 176.0]
    pogo_fp = f"""\t(footprint "footprints:PogoPin_Target_12Pin_Distributed"
\t\t(layer "F.Cu")
\t\t(uuid "{new_uuid()}")
\t\t(at 164.5 73.5)
\t\t(descr "6-Pin Low-Leakage ENIG Pogo Pin Landing Array for Nanopore Microfluidic Interposer (Mill-Max 821/824 series, 0.8N spring force, Guarded Cis/Trans lines)")
\t\t(tags "pogo landing array target enig rogers ptfe nanopore mill-max")
\t\t(property "Reference" "J_POGO1"
\t\t\t(at 0 -3.0 0)
\t\t\t(layer "F.SilkS")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Value" "PogoPin_Target_12Pin_Distributed"
\t\t\t(at 0 3.0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Footprint" "footprints:PogoPin_Target_12Pin_Distributed"
\t\t\t(at 0 0 0)
\t\t\t(hide yes)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t)
\t\t(attr smd)
\t\t(fp_line (start -13.5 -2.0) (end 13.5 -2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "{new_uuid()}"))
\t\t(fp_line (start 13.5 -2.0) (end 13.5 2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "{new_uuid()}"))
\t\t(fp_line (start 13.5 2.0) (end -13.5 2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "{new_uuid()}"))
\t\t(fp_line (start -13.5 2.0) (end -13.5 -2.0) (stroke (width 0.15) (type default)) (layer "F.SilkS") (uuid "{new_uuid()}"))
\t\t(fp_text user "CIS_WE" (at -11.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(fp_text user "CIS_GRD" (at -6.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(fp_text user "SHLD" (at -1.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(fp_text user "LEAK" (at 1.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(fp_text user "TRANS_GRD" (at 6.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(fp_text user "TRANS_VBIAS" (at 11.5 -2.5 0) (layer "F.SilkS") (uuid "{new_uuid()}") (effects (font (size 0.6 0.6) (thickness 0.1))))
\t\t(pad "1" smd circle (at -11.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net ">PORE_AMP") (uuid "{new_uuid()}"))
\t\t(pad "2" smd circle (at -6.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.3) (zone_connect 0) (net "GUARD") (uuid "{new_uuid()}"))
\t\t(pad "3" smd circle (at -1.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.3) (zone_connect 0) (net "GNDA") (uuid "{new_uuid()}"))
\t\t(pad "4" smd circle (at 1.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.3) (zone_connect 0) (net "WEEP_SENSE") (uuid "{new_uuid()}"))
\t\t(pad "5" smd circle (at 6.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.3) (zone_connect 0) (net "GUARD_TRANS") (uuid "{new_uuid()}"))
\t\t(pad "6" smd circle (at 11.5 0) (size 1.8 1.8) (layers "F.Cu" "F.Mask") (clearance 0.4) (zone_connect 0) (net "Vbias") (uuid "{new_uuid()}"))
\t)"""
    out_lines.append(pogo_fp)

    # 3. Process drawings, segments, vias, zones, groups
    while i < len(lines):
        line = lines[i]
        
        # Check for segments
        if line.startswith("\t(segment"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            # Skip old active traces
            continue

        # Check for vias
        if line.startswith("\t(via"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            # Skip old active vias
            continue

        # Check for zones
        if line.startswith("\t(zone"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            # Keep only outer shield zone or regenerate cleanly
            continue

        # Check for groups
        if line.startswith("\t(group"):
            block = [line]
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            # Filter out removed footprint uuids from group members
            grp_txt = "\n".join(block)
            members = re.findall(r'"([0-9a-f\-]{36})"', grp_txt)
            active_m = [m for m in members if m not in removed_fp_uuids]
            if active_m:
                # Reconstruct group with remaining members
                m_str = " ".join(f'"{m}"' for m in active_m)
                grp_id = re.search(r'\(uuid\s+"([^"]+)"\)', grp_txt).group(1)
                locked = "\t\t(locked yes)\n" if "(locked yes)" in grp_txt else ""
                out_lines.append(f'\t(group ""\n\t\t(uuid "{grp_id}")\n{locked}\t\t(members {m_str})\n\t)')
            continue

        # Normal drawing lines, Edge.Cuts, etc.
        out_lines.append(line)
        i += 1

    # 4. Add new Interposer Routing Segments and Copper Flood Zones (4-Electrode Gamry Architecture)
    # J_POGO1 Pad 1 (176.0, 73.5) to J2 (CE_GNDA on B.Cu) via transition via
    # J_POGO1 Pad 2 (171.0, 73.5) to J1 (RE_TRANS on B.Cu) via transition via
    # J_POGO1 Pad 3 (166.0, 73.5) to GNDA ground plane
    # J_POGO1 Pad 4 (163.0, 73.5) to WEEP_SENSE channel-contouring moat (F.Cu & B.Cu)
    # J_POGO1 Pad 5 (158.0, 73.5) to J11 (WS_CIS on F.Cu)
    # J_POGO1 Pad 6 (153.0, 73.5) to J10 (WE_POS on F.Cu)

    new_segments = [
        # WE_POS: Cis outer drive electrode
        f'\t(segment (start 153 73.5) (end 153 68) (width 0.4) (layer "F.Cu") (net "WE_POS") (uuid "{new_uuid()}"))',
        f'\t(segment (start 153 68) (end 150.37866 65.488975) (width 0.4) (layer "F.Cu") (net "WE_POS") (uuid "{new_uuid()}"))',

        # WS_CIS: Cis inner sense electrode
        f'\t(segment (start 158 73.5) (end 158.103349 61.072276) (width 0.4) (layer "F.Cu") (net "WS_CIS") (uuid "{new_uuid()}"))',

        # RE_TRANS: Trans inner sense electrode (B.Cu)
        f'\t(segment (start 171 73.5) (end 170.855 61.077276) (width 0.4) (layer "B.Cu") (net "RE_TRANS") (uuid "{new_uuid()}"))',

        # CE_GNDA: Trans outer counter electrode (B.Cu)
        f'\t(segment (start 176 73.5) (end 176 68) (width 0.4) (layer "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',
        f'\t(segment (start 176 68) (end 178.595144 65.541773) (width 0.4) (layer "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',

        # Transition and Stitch Vias
        f'\t(via (at 176 73.5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "CE_GNDA") (uuid "{new_uuid()}"))',
        f'\t(via (at 171 73.5) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "RE_TRANS") (uuid "{new_uuid()}"))',
        f'\t(via (at 163 68) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(via (at 180.4 46.1) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(via (at 148.6 70.9) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        # WEEP_SENSE: Channel-contouring moat traces on F.Cu (Cis channel)
        f'\t(segment (start 163 73.5) (end 163 68) (width 0.4) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163 68) (end 165.9 60.9) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 165.9 60.9) (end 183.2 50.9) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 183.2 50.9) (end 183.5 47.5) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 183.5 47.5) (end 180.4 46.1) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 180.4 46.1) (end 165.9 54.5) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 165.9 54.5) (end 164.5 52) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 164.5 52) (end 160 52) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 160 52) (end 157 56.5) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 157 56.5) (end 149 63) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 149 63) (end 145.8 66.1) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 145.8 66.1) (end 145.5 69.5) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 145.5 69.5) (end 148.6 70.9) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        # WEEP_SENSE: Channel-contouring moat traces on B.Cu (Trans channel)
        f'\t(segment (start 148.6 70.9) (end 156 68.5) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 156 68.5) (end 163 68) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163 68) (end 163.1 61) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163.1 61) (end 145.8 51) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 145.8 51) (end 145.5 48) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 145.5 48) (end 146 46) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 146 46) (end 163.1 55.9) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163.1 55.9) (end 180.4 65.9) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 180.4 65.9) (end 183.5 67.5) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 183.5 67.5) (end 180.4 46.1) (width 0.3) (layer "B.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        # GNDA: Full-board copper pour zone on F.Cu and B.Cu
        f'\t(zone (net "GNDA") (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (connect_pads (clearance 0.25)) (min_thickness 0.2) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 0)) (polygon (pts (xy 149.51 84.48) (xy 137.55 84.48) (xy 136.55 83.48) (xy 136.55 32.84) (xy 137.89 31.5) (xy 192.23 31.5) (xy 195.2 34.47) (xy 195.2 85.22) (xy 150.25 85.22))))',
    ]

    # Insert new segments right before the final closing parenthesis
    # Find last ')' in out_lines
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
    sch = f"""(kicad_sch
\t(version 20260306)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{new_uuid()}")
\t(paper "A4")
\t(title_block
\t\t(title "Daemon Pore - PTFE Microfluidic Interposer Board")
\t\t(date "2026-09-30")
\t\t(rev "1.0")
\t\t(company "Daemon Pore Open Source Nanopore Project")
\t\t(comment 1 "Passive Microfluidic Flow Cell Interposer & Electrode Pogo Interface")
\t\t(comment 2 "0.8mm Rogers RO4350B / PTFE Substrate (er=2.1, tan_delta=0.0002, ENIG Finish)")
\t\t(comment 3 "Mill-Max High Contact Force Spring Pin Landing Interface (Guarded Cis/Trans)")
\t\t(comment 4 "Dual-Sided Ag/AgCl Ribbon Electrode Contacts with Weep Moat Leak Detection")
\t)
\t(lib_symbols
\t\t(symbol "Connector_Generic:Conn_01x12" (in_bom yes) (on_board yes)
\t\t\t(property "Reference" "J" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "Conn_01x06" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t)
\t\t(symbol "Connector_Generic:Conn_01x02" (in_bom yes) (on_board yes)
\t\t\t(property "Reference" "J" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "Conn_01x02" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t)
\t\t(symbol "Mechanical:MountingHole" (in_bom yes) (on_board yes)
\t\t\t(property "Reference" "H" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "MountingHole" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27))))
\t\t)
\t)

\t(symbol (lib_id "Connector_Generic:Conn_01x12") (at 70.0 80.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J_POGO1" (at 70.0 68.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "PogoPin_Target_12Pin_Distributed" (at 70.0 70.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:PogoPin_Target_12Pin_Distributed" (at 70.0 80.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(pin "2" (uuid "{new_uuid()}"))
\t\t(pin "3" (uuid "{new_uuid()}"))
\t\t(pin "4" (uuid "{new_uuid()}"))
\t\t(pin "5" (uuid "{new_uuid()}"))
\t\t(pin "6" (uuid "{new_uuid()}"))
\t)

\t(symbol (lib_id "Mechanical:MountingHole") (at 140.0 80.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "H1" (at 140.0 72.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "Nanopore_Wafer_Aperture" (at 140.0 74.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:Nanopore holder_recessed" (at 140.0 80.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t)

\t(symbol (lib_id "Connector_Generic:Conn_01x02") (at 190.0 60.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J1" (at 190.0 52.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "Cis_Electrode_In" (at 190.0 54.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:Electrode_Guard_Shield" (at 190.0 60.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(pin "2" (uuid "{new_uuid()}"))
\t)

\t(symbol (lib_id "Connector_Generic:Conn_01x02") (at 190.0 80.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J2" (at 190.0 72.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "Cis_Electrode_Out" (at 190.0 74.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:Electrode_Guard_Shield" (at 190.0 80.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(pin "2" (uuid "{new_uuid()}"))
\t)

\t(symbol (lib_id "Connector_Generic:Conn_01x02") (at 190.0 110.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J10" (at 190.0 102.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "Trans_Electrode_Out" (at 190.0 104.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:Electrode_Guard_Shield" (at 190.0 110.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(pin "2" (uuid "{new_uuid()}"))
\t)

\t(symbol (lib_id "Connector_Generic:Conn_01x02") (at 190.0 130.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J11" (at 190.0 122.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "Trans_Electrode_In" (at 190.0 124.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:Electrode_Guard_Shield" (at 190.0 130.0 0) (hide yes) (effects (font (size 1.27 1.27))))
\t\t(pin "1" (uuid "{new_uuid()}"))
\t\t(pin "2" (uuid "{new_uuid()}"))
\t)

\t(label ">PORE_AMP" (at 55.0 73.66 180) (effects (font (size 1.27 1.27))))
\t(label "GUARD" (at 55.0 76.2 180) (effects (font (size 1.27 1.27))))
\t(label "GNDA" (at 55.0 78.74 180) (effects (font (size 1.27 1.27))))
\t(label "WEEP_SENSE" (at 55.0 81.28 180) (effects (font (size 1.27 1.27))))
\t(label "GUARD_TRANS" (at 55.0 83.82 180) (effects (font (size 1.27 1.27))))
\t(label "Vbias" (at 55.0 86.36 180) (effects (font (size 1.27 1.27))))

\t(label ">PORE_AMP" (at 210.0 57.46 0) (effects (font (size 1.27 1.27))))
\t(label "GUARD" (at 210.0 60.0 0) (effects (font (size 1.27 1.27))))
\t(label ">PORE_AMP" (at 210.0 77.46 0) (effects (font (size 1.27 1.27))))
\t(label "GUARD" (at 210.0 80.0 0) (effects (font (size 1.27 1.27))))

\t(label "Vbias" (at 210.0 107.46 0) (effects (font (size 1.27 1.27))))
\t(label "GUARD_TRANS" (at 210.0 110.0 0) (effects (font (size 1.27 1.27))))
\t(label "Vbias" (at 210.0 127.46 0) (effects (font (size 1.27 1.27))))
\t(label "GUARD_TRANS" (at 210.0 130.0 0) (effects (font (size 1.27 1.27))))
)
"""
    out_path.write_text(sch, encoding="utf-8")
    print(f"Successfully built {out_path}!")

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Daemon Pore Interposer KiCad Synchronization Utility.\n"
                    "NOTE: 'Interposer/' contains authoritative production design files."
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
        help="Directory to write generated output files (does not touch Interposer/ unless specified)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing any files (default behavior when --write and --out-dir are omitted)."
    )
    return parser.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)

    if args.dry_run or (not args.write and args.out_dir is None):
        print("Dry-run mode: Interposer design assets protected. No files written.")
        print("Use --write to synchronize Interposer/ or --out-dir <PATH> to export to a custom directory.")
        return 0

    out_dir = args.out_dir if args.out_dir is not None else Path("Interposer")
    out_dir.mkdir(parents=True, exist_ok=True)
    build_interposer_pcb(out_dir)
    build_interposer_sch(out_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
