#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
generate_footprint.py
=====================
Generates the MR1 coax pogo-pin KiCad footprints from `src/stack_spec.py` (the
single source of truth for pin map, pad geometry, rings and fluid ports).

Coax convention: Pad 1 = centre signal landing pad (circle or square), Pad 2 =
concentric outer ring (GUARD, GUARD_WIDE or GNDA). Feeder pins carry no ring.

Library output (written to Amplifier/footprints.pretty and Interposer/footprints.pretty):
    PogoPin_SMT_{Circle|Square}[_{Guard|GuardWide|GNDA}]      Amplifier, F.Cu only
    PogoPin_Target_{Circle|Square}[_{Guard|GuardWide|GNDA}]   Interposer, bare ENIG pad
    PogoPin_MillMax_SMT_1Pin[_Guarded], PogoPin_Target_Landing_1Pin[_Guarded]
        (deprecated aliases still referenced by the current boards; removed in P4)
    Fluid_Overlay_DRILLS / Fluid_Overlay_SILKSCREEN_ONLY

`exports/footprints/PogoPin_Target_6Pin_Distributed.kicad_mod` (whole-board
legacy footprint, geometry still sampled from build123d) is kept only until the
board builders replace it (REFACTOR_PLAN.md, P4).

CLI:
    ./scripts/run_python.sh scripts/generate_footprint.py            # write libraries
    ./scripts/run_python.sh scripts/generate_footprint.py --check    # exit 1 on drift
    ./scripts/run_python.sh scripts/generate_footprint.py --list
    ./scripts/run_python.sh scripts/generate_footprint.py --check-cad
    ./scripts/run_python.sh scripts/generate_footprint.py --read-pcb Amplifier/Amplifier.kicad_pcb
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Ensure repository root is importable when invoked from any working directory
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build123d import GeomType  # noqa: E402
from src import stack_spec as spec  # noqa: E402
from src.common import Hex_Base_Sketch, Weep_Duct_Holes  # noqa: E402
from src.constants import HEX_DIAM, PORT_RADIUS  # noqa: E402
from src.cartridge import PTFE_Interposer  # noqa: E402


# ---------------------------------------------------------------------------
# Constants (all derived from src/stack_spec.py)
# ---------------------------------------------------------------------------

FOOTPRINT_NAME = "PogoPin_Target_6Pin_Distributed"  # legacy whole-board footprint (until P4)

FLUID_PORT_X = spec.FLUID_PORT_X
FLUID_PORT_Y = spec.FLUID_PORT_Y
FLUID_DRILL_DIA = spec.FLUID_DRILL_DIA
TARGET_PAD_DIA = spec.PAD_SIZE
TARGET_PAD_CLEARANCE = 0.4000
SMT_PAD_SIZE = spec.PAD_SIZE

HIGH_Z_NETS = set(spec.HIGH_Z_NETS)
GUARD_NETS = {"GUARD", "GUARD_WIDE"}

# (pin number, net, CAD x, CAD y, description) in P1..P12 order.
PIN_NET_SEQUENCE: List[Tuple[int, str, float, float, str]] = [
    (p.number, p.net, p.x, p.y, f"Pin {p.number}: {p.description}") for p in spec.PINS
]


def r4(val: float) -> float:
    """Round float coordinate cleanly to 4 decimal places (avoiding -0.0)."""
    rounded = round(float(val), 4)
    return 0.0 if abs(rounded) < 1e-9 else rounded


def fmt4(val: float) -> str:
    """Format a float rounded to at most 4 decimal places for S-expressions."""
    v = r4(val)
    if v == int(v):
        return f"{int(v)}.0"
    return f"{v:.4f}".rstrip("0").rstrip(".")


