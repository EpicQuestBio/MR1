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
    # Strip embedded Edge.Cuts lines from footprint instance so board-level Edge.Cuts defines the outline
    fp_lines = [l for l in fp_txt.splitlines() if '(layer "Edge.Cuts")' not in l]
    indented_lines = ["\t" + l if l.strip() else "" for l in fp_lines]
    return "\n".join(indented_lines)

PIN_NET_MAP = {
    "1": "GNDA",
    "2": "WS_CIS_WIDE",
    "3": "GUARD_WIDE",
    "4": "GUARD",
    "5": "WS_CIS",
    "7": "CE_GNDA",
    "8": "RE_TRANS",
    "9": ">PORE_AMP",
    "10": "GNDA",
    "11": "WEEP_SENSE",
    "12": "GNDA",
    "13": "GNDA",
    "14": "GNDA",
    "15": "GNDA",
    "16": "GNDA",
}

def annotate_pogo_12pin_nets(fp_str: str) -> str:
    def inject_pad_net(m):
        pnum = m.group(1)
        pad_type = m.group(2)
        pad_shape = m.group(3)
        rest = m.group(4)
        net = PIN_NET_MAP.get(pnum)
        if net:
            return f'(pad "{pnum}" {pad_type} {pad_shape} {rest}(net "{net}") (uuid'
        return m.group(0)
    return re.sub(
        r'\(pad\s+"(\d+)"\s+(smd|np_thru_hole)\s+(circle|rect|custom)\s+([\s\S]*?)\(uuid',
        inject_pad_net,
        fp_str
    )

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
            pad1_net = ">PORE_AMP"

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


def generate_fluid_hole_footprint(ref: str, val: str, x: float, y: float) -> str:
    """
    Generates a microfluidic pass-through port footprint (2.1mm non-plated through-hole, NPTH).
    Pure bare dielectric hole with zero conductive copper and no net connection, ensuring
    the liquid path remains electrically isolated from ground and signal nets.
    Includes a 5.0mm diameter silkscreen keepout ring defining the gasket sealing zone.
    """
    return (
        f'\t(footprint "footprints:Fluidic_Port_PassThrough_5mm"\n'
        f'\t\t(locked yes)\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {x:.4f} {y:.4f})\n'
        f'\t\t(descr "Microfluidic Port 2.1mm NPTH non-plated through-hole with 5.0mm gasket sealing zone")\n'
        f'\t\t(tags "fluidic port npth mountinghole non-conductive")\n'
        f'\t\t(property "Reference" "{ref}"\n'
        f'\t\t\t(at 0 -3.6 0)\n'
        f'\t\t\t(layer "F.SilkS")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects\n'
        f'\t\t\t\t(font\n'
        f'\t\t\t\t\t(size 0.8 0.8)\n'
        f'\t\t\t\t\t(thickness 0.15)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "{val}"\n'
        f'\t\t\t(at 0 3.6 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects\n'
        f'\t\t\t\t(font\n'
        f'\t\t\t\t\t(size 0.7 0.7)\n'
        f'\t\t\t\t\t(thickness 0.12)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "footprints:Fluidic_Port_PassThrough_5mm"\n'
        f'\t\t\t(at 0 0 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t\t(fp_circle (center 0 0) (end 2.5 0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_circle (center 0 0) (end 2.5 0) (stroke (width 0.15) (type solid)) (fill none) (layer "B.SilkS") (uuid "{new_uuid()}"))\n'
        f'\t\t(pad "" np_thru_hole circle\n'
        f'\t\t\t(at 0 0)\n'
        f'\t\t\t(size 2.1 2.1)\n'
        f'\t\t\t(drill 2.1)\n'
        f'\t\t\t(layers "*.Cu" "*.Mask")\n'
        f'\t\t\t(clearance 1.0)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t)'
    )

