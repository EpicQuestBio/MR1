import math
from build123d import *
from src.constants import *
from src.common import Circuitry_Cutouts, Weep_Duct_Holes, Weep_Trench_Cutout

# Port coordinates on mold YZ plane (mapped with rotate(Axis.Y, 90) around CAVITY_Z):
# Cartridge XY: p_in (210 deg), p_out (30 deg), q_in (330 deg), q_out (150 deg)
# Mapped to YZ plane: y_mold = y_cart, z_mold = CAVITY_Z - x_cart
P_CIS_IN = (-10.0, CAVITY_Z + PORT_RADIUS * math.cos(math.radians(30)))     # Y=-10.0, Z=52.32
P_CIS_OUT = (10.0, CAVITY_Z - PORT_RADIUS * math.cos(math.radians(30)))    # Y=+10.0, Z=17.68
P_TRANS_IN = (-10.0, CAVITY_Z - PORT_RADIUS * math.cos(math.radians(30)))  # Y=-10.0, Z=17.68
P_TRANS_OUT = (10.0, CAVITY_Z + PORT_RADIUS * math.cos(math.radians(30)))  # Y=+10.0, Z=52.32
PASS_PORTS_NANO = [P_TRANS_IN, P_TRANS_OUT]
ALL_PORTS = [P_CIS_IN, P_CIS_OUT, P_TRANS_IN, P_TRANS_OUT]

