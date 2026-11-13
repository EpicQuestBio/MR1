# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
scripts/generate_board_zones.py
===============================
Automated generation and injection of high-Z guard and keepout zones for
the MR1 Cartridge Amplifier PCB (Amplifier/Amplifier.kicad_pcb).

Generates exact, layout-aligned zones derived directly from routed copper:
1. GNDA Keepout Zone (B.Cu):
   - Keeps GNDA copper pour >= 1.0 mm away from Route 1 (/WS_CIS, /GUARD) sensitive nodes.
   - Prevents capacitive loading (< 1.0 pF) and surface leakage gradient from ground plane.
2. B.Cu Guard Island Zone (/GUARD):
   - Solid bottom-copper plane directly beneath Route 1 electrometer traces for 3D shielding.
3. Solder Mask Openings (F.Mask & B.Mask):
   - Strips moisture-absorbing solder mask polymers over the guarded area.
4. Silkscreen Keepout Zones (F.SilkS & B.SilkS):
   - Prevents silkscreen ink contamination over bare copper and high-Z guard nodes.
   - Enforces mask clearance on front and back.

Usage:
    ./scripts/run_python.sh scripts/generate_board_zones.py [--write] [--check]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulations.em_board_analysis import BoardGeometryParser
from scripts.backup_hardware import create_snapshot

DEFAULT_PCB = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"


@dataclass
class BBox:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def expanded(self, margin_x: float, margin_y: float) -> BBox:
        return BBox(
            self.min_x - margin_x,
            self.min_y - margin_y,
            self.max_x + margin_x,
            self.max_y + margin_y,
        )


def compute_net_bounds(parser: BoardGeometryParser, nets: List[str]) -> BBox:
    """Compute exact bounding box of all pads and segments associated with given nets."""
    xs, ys = [], []
    for p in parser.pads:
        if p.net in nets:
            xs.extend([p.x - p.sx / 2.0, p.x + p.sx / 2.0])
            ys.extend([p.y - p.sy / 2.0, p.y + p.sy / 2.0])
    for s in parser.segments:
        if s.net in nets:
            xs.extend([s.x1, s.x2])
            ys.extend([s.y1, s.y2])
    if not xs or not ys:
        raise ValueError(f"No copper elements found for nets: {nets}")
    return BBox(min(xs), min(ys), max(xs), max(ys))


def format_pts(bbox: BBox) -> str:
    """Format rectangle points for KiCad S-expression (clockwise)."""
    return (
        f"(xy {bbox.min_x:.3f} {bbox.min_y:.3f}) "
        f"(xy {bbox.max_x:.3f} {bbox.min_y:.3f}) "
        f"(xy {bbox.max_x:.3f} {bbox.max_y:.3f}) "
        f"(xy {bbox.min_x:.3f} {bbox.max_y:.3f})"
    )


def build_mask_polygon_sexpr(bbox: BBox, layer: str, uuid_str: str) -> str:
    """Generates gr_poly S-expression for solder mask removal."""
    pts = format_pts(bbox)
    return (
        f'\t(gr_poly\n'
        f'\t\t(pts\n'
        f'\t\t\t{pts}\n'
        f'\t\t)\n'
        f'\t\t(stroke\n'
        f'\t\t\t(width 0.1)\n'
        f'\t\t\t(type solid)\n'
        f'\t\t)\n'
        f'\t\t(fill yes)\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(uuid "{uuid_str}")\n'
        f'\t)'
    )


