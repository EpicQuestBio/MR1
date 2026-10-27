# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

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

def Rounded_Reservoir_Block(t, w, h, is_left=True, r_corner=3.0, r_floor=2.0):
    """
    Creates a smooth resin pouring reservoir cutout block with rounded vertical
    corners and bottom transition, eliminating sharp corners that trap bubbles or resin.
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(t, w, h)
        # Vertical edges at the back of the mold half (away from parting line X=0)
        z_edges = p.edges().filter_by(Axis.Z)
        if is_left:
            back_z = [e for e in z_edges if e.center().X < 0]
        else:
            back_z = [e for e in z_edges if e.center().X > 0]
        if back_z:
            fillet(back_z, radius=r_corner)

        # Bottom floor edges
        bot_y = p.edges().filter_by(Axis.Y).sort_by(Axis.Z)[:2]
        if is_left:
            bot_back = [e for e in bot_y if e.center().X < 0]
        else:
            bot_back = [e for e in bot_y if e.center().X > 0]
        bot_x = p.edges().filter_by(Axis.X).sort_by(Axis.Z)[:2]
        edges_to_fillet = (bot_back if bot_back else bot_y[:1]) + bot_x
        if edges_to_fillet:
            fillet(edges_to_fillet, radius=r_floor)
    return p.part

def build_base_mold_half(is_left=True):
    """
    Constructs the shared structural body of one mold half:
    - Base rounded block (80 x 90 x 15 mm)
    - Top degassing/pouring reservoir (50 x 15 x 12 mm cut with smooth filleted corners)
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

        # 2. Top Degassing & Pouring Reservoir (leaves 3mm back wall, smooth rounded corners)
        res_w = HEX_DIAM - 10.0  # 50.0 mm
        res_d = 15.0             # 15.0 mm depth
        res_t = MOLD_T - 3.0     # 12.0 mm thickness cut
        res_x_center = -res_t / 2.0 if is_left else res_t / 2.0
        res_cut = Rounded_Reservoir_Block(res_t + 0.1, res_w, res_d + 0.1, is_left=is_left, r_corner=3.0, r_floor=2.0)
        with Locations((res_x_center, 0, MOLD_H - res_d / 2.0 + 0.05)):
            add(res_cut, mode=Mode.SUBTRACT)

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
                with Locations((FINGER_GRIP_NOTCH_X, 0), (-FINGER_GRIP_NOTCH_X, 0)):
                    Circle(FINGER_GRIP_NOTCH_R, mode=Mode.SUBTRACT)
        extrude(amount=-GASKET_THICK / 2.0 if is_left else GASKET_THICK / 2.0, mode=Mode.SUBTRACT)

    return p.part

