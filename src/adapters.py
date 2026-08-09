from build123d import *
from src.constants import *
import math

def Threaded_Luer_Adapter(render_threads=False):
    """G1/8 (1/8" NPT) to Male Luer Lock adapter."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base/Threaded section (Simplistic cylinder for now)
        with Locations((0, 0, 3.0)):
            Cylinder(radius=9.4/2.0, height=6.0)

        # Hex Flange
        with Locations((0, 0, 6.0)):
            with BuildSketch():
                RegularPolygon(radius=12.0/math.cos(math.pi/6)/2.0, side_count=6)
            extrude(amount=5.5)

        # Luer Collar
        with Locations((0, 0, 11.5 + 4.5)):
            Cylinder(radius=11.0/2.0, height=9.0)

        # Central bore
        Cylinder(radius=2.0, height=30.0, mode=Mode.SUBTRACT)
    return p.part

def Elbow_Adapter():
    """Luer elbow adapter."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Vertical shaft
        with Locations((0, 0, 23.2/2.0)):
            Cylinder(radius=2.0, height=23.2)

        # Horizontal tube
        with Locations((14.8/2.0, 0, 23.2)):
            Cylinder(radius=3.0, height=14.8, rotation=(0, 90, 0))

        # Hollow out
        with Locations((0, 0, 23.2/2.0)):
            Cylinder(radius=1.25, height=25.0, mode=Mode.SUBTRACT)
        with Locations((14.8/2.0, 0, 23.2)):
            Cylinder(radius=2.0, height=16.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

    return p.part
