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

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import stack_spec as spec

def new_uuid():
    return str(uuid.uuid4())

def get_pogo_12pin_fp_str(fluid_mode: str = "drills"):
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.generate_footprint import extract_cad_geometry, generate_kicad_footprint
    geom = extract_cad_geometry(pin_count=12)
    fp_txt = generate_kicad_footprint(geom, footprint_name="PogoPin_Target_12Pin_Distributed", fluid_mode=fluid_mode)
    # Indent block to match PCB footprint section
    indented_lines = ["\t" + l if l.strip() else "" for l in fp_txt.splitlines()]
    return "\n".join(indented_lines)

def get_single_pin_pogo_landings_fp_str():
    """
    Generates placement string for discrete single-pin pogo landing footprints:
    Uses 'PogoPin_Target_Landing_1Pin' as standard default for pogo landings,
    and 'PogoPin_Target_Landing_1Pin_Guarded' for High-Z/driven-guard nets
    (WS_CIS, >PORE_AMP, WS_CIS_WIDE, WEEP_SENSE, GUARD, GUARD_WIDE).
    """
    import sys
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.generate_footprint import (
        PIN_NET_SEQUENCE,
        HIGH_Z_NETS,
        GUARD_NETS,
        generate_single_pin_footprint,
    )

    blocks = []
    center_x = 164.5
    center_y = 58.494

    guarded_nets = HIGH_Z_NETS.union(GUARD_NETS)

    for entry in PIN_NET_SEQUENCE:
        pin_num, net_name, cad_x, cad_y, desc = entry
        is_guarded = net_name in guarded_nets
        fp_name = (
            "PogoPin_Target_Landing_1Pin_Guarded"
            if is_guarded
            else "PogoPin_Target_Landing_1Pin"
        )
        fp_txt = generate_single_pin_footprint(
            fp_name, pin_type="target", guarded=is_guarded, layer="F.Cu"
        )

        px = center_x + cad_x
        py = center_y - cad_y

        # Insert top-level (at X Y) position into footprint definition header
        fp_txt = re.sub(
            r'^\(footprint\s+"([^"]+)"',
            rf'(footprint "\1" (at {px:.4f} {py:.4f})',
            fp_txt,
            count=1,
            flags=re.MULTILINE
        )

        fp_txt = re.sub(
            r'\(property\s+"Reference"\s+"[^"]*"',
            f'(property "Reference" "P_LAND_{pin_num}"',
            fp_txt,
        )
        fp_txt = re.sub(
            r'\(property\s+"Value"\s+"[^"]*"',
            f'(property "Value" "{net_name}"',
            fp_txt,
        )

        # Inject net annotations for KiCad DRC and connectivity
        from src import stack_spec as spec
        pin_def = spec.pin(pin_num)
        ring_net = pin_def.ring

        pad1_net = net_name
        if pin_num in (4, 6):
            pad1_net = "GUARD"
        elif pin_num == 3:
            pad1_net = "GUARD_WIDE"
        elif pin_num in (1, 10, 12):
            pad1_net = "GNDA"
        elif pin_num == 9:
            pad1_net = "WE_POS"

        fp_txt = re.sub(
            r'(\(pad\s+"1"[^\n]*?)\(uuid',
            rf'\1(net "{pad1_net}") (uuid',
            fp_txt,
            count=1
        )
        if ring_net:
            fp_txt = re.sub(
                r'(\(pad\s+"2"\s+smd\s+custom[^\n]*\))',
                rf'\1 (net "{ring_net}")',
                fp_txt,
                count=1
            )

        # Ensure fresh unique UUIDs for all elements within this footprint instance
        fp_txt = re.sub(
            r'\(uuid\s+"[^"]+"\)',
            lambda m: f'(uuid "{new_uuid()}")',
            fp_txt
        )

        indented_lines = ["\t" + l if l.strip() else "" for l in fp_txt.splitlines()]
        blocks.append("\n".join(indented_lines))

    return "\n".join(blocks)

POGO_12PIN_PCB_FP = get_pogo_12pin_fp_str()
SINGLE_PIN_POGO_LANDINGS_FP = get_single_pin_pogo_landings_fp_str()


