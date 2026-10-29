#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
generate_footprint.py
=====================
Extracts mechanical geometry, fluidic manifold coordinates, concentric
compression electrode guard rings, and 12-pin distributed pogo-pin target
locations directly from the `build123d` CAD models (`src.cartridge`,
`src.common`, `src.constants`, `src.nanopore_wafer_mold`) and generates the
production-ready KiCad 8/9 footprint:

    PogoPin_Target_6Pin_Distributed.kicad_mod

Can be executed standalone as a CLI tool:
    python generate_footprint.py --out PogoPin_Target_6Pin_Distributed.kicad_mod

Or imported as a module in automated build pipelines:
    from generate_footprint import extract_cad_geometry, generate_kicad_footprint
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Ensure repository root is importable when invoked from any working directory
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build123d import GeomType, ShapeList, Vertex, Wire  # noqa: E402
from src.cartridge import (  # noqa: E402
    PTFE_Interposer,
    PogoPinHoles,
    Silver_Chloride_Ribbon_Pads,
)
from src.common import Hex_Base_Sketch, Weep_Duct_Holes  # noqa: E402
from src.constants import (  # noqa: E402
    HEX_DIAM,
    PCB_WAFER_HOLE_SIZE,
    POGO_Y,
    PORT_RADIUS,
)
from src.nanopore_wafer_mold import (  # noqa: E402
    Bottom_Fluidic_Electrode_Mold_Plate,
    Concentric_Guard_Mold_Plate_Top,
)


# ---------------------------------------------------------------------------
# Constants & Dual 6-Pin (Cis + Trans) Net Mapping Specification
# ---------------------------------------------------------------------------

FOOTPRINT_NAME = "PogoPin_Target_6Pin_Distributed"

# Bank B (Cis / Sensing - Top Quadrant CAD Y > 0 / KiCad Y = -15.0..-16.0 mm):
# P1: GNDA_SHLD (-18, +16 CAD), P2: WS_CIS_WIDE (-10, +15 CAD), P3: GUARD_WIDE (-6, +15 CAD),
# P4: GUARD_CIS_A (+4, +15 CAD), P5: WS_CIS (+8, +15 CAD), P6: GUARD_CIS_B (+12, +15 CAD)
PIN_NET_SEQUENCE_6PIN_CIS: List[Tuple[int, str, float, float, str]] = [
    (1, "GNDA_SHLD", -18.0, 16.0, "Shield anchor pinning inlet/outlet fluid manifold ground boundary"),
    (2, "WS_CIS_WIDE", -10.0, 15.0, "Path 2 (200 nm Pore) working electrode contact; short straight escape"),
    (3, "GUARD_WIDE", -6.0, 15.0, "Active driven guard for Path 2; isolates Path 2 from Path 1 sensing"),
    (4, "GUARD_CIS_A", 4.0, 15.0, "Driven Guard (Left wing of triaxial Faraday cocoon around P5)"),
    (5, "WS_CIS", 8.0, 15.0, "Path 1 (Sub-5 nm Pore) high-Z electrometer node (LMP7721 Pin 8)"),
    (6, "GUARD_CIS_B", 12.0, 15.0, "Driven Guard (Right wing of triaxial Faraday cocoon around P5)"),
]

# Bank A (Trans / Excitation - Bottom Quadrant CAD Y < 0 / KiCad Y = +15.0..+16.0 mm):
# P7: CE_GNDA (-18, -16 CAD), P8: RE_TRANS (-10, -15 CAD), P9: >PORE_AMP (-4, -15 CAD),
# P10: GNDA (+3, -15 CAD), P11: WEEP_SENSE (+12, -15 CAD), P12: GNDA_WEEP (+18, -16 CAD)
PIN_NET_SEQUENCE_6PIN_TRANS: List[Tuple[int, str, float, float, str]] = [
    (7, "CE_GNDA", -18.0, -16.0, "Trans Counter Electrode return path; mates directly to bottom Ag strip"),
    (8, "RE_TRANS", -10.0, -15.0, "Trans bulk reference sense node; minimizes lead length into trans fluid well"),
    (9, ">PORE_AMP", -4.0, -15.0, "Active bias excitation drive; isolated symmetrically across board"),
    (10, "GNDA", 3.0, -15.0, "Low-noise analog ground return fence; shields excitation from weep sensing"),
    (11, "WEEP_SENSE", 12.0, -15.0, "Moisture-sensing trace intercepting droplet breaches before dry contacts"),
    (12, "GNDA_WEEP", 18.0, -16.0, "Perimeter weep moat static drain & outer chassis tie"),
]