def deterministic_uuid(tag: str) -> str:
    """Generate a reproducible UUIDv5 for KiCad 8/9 S-expression nodes."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return str(uuid.uuid5(namespace, f"{FOOTPRINT_NAME}:{tag}"))


# ---------------------------------------------------------------------------
# Data Structures for Extracted CAD Geometry
# ---------------------------------------------------------------------------


@dataclass
class LineSegment2D:
    start: Tuple[float, float]
    end: Tuple[float, float]


@dataclass
class ArcSegment2D:
    start: Tuple[float, float]
    mid: Tuple[float, float]
    end: Tuple[float, float]
    radius: float


@dataclass
class PadSpec:
    pin_number: str
    net_name: str
    pad_type: str  # "smd" or "np_thru_hole"
    pad_shape: str  # "circle", "roundrect", "custom"
    x: float
    y: float
    size_w: float
    size_h: float
    drill: Optional[float]
    layers: List[str]
    clearance: float
    solder_mask_margin: float
    description: str
    is_primary_table_entry: bool = True
    custom_primitives: List[str] = field(default_factory=list)


@dataclass
class ConcentricElectrodeSpec:
    name: str
    center: Tuple[float, float]
    signal_pin: str
    signal_net: str
    guard_pin: str
    guard_net: str
    gnd_pin: str
    gnd_net: str
    inner_dot_dia: float
    guard_id: float
    guard_od: float
    gnd_id: float
    gnd_od: float
    mask_keepout_dia: float


@dataclass
class ExtractedCADGeometry:
    datum: Tuple[float, float]
    board_width: float
    board_height: float
    hex_lines: List[LineSegment2D]
    notch_arcs: List[ArcSegment2D]
    courtyard_vertices: List[Tuple[float, float]]
    wafer_diamond_vertices: List[Tuple[float, float]]
    fluid_holes: List[Tuple[str, float, float, float]]  # (name, x, y, drill_dia)
    weep_holes: List[Tuple[str, float, float, float]]  # (name, x, y, dia)
    pogo_pads: List[PadSpec]
    concentric_electrodes: List[ConcentricElectrodeSpec]
    channel_electrode_recesses: List[Tuple[float, float, float]]  # (x, y, radius)
    fiducials: List[Tuple[str, float, float]]


# ---------------------------------------------------------------------------
# CAD Extraction via build123d
# ---------------------------------------------------------------------------


FIDUCIALS = [
    ("FID1", -12.0, -22.0),
    ("FID2", 12.0, -22.0),
    ("FID3", 0.0, 22.0),
]


def extract_cad_geometry(
    pin_count: int = 12,
    bank: str = "trans",
    pin_positions: Optional[Dict[Union[int, str], Tuple[float, float]]] = None,
) -> ExtractedCADGeometry:
    """
    Query parametric locations, centers, radii, and outlines directly from
    the `build123d` CAD parts and sketches:
      - `Hex_Base_Sketch()` for perimeter lines and finger-grip notch arcs
      - `PTFE_Interposer()` top face inner wires for fluid manifold holes,
        wafer diamond cutout, and pogo pin targets
    Pogo pads, fluid holes and fiducials come from `src.stack_spec`. Use
    `cross_check_cad()` to verify they still agree with the CAD interposer.
      - `Weep_Duct_Holes()` for fluidic weep sense locations
    """
    # 1. Extract Board Perimeter & Internal Features from PTFE_Interposer(render_electrodes=False)
    # and Hex_Base_Sketch()
    hex_sketch = Hex_Base_Sketch()
    hex_bbox = hex_sketch.bounding_box()
    datum = (r4(hex_bbox.center().X), r4(hex_bbox.center().Y))
    board_width = r4(hex_bbox.size.X)
    board_height = r4(hex_bbox.size.Y)

    interposer_part = PTFE_Interposer(render_electrodes=False)
    top_face = max(interposer_part.faces(), key=lambda f: f.center().Z)
    bot_face = min(interposer_part.faces(), key=lambda f: f.center().Z)

    hex_lines: List[LineSegment2D] = []
    notch_arcs: List[ArcSegment2D] = []

    for edge in top_face.outer_wire().edges():
        v_start = edge.vertices()[0]
        v_end = edge.vertices()[-1]
        # Map CAD (X, Y_up) to KiCad footprint (X, Y_down)
        p_start = (r4(v_start.X), r4(-v_start.Y))
        p_end = (r4(v_end.X), r4(-v_end.Y))

        if edge.geom_type == GeomType.LINE:
            hex_lines.append(LineSegment2D(start=p_start, end=p_end))
        elif edge.geom_type == GeomType.CIRCLE:
            mid_pt = edge.position_at(0.5)
            p_mid = (r4(mid_pt.X), r4(-mid_pt.Y))
            notch_arcs.append(
                ArcSegment2D(
                    start=p_start,
                    mid=p_mid,
                    end=p_end,
                    radius=r4(edge.radius),
                )
            )

    # Compute expanded 8-vertex courtyard polygon (0.25 mm outward offset around notched hex boundary)
    crtyd_margin = 0.25
    half_w = r4(board_width / 2.0 + crtyd_margin)
    half_h = r4(board_height / 2.0 + crtyd_margin)
    top_flat_x = r4(HEX_DIAM / 4.0 + crtyd_margin * 0.5774)
    corner_y = r4(4.3301 + crtyd_margin * 0.5)
    courtyard_vertices = [
        (-top_flat_x, -half_h),
        (top_flat_x, -half_h),
        (half_w, -corner_y),
        (half_w, corner_y),
        (top_flat_x, half_h),
        (-top_flat_x, half_h),
        (-half_w, corner_y),
        (-half_w, -corner_y),
        (-top_flat_x, -half_h),
    ]

    # 2. Extract Internal Features from Top and Bottom Planar Faces
    wafer_diamond_vertices: List[Tuple[float, float]] = []
    channel_recesses: List[Tuple[float, float, float]] = []

    for wire in top_face.inner_wires():
        wbbox = wire.bounding_box()
        wcenter = wbbox.center()
        wx = r4(wcenter.X)
        wy = r4(-wcenter.Y)  # Convert CAD +Y_up to KiCad +Y_down
        wsize_x = r4(wbbox.size.X)
        wsize_y = r4(wbbox.size.Y)
        radial_dist = math.hypot(wx, wy)
        num_edges = len(wire.edges())

        # Central 45-degree rotated square wafer cutout at (0.0, 0.0)
        if abs(wx) < 0.1 and abs(wy) < 0.1 and num_edges == 4:
            for v in wire.vertices():
                wafer_diamond_vertices.append((r4(v.X), r4(-v.Y)))
        # Channel-aligned Cis electrode recesses (rotated 2x2 mm squares at r=12, 17 mm)
        elif num_edges == 4 and radial_dist > 5.0:
            channel_recesses.append((wx, wy, r4(radial_dist)))

    for wire in bot_face.inner_wires():
        wbbox = wire.bounding_box()
        wcenter = wbbox.center()
        wx = r4(wcenter.X)
        wy = r4(-wcenter.Y)
        radial_dist = math.hypot(wx, wy)
        if len(wire.edges()) == 4 and radial_dist > 5.0:
            pt_entry = (wx, wy, r4(radial_dist))
            if pt_entry not in channel_recesses:
                channel_recesses.append(pt_entry)

    # Fluid holes H1..H4 come from the spec (CAD Y up -> KiCad Y down)
    fluid_holes: List[Tuple[str, float, float, float]] = []
    for h_name, (hx, hy) in spec.FLUID_HOLES.items():
        kx, ky = spec.kicad_xy(hx, hy)
        fluid_holes.append((h_name, r4(kx), r4(ky), spec.FLUID_DRILL_DIA))

    # 3. Extract Weep Duct Sense Holes from Weep_Duct_Holes()
    weep_sketch = Weep_Duct_Holes()
    weep_holes: List[Tuple[str, float, float, float]] = []
    for idx, face in enumerate(
        sorted(weep_sketch.faces(), key=lambda f: f.bounding_box().center().X), start=1
    ):
        fbbox = face.bounding_box()
        fc = fbbox.center()
        weep_holes.append(
            (f"WEEP_{idx}", r4(fc.X), r4(-fc.Y), r4(fbbox.size.X))
        )

    # 4. Pogo pin pads from the spec (12 pins, Pad = signal landing)
    pad_dia = spec.PAD_SIZE
    pogo_pads: List[PadSpec] = []
    for pin_num, net_name, cad_x, cad_y, desc in PIN_NET_SEQUENCE:
        if pin_positions and (
            pin_num in pin_positions
            or str(pin_num) in pin_positions
            or f"P{pin_num}" in pin_positions
        ):
            override_pos = (
                pin_positions.get(pin_num)
                or pin_positions.get(str(pin_num))
                or pin_positions.get(f"P{pin_num}")
            )
            px, py = r4(override_pos[0]), r4(override_pos[1])
        else:
            kx, ky = spec.kicad_xy(cad_x, cad_y)
            px, py = r4(kx), r4(ky)

        special = net_name in HIGH_Z_NETS or net_name in GUARD_NETS
        pogo_pads.append(
            PadSpec(
                pin_number=str(pin_num),
                net_name=net_name,
                pad_type="smd",
                pad_shape="circle",
                x=px,
                y=py,
                size_w=pad_dia,
                size_h=pad_dia,
                drill=None,
                layers=["F.Cu", "F.Mask"],
                clearance=TARGET_PAD_CLEARANCE,
                solder_mask_margin=0.100 if special else 0.050,
                description=desc,
                is_primary_table_entry=True,
            )
        )

    concentric_electrodes: List[ConcentricElectrodeSpec] = []

    fiducials = list(FIDUCIALS)

    return ExtractedCADGeometry(
        datum=datum,
        board_width=board_width,
        board_height=board_height,
        hex_lines=hex_lines,
        notch_arcs=notch_arcs,
        courtyard_vertices=courtyard_vertices,
        wafer_diamond_vertices=wafer_diamond_vertices,
        fluid_holes=fluid_holes,
        weep_holes=weep_holes,
        pogo_pads=pogo_pads,
        concentric_electrodes=concentric_electrodes,
        channel_electrode_recesses=sorted(channel_recesses, key=lambda r: (r[0], r[1])),
        fiducials=fiducials,
    )



def cross_check_cad(tol: float = 0.05) -> List[str]:
    """Compare spec fluid-hole and pogo-pad centres with the build123d interposer.
    Returns a list of mismatch messages (empty = CAD agrees with the spec)."""
    problems: List[str] = []
    top_face = max(PTFE_Interposer(render_electrodes=False).faces(), key=lambda f: f.center().Z)
    fluid: List[Tuple[float, float]] = []
    pogo: List[Tuple[float, float]] = []
    for wire in top_face.inner_wires():
        c = wire.bounding_box().center()
        if len(wire.edges()) != 1:
            continue
        if any(math.hypot(c.X - hx, c.Y - hy) < 0.5 for hx, hy in spec.FLUID_HOLES.values()):
            fluid.append((c.X, c.Y))
        elif abs(wire.bounding_box().size.X / 2.0 - 1.0) < 0.2:
            pogo.append((c.X, c.Y))

    def near(pt, pts):
        return any(math.hypot(pt[0] - q[0], pt[1] - q[1]) <= tol for q in pts)

    for name, xy in spec.FLUID_HOLES.items():
        if not near(xy, fluid):
            problems.append(f"fluid hole {name} {xy} not found in CAD interposer")
    for p in spec.PINS:
        if math.hypot(p.x, p.y) < 26.0 and math.hypot(p.x, p.y) > 4.5:
            if not near((p.x, p.y), pogo):
                problems.append(f"{p.ref} ({p.x}, {p.y}) has no landing hole in CAD interposer")
    return problems


# ---------------------------------------------------------------------------
# S-expression helpers & fluid references
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Single-Pin Modular Footprint & Fluid Reference Generators
# ---------------------------------------------------------------------------


def generate_header(name: str, desc: str) -> str:
    """Generate standard KiCad 8/9 footprint header block."""
    return (
        f'(footprint "{name}"\n'
        f'  (version 20240108)\n'
        f'  (generator "generate_footprint.py")\n'
        f'  (layer "F.Cu")\n'
        f'  (descr "{desc}")\n'
        f'  (attr smd)\n'
        f'  (property "Reference" "REF**" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{name}_ref")}")\n'
        f'    (effects (font (size 1 1) (thickness 0.15)))\n'
        f'  )\n'
        f'  (property "Value" "{name}" (at 0 2.5 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{name}_val")}")\n'
        f'    (effects (font (size 0.8 0.8) (thickness 0.12)))\n'
        f'  )\n'
    )



# ---------------------------------------------------------------------------
# Coax pogo-pin footprints (Pad 1 = signal, Pad 2 = ring)
# ---------------------------------------------------------------------------

RING_SUFFIX = {None: "", spec.GUARD: "_Guard", spec.GUARD_WIDE: "_GuardWide", spec.GNDA: "_GNDA"}
STYLE_DESC = {
    "smt": "Amplifier-side SMT pad for the pogo pin (F.Cu only, component side, board mounted inverted)",
    "target": "Interposer-side bare ENIG landing pad (no paste)",
}


def coax_footprint_name(style: str, shape: str, ring: Optional[str]) -> str:
    kind = "SMT" if style == "smt" else "Target"
    return f"PogoPin_{kind}_{shape.capitalize()}{RING_SUFFIX[ring]}"


def generate_coax_footprint(
    style: str,
    shape: str = spec.CIRCLE,
    ring: Optional[str] = None,
    name: Optional[str] = None,
) -> str:
    """One coax pogo-pin footprint.

    style: "smt" (Amplifier, F.Cu + F.Paste + F.Mask) or "target" (Interposer, F.Cu + F.Mask)
    shape: "circle" or "square" signal pad (Pad 1)
    ring:  None, "GUARD", "GUARD_WIDE" or "GNDA" -> concentric ring on Pad 2 (mask-covered)
    """
    if style not in ("smt", "target"):
        raise ValueError(f"unknown style {style!r}")
    if shape not in (spec.CIRCLE, spec.SQUARE):
        raise ValueError(f"unknown shape {shape!r}")
    if ring not in RING_SUFFIX:
        raise ValueError(f"unknown ring {ring!r}")
    name = name or coax_footprint_name(style, shape, ring)
    size = spec.PAD_SIZE
    u = lambda tag: deterministic_uuid(f"{name}_{tag}")  # noqa: E731
    ring_mid = spec.RING_INNER_R + spec.RING_WIDTH / 2.0
    ring_note = f"ring {ring}" if ring else "no ring (feeder pin)"
    desc = (
        f"MR1 coax pogo pin, {shape} pad, {ring_note}. {STYLE_DESC[style]}. "
        f"Pad 1 = signal, Pad 2 = ring. Pin: {spec.POGO.part}, {spec.POGO.free_length:g} mm free / "
        f"{spec.POGO.working_height:g} mm working."
    )
    pad_layers = '"F.Cu" "F.Paste" "F.Mask"' if style == "smt" else '"F.Cu" "F.Mask"'
    shape_tok = "circle" if shape == spec.CIRCLE else "rect"

    out: List[str] = [
        f'(footprint "{name}"',
        "  (version 20240108)",
        '  (generator "generate_footprint.py")',
        '  (layer "F.Cu")',
        f'  (descr "{desc}")',
        f'  (tags "mr1 pogo coax {style} {shape} {ring or "plain"}")',
        f'  (property "Reference" "REF**" (at 0 -3.2 0) (layer "F.SilkS") (uuid "{u("ref")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        f'  (property "Value" "{name}" (at 0 3.2 0) (layer "F.Fab") (uuid "{u("val")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        "  (attr smd)",
        f'  (pad "1" smd {shape_tok} (at 0 0) (size {size} {size}) (layers {pad_layers}) '
        f'(clearance {TARGET_PAD_CLEARANCE}) (uuid "{u("pad1")}"))',
    ]
    if ring:
        r_out = spec.RING_OUTER_R
        out += [
            f'  (pad "2" smd custom (at {fmt4(ring_mid)} 0) (size 0.1 0.1) (layers "F.Cu")',
            "    (clearance 0.3)",
            "    (options (clearance outline) (anchor circle))",
            "    (primitives",
            f"      (gr_circle (center {fmt4(-ring_mid)} 0) (end 0 0) (width {fmt4(spec.RING_WIDTH)}) (fill none))",
            "    )",
            f'    (uuid "{u("pad2_ring")}")',
            "  )",
            f'  (fp_text user "{ring}" (at 0 {fmt4(r_out + 0.7)}) (layer "F.SilkS") (uuid "{u("txt_ring")}") '
            "(effects (font (size 0.5 0.5) (thickness 0.1))))",
            f'  (fp_circle (center 0 0) (end {fmt4(r_out + 0.3)} 0) (stroke (width 0.05) (type solid)) (fill none) '
            f'(layer "F.CrtYd") (uuid "{u("crtyd")}"))',
        ]
    else:
        out.append(
            f'  (fp_circle (center 0 0) (end {fmt4(size / 2 + 0.5)} 0) (stroke (width 0.05) (type solid)) (fill none) '
            f'(layer "F.CrtYd") (uuid "{u("crtyd")}"))'
        )
    out.append(")")
    return "\n".join(out) + "\n"


# Deprecated 1-pin names still referenced by the current boards -> new coax equivalent.
LEGACY_ALIASES: Dict[str, Tuple[str, str, Optional[str]]] = {
    "PogoPin_MillMax_SMT_1Pin": ("smt", spec.CIRCLE, None),
    "PogoPin_MillMax_SMT_1Pin_Guarded": ("smt", spec.CIRCLE, spec.GUARD),
    "PogoPin_Target_Landing_1Pin": ("target", spec.CIRCLE, None),
    "PogoPin_Target_Landing_1Pin_Guarded": ("target", spec.CIRCLE, spec.GUARD),
}


def generate_single_pin_footprint(
    name: str,
    pin_type: str = "target",
    guarded: bool = False,
    layer: str = "F.Cu",
) -> str:
    """Compatibility generator for single pin landing and pogo footprints."""
    shape = spec.CIRCLE
    ring = spec.GUARD if guarded else None
    style = "smt" if "smt" in pin_type.lower() else "target"
    return generate_coax_footprint(style, shape=shape, ring=ring, name=name)


def pin_footprint_name(p: "spec.PinSpec", style: str) -> str:
    """Library footprint a given spec pin should use on the Amplifier (smt) or Interposer (target)."""
    return coax_footprint_name(style, p.shape, p.ring)

def generate_fluid_references(fluid_mode: str = "silkscreen_only", layer: str = "F") -> str:
    """Generates fluid port markers and flow channel references for Amplifier vs Interposer."""
    lines = []
    ports = [
        ("H1", -FLUID_PORT_X, FLUID_PORT_Y),
        ("H2", FLUID_PORT_X, -FLUID_PORT_Y),
        ("H3", -FLUID_PORT_X, -FLUID_PORT_Y),
        ("H4", FLUID_PORT_X, FLUID_PORT_Y),
    ]
    silk_layer = f"{layer}.SilkS"

    for name, x, y in ports:
        if fluid_mode == "drills":
            lines.append(
                f'  (pad "{name}" np_thru_hole circle (at {x:.4f} {y:.4f}) '
                f'(size {FLUID_DRILL_DIA} {FLUID_DRILL_DIA}) (drill {FLUID_DRILL_DIA}) (layers "*.Cu" "*.Mask") (uuid "{deterministic_uuid(f"fluid_pad_{name}")}"))\n'
            )
            lines.append(
                f'  (fp_text user "{name}" (at {x:.4f} {y+1.8:.4f} 0) (layer "{silk_layer}") (uuid "{deterministic_uuid(f"fluid_txt_{name}")}") (effects (font (size 0.7 0.7) (thickness 0.12))))\n'
            )
        else:
            # Silkscreen reference circle and crosshair
            lines.append(
                f'  (fp_circle (center {x:.4f} {y:.4f}) (end {x:.4f} {y + FLUID_DRILL_DIA/2.0:.4f}) (stroke (width 0.15) (type solid)) (fill none) (layer "{silk_layer}") (uuid "{deterministic_uuid(f"fluid_silk_circ_{name}")}"))\n'
            )
            lines.append(
                f'  (fp_line (start {x-1.5:.4f} {y:.4f}) (end {x+1.5:.4f} {y:.4f}) (stroke (width 0.12) (type solid)) (layer "{silk_layer}") (uuid "{deterministic_uuid(f"fluid_silk_h_{name}")}"))\n'
            )
            lines.append(
                f'  (fp_line (start {x:.4f} {y-1.5:.4f}) (end {x:.4f} {y+1.5:.4f}) (stroke (width 0.12) (type solid)) (layer "{silk_layer}") (uuid "{deterministic_uuid(f"fluid_silk_v_{name}")}"))\n'
            )
            lines.append(
                f'  (fp_text user "REF_{name}" (at {x:.4f} {y+1.8:.4f} 0) (layer "{silk_layer}") (uuid "{deterministic_uuid(f"fluid_txt_{name}")}") (effects (font (size 0.7 0.7) (thickness 0.12))))\n'
            )

    # Draw Flow Channel Paths on Silk:
    # Cis channel: H1 (-17.3205, 10.0) -> H2 (17.3205, -10.0)
    lines.append(
        f'  (fp_line (start -17.3205 10.0) (end 17.3205 -10.0) (stroke (width 0.15) (type dash)) (layer "{silk_layer}") (uuid "{deterministic_uuid("fluid_channel_cis")}"))\n'
    )
    lines.append(
        f'  (fp_text user "CIS FLOW (H1 -> H2)" (at -5.0 4.0 330) (layer "{silk_layer}") (uuid "{deterministic_uuid("fluid_channel_cis_label")}") (effects (font (size 0.7 0.7) (thickness 0.11))))\n'
    )

    # Trans channel: H3 (-17.3205, -10.0) -> H4 (17.3205, 10.0)
    lines.append(
        f'  (fp_line (start -17.3205 -10.0) (end 17.3205 10.0) (stroke (width 0.15) (type dash)) (layer "{silk_layer}") (uuid "{deterministic_uuid("fluid_channel_trans")}"))\n'
    )
    lines.append(
        f'  (fp_text user "TRANS FLOW (H3 -> H4)" (at -5.0 -4.0 30) (layer "{silk_layer}") (uuid "{deterministic_uuid("fluid_channel_trans_label")}") (effects (font (size 0.7 0.7) (thickness 0.11))))\n'
    )
    return "".join(lines)


def _parse_sexpr(text: str):
    """Minimal S-expression parser (strings, atoms, nested lists)."""
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+', text)
    pos = 0

    def parse():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            node = []
            while tokens[pos] != ")":
                node.append(parse())
            pos += 1
            return node
        if tok.startswith('"'):
            return ("str", tok[1:-1])
        return tok

    return parse()


def extract_pin_placements_from_pcb(
    pcb_path: Union[str, Path], pattern: str = r"P\d+"
) -> Dict[str, Dict[str, object]]:
    """Parse a KiCad 7+ `.kicad_pcb` and return every footprint whose reference
    matches `pattern`: {ref: {"x", "y", "rot", "layer", "footprint"}} in KiCad
    board coordinates. Handles KiCad 8+ `(property "Reference" ...)` and flip."""
    p_path = Path(pcb_path)
    if not p_path.is_file():
        raise FileNotFoundError(f"PCB file not found: {pcb_path}")
    tree = _parse_sexpr(p_path.read_text(encoding="utf-8"))
    rx = re.compile(pattern)
    found: Dict[str, Dict[str, object]] = {}

    def text(n):
        return n[1] if isinstance(n, tuple) else n

    for node in tree[1:]:
        if not (isinstance(node, list) and node and node[0] == "footprint"):
            continue
        ref = None
        at = None
        layer = "F.Cu"
        for child in node[2:]:
            if not isinstance(child, list) or not child:
                continue
            head = child[0]
            if head == "at" and at is None:
                at = [float(c) for c in child[1:]]
            elif head == "layer":
                layer = text(child[1])
            elif head == "property" and len(child) > 2 and text(child[1]) == "Reference":
                ref = text(child[2])
            elif head == "fp_text" and len(child) > 2 and child[1] == "reference":
                ref = text(child[2])
        if ref and at and rx.fullmatch(ref):
            found[ref] = {
                "x": at[0],
                "y": at[1],
                "rot": at[2] if len(at) > 2 else 0.0,
                "layer": layer,
                "footprint": text(node[1]),
            }
    return found


def extract_pin_positions_from_pcb(
    pcb_path: Union[str, Path], prefix: str = "P"
) -> Dict[str, Tuple[float, float]]:
    """Back-compat wrapper: {ref: (x, y)} for refs like P1, P2, ..."""
    placements = extract_pin_placements_from_pcb(pcb_path, pattern=prefix + r"\d+")
    return {ref: (v["x"], v["y"]) for ref, v in placements.items()}  # type: ignore[misc]

# ---------------------------------------------------------------------------
# KiCad 8/9 S-Expression Generator
# ---------------------------------------------------------------------------


def generate_kicad_footprint(
    geom: ExtractedCADGeometry,
    footprint_name: Optional[str] = None,
    fluid_mode: str = "drills",
) -> str:
    """
    Render the extracted `build123d` CAD geometry into a syntactically pristine
    KiCad 8/9 `.kicad_mod` S-expression string.
    """
    fp_name = footprint_name or FOOTPRINT_NAME
    is_6pin = len(geom.pogo_pads) == 6
    lines: List[str] = []

    # Header & Metadata
    lines.append(
        f'(footprint "{fp_name}" (version 20240108) (generator "generate_footprint.py")'
    )
    lines.append('  (layer "F.Cu")')
    if is_6pin:
        lines.append(
            '  (descr "6-Pin Mill-Max 09xx Bias-Tail/Ball-Contact Bare ENIG/Hard Gold Pogo Target + Dual-Seal PDMS Weep Moat + Rigid Anvil Clamp (50-100kHz Sub-pA Nanopore)")'
        )
        lines.append(
            '  (tags "pogo target 6-pin mill-max 09xx bias-tail ball-contact enig guard weep-moat anvil build123d")'
        )
    else:
        lines.append(
            '  (descr "Dual 6-Pin (6 Cis + 6 Trans) Mill-Max 09xx Bias-Tail/Ball-Contact Bare ENIG/Hard Gold Pogo Target + 4x 2.1mm Fluid Pass-Throughs + Dual-Seal PDMS Weep Moats + Rigid Anvil Clamps")'
        )
        lines.append(
            '  (tags "pogo target 6-pin cis trans mill-max 09xx bias-tail ball-contact interposer nanopore guard concentric fluidic build123d")'
        )

    # Required KiCad 8/9 Library Properties
    lines.append('  (property "Reference" "REF**"')
    lines.append("    (at 0.0 -27.5 0)")
    lines.append('    (layer "F.SilkS")')
    lines.append(f'    (uuid "{deterministic_uuid(f"{fp_name}_prop_ref")}")')
    lines.append("    (effects (font (size 1 1) (thickness 0.15)))")
    lines.append("  )")

    lines.append(f'  (property "Value" "{fp_name}"')
    lines.append("    (at 0.0 27.5 0)")
    lines.append('    (layer "F.Fab")')
    lines.append(f'    (uuid "{deterministic_uuid(f"{fp_name}_prop_val")}")')
    lines.append("    (effects (font (size 1 1) (thickness 0.15)))")
    lines.append("  )")

    lines.append(
        '  (property "Datasheet" "https://www.mill-max.com/products/new/spring-loaded-pogo-pins"'
    )
    lines.append("    (at 0.0 29.0 0)")
    lines.append("    (unlocked yes)")
    lines.append('    (layer "F.Fab")')
    lines.append("    (hide yes)")
    lines.append(f'    (uuid "{deterministic_uuid(f"{fp_name}_prop_ds")}")')
    lines.append("    (effects (font (size 1 1) (thickness 0.15)))")
    lines.append("  )")

    desc_prop = (
        "6-Pin Bare Unmasked ENIG/Hard Gold Pogo Target for Mill-Max 09xx Bias-Tail/Ball-Contact Pins, Dual-Seal PDMS Weep Moat & Rigid Anvil Support"
        if is_6pin
        else "Dual 6-Pin (6 Cis at Y=-15mm + 6 Trans at Y=+15mm) Bare ENIG/Hard Gold Pogo Target for Mill-Max 09xx Bias-Tail/Ball-Contact Pins with 4x 2.1mm Fluid Pass-Throughs, Dual-Seal PDMS Weep Moats, and Rigid Anvil Clamps"
    )
    lines.append(f'  (property "Description" "{desc_prop}"')
    lines.append("    (at 0.0 30.5 0)")
    lines.append("    (unlocked yes)")
    lines.append('    (layer "F.Fab")')
    lines.append("    (hide yes)")
    lines.append(f'    (uuid "{deterministic_uuid(f"{fp_name}_prop_desc")}")')
    lines.append("    (effects (font (size 1 1) (thickness 0.15)))")
    lines.append("  )")

    lines.append("  (attr smd)")
    lines.append("  ( clearance 0.25 )")

    # -----------------------------------------------------------------------
    # 1. Board Perimeter / Outline on Edge.Cuts, F.Fab, F.SilkS + Courtyard
    # -----------------------------------------------------------------------
    for idx, seg in enumerate(geom.hex_lines):
        sx, sy = fmt4(seg.start[0]), fmt4(seg.start[1])
        ex, ey = fmt4(seg.end[0]), fmt4(seg.end[1])
        lines.append(
            f'  (fp_line (start {sx} {sy}) (end {ex} {ey}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{deterministic_uuid(f"edge_hex_{idx}")}"))'
        )
        lines.append(
            f'  (fp_line (start {sx} {sy}) (end {ex} {ey}) (stroke (width 0.12) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"fab_hex_{idx}")}"))'
        )
        lines.append(
            f'  (fp_line (start {sx} {sy}) (end {ex} {ey}) (stroke (width 0.12) (type dash)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"silk_hex_{idx}")}"))'
        )

    for idx, arc in enumerate(geom.notch_arcs):
        sx, sy = fmt4(arc.start[0]), fmt4(arc.start[1])
        mx, my = fmt4(arc.mid[0]), fmt4(arc.mid[1])
        ex, ey = fmt4(arc.end[0]), fmt4(arc.end[1])
        lines.append(
            f'  (fp_arc (start {sx} {sy}) (mid {mx} {my}) (end {ex} {ey}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{deterministic_uuid(f"edge_arc_{idx}")}"))'
        )
        lines.append(
            f'  (fp_arc (start {sx} {sy}) (mid {mx} {my}) (end {ex} {ey}) (stroke (width 0.12) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"fab_arc_{idx}")}"))'
        )
        lines.append(
            f'  (fp_arc (start {sx} {sy}) (mid {mx} {my}) (end {ex} {ey}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"silk_arc_{idx}")}"))'
        )

    # Courtyard boundary on F.CrtYd
    for idx in range(len(geom.courtyard_vertices) - 1):
        p1 = geom.courtyard_vertices[idx]
        p2 = geom.courtyard_vertices[idx + 1]
        lines.append(
            f'  (fp_line (start {fmt4(p1[0])} {fmt4(p1[1])}) (end {fmt4(p2[0])} {fmt4(p2[1])}) (stroke (width 0.05) (type solid)) (layer "F.CrtYd") (uuid "{deterministic_uuid(f"crtyd_{idx}")}"))'
        )

    # Datum anchor crosshair at (0.0, 0.0) on F.Fab
    lines.append(
        f'  (fp_line (start -1.0 0.0) (end 1.0 0.0) (stroke (width 0.1) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid("datum_x")}"))'
    )
    lines.append(
        f'  (fp_line (start 0.0 -1.0) (end 0.0 1.0) (stroke (width 0.1) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid("datum_y")}"))'
    )

    # Central 6.20 x 6.20 mm 45-deg rotated diamond wafer aperture on Edge.Cuts, F.Fab & F.SilkS
    if len(geom.wafer_diamond_vertices) == 4:
        ordered_v = sorted(
            geom.wafer_diamond_vertices, key=lambda pt: math.atan2(pt[1], pt[0])
        )
        for idx in range(4):
            v1 = ordered_v[idx]
            v2 = ordered_v[(idx + 1) % 4]
            lines.append(
                f'  (fp_line (start {fmt4(v1[0])} {fmt4(v1[1])}) (end {fmt4(v2[0])} {fmt4(v2[1])}) (stroke (width 0.15) (type solid)) (layer "Edge.Cuts") (uuid "{deterministic_uuid(f"wafer_edge_{idx}")}"))'
            )
            lines.append(
                f'  (fp_line (start {fmt4(v1[0])} {fmt4(v1[1])}) (end {fmt4(v2[0])} {fmt4(v2[1])}) (stroke (width 0.12) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"wafer_fab_{idx}")}"))'
            )
            lines.append(
                f'  (fp_line (start {fmt4(v1[0])} {fmt4(v1[1])}) (end {fmt4(v2[0])} {fmt4(v2[1])}) (stroke (width 0.12) (type dot)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"wafer_silk_{idx}")}"))'
            )

    # Optical Alignment Fiducial Markings on F.SilkS and F.Fab
    for fid_name, fx, fy in geom.fiducials:
        lines.append(
            f'  (fp_circle (center {fmt4(fx)} {fmt4(fy)}) (end {fmt4(fx + 0.5)} {fmt4(fy)}) (stroke (width 0.15) (type solid)) (fill none) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fid_name}_fab")}"))'
        )
        lines.append(
            f'  (fp_circle (center {fmt4(fx)} {fmt4(fy)}) (end {fmt4(fx + 1.0)} {fmt4(fy)}) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fid_name}_silk")}"))'
        )
        lines.append(
            f'  (fp_text user "{fid_name}" (at {fmt4(fx)} {fmt4(fy - 1.6)} 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fid_name}_txt")}") (effects (font (size 0.7 0.7) (thickness 0.12))))'
        )

    # Determine active Y-perimeters present in this footprint ([-15.0] Cis, [+15.0] Trans, or both)
    active_y_banks = sorted({pad.y for pad in geom.pogo_pads})
    for y_bank in active_y_banks:
        bank_tag = "cis" if y_bank < 0 else "trans"
        bank_label = "CIS 6-PIN BANK (J_POGO_CIS)" if y_bank < 0 else "TRANS 6-PIN BANK (J_POGO_TRANS)"
        sign = -1.0 if y_bank < 0 else 1.0

        # High-Z Pogo Array Enclosure Box on F.SilkS & F.CrtYd (Bone-Dry Outer Cavity)
        y_box_in = fmt4(y_bank - 2.0)
        y_box_out = fmt4(y_bank + 2.0)
        y_crt_in = fmt4(y_bank - 2.5)
        y_crt_out = fmt4(y_bank + 2.5)
        lines.append(
            f'  (fp_rect (start -13.5 {y_box_in}) (end 13.5 {y_box_out}) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_pogo_silk_box")}"))'
        )
        lines.append(
            f'  (fp_rect (start -14.0 {y_crt_in}) (end 14.0 {y_crt_out}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_pogo_crtyd_box")}"))'
        )

        # Dual-Perimeter Cast PDMS Gasket Seal & Atmospheric Weep Moat Barrier (Fluid Isolation)
        y_seal_inner = fmt4(sign * 11.2)
        y_moat = fmt4(sign * 11.8)
        y_seal_outer = fmt4(sign * 12.4)
        y_moat_txt = fmt4(sign * 10.6)
        lines.append(
            f'  (fp_line (start -16.0 {y_seal_inner}) (end 16.0 {y_seal_inner}) (stroke (width 0.15) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_pdms_inner_seal")}"))'
        )
        lines.append(
            f'  (fp_line (start -16.0 {y_moat}) (end 16.0 {y_moat}) (stroke (width 0.12) (type dash)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_weep_moat_trench")}"))'
        )
        lines.append(
            f'  (fp_line (start -16.0 {y_seal_outer}) (end 16.0 {y_seal_outer}) (stroke (width 0.15) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_pdms_outer_seal")}"))'
        )
        lines.append(
            f'  (fp_text user "{bank_label}: DUAL-PERIMETER PDMS SEAL + ATMOSPHERIC WEEP MOAT" (at 0.0 {y_moat_txt} 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_txt_weep_moat")}") (effects (font (size 0.55 0.55) (thickness 0.1))))'
        )

        # Rigid Bottom Clamp Block / Backing Anvil Reaction Zone (Delrin / Al / Acrylic Creep Neutralization)
        y_anvil_1 = fmt4(y_bank - 2.4)
        y_anvil_2 = fmt4(y_bank + 2.4)
        y_anvil_txt = fmt4(y_bank + sign * 3.2)
        lines.append(
            f'  (fp_rect (start -14.5 {y_anvil_1}) (end 14.5 {y_anvil_2}) (stroke (width 0.12) (type dot)) (fill none) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_rigid_anvil_zone")}"))'
        )
        lines.append(
            f'  (fp_text user "{bank_label}: RIGID ANVIL CLAMP ZONE (DELRIN/AL CREEP NEUTRALIZATION)" (at 0.0 {y_anvil_txt} 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{fp_name}_{bank_tag}_txt_anvil")}") (effects (font (size 0.55 0.55) (thickness 0.1))))'
        )

        if y_bank < 0:
            # Cis 6-pin guard envelopes around >PORE_AMP (-6.5, -15.0) and WEEP_SENSE (11.5, -15.0)
            lines.append(
                f'  (fp_rect (start -12.8 -16.6) (end 0.2 -13.4) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_cis_pore_guard_env")}"))'
            )
            lines.append(
                f'  (fp_rect (start 5.2 -16.6) (end 12.8 -13.4) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_cis_weep_guard_env")}"))'
            )
        else:
            # Trans 6-pin guard envelopes around GUARD_WIDE/WS_CIS_WIDE (-1.5..+1.5) and GUARD/WS_CIS (+6.5..+11.5)
            lines.append(
                f'  (fp_rect (start -2.8 13.4) (end 2.8 16.6) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_trans_wide_guard_env")}"))'
            )
            lines.append(
                f'  (fp_rect (start 5.2 13.4) (end 12.8 16.6) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{fp_name}_trans_wscis_guard_env")}"))'
            )

    # Concentric Electrode Soldermask Expansion Keepouts & Silkscreen Annotations
    for ce in geom.concentric_electrodes:
        cx, cy = ce.center
        mask_r = r4(ce.mask_keepout_dia / 2.0)
        guard_mid_r = r4((ce.guard_id + ce.guard_od) / 4.0)
        gnd_mid_r = r4((ce.gnd_id + ce.gnd_od) / 4.0)

        # Soldermask expansion circle (exposes bare gold/copper guard ring to elastomer)
        lines.append(
            f'  (fp_circle (center {fmt4(cx)} {fmt4(cy)}) (end {fmt4(cx + mask_r)} {fmt4(cy)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Mask") (uuid "{deterministic_uuid(f"{ce.name}_mask")}"))'
        )
        # Silkscreen concentric target rings
        lines.append(
            f'  (fp_circle (center {fmt4(cx)} {fmt4(cy)}) (end {fmt4(cx + guard_mid_r)} {fmt4(cy)}) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{ce.name}_silk_guard")}"))'
        )
        lines.append(
            f'  (fp_circle (center {fmt4(cx)} {fmt4(cy)}) (end {fmt4(cx + gnd_mid_r)} {fmt4(cy)}) (stroke (width 0.12) (type dot)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{ce.name}_silk_gnd")}"))'
        )
        lines.append(
            f'  (fp_text user "{ce.name}" (at {fmt4(cx)} {fmt4(cy - 3.8)} 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{ce.name}_label")}") (effects (font (size 0.6 0.6) (thickness 0.1))))'
        )

    # Channel-aligned Ag/AgCl Electrode_Guard_Shield boundary annotations on F.Fab
    for idx, (rx, ry, r_dist) in enumerate(geom.channel_electrode_recesses, start=1):
        lines.append(
            f'  (fp_circle (center {fmt4(rx)} {fmt4(ry)}) (end {fmt4(rx + 1.0)} {fmt4(ry)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab") (uuid "{deterministic_uuid(f"agcl_recess_{idx}")}"))'
        )

    # Silkscreen Net Labels for the Pogo Pin Targets
    for pad in geom.pogo_pads:
        lbl_y = pad.y - 2.4 if pad.y < 0 else pad.y + 2.4
        lines.append(
            f'  (fp_text user "{pad.pin_number}:{pad.net_name}" (at {fmt4(pad.x)} {fmt4(lbl_y)} 90) (layer "F.SilkS") (uuid "{deterministic_uuid(f"lbl_pin_{pad.pin_number}")}") (effects (font (size 0.5 0.5) (thickness 0.1))))'
        )

    # -----------------------------------------------------------------------
    # 2. Fluidic Pass-Through Holes (H1, H2, H3, H4) - Drills vs Silkscreen-Only
    # -----------------------------------------------------------------------
    for h_name, hx, hy, h_drill in geom.fluid_holes:
        r_silk = r4(h_drill / 2.0 + 0.35)
        lines.append(
            f'  (fp_circle (center {fmt4(hx)} {fmt4(hy)}) (end {fmt4(hx + r_silk)} {fmt4(hy)}) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_silk_{h_name}")}"))'
        )
        lines.append(
            f'  (fp_text user "{h_name}" (at {fmt4(hx)} {fmt4(hy - 1.8)} 0) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_txt_{h_name}")}") (effects (font (size 0.8 0.8) (thickness 0.15))))'
        )
        if fluid_mode == "drills":
            lines.append(
                f'  (pad "{h_name}" np_thru_hole circle (at {fmt4(hx)} {fmt4(hy)}) (size {fmt4(h_drill)} {fmt4(h_drill)}) (drill {fmt4(h_drill)}) (layers "*.Cu" "*.Mask") (uuid "{deterministic_uuid(f"pad_{h_name}")}"))'
            )
        else:
            # Silkscreen-only crosshair and reference marking for Amplifier PCB reasoning
            lines.append(
                f'  (fp_line (start {fmt4(hx - 1.5)} {fmt4(hy)}) (end {fmt4(hx + 1.5)} {fmt4(hy)}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_cross_h_{h_name}")}"))'
            )
            lines.append(
                f'  (fp_line (start {fmt4(hx)} {fmt4(hy - 1.5)}) (end {fmt4(hx)} {fmt4(hy + 1.5)}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_cross_v_{h_name}")}"))'
            )

    # -----------------------------------------------------------------------
    # 3. Distributed Pogo Pin Target Pads (Cis & Trans 6-Pin Banks)
    # -----------------------------------------------------------------------
    for pad in geom.pogo_pads:
        layers_str = " ".join(f'"{lyr}"' for lyr in pad.layers)
        lines.append(
            f'  (pad "{pad.pin_number}" {pad.pad_type} {pad.pad_shape} '
            f"(at {fmt4(pad.x)} {fmt4(pad.y)}) "
            f"(size {fmt4(pad.size_w)} {fmt4(pad.size_h)}) "
            f"(layers {layers_str}) "
            f"(clearance {fmt4(pad.clearance)}) "
            f"(solder_mask_margin {fmt4(pad.solder_mask_margin)}) "
            f'(uuid "{deterministic_uuid(f"pad_pogo_{pad.pin_number}")}"))'
        )

    # -----------------------------------------------------------------------
    # 4. High-Z Analog Shielding & Concentric Compression Electrode Guard Pads
    # -----------------------------------------------------------------------
    for ce in geom.concentric_electrodes:
        cx, cy = ce.center
        dot_d = fmt4(ce.inner_dot_dia)
        guard_r = r4((ce.guard_id + ce.guard_od) / 4.0)
        guard_w = r4((ce.guard_od - ce.guard_id) / 2.0)
        gnd_r = r4((ce.gnd_id + ce.gnd_od) / 4.0)
        gnd_w = r4((ce.gnd_od - ce.gnd_id) / 2.0)

        # Center Silver-Silicone Compression Electrode Contact Dot (F.Cu + F.Mask)
        lines.append(
            f'  (pad "{ce.signal_pin}" smd circle '
            f"(at {fmt4(cx)} {fmt4(cy)}) "
            f"(size {dot_d} {dot_d}) "
            f'(layers "F.Cu" "F.Mask") '
            f"(clearance 0.4) "
            f"(solder_mask_margin 0.1) "
            f'(uuid "{deterministic_uuid(f"{ce.name}_dot")}"))'
        )

        # Concentric Active Driven Guard Ring (Unbroken custom ring pad)
        lines.append(
            f'  (pad "{ce.guard_pin}" smd custom '
            f"(at {fmt4(cx + guard_r)} {fmt4(cy)}) "
            f"(size 0.4 0.4) "
            f'(layers "F.Cu" "F.Mask") '
            f"(clearance 0.4) "
            f"(solder_mask_margin 0.1) "
            f"(options (clearance outline) (anchor circle)) "
            f"(primitives "
            f"(gr_circle (center {fmt4(-guard_r)} 0.0) (end 0.0 0.0) (width {fmt4(guard_w)}) (fill none))"
            f") "
            f'(uuid "{deterministic_uuid(f"{ce.name}_guard_ring")}"))'
        )

        # Outer Concentric Faraday Ground Ring (GNDA Shield)
        lines.append(
            f'  (pad "{ce.gnd_pin}" smd custom '
            f"(at {fmt4(cx + gnd_r)} {fmt4(cy)}) "
            f"(size 0.5 0.5) "
            f'(layers "F.Cu" "F.Mask") '
            f"(clearance 0.35) "
            f"(solder_mask_margin 0.05) "
            f"(options (clearance outline) (anchor circle)) "
            f"(primitives "
            f"(gr_circle (center {fmt4(-gnd_r)} 0.0) (end 0.0 0.0) (width {fmt4(gnd_w)}) (fill none))"
            f") "
            f'(uuid "{deterministic_uuid(f"{ce.name}_gnd_ring")}"))'
        )

    # Emit 360-deg Concentric Copper Guard Rings around High-Z Pogo Landing Pads (using gr_circle graphic lines)
    for p in geom.pogo_pads:
        if p.net_name in HIGH_Z_NETS:
            lines.append(
                f'  (fp_circle (center {fmt4(p.x)} {fmt4(p.y)}) (end {fmt4(p.x + 1.45)} {fmt4(p.y)}) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Cu") (uuid "{deterministic_uuid(f"{fp_name}_guard_ring_cu_{p.pin_number}")}"))'
            )
            lines.append(
                f'  (fp_circle (center {fmt4(p.x)} {fmt4(p.y)}) (end {fmt4(p.x + 1.45)} {fmt4(p.y)}) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Mask") (uuid "{deterministic_uuid(f"{fp_name}_guard_ring_mask_{p.pin_number}")}"))'
            )

    lines.append(")")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Verification Table Printer
# ---------------------------------------------------------------------------


def format_validation_table(geom: ExtractedCADGeometry) -> str:
    """
    Build a formatted verification table summarizing the extracted CAD
    coordinates, pad/drill sizes, layers, and clearances for all signal
    connections, 4 fluid pass-through holes, and concentric guard electrodes.
    """
    out: List[str] = []
    sep = "=" * 108
    subsep = "-" * 108

    out.append(sep)
    out.append(
        f" KiCad 8/9 Footprint Verification Summary: {FOOTPRINT_NAME}.kicad_mod"
    )
    out.append(
        f" Extracted via build123d | Datum Anchor: ({geom.datum[0]:.4f}, {geom.datum[1]:.4f}) mm | "
        f"Hex Envelope: {geom.board_width:.4f} x {geom.board_height:.4f} mm"
    )
    out.append(sep)
    out.append(
        f"{'Pin':<6} | {'Net Name':<14} | {'Type / Shape':<18} | {'Coord (X, Y) [mm]':<22} | "
        f"{'Pad / Drill [mm]':<18} | {'Clear / Mask [mm]':<18}"
    )
    out.append(subsep)

    # Pogo Pin Connections
    for p in geom.pogo_pads:
        coord_str = f"({p.x:>7.4f}, {p.y:>7.4f})"
        size_str = f"{p.size_w:.4f} / {'SMD':>6}"
        clr_str = f"{p.clearance:.4f} / +{p.solder_mask_margin:.4f}"
        shape_str = f"{p.pad_type} {p.pad_shape}"
        out.append(
            f"{p.pin_number:<6} | {p.net_name:<14} | {shape_str:<18} | {coord_str:<22} | "
            f"{size_str:<18} | {clr_str:<18}"
        )

    out.append(subsep)

    # 4 Fluidic Pass-Through Holes
    for h_name, hx, hy, h_drill in geom.fluid_holes:
        coord_str = f"({hx:>7.4f}, {hy:>7.4f})"
        size_str = f"{h_drill:.4f} / {h_drill:.4f}"
        clr_str = "0.2500 /  0.0000"
        out.append(
            f"{h_name:<6} | {'FLUID_PORT':<14} | {'np_thru_hole circ':<18} | {coord_str:<22} | "
            f"{size_str:<18} | {clr_str:<18}"
        )

    out.append(subsep)

    # Concentric Compression Electrode & Guard Ring Summary
    for ce in geom.concentric_electrodes:
        cx, cy = ce.center
        coord_str = f"({cx:>7.4f}, {cy:>7.4f})"
        dot_str = f"Dot {ce.inner_dot_dia:.2f}mm"
        guard_str = f"ID {ce.guard_id:.1f}/OD {ce.guard_od:.1f}"
        out.append(
            f"{ce.signal_pin + '/' + ce.guard_pin:<6} | {ce.signal_net + '+' + ce.guard_net:<14} | "
            f"{'concentric ring':<18} | {coord_str:<22} | {dot_str:<18} | {guard_str:<18}"
        )

    out.append(sep)
    return "\n".join(out)



# ---------------------------------------------------------------------------
# Library generation, check mode, CLI
# ---------------------------------------------------------------------------

# Footprint libraries that receive the coax / alias / fluid footprints.
LIBRARY_DIRS = [
    REPO_ROOT / "Amplifier" / "footprints.pretty",
    REPO_ROOT / "Interposer" / "footprints.pretty",
]
EXPORT_DIR = REPO_ROOT / "exports" / "footprints"

# Generated footprints that used to be emitted (6-pin experiments, MillMax 09xx,
# spring headers, copies in Amplifier/footprints). Removed on write.
OBSOLETE_FOOTPRINTS = [
    "PogoPin_Target_6Pin_Cis",
    "PogoPin_Target_6Pin_Trans",
    "PogoPin_Target_6Pin_Array",
    "PogoPin_Target_6Pin_MillMax_09xx",
    "PogoPin_SpringHeader_6Pin_Cis",
    "PogoPin_SpringHeader_6Pin_Trans",
    "PogoPin_SpringHeader_6Pin_Array",
    FOOTPRINT_NAME,
]


def generate_library() -> Dict[str, str]:
    """Return {footprint name: .kicad_mod text} for every library footprint."""
    out: Dict[str, str] = {}
    for style in ("smt", "target"):
        for shape in (spec.CIRCLE, spec.SQUARE):
            for ring in RING_SUFFIX:
                n = coax_footprint_name(style, shape, ring)
                out[n] = generate_coax_footprint(style, shape, ring)
    for alias, (style, shape, ring) in LEGACY_ALIASES.items():
        out[alias] = generate_coax_footprint(style, shape, ring, name=alias)
    for fmode in ("drills", "silkscreen_only"):
        ref = f"Fluid_Overlay_{fmode.upper()}"
        out[ref] = (
            generate_header(ref, f"Fluid overlay: {fmode}")
            + generate_fluid_references(fluid_mode=fmode)
            + ")\n"
        )
    return out


def check_library(verbose: bool = True) -> List[str]:
    """Compare generated footprints with files on disk. Returns drifted paths."""
    drift: List[str] = []
    for name, sexpr in generate_library().items():
        for d in LIBRARY_DIRS:
            f = d / f"{name}.kicad_mod"
            if not f.is_file() or f.read_text(encoding="utf-8") != sexpr:
                drift.append(str(f.relative_to(REPO_ROOT)))
    for name in OBSOLETE_FOOTPRINTS:
        for d in LIBRARY_DIRS:
            f = d / f"{name}.kicad_mod"
            if f.exists():
                drift.append(f"{f.relative_to(REPO_ROOT)} (obsolete, should be removed)")
    if verbose:
        for item in drift:
            print(f"[DRIFT] {item}")
    return drift


def write_library(verbose: bool = True) -> List[Path]:
    """Write all library footprints and delete obsolete generated ones."""
    written: List[Path] = []
    for d in LIBRARY_DIRS:
        d.mkdir(parents=True, exist_ok=True)
        for name, sexpr in generate_library().items():
            f = d / f"{name}.kicad_mod"
            if not f.is_file() or f.read_text(encoding="utf-8") != sexpr:
                f.write_text(sexpr, encoding="utf-8")
                written.append(f)
        for name in OBSOLETE_FOOTPRINTS:
            f = d / f"{name}.kicad_mod"
            if f.exists():
                f.unlink()
                if verbose:
                    print(f"[REMOVED] {f.relative_to(REPO_ROOT)}")
    if verbose:
        print(f"[OK] Library up to date ({len(written)} file(s) changed).")
    return written


def build_footprint_file(
    output_path: Path | str = EXPORT_DIR / f"{FOOTPRINT_NAME}.kicad_mod",
    sync_libraries: bool = False,
    verbose: bool = True,
    pin_positions: Optional[Dict[Union[int, str], Tuple[float, float]]] = None,
    fluid_mode: str = "drills",
) -> Tuple[ExtractedCADGeometry, str]:
    """Write the legacy whole-board footprint to `output_path` and, if
    `sync_libraries`, regenerate the coax library footprints (all spec-driven)."""
    geom = extract_cad_geometry(pin_positions=pin_positions)
    sexpr = generate_kicad_footprint(geom, footprint_name=FOOTPRINT_NAME, fluid_mode=fluid_mode)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sexpr, encoding="utf-8")
    if sync_libraries:
        write_library(verbose=verbose)
    if verbose:
        print(format_validation_table(geom))
        print(f"\n[OK] Wrote legacy whole-board footprint to: {out_path}")
    return geom, sexpr


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MR1 coax pogo-pin KiCad footprints from src/stack_spec.py."
    )
    parser.add_argument(
        "--out", "-o", type=Path, default=EXPORT_DIR / f"{FOOTPRINT_NAME}.kicad_mod",
        help="Output for the legacy whole-board footprint (default: exports/footprints/...)",
    )
    parser.add_argument(
        "--fluid-mode", choices=["drills", "silkscreen_only"], default="drills",
        help="Fluid hole representation in the legacy whole-board footprint",
    )
    parser.add_argument(
        "--pin-coords", "--pin-positions", "--pins", type=str,
        help="JSON string or file with per-pin (x, y) KiCad-coordinate overrides (legacy whole-board footprint)",
    )
    parser.add_argument("--read-pcb", type=Path, help="Print pin placements parsed from a .kicad_pcb and exit")
    parser.add_argument("--list", action="store_true", help="List library footprints and exit")
    parser.add_argument("--check", action="store_true", help="Exit 1 if libraries differ from generated output (CI)")
    parser.add_argument("--check-cad", action="store_true", help="Exit 1 if build123d CAD disagrees with the spec")
    parser.add_argument("--dry-run", action="store_true", help="Generate in memory only; write nothing")
    parser.add_argument("--no-sync-libs", action="store_false", dest="sync_libs", default=True,
                        help="Write only the legacy --out file, not the libraries")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress stdout verification table")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    problems = spec.validate()
    if problems:
        print("stack_spec validation failed:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    if args.list:
        for name in generate_library():
            print(name)
        return 0
    if args.read_pcb:
        print(json.dumps(extract_pin_placements_from_pcb(args.read_pcb), indent=2))
        return 0
    if args.check_cad:
        mism = cross_check_cad()
        for m in mism:
            print(f"[CAD MISMATCH] {m}")
        print("[OK] CAD matches stack_spec." if not mism else f"{len(mism)} mismatch(es).")
        return 1 if mism else 0
    if args.check:
        return 1 if check_library() else 0
    if args.dry_run:
        lib = generate_library()
        print(f"[DRY RUN] would generate {len(lib)} footprints into {len(LIBRARY_DIRS)} libraries.")
        return 0

    pin_positions = None
    if args.pin_coords:
        if os.path.exists(args.pin_coords):
            with open(args.pin_coords, "r", encoding="utf-8") as f:
                pin_positions = json.load(f)
        else:
            pin_positions = json.loads(args.pin_coords)

    build_footprint_file(
        output_path=args.out,
        sync_libraries=args.sync_libs,
        verbose=not args.quiet,
        pin_positions=pin_positions,
        fluid_mode=args.fluid_mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
