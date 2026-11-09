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

DEFAULT_INTERPOSER_DIR = REPO_ROOT / "Interposer"
DEFAULT_PCB_PATH = DEFAULT_INTERPOSER_DIR / "Interposer.kicad_pcb"
DEFAULT_SCH_PATH = DEFAULT_INTERPOSER_DIR / "Interposer.kicad_sch"
DEFAULT_AMPLIFIER_PCB_PATH = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"

INTERPOSER_CENTER_X = 43.7042
INTERPOSER_CENTER_Y = 42.0206

def new_uuid():
    return str(uuid.uuid4())

def get_pogo_12pin_fp_str(fluid_mode: str = "silk"):
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

PIN_NET_MAP = {
    "1": "GNDA",
    "2": "WS_CIS_WIDE",
    "3": "GUARD_WIDE",
    "4": "GUARD",
    "5": "WS_CIS",
    "6": "GUARD",
    "7": "CE_GNDA",
    "8": "RE_TRANS",
    "9": "WE_POS",
    "10": "GNDA",
    "11": "WEEP_SENSE",
    "12": "GNDA",
}

def annotate_pogo_12pin_nets(fp_str: str) -> str:
    def inject_pad_net(m):
        pnum = m.group(1)
        net = PIN_NET_MAP.get(pnum)
        if net:
            return f'(pad "{pnum}" smd circle {m.group(2)}(net "{net}") (uuid'
        return m.group(0)
    return re.sub(r'\(pad\s+"(\d+)"\s+smd\s+circle\s+([^\n]*?)\(uuid', inject_pad_net, fp_str)

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
    center_x = INTERPOSER_CENTER_X
    center_y = INTERPOSER_CENTER_Y

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