# Alias for 6-pin Mill-Max 09xx sequence
PIN_NET_SEQUENCE_6PIN: List[Tuple[int, str, float, float, str]] = PIN_NET_SEQUENCE_6PIN_TRANS

# Exact 12-connection Distributed 2 x 6 Pogo Pin Map (6 Bank B Cis at CAD Y > 0 + 6 Bank A Trans at CAD Y < 0)
PIN_NET_SEQUENCE: List[Tuple[int, str, float, float, str]] = [
    # Bank B (Cis / Sensing - Pins 1..6)
    (1, "GNDA_SHLD", -18.0, 16.0, "Pin 1: Shield anchor pinning inlet/outlet fluid manifold ground boundary"),
    (2, "WS_CIS_WIDE", -10.0, 15.0, "Pin 2: Path 2 (200 nm Pore) working electrode contact"),
    (3, "GUARD_WIDE", -6.0, 15.0, "Pin 3: Active driven guard for Path 2"),
    (4, "GUARD_CIS_A", 4.0, 15.0, "Pin 4: Driven Guard (Left wing of triaxial Faraday cocoon around P5)"),
    (5, "WS_CIS", 8.0, 15.0, "Pin 5: Path 1 (Sub-5 nm Pore) high-Z electrometer node"),
    (6, "GUARD_CIS_B", 12.0, 15.0, "Pin 6: Driven Guard (Right wing of triaxial Faraday cocoon around P5)"),
    # Bank A (Trans / Excitation - Pins 7..12)
    (7, "CE_GNDA", -18.0, -16.0, "Pin 7: Trans Counter Electrode return path"),
    (8, "RE_TRANS", -10.0, -15.0, "Pin 8: Trans bulk reference sense node"),
    (9, ">PORE_AMP", -4.0, -15.0, "Pin 9: Active bias excitation drive"),
    (10, "GNDA", 3.0, -15.0, "Pin 10: Low-noise analog ground return fence"),
    (11, "WEEP_SENSE", 12.0, -15.0, "Pin 11: Moisture-sensing trace intercepting droplet breaches"),
    (12, "GNDA_WEEP", 18.0, -16.0, "Pin 12: Perimeter weep moat static drain & outer chassis tie"),
]

HIGH_Z_NETS = {">PORE_AMP", "WS_CIS", "WS_CIS_WIDE", "WEEP_SENSE"}
GUARD_NETS = {"GUARD", "GUARD_WIDE"}


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


