from build123d import *
import math
from src.constants import *
from src.common import Circuitry_Cutouts, Finger_Grip_Cutout, Weep_Duct_Holes, Weep_Trench_Cutout

def PogoPinHoles():
    """Returns a sketch containing the pogo pin holes."""
    with BuildSketch(mode=Mode.PRIVATE) as p:
        for x_sign in [1, -1]:
            for x_offset in [1.5, 6.5, 11.5]: # Hardcoded from original OpenSCAD
                with Locations((x_sign * x_offset, POGO_Y)):
                    Circle(0.5)
    return p.sketch

def PCB_Main_Reader_2D():
    """Main Reader PCB profile."""
    with BuildSketch(mode=Mode.PRIVATE) as p:
        # Base Hexagon
        RegularPolygon(radius=HEX_DIAM/2.0, side_count=6)

        # Central Cutout
        Circle(radius=CARRIER_DIAM/2.0, mode=Mode.SUBTRACT)

        # Pogo Pins
        add(PogoPinHoles(), mode=Mode.SUBTRACT)

        # Fluid Port Clearances (6mm)
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((PORT_RADIUS, 0)) * Rotation(a)):
                Circle(radius=3.0, mode=Mode.SUBTRACT)

        # Cutouts for Back Connectors
        with Locations((0, HEX_DIAM/2.0)):
            Rectangle(32, 10, mode=Mode.SUBTRACT)
    return p.sketch

def PCB_Rigid_Active():
    """The Amplifier PCB."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=HEX_DIAM/2.0, side_count=6)
            if USE_NANOPORE_WAFER_GASKET:
                Rectangle(WAFER_HOLE_SIZE, WAFER_HOLE_SIZE, mode=Mode.SUBTRACT)
            else:
                Circle(radius=CARRIER_DIAM/2.0, mode=Mode.SUBTRACT)

            # Fluid port pass-throughs
            for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
                with Locations(Location((PORT_RADIUS, 0)) * Rotation(a)):
                    Circle(radius=1.0, mode=Mode.SUBTRACT)

            add(PogoPinHoles(), mode=Mode.SUBTRACT)

        extrude(amount=PCB_THIN)

        # Weep duct pass-through
        with Locations((0, 0, PCB_THIN/2.0)):
            add(Weep_Duct_Holes(height=PCB_THIN + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Cast_Nanopore_Wafer_Gasket():
    """Top cast silicone gasket with embedded nanopore wafer."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=PRIMARY_GASKET_DIAM/2.0, side_count=6)
        extrude(amount=GASKET_THICK)

        # Protrusion
        with Locations((0, 0, -PCB_THICKNESS/2.0)):
            Box(PROTRUSION_SIZE, PROTRUSION_SIZE, PCB_THICKNESS)

        # Finger Grip
        add(Finger_Grip_Cutout(height=GASKET_THICK + 10.0), mode=Mode.SUBTRACT)

        # Wafer pocket
        with Locations((0, 0, PCB_THICKNESS/2.0 + WAFER_RECESS + WAFER_THICK/2.0)):
            Box(WAFER_SIZE + 0.1, WAFER_SIZE + 0.1, WAFER_THICK + 0.1, mode=Mode.SUBTRACT)

        # Central hole
        Cylinder(radius=PLUG_DIAMETER/2.0, height=GASKET_THICK + PCB_THICKNESS*2.0 + 2.0, mode=Mode.SUBTRACT)

        # Ports
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, GASKET_THICK/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=1.0, height=GASKET_THICK + 2.0, mode=Mode.SUBTRACT)

        # Active flow channels
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, GASKET_THICK/2.0)) * Rotation(0, 0, a)):
                with BuildSketch():
                    with Locations((PORT_RADIUS, 0), (0, 0)):
                        Circle(0.6)
                    make_hull()
                extrude(amount=GASKET_THICK + 0.1, mode=Mode.SUBTRACT)

        # Weep system cutouts
        with Locations((0, 0, GASKET_THICK/2.0)):
            add(Weep_Duct_Holes(height=GASKET_THICK + 2.0), mode=Mode.SUBTRACT)
        # Molded wick trench on the top face
        with Locations((0, 0, GASKET_THICK - WEEP_MOAT_DEPTH/2.0)):
            add(Weep_Trench_Cutout(), mode=Mode.SUBTRACT)

    return p.part