def generate_channel_electrode_pad_fp(ref: str, val: str, x: float, y: float, rot: float, layer: str, net: str) -> str:
    """
    Generates a 2.0x0.8mm SMD solder pad with exposed solder mask (ENIG bare copper)
    aligned with the microfluidic liquid flow channel (1.4mm width) for attaching
    silver (Ag) ribbon foil (2.0x0.8x0.1mm), bleach-sensitized to form Ag/AgCl electrodes.
    """
    silk_layer = f"{layer}.SilkS"
    fab_layer = f"{layer}.Fab"
    cu_layer = f"{layer}.Cu"
    mask_layer = f"{layer}.Mask"
    mirror_eff = " (justify mirror)" if layer == "B" else ""
    return (
        f'\t(footprint "footprints:Electrode_Guard_Shield"\n'
        f'\t\t(locked yes)\n'
        f'\t\t(layer "{cu_layer}")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {x:.4f} {y:.4f} {rot:.1f})\n'
        f'\t\t(descr "Channel-aligned Ag/AgCl ribbon electrode pad 1.905x1.270mm (0.075x0.050in) with driven guard shield")\n'
        f'\t\t(tags "electrode ag_agcl ribbon microfluidic guard")\n'
        f'\t\t(property "Reference" "{ref}"\n'
        f'\t\t\t(at 0 -1.6 {rot:.1f})\n'
        f'\t\t\t(layer "{silk_layer}")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.7 0.7) (thickness 0.12)){mirror_eff})\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "{val}"\n'
        f'\t\t\t(at 0 1.6 {rot:.1f})\n'
        f'\t\t\t(layer "{fab_layer}")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.6 0.6) (thickness 0.10)){mirror_eff})\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "footprints:Electrode_Guard_Shield"\n'
        f'\t\t\t(at 0 0 {rot:.1f})\n'
        f'\t\t\t(layer "{fab_layer}")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t\t(fp_line (start -0.9525 0.635) (end 0.9525 0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start 0.9525 0.635) (end 0.9525 -0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start 0.9525 -0.635) (end -0.9525 -0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start -0.9525 -0.635) (end -0.9525 0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_text user "Ag/AgCl" (at 0 0 {rot:.1f}) (layer "{fab_layer}") (uuid "{new_uuid()}") (effects (font (size 0.4 0.4) (thickness 0.08)){mirror_eff}))\n'
        f'\t\t(pad "1" smd roundrect\n'
        f'\t\t\t(at 0 0 {rot:.1f})\n'
        f'\t\t\t(size 1.905 1.27)\n'
        f'\t\t\t(layers "{cu_layer}" "{mask_layer}")\n'
        f'\t\t\t(roundrect_rratio 0.15)\n'
        f'\t\t\t(net "{net}")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t)'
    )

def get_fluid_overlay_fp_str(center_x: float, center_y: float) -> str:
    """
    Loads Fluid_Overlay_SILKSCREEN_ONLY footprint and positions it at the board center.
    Provides microfluidic channel outlines (1.4mm width), flow direction indicators,
    wafer 4x4mm pocket boundary, and port keepouts.
    """
    fp_path = DEFAULT_INTERPOSER_DIR / "footprints.pretty" / "Fluid_Overlay_SILKSCREEN_ONLY.kicad_mod"
    fp_txt = fp_path.read_text(encoding="utf-8")
    fp_txt = re.sub(
        r'^\(footprint\s+"([^"]+)"[^\n]*',
        rf'(footprint "\1" (at {center_x:.4f} {center_y:.4f})',
        fp_txt,
        count=1,
        flags=re.MULTILINE
    )
    fp_txt = re.sub(
        r'\(property\s+"Reference"\s+"[^"]*"',
        '(property "Reference" "SYM_FLUID1"',
        fp_txt,
    )
    fp_txt = re.sub(r'\(uuid\s+"[^"]+"\)', lambda m: f'(uuid "{new_uuid()}")', fp_txt)
    indented_lines = ["\t" + l if l.strip() else "" for l in fp_txt.splitlines()]
    return "\n".join(indented_lines)

