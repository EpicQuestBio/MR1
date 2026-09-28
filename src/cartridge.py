from build123d import *
import math
from src.constants import *
from src.common import Circuitry_Cutouts, Finger_Grip_Cutout, Hex_Base_Sketch, Weep_Duct_Holes, Weep_Trench_Cutout

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
        # Base Hexagon matching PCB source of truth
        add(Hex_Base_Sketch())

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
    """The Amplifier PCB matching KiCad source of truth (55.0 x 51.962 mm).
    Features an opened 6.20 x 6.20 mm diamond cutout (rotated 45 deg) matching KiCad Edge.Cuts,
    providing clean 0.1mm clearance for the fully encapsulated silicone protrusion.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
            if USE_NANOPORE_WAFER_GASKET:
                Rectangle(PCB_WAFER_HOLE_SIZE, PCB_WAFER_HOLE_SIZE, rotation=WAFER_ROTATION, mode=Mode.SUBTRACT)
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

def Nanopore_Wafer_Silicon():
    """Solid-state silicon nanopore chip (4.0 x 4.0 x 0.5 mm) rotated 45 degrees.
    Embedded inside the cast silicone gasket between Cis and Trans fluidic chambers.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(WAFER_SIZE, WAFER_SIZE, WAFER_THICK, rotation=(0, 0, WAFER_ROTATION))
        # Central membrane aperture (0.5mm window)
        Cylinder(radius=0.25, height=WAFER_THICK + 0.2, mode=Mode.SUBTRACT)
    return p.part

def Cast_Nanopore_Wafer_Gasket():
    """Top cast silicone gasket with embedded nanopore wafer and continuous Cis flow channel.
    Channel runs along the X-diagonal: 210 deg -> Center -> 30 deg.
    Passive through-holes at 330 deg and 150 deg allow Trans fluid pass-through.
    The nanopore silicon chip is embedded inside the gasket, rotated 45 degrees,
    with a silicone protrusion (6.0 x 6.0 mm, 45 deg) that nests through the opened PCB hole.
    """
    p_in = (-PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30))) # 210 deg
    p_out = (PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30)))   # 30 deg
    q_in = (PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30)))  # 330 deg
    q_out = (-PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30))) # 150 deg

    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
        extrude(amount=GASKET_THICK)

        # Silicone protrusion on PCB-facing side (Z < 0), rotated 45 degrees
        with Locations((0, 0, -PCB_THICKNESS/2.0)):
            Box(PROTRUSION_SIZE, PROTRUSION_SIZE, PCB_THICKNESS, rotation=(0, 0, PROTRUSION_ROTATION))

        # Embedded square silicon wafer pocket, rotated 45 degrees
        with Locations((0, 0, -PCB_THICKNESS/2.0)):
            Box(WAFER_SIZE + 0.1, WAFER_SIZE + 0.1, WAFER_THICK + 0.1, rotation=(0, 0, WAFER_ROTATION), mode=Mode.SUBTRACT)

        # Central aperture through protrusion to expose nanopore sensing window to fluid
        Cylinder(radius=PLUG_DIAMETER/2.0, height=GASKET_THICK + PCB_THICKNESS*2.0 + 2.0, mode=Mode.SUBTRACT)

        # Passive pass-through holes for bottom/Trans ports
        with Locations((0, 0, GASKET_THICK/2.0)):
            with Locations((q_in[0], q_in[1], 0), (q_out[0], q_out[1], 0)):
                Cylinder(radius=1.0, height=GASKET_THICK + 2.0, mode=Mode.SUBTRACT)

        # Active flow channels
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
            with Locations(Location((0, 0, GASKET_THICK/2.0)) * Rotation(0, 0, a)):
                with BuildSketch():
                    with Locations((PORT_RADIUS, 0), (0, 0)):
                        Circle(0.6)
                    make_hull()
            extrude(amount=GASKET_THICK + 0.1, mode=Mode.SUBTRACT)

        # Active Cis flow channel (210 deg -> Center -> 30 deg continuous channel)
        with Locations((0, 0, GASKET_THICK/2.0)):
            with BuildSketch():
                with Locations(p_in, (0, 0), p_out):
                    Circle(radius=FLUID_CHANNEL_W/2.0)
                make_hull()
                Circle(radius=CHAMBER_DIAM/2.0)
                with Locations(p_in, p_out):
                    Circle(radius=1.0)
            extrude(amount=GASKET_THICK + 0.1, mode=Mode.SUBTRACT)

        # Weep system cutouts
        with Locations((0, 0, GASKET_THICK/2.0)):
            add(Weep_Duct_Holes(height=GASKET_THICK + 2.0), mode=Mode.SUBTRACT)
        # Molded wick trench on the top face
        with Locations((0, 0, GASKET_THICK - WEEP_MOAT_DEPTH/2.0)):
            add(Weep_Trench_Cutout(), mode=Mode.SUBTRACT)

    return p.part