def Fitted_Amplifier_Gasket():
    """Bottom cast silicone gasket for amplifier."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=PRIMARY_GASKET_DIAM/2.0, side_count=6)
        extrude(amount=GASKET_THICK)

        add(Finger_Grip_Cutout(height=GASKET_THICK + 10.0), mode=Mode.SUBTRACT)

        # Central hole
        Box(WAFER_HOLE_SIZE, WAFER_HOLE_SIZE, GASKET_THICK + 2.0, mode=Mode.SUBTRACT)

        # Passive Ports
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, GASKET_THICK/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=1.0, height=GASKET_THICK + 2.0, mode=Mode.SUBTRACT)

        # Active flow channels
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
            with Locations(Location((0, 0, GASKET_THICK/2.0)) * Rotation(0, 0, a)):
                with Locations((PORT_RADIUS, 0, 0)):
                    Cylinder(radius=1.0, height=GASKET_THICK + 2.0, mode=Mode.SUBTRACT)
                with BuildSketch():
                    with Locations((PORT_RADIUS, 0), (0, 0)):
                        Circle(0.6)
                    make_hull()
                extrude(amount=GASKET_THICK + 0.1, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, GASKET_THICK/2.0)):
            add(Weep_Duct_Holes(height=GASKET_THICK + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Bottom_Pusher_Plate():
    """Bottom TPU Seal plate."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=HEX_DIAM/2.0, side_count=6)
        extrude(amount=PP_H)

        # Subtract Cutouts
        add(Circuitry_Cutouts(height=PP_H*3.0), mode=Mode.SUBTRACT)
        add(Finger_Grip_Cutout(height=PP_H*3.0), mode=Mode.SUBTRACT)

        # Ports
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, PP_H/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=NPT_1_8_TAP_D/2.0, height=PP_H + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PP_H/2.0)):
            add(Weep_Duct_Holes(height=PP_H + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Plate_1_Base_Hex():
    """Base PP Plate."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=HEX_DIAM/2.0, side_count=6)
        extrude(amount=PLATE_THICK)

        add(Circuitry_Cutouts(height=PLATE_THICK*3.0), mode=Mode.SUBTRACT)
        add(Finger_Grip_Cutout(height=PLATE_THICK*3.0), mode=Mode.SUBTRACT)

        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, PLATE_THICK/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=NPT_1_8_TAP_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PLATE_THICK/2.0)):
            add(Weep_Duct_Holes(height=PLATE_THICK + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Plate_3_Top_Hex():
    """Top PP Plate."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            RegularPolygon(radius=HEX_DIAM/2.0, side_count=6)
        extrude(amount=PLATE_THICK)

        add(Finger_Grip_Cutout(height=PLATE_THICK*3.0), mode=Mode.SUBTRACT)

        # Central hole
        Cylinder(radius=PIPETTE_ACCESS_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, PLATE_THICK/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=FLUID_PORT_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PLATE_THICK/2.0)):
            add(Weep_Duct_Holes(height=PLATE_THICK + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Pressure_Puck():
    """Pressure puck for cap interaction."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main Body
        Cylinder(radius=(NECK_ID - 1.0)/2.0, height=PUCK_H)

        # Center Hole
        with Locations((0,0,-5)):
            Cone(bottom_radius=3.0, top_radius=8.0, height=20.0, mode=Mode.SUBTRACT)

        # Underside recess
        with Locations((0,0,-5)):
            with BuildPart(mode=Mode.PRIVATE) as recess:
                Cylinder(radius=(NECK_ID - 4.0)/2.0, height=8.4)
                Cylinder(radius=10.0, height=10.0, mode=Mode.SUBTRACT)
            add(recess.part, mode=Mode.SUBTRACT)

        # Recessed Cups
        with Locations((0,0,3)):
            add(Finger_Grip_Cutout(height=20.0), mode=Mode.SUBTRACT)
    return p.part

if __name__ == "__main__":
    from build123d.exporters3d import export_step

    export_step(Bottom_Pusher_Plate(), "Bottom_Pusher_Plate.step")
    export_step(Plate_1_Base_Hex(), "Plate_1_Base_Hex.step")
    export_step(Plate_3_Top_Hex(), "Plate_3_Top_Hex.step")
    export_step(Cast_Nanopore_Wafer_Gasket(), "Cast_Nanopore_Wafer_Gasket.step")
    export_step(Fitted_Amplifier_Gasket(), "Fitted_Amplifier_Gasket.step")
    export_step(Pressure_Puck(), "Pressure_Puck.step")
    export_step(PCB_Rigid_Active(), "PCB_Rigid_Active.step")

    print("Exported Cartridge Stack Components as STEP files.")
