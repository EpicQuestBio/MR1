from build123d import *
import math
from src.constants import *
from src.common import Circuitry_Cutouts, Weep_Duct_Holes, Weep_Trench_Cutout

def Rounded_Mold_Block(t, w, h, r=4.0):
    """Creates a basic mold block with rounded Y-Z corners."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base box
        Box(t, w, h)
        # Fillet the 4 edges along the X-axis (thickness direction)
        edges_to_fillet = p.edges().filter_by(Axis.X)
        if edges_to_fillet:
            fillet(edges_to_fillet, radius=r)
    return p.part

def Rounded_Reservoir_Block(t, w, h, r=2.0):
    """Creates a reservoir cutout block with rounded corners."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(t, w, h)
        edges_to_fillet = p.edges().filter_by(Axis.X)
        if edges_to_fillet:
            fillet(edges_to_fillet, radius=r)
    return p.part

def Nanopore_Wafer_Mold_Left(is_nanopore=True, gasket_type="top"):
    """
    Left mold half (X < 0 in assembly).
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        # 1. Base Block
        with Locations(( -MOLD_T/2.0, 0, MOLD_H/2.0 )):
            add(Rounded_Mold_Block(MOLD_T, MOLD_W, MOLD_H, r=4.0))

        # 2. Subtract Reservoir
        with Locations(( 0.01, 0, MOLD_H - RES_D/2.0 + 0.1 )):
            add(Rounded_Reservoir_Block(RES_T * 2.0, MOLD_W - 10.0, RES_D, r=2.0), mode=Mode.SUBTRACT)

        # 3. Tapered Sprue Channel
        with BuildSketch(Plane.XY.offset(MOLD_H - RES_D)):
            Circle(3.0)
        with BuildSketch(Plane.XY.offset(CAVITY_Z + 26.0)):
            Circle(1.5)
        loft(mode=Mode.SUBTRACT)

        # Sprue vertical drop
        with Locations((0, 0, CAVITY_Z + 26.0/2.0)):
            Cylinder(radius=1.5, height=26.0, mode=Mode.SUBTRACT)

        # 4. Air Bleed / Vents
        y_vent = HEX_DIAM / 2.0 - 2.0
        h_vent = MOLD_H - (CAVITY_Z + 26.0) + 0.2
        z_vent = (MOLD_H + CAVITY_Z + 26.0) / 2.0
        with Locations(( -0.0001, y_vent, z_vent ), ( -0.0001, -y_vent, z_vent )):
            Box(1.5, 1.5, h_vent, mode=Mode.SUBTRACT)

        # Vents to corners
        with Locations(( 0, y_vent, CAVITY_Z + 26.0 ), ( 0, -y_vent, CAVITY_Z + 26.0 )):
            Sphere(radius=1.5, mode=Mode.SUBTRACT)

        # 5. Clamping Bolt Holes
        for y_sign in [1, -1]:
            for z_sign in [1, -1]:
                y = y_sign * BOLT_Y_OFFSET
                z = MOLD_H / 2.0 + z_sign * BOLT_Z_OFFSET
                # Bolt shaft - apply tolerance for smooth bolt insertion
                with Locations(( -MOLD_T - 0.5, y, z )):
                    Cylinder(radius=(BOLT_D + TOLERANCE)/2.0, height=MOLD_T * 2.0 + 1.0,
                             rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                # Bolt head recess
                with Locations(( -MOLD_T - 0.1, y, z )):
                    Cylinder(radius=(BOLT_HEAD_D + TOLERANCE)/2.0, height=BOLT_HEAD_DEPTH * 2.0,
                             rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 6. Gasket Cavity Cutout (Hexagonal)
        with Locations((0, 0, CAVITY_Z)):
            with BuildSketch(Plane.YZ):
                RegularPolygon(radius=PRIMARY_GASKET_DIAM/2.0, side_count=6)
            # Extrude into the block (negative X direction)
            extrude(amount=-GASKET_THICK/2.0, mode=Mode.SUBTRACT)


        # 8. Nanopore specific features
        if is_nanopore:
            # Wafer alignment pins (4 pins, offset diagonally)
            for y_sign in [1, -1]:
                for z_sign in [1, -1]:
                    pin_y = y_sign * (WAFER_SIZE/2.0 + 0.424)
                    pin_z = CAVITY_Z + z_sign * (WAFER_SIZE/2.0 + 0.424)
                    with Locations(( -MOLD_T/2.0, pin_y, pin_z )):
                        Cylinder(radius=(1.2 + TOLERANCE)/2.0, height=MOLD_T + 2.0,
                                 rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            # Top passive ports (pass-through holes)
            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
                # Rotate around X-axis in mold space
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0) * Location((0, PORT_RADIUS, 0))
                with Locations(port_loc):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0,
                             rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            # Active Bottom ports (Bosses that create channels in the gasket)
            for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0)
                # Port pin
                with Locations(port_loc * Location((0, PORT_RADIUS, 0))):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.ADD)
                # Channel boss
                with Locations(port_loc):
                    with BuildSketch(Plane.YZ):
                        with Locations((PORT_RADIUS, 0), (0, 0)):
                            Circle(0.6)
                        make_hull()
                    extrude(amount=-GASKET_THICK/2.0, mode=Mode.ADD)

            # Weep Duct Pins
            with Locations((0, 0, CAVITY_Z)):
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((-GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)

        else:
            # 7. Apply Circuitry_Cutouts to the gasket cavity ONLY for amplifier gasket (without nanopore)
            # as requested in the bug fix instructions.
            cutouts = Circuitry_Cutouts(height=GASKET_THICK * 3.0)
            cutouts = cutouts.move(Rotation(90, 0, 90)).move(Location((0, 0, CAVITY_Z)))
            add(cutouts, mode=Mode.SUBTRACT)

            # Amplifier Gasket Mode
            # Central square plug (forms the hole)
            with Locations(( -GASKET_THICK/4.0, 0, CAVITY_Z )):
                Box(GASKET_THICK/2.0, WAFER_HOLE_SIZE, WAFER_HOLE_SIZE, mode=Mode.ADD)

            # Passive top ports
            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0) * Location((0, PORT_RADIUS, 0))
                with Locations(port_loc):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            # Active bottom ports
            for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0)
                with Locations(port_loc * Location((0, PORT_RADIUS, 0))):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.ADD)
                with Locations(port_loc):
                    with BuildSketch(Plane.YZ):
                        with Locations((PORT_RADIUS, 0), (0, 0)):
                            Circle(0.6)
                        make_hull()
                    extrude(amount=-GASKET_THICK/2.0, mode=Mode.ADD)

            # Weep Duct Pins
            with Locations((0, 0, CAVITY_Z)):
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((-GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)

    return p.part


def Nanopore_Wafer_Mold_Right(is_nanopore=True, gasket_type="top"):
    """
    Right mold half (X > 0 in assembly).
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        # 1. Base Block
        with Locations(( MOLD_T/2.0, 0, MOLD_H/2.0 )):
            add(Rounded_Mold_Block(MOLD_T, MOLD_W, MOLD_H, r=4.0))

        # 2. Subtract Reservoir
        with Locations(( 0.01, 0, MOLD_H - RES_D/2.0 + 0.1 )):
            add(Rounded_Reservoir_Block(RES_T * 2.0, MOLD_W - 10.0, RES_D, r=2.0), mode=Mode.SUBTRACT)

        # 3. Tapered Sprue Channel
        with BuildSketch(Plane.XY.offset(MOLD_H - RES_D)):
            Circle(3.0)
        with BuildSketch(Plane.XY.offset(CAVITY_Z + 26.0)):
            Circle(1.5)
        loft(mode=Mode.SUBTRACT)

        with Locations((0, 0, CAVITY_Z + 26.0/2.0)):
            Cylinder(radius=1.5, height=26.0, mode=Mode.SUBTRACT)

        # 4. Air Bleed / Vents
        y_vent = HEX_DIAM / 2.0 - 2.0
        h_vent = MOLD_H - (CAVITY_Z + 26.0) + 0.2
        z_vent = (MOLD_H + CAVITY_Z + 26.0) / 2.0
        with Locations(( 0.001, y_vent, z_vent ), ( 0.001, -y_vent, z_vent )):
            Box(1.5, 1.5, h_vent, mode=Mode.SUBTRACT)

        with Locations(( 0, y_vent, CAVITY_Z + 26.0 ), ( 0, -y_vent, CAVITY_Z + 26.0 )):
            Sphere(radius=1.5, mode=Mode.SUBTRACT)

        # 5. Clamping Bolt Holes
        for y_sign in [1, -1]:
            for z_sign in [1, -1]:
                y = y_sign * BOLT_Y_OFFSET
                z = MOLD_H / 2.0 + z_sign * BOLT_Z_OFFSET
                with Locations(( MOLD_T + 0.5, y, z )):
                    Cylinder(radius=(BOLT_D + TOLERANCE)/2.0, height=MOLD_T * 2.0 + 1.0,
                             rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                with Locations(( MOLD_T - BOLT_HEAD_DEPTH + 0.1, y, z )):
                    Cylinder(radius=(BOLT_HEAD_D + TOLERANCE)/2.0, height=BOLT_HEAD_DEPTH * 2.0,
                             rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 6. Gasket Cavity Cutout
        with Locations((0, 0, CAVITY_Z)):
            with BuildSketch(Plane.YZ):
                RegularPolygon(radius=PRIMARY_GASKET_DIAM/2.0, side_count=6)
            # Extrude in positive X direction
            extrude(amount=GASKET_THICK/2.0, mode=Mode.SUBTRACT)


        # 8. Nanopore specific features
        if is_nanopore:
            # Central Protective Plug
            with Locations((GASKET_THICK/2.0, 0, CAVITY_Z)):
                # From meeting surface to wafer
                Cylinder(radius=PLUG_DIAMETER/2.0, height=GASKET_THICK + PCB_THICKNESS*2,
                         rotation=(0, 90, 0), mode=Mode.ADD)

            # Wafer seating lip / recess in the plug
            # Subtracted from the plug
            with Locations(( GASKET_THICK/2.0 + PCB_THICKNESS - WAFER_RECESS, 0, CAVITY_Z )):
                Box(WAFER_RECESS * 2.0, WAFER_SIZE, WAFER_SIZE, mode=Mode.SUBTRACT)

            # Alignment pins
            for y_sign in [1, -1]:
                for z_sign in [1, -1]:
                    pin_y = y_sign * (WAFER_SIZE/2.0 + 0.424)
                    pin_z = CAVITY_Z + z_sign * (WAFER_SIZE/2.0 + 0.424)
                    with Locations(( MOLD_T/2.0, pin_y, pin_z )):
                        Cylinder(radius=(1.2 + TOLERANCE)/2.0, height=MOLD_T + 2.0,
                                 rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            # Top Active ports (Bosses)
            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0)
                with Locations(port_loc * Location((0, PORT_RADIUS, 0))):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.ADD)
                with Locations(port_loc):
                    with BuildSketch(Plane.YZ):
                        with Locations((PORT_RADIUS, 0), (0, 0)):
                            Circle(0.6)
                        make_hull()
                    extrude(amount=GASKET_THICK/2.0, mode=Mode.ADD)

            # Weep Duct Pins and Trench Boss
            with Locations((0, 0, CAVITY_Z)):
                # Core pin for duct
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)
                # Raised boss for the trench (molded into top face)
                add(Weep_Trench_Cutout().move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0 - WEEP_MOAT_DEPTH/2.0, 0, 0))), mode=Mode.ADD)

            # Bottom Passive ports
            for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0) * Location((0, PORT_RADIUS, 0))
                with Locations(port_loc):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        else:
            # 7. Apply Circuitry_Cutouts to the gasket cavity ONLY for amplifier gasket (without nanopore)
            # The right half also needs it for full clearance if it protrudes.
            cutouts = Circuitry_Cutouts(height=GASKET_THICK * 3.0)
            cutouts = cutouts.move(Rotation(90, 0, 90)).move(Location((0, 0, CAVITY_Z)))
            add(cutouts, mode=Mode.SUBTRACT)

            # Amplifier Gasket
            with Locations(( GASKET_THICK/4.0, 0, CAVITY_Z )):
                Box(GASKET_THICK/2.0, WAFER_HOLE_SIZE, WAFER_HOLE_SIZE, mode=Mode.ADD)

            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0) * Location((0, PORT_RADIUS, 0))
                with Locations(port_loc):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
                port_loc = Location((0, 0, CAVITY_Z)) * Rotation(a, 0, 0)
                with Locations(port_loc * Location((0, PORT_RADIUS, 0))):
                    Cylinder(radius=1.0, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.ADD)
                with Locations(port_loc):
                    with BuildSketch(Plane.YZ):
                        with Locations((PORT_RADIUS, 0), (0, 0)):
                            Circle(0.6)
                        make_hull()
                    extrude(amount=GASKET_THICK/2.0, mode=Mode.ADD)

            # Weep Duct Pins and Trench Boss
            with Locations((0, 0, CAVITY_Z)):
                # Core pin for duct
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)
                # Raised boss for the trench (molded into top face)
                add(Weep_Trench_Cutout().move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0 - WEEP_MOAT_DEPTH/2.0, 0, 0))), mode=Mode.ADD)

    return p.part

if __name__ == "__main__":
    from build123d.exporters3d import export_step

    # Test export
    left_mold = Nanopore_Wafer_Mold_Left(is_nanopore=False)
    right_mold = Nanopore_Wafer_Mold_Right(is_nanopore=False)

    # Orient flat for 3D printing
    left_flat = left_mold.move(Rotation(0, -90, 0)).move(Location((0, 0, MOLD_T/2.0)))
    right_flat = right_mold.move(Rotation(0, 90, 0)).move(Location((0, 0, MOLD_T/2.0)))

    export_step(left_flat, "Nanopore_Wafer_Mold_Left.step")
    export_step(right_flat, "Nanopore_Wafer_Mold_Right.step")
    print("Exported Left and Right Molds as STEP files.")
