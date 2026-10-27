# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

from build123d import *
from src.constants import *
import math

def generate_helical_thread(
    pitch: float,
    depth: float,
    length: float,
    core_radius: float,
    is_internal: bool = False,
    flank_angle: float = 60.0,
    overlap: float = 0.3,
    taper_length: float | None = None
) -> Part:
    """Generates a perfectly formed helical thread (trapezoidal profile with smooth
    lead-in/lead-out tapers and solid core overlap).

    Args:
        pitch: Thread pitch in mm.
        depth: Radial depth/height of the thread profile (mm).
        length: Total axial height of the threaded section (mm).
        core_radius: Radius of the core shaft cylinder (for external threads) or inner bore (for internal threads).
        is_internal: If True, sweeps thread ridge inward from core_radius. If False, sweeps outward.
        flank_angle: Included angle of trapezoidal thread profile in degrees (default 60 deg).
        overlap: Radial penetration depth into the core cylinder (mm) to guarantee seamless boolean union.
        taper_length: Axial distance at top and bottom over which threads taper smoothly into the core shaft.
                     Defaults to pitch / 2.0.

    Returns:
        Part: The swept and tapered helical thread solid (aligned Z: 0 to length).
    """
    if taper_length is None:
        taper_length = pitch / 2.0

    ext_length = length + 2.0 * pitch

    with BuildPart(mode=Mode.PRIVATE) as thread_builder:
        with BuildPart(mode=Mode.PRIVATE) as ridge_builder:
            with BuildLine() as path:
                Helix(pitch=pitch, height=ext_length, radius=core_radius)

            path_wire = path.wire().move(Location((0, 0, -pitch)))

            # Cross-sectional trapezoidal thread profile parameters:
            root_w = pitch * 0.44
            crest_w = pitch * 0.20

            # Points defined in local XZ plane relative to core_radius
            if is_internal:
                pts = [
                    (overlap, -root_w / 2.0),
                    (-depth, -crest_w / 2.0),
                    (-depth, crest_w / 2.0),
                    (overlap, root_w / 2.0)
                ]
            else:
                pts = [
                    (-overlap, -root_w / 2.0),
                    (depth, -crest_w / 2.0),
                    (depth, crest_w / 2.0),
                    (-overlap, root_w / 2.0)
                ]

            with BuildSketch(Plane.XZ) as s:
                with Locations((core_radius, 0)):
                    Polygon(pts)

            thread_ridge = sweep(sections=s.sketch, path=path_wire)

        # Conical trimming body for smooth lead-in and lead-out tapers within [0, length]
        with BuildPart(mode=Mode.PRIVATE) as cutter:
            r_inner = core_radius - depth - 0.1 if is_internal else core_radius - overlap - 0.1
            r_outer = core_radius + overlap + 1.0 if is_internal else core_radius + depth + 1.0

            with Locations((0, 0, 0)):
                Cone(bottom_radius=r_inner, top_radius=r_outer, height=taper_length, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, 0, taper_length)):
                Cylinder(radius=r_outer, height=length - 2.0 * taper_length, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((0, 0, length - taper_length)):
                Cone(bottom_radius=r_outer, top_radius=r_inner, height=taper_length, align=(Align.CENTER, Align.CENTER, Align.MIN))

        trimmed_ridge = thread_ridge.intersect(cutter.part)
        res = trimmed_ridge[0] if isinstance(trimmed_ridge, ShapeList) else trimmed_ridge
        insert(res)

    return thread_builder.part

def Circuitry_Cutouts(height=10.0):
    """
    Returns a single build123d Part representing the active circuitry components
    to be subtracted for clearance.
    Matches the OpenSCAD module Circuitry_Cutouts(height).
    Uses Mode.PRIVATE to avoid polluting external BuildPart contexts.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        # LMP7721 OpAmp
        with Locations((0, -13, 0)):
            Box(6, 7, height)
        # Ribbon Cable Clearance Channel against hexagon wall (cuts 3.0mm into Y=-25.9808 hex edge to Y=-22.9808)
        with Locations((0, -25.9808, 0)):
            Box(13.5, 6.0, height)
        # V+ Rail Filtering
        with Locations((-10, -18, 0)):
            Box(4, 4, height)
        # V- Rail Filtering
        with Locations((6, -18, 0)):
            Box(4, 4, height)
        # Feedback Network
        with Locations((8, -24, 0)):
            Box(4, 3, height)
        # ESD Protection
        with Locations((-8, -24, 0)):
            Box(4, 3, height)
        # Optional Test Point / Via clearout
        with Locations((0, -25, 0)):
            Box(8, 4, height)

    return p.part

def Finger_Grip_Cutout(height=10.0):
    """
    Returns a Part representing the side notches for finger grips.
    Placed at X = +/- HEX_CORNER_RADIUS (30.0mm) so the R=5mm notch reaches X = +/- 25.0mm.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with Locations((HEX_CORNER_RADIUS, 0, 0), (-HEX_CORNER_RADIUS, 0, 0)):
            Cylinder(radius=FINGER_GRIP_NOTCH_R, height=height)
    return p.part

def Hex_Base_Sketch(diam=HEX_DIAM, notch_r=FINGER_GRIP_NOTCH_R, notch_x=HEX_CORNER_RADIUS):
    """
    Returns a BuildSketch for the 60mm Hex with R=5mm finger notches centered at the
    X = +/- 30mm hex corners (reaching X = +/- 25mm at Y = 0).
    Produces exact bounds matching KiCad amplifier.kicad_pcb Edge.Cuts:
    Width = 55.0mm, Height = 51.9615mm.
    """
    with BuildSketch(mode=Mode.PRIVATE) as s:
        RegularPolygon(radius=diam / 2.0, side_count=6)
        with Locations((notch_x, 0), (-notch_x, 0)):
            Circle(radius=notch_r, mode=Mode.SUBTRACT)
    return s.sketch

def Weep_Duct_Holes(height=10.0):
    """
    Returns a Part representing the vertical weep duct drops.
    These are placed at WEEP_DROP_R for angles in WEEP_ANGLES.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        for a in WEEP_ANGLES:
            with Locations(Location((WEEP_DROP_R, 0, 0)) * Rotation(0, 0, a)):
                Cylinder(radius=WEEP_DUCT_D/2.0, height=height)
    return p.part

def Weep_Trench_Cutout(height=WEEP_MOAT_DEPTH):
    """
    Returns a Part representing the radial wick trenches with angled edges (trapezoidal).
    Runs from WEEP_MOAT_R out to WEEP_DROP_R.
    Molded directly into the top face of the silicone gasket.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        length = WEEP_DROP_R - WEEP_MOAT_R
        mid_r = WEEP_MOAT_R + length / 2.0
        for a in WEEP_ANGLES:
            with Locations(Location((mid_r, 0, height/2.0)) * Rotation(0, 0, a)):
                with BuildSketch(Plane.YZ):
                    # Trapezoidal cross section: wider at the top, narrower at the bottom
                    # Bottom width = WEEP_DUCT_D, Top width = WEEP_DUCT_D + 2.0
                    with BuildLine():
                        l1 = Line((-WEEP_DUCT_D/2.0, -height/2.0), (WEEP_DUCT_D/2.0, -height/2.0))
                        l2 = Line((WEEP_DUCT_D/2.0, -height/2.0), (WEEP_DUCT_D/2.0 + 1.0, height/2.0))
                        l3 = Line((WEEP_DUCT_D/2.0 + 1.0, height/2.0), (-WEEP_DUCT_D/2.0 - 1.0, height/2.0))
                        l4 = Line((-WEEP_DUCT_D/2.0 - 1.0, height/2.0), (-WEEP_DUCT_D/2.0, -height/2.0))
                    make_face()
                extrude(amount=length/2.0, both=True)
    return p.part