def build_interposer_pcb(out_dir: Path = DEFAULT_INTERPOSER_DIR):
    out_dir = Path(out_dir)
    out_path = out_dir / "Interposer.kicad_pcb"
    src_pcb_path = DEFAULT_AMPLIFIER_PCB_PATH
    src_pcb = src_pcb_path.read_text(encoding="utf-8")
    lines = src_pcb.splitlines()

    center_x = INTERPOSER_CENTER_X
    center_y = INTERPOSER_CENTER_Y

    def make_gr_line(x1, y1, x2, y2, width=0.2, layer="Edge.Cuts"):
        return (
            f'\t(gr_line\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(stroke (width {width}) (type default))\n'
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{new_uuid()}")\n'
            f'\t)'
        )

    active_refs = {
        "U2", "U16", "J9",
        "R1", "R3", "R4", "R5", "R6", "R8", "R9",
        "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
        "NT3", "NT4", "NT5", "E1"
    }

    retained_refs = set()

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
                cavity_ec = "\n".join([
                    make_gr_line(36.9542, 68.001372, 36.9542, 65.001372),
                    make_gr_line(36.9542, 65.001372, 50.4542, 65.001372),
                    make_gr_line(50.4542, 65.001372, 50.4542, 68.001372),
                ])
                out_lines.append(cavity_ec)
                continue

            # Retain other top-level drawing/setup blocks, except Amplifier mask exclusions
            if '(layer "F.Mask")' in block_txt or '(layer "B.Mask")' in block_txt:
                continue
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

    # 1. Add Fluid Overlay (Microfluidic channels, flow arrows, keepouts, wafer marking)
    out_lines.append(get_fluid_overlay_fp_str(center_x, center_y))

    # 2. Add Fluid Holes H1..H4 with 5.0mm OD landing pads for hermetic sealing
    # H3: Cis In (Bottom-Left), H4: Cis Out (Top-Right)
    # H1: Trans In (Top-Left), H2: Trans Out (Bottom-Right)
    hole_defs = [
        ("H3", "Port_Cis_In_H3", round(center_x - spec.FLUID_PORT_X, 4), round(center_y + spec.FLUID_PORT_Y, 4)),
        ("H4", "Port_Cis_Out_H4", round(center_x + spec.FLUID_PORT_X, 4), round(center_y - spec.FLUID_PORT_Y, 4)),
        ("H1", "Port_Trans_In_H1", round(center_x - spec.FLUID_PORT_X, 4), round(center_y - spec.FLUID_PORT_Y, 4)),
        ("H2", "Port_Trans_Out_H2", round(center_x + spec.FLUID_PORT_X, 4), round(center_y + spec.FLUID_PORT_Y, 4)),
    ]
    for href, hval, hx, hy in hole_defs:
        out_lines.append(generate_fluid_hole_footprint(href, hval, hx, hy))

    # Ribbon electrode route targets aligned with liquid flow:
    # Cis channel (H3 at South-West -> Center -> H4 at North-East, 330 deg flow angle):
    #   J2: Cis Drive (WS_CIS_WIDE), near Inlet H3 at r = 15.5mm
    #   J1: Cis Sense (WS_CIS), near Nanopore at r = 7.0mm
    j2_x, j2_y = round(center_x - 15.5 * 0.866025, 3), round(center_y + 15.5 * 0.500000, 3)
    j1_x, j1_y = round(center_x - 7.0 * 0.866025, 3), round(center_y + 7.0 * 0.500000, 3)

    # Trans channel (H1 at North-West -> Center -> H2 at South-East, 30 deg flow angle):
    #   J11: Trans Sense (RE_TRANS), near Nanopore at r = 7.0mm
    #   J10: Trans Drive (CE_GNDA), near Port H2 at r = 15.5mm
    j11_x, j11_y = round(center_x + 7.0 * 0.866025, 3), round(center_y + 7.0 * 0.500000, 3)
    j10_x, j10_y = round(center_x + 15.5 * 0.866025, 3), round(center_y + 15.5 * 0.500000, 3)

    # 3. Add Channel-Aligned Solder Pads for Ag/AgCl Ribbon Electrodes (1.905x1.27mm exposed ENIG pads)
    # Mirrored rotations: J1 & J2 along H3 leg rotated 30.0 deg; J11 & J10 along H2 leg rotated 330.0 deg
    electrode_defs = [
        ("J2", "Cis_Drive_AgAgCl", j2_x, j2_y, 30.0, "F", "WS_CIS_WIDE"),
        ("J1", "Cis_Sense_AgAgCl", j1_x, j1_y, 30.0, "F", "WS_CIS"),
        ("J11", "Trans_Sense_AgAgCl", j11_x, j11_y, 330.0, "B", "RE_TRANS"),
        ("J10", "Trans_Drive_AgAgCl", j10_x, j10_y, 330.0, "B", "CE_GNDA"),
    ]
    for jref, jval, jx, jy, jrot, jlayer, jnet in electrode_defs:
        out_lines.append(generate_channel_electrode_pad_fp(jref, jval, jx, jy, jrot, jlayer, jnet))

    # 4. Add Central Nanopore Wafer Recess NP1 and Weep Moat Sensor W1 Footprints
    np1_fp = (
        f'\t(footprint "footprints:Nanopore holder_recessed"\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {center_x:.4f} {center_y:.4f})\n'
        f'\t\t(descr "Central 6.20x6.20mm diamond aperture recess for 4x4mm silicon nanopore chip")\n'
        f'\t\t(tags "nanopore wafer aperture flowcell microfluidic")\n'
        f'\t\t(property "Reference" "NP1"\n'
        f'\t\t\t(at 0 -5.0 0)\n'
        f'\t\t\t(layer "F.SilkS")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.8 0.8) (thickness 0.15)))\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "Nanopore_Wafer_Aperture"\n'
        f'\t\t\t(at 0 5.0 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "footprints:Nanopore holder_recessed"\n'
        f'\t\t\t(at 0 0 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t\t(attr smd)\n'
        f'\t\t(embedded_fonts no)\n'
        f'\t)'
    )
    out_lines.append(np1_fp)

    # Board-level Edge.Cuts lines for the 6.20x6.20mm diamond cutout
    wafer_cutout_lines = [
        make_gr_line(f"{center_x:.4f}", f"{center_y - 4.3841:.4f}", f"{center_x + 4.3841:.4f}", f"{center_y:.4f}"),
        make_gr_line(f"{center_x + 4.3841:.4f}", f"{center_y:.4f}", f"{center_x:.4f}", f"{center_y + 4.3841:.4f}"),
        make_gr_line(f"{center_x:.4f}", f"{center_y + 4.3841:.4f}", f"{center_x - 4.3841:.4f}", f"{center_y:.4f}"),
        make_gr_line(f"{center_x - 4.3841:.4f}", f"{center_y:.4f}", f"{center_x:.4f}", f"{center_y - 4.3841:.4f}"),
    ]
    for wl in wafer_cutout_lines:
        out_lines.append(wl)

    w1_fp = (
        f'\t(footprint "footprints:Weep_Moat_Sensor"\n'
        f'\t\t(layer "F.Cu")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {center_x:.4f} {center_y:.4f})\n'
        f'\t\t(descr "Perimeter moisture & leak detection sensor moat flanking microfluidic channels")\n'
        f'\t\t(tags "weep moat leak sensor interlock")\n'
        f'\t\t(property "Reference" "W1"\n'
        f'\t\t\t(at 0 -2.5 0)\n'
        f'\t\t\t(layer "F.SilkS")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.8 0.8) (thickness 0.15)))\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "Weep_Moat_Sensor"\n'
        f'\t\t\t(at 0 2.5 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "footprints:Weep_Moat_Sensor"\n'
        f'\t\t\t(at 0 0 0)\n'
        f'\t\t\t(layer "F.Fab")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t\t(attr smd)\n'
        f'\t\t(embedded_fonts no)\n'
        f'\t)'
    )
    out_lines.append(w1_fp)

    # 5. Add new Interposer Routing Segments, Vias, and Copper Flood Zones
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
        kx, ky = spec.kicad_xy(p.x, p.y, interposer=True)
        return round(center_x + kx, 3), round(center_y + ky, 3)

    p1_x, p1_y = pin_pos(1)
    p2_x, p2_y = pin_pos(2)
    p3_x, p3_y = pin_pos(3)
    p4_x, p4_y = pin_pos(4)
    p5_x, p5_y = pin_pos(5)
    p7_x, p7_y = pin_pos(7)
    p8_x, p8_y = pin_pos(8)
    p9_x, p9_y = pin_pos(9)
    p10_x, p10_y = pin_pos(10)
    p11_x, p11_y = pin_pos(11)
    p12_x, p12_y = pin_pos(12)
    p13_x, p13_y = pin_pos(13)
    p14_x, p14_y = pin_pos(14)
    p15_x, p15_y = pin_pos(15)
    p16_x, p16_y = pin_pos(16)

    # Weep moat closed contour coordinates routed clear of all 4 fluid ports and inside hex Edge.Cuts
    w_pts = [
        (p11_x, p11_y),
        (p11_x, round(center_y + 15.000, 3)),
        (round(center_x + 18.000, 3), round(center_y + 15.000, 3)),
        (round(center_x + 21.200, 3), round(center_y + 11.000, 3)),
        (round(center_x + 21.200, 3), round(center_y - 11.000, 3)),
        (round(center_x + 16.000, 3), round(center_y - 18.000, 3)),
        (round(center_x - 16.000, 3), round(center_y - 18.000, 3)),
        (round(center_x - 21.200, 3), round(center_y - 11.000, 3)),
        (round(center_x - 21.200, 3), round(center_y + 11.000, 3)),
        (round(center_x - 18.500, 3), p11_y),
        (p11_x, p11_y),
    ]

    def make_circle_keepout(cx, cy, radius):
        import math
        pts = []
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            pts.append(f"(xy {cx + radius*math.cos(rad):.3f} {cy + radius*math.sin(rad):.3f})")
        pts_str = " ".join(pts)
        return f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks not_allowed) (vias not_allowed) (copperpour not_allowed)) (polygon (pts {pts_str})))'

    new_segments = [
        # --- Cis Signal & Guard Routes ---
        # J1 (WS_CIS at j1_x, j1_y): Pin 5 is at (p5_x, p5_y). Drops via to B.Cu, routes to J1
        make_via(p5_x, p5_y, 0.7, 0.35, "WS_CIS"),
        make_seg(p5_x, p5_y, j1_x, j1_y, 0.35, "B.Cu", "WS_CIS"),
        make_via(j1_x, j1_y, 0.7, 0.35, "WS_CIS"),

        # J2 (WS_CIS_WIDE at j2_x, j2_y): Pin 2 on F.Cu escapes east through guard notch, routes south of central wafer cutout to Y=54.0, west to j2_x, then north to J2
        make_seg(p2_x, p2_y, 43.600, p2_y, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_seg(43.600, p2_y, 43.600, 54.000, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_seg(43.600, 54.000, j2_x, 54.000, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_seg(j2_x, 54.000, j2_x, j2_y, 0.35, "F.Cu", "WS_CIS_WIDE"),

        # GUARD feeder: P4 feeding P5 GUARD ring directly on F.Cu
        make_seg(p4_x, p4_y, p5_x - 1.85, p5_y, 0.4, "F.Cu", "GUARD"),

        # GUARD_WIDE feeder: P3 feeding P2 GUARD_WIDE ring directly on F.Cu
        make_seg(p3_x, p3_y, p2_x - 1.85, p2_y, 0.4, "F.Cu", "GUARD_WIDE"),

        # --- Trans Signal Routes ---
        # J11 (RE_TRANS at j11_x, j11_y): Pin 8 drops via to B.Cu, routes directly to J11
        make_via(p8_x, p8_y, 0.7, 0.35, "RE_TRANS"),
        make_seg(p8_x, p8_y, j11_x, j11_y, 0.35, "B.Cu", "RE_TRANS"),

        # J10 (CE_GNDA at j10_x, j10_y): Pin 7 on F.Cu routes north of WEEP_SENSE on F.Cu, drops via to J10 on B.Cu
        make_seg(p7_x, p7_y, j10_x, j10_y, 0.4, "F.Cu", "CE_GNDA"),
        make_via(j10_x, j10_y, 0.7, 0.35, "CE_GNDA"),

        # --- WEEP_SENSE Channel-Contouring Closed Moat (F.Cu and B.Cu) ---
        make_via(p11_x, p11_y, 0.7, 0.35, "WEEP_SENSE"),
        *[
            make_seg(w_pts[k][0], w_pts[k][1], w_pts[k + 1][0], w_pts[k + 1][1], 0.3, "B.Cu", "WEEP_SENSE")
            for k in range(len(w_pts) - 1)
        ],
        # F.Cu Moat Perimeter Segments (East and West sides outside fluid keepouts, 6 segments)
        *[
            make_seg(w_pts[k][0], w_pts[k][1], w_pts[k + 1][0], w_pts[k + 1][1], 0.3, "F.Cu", "WEEP_SENSE")
            for k in (2, 3, 4, 6, 7, 8)
        ],
        # WEEP_SENSE stitch/transition vias
        *[
            make_via(w_pts[idx][0], w_pts[idx][1], 0.7, 0.35, "WEEP_SENSE")
            for idx in (2, 5, 6, 9)
        ],

        # --- GNDA Plane Stitching Vias & Sector Bridges Across Fluid Keepout Corridors ---
        *[
            make_via(gx, gy, 0.7, 0.35, "GNDA")
            for gx, gy in [
                (p1_x, p1_y),
                (p10_x, p10_y),
                (p12_x, p12_y),
                (p13_x, p13_y),
                (p14_x, p14_y),
                (p15_x, p15_y),
                (p16_x, p16_y),
                (p1_x, 55.0),
            ]
        ],
        make_seg(p10_x, p10_y, p15_x, p15_y, 0.4, "F.Cu", "GNDA"),
        make_seg(p1_x, 55.0, p1_x, p1_y, 0.4, "F.Cu", "GNDA"),
        make_seg(p15_x, p15_y, p13_x, p13_y, 0.4, "B.Cu", "GNDA"),
        make_seg(p15_x, p15_y, 31.0, 36.0, 0.4, "B.Cu", "GNDA"),
        make_seg(31.0, 36.0, p16_x, p16_y, 0.4, "B.Cu", "GNDA"),
        make_seg(p13_x, p13_y, 56.4, 36.0, 0.4, "B.Cu", "GNDA"),
        make_seg(56.4, 36.0, p14_x, p14_y, 0.4, "B.Cu", "GNDA"),
        make_seg(p14_x, p14_y, 58.0, 46.0, 0.4, "B.Cu", "GNDA"),
        make_seg(58.0, 46.0, p12_x, p12_y, 0.4, "B.Cu", "GNDA"),
        make_seg(58.0, 46.0, p1_x, 55.0, 0.4, "B.Cu", "GNDA"),

        # --- Fluidic Isolation Keepout Zones (Zero Copper / Zero Ground over Fluid Path) ---
        # Port H1..H4 keepouts (5.5mm diameter circles around fluid ports to guarantee non-conductive boundary)
        make_circle_keepout(center_x + spec.FLUID_HOLES["H1"][0], center_y - spec.FLUID_HOLES["H1"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H2"][0], center_y - spec.FLUID_HOLES["H2"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H3"][0], center_y - spec.FLUID_HOLES["H3"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H4"][0], center_y - spec.FLUID_HOLES["H4"][1], 2.75),

        # Cis fluid channel corridor keepout (H3 -> H4 along -30 deg, width 3.6mm) - strictly isolates fluid path from ground copperpour
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (polygon (pts (xy 63.657 32.580) (xy 25.551 54.580) (xy 23.751 51.462) (xy 61.857 29.462))))',

        # Trans fluid channel corridor keepout (H1 -> H2 along 30 deg, width 3.6mm) - strictly isolates fluid path from ground copperpour
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) (polygon (pts (xy 61.857 54.580) (xy 23.751 32.580) (xy 25.551 29.462) (xy 63.657 51.462))))',

        # Central Nanopore Chip aperture copper/track keepout zone (>= 0.5mm clearance around 6.2x6.2mm diamond)
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks not_allowed) (vias not_allowed) (copperpour not_allowed)) (polygon (pts (xy {center_x:.4f} {center_y - 5.5:.4f}) (xy {center_x + 5.5:.4f} {center_y:.4f}) (xy {center_x:.4f} {center_y + 5.5:.4f}) (xy {center_x - 5.5:.4f} {center_y:.4f}))))',

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

    required = ["H1", "H2", "H3", "H4", "J_POGO1", "J1", "J2", "J10", "J11"]
    for r in required:
        if r not in refs:
            issues.append(f"Required reference {r} missing from Interposer PCB")

    if '(layer "Edge.Cuts")' not in content:
        issues.append("Edge.Cuts boundary missing from Interposer PCB")
    if "37.6365" not in content or "46.4047" not in content:
        issues.append("Central 6.2x6.2mm diamond wafer aperture missing from Edge.Cuts")
    if "Fluid_Overlay" not in content:
        issues.append("Fluid_Overlay footprint missing from Interposer PCB")

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
