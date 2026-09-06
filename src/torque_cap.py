from build123d import *
import math
from src.constants import *


def Torque_Cap_Inner():
    """Inner threaded cap with M76 helical thread, 24 ratchet teeth, retention flange, and pipette hole.
    Exact match to golden STL (81.4 x 81.4 x 20.2 mm).
    """
    cap_h = INNER_CAP_H # 20.2
    retention_h = CAP_RETENTION_H # 2.0
    flange_r = INNER_CAP_OD / 2.0 # 40.7 (D = 81.4)
    body_r = (NECK_OD + 4.0) / 2.0 # 39.5 (D = 79.0)
    thread_r = (NECK_OD + 1.0) / 2.0 # 38.0 (D = 76.0)
    pitch = CAP_THREAD_PITCH # 8.0
    depth = 1.6
    pipette_d = PIPETTE_HOLE_D # 25.0
    teeth_count = TORQUE_TEETH_COUNT # 24

    with BuildPart(mode=Mode.PRIVATE) as p:
        # 1. Retention Flange at bottom
        with Locations((0, 0, retention_h / 2.0)):
            Cylinder(radius=flange_r, height=retention_h)

        # 2. Main ring body above flange
        with Locations((0, 0, retention_h + (cap_h - retention_h) / 2.0)):
            Cylinder(radius=body_r, height=cap_h - retention_h)

        # 3. 24 Ratchet Teeth around perimeter
        tooth_h = cap_h - retention_h
        for i in range(teeth_count):
            ang = i * (360.0 / teeth_count)
            with Locations(Rotation(0, 0, ang) * Location((body_r, 0, retention_h + tooth_h / 2.0))):
                with BuildSketch():
                    RegularPolygon(radius=0.8, side_count=3)
                extrude(amount=tooth_h / 2.0, both=True)

        # 4. Core inner bore
        with Locations((0, 0, cap_h / 2.0)):
            Cylinder(radius=thread_r, height=cap_h + 2.0, mode=Mode.SUBTRACT)

        # 5. Helical Internal Thread Ridge (swept inward)
        path = Helix(pitch=pitch, height=cap_h, radius=thread_r)
        with BuildSketch(Plane.XZ) as s:
            with Locations((thread_r, 0)):
                pts = [
                    (0, -pitch * 0.25),
                    (-depth, -pitch * 0.12),
                    (-depth, pitch * 0.12),
                    (0, pitch * 0.25)
                ]
                Polygon(pts)
        sweep(sections=s.sketch, path=path, mode=Mode.ADD)

        # 6. Central pipette access hole
        Cylinder(radius=pipette_d / 2.0, height=cap_h * 3.0, mode=Mode.SUBTRACT)

        # 7. Trim top and bottom flush to cap_h
        split(bisect_by=Plane(origin=(0, 0, 0), z_dir=(0, 0, 1)), keep=Keep.TOP)
        split(bisect_by=Plane(origin=(0, 0, cap_h), z_dir=(0, 0, 1)), keep=Keep.BOTTOM)

    return p.part

def Torque_Cap_Outer():
    """Outer rotating cap handle with 12 fluted grips, 6 flex ratchet slots, retention lip, and pipette access.
    Matches golden STL (95.0 x 95.0 x 30.2 mm).
    """
    cap_h = OUTER_CAP_H # 30.2
    body_r = OUTER_CAP_OD / 2.0 # 47.5 (D = 95.0)
    cap_top_thick = CAP_TOP_THICK # 5.0
    cap_retention_h = CAP_RETENTION_H # 2.0
    pipette_d = PIPETTE_HOLE_D # 25.0

    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main Body Cylinder
        with Locations((0, 0, cap_h / 2.0)):
            Cylinder(radius=body_r, height=cap_h)

        # 12 Fluted Grips around circumference
        for i in range(12):
            ang = 15.0 + i * 30.0
            with Locations(Rotation(0, 0, ang) * Location((body_r, 0, cap_h / 2.0))):
                Cylinder(radius=4.0, height=cap_h + 2.0, mode=Mode.SUBTRACT)

        # Bottom Retention Lip (inner diameter = 80mm)
        with Locations((0, 0, (cap_retention_h + 1.0) / 2.0 - 0.5)):
            Cylinder(radius=(NECK_OD + 5.0) / 2.0, height=cap_retention_h + 1.0, mode=Mode.SUBTRACT)

        # Main inner clearance cavity
        cavity_h = cap_h - cap_top_thick - (cap_retention_h - 0.5)
        cavity_z = (cap_retention_h - 0.5) + cavity_h / 2.0
        with Locations((0, 0, cavity_z)):
            Cylinder(radius=(NECK_OD + 9.0) / 2.0, height=cavity_h, mode=Mode.SUBTRACT)

        # Pipette hole in top ceiling
        with Locations((0, 0, cap_h - cap_top_thick / 2.0)):
            Cylinder(radius=pipette_d / 2.0, height=cap_top_thick + 2.0, mode=Mode.SUBTRACT)

        # 6 Flex ratchet windows
        slot_w = 30.0
        slot_l = 20.0
        slot_h = cap_h - cap_retention_h - 2.0
        slot_z = (cap_h + cap_retention_h - 1.0) / 2.0
        for i in range(6):
            ang = i * 60.0
            with Locations(Rotation(0, 0, ang) * Location((NECK_OD / 2.0 + 6.0, 0, slot_z))):
                Box(slot_w, slot_l, slot_h, mode=Mode.SUBTRACT)

        # Cantilever spring arms with pawls
        arm_h = cap_h - cap_retention_h - 6.0
        arm_z = cap_retention_h + 1.0 + arm_h / 2.0
        for i in range(6):
            ang = i * 60.0
            with Locations(Rotation(0, 0, ang) * Location((NECK_OD / 2.0 + 6.0, -3.0, arm_z))):
                Box(4.0, 16.0, arm_h, mode=Mode.ADD)
            with Locations(Rotation(0, 0, ang) * Location((NECK_OD / 2.0 + 3.0, 4.0, arm_z))):
                Cylinder(radius=1.5, height=arm_h, mode=Mode.ADD)

    return p.part