def generate_fluid_hole_footprint(ref: str, x: float, y: float) -> str:
    return (
        f'\t(footprint "MountingHole:MountingHole_2.1mm"\n'
        f'\t\t(locked yes)\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {x:.4f} {y:.4f})\n'
        f'\t\t(descr "Mounting Hole 2.1mm, no annular, generated by kicad-footprint-generator mountinghole.py")\n'
        f'\t\t(tags "mountinghole")\n'
        f'\t\t(property "Reference" "{ref}"\n'
        f'\t\t\t(at 0 -3.05 0)\n'
        f'\t\t\t(layer "F.SilkS")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects\n'
        f'\t\t\t\t(font\n'
        f'\t\t\t\t\t(size 0.6 0.6)\n'
        f'\t\t\t\t\t(thickness 0.15)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "FluidHole"\n'
        f'\t\t\t(at 0 3.05 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects\n'
        f'\t\t\t\t(font\n'
        f'\t\t\t\t\t(size 1 1)\n'
        f'\t\t\t\t\t(thickness 0.15)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t\t(property "Description" "Mounting Hole without connection"\n'
        f'\t\t\t(at 0 0 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects\n'
        f'\t\t\t\t(font\n'
        f'\t\t\t\t\t(size 0.6 0.6)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t\t(attr exclude_from_bom)\n'
        f'\t\t(duplicate_pad_numbers_are_jumpers no)\n'
        f'\t\t(pad "" np_thru_hole circle\n'
        f'\t\t\t(at 0 0)\n'
        f'\t\t\t(size 2.1 2.1)\n'
        f'\t\t\t(drill 2.1)\n'
        f'\t\t\t(layers "*.Cu" "*.Mask")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t)'
    )

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
    removed_fp_uuids = set()
    pogo_added = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Top-level S-expression blocks (indented by 1 tab)
        if line.startswith("\t("):
            depth = line.count("(") - line.count(")")
            block = [line]
            i += 1
            while i < len(lines) and depth > 0:
                block.append(lines[i])
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            block_txt = "\n".join(block)

            # Handle Footprints
            if line.startswith("\t(footprint "):
                ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block_txt)
                ref = ref_m.group(1) if ref_m else ""

                if ref.startswith("J_POGO") or "PogoPin_Target" in block_txt or "PogoPin_SpringHeader" in block_txt or ref.startswith("P_LAND_"):
                    if not pogo_added:
                        pogo_fp_positioned = re.sub(r'\(property\s+"Reference"\s+"[^"]*"', '(property "Reference" "J_POGO1"', POGO_12PIN_PCB_FP)
                        pogo_fp_positioned = re.sub(r'\(at\s+[0-9\.\-]+\s+[0-9\.\-]+\)', '(at 164.5 58.494)', pogo_fp_positioned, count=1)
                        out_lines.append(pogo_fp_positioned)
                        out_lines.append(SINGLE_PIN_POGO_LANDINGS_FP)
                        pogo_added = True
                    continue

                if ref in retained_refs:
                    fp_txt = block_txt
                    if ref in ("J1", "J2"):
                        fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt)
                        fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1">PORE_AMP"', fp_txt)
                        fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD"', fp_txt)
                    elif ref in ("J10", "J11"):
                        fp_txt = re.sub(r'\(net\s+"[^"]*"\)', '(net "GNDA")', fp_txt)
                        fp_txt = re.sub(r'(\(pad\s+"1"[\s\S]*?\(net\s+)"[^"]*"', r'\1"Vbias"', fp_txt)
                        fp_txt = re.sub(r'(\(pad\s+"2"[\s\S]*?\(net\s+)"[^"]*"', r'\1"GUARD_TRANS"', fp_txt)
                    out_lines.append(fp_txt)
                else:
                    for u in re.findall(r'\(uuid\s+"([^"]+)"\)', block_txt):
                        removed_fp_uuids.add(u)
                continue

            # Strip obsolete segments, vias, and copper zones from active amplifier board
            if line.startswith("\t(segment") or line.startswith("\t(via") or line.startswith("\t(zone"):
                continue

            # Handle groups: strip removed members
            if line.startswith("\t(group"):
                members = re.findall(r'"([0-9a-f\-]{36})"', block_txt)
                active_m = [m for m in members if m not in removed_fp_uuids]
                if active_m:
                    m_str = " ".join(f'"{m}"' for m in active_m)
                    grp_id = re.search(r'\(uuid\s+"([^"]+)"\)', block_txt).group(1)
                    locked = "\t\t(locked yes)\n" if "(locked yes)" in block_txt else ""
                    out_lines.append(f'\t(group ""\n\t\t(uuid "{grp_id}")\n{locked}\t\t(members {m_str})\n\t)')
                continue

            # Retain other top-level drawing/setup blocks (gr_line, gr_poly, setup, layers, etc.)
            out_lines.append(block_txt)
            continue

        out_lines.append(line)
        i += 1

    if not pogo_added:
        out_lines.append(POGO_12PIN_PCB_FP)
        out_lines.append(SINGLE_PIN_POGO_LANDINGS_FP)

    seen_refs = set(re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', "\n".join(out_lines)))
    for href in ("H1", "H2", "H3", "H4"):
        if href not in seen_refs:
            hx = 164.5 + spec.FLUID_HOLES[href][0]
            hy = 58.494 - spec.FLUID_HOLES[href][1]
            out_lines.append(generate_fluid_hole_footprint(href, hx, hy))

    # 4. Add new Interposer Routing Segments, Vias, and Copper Flood Zones
    def make_seg(x1, y1, x2, y2, width, layer, net):
        return (
            f'\t(segment\n'
            f'\t\t(start {x1:.4f} {y1:.4f})\n'
            f'\t\t(end {x2:.4f} {y2:.4f})\n'
            f'\t\t(width {width})\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{new_uuid()}")\n'
            f'\t)'
        )

    def make_via(vx, vy, size, drill, net, layers=("F.Cu", "B.Cu")):
        return (
            f'\t(via\n'
            f'\t\t(at {vx:.4f} {vy:.4f})\n'
            f'\t\t(size {size})\n'
            f'\t\t(drill {drill})\n'
            f'\t\t(layers "{layers[0]}" "{layers[1]}")\n'
            f'\t\t(net "{net}")\n'
            f'\t\t(uuid "{new_uuid()}")\n'
            f'\t)'
        )

    def pin_pos(n):
        p = spec.pin(n)
        return round(164.50 + p.x, 3), round(58.494 - p.y, 3)

    p1_x, p1_y = pin_pos(1)
    p2_x, p2_y = pin_pos(2)
    p3_x, p3_y = pin_pos(3)
    p4_x, p4_y = pin_pos(4)
    p5_x, p5_y = pin_pos(5)
    p6_x, p6_y = pin_pos(6)
    p7_x, p7_y = pin_pos(7)
    p8_x, p8_y = pin_pos(8)
    p9_x, p9_y = pin_pos(9)
    p10_x, p10_y = pin_pos(10)
    p11_x, p11_y = pin_pos(11)
    p12_x, p12_y = pin_pos(12)

    new_segments = [
        # --- Cis Signal & Guard Routes (B.Cu escape with via-in-pad to clear concentric guard rings) ---
        # WS_CIS: P5 -> via to B.Cu -> J1 (174.892, 52.50) via up to F.Cu
        make_seg(p5_x, p5_y, 174.892, 52.50, 0.35, "B.Cu", "WS_CIS"),
        make_seg(174.892, 52.50, 174.892, 52.50, 0.35, "F.Cu", "WS_CIS"),
        make_via(p5_x, p5_y, 0.7, 0.35, "WS_CIS"),
        make_via(174.892, 52.50, 0.7, 0.35, "WS_CIS"),

        # WS_CIS_WIDE: P2 -> via to B.Cu -> J2 (179.222, 50.00) via up to F.Cu
        make_seg(p2_x, p2_y, 170.00, 46.50, 0.35, "B.Cu", "WS_CIS_WIDE"),
        make_seg(170.00, 46.50, 179.222, 50.00, 0.35, "B.Cu", "WS_CIS_WIDE"),
        make_seg(179.222, 50.00, 179.222, 50.00, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_via(p2_x, p2_y, 0.7, 0.35, "WS_CIS_WIDE"),
        make_via(179.222, 50.00, 0.7, 0.35, "WS_CIS_WIDE"),

        # GUARD feeders: P4 and P6 feeding P5 GUARD ring (routed north to avoid crossing WS_CIS pad 1)
        make_seg(p6_x, p6_y, p5_x + 1.85, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p4_x, p4_y, p4_x, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p5_x + 1.85, p6_y, p5_x + 1.85, p5_y, 0.4, "F.Cu", "GUARD"),

        # GUARD_WIDE feeder: P3 feeding P2 GUARD_WIDE ring (routed south to clear P5)
        make_seg(p3_x, p3_y, p3_x, 63.50, 0.4, "F.Cu", "GUARD_WIDE"),
        make_seg(p3_x, 63.50, p2_x + 1.85, 63.50, 0.4, "F.Cu", "GUARD_WIDE"),
        make_seg(p2_x + 1.85, 63.50, p2_x + 1.85, p2_y, 0.4, "F.Cu", "GUARD_WIDE"),

        # --- Trans Signal Routes (B.Cu with transition vias at pad center) ---
        # >PORE_AMP / WE_POS: P9 via to B.Cu -> J11 (154.108, 64.50)
        make_seg(p9_x, p9_y, 154.108, 64.50, 0.4, "B.Cu", "WE_POS"),
        make_via(p9_x, p9_y, 0.7, 0.35, "WE_POS"),

        # RE_TRANS: P8 via to B.Cu -> J10 (149.778, 67.00)
        make_seg(p8_x, p8_y, 149.778, 67.00, 0.4, "B.Cu", "RE_TRANS"),
        make_via(p8_x, p8_y, 0.7, 0.35, "RE_TRANS"),

        # CE_GNDA: P7 via to B.Cu -> ground return
        make_seg(p7_x, p7_y, 148.00, 65.00, 0.4, "B.Cu", "CE_GNDA"),
        make_via(p7_x, p7_y, 0.7, 0.35, "CE_GNDA"),

        # --- WEEP_SENSE Channel-Contouring Moat (F.Cu and B.Cu) ---
        # Feeder from P11 via to B.Cu
        make_via(p11_x, p11_y, 0.7, 0.35, "WEEP_SENSE"),
        make_seg(p11_x, p11_y, 176.50, 68.00, 0.4, "B.Cu", "WEEP_SENSE"),

        # B.Cu Moat Perimeter Segments (>= 5 segments)
        make_seg(176.50, 68.00, 183.20, 60.90, 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(183.20, 60.90, 183.20, 50.90, 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(183.20, 50.90, 165.90, 40.00, 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(165.90, 40.00, 148.00, 40.00, 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(148.00, 40.00, 145.00, 55.00, 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(145.00, 55.00, 148.00, 65.00, 0.3, "B.Cu", "WEEP_SENSE"),

        # F.Cu Moat Perimeter Segments (outside gasket perimeter, >= 5 segments)
        make_seg(183.20, 60.90, 183.20, 50.90, 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(183.20, 50.90, 165.90, 40.00, 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(165.90, 40.00, 148.00, 40.00, 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(148.00, 40.00, 145.00, 55.00, 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(145.00, 55.00, 148.00, 65.00, 0.3, "F.Cu", "WEEP_SENSE"),

        # WEEP_SENSE stitch/transition vias (>= 2 vias)
        make_via(183.20, 60.90, 0.8, 0.4, "WEEP_SENSE"),
        make_via(183.20, 50.90, 0.8, 0.4, "WEEP_SENSE"),
        make_via(148.00, 40.00, 0.8, 0.4, "WEEP_SENSE"),

        # Full-board GNDA copper pour zone covering both F.Cu and B.Cu
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

def verify_interposer_pcb(pcb_path: Path = Path("Interposer/Interposer.kicad_pcb")) -> list[str]:
    """Verifies that the Interposer KiCad PCB adheres to the passive interface specification."""
    if not pcb_path.exists():
        return [f"Interposer PCB file not found: {pcb_path}"]

    content = pcb_path.read_text(encoding="utf-8")
    refs = set(re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', content))
    issues = []

    prohibited = [
        "U2", "U16", "J9",
        "R1", "R3", "R4", "R5", "R6", "R8", "R9",
        "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
        "NT3", "NT4", "NT5", "E1"
    ]
    for p in prohibited:
        if p in refs:
            issues.append(f"Prohibited active component {p} found on Interposer PCB")

    required = ["H1", "H2", "H3", "H4", "J_POGO1"]
    for r in required:
        if r not in refs:
            issues.append(f"Required reference {r} missing from Interposer PCB")

    if '(layer "Edge.Cuts")' not in content:
        issues.append("Edge.Cuts boundary missing from Interposer PCB")

    return issues


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="MR1 Interposer KiCad Synchronization Utility."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check Interposer PCB consistency against specification."
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

    if args.check:
        pcb_path = Path("Interposer/Interposer.kicad_pcb") if args.out_dir is None else args.out_dir / "Interposer.kicad_pcb"
        issues = verify_interposer_pcb(pcb_path)
        if issues:
            print(f"[!] Interposer PCB verification failed ({len(issues)} issues):")
            for iss in issues:
                print(f"    - {iss}")
            return 1
        print("[OK] Interposer PCB is in sync with passive specification.")
        return 0

    if args.dry_run or (not args.write and args.out_dir is None):
        print("Dry-run mode: Interposer design assets protected. No files written.")
        return 0

    out_dir = args.out_dir if args.out_dir is not None else Path("Interposer")
    out_dir.mkdir(parents=True, exist_ok=True)
    build_interposer_pcb(out_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
