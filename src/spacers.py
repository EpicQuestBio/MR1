# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
src/spacers.py
==============
CAD solids for the MR1 coax pogo-pin stack:
  - `Pogo_Pin_Solid`: 3D model of single C5221285 SMT spring-loaded pogo pin
  - `Pogo_Pin_Array_Solid`: 12-pin distributed pogo array matching `src.stack_spec`
  - `PP_Shim`: Solid 0.030" (0.762 mm) Polypropylene stock shim
  - `Delrin_Block`: Coarse structural Delrin block (0.125" / 3.175 mm or 0.270" / 6.858 mm)
  - `Printed_Spacer`: 3D-printed adjustable spacer (>= 3.0 mm) with component cavities
"""

from __future__ import annotations

import math
from typing import Optional

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    extrude,
    insert,
)

from src import stack_spec as spec
from src.common import Circuitry_Cutouts, Finger_Grip_Cutout, Hex_Base_Sketch, Weep_Duct_Holes
from src.constants import HEX_DIAM, PORT_RADIUS


def Pogo_Pin_Solid(compressed: bool = True) -> Part:
    """3D CAD solid of a single C5221285 pogo pin.

    - SMT base: 2.0 mm diameter or 1.8x1.8 mm, height = 2.0 mm
    - Brass barrel: 1.5 mm diameter
    - Gold-plated plunger tip: 0.9 mm diameter
    - Total height: working_height (7.5 mm) if compressed, free_length (9.0 mm) if uncompressed.
    """
    total_h = spec.POGO.working_height if compressed else spec.POGO.free_length
    base_h = spec.POGO.base_thickness  # 2.0 mm
    barrel_h = total_h - 1.5
    plunger_h = total_h

    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base SMT collar (Z = 0 to base_h)
        Cylinder(radius=1.0, height=base_h, align=(None, None, None))
        # Main barrel (Z = 0 to barrel_h)
        Cylinder(radius=0.75, height=barrel_h, align=(None, None, None))
        # Extended plunger tip (Z = 0 to plunger_h)
        Cylinder(radius=0.45, height=plunger_h, align=(None, None, None))

    return p.part


def Pogo_Pin_Array_Solid(compressed: bool = True) -> Compound:
    """Compound of all 12 discrete pogo pins placed at CAD coordinates from `src.stack_spec`."""
    instances = []
    for p in spec.PINS:
        pin_solid = Pogo_Pin_Solid(compressed=compressed)
        instances.append(pin_solid.move(Location((p.x, p.y, 0))))
    return Compound(children=instances)


def PP_Shim(height: float = spec.PP_SHIM) -> Part:
    """Solid Polypropylene (PP) stock shim plate (default 0.030" / 0.762 mm).

    Provides chemical barrier and fine vertical spacing adjustment.
    Includes clearance holes for 12 pogo pins and 4 fluid ports.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            insert(Hex_Base_Sketch())
            # 12 Pogo clearance through-holes (D = 2.6 mm)
            for pin in spec.PINS:
                with Locations((pin.x, pin.y)):
                    Circle(1.3, mode=Mode.SUBTRACT)
            # 4 Fluid pass-through clearance holes (D = 2.5 mm)
            for hx, hy in spec.FLUID_HOLES.values():
                with Locations((hx, hy)):
                    Circle(1.25, mode=Mode.SUBTRACT)
        extrude(amount=height)
        insert(Finger_Grip_Cutout(height=height + 2.0), mode=Mode.SUBTRACT)

    return p.part


def Delrin_Block(thickness: float = spec.DELRIN_THIN) -> Part:
    """Coarse stock Delrin block (default 0.125" / 3.175 mm or 0.270" / 6.858 mm).

    Provides rigid backing and spacing between stack layers.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            insert(Hex_Base_Sketch())
            for pin in spec.PINS:
                with Locations((pin.x, pin.y)):
                    Circle(1.3, mode=Mode.SUBTRACT)
            for hx, hy in spec.FLUID_HOLES.values():
                with Locations((hx, hy)):
                    Circle(1.25, mode=Mode.SUBTRACT)
        extrude(amount=thickness)
        insert(Finger_Grip_Cutout(height=thickness + 2.0), mode=Mode.SUBTRACT)

    return p.part


def Printed_Spacer(height: float = 3.6) -> Part:
    """3D-printed adjustable spacer block.

    Parameters:
      height: Total height in mm (must be >= 3.0 mm to clear amplifier components).

    Features:
      - Fits hexagonal cartridge envelope matching `Hex_Base_Sketch`
      - Circuitry clearance pocket (`Circuitry_Cutouts`) to enclose inverted amplifier components
      - 12 through-holes for pogo pin shafts (D = 2.5 mm) with anti-wicking air margin
      - 4 through-holes for fluid port clearance (D = 2.8 mm)
      - Finger grip notches and weep duct drain holes
    """
    if height < spec.PRINTED_MIN:
        raise ValueError(f"Printed_Spacer height {height} mm < minimum {spec.PRINTED_MIN} mm")

    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            insert(Hex_Base_Sketch())
            # 12 Pogo clearance holes (dia 2.5 mm -> radius 1.25 mm)
            for pin in spec.PINS:
                with Locations((pin.x, pin.y)):
                    Circle(1.25, mode=Mode.SUBTRACT)
            # 4 Fluid pass-through holes (dia 2.8 mm -> radius 1.4 mm)
            for hx, hy in spec.FLUID_HOLES.values():
                with Locations((hx, hy)):
                    Circle(1.4, mode=Mode.SUBTRACT)
        extrude(amount=height)

        # Subtract component clearance cavities
        cavity_depth = max(height - 0.6, 2.5)
        cutouts = Circuitry_Cutouts(height=cavity_depth)
        cutouts = cutouts.move(Location((0, 0, height - cavity_depth / 2.0)))
        insert(cutouts, mode=Mode.SUBTRACT)

        # Finger grip side notches
        insert(Finger_Grip_Cutout(height=height + 2.0), mode=Mode.SUBTRACT)
        # Weep duct through-drain holes
        insert(Weep_Duct_Holes(height=height + 2.0), mode=Mode.SUBTRACT)

    return p.part
