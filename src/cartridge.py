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
    """Main Reader PCB 2D profile (80 x 60 mm rectangular motherboard).
    Matches OpenSCAD modules/housing_reader.scad:PCB_Main_Reader_2D.
    Includes 4 standoff mounting holes, 2 USB-C rear cutouts,
    1 JST connector clearance cutout, and 4 fluid pass-through holes.
    """
    with BuildSketch(mode=Mode.PRIVATE) as s:
        Rectangle(PCB_W, PCB_L)

        # Mounting holes matching lid standoffs (+/- (PCB_W/2 - 2), +/- (PCB_L/2 - 2))
        for mx in [-PCB_W / 2.0 + 2.0, PCB_W / 2.0 - 2.0]:
            for my in [-PCB_L / 2.0 + 2.0, PCB_L / 2.0 - 2.0]:
                with Locations((mx, my)):
                    Circle(radius=3.2 / 2.0, mode=Mode.SUBTRACT)

        # Dual USB-C back edge cutouts (at X = +/-15, Y = 25, size 14 x 10.1 mm)
        with Locations((-15.0, 25.0), (15.0, 25.0)):
            Rectangle(14.0, 10.1, mode=Mode.SUBTRACT)

        # Fluid port clearance holes (D=6mm at PORT_RADIUS=20mm)
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP, ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
            ang_rad = math.radians(a)
            with Locations((PORT_RADIUS * math.cos(ang_rad), PORT_RADIUS * math.sin(ang_rad))):
                Circle(radius=3.0, mode=Mode.SUBTRACT)

        # JST vertical connector clearance cutout (centered at [0, -19], size 14 x 10 mm)
        with Locations((0.0, -19.0)):
            Rectangle(14.0, 10.0, mode=Mode.SUBTRACT)

    return s.sketch

def PCB_Main_Reader():
    """Main Reader PCB 3D solid (80 x 60 x 1.6 mm FR4 motherboard)."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(PCB_Main_Reader_2D())
        extrude(amount=PCB_THICK)
    return p.part

def PCB_Pump_Controller_2D():
    """Pump Controller & USB-PD Hub PCB 2D profile (88 x 88 mm square).
    Matches Housing_Pump_Case bucket (90 x 90 mm) and mounting pattern.
    Includes:
    - 4 corner mounting holes (D=3.2mm) at (+/-38.0, +/-38.0)
    - 2 rear USB-C edge cutouts at X = +/-15.0 mm, Y = 44.0 mm (matching Housing_Pump_Case cutouts)
    - 2 peristaltic pump motor cutouts at X = +/-25.0 mm, Y = 20.0 mm
    - 2 pressure transducer clearance holes at X = +/-32.0 mm, Y = 0.0 mm
    """
    with BuildSketch(mode=Mode.PRIVATE) as s:
        Rectangle(88.0, 88.0)
        # Fillet corners with 2.0 mm radius
        fillet(s.vertices(), radius=2.0)

        # 4 corner mounting holes
        for mx in [-38.0, 38.0]:
            for my in [-38.0, 38.0]:
                with Locations((mx, my)):
                    Circle(radius=3.2 / 2.0, mode=Mode.SUBTRACT)

        # Dual USB-C back edge cutouts at X = +/-15, Y = 44.0 (size 14 x 10 mm)
        with Locations((-15.0, 44.0), (15.0, 44.0)):
            Rectangle(14.0, 10.0, mode=Mode.SUBTRACT)

        # Peristaltic pump motor cutouts at X = +/-25, Y = 20
        for px in [-25.0, 25.0]:
            with Locations((px, 20.0)):
                Circle(radius=PUMP_MOUNT_D / 2.0, mode=Mode.SUBTRACT)

        # Pressure transducer fluid clearance holes at X = +/-32, Y = 0
        with Locations((-32.0, 0.0), (32.0, 0.0)):
            Circle(radius=6.35 / 2.0, mode=Mode.SUBTRACT)

    return s.sketch

def PCB_Pump_Controller():
    """Pump Controller & USB-PD Hub PCB 3D solid (88 x 88 x 1.6 mm FR4)."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(PCB_Pump_Controller_2D())
        extrude(amount=1.6)
    return p.part

def Carrier_Frame_Hex():
    """Hexagonal Carrier Frame (Plate 2 Channel) holding the active PCB.
    Matches OpenSCAD modules/cartridge.scad:Carrier_Frame_Hex.
    Hex diameter 60mm with finger grip notches, 28.5 x 38.5 mm central pocket,
    and 4 fluid pass-through holes (D=4mm).
    Thickness = 2.6 mm (CARRIER_THICK).
    """
    ins_w = 28.0
    ins_l = 38.0
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            add(Hex_Base_Sketch())
            # Central PCB through-pocket
            Rectangle(ins_w + 0.5, ins_l + 0.5, mode=Mode.SUBTRACT)
            # Fluid pass-throughs
            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP, ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
                ang_rad = math.radians(a)
                with Locations((PORT_RADIUS * math.cos(ang_rad), PORT_RADIUS * math.sin(ang_rad))):
                    Circle(radius=2.0, mode=Mode.SUBTRACT)
        extrude(amount=CARRIER_THICK)
    return p.part