def Fitted_Amplifier_Gasket():
    """Bottom cast silicone gasket for amplifier with continuous Trans flow channel.
    Channel runs along the X-diagonal: 330 deg -> Center -> 150 deg.
    Passive through-holes at 210 deg and 30 deg allow Cis fluid pass-through.
    """
    p_in = (-PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30))) # 210 deg
    p_out = (PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30)))   # 30 deg
    q_in = (PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30)))  # 330 deg
    q_out = (-PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30))) # 150 deg

    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
        extrude(amount=GASKET_THICK)

        # Passive pass-through holes for top/Cis ports
        with Locations((0, 0, GASKET_THICK/2.0)):
            with Locations((p_in[0], p_in[1], 0), (p_out[0], p_out[1], 0)):
                Cylinder(radius=1.0, height=GASKET_THICK + 2.0, mode=Mode.SUBTRACT)

        # Active Trans flow channel (330 deg -> Center -> 150 deg continuous channel)
        with Locations((0, 0, GASKET_THICK/2.0)):
            with BuildSketch():
                with Locations(q_in, (0, 0), q_out):
                    Circle(radius=FLUID_CHANNEL_W/2.0)
                make_hull()
                Circle(radius=CHAMBER_DIAM/2.0)
                with Locations(q_in, q_out):
                    Circle(radius=1.0)
            extrude(amount=GASKET_THICK + 0.1, mode=Mode.SUBTRACT)

        # Circuitry clearance cutouts on bottom face
        add(Circuitry_Cutouts(height=GASKET_THICK * 2.0), mode=Mode.SUBTRACT)

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
    """Bottom TPU Seal plate. Exact match to golden STL (55.0 x 51.962 x 3.0 mm)."""
    height = 3.0
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
        extrude(amount=height)

        # Subtract Cutouts
        add(Circuitry_Cutouts(height=height*3.0), mode=Mode.SUBTRACT)

        # Ports (4x)
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            ang_rad = math.radians(a)
            px = PORT_RADIUS * math.cos(ang_rad)
            py = PORT_RADIUS * math.sin(ang_rad)
            with Locations((px, py, height/2.0)):
                Cylinder(radius=NPT_1_8_TAP_D/2.0, height=height + 1.0, mode=Mode.SUBTRACT)
            with Locations(Location((0, 0, PP_H/2.0)) * Rotation(0, 0, a) * Location((PORT_RADIUS, 0, 0))):
                Cylinder(radius=NPT_1_8_TAP_D/2.0, height=PP_H + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PP_H/2.0)):
            add(Weep_Duct_Holes(height=PP_H + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Plate_1_Base_Hex():
    """Base PP Plate with exact KiCad hex profile."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
        extrude(amount=PLATE_THICK)

        add(Circuitry_Cutouts(height=PLATE_THICK*3.0), mode=Mode.SUBTRACT)

        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            ang_rad = math.radians(a)
            px = PORT_RADIUS * math.cos(ang_rad)
            py = PORT_RADIUS * math.sin(ang_rad)
            with Locations((px, py, PLATE_THICK/2.0)):
                Cylinder(radius=NPT_1_8_TAP_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PLATE_THICK/2.0)):
            add(Weep_Duct_Holes(height=PLATE_THICK + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Plate_3_Top_Hex():
    """Top PP Plate with central pipette access and fluid ports."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
        extrude(amount=PLATE_THICK)

        # Central hole
        Cylinder(radius=PIPETTE_ACCESS_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP]:
            ang_rad = math.radians(a)
            px = PORT_RADIUS * math.cos(ang_rad)
            py = PORT_RADIUS * math.sin(ang_rad)
            with Locations((px, py, PLATE_THICK/2.0)):
                Cylinder(radius=FLUID_PORT_D/2.0, height=PLATE_THICK + 1.0, mode=Mode.SUBTRACT)

        # Weep duct pass-through
        with Locations((0, 0, PLATE_THICK/2.0)):
            add(Weep_Duct_Holes(height=PLATE_THICK + 2.0), mode=Mode.SUBTRACT)

    return p.part

def Pressure_Puck():
    """Pressure puck for cap interaction. Exact match to golden STL (59.15 x 60.0 x 6.0 mm)."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main Body
        Cylinder(radius=(HEX_DIAM)/2.0, height=PUCK_H)

        # Center Hole
        with Locations((0,0,-5)):
            Cone(bottom_radius=3.0, top_radius=8.0, height=20.0, mode=Mode.SUBTRACT)

        # Underside recess
        with Locations((0,0,-5)):
            with BuildPart(mode=Mode.PRIVATE) as recess:
                Cylinder(radius=(NECK_ID - 4.0)/2.0, height=8.4)
                Cylinder(radius=10.0, height=10.0, mode=Mode.SUBTRACT)
            add(recess.part, mode=Mode.SUBTRACT)

        # Recessed Cups at X = +/- 30
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
