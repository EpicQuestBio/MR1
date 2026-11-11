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
    "6": "GUARD",
    "7": "CE_GNDA",
    "8": "RE_TRANS",
    "9": ">PORE_AMP",
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
    return (
        f'\t(footprint "footprints:Electrode_Guard_Shield"\n'
        f'\t\t(locked yes)\n'
        f'\t\t(layer "{cu_layer}")\n'
        f'\t\t(uuid "{new_uuid()}")\n'
        f'\t\t(at {x:.4f} {y:.4f} {rot:.1f})\n'
        f'\t\t(descr "Channel-aligned Ag/AgCl ribbon electrode pad 1.905x1.270mm (0.075x0.050in) with driven guard shield")\n'
        f'\t\t(tags "electrode ag_agcl ribbon microfluidic guard")\n'
        f'\t\t(property "Reference" "{ref}"\n'
        f'\t\t\t(at 0 -1.6 0)\n'
        f'\t\t\t(layer "{silk_layer}")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.7 0.7) (thickness 0.12)))\n'
        f'\t\t)\n'
        f'\t\t(property "Value" "{val}"\n'
        f'\t\t\t(at 0 1.6 0)\n'
        f'\t\t\t(layer "{fab_layer}")\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t\t(effects (font (size 0.6 0.6) (thickness 0.10)))\n'
        f'\t\t)\n'
        f'\t\t(property "Footprint" "footprints:Electrode_Guard_Shield"\n'
        f'\t\t\t(at 0 0 0)\n'
        f'\t\t\t(layer "{fab_layer}")\n'
        f'\t\t\t(hide yes)\n'
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f'\t\t)\n'
        f'\t\t(fp_line (start -0.9525 0.635) (end 0.9525 0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start 0.9525 0.635) (end 0.9525 -0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start 0.9525 -0.635) (end -0.9525 -0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_line (start -0.9525 -0.635) (end -0.9525 0.635) (stroke (width 0.1) (type default)) (layer "{silk_layer}") (uuid "{new_uuid()}"))\n'
        f'\t\t(fp_text user "Ag/AgCl" (at 0 0 0) (layer "{fab_layer}") (uuid "{new_uuid()}") (effects (font (size 0.4 0.4) (thickness 0.08))))\n'
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

    # 1. Add Fluid Overlay (Microfluidic channels, flow arrows, keepouts, wafer marking)
    out_lines.append(get_fluid_overlay_fp_str(center_x, center_y))

    # 2. Add Fluid Holes H1..H4 with 5.0mm OD landing pads for hermetic sealing
    hole_defs = [
        ("H1", "Port_Cis_In_H1", center_x + spec.FLUID_HOLES["H1"][0], center_y - spec.FLUID_HOLES["H1"][1]),
        ("H2", "Port_Cis_Out_H2", center_x + spec.FLUID_HOLES["H2"][0], center_y - spec.FLUID_HOLES["H2"][1]),
        ("H3", "Port_Trans_In_H3", center_x + spec.FLUID_HOLES["H3"][0], center_y - spec.FLUID_HOLES["H3"][1]),
        ("H4", "Port_Trans_Out_H4", center_x + spec.FLUID_HOLES["H4"][0], center_y - spec.FLUID_HOLES["H4"][1]),
    ]
    for href, hval, hx, hy in hole_defs:
        out_lines.append(generate_fluid_hole_footprint(href, hval, hx, hy))

    # Ribbon electrode route targets aligned with liquid flow:
    # Cis channel (H1 -> Center -> H2, 330 deg flow angle):
    # Both pads placed on Inlet side (between H1 at bottom-right and Nanopore aperture):
    #   J1: Cis Pre-pore (WS_CIS / >PORE_AMP), closest near Nanopore at r = 7.0mm
    #   J2: Cis Inlet (WS_CIS_WIDE), closest near Inlet H1 at r = 15.5mm
    j1_x, j1_y = round(center_x + 7.0 * 0.866025, 3), round(center_y + 7.0 * 0.500000, 3)
    j2_x, j2_y = round(center_x + 15.5 * 0.866025, 3), round(center_y + 15.5 * 0.500000, 3)

    # Trans channel (H3 -> Center -> H4, -30 deg / 150 deg flow angle):
    # Both pads placed on Inlet side (between H3 and Nanopore aperture):
    #   J11: Trans Pre-pore (RE_TRANS), closest near Nanopore at r = 7.0mm
    #   J10: Trans Inlet (CE_GNDA), closest near Inlet H3 at r = 15.5mm
    j11_x, j11_y = round(center_x - 7.0 * 0.866025, 3), round(center_y + 7.0 * 0.500000, 3)
    j10_x, j10_y = round(center_x - 15.5 * 0.866025, 3), round(center_y + 15.5 * 0.500000, 3)

    # 3. Add Channel-Aligned Solder Pads for Ag/AgCl Ribbon Electrodes (1.905x1.27mm exposed ENIG pads)
    # J1: Cis Inlet / Drive (>PORE_AMP) at r=15.5mm near Inlet H1 (adjacent to Pin 9)
    # J2: Cis Pre-pore / Sense (WS_CIS_WIDE) at r=7.0mm near Nanopore (adjacent to Pin 2)
    electrode_defs = [
        ("J1", "Cis_Electrode_In", j2_x, j2_y, 330.0, "F", ">PORE_AMP"),
        ("J2", "Cis_Electrode_Out", j1_x, j1_y, 330.0, "F", "WS_CIS_WIDE"),
        ("J11", "Trans_Sense_AgAgCl", j11_x, j11_y, 210.0, "B", "RE_TRANS"),
        ("J10", "Trans_Drive_AgAgCl", j10_x, j10_y, 210.0, "B", "CE_GNDA"),
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
        f'\t(gr_line (start {center_x:.4f} {center_y - 4.3841:.4f}) (end {center_x + 4.3841:.4f} {center_y:.4f}) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))',
        f'\t(gr_line (start {center_x + 4.3841:.4f} {center_y:.4f}) (end {center_x:.4f} {center_y + 4.3841:.4f}) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))',
        f'\t(gr_line (start {center_x:.4f} {center_y + 4.3841:.4f}) (end {center_x - 4.3841:.4f} {center_y:.4f}) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))',
        f'\t(gr_line (start {center_x - 4.3841:.4f} {center_y:.4f}) (end {center_x:.4f} {center_y - 4.3841:.4f}) (stroke (width 0.2) (type default)) (layer "Edge.Cuts") (uuid "{new_uuid()}"))',
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

    # Weep moat contour coordinates routed clear of all 4 fluid ports
    w_p1 = (round(center_x + 12.00, 3), round(center_y + 9.506, 3))
    w_p2 = (round(center_x + 23.30, 3), round(center_y + 5.000, 3))
    w_p3 = (round(center_x + 23.30, 3), round(center_y - 14.000, 3))
    w_p4 = (round(center_x + 5.00, 3), round(center_y - 20.000, 3))
    w_p5 = (round(center_x - 16.50, 3), round(center_y - 20.000, 3))
    w_p6 = (round(center_x - 22.70, 3), round(center_y - 14.000, 3))
    w_p7 = (round(center_x - 22.70, 3), round(center_y + 5.000, 3))

    def make_circle_keepout(cx, cy, radius):
        import math
        pts = []
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            pts.append(f"(xy {cx + radius*math.cos(rad):.3f} {cy + radius*math.sin(rad):.3f})")
        pts_str = " ".join(pts)
        return f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (tracks not_allowed) (vias not_allowed) (copperpour not_allowed)) (polygon (pts {pts_str})))'

    new_segments = [
        # --- Cis Signal & Guard Routes (F.Cu direct escape, zero vias) ---
        # J1 (>PORE_AMP at j2_x, j2_y): Pin 9 on F.Cu, routed cleanly south & west to J1 pad on F.Cu
        make_seg(p9_x, p9_y, p9_x, j2_y, 0.4, "F.Cu", ">PORE_AMP"),
        make_seg(p9_x, j2_y, j2_x, j2_y, 0.4, "F.Cu", ">PORE_AMP"),

        # J2 (WS_CIS_WIDE at j1_x, j1_y): Pin 2 on F.Cu, routed cleanly north & east to J2 pad on F.Cu (NO VIAS!)
        make_seg(p2_x, p2_y, p2_x, j1_y, 0.35, "F.Cu", "WS_CIS_WIDE"),
        make_seg(p2_x, j1_y, j1_x, j1_y, 0.35, "F.Cu", "WS_CIS_WIDE"),

        # GUARD feeders: P4 and P6 feeding P5 GUARD ring (routed north at Y=40.0 to clear WS_CIS pad 5)
        make_seg(p4_x, p4_y, p4_x, 40.0, 0.4, "F.Cu", "GUARD"),
        make_seg(p4_x, 40.0, p6_x, 40.0, 0.4, "F.Cu", "GUARD"),
        make_seg(p6_x, 40.0, p6_x, p6_y, 0.4, "F.Cu", "GUARD"),
        make_seg(p5_x + 1.85, 40.0, p5_x + 1.85, p5_y, 0.4, "F.Cu", "GUARD"),

        # GUARD_WIDE feeder: P3 feeding P2 GUARD_WIDE ring (routed north and east on F.Cu to clear P12 and P2)
        make_seg(p3_x, p3_y, p3_x, p2_y, 0.4, "F.Cu", "GUARD_WIDE"),
        make_seg(p3_x, p2_y, p2_x - 1.45, p2_y, 0.4, "F.Cu", "GUARD_WIDE"),

        # --- Trans Signal Routes (B.Cu direct & F.Cu excitation feed) ---
        # J11 (RE_TRANS): Pin 8 on B.Cu, direct short route to J11 pad on B.Cu
        make_via(p8_x, p8_y, 0.7, 0.35, "RE_TRANS"),
        make_seg(p8_x, p8_y, j11_x, j11_y, 0.35, "B.Cu", "RE_TRANS"),

        # J10 (CE_GNDA): Pin 7 on B.Cu, direct short route to J10 pad on B.Cu
        make_via(p7_x, p7_y, 0.7, 0.35, "CE_GNDA"),
        make_seg(p7_x, p7_y, j10_x, j10_y, 0.4, "B.Cu", "CE_GNDA"),

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

        # --- Fluidic Isolation Keepout Zones (Zero Copper / Zero Ground over Fluid Path) ---
        # Port H1..H4 keepouts (5.5mm diameter circles around fluid ports to guarantee non-conductive boundary)
        make_circle_keepout(center_x + spec.FLUID_HOLES["H1"][0], center_y - spec.FLUID_HOLES["H1"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H2"][0], center_y - spec.FLUID_HOLES["H2"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H3"][0], center_y - spec.FLUID_HOLES["H3"][1], 2.75),
        make_circle_keepout(center_x + spec.FLUID_HOLES["H4"][0], center_y - spec.FLUID_HOLES["H4"][1], 2.75),

        # Cis fluid channel corridor keepout (H1 -> H2 along 30 deg, width 3.6mm) - strictly isolates fluid path from ground copperpour
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (copperpour not_allowed)) (polygon (pts (xy 61.857 54.580) (xy 23.751 32.580) (xy 25.551 29.462) (xy 63.657 51.462))))',

        # Trans fluid channel corridor keepout (H3 -> H4 along 150 deg, width 3.6mm) - strictly isolates fluid path from ground copperpour
        f'\t(zone (layers "F.Cu" "B.Cu") (uuid "{new_uuid()}") (hatch edge 0.5) (keepout (copperpour not_allowed)) (polygon (pts (xy 63.657 32.580) (xy 25.551 54.580) (xy 23.751 51.462) (xy 61.857 29.462))))',

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
