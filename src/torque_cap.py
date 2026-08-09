from build123d import *
from src.constants import *

def Torque_Cap_Outer():
    """Outer rotating cap handle."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Cylinder(radius=NECK_OD/2.0 + 5.0, height=CAP_H)

        # Hollow inner cavity
        with Locations((0, 0, CAP_TOP_THICK)):
            Cylinder(radius=NECK_OD/2.0 + 1.0, height=CAP_H, mode=Mode.SUBTRACT)

        # Grips (simplified)
        for i in range(12):
            with Locations(Location((NECK_OD/2.0 + 5.0, 0, CAP_H/2.0)) * Rotation(0, 0, i * 30)):
                Cylinder(radius=2.0, height=CAP_H + 1.0, mode=Mode.SUBTRACT)

    return p.part

def Torque_Cap_Inner():
    """Inner threaded cap with ratchet mechanism."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Cylinder(radius=NECK_OD/2.0, height=CAP_INNER_H)

        # Hollow out
        with Locations((0, 0, -1)):
            Cylinder(radius=NECK_ID/2.0 + 1.0, height=CAP_INNER_H + 2.0, mode=Mode.SUBTRACT)

        # Ratchet slots (simplified)
        for i in range(4):
            with Locations(Location((NECK_OD/2.0, 0, CAP_INNER_H/2.0)) * Rotation(0, 0, i * 90)):
                Box(10.0, 20.0, CAP_INNER_H - 4.0, mode=Mode.SUBTRACT)

    return p.part