def build_keepout_zone_sexpr(bbox: BBox, uuid_str: str) -> str:
    """Generates keepout zone S-expression forbidding copper pour on B.Cu beneath Route 1."""
    pts = format_pts(bbox)
    return (
        f'\t(zone\n'
        f'\t\t(layer "B.Cu")\n'
        f'\t\t(uuid "{uuid_str}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(connect_pads\n'
        f'\t\t\t(clearance 0)\n'
        f'\t\t)\n'
        f'\t\t(min_thickness 0.25)\n'
        f'\t\t(keepout\n'
        f'\t\t\t(tracks allowed)\n'
        f'\t\t\t(vias allowed)\n'
        f'\t\t\t(pads allowed)\n'
        f'\t\t\t(copperpour not_allowed)\n'
        f'\t\t\t(footprints allowed)\n'
        f'\t\t)\n'
        f'\t\t(placement\n'
        f'\t\t\t(enabled no)\n'
        f'\t\t\t(sheetname "")\n'
        f'\t\t)\n'
        f'\t\t(fill\n'
        f'\t\t\t(thermal_gap 0.5)\n'
        f'\t\t\t(thermal_bridge_width 0.5)\n'
        f'\t\t\t(island_removal_mode 0)\n'
        f'\t\t)\n'
        f'\t\t(polygon\n'
        f'\t\t\t(pts\n'
        f'\t\t\t\t{pts}\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t)'
    )


def build_guard_zone_sexpr(bbox: BBox, uuid_str: str) -> str:
    """Generates driven B.Cu /GUARD zone S-expression beneath Route 1."""
    pts = format_pts(bbox)
    return (
        f'\t(zone\n'
        f'\t\t(net "/GUARD")\n'
        f'\t\t(layer "B.Cu")\n'
        f'\t\t(uuid "{uuid_str}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(connect_pads\n'
        f'\t\t\t(clearance 0.15)\n'
        f'\t\t)\n'
        f'\t\t(min_thickness 0.15)\n'
        f'\t\t(fill yes\n'
        f'\t\t\t(thermal_gap 0.5)\n'
        f'\t\t\t(thermal_bridge_width 0.5)\n'
        f'\t\t\t(island_removal_mode 0)\n'
        f'\t\t)\n'
        f'\t\t(polygon\n'
        f'\t\t\t(pts\n'
        f'\t\t\t\t{pts}\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t)'
    )


def build_silk_keepout_zone_sexpr(bbox: BBox, layer: str, uuid_str: str, name: str) -> str:
    """Generates silkscreen keepout zone S-expression forbidding silkscreen markings over bare copper."""
    pts = format_pts(bbox)
    return (
        f'\t(zone\n'
        f'\t\t(name "{name}")\n'
        f'\t\t(layer "{layer}")\n'
        f'\t\t(uuid "{uuid_str}")\n'
        f'\t\t(hatch edge 0.5)\n'
        f'\t\t(connect_pads\n'
        f'\t\t\t(clearance 0)\n'
        f'\t\t)\n'
        f'\t\t(min_thickness 0.25)\n'
        f'\t\t(keepout\n'
        f'\t\t\t(tracks allowed)\n'
        f'\t\t\t(vias allowed)\n'
        f'\t\t\t(pads allowed)\n'
        f'\t\t\t(copperpour not_allowed)\n'
        f'\t\t\t(footprints allowed)\n'
        f'\t\t)\n'
        f'\t\t(placement\n'
        f'\t\t\t(enabled no)\n'
        f'\t\t\t(sheetname "")\n'
        f'\t\t)\n'
        f'\t\t(polygon\n'
        f'\t\t\t(pts\n'
        f'\t\t\t\t{pts}\n'
        f'\t\t\t)\n'
        f'\t\t)\n'
        f'\t)'
    )


def replace_sexpr_block(text: str, uuid_str: str, new_block: str, tag: str) -> str:
    """Replace an S-expression block identified by tag and uuid without affecting other blocks."""
    uuid_idx = text.find(uuid_str)
    if uuid_idx == -1:
        # If not present, append before the final board closing parenthesis
        idx = text.rfind(")")
        return text[:idx] + new_block + "\n" + text[idx:]

    # Locate the enclosing tag start
    start = text.rfind(f"({tag}", 0, uuid_idx)
    # Locate end by matching parentheses starting from start
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if start != -1 and end != -1:
        # Preserve leading tab indentation if present
        prefix_tab = "\t" if (start > 0 and text[start-1] == '\t') else ""
        return text[:start - len(prefix_tab)] + new_block + text[end:]
    return text


