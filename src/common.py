from build123d import *
from src.constants import *

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
        # JST Connector
        with Locations((0, -19, 0)):
            Box(13, 7, height)
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
        # Downward-pointing headers
        with Locations((0, -30, 0)):
            Box(14, 5, height)

    return p.part

def Finger_Grip_Cutout(height=10.0):
    """
    Returns a Part representing the side notches for finger grips.
    Placed at X = +/- 30 (Hex Corners).
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with Locations((30, 0, 0), (-30, 0, 0)):
            Cylinder(radius=5.0, height=height)
    return p.part

def Hex_Base_Sketch(diam=HEX_DIAM, notch_r=5.0):
    """
    Returns a BuildSketch for the 60mm Hex with R=5mm finger notches at X = +/- 30.
    Produces exact bounds matching KiCad amplifier.kicad_pcb:
    Width = 55.0mm, Height = 51.9615mm.
    """
    with BuildSketch(mode=Mode.PRIVATE) as s:
        RegularPolygon(radius=diam / 2.0, side_count=6)
        with Locations((diam / 2.0, 0), (-diam / 2.0, 0)):
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

