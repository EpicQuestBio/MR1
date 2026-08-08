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