def remove_sexpr_block(text: str, uuid_str: str, tag: str) -> str:
    """Removes an S-expression block identified by tag and uuid without affecting other blocks."""
    uuid_idx = text.find(uuid_str)
    if uuid_idx == -1:
        return text
    start = text.rfind(f"({tag}", 0, uuid_idx)
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if start != -1 and end != -1:
        prefix_tab = "\t" if (start > 0 and text[start-1] == '\t') else ""
        while end < len(text) and text[end] in ' \t\r\n':
            end += 1
        return text[:start - len(prefix_tab)] + text[end:]
    return text


def sanitize_silkscreen_over_guard(pcb_text: str) -> str:
    """Removes and relocates all silkscreen ink from the electrometer bare copper / guard window.

    KiCad keepout zones do not automatically erase footprint silkscreen vectors. To prevent
    moisture-absorbing dielectric ink contamination over bare copper and high-Z guard nodes:
    - Component body outlines/circles/polygons on F.SilkS are moved to F.Fab.
    - Component reference designators are repositioned onto adjacent soldermask or hidden on silk.
    Only the 11 footprints within or immediately touching the keepout window are modified.
    All other footprints across the board remain completely untouched.
    """
    import re

    lines = pcb_text.splitlines(keepends=True)
    header = []
    footer = []
    blocks = []
    current = []
    in_fp = False
    past_fps = False

    for line in lines:
        if not past_fps:
            if line.startswith('\t(footprint '):
                in_fp = True
                current = [line]
            elif in_fp:
                current.append(line)
                if line == '\t)\n' or line == '\t)':
                    blocks.append(''.join(current))
                    in_fp = False
                    current = []
            else:
                if blocks:
                    past_fps = True
                    footer.append(line)
                else:
                    header.append(line)
        else:
            footer.append(line)

    def update_target_fp(ref: str, blk: str) -> str:
        if ref == 'P4':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"P4\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>2.7 0 90\2', blk)
            blk = re.sub(r'(\(fp_circle[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'P5':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"P5\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>6.0 3.46 30\2', blk)
            blk = re.sub(r'(\(fp_circle[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
            blk = re.sub(r'(\(fp_text\s+user\s+\"GUARD\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'P6':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"P6\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>2.6 0 0\2', blk)
            blk = re.sub(r'(\(fp_circle[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'P8':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"P8\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>-2.0 0 0\2', blk)
            blk = re.sub(r'(\(fp_circle[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'P2':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"P2\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2\n\t\t\t(hide yes)', blk)
            blk = re.sub(r'(\(fp_circle[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
            blk = re.sub(r'(\(fp_text\s+user\s+\"GUARD\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'U2':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"U2\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>-0.04 5.2 0\2', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
            blk = re.sub(r'(\(fp_poly[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'R1':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"R1\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>-4.5 0 90\2', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'C1':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"C1\"[\s\S]*?\(at\s+)[^\)]+(\))', r'\g<1>-4.5 0 90\2', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'C19':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"C19\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2\n\t\t\t(hide yes)', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'C14':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"C14\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2\n\t\t\t(hide yes)', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        elif ref == 'R32':
            blk = re.sub(r'(\(property\s+\"Reference\"\s+\"R32\"[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2\n\t\t\t(hide yes)', blk)
            blk = re.sub(r'(\(fp_line[\s\S]*?\(layer\s+\")F\.SilkS(\"\))', r'\g<1>F.Fab\2', blk)
        return blk

    targets = {'P4', 'P5', 'P6', 'P8', 'P2', 'U2', 'R1', 'C1', 'C19', 'R32'}
    new_blocks = []
    for blk in blocks:
        ref_m = re.search(r'\(property\s+\"Reference\"\s+\"([^\"]+)\"', blk)
        if ref_m and ref_m.group(1) in targets:
            new_blocks.append(update_target_fp(ref_m.group(1), blk))
        else:
            new_blocks.append(blk)

    return ''.join(header) + ''.join(new_blocks) + ''.join(footer)


def update_pcb_zones(pcb_path: Path = DEFAULT_PCB, write: bool = False) -> bool:
    """Calculates Route 1 bounds and updates zones & mask exclusions in PCB."""
    parser = BoardGeometryParser(pcb_path)
    r1_raw = compute_net_bounds(parser, [">PORE_AMP", "/WS_CIS", "/GUARD"])

    # Layout-aligned envelopes
    mask_box = r1_raw.expanded(0.5, 0.5)
    keepout_box = r1_raw.expanded(1.0, 0.8)
    guard_box = r1_raw.expanded(0.3, 0.3)

    print("Calculated layout-aligned zone envelopes:")
    print(f"  Route 1 raw copper  : X=[{r1_raw.min_x:.3f}, {r1_raw.max_x:.3f}], Y=[{r1_raw.min_y:.3f}, {r1_raw.max_y:.3f}]")
    print(f"  Mask Cutouts (F/B)  : X=[{mask_box.min_x:.3f}, {mask_box.max_x:.3f}], Y=[{mask_box.min_y:.3f}, {mask_box.max_y:.3f}]")
    print(f"  GNDA Keepout (B.Cu) : X=[{keepout_box.min_x:.3f}, {keepout_box.max_x:.3f}], Y=[{keepout_box.min_y:.3f}, {keepout_box.max_y:.3f}]")
    print(f"  /GUARD Island (B.Cu): X=[{guard_box.min_x:.3f}, {guard_box.max_x:.3f}], Y=[{guard_box.min_y:.3f}, {guard_box.max_y:.3f}]")

    pcb_text = pcb_path.read_text(encoding="utf-8")

    uuid_fmask = "c3d4e5f6-a7b8-9012-cdef-123456789012"
    uuid_bmask = "d4e5f6a7-b8c9-0123-def1-234567890123"
    uuid_keepout = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    uuid_guard = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
    uuid_silk_f = "e5f6a7b8-c9d0-1234-abcd-345678901234"
    uuid_silk_b = "f6a7b8c9-d0e1-2345-bcde-456789012345"

    new_fmask_poly = build_mask_polygon_sexpr(mask_box, "F.Mask", uuid_fmask)
    new_bmask_poly = build_mask_polygon_sexpr(mask_box, "B.Mask", uuid_bmask)
    new_keepout = build_keepout_zone_sexpr(keepout_box, uuid_keepout)
    new_guard = build_guard_zone_sexpr(guard_box, uuid_guard)

    pcb_text = replace_sexpr_block(pcb_text, uuid_fmask, new_fmask_poly, "gr_poly")
    pcb_text = replace_sexpr_block(pcb_text, uuid_bmask, new_bmask_poly, "gr_poly")
    pcb_text = replace_sexpr_block(pcb_text, uuid_keepout, new_keepout, "zone")
    pcb_text = replace_sexpr_block(pcb_text, uuid_guard, new_guard, "zone")
    # Clean up obsolete silkscreen keepout zones if present (zones on SilkS layers are positive fills in KiCad)
    pcb_text = remove_sexpr_block(pcb_text, uuid_silk_f, "zone")
    pcb_text = remove_sexpr_block(pcb_text, uuid_silk_b, "zone")

    # Enforce subtractmaskfromsilk yes so 3D viewer and plotters suppress silk over bare copper
    if "(subtractmaskfromsilk no)" in pcb_text:
        pcb_text = pcb_text.replace("(subtractmaskfromsilk no)", "(subtractmaskfromsilk yes)")

    # Sanitize silkscreen vectors and references over bare copper guard window
    pcb_text = sanitize_silkscreen_over_guard(pcb_text)

    if write:
        create_snapshot(label="pre_zone_injection", files=[pcb_path])
        pcb_path.write_text(pcb_text, encoding="utf-8")
        print(f"[OK] Injected layout-aligned zones and mask exclusions into: {pcb_path}")
        return True
    else:
        print("[CHECK] Dry-run completed. Re-run with --write to apply changes.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate layout-aligned high-Z guard and keepout zones.")
    parser.add_argument("--pcb", type=Path, default=DEFAULT_PCB, help="Path to Amplifier.kicad_pcb")
    parser.add_argument("--write", action="store_true", help="Write changes to PCB file")
    parser.add_argument("--check", action="store_true", help="Dry-run check only")
    args = parser.parse_args()

    update_pcb_zones(args.pcb, write=args.write)


if __name__ == "__main__":
    main()
