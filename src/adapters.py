from build123d import *
from src.constants import *
from src.common import generate_helical_thread
import math

def Threaded_Luer_Adapter(render_threads=False):
    """G1/8 (1/8" NPT) to Male Luer Lock adapter."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base/Threaded section
        with Locations((0, 0, 3.0)):
            Cylinder(radius=9.4 / 2.0, height=6.0)

        # Helical threads (swept when render_threads=True)
        if render_threads:
            pitch = NPT_1_8_THREAD_PITCH
            h = 5.0
            r = 9.4 / 2.0
            depth = 0.5
            thread = generate_helical_thread(
                pitch=pitch,
                depth=depth,
                length=h,
                core_radius=r - depth,
                is_internal=False
            )
            with Locations((0, 0, 0.5)):
                insert(thread, mode=Mode.ADD)

        # Hex Flange
        with Locations((0, 0, 6.0)):
            with BuildSketch():
                RegularPolygon(radius=12.0 / math.cos(math.pi / 6) / 2.0, side_count=6)
            extrude(amount=5.5)

        # Luer Collar
        with Locations((0, 0, 11.5 + 4.5)):
            Cylinder(radius=11.0 / 2.0, height=9.0)

        # Central bore
        Cylinder(radius=2.0, height=30.0, mode=Mode.SUBTRACT)
    return p.part

def Elbow_Adapter():
    """Luer elbow adapter with smoothed internal bend to eliminate fluidic stagnation."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Vertical shaft
        with Locations((0, 0, 23.2 / 2.0)):
            Cylinder(radius=3.0, height=23.2)

        # Horizontal tube
        with Locations((14.8 / 2.0, 0, 23.2)):
            Cylinder(radius=3.0, height=14.8, rotation=(0, 90, 0))

        # Outer corner blend
        with Locations((0, 0, 23.2)):
            Sphere(radius=3.0)

        # Hollow out with smoothed internal turn
        with Locations((0, 0, 23.2 / 2.0)):
            Cylinder(radius=1.5, height=25.0, mode=Mode.SUBTRACT)
        with Locations((14.8 / 2.0, 0, 23.2)):
            Cylinder(radius=1.5, height=16.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
        with Locations((0, 0, 23.2)):
            Sphere(radius=1.8, mode=Mode.SUBTRACT)

    return p.part
