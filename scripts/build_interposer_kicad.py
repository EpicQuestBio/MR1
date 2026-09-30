"""
build_interposer_kicad.py

Generates the adapted Interposer KiCad PCB and Schematic:
1. Strips all active components (U2 LMP7721, U16 LTC6268, R1..R9, C1..C20, NT3..NT5, J9).
2. Retains Edge.Cuts (55.0 x 51.962 mm hexagon, central wafer aperture, fluid pass-throughs).
3. Retains H1 (Nanopore chip holder) and J1, J2, J10, J11 (Ag/AgCl ribbon electrode pads).
4. Adds J_POGO1 (PogoPin_Target_6Pin_Array) with ultra-low-leakage ENIG landing pads.
5. Adds guarded, low-leakage routing tracks connecting Pogo targets to electrodes.
6. Builds a clean, valid Interposer schematic (Interposer.kicad_sch).
"""

import re
import uuid
from pathlib import Path

def new_uuid():
    return str(uuid.uuid4())

def build_interposer_pcb():
    src_pcb = Path("Amplifier/amplifier.kicad_pcb").read_text(encoding="utf-8")
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
    pogo_fp = f"""\t(footprint "footprints:PogoPin_Target_6Pin_Array"
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
\t\t(property "Value" "PogoPin_Target_6Pin_Array"
\t\t\t(at 0 3.0 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{new_uuid()}")
\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))
\t\t)
\t\t(property "Footprint" "footprints:PogoPin_Target_6Pin_Array"
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

    # 4. Add new Interposer Routing Segments
    # J_POGO1 Pad 1 (153.0, 73.5) to J1/J2 Pad 1 (>PORE_AMP)
    # J_POGO1 Pad 2 (158.0, 73.5) to J1 Pad 2 (GUARD)
    # J_POGO1 Pad 3 (163.0, 73.5) to Ground
    # J_POGO1 Pad 4 (166.0, 73.5) to Weep moat
    # J_POGO1 Pad 5 (171.0, 73.5) to J10 Pad 2 (GUARD_TRANS)
    # J_POGO1 Pad 6 (176.0, 73.5) to J10/J11 Pad 1 (Vbias)

    new_segments = [
        # >PORE_AMP: From pogo pin 1 (153.0, 73.5) -> (153.0, 68.0) -> (170.855, 61.077)
        f'\t(segment (start 153.0 73.5) (end 153.0 68.0) (width 0.4) (layer "F.Cu") (net ">PORE_AMP") (uuid "{new_uuid()}"))',
        f'\t(segment (start 153.0 68.0) (end 162.0 64.0) (width 0.4) (layer "F.Cu") (net ">PORE_AMP") (uuid "{new_uuid()}"))',
        f'\t(segment (start 162.0 64.0) (end 170.855 61.077) (width 0.4) (layer "F.Cu") (net ">PORE_AMP") (uuid "{new_uuid()}"))',
        f'\t(segment (start 170.855 61.077) (end 178.595 65.542) (width 0.4) (layer "F.Cu") (net ">PORE_AMP") (uuid "{new_uuid()}"))',

        # GUARD: Guard line running alongside >PORE_AMP from pogo pin 2 (158.0, 73.5)
        f'\t(segment (start 158.0 73.5) (end 158.0 69.0) (width 0.3) (layer "F.Cu") (net "GUARD") (uuid "{new_uuid()}"))',
        f'\t(segment (start 158.0 69.0) (end 163.5 66.5) (width 0.3) (layer "F.Cu") (net "GUARD") (uuid "{new_uuid()}"))',
        f'\t(segment (start 163.5 66.5) (end 170.855 62.5) (width 0.3) (layer "F.Cu") (net "GUARD") (uuid "{new_uuid()}"))',

        # Vbias: From pogo pin 6 (176.0, 73.5) -> (176.0, 68.0) -> (158.103, 61.072) on B.Cu
        f'\t(segment (start 176.0 73.5) (end 176.0 68.0) (width 0.4) (layer "B.Cu") (net "Vbias") (uuid "{new_uuid()}"))',
        f'\t(segment (start 176.0 68.0) (end 166.0 64.0) (width 0.4) (layer "B.Cu") (net "Vbias") (uuid "{new_uuid()}"))',
        f'\t(segment (start 166.0 64.0) (end 158.103 61.072) (width 0.4) (layer "B.Cu") (net "Vbias") (uuid "{new_uuid()}"))',
        f'\t(segment (start 158.103 61.072) (end 150.379 65.489) (width 0.4) (layer "B.Cu") (net "Vbias") (uuid "{new_uuid()}"))',

        # GUARD_TRANS: Guard line running alongside Vbias from pogo pin 5 (171.0, 73.5)
        f'\t(segment (start 171.0 73.5) (end 171.0 69.0) (width 0.3) (layer "B.Cu") (net "GUARD_TRANS") (uuid "{new_uuid()}"))',
        f'\t(segment (start 171.0 69.0) (end 164.5 66.0) (width 0.3) (layer "B.Cu") (net "GUARD_TRANS") (uuid "{new_uuid()}"))',
        f'\t(segment (start 164.5 66.0) (end 158.103 62.5) (width 0.3) (layer "B.Cu") (net "GUARD_TRANS") (uuid "{new_uuid()}"))',

        # WEEP_SENSE: Leak detection moat trace around fluidic zone
        f'\t(segment (start 166.0 73.5) (end 166.0 71.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 166.0 71.0) (end 175.0 71.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 175.0 71.0) (end 175.0 52.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 175.0 52.0) (end 154.0 52.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 154.0 52.0) (end 154.0 71.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',
        f'\t(segment (start 154.0 71.0) (end 163.0 71.0) (width 0.3) (layer "F.Cu") (net "WEEP_SENSE") (uuid "{new_uuid()}"))',

        # GNDA / Shield tie
        f'\t(segment (start 163.0 73.5) (end 163.0 75.0) (width 0.5) (layer "F.Cu") (net "GNDA") (uuid "{new_uuid()}"))',
    ]

    # Insert new segments right before the final closing parenthesis
    # Find last ')' in out_lines
    insert_idx = len(out_lines) - 1
    while insert_idx >= 0 and out_lines[insert_idx].strip() != ")":
        insert_idx -= 1

    final_lines = out_lines[:insert_idx] + new_segments + out_lines[insert_idx:]
    Path("Interposer/Interposer.kicad_pcb").write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    print("Successfully built Interposer/Interposer.kicad_pcb!")

def build_interposer_sch():
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
\t\t(symbol "Connector_Generic:Conn_01x06" (in_bom yes) (on_board yes)
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

\t(symbol (lib_id "Connector_Generic:Conn_01x06") (at 70.0 80.0 0) (unit 1)
\t\t(uuid "{new_uuid()}")
\t\t(property "Reference" "J_POGO1" (at 70.0 68.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Value" "PogoPin_Target_6Pin_Array" (at 70.0 70.0 0) (effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "footprints:PogoPin_Target_6Pin_Array" (at 70.0 80.0 0) (hide yes) (effects (font (size 1.27 1.27))))
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
    Path("Interposer/Interposer.kicad_sch").write_text(sch, encoding="utf-8")
    print("Successfully built Interposer/Interposer.kicad_sch!")

if __name__ == "__main__":
    build_interposer_pcb()
    build_interposer_sch()