def build_interposer_pcb(out_dir: Path = DEFAULT_INTERPOSER_DIR):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_pcb"
    src_pcb_path = DEFAULT_AMPLIFIER_PCB_PATH
    src_pcb = src_pcb_path.read_text(encoding="utf-8")
    lines = src_pcb.splitlines()

    center_x = INTERPOSER_CENTER_X
    center_y = INTERPOSER_CENTER_Y

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

                if (
                    ref.startswith("J_POGO")
                    or "PogoPin" in block_txt
                    or ref.startswith("P_LAND_")
                    or (ref.startswith("P") and ref[1:].isdigit())
                ):
                    if not pogo_added:
                        pogo_fp_positioned = re.sub(
                            r'^\t\(footprint\s+"([^"]+)"[^\n]*',
                            rf'\t(footprint "\1" (at {center_x:.4f} {center_y:.4f})',
                            POGO_12PIN_PCB_FP,
                            count=1,
                            flags=re.MULTILINE
                        )
                        pogo_fp_positioned = re.sub(
                            r'\(property\s+"Reference"\s+"[^"]*"',
                            '(property "Reference" "J_POGO1"',
                            pogo_fp_positioned
                        )
                        pogo_fp_positioned = annotate_pogo_12pin_nets(pogo_fp_positioned)
                        out_lines.append(pogo_fp_positioned)
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

            # If Edge.Cuts flat bottom edge, carve the 13.5x3.0mm cavity notch for Interposer
            if (
                '(layer "Edge.Cuts")' in block_txt
                and "36.9542" in block_txt
                and "50.4542" in block_txt
                and "68.001372" in block_txt
            ):
                cavity_ec = (
                    f'\t(gr_line (start 36.9542 68.001372) (end 36.9542 65.001372) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))\n'
                    f'\t(gr_line (start 36.9542 65.001372) (end 50.4542 65.001372) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))\n'
                    f'\t(gr_line (start 50.4542 65.001372) (end 50.4542 68.001372) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))'
                )
                out_lines.append(cavity_ec)
                continue

            # Retain other top-level drawing/setup blocks (gr_line, gr_poly, setup, layers, etc.)
            out_lines.append(block_txt)
            continue

        out_lines.append(line)
        i += 1

    # Strip any trailing closing parentheses from out_lines so we can append footprints and segments cleanly
    while out_lines and out_lines[-1].strip() in (")", ""):
        out_lines.pop()

    if not pogo_added:
        pogo_fp_positioned = re.sub(
            r'^\t\(footprint\s+"([^"]+)"[^\n]*',
            rf'\t(footprint "\1" (at {center_x:.4f} {center_y:.4f})',
            POGO_12PIN_PCB_FP,
            count=1,
            flags=re.MULTILINE
        )
        pogo_fp_positioned = re.sub(
            r'\(property\s+"Reference"\s+"[^"]*"',
            '(property "Reference" "J_POGO1"',
            pogo_fp_positioned
        )
        pogo_fp_positioned = annotate_pogo_12pin_nets(pogo_fp_positioned)
        out_lines.append(pogo_fp_positioned)

    seen_refs = set(re.findall(r'\(property\s+"Reference"\s+"([^"]+)"', "\n".join(out_lines)))
    for href in ("H1", "H2", "H3", "H4"):
        if href not in seen_refs:
            hx = center_x + spec.FLUID_HOLES[href][0]
            hy = center_y - spec.FLUID_HOLES[href][1]
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
        return round(center_x + p.x, 3), round(center_y - p.y, 3)

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

    # Ribbon electrode route targets relative to board center
    j1_x, j1_y = round(center_x + 10.392, 3), round(center_y - 5.994, 3)
    j2_x, j2_y = round(center_x + 14.722, 3), round(center_y - 8.494, 3)
    j2_mid_x, j2_mid_y = round(center_x + 5.500, 3), round(center_y - 11.994, 3)
    gw_y = round(center_y + 5.006, 3)
    j11_x, j11_y = round(center_x - 10.392, 3), round(center_y + 6.006, 3)
    j10_x, j10_y = round(center_x - 14.722, 3), round(center_y + 8.506, 3)
    ce_ret_x, ce_ret_y = round(center_x - 16.500, 3), round(center_y + 6.506, 3)

    # Weep moat contour coordinates relative to board center
    w_p1 = (round(center_x + 12.00, 3), round(center_y + 9.506, 3))
    w_p2 = (round(center_x + 18.70, 3), round(center_y + 2.406, 3))
    w_p3 = (round(center_x + 18.70, 3), round(center_y - 7.594, 3))
    w_p4 = (round(center_x + 1.40, 3), round(center_y - 18.494, 3))
    w_p5 = (round(center_x - 16.50, 3), round(center_y - 18.494, 3))
    w_p6 = (round(center_x - 19.50, 3), round(center_y - 3.494, 3))
    w_p7 = (round(center_x - 16.50, 3), round(center_y + 6.506, 3))

    new_segments = [
        # --- Cis Signal & Guard Routes (B.Cu escape with via-in-pad to clear concentric guard rings) ---
        make_seg(p5_x, p5_y, j1_x, j1_y, 0.35, "B.Cu", "WS_CIS"),
        make_seg(j1_x, j1_y, j1_x, j1_y, 0.35, "F.Cu", "WS_CIS"),
        make_via(p5_x, p5_y, 0.7, 0.35, "WS_CIS"),
        make_via(j1_x, j1_y, 0.7, 0.35, "WS_CIS"),

        make_seg(p2_x, p2_y, j2_mid_x, j2_mid_y, 0.35, "B.Cu", "WS_CIS_WIDE"),
        make_seg(j2_mid_x, j2_mid_y, j2_x, j2_y, 0.35, "B.Cu", "WS_CIS_WIDE"),
        make_seg(j2_x, j2_y, j2_x, j2_y, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_via(p2_x, p2_y, 0.7, 0.35, "WS_CIS_WIDE"),
        make_via(j2_x, j2_y, 0.7, 0.35, "WS_CIS_WIDE"),

        # GUARD feeders: P4 and P6 feeding P5 GUARD ring (routed north to avoid crossing WS_CIS pad 1)
        make_seg(p4_x, p4_y, p4_x, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p4_x, p6_y, p5_x + 1.85, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p6_x, p6_y, p5_x + 1.85, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p5_x + 1.85, p6_y, p5_x + 1.85, p5_y, 0.4, "F.Cu", "GUARD"),

        # GUARD_WIDE feeder: P3 feeding P2 GUARD_WIDE ring (routed south to clear P5 and P2)
        make_seg(p3_x, p3_y, p2_x + 1.85, p3_y, 0.4, "F.Cu", "GUARD_WIDE"),
        make_seg(p2_x + 1.85, p3_y, p2_x + 1.85, p2_y, 0.4, "F.Cu", "GUARD_WIDE"),

        # --- Trans Signal Routes (B.Cu with transition vias at pad center) ---
        make_seg(p9_x, p9_y, p9_x, 54.50, 0.4, "B.Cu", "WE_POS"),
        make_seg(p9_x, 54.50, j11_x, 54.50, 0.4, "B.Cu", "WE_POS"),
        make_seg(j11_x, 54.50, j11_x, j11_y, 0.4, "B.Cu", "WE_POS"),
        make_via(p9_x, p9_y, 0.7, 0.35, "WE_POS"),

        make_seg(p8_x, p8_y, j10_x, j10_y, 0.4, "B.Cu", "RE_TRANS"),
        make_via(p8_x, p8_y, 0.7, 0.35, "RE_TRANS"),

        make_seg(p7_x, p7_y, ce_ret_x, ce_ret_y, 0.4, "B.Cu", "CE_GNDA"),
        make_via(p7_x, p7_y, 0.7, 0.35, "CE_GNDA"),

        # --- WEEP_SENSE Channel-Contouring Moat (F.Cu and B.Cu) ---
        make_via(p11_x, p11_y, 0.7, 0.35, "WEEP_SENSE"),
        make_seg(p11_x, p11_y, w_p1[0], w_p1[1], 0.4, "B.Cu", "WEEP_SENSE"),

        # B.Cu Moat Perimeter Segments (>= 5 segments)
        make_seg(w_p1[0], w_p1[1], w_p2[0], w_p2[1], 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(w_p2[0], w_p2[1], w_p3[0], w_p3[1], 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(w_p3[0], w_p3[1], w_p4[0], w_p4[1], 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(w_p4[0], w_p4[1], w_p5[0], w_p5[1], 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(w_p5[0], w_p5[1], w_p6[0], w_p6[1], 0.3, "B.Cu", "WEEP_SENSE"),
        make_seg(w_p6[0], w_p6[1], w_p7[0], w_p7[1], 0.3, "B.Cu", "WEEP_SENSE"),

        # F.Cu Moat Perimeter Segments (outside gasket perimeter, >= 5 segments)
        make_seg(w_p2[0], w_p2[1], w_p3[0], w_p3[1], 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(w_p3[0], w_p3[1], w_p4[0], w_p4[1], 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(w_p4[0], w_p4[1], w_p5[0], w_p5[1], 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(w_p5[0], w_p5[1], w_p6[0], w_p6[1], 0.3, "F.Cu", "WEEP_SENSE"),
        make_seg(w_p6[0], w_p6[1], w_p7[0], w_p7[1], 0.3, "F.Cu", "WEEP_SENSE"),

        # WEEP_SENSE stitch/transition vias (>= 2 vias)
        make_via(w_p2[0], w_p2[1], 0.8, 0.4, "WEEP_SENSE"),
        make_via(w_p3[0], w_p3[1], 0.8, 0.4, "WEEP_SENSE"),
        make_via(w_p5[0], w_p5[1], 0.8, 0.4, "WEEP_SENSE"),

        # Cavity copper/track keepout zone over ribbon cable slot [36.954, 50.454] x [65.001, 68.001]
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks not_allowed) (vias not_allowed) (copperpour not_allowed)) (polygon (pts (xy {center_x - 7.25:.2f} {center_y + 22.50:.2f}) (xy {center_x + 7.25:.2f} {center_y + 22.50:.2f}) (xy {center_x + 7.25:.2f} {center_y + 27.00:.2f}) (xy {center_x - 7.25:.2f} {center_y + 27.00:.2f}))))',

        # Full-board GNDA copper pour zone covering both F.Cu and B.Cu
        f'\t(zone (net "GNDA") (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (connect_pads (clearance 0.25)) (min_thickness 0.2) (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3) (island_removal_mode 0)) (polygon (pts (xy {center_x - 14.99:.2f} {center_y + 25.99:.2f}) (xy {center_x - 26.95:.2f} {center_y + 25.99:.2f}) (xy {center_x - 27.95:.2f} {center_y + 24.99:.2f}) (xy {center_x - 27.95:.2f} {center_y - 25.65:.2f}) (xy {center_x - 26.61:.2f} {center_y - 26.99:.2f}) (xy {center_x + 27.73:.2f} {center_y - 26.99:.2f}) (xy {center_x + 30.70:.2f} {center_y - 24.02:.2f}) (xy {center_x + 30.70:.2f} {center_y + 26.73:.2f}) (xy {center_x - 14.25:.2f} {center_y + 26.73:.2f}))))',
    ]

    final_lines = out_lines + new_segments + [")"]
    out_path.write_text("\n".join(final_lines) + "\n", encoding="utf-8")
    print(f"Successfully built {out_path}!")

def build_interposer_sch(out_dir: Path = DEFAULT_INTERPOSER_DIR):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_sch"
    int_sch_src = DEFAULT_SCH_PATH

    if int_sch_src.exists():
        out_path.write_text(int_sch_src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Successfully synchronized {out_path}!")
        return

def verify_interposer_pcb(pcb_path: Path = DEFAULT_PCB_PATH) -> list[str]:
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
        pcb_path = DEFAULT_PCB_PATH if args.out_dir is None else args.out_dir / "Interposer.kicad_pcb"
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

    out_dir = args.out_dir if args.out_dir is not None else DEFAULT_INTERPOSER_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    build_interposer_pcb(out_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
