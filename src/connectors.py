# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

from build123d import *
from src.constants import *

def JST_XH_2_Pin_Header():
    """Simplified 2-pin JST XH 2.54mm Pitch Downward-facing Header"""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base housing
        Box(7.5, 5.7, 9.8)
        # Pins (visual only)
        with Locations((-1.27, 0, -4.9)):
            Cylinder(radius=0.3, height=3.0, mode=Mode.ADD)
        with Locations((1.27, 0, -4.9)):
            Cylinder(radius=0.3, height=3.0, mode=Mode.ADD)
    return p.part

def USB_C_Panel_Mount():
    """Simplified USB-C Panel Mount Connector Breakout with M2 mounting holes"""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main PCB Breakout Board
        Box(14.0, 15.0, 1.6)
        # USB-C Receptacle
        with Locations((0, 7.5, 1.6)):
            Box(9.0, 7.0, 3.2, mode=Mode.ADD)
        # M2 mounting screw holes (2.2mm diameter, 10mm hole spacing)
        with Locations((-5.0, -4.0, 0), (5.0, -4.0, 0)):
            Cylinder(radius=2.2 / 2.0, height=5.0, mode=Mode.SUBTRACT)
    return p.part

def Luer_Bulkhead_Panel_Mount():
    """1/8" Hose Barb x Female Luer Panel Mount Bulkhead"""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Hex Nut / Panel Mount section
        with BuildSketch():
            RegularPolygon(radius=14.0/2.0, side_count=6)
        extrude(amount=4.0)

        # Threaded body for panel
        with Locations((0, 0, -5.0)):
            Cylinder(radius=6.35/2.0, height=5.0, mode=Mode.ADD) # 1/4-28 UNF

        # Luer Receptacle on top
        with Locations((0, 0, 4.0)):
            Cylinder(radius=10.0/2.0, height=8.0, mode=Mode.ADD)
            Cylinder(radius=4.2/2.0, height=8.0, mode=Mode.SUBTRACT) # Luer taper simplified

        # Barb extending downward
        with Locations((0, 0, -12.0)):
            Cylinder(radius=3.2/2.0, height=7.0, mode=Mode.ADD)

        # Through hole
        with Locations((0, 0, -12.0)):
            Cylinder(radius=1.5, height=30.0, mode=Mode.SUBTRACT)
    return p.part

def JST_XH_2_Pin_Plug():
    """Simplified 2-pin JST XH 2.54mm Pitch Mating Plug"""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Plug body
        Box(5.7, 5.7, 8.0)
        # Wires extending upwards
        with Locations((-1.27, 0, 4.0)):
            Cylinder(radius=WIRE_OD/2.0, height=5.0, mode=Mode.ADD)
        with Locations((1.27, 0, 4.0)):
            Cylinder(radius=WIRE_OD/2.0, height=5.0, mode=Mode.ADD)
    return p.part