def Nanopore_Carrier():
    """Round Nanopore Carrier PCB (20.0 mm diameter x 0.8 mm thickness).
    Matches OpenSCAD modules/cartridge.scad:Nanopore_Carrier.
    Features central 1.5mm chip aperture and lateral tab slots.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch():
            Circle(radius=CARRIER_DIAM / 2.0)
            Circle(radius=1.5 / 2.0, mode=Mode.SUBTRACT)
            for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_IN_BOT]:
                ang_rad = math.radians(a)
                with Locations((CARRIER_DIAM / 2.0 * math.cos(ang_rad), CARRIER_DIAM / 2.0 * math.sin(ang_rad))):
                    Rectangle(4.0, 6.0, rotation=a, mode=Mode.SUBTRACT)
        extrude(amount=PCB_THIN)
    return p.part

def Silver_Chloride_Ribbon_Pads(top=True, length=2.0, width=0.8, thickness=0.1):
    """Silver Chloride (Ag/AgCl) ribbon electrode pads for microfluidic channels.
    top=True: Top Cis chamber pads along ANGLE_FLUID_IN_TOP (30 deg) at r=12mm and r=17mm.
    top=False: Bottom Trans chamber pads along ANGLE_FLUID_IN_BOT (210 deg) at r=12mm and r=17mm.
    """
    angle = ANGLE_FLUID_IN_TOP if top else ANGLE_FLUID_IN_BOT
    pad_inner_r = 12.0
    pad_outer_r = 17.0
    with BuildPart(mode=Mode.PRIVATE) as p:
        for r_dist in [pad_inner_r, pad_outer_r]:
            with Locations(Location((0, 0, 0)) * Rotation(0, 0, angle)):
                with Locations((r_dist, 0, 0)):
                    Box(length, width, thickness)
    return p.part

def PTFE_Interposer(render_electrodes=False):
    """The PTFE / Rogers RO4350B Interposer Circuit Board (55.0 x 51.962 x 0.8 mm).
    Serves as the mechanical fluidic partition and low-noise electrical interface
    between Cis and Trans chambers:
    - Interfaces with pogo pin connector array on the reader unit
    - Top surface interfaces with Cast_Nanopore_Wafer_Gasket (Cis fluid chamber)
    - Bottom surface interfaces with Fitted_Amplifier_Gasket (Trans fluid chamber)
    - Dual-sided silver chloride (Ag/AgCl) ribbon electrode pads positioned in flow paths
    - Central opened 6.20 x 6.20 mm diamond cutout (45 deg) for silicone protrusion
    - 4 fluid pass-through holes at PORT_RADIUS=20mm (d=2.0mm)
    - Pogo pin landing array at Y=2.5mm (X = +/-1.5, +/-6.5, +/-11.5mm)
    - Weep duct moisture pass-throughs for early leak detection
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
                ang_rad = math.radians(a)
                with Locations((PORT_RADIUS * math.cos(ang_rad), PORT_RADIUS * math.sin(ang_rad))):
                    Circle(radius=1.0, mode=Mode.SUBTRACT)

            add(PogoPinHoles(), mode=Mode.SUBTRACT)

        extrude(amount=PCB_THIN)

        # Weep duct pass-through
        with Locations((0, 0, PCB_THIN/2.0)):
            add(Weep_Duct_Holes(height=PCB_THIN + 2.0), mode=Mode.SUBTRACT)

        # Solder mask pad recesses for Ag/AgCl ribbon electrodes
        # Top pads (Z = PCB_THIN) along 30 deg
        for r_dist in [12.0, 17.0]:
            with Locations(Location((0, 0, PCB_THIN)) * Rotation(0, 0, ANGLE_FLUID_IN_TOP)):
                with Locations((r_dist, 0, 0)):
                    Box(2.0, 2.0, 0.05, mode=Mode.SUBTRACT)
                    Box(2.0, 0.8, 0.1, mode=Mode.SUBTRACT)

        # Bottom pads (Z = 0) along 210 deg
        for r_dist in [12.0, 17.0]:
            with Locations(Location((0, 0, 0)) * Rotation(0, 0, ANGLE_FLUID_IN_BOT)):
                with Locations((r_dist, 0, 0)):
                    Box(2.0, 2.0, 0.05, mode=Mode.SUBTRACT)
                    Box(2.0, 0.8, 0.1, mode=Mode.SUBTRACT)

        if render_electrodes:
            # Add Ag/AgCl ribbons
            with Locations((0, 0, PCB_THIN)):
                add(Silver_Chloride_Ribbon_Pads(top=True), mode=Mode.ADD)
            with Locations((0, 0, 0)):
                add(Silver_Chloride_Ribbon_Pads(top=False), mode=Mode.ADD)

    return p.part

# Backward-compatible and functional aliases
PCB_Rigid_Active = PTFE_Interposer
Interposer = PTFE_Interposer

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