def Nanopore_Wafer_Mold_Left(is_nanopore=True, gasket_type="top", multi_stage_guard=False):
    """
    Left mold half (X < 0 in assembly).
    Forms the back face of the gasket where the diamond boss and wafer protrude into the PCB.
    Features:
    - 45-degree diamond protrusion pocket (if is_nanopore=True)
    - Central clamping protective plug (D=2.0mm)
    - 4 wafer corner guide pin holes (D=1.2mm)
    - Passive port core pins (D=2.0mm) for pass-through ports
    - Circuitry cutouts and square central plug (if is_nanopore=False)
    - Multi-stage 3D driven guard coaxial wells (if multi_stage_guard=True)
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
            pass_ports = [P_TRANS_IN, P_TRANS_OUT] if gasket_type == "top" else [P_CIS_IN, P_CIS_OUT]
            for port in pass_ports:
                with Locations((-GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # Weep Duct Pins
            add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((-GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

            if multi_stage_guard:
                # 3D Driven Guard Coaxial Wells:
                # Central Signal Dot well (WS_CIS): D=1.2mm, depth 0.4mm into mold
                with Locations((-GASKET_THICK / 2.0 - 0.2, 0, CAVITY_Z)):
                    Cylinder(radius=0.6, height=0.4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                # Driven Guard Ring groove (GUARD): ID=2.8mm, OD=4.2mm, depth 0.4mm
                with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(2.1)
                        Circle(1.4, mode=Mode.SUBTRACT)
                extrude(amount=-0.4, mode=Mode.SUBTRACT)
                # Outer Faraday Shield Ring groove (GNDA): ID=5.2mm, OD=6.5mm, depth 0.4mm
                with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(3.25)
                        Circle(2.6, mode=Mode.SUBTRACT)
                extrude(amount=-0.4, mode=Mode.SUBTRACT)

        else:
            # Amplifier mold (is_nanopore=False)
            cutouts = Circuitry_Cutouts(height=GASKET_THICK / 2.0)
            cutouts = cutouts.rotate(Axis.Y, -90).move(Location((-GASKET_THICK / 4.0, 0, CAVITY_Z)))
            add(cutouts, mode=Mode.ADD)

            # Central square plug (3.0 x 3.0 mm from X = -GASKET_THICK/2 to X = 0)
            with Locations((-GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Box(GASKET_THICK / 2.0, WAFER_SIZE, WAFER_SIZE, mode=Mode.ADD)

            # Port core pins for passive ports on amplifier gasket
            pass_ports = [P_TRANS_IN, P_TRANS_OUT] if gasket_type == "top" else [P_CIS_IN, P_CIS_OUT]
            for port in pass_ports:
                with Locations((-GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # Weep Duct Pins
            add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((-GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

            if multi_stage_guard:
                # 3D Driven Guard Coaxial Wells:
                with Locations((-GASKET_THICK / 2.0 - 0.2, 0, CAVITY_Z)):
                    Cylinder(radius=0.6, height=0.4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(2.1)
                        Circle(1.4, mode=Mode.SUBTRACT)
                extrude(amount=-0.4, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(3.25)
                        Circle(2.6, mode=Mode.SUBTRACT)
                extrude(amount=-0.4, mode=Mode.SUBTRACT)

    return p.part

def Nanopore_Wafer_Mold_Right(is_nanopore=True, gasket_type="top", multi_stage_guard=False):
    """
    Right mold half (X > 0 in assembly).
    Forms the front channel face of the gasket sealed against Plate 3.
    Features:
    - Male dowel alignment pins protruding 4.8mm from X=0
    - Opposing central clamping protective plug (D=2.0mm)
    - Port core pins meeting Left half at X=0
    - Positive microfluidic channel ridge along Cis path for Nanopore mold
    - Positive microfluidic channel ridge along Trans path for Amplifier mold
    - Compliant port crush-rib sealing grooves & electrode ring grooves (if multi_stage_guard=True)
    """
    base = build_base_mold_half(is_left=False)
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(base)
        if is_nanopore:
            # 1. Opposing Central Clamping Plug (D=2.0mm from X = +0.8 down to X = 0)
            with Locations((GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Cylinder(radius=PLUG_DIAMETER / 2.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # 2. Port Core Pins (D=2.0mm from X = +0.8 down to X = 0)
            for port in ALL_PORTS:
                with Locations((GASKET_THICK / 4.0, port[0], port[1])):
                    Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

            # 3. Active Microfluidic Flow Channel Ridge (1.4mm wide, height 0.8mm from X = 0 to X = 0.8)
            active_in = P_CIS_IN if gasket_type == "top" else P_TRANS_IN
            active_out = P_CIS_OUT if gasket_type == "top" else P_TRANS_OUT
            with BuildSketch(Plane.YZ.offset(0)):
                with Locations(active_in, (0, CAVITY_Z), active_out):
                    Circle(FLUID_CHANNEL_W / 2.0)
                make_hull()
                with Locations((0, CAVITY_Z)):
                    Circle(CHAMBER_DIAM / 2.0)
            extrude(amount=GASKET_THICK / 2.0, mode=Mode.ADD)

            # Weep Duct Pins and Trench Boss
            add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)
            add(Weep_Trench_Cutout(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

            if multi_stage_guard:
                # 1. Port Crush-Rib Sealing Grooves (depth 0.4mm into mold face)
                for port in ALL_PORTS:
                    with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
                        with Locations(port):
                            Circle(2.2)
                            Circle(1.4, mode=Mode.SUBTRACT)
                    extrude(amount=0.4, mode=Mode.SUBTRACT)

                # 2. Concentric Bottom Electrode Ring Grooves
                with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(3.2)
                        Circle(2.5, mode=Mode.SUBTRACT)
                        Circle(5.0)
                        Circle(4.0, mode=Mode.SUBTRACT)
                extrude(amount=0.4, mode=Mode.SUBTRACT)

        else:
            # Amplifier mold (is_nanopore=False)
            # 1. Central square plug (3.0 x 3.0 mm from X = +0.8 down to X = 0)
            with Locations((GASKET_THICK / 4.0, 0, CAVITY_Z)):
                Box(GASKET_THICK / 2.0, WAFER_SIZE, WAFER_SIZE, mode=Mode.ADD)

            # 2. Active Microfluidic Channel Ridge
            active_in = P_CIS_IN if gasket_type == "top" else P_TRANS_IN
            active_out = P_CIS_OUT if gasket_type == "top" else P_TRANS_OUT
            with BuildSketch(Plane.YZ.offset(0)):
                with Locations(active_in, (0, CAVITY_Z), active_out):
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
            add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)
            add(Weep_Trench_Cutout(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

            if multi_stage_guard:
                for port in ALL_PORTS:
                    with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
                        with Locations(port):
                            Circle(2.2)
                            Circle(1.4, mode=Mode.SUBTRACT)
                    extrude(amount=0.4, mode=Mode.SUBTRACT)
                with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
                    with Locations((0, CAVITY_Z)):
                        Circle(3.2)
                        Circle(2.5, mode=Mode.SUBTRACT)
                        Circle(5.0)
                        Circle(4.0, mode=Mode.SUBTRACT)
                extrude(amount=0.4, mode=Mode.SUBTRACT)

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

def Concentric_Guard_Mold_Plate_Top():
    """
    Dedicated SLA resin mold plate for casting the top interconnect face of the monolithic interposer.
    Features negative coaxial cavities:
    - Central Signal Dot well (WS_CIS, D=1.2mm, depth 0.4mm into mold)
    - Wideband Signal Dot well (WS_CIS_WIDE, D=1.2mm, depth 0.4mm into mold)
    - Concentric Driven Guard Ring groove (GUARD / GUARD_WIDE, ID=2.8mm, OD=4.2mm, depth 0.4mm)
    - Outer Concentric Faraday Shield Ring groove (GNDA, ID=5.2mm, OD=6.5mm, depth 0.4mm)
    - Degassing reservoir and alignment interlocks
    """
    base = build_base_mold_half(is_left=True)
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(base)
        # 1. Central Signal Dot well (WS_CIS): D=1.2mm, depth 0.4mm into mold
        with Locations((-GASKET_THICK / 2.0 - 0.2, 0, CAVITY_Z)):
            Cylinder(radius=0.6, height=0.4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 2. Concentric Driven Guard Ring groove (GUARD): ID=2.8mm, OD=4.2mm, depth 0.4mm
        with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
            with Locations((0, CAVITY_Z)):
                Circle(2.1)
                Circle(1.4, mode=Mode.SUBTRACT)
        extrude(amount=-0.4, mode=Mode.SUBTRACT)

        # 3. Outer Concentric Faraday Shield Ring groove (GNDA): ID=5.2mm, OD=6.5mm, depth 0.4mm
        with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
            with Locations((0, CAVITY_Z)):
                Circle(3.25)
                Circle(2.6, mode=Mode.SUBTRACT)
        extrude(amount=-0.4, mode=Mode.SUBTRACT)

        # 4. Wideband Signal Dot well (WS_CIS_WIDE, offset 10mm along Y)
        with Locations((-GASKET_THICK / 2.0 - 0.2, 10.0, CAVITY_Z)):
            Cylinder(radius=0.6, height=0.4, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
        with BuildSketch(Plane.YZ.offset(-GASKET_THICK / 2.0)):
            with Locations((10.0, CAVITY_Z)):
                Circle(2.1)
                Circle(1.4, mode=Mode.SUBTRACT)
        extrude(amount=-0.4, mode=Mode.SUBTRACT)

        # Weep Duct Pins
        add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((-GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

    return p.part

def Bottom_Fluidic_Electrode_Mold_Plate():
    """
    Dedicated SLA resin mold plate for casting the bottom face of the monolithic interposer.
    Features:
    - 4 Port Crush-Rib Sealing Grooves (depth 0.4mm, width 0.8mm) around fluid ports for leak-free seal against unprimed PP.
    - Annular Ag/AgCl pickoff ring grooves for RE_TRANS (ID 5.0mm, OD 6.4mm) and CE_GNDA (ID 8.0mm, OD 10.0mm).
    - Port core pins, alignment dowels, and sprue runner.
    """
    base = build_base_mold_half(is_left=False)
    with BuildPart(mode=Mode.PRIVATE) as p:
        add(base)
        # 1. Port Crush-Rib Sealing Grooves (depth 0.4mm into mold face)
        for port in ALL_PORTS:
            with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
                with Locations(port):
                    Circle(2.2)
                    Circle(1.4, mode=Mode.SUBTRACT)
            extrude(amount=0.4, mode=Mode.SUBTRACT)

        # 2. Concentric Bottom Electrode Ring Grooves (Ag/AgCl pickoff rings)
        with BuildSketch(Plane.YZ.offset(GASKET_THICK / 2.0)):
            with Locations((0, CAVITY_Z)):
                # RE_TRANS ring (r: 2.5 to 3.2 mm -> D: 5.0 to 6.4 mm)
                Circle(3.2)
                Circle(2.5, mode=Mode.SUBTRACT)
                # CE_GNDA ring (r: 4.0 to 5.0 mm -> D: 8.0 to 10.0 mm)
                Circle(5.0)
                Circle(4.0, mode=Mode.SUBTRACT)
        extrude(amount=0.4, mode=Mode.SUBTRACT)

        # 3. Port core pins
        for port in ALL_PORTS:
            with Locations((GASKET_THICK / 4.0, port[0], port[1])):
                Cylinder(radius=1.0, height=GASKET_THICK / 2.0, rotation=(0, 90, 0), mode=Mode.ADD)

        # Weep Duct Pins and Trench Boss
        add(Weep_Duct_Holes(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)
        add(Weep_Trench_Cutout(height=GASKET_THICK / 2.0).rotate(Axis.Y, 90).move(Location((GASKET_THICK / 4.0, 0, CAVITY_Z))), mode=Mode.ADD)

    return p.part

def MidLayer_PVA_Alignment_Frame():
    """
    Mid-layer alignment frame for positioning sacrificial PVA microfluidic cores
    and the silicon nanopore chip during potting.
    Features:
    - Hexagonal carrier body (55.0 mm flat-to-flat, 0.8 mm thickness)
    - Central 45-degree diamond chip pocket (4.0 x 4.0 mm)
    - Fluid port pass-through collars
    - Vertical Z-axis conductive via pilot holes (D=1.2mm)
    """
    with BuildPart(mode=Mode.PRIVATE) as p:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=HEX_DIAM / 2.0, side_count=6, rotation=90)
            # Central chip pocket cutout
            with Locations((0, 0)):
                Rectangle(WAFER_SIZE + 0.2, WAFER_SIZE + 0.2, rotation=45, mode=Mode.SUBTRACT)
            # Port pass-throughs
            for port in [(10.0, 17.32), (-10.0, 17.32), (10.0, -17.32), (-10.0, -17.32)]:
                with Locations(port):
                    Circle(1.5, mode=Mode.SUBTRACT)
            # Z-axis conductive via holes
            for via_r in [3.0, 4.5]:
                for angle in [0, 90, 180, 270]:
                    vx = via_r * math.cos(math.radians(angle))
                    vy = via_r * math.sin(math.radians(angle))
                    with Locations((vx, vy)):
                        Circle(0.6, mode=Mode.SUBTRACT)
        extrude(amount=0.8)
    return p.part

def MultiStage_Interposer_Mold_Assembly(explode=0.0):
    """
    Returns the complete 3-part multi-stage casting mold assembly:
    1. Top Concentric Guard Mold Plate
    2. Mid-Layer PVA Alignment Frame
    3. Bottom Fluidic / Electrode Mold Plate
    """
    exp = max(0.0, float(explode))
    bot = Bottom_Fluidic_Electrode_Mold_Plate().move(Location((exp, 0, 0)))
    top = Concentric_Guard_Mold_Plate_Top().move(Location((-exp, 0, 0)))
    frame = MidLayer_PVA_Alignment_Frame().rotate(Axis.Y, 90).move(Location((0, 0, CAVITY_Z)))
    return [top, frame, bot]

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
    top_guard = Concentric_Guard_Mold_Plate_Top()
    bot_electrode = Bottom_Fluidic_Electrode_Mold_Plate()
    mid_frame = MidLayer_PVA_Alignment_Frame()

    # Orient flat for 3D printing (parting face pointing up at Z=15mm)
    left_flat = left_nano.move(Rotation(0, -90, 0)).move(Location((0, 0, MOLD_T / 2.0)))
    right_flat = right_nano.move(Rotation(0, 90, 0)).move(Location((0, 0, MOLD_T / 2.0)))
    top_guard_flat = top_guard.move(Rotation(0, -90, 0)).move(Location((0, 0, MOLD_T / 2.0)))
    bot_electrode_flat = bot_electrode.move(Rotation(0, 90, 0)).move(Location((0, 0, MOLD_T / 2.0)))

    export_step(left_flat, "Nanopore_Wafer_Mold_Left.step")
    export_step(right_flat, "Nanopore_Wafer_Mold_Right.step")
    export_step(top_guard_flat, "Concentric_Guard_Mold_Plate_Top.step")
    export_step(bot_electrode_flat, "Bottom_Fluidic_Electrode_Mold_Plate.step")
    export_step(mid_frame, "MidLayer_PVA_Alignment_Frame.step")
    print("Exported standard and multi-stage concentric guard molds as STEP files.")