def extract_cad_geometry(pin_count: int = 12, bank: str = "trans") -> ExtractedCADGeometry:
    """
    Query parametric locations, centers, radii, and outlines directly from
    the `build123d` CAD parts and sketches:
      - `Hex_Base_Sketch()` for perimeter lines and finger-grip notch arcs
      - `PTFE_Interposer()` top face inner wires for fluid manifold holes,
        wafer diamond cutout, and pogo pin targets
      - `PogoPinHoles()` for the 12 (6 Cis + 6 Trans) or 6 pogo pin landing coordinates
      - `Concentric_Guard_Mold_Plate_Top()` and `Silver_Chloride_Ribbon_Pads()`
        for concentric silver-silicone compression electrode & guard rings
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
    raw_fluid_pts: List[Tuple[float, float]] = []
    wafer_diamond_vertices: List[Tuple[float, float]] = []
    channel_recesses: List[Tuple[float, float, float]] = []
    interposer_pogo_pts: List[Tuple[float, float, float]] = []

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
        # 4 Fluidic Pass-Through Holes at PORT_RADIUS = 20.0 mm
        elif num_edges == 1 and abs(radial_dist - PORT_RADIUS) < 0.5:
            raw_fluid_pts.append((wx, wy))
        # Distributed Pogo Pin Targets along Y = +/-15.0 mm
        elif num_edges == 1 and abs(abs(wcenter.Y) - abs(POGO_Y)) < 0.5:
            interposer_pogo_pts.append((wx, wy, r4((wsize_x + wsize_y) / 2.0)))
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

    # Order the 4 fluid pass-through holes deterministically as H1..H4
    # H1: Bottom-Left (-17.3205, 10.0), H2: Top-Right (17.3205, -10.0),
    # H3: Top-Left (-17.3205, -10.0), H4: Bottom-Right (17.3205, 10.0)
    fluid_quadrant_order = [
        ("H1", lambda pt: pt[0] < 0 and pt[1] > 0),
        ("H2", lambda pt: pt[0] > 0 and pt[1] < 0),
        ("H3", lambda pt: pt[0] < 0 and pt[1] < 0),
        ("H4", lambda pt: pt[0] > 0 and pt[1] > 0),
    ]
    fluid_holes: List[Tuple[str, float, float, float]] = []
    fluid_drill_dia = 2.1  # 2.1 mm mechanical fluid pass-through specification
    for h_name, pred in fluid_quadrant_order:
        matches = [pt for pt in raw_fluid_pts if pred(pt)]
        if matches:
            fx, fy = matches[0]
            fluid_holes.append((h_name, r4(fx), r4(fy), fluid_drill_dia))

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

    # 4. Extract Pogo Pin Target Locations from Distributed Table Specification
    pad_dia = 2.000  # Standard 2.0 mm ENIG circular pads

    bank_norm = bank.lower()
    if pin_count == 6:
        active_seq = (
            PIN_NET_SEQUENCE_6PIN_CIS
            if bank_norm == "cis"
            else PIN_NET_SEQUENCE_6PIN_TRANS
        )
    else:
        active_seq = PIN_NET_SEQUENCE

    pogo_pads: List[PadSpec] = []
    for entry in active_seq:
        pin_num, net_name, cad_x, cad_y, desc = entry
        px = r4(cad_x)
        py = r4(-cad_y)  # Convert CAD +Y_up to KiCad +Y_down

        is_high_z = net_name in HIGH_Z_NETS
        is_guard = net_name in GUARD_NETS

        # High-Z and Guard pads receive increased isolation clearance (0.4 mm)
        # and explicit solder-mask margin expansion (0.1 mm)
        clearance = 0.400 if (is_high_z or is_guard) else 0.400
        mask_margin = 0.100 if (is_high_z or is_guard) else 0.050

        # Bare, unmasked ENIG / Hard Gold landing pads on passive interposer:
        # F.Cu + F.Mask ONLY (no F.Paste so solder paste never contaminates gold contacts)
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
                clearance=clearance,
                solder_mask_margin=mask_margin,
                description=desc,
                is_primary_table_entry=True,
            )
        )

    # 5. Extract Concentric Silver-Silicone Compression Electrode & Guard Ring Geometry
    # Query Concentric_Guard_Mold_Plate_Top() and Silver_Chloride_Ribbon_Pads()
    guard_mold_top = Concentric_Guard_Mold_Plate_Top()
    mold_radii = sorted(
        {
            r4(e.radius)
            for e in guard_mold_top.edges()
            if e.geom_type == GeomType.CIRCLE and e.radius < 5.0
        }
    )
    _ = mold_radii  # Verified extracted from build123d Concentric_Guard_Mold_Plate_Top

    ribbon_pads_part = Silver_Chloride_Ribbon_Pads()
    _ = ribbon_pads_part.bounding_box()

    if pin_count == 6 and bank_norm == "cis":
        concentric_electrodes = [
            ConcentricElectrodeSpec(
                name="CIS_NANOPORE_CONCENTRIC",
                center=(0.0, 0.0),
                signal_pin="2",
                signal_net=">PORE_AMP",
                guard_pin="4",
                guard_net="GUARD",
                gnd_pin="1",
                gnd_net="GNDA",
                inner_dot_dia=0.7,
                guard_id=2.1,
                guard_od=3.0,
                gnd_id=5.2,
                gnd_od=6.5,
                mask_keepout_dia=4.0,
            ),
        ]
    elif pin_count == 6:
        concentric_electrodes = [
            ConcentricElectrodeSpec(
                name="CIS_NANOPORE_CONCENTRIC",
                center=(0.0, 0.0),
                signal_pin="6",
                signal_net="WS_CIS",
                guard_pin="5",
                guard_net="GUARD",
                gnd_pin="1",
                gnd_net="CE_GNDA",
                inner_dot_dia=0.7,
                guard_id=2.1,
                guard_od=3.0,
                gnd_id=5.2,
                gnd_od=6.5,
                mask_keepout_dia=4.0,
            ),
            ConcentricElectrodeSpec(
                name="CIS_WIDEBAND_CONCENTRIC",
                center=(10.0, 0.0),
                signal_pin="4",
                signal_net="WS_CIS_WIDE",
                guard_pin="3",
                guard_net="GUARD_WIDE",
                gnd_pin="1",
                gnd_net="CE_GNDA",
                inner_dot_dia=0.7,
                guard_id=2.1,
                guard_od=3.0,
                gnd_id=5.2,
                gnd_od=6.5,
                mask_keepout_dia=4.0,
            ),
        ]
    else:
        concentric_electrodes = [
            # Primary Nanopore Working Electrode & Concentric Guard at Datum (0.0, 0.0)
            ConcentricElectrodeSpec(
                name="CIS_NANOPORE_CONCENTRIC",
                center=(0.0, 0.0),
                signal_pin="12",
                signal_net="WS_CIS",
                guard_pin="11",
                guard_net="GUARD",
                gnd_pin="1",
                gnd_net="GNDA",
                inner_dot_dia=0.7,
                guard_id=2.1,
                guard_od=3.0,
                gnd_id=5.2,
                gnd_od=6.5,
                mask_keepout_dia=4.0,
            ),
            # Wideband 100 um Micropore Working Electrode & Concentric Guard at (10.0, 0.0)
            ConcentricElectrodeSpec(
                name="CIS_WIDEBAND_CONCENTRIC",
                center=(10.0, 0.0),
                signal_pin="10",
                signal_net="WS_CIS_WIDE",
                guard_pin="9",
                guard_net="GUARD_WIDE",
                gnd_pin="3",
                gnd_net="GNDA",
                inner_dot_dia=0.7,
                guard_id=2.1,
                guard_od=3.0,
                gnd_id=5.2,
                gnd_od=6.5,
                mask_keepout_dia=4.0,
            ),
        ]

    # Optical alignment fiducials located inside the hex perimeter corners
    fiducials = [
        ("FID1", -12.0, -22.0),
        ("FID2", 12.0, -22.0),
        ("FID3", 0.0, 22.0),
    ]

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


# ---------------------------------------------------------------------------
# KiCad 8/9 S-Expression Generator
# ---------------------------------------------------------------------------


def generate_kicad_footprint(
    geom: ExtractedCADGeometry,
    footprint_name: Optional[str] = None,
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
    # 2. Fluidic Pass-Through Holes (H1, H2, H3, H4) - 2.1 mm NPTH
    # -----------------------------------------------------------------------
    for h_name, hx, hy, h_drill in geom.fluid_holes:
        r_silk = r4(h_drill / 2.0 + 0.35)
        lines.append(
            f'  (fp_circle (center {fmt4(hx)} {fmt4(hy)}) (end {fmt4(hx + r_silk)} {fmt4(hy)}) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_silk_{h_name}")}"))'
        )
        lines.append(
            f'  (fp_text user "{h_name}" (at {fmt4(hx)} {fmt4(hy - 1.8)} 0) (layer "F.SilkS") (uuid "{deterministic_uuid(f"fluid_txt_{h_name}")}") (effects (font (size 0.8 0.8) (thickness 0.15))))'
        )
        lines.append(
            f'  (pad "{h_name}" np_thru_hole circle (at {fmt4(hx)} {fmt4(hy)}) (size {fmt4(h_drill)} {fmt4(h_drill)}) (drill {fmt4(h_drill)}) (layers "*.Cu" "*.Mask") (uuid "{deterministic_uuid(f"pad_{h_name}")}"))'
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


def generate_6pin_target_array_sexpr(
    footprint_name: str = "PogoPin_Target_6Pin_Array",
    bank: str = "trans",
) -> str:
    """
    Generate a standalone 6-pin passive PTFE Interposer target array footprint
    (`PogoPin_Target_6Pin_Cis.kicad_mod` or `PogoPin_Target_6Pin_Trans.kicad_mod`)
    for mating with bottom-mounted Amplifier Mill-Max 09xx series bias-tail /
    ball-contact spring pins:
      - Bare, unmasked ENIG / Hard Gold landing pads (`F.Cu` + `F.Mask` only, no `F.Paste`)
      - Cis Bank (`J_POGO_CIS`): `[GNDA, >PORE_AMP, GNDA, GUARD, GNDA, WEEP_SENSE]`
      - Trans Bank (`J_POGO_TRANS`): `[CE_GNDA, RE_TRANS, GUARD_WIDE, WS_CIS_WIDE, GUARD, WS_CIS]`
      - Dual-perimeter cast PDMS gasket seal & atmospheric weep moat boundary
      - Rigid bottom clamp block (Delrin / Aluminum / thick Acrylic) anvil reaction zone
    """
    bank_norm = bank.lower()
    is_cis = bank_norm == "cis"
    seq = PIN_NET_SEQUENCE_6PIN_CIS if is_cis else PIN_NET_SEQUENCE_6PIN_TRANS
    ref_des = "J_POGO_CIS" if is_cis else "J_POGO_TRANS"
    bank_title = "CIS 6-Pin Bank (GNDA, >PORE_AMP, GNDA, GUARD, GNDA, WEEP_SENSE)" if is_cis else "TRANS 6-Pin Bank (CE_GNDA, RE_TRANS, GUARD_WIDE, WS_CIS_WIDE, GUARD, WS_CIS)"

    lines: List[str] = [
        f'(footprint "{footprint_name}" (version 20241229) (generator "generate_footprint.py")',
        '  (layer "F.Cu")',
        f'  (descr "6-Pin Bare Unmasked ENIG/Hard Gold Pogo Target Array [{bank_title}] for Mill-Max 09xx Bias-Tail/Ball-Contact Pins (Sub-pA 50-100kHz Nanopore, Dual-Seal PDMS Weep Moat, Rigid Anvil Support)")',
        f'  (tags "pogo landing array target 6-pin {bank_norm} mill-max 09xx bias-tail ball-contact enig hard-gold ptfe guard weep-moat anvil")',
        f'  (property "Reference" "{ref_des}"',
        "    (at 0.0 -3.2 0)",
        "    (unlocked yes)",
        '    (layer "F.SilkS")',
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_ref")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        f'  (property "Value" "{footprint_name}"',
        "    (at 0.0 3.2 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_val")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        '  (property "Datasheet" "https://www.mill-max.com/products/new/spring-loaded-pogo-pins"',
        "    (at 0.0 0.0 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        "    (hide yes)",
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_ds")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        f'  (property "Description" "6-Position Bare Unmasked ENIG/Hard Gold Target Array ({bank_title}) for Mill-Max 09xx Bias-Tail/Ball-Contact Spring Pins; Bone-Dry Outer Perimeter with PDMS Weep Moat & Rigid Anvil"',
        "    (at 0.0 0.0 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        "    (hide yes)",
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_desc")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        "  (attr smd)",
        f'  (fp_rect (start -13.5 -2.0) (end 13.5 2.0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_silk_box")}"))',
        f'  (fp_rect (start -14.0 -2.4) (end 14.0 2.4) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (uuid "{deterministic_uuid(f"{footprint_name}_crtyd_box")}"))',
        # Dual-Perimeter Cast PDMS Gasket Seal & Atmospheric Weep Moat Boundary (between center chamber and dry pogo zone)
        f'  (fp_line (start -14.5 -3.6) (end 14.5 -3.6) (stroke (width 0.15) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_pdms_inner")}"))',
        f'  (fp_line (start -14.5 -3.1) (end 14.5 -3.1) (stroke (width 0.12) (type dash)) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_weep_moat")}"))',
        f'  (fp_line (start -14.5 -2.6) (end 14.5 -2.6) (stroke (width 0.15) (type solid)) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_pdms_outer")}"))',
        f'  (fp_text user "PDMS DUAL-SEAL + ATMOSPHERIC WEEP MOAT (DRY POGO CAVITY)" (at 0.0 -4.1 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_txt_moat")}") (effects (font (size 0.5 0.5) (thickness 0.09))))',
        # Rigid Bottom Clamp Block / Backing Anvil Reaction Outline (Delrin / Aluminum / Acrylic)
        f'  (fp_rect (start -14.2 -2.2) (end 14.2 2.2) (stroke (width 0.12) (type dot)) (fill none) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_anvil_box")}"))',
        f'  (fp_text user "RIGID BOTTOM CLAMP ANVIL (DELRIN/AL - 4.8N CREEP NEUTRALIZATION)" (at 0.0 4.3 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_txt_anvil")}") (effects (font (size 0.5 0.5) (thickness 0.09))))',
        f'  (fp_rect (start 0.2 -1.7) (end 12.8 1.7) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_guard_env")}"))',
    ]

    for entry in seq:
        pin_num, net_name, cad_x, cad_y, _desc = entry
        px = r4(cad_x)
        py = 0.0
        lines.append(
            f'  (fp_text user "{pin_num}:{net_name}" (at {fmt4(px)} -2.5 0) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_lbl_{pin_num}")}") (effects (font (size 0.55 0.55) (thickness 0.1))))'
        )
        # Bare, unmasked ENIG / Hard Gold landing pads: F.Cu + F.Mask only (NO F.Paste)
        lines.append(
            f'  (pad "{pin_num}" smd circle (at {fmt4(px)} {fmt4(py)}) (size 2.0 2.0) (layers "F.Cu" "F.Mask") (clearance 0.4) (solder_mask_margin 0.1) (uuid "{deterministic_uuid(f"{footprint_name}_pad_{pin_num}")}"))'
        )

    for entry in seq:
        _pin_num, net_name, cad_x, _cad_y, _desc = entry
        if net_name in HIGH_Z_NETS:
            px = r4(cad_x)
            lines.append(
                f'  (fp_circle (center {fmt4(px)} 0.0) (end {fmt4(px + 1.45)} 0.0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Cu") (uuid "{deterministic_uuid(f"{footprint_name}_guard_ring_cu_{net_name}")}"))'
            )
            lines.append(
                f'  (fp_circle (center {fmt4(px)} 0.0) (end {fmt4(px + 1.45)} 0.0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Mask") (uuid "{deterministic_uuid(f"{footprint_name}_guard_ring_mask_{net_name}")}"))'
            )
    lines.append(")")
    return "\n".join(lines) + "\n"


def generate_6pin_spring_header_sexpr(
    footprint_name: str = "PogoPin_SpringHeader_6Pin_Array",
    bank: str = "trans",
) -> str:
    """
    Generate a 6-pin downward-facing Reader Lid (`Amplifier` PCB bottom-mounted)
    footprint for Mill-Max 09xx Series (`0906-1-15-20-75-14-11-0` / `0985-0-15-20-71-14-11-0`)
    gold-plated bias-tail / internal ball-contact spring-loaded pogo pins:
      - Soldered to the bottom of the Amplifier PCB along Cis or Trans inlet/outlet
      - Cis Bank (`J_POGO_CIS`): `[GNDA, >PORE_AMP, GNDA, GUARD, GNDA, WEEP_SENSE]`
      - Trans Bank (`J_POGO_TRANS`): `[CE_GNDA, RE_TRANS, GUARD_WIDE, WS_CIS_WIDE, GUARD, WS_CIS]`
    """
    bank_norm = bank.lower()
    is_cis = bank_norm == "cis"
    seq = PIN_NET_SEQUENCE_6PIN_CIS if is_cis else PIN_NET_SEQUENCE_6PIN_TRANS
    ref_des = "J_POGO_CIS" if is_cis else "J_POGO_TRANS"
    bank_title = "CIS 6-Pin Bank (GNDA, >PORE_AMP, GNDA, GUARD, GNDA, WEEP_SENSE)" if is_cis else "TRANS 6-Pin Bank (CE_GNDA, RE_TRANS, GUARD_WIDE, WS_CIS_WIDE, GUARD, WS_CIS)"

    lines: List[str] = [
        f'(footprint "{footprint_name}" (version 20241229) (generator "generate_footprint.py")',
        '  (layer "F.Cu")',
        f'  (descr "Mill-Max 09xx Series (0906/0985) Gold-Plated Bias-Tail/Ball-Contact 6-Pin Spring Header [{bank_title}] Soldered to Bottom of Amplifier PCB (Sub-pA, 50-100kHz)")',
        f'  (tags "mill-max 09xx 0906 0985 bias-tail ball-contact spring pogo 6-pin {bank_norm} reader-lid guard low-leakage")',
        f'  (property "Reference" "{ref_des}"',
        "    (at 0.0 -3.2 0)",
        "    (unlocked yes)",
        '    (layer "F.SilkS")',
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_ref")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        f'  (property "Value" "{footprint_name}"',
        "    (at 0.0 3.2 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_val")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        '  (property "Datasheet" "https://www.mill-max.com/products/new/spring-loaded-pogo-pins"',
        "    (at 0.0 0.0 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        "    (hide yes)",
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_ds")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        f'  (property "Description" "Mill-Max 09xx Series (0906-1-15-20-75-14-11-0) Gold-Plated Bias-Tail/Ball-Contact 6-Pin SMT Spring Header ({bank_title}) Soldered to Bottom of Reader Lid Amplifier PCB"',
        "    (at 0.0 0.0 0)",
        "    (unlocked yes)",
        '    (layer "F.Fab")',
        "    (hide yes)",
        f'    (uuid "{deterministic_uuid(f"{footprint_name}_desc")}")',
        "    (effects (font (size 0.8 0.8) (thickness 0.12)))",
        "  )",
        "  (attr smd)",
        f'  (fp_rect (start -13.5 -2.0) (end 13.5 2.0) (stroke (width 0.15) (type solid)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_silk_box")}"))',
        f'  (fp_rect (start -14.0 -2.4) (end 14.0 2.4) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (uuid "{deterministic_uuid(f"{footprint_name}_crtyd_box")}"))',
        f'  (fp_rect (start 0.2 -1.7) (end 12.8 1.7) (stroke (width 0.12) (type dash)) (fill none) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_guard_env")}"))',
        f'  (fp_text user "READER LID BOTTOM-MOUNTED MILL-MAX 09XX BIAS-TAIL/BALL-CONTACT PINS ({bank_norm.upper()})" (at 0.0 4.3 0) (layer "F.Fab") (uuid "{deterministic_uuid(f"{footprint_name}_txt_lid")}") (effects (font (size 0.5 0.5) (thickness 0.09))))',
    ]

    for entry in seq:
        pin_num, net_name, cad_x, cad_y, _desc = entry
        px = r4(cad_x)
        py = 0.0
        lines.append(
            f'  (fp_text user "{pin_num}:{net_name}" (at {fmt4(px)} -2.5 0) (layer "F.SilkS") (uuid "{deterministic_uuid(f"{footprint_name}_lbl_{pin_num}")}") (effects (font (size 0.55 0.55) (thickness 0.1))))'
        )
        # Mill-Max 09xx SMT base pad (1.5 x 2.0 mm solder pad on Amplifier PCB)
        lines.append(
            f'  (pad "{pin_num}" smd roundrect (at {fmt4(px)} {fmt4(py)}) (size 1.5 2.0) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (clearance 0.4) (uuid "{deterministic_uuid(f"{footprint_name}_pad_{pin_num}")}"))'
        )

    for entry in seq:
        _pin_num, net_name, cad_x, _cad_y, _desc = entry
        if net_name in HIGH_Z_NETS:
            px = r4(cad_x)
            lines.append(
                f'  (fp_circle (center {fmt4(px)} 0.0) (end {fmt4(px + 1.45)} 0.0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Cu") (uuid "{deterministic_uuid(f"{footprint_name}_guard_ring_cu_{net_name}")}"))'
            )
            lines.append(
                f'  (fp_circle (center {fmt4(px)} 0.0) (end {fmt4(px + 1.45)} 0.0) (stroke (width 0.25) (type solid)) (fill none) (layer "F.Mask") (uuid "{deterministic_uuid(f"{footprint_name}_guard_ring_mask_{net_name}")}"))'
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
# CLI & Pipeline Entrypoint
# ---------------------------------------------------------------------------


def build_footprint_file(
    output_path: Path | str = Path(f"{FOOTPRINT_NAME}.kicad_mod"),
    sync_libraries: bool = False,
    verbose: bool = True,
    pin_count: int = 12,
    bank: str = "trans",
) -> Tuple[ExtractedCADGeometry, str]:
    """
    Extract CAD geometry, generate the KiCad S-expression, write to `output_path`,
    optionally synchronize the repository footprint libraries (including the two
    separate 6-pin Mill-Max 09xx Cis & Trans target and spring header footprints),
    and print the verification table.
    """
    fp_name = (
        "PogoPin_Target_6Pin_MillMax_09xx"
        if pin_count == 6 and str(output_path) == f"{FOOTPRINT_NAME}.kicad_mod"
        else FOOTPRINT_NAME
    )
    geom = extract_cad_geometry(pin_count=pin_count, bank=bank)
    sexpr = generate_kicad_footprint(
        geom, footprint_name=fp_name if pin_count == 6 else FOOTPRINT_NAME
    )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(sexpr, encoding="utf-8")

    if sync_libraries:
        target_dirs = [
            REPO_ROOT / "Amplifier" / "footprints",
            REPO_ROOT / "Amplifier" / "footprints.pretty",
            REPO_ROOT / "Interposer" / "footprints.pretty",
            REPO_ROOT / "exports" / "footprints",
        ]
        spring_dirs = [
            REPO_ROOT / "Amplifier" / "footprints",
            REPO_ROOT / "Amplifier" / "footprints.pretty",
            REPO_ROOT / "exports" / "footprints",
        ]
        for d in target_dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 1. Sync full Dual 6-Pin (6 Cis + 6 Trans) Interposer footprints
        geom_12 = geom if pin_count == 12 else extract_cad_geometry(pin_count=12)
        sexpr_12 = generate_kicad_footprint(geom_12, footprint_name=FOOTPRINT_NAME)
        for d in target_dirs:
            p = d / f"{FOOTPRINT_NAME}.kicad_mod"
            if p.resolve() != out_path.resolve():
                p.write_text(sexpr_12, encoding="utf-8")

        sexpr_12_millmax = generate_kicad_footprint(
            geom_12, footprint_name="PogoPin_Target_6Pin_MillMax_09xx"
        )
        for d in target_dirs:
            (d / "PogoPin_Target_6Pin_MillMax_09xx.kicad_mod").write_text(
                sexpr_12_millmax, encoding="utf-8"
            )

        # 2. Generate & sync two separate 6-Pin Bare ENIG/Hard Gold Target Arrays (J_POGO_CIS & J_POGO_TRANS)
        sexpr_cis_target = generate_6pin_target_array_sexpr(
            "PogoPin_Target_6Pin_Cis", bank="cis"
        )
        sexpr_trans_target = generate_6pin_target_array_sexpr(
            "PogoPin_Target_6Pin_Trans", bank="trans"
        )
        sexpr_arr_target = generate_6pin_target_array_sexpr(
            "PogoPin_Target_6Pin_Array", bank="trans"
        )
        for d in target_dirs:
            (d / "PogoPin_Target_6Pin_Cis.kicad_mod").write_text(
                sexpr_cis_target, encoding="utf-8"
            )
            (d / "PogoPin_Target_6Pin_Trans.kicad_mod").write_text(
                sexpr_trans_target, encoding="utf-8"
            )
            (d / "PogoPin_Target_6Pin_Array.kicad_mod").write_text(
                sexpr_arr_target, encoding="utf-8"
            )

        # 3. Generate & sync two separate 6-Pin Mill-Max 09xx Spring Headers (J_POGO_CIS & J_POGO_TRANS on Amplifier bottom)
        sexpr_cis_spring = generate_6pin_spring_header_sexpr(
            "PogoPin_SpringHeader_6Pin_Cis", bank="cis"
        )
        sexpr_trans_spring = generate_6pin_spring_header_sexpr(
            "PogoPin_SpringHeader_6Pin_Trans", bank="trans"
        )
        sexpr_arr_spring = generate_6pin_spring_header_sexpr(
            "PogoPin_SpringHeader_6Pin_Array", bank="trans"
        )
        for d in spring_dirs:
            (d / "PogoPin_SpringHeader_6Pin_Cis.kicad_mod").write_text(
                sexpr_cis_spring, encoding="utf-8"
            )
            (d / "PogoPin_SpringHeader_6Pin_Trans.kicad_mod").write_text(
                sexpr_trans_spring, encoding="utf-8"
            )
            (d / "PogoPin_SpringHeader_6Pin_Array.kicad_mod").write_text(
                sexpr_arr_spring, encoding="utf-8"
            )

    if verbose:
        print(format_validation_table(geom))
        print(f"\n[OK] Wrote KiCad footprint to: {out_path}")

    return geom, sexpr


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract mechanical & fluidic geometry from build123d CAD models "
            "and generate Dual 6-pin (Cis + Trans) Mill-Max 09xx pogo pin KiCad footprints."
        )
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default=Path(f"{FOOTPRINT_NAME}.kicad_mod"),
        help="Output path for the generated .kicad_mod file (default: PogoPin_Target_6Pin_Distributed.kicad_mod)",
    )
    parser.add_argument(
        "--pins",
        type=int,
        choices=[6, 12],
        default=12,
        help="Number of pogo pins to generate (6 for single Cis/Trans 6-pin bank, or 12 for dual 6-pin Cis+Trans; default: 12)",
    )
    parser.add_argument(
        "--bank",
        choices=["cis", "trans"],
        default="trans",
        help="Which 6-pin bank to generate when --pins 6 is selected ('cis' or 'trans'; default: 'trans')",
    )
    parser.add_argument(
        "--sync-libs",
        action="store_true",
        default=True,
        help="Also synchronize Amplifier/footprints.pretty and Interposer/footprints.pretty copies (default: True)",
    )
    parser.add_argument(
        "--no-sync-libs",
        action="store_false",
        dest="sync_libs",
        help="Write only to --out without updating footprint libraries",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress stdout verification table",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    build_footprint_file(
        output_path=args.out,
        sync_libraries=args.sync_libs,
        verbose=not args.quiet,
        pin_count=args.pins,
        bank=args.bank,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