def Rounded_Mold_Block(t, w, h, r=4.0):
    """Creates a basic mold block with rounded Y-Z corners along the X-axis."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(t, w, h)
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

def build_base_mold_half(is_left=True):
    """
    Constructs the shared structural body of one mold half:
    - Base rounded block (80 x 90 x 15 mm)
    - Top degassing/pouring reservoir (50 x 15 x 12 mm cut)
    - Tapered injection sprue runner (D=6mm -> 3mm down to hex cavity apex at Z=61)
    - Symmetric air bleed vents (1.5 x 1.5 mm up to Z=90)
    - 4 M4 clamping bolt through-holes with counterbores
    - Demolding pry notches (scallops) along top and bottom parting lines
    - Precision alignment interlocks (female sockets on Left, male dowel pins on Right)
    - Hexagonal gasket cavity cutout (0.8mm deep)
    """
    x_center = -MOLD_T / 2.0 if is_left else MOLD_T / 2.0
    with BuildPart(mode=Mode.PRIVATE) as p:
        # 1. Base Rounded Block
        with Locations((x_center, 0, MOLD_H / 2.0)):
            Box(MOLD_T, MOLD_W, MOLD_H)
            edges_to_fillet = p.edges().filter_by(Axis.X)
            if edges_to_fillet:
                fillet(edges_to_fillet, radius=4.0)

        # 2. Top Degassing & Pouring Reservoir (leaves 3mm back wall)
        res_w = HEX_DIAM - 10.0  # 50.0 mm
        res_d = 15.0             # 15.0 mm depth
        res_t = MOLD_T - 3.0     # 12.0 mm thickness cut
        res_x_center = -res_t / 2.0 if is_left else res_t / 2.0
        with Locations((res_x_center, 0, MOLD_H - res_d / 2.0)):
            Box(res_t + 0.1, res_w, res_d + 0.1, mode=Mode.SUBTRACT)

        # 3. Tapered Sprue Channel (stops at hex cavity apex Z=61)
        with BuildSketch(Plane.YZ.offset(0)):
            with Locations((0, MOLD_H - res_d)):
                Circle(3.0)
            with Locations((0, CAVITY_Z + 25.5)):
                Circle(1.5)
            make_hull()
        extrude(amount=-1.5 if is_left else 1.5, mode=Mode.SUBTRACT)

        # 4. Air Bleed Vents (from hex cavity up to mold top)
        for y_vent in [-15.0, 15.0]:
            h_vent = MOLD_H - (CAVITY_Z + 25.5) + 0.1
            z_vent = (MOLD_H + CAVITY_Z + 25.5) / 2.0
            with Locations((-0.75 if is_left else 0.75, y_vent, z_vent)):
                Box(1.51, 1.5, h_vent, mode=Mode.SUBTRACT)

        # 5. Clamping Bolt Holes (M4 clearance + counterbores)
        bolt_y_offset = MOLD_W / 2.0 - 6.0   # 34.0 mm
        bolt_z_offset = MOLD_H / 2.0 - 6.0   # 39.0 mm
        for y_sign in [1, -1]:
            for z_sign in [1, -1]:
                y = y_sign * bolt_y_offset
                z = MOLD_H / 2.0 + z_sign * bolt_z_offset
                # Bolt shaft through-hole
                with Locations((0, y, z)):
                    Cylinder(radius=BOLT_D / 2.0, height=MOLD_T * 2.0 + 1.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                # Counterbore for bolt head / nut
                cb_x = -MOLD_T if is_left else MOLD_T - BOLT_HEAD_DEPTH
                with Locations((cb_x, y, z)):
                    Cylinder(radius=BOLT_HEAD_D / 2.0, height=BOLT_HEAD_DEPTH * 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 6. Demolding Pry Notches (Top & Bottom Scallops on Parting Seam)
        for z_notch in [CAVITY_Z + 30.0, CAVITY_Z - 30.0]:
            with Locations((0, 0, z_notch)):
                Cylinder(radius=5.0, height=2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 7. Alignment Interlocks (Pins on Right, Sockets on Left)
        for y_pin in [-bolt_y_offset, bolt_y_offset]:
            if is_left:
                # Female socket: D=4.2mm, depth 5.0mm into Left half (negative X)
                with Locations((-2.5, y_pin, CAVITY_Z)):
                    Cylinder(radius=2.1, height=5.1, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
            else:
                # Male dowel pin: D=4.0mm, protruding 4.8mm into negative X from X=0
                with Locations((-4.8 / 2.0, y_pin, CAVITY_Z)):
                    Cylinder(radius=2.0, height=4.8, rotation=(0, 90, 0), mode=Mode.ADD)

        # 8. Main Hex Gasket Cavity Cutout (0.8mm deep per half)
        with BuildSketch(Plane.YZ.offset(0)):
            with Locations((0, CAVITY_Z)):
                RegularPolygon(radius=HEX_DIAM / 2.0, side_count=6, rotation=90)
                with Locations((0, HEX_DIAM / 2.0), (0, -HEX_DIAM / 2.0)):
                    Circle(5.0, mode=Mode.SUBTRACT)
        extrude(amount=-GASKET_THICK / 2.0 if is_left else GASKET_THICK / 2.0, mode=Mode.SUBTRACT)

    return p.part

def Nanopore_Wafer_Mold_Left(is_nanopore=True, gasket_type="top"):
    """
    Left mold half (X < 0 in assembly).
    Forms the back face of the gasket where the diamond boss and wafer protrude into the PCB.
    Features:
    - 45-degree diamond protrusion pocket (if is_nanopore=True)
    - Central clamping protective plug (D=2.0mm)
    - 4 wafer corner guide pin holes (D=1.2mm)
    - Passive port core pins (D=2.0mm) for pass-through ports
    - Circuitry cutouts and square central plug (if is_nanopore=False)
    """
    base = build_base_mold_half(is_left=True)
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(base)
        if is_nanopore:
            # 1. Diamond Protrusion Pocket (6.0 x 6.0 mm, 45 deg, depth 0.8mm from X = -GASKET_THICK/2 to -GASKET_THICK/2 - PCB_THICKNESS)
            with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
                with Locations((0, CAVITY_Z)):
                    Rectangle(PROTRUSION_SIZE, PROTRUSION_SIZE, rotation=45)
            extrude(amount=-PCB_THICKNESS, mode=Mode.SUBTRACT)

            # 2. Central Clamping Plug (protects sensing membrane, D=2.0mm from X = -1.6 up to -1.35)
            with Locations((-GASKET_THICK / 2.0 - PCB_THICKNESS + 0.125, 0, CAVITY_Z)):
                Cylinder(radius=PLUG_DIAMETER / 2.0, height=0.25, rotation=(0, 90, 0), mode=Mode.ADD)

            # 3. 4 Corner Wafer Alignment Pin Holes (D=1.2mm through the back to register chip)
            diag_offset = (WAFER_SIZE / 2.0) * math.sqrt(2)
            pin_locs = [
                (0, CAVITY_Z + diag_offset),
                (0, CAVITY_Z - diag_offset),
                (diag_offset, CAVITY_Z),
                (-diag_offset, CAVITY_Z)
            ]
            for pl in pin_locs:
                with Locations((-MOLD_T / 2.0, pl[0], pl[1])):
                    Cylinder(radius=0.6, height=MOLD_T + 2.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

            # 4. Passive Port Core Pins (D=2.0mm, height 0.8mm from X = -GASKET_THICK/2 up to X = 0)
            for port in PASS_PORTS_NANO:
                with Locations((-GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # Weep Duct Pins
            with Locations((0, 0, CAVITY_Z)):
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((-GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)

        else:
            # Amplifier mold (is_nanopore=False)
            cutouts = Circuitry_Cutouts(height=GASKET_THICK * 2.0)
            cutouts = cutouts.rotate(Axis.Y, -90).move(Location((-GASKET_THICK / 2.0, 0, CAVITY_Z)))
            add(cutouts, mode=Mode.SUBTRACT)

            # Central square plug (3.0 x 3.0 mm from X = -GASKET_THICK/2 to X = 0)
            with Locations((-GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Box(GASKET_THICK / 2.0, WAFER_SIZE, WAFER_SIZE, mode=Mode.ADD)

            # Port core pins for passive Cis ports on amplifier gasket
            for port in [P_CIS_IN, P_CIS_OUT]:
                with Locations((-GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # Weep Duct Pins
            with Locations((0, 0, CAVITY_Z)):
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((-GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)

    return p.part

def Nanopore_Wafer_Mold_Right(is_nanopore=True, gasket_type="top"):
    """
    Right mold half (X > 0 in assembly).
    Forms the front channel face of the gasket sealed against Plate 3.
    Features:
    - Male dowel alignment pins protruding 4.8mm from X=0
    - Opposing central clamping protective plug (D=2.0mm)
    - Port core pins meeting Left half at X=0
    - Positive microfluidic channel ridge along Cis path for Nanopore mold
    - Positive microfluidic channel ridge along Trans path for Amplifier mold
    """
    base = build_base_mold_half(is_left=False)
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(base)
        if is_nanopore:
        """
            # 1. Opposing Central Clamping Plug (D=2.0mm from X = +0.8 down to X = 0)
            with Locations((GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Cylinder(radius=PLUG_DIAMETER / 2.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # 2. Port Core Pins (D=2.0mm from X = +0.8 down to X = 0)
            for port in ALL_PORTS:
                with Locations((GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # 3. Cis Active Microfluidic Flow Channel Ridge (1.4mm wide, height 0.8mm from X = 0 to X = 0.8)
            # Extends from cavity floor towards parting plane X=0 to mold open channel in gasket
            with BuildSketch(Plane.YZ.offset(0)):
                with Locations(P_CIS_IN, (0, CAVITY_Z), P_CIS_OUT):
                    Circle(FLUID_CHANNEL_W / 2.0)
        """
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
               # with Locations((0, CAVITY_Z)):
               #     Circle(CHAMBER_DIAM / 2.0)
            extrude(amount=GASKET_THICK / 2.0, mode=Mode.ADD)

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
            # Amplifier mold (is_nanopore=False)
            # 1. Central square plug (3.0 x 3.0 mm from X = +0.8 down to X = 0)
            with Locations((GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Box(GASKET_THICK / 2.0, WAFER_SIZE, WAFER_SIZE, mode=Mode.ADD)

            # 2. Trans Active Microfluidic Channel Ridge (330 deg -> Center -> 150 deg)
            with BuildSketch(Plane.YZ.offset(0)):
                with Locations(P_TRANS_IN, (0, CAVITY_Z), P_TRANS_OUT):
                    Circle(FLUID_CHANNEL_W / 2.0)
                make_hull()
                with Locations((0, CAVITY_Z)):
                    Circle(CHAMBER_DIAM / 2.0)
            extrude(amount=GASKET_THICK / 2.0, mode=Mode.ADD)

            # 3. Port Core Pins
            for port in ALL_PORTS:
                with Locations((GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # Weep Duct Pins and Trench Boss
            with Locations((0, 0, CAVITY_Z)):
                # Core pin for duct
                add(Weep_Duct_Holes(height=GASKET_THICK).move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0, 0, 0))), mode=Mode.ADD)
                # Raised boss for the trench (molded into top face)
                add(Weep_Trench_Cutout().move(Rotation(90, 0, 90)).move(Location((GASKET_THICK/2.0 - WEEP_MOAT_DEPTH/2.0, 0, 0))), mode=Mode.ADD)

    return p.part

def Nanopore_Wafer_Mold_Assembly(explode=0.0, show_gasket=True, is_nanopore=True):
    """
    Returns the assembled mold pair with optional gasket and embedded wafer, sliding laterally apart along X.
    """
    left = Nanopore_Wafer_Mold_Left(is_nanopore=is_nanopore).move(Location((-explode, 0, 0)))
    right = Nanopore_Wafer_Mold_Right(is_nanopore=is_nanopore).move(Location((explode, 0, 0)))
    parts = [left, right]
    if show_gasket:
        if is_nanopore:
            from src.cartridge import Cast_Nanopore_Wafer_Gasket, Nanopore_Wafer_Silicon
            gasket = Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, 0, CAVITY_Z)))
            wafer = Nanopore_Wafer_Silicon().move(Location((0, 0, -0.4))).move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, 0, CAVITY_Z)))
            parts.extend([gasket, wafer])
        else:
            from src.cartridge import Fitted_Amplifier_Gasket
            gasket = Fitted_Amplifier_Gasket().move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, 0, CAVITY_Z)))
            parts.append(gasket)
    return parts

def Multi_Mold_Visualizer(explode=0.0):
    """
    Dual mold visualizer matching OpenSCAD:
    Nanopore mold pair at Y = -55mm, Amplifier mold pair at Y = +55mm.
    """
    exp = max(0.0, float(explode))
    from src.cartridge import Cast_Nanopore_Wafer_Gasket, Nanopore_Wafer_Silicon, Fitted_Amplifier_Gasket
    nano_left = Nanopore_Wafer_Mold_Left(is_nanopore=True).move(Location((-exp, -55.0, 0)))
    nano_right = Nanopore_Wafer_Mold_Right(is_nanopore=True).move(Location((exp, -55.0, 0)))
    nano_gasket = Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, -55.0, CAVITY_Z)))
    nano_wafer = Nanopore_Wafer_Silicon().move(Location((0, 0, -0.4))).move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, -55.0, CAVITY_Z)))

    amp_left = Nanopore_Wafer_Mold_Left(is_nanopore=False).move(Location((-exp, 55.0, 0)))
    amp_right = Nanopore_Wafer_Mold_Right(is_nanopore=False).move(Location((exp, 55.0, 0)))
    amp_gasket = Fitted_Amplifier_Gasket().move(Location((0, 0, -GASKET_THICK / 2.0))).rotate(Axis.Y, 90).move(Location((0, 55.0, CAVITY_Z)))

    return [nano_left, nano_right, nano_gasket, nano_wafer, amp_left, amp_right, amp_gasket]


if __name__ == "__main__":
    from build123d.exporters3d import export_step, export_stl

    left_nano = Nanopore_Wafer_Mold_Left(is_nanopore=True)
    right_nano = Nanopore_Wafer_Mold_Right(is_nanopore=True)

    # Orient flat for 3D printing (parting face pointing up at Z=15mm)
    left_flat = left_nano.move(Rotation(0, -90, 0)).move(Location((0, 0, MOLD_T / 2.0)))
    right_flat = right_nano.move(Rotation(0, 90, 0)).move(Location((0, 0, MOLD_T / 2.0)))

    export_step(left_flat, "Nanopore_Wafer_Mold_Left.step")
    export_step(right_flat, "Nanopore_Wafer_Mold_Right.step")
    print("Exported Left and Right Molds as STEP files.")
