from build123d import *
from src.constants import *
from src.common import Weep_Duct_Holes
import math

def Housing_Pump_Case(pump_type=PUMP_TYPE):
    """Bottom Pump Module Base Case."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main Block (cuboid with Z edges rounded)
        Box(BASE_W + 2*WALL, BASE_L + 2*WALL, PUMP_H)
        edges_to_fillet = p.edges().filter_by(Axis.Z)
        if edges_to_fillet:
            fillet(edges_to_fillet, radius=WALL)

        # Internal Bucket
        with Locations((0, 0, WALL)):
            with BuildPart(mode=Mode.PRIVATE) as bucket:
                Box(BASE_W - 2*WALL, BASE_L - 2*WALL, PUMP_H)
                edges = bucket.edges().filter_by(Axis.Z)
                if edges:
                    fillet(edges, radius=2.0)
            add(bucket.part, mode=Mode.SUBTRACT)

        # Fluid Ports with Bosses on Side Walls (Left and Right at Y = +/- 20)
        boss_d = 20.0
        boss_len = WALL * 3.0  # 15.0 mm matching OpenSCAD cyl(h=wall*3, d=20, anchor=CENTER)
        port_d = 6.35
        for x_side in [-(BASE_W/2.0 + WALL), (BASE_W/2.0 + WALL)]:
            rot = (0, -90, 0) if x_side < 0 else (0, 90, 0)
            for y_pos in [-20.0, 20.0]:
                with Locations((x_side, y_pos, 0)):
                    Cylinder(radius=boss_d/2.0, height=boss_len, rotation=rot, mode=Mode.ADD)
                    Cylinder(radius=port_d/2.0, height=WALL*4.0, rotation=rot, mode=Mode.SUBTRACT)

        # Handle (D-shape logic)
        h_center = 26.0
        stick_out = 36.0
        tube_d = 12.0
        with Locations((0, -(BASE_L/2.0 + WALL), -PUMP_H/2.0 + stick_out/2.0)):
            with BuildPart(mode=Mode.PRIVATE) as handle:
                Box(stick_out, h_center*2.0 + tube_d, tube_d)
                Box(stick_out - tube_d, h_center*2.0 - tube_d, tube_d + 1.0, mode=Mode.SUBTRACT)
            add(handle.part.move(Rotation(0, 90, 0)), mode=Mode.ADD)

        # Back Wall Connectivity
        with Locations((0, BASE_L/2.0 + WALL, 0)):
            with Locations((-15, 0, 0), (15, 0, 0)):
                Box(12, WALL*10, 6, mode=Mode.SUBTRACT)

        # Lid Mounts
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * BASE_W/2.0, y_sign * BASE_L/2.0, 0)):
                    Cylinder(radius=3.2/2.0, height=PUMP_H*3.0, mode=Mode.SUBTRACT)

        # Top Knife-Edge Seal Ridge
        with Locations((0, 0, PUMP_H/2.0 + SEAL_RADIUS/2.0)):
            with BuildPart(mode=Mode.PRIVATE) as seal:
                with BuildSketch():
                    Rectangle(BASE_W - 8.0 + SEAL_RADIUS*2, BASE_L - 8.0 + SEAL_RADIUS*2)
                    Rectangle(BASE_W - 8.0 - SEAL_RADIUS*2, BASE_L - 8.0 - SEAL_RADIUS*2, mode=Mode.SUBTRACT)
                extrude(amount=SEAL_RADIUS)
            add(seal.part, mode=Mode.ADD)

        # Pump Mounting Plate on floor
        with Locations((0, 0, -PUMP_H/2.0 + WALL + 2.5)):
            with BuildPart(mode=Mode.PRIVATE) as mplate:
                Box(BASE_W - 2*WALL - 1.0, BASE_L - 2*WALL - 1.0, 5.0)
                # Dual pump cutouts
                for side in [-1, 1]:
                    with Locations((side * (BASE_W/4.0), 20.0, 0)):
                        Cylinder(radius=PUMP_MOUNT_D/2.0, height=6.0, mode=Mode.SUBTRACT)
            add(mplate.part, mode=Mode.ADD)

    return p.part

def Housing_Pump_Lid():
    """Lid for the pump case."""
    lid_thick = PUMP_LID_THICK
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(BASE_W + 2*WALL, BASE_L + 2*WALL, lid_thick)
        edges = p.edges().filter_by(Axis.Z)
        if edges:
            fillet(edges, radius=WALL)

        # Center pass-through
        Cylinder(radius=20.0, height=lid_thick + 2.0, mode=Mode.SUBTRACT)

        # Dimples for sensor enclosures (top surface)
        with Locations((0, 0, lid_thick/2.0)):
            for x_sign in [-1, 1]:
                for y_sign in [-1, 1]:
                    with Locations((x_sign * (BASE_W/2.0 - FEET_INSET), y_sign * (BASE_L/2.0 - FEET_INSET), 0)):
                        Sphere(radius=13.5/2.0, mode=Mode.SUBTRACT)

        # Mounting holes with counterbores
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * BASE_W/2.0, y_sign * BASE_L/2.0, 0)):
                    Cylinder(radius=3.5/2.0, height=lid_thick*3.0, mode=Mode.SUBTRACT)
                with Locations((x_sign * BASE_W/2.0, y_sign * BASE_L/2.0, lid_thick/2.0 - 2.0)):
                    Cylinder(radius=6.0/2.0, height=4.1, mode=Mode.SUBTRACT)

        # Bottom Indexing Lip
        with Locations((0, 0, -lid_thick/2.0 - 2.5)):
            with BuildPart(mode=Mode.PRIVATE) as lip:
                Box(BASE_W - 2*WALL - 0.4, BASE_L - 2*WALL - 0.4, 5.0)
                Box(BASE_W - 2*WALL - 0.4 - 3.0, BASE_L - 2*WALL - 0.4 - 3.0, 5.1, mode=Mode.SUBTRACT)
            add(lip.part, mode=Mode.ADD)

        # Bottom O-Ring Groove
        with Locations((0, 0, -lid_thick/2.0)):
            with BuildPart(mode=Mode.PRIVATE) as groove:
                with BuildSketch():
                    Rectangle(BASE_W - 8.0 + 1.0, BASE_L - 8.0 + 1.0)
                    Rectangle(BASE_W - 8.0 - 1.0, BASE_L - 8.0 - 1.0, mode=Mode.SUBTRACT)
                extrude(amount=1.5)
            add(groove.part, mode=Mode.SUBTRACT)

    return p.part

def Housing_Case_Reader():
    """Reader module base case."""
    inset_depth = 2.5
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base
        Box(BASE_W + 2*(WALL - inset_depth), BASE_L + 2*(WALL - inset_depth), READER_LID_THICK)
        edges = p.edges().filter_by(Axis.Z)
        if edges:
            fillet(edges, radius=WALL - inset_depth)

        # Bottom edges fillet for rounded corners
        b_edges = [e for e in p.edges() if abs(e.center().Z - (-READER_LID_THICK/2.0)) < 0.01 and e.geom_type == GeomType.LINE]
        if b_edges:
            fillet(b_edges, radius=2.0)

        # Hollow out
        with BuildPart(mode=Mode.PRIVATE) as bucket:
            Box(BASE_W - 2*WALL, BASE_L - 2*WALL, READER_LID_THICK)
            bedges = bucket.edges().filter_by(Axis.Z)
            if bedges:
                fillet(bedges, radius=2.0)
        with Locations((0, 0, WALL)):
            add(bucket.part, mode=Mode.SUBTRACT)

        # Top outer rim fillet
        t_edges = [e for e in p.edges() if abs(e.center().Z - (READER_LID_THICK/2.0)) < 0.01 and e.geom_type == GeomType.LINE and (abs(e.center().X) > 40 or abs(e.center().Y) > 40)]
        if t_edges:
            fillet(t_edges, radius=1.0)

        # Feet Dimples (Truncated sphere)
        with BuildPart(mode=Mode.PRIVATE) as dimple_tpl:
            Sphere(radius=13.0/2.0)
            with Locations((0, 0, -3.5/2.0 + 0.1/2.0)):
                Cylinder(radius=15.0/2.0, height=3.5 + 0.1, mode=Mode.INTERSECT)
        dimple_shape = dimple_tpl.part

        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                loc = Location((x_sign * (BASE_W/2.0 - FEET_INSET), y_sign * (BASE_L/2.0 - FEET_INSET), -READER_LID_THICK/2.0))
                add(dimple_shape.moved(loc), mode=Mode.ADD)

        # PCB Standoffs (Floor / Bottom Lid)
        standoff_h = 5.0
        with Locations((0, 0, -READER_LID_THICK/2.0 + WALL + standoff_h/2.0)):
            for mx in [-35.0, 35.0]:
                for my in [-25.0, 25.0]:
                    with Locations((mx, my, 0)):
                        Cylinder(radius=6.0/2.0, height=standoff_h, mode=Mode.ADD)
                        Cylinder(radius=(2.5 - TOLERANCE)/2.0, height=standoff_h + 2.0, mode=Mode.SUBTRACT)

        # Back Wall Connectivity (USB-C cutout for Main Reader PCB)
        with Locations((0, BASE_L/2.0 + WALL, 0)):
            with Locations((USB_OFFSET_X, 0, 0)):
                Box(12, WALL*10, 6, mode=Mode.SUBTRACT)

        # Corner Lid Mounting Screw Holes
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * (BASE_W/2.0 - 2.0), y_sign * (BASE_L/2.0 - 2.0), 0)):
                    Cylinder(radius=3.2/2.0, height=READER_LID_THICK*3.0, mode=Mode.SUBTRACT)

        # Top Knife-Edge Seal
        with Locations((0, 0, READER_LID_THICK/2.0 + SEAL_RADIUS/2.0)):
            with BuildPart(mode=Mode.PRIVATE) as seal:
                with BuildSketch():
                    Rectangle(BASE_W - 8.0 + SEAL_RADIUS*2, BASE_L - 8.0 + SEAL_RADIUS*2)
                    Rectangle(BASE_W - 8.0 - SEAL_RADIUS*2, BASE_L - 8.0 - SEAL_RADIUS*2, mode=Mode.SUBTRACT)
                extrude(amount=SEAL_RADIUS)
            add(seal.part, mode=Mode.ADD)

        # Wire clearance cutouts for internal reader wiring harness
        try:
            from src.assembly import route_spline, get_wiring_routes
            for name, (pts, radius) in get_wiring_routes().items():
                pts_local = [(x, y, z - (PUMP_H + PUMP_LID_THICK + 5.0)) for x, y, z in pts]
                w_cut = route_spline(pts_local, radius + 0.1)
                add(w_cut, mode=Mode.SUBTRACT)
        except Exception:
            pass

    return p.part

def Housing_Lid_Reader():
    """Top reader module lid with threaded neck (M75 x 8mm thread), inner hex socket,
    hollow internal chamber for tubes and fittings, and rounded corners.
    Includes:
    - 4 vertical fluid pass-through holes (D=10mm at PORT_RADIUS=20mm) into hollow chamber
    - Ribbon cable clearance channel (13.5x3.0mm cavity recessed into hexagon wall at Y=-27.5)
    - 4 horizontal side fluid ports (D=6.35mm at Y = +/-20mm) penetrating into hollow chamber
    - Corner mounting holes matching case at (+/- 53.0, +/- 53.0) with counterbores
    - Lower outer wall inset (2.5mm inset on bottom 15mm)
    - Bottom indexing lip and underside O-ring groove
    - Rounded edges and corners for smooth ergonomics
    """
    lid_w = BASE_W + 2*(WALL - 2.5) # 115.0 mm matching case width
    lid_l = BASE_L + 2*(WALL - 2.5) # 115.0 mm matching case length
    lid_thick = 25.0
    ceiling_thick = 5 # Thin ceiling under hex socket leaves 24mm tall hollow bucket
    neck_length = 25.2
    outer_thread_od = 74.5
    depth = THREAD_DEPTH # 4.75 mm depth
    neck_r = outer_thread_od / 2.0 # 37.25 mm (outer thread radius)
    neck_core_r = neck_r - depth   # 32.5 mm (core neck radius)
    pitch = CAP_THREAD_PITCH
    inset_depth = 2.5
    inset_height = 15.0

    with BuildPart(mode=Mode.PRIVATE) as p:
        # 1. Base plate centered at Z = -lid_thick / 2.0 (top surface at Z = 0)
        with Locations((0, 0, -lid_thick / 2.0)):
            Box(lid_w, lid_l, lid_thick)
            edges_z = p.edges().filter_by(Axis.Z)
            if edges_z:
                fillet(edges_z, radius=WALL)

        # 2. Inset indexing lip at bottom extending down to Z = -27.5
        with Locations((0, 0, -lid_thick - 1.25)):
            Box(BASE_W - 2 * WALL - 0.4, BASE_L - 2 * WALL - 0.4, 2.5)

        # 3. Fillet top outer perimeter edges of base plate (at Z = 0)
        top_outer_edges = [e for e in p.edges() if abs(e.center().Z) < 0.01 and e.geom_type == GeomType.LINE]
        if top_outer_edges:
            fillet(top_outer_edges, radius=2.5)

        # 4. Hollow internal bucket from Z = -ceiling_thick down to bottom
        bucket_h = lid_thick - ceiling_thick + 2.5 + 2.0 # 26.0 mm height
        bucket_z = -ceiling_thick - bucket_h / 2.0
        with BuildPart(mode=Mode.PRIVATE) as bucket:
            Box(lid_w - 2 * WALL - 4.0, lid_l - 2 * WALL - 4.0, bucket_h)
            bedges = bucket.edges().filter_by(Axis.Z)
            if bedges:
                fillet(bedges, radius=3.0)
        with Locations((0, 0, bucket_z)):
            add(bucket.part, mode=Mode.SUBTRACT)

        # 5. Neck transition cone (Z: 0 to 5)
        with Locations((0, 0, 2.5)):
            Cone(bottom_radius=neck_r + 2.5, top_radius=neck_r, height=5.0)

        # 6. Neck cylinder core (Z: 5 to 5 + neck_length)
        with Locations((0, 0, 5.0 + neck_length / 2.0)):
            Cylinder(radius=neck_core_r, height=neck_length)

        # 7. External Helical Thread (74.5mm outer OD x 4.75mm depth x 8mm pitch)
        with BuildLine():
            path = Helix(pitch=pitch, height=neck_length, radius=neck_r)
        with Locations((0, 0, 5.0)):
            with BuildSketch(Plane.XZ) as s:
                with Locations((neck_r, 0)):
                    pts = [
                        (-depth, -pitch * 0.22),
                        (0, -pitch * 0.10),
                        (0, pitch * 0.10),
                        (-depth, pitch * 0.22)
                    ]
                    Polygon(pts)
            sweep(sections=s.sketch, path=path, mode=Mode.ADD)

        # 8. Inner Hex Socket Cutout (61mm across corners) starting cleanly at Z = 0.0
        with Locations((0, 0, 0.0)):
            with BuildSketch():
                RegularPolygon(radius=61.0 / 2.0, side_count=6)
            extrude(amount=5.0 + neck_length + 20.0, mode=Mode.SUBTRACT)

        # 9. Vertical Fluid Pass-Through Holes (4x D=13mm through neck/ceiling into hollow interior)
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP, ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
            ang_rad = math.radians(a)
            with Locations((PORT_RADIUS * math.cos(ang_rad), PORT_RADIUS * math.sin(ang_rad), -ceiling_thick/2.0)):
                Cylinder(radius=13.0 / 2.0, height=neck_length + ceiling_thick*3.0, mode=Mode.SUBTRACT)

        # 10. Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
        with Locations((0.0, -27.5, 0.0)):
            Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)

        # 10b. Weep holes penetrating the reader lid ceiling into the hollow bucket
        with Locations((0, 0, -ceiling_thick/2.0)):
            add(Weep_Duct_Holes(height=neck_length + ceiling_thick*3.0), mode=Mode.SUBTRACT)

        # 11. Horizontal Side Fluid Ports (at Y = +/- 20, Z = -13.0mm penetrating into hollow bucket)
        # Includes counterbores for Luer bulkhead panel mount fittings (D=15.0mm, depth=2.5mm)
        for x_wall in [-(lid_w / 2.0), (lid_w / 2.0)]:
            for y_port in [-20.0, 20.0]:
                with Locations((x_wall, y_port, -13.0)):
                    Cylinder(radius=15.0 / 2.0, height=5.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
                    Cylinder(radius=6.35 / 2.0, height=WALL * 4.0, rotation=(0, 90, 0), mode=Mode.SUBTRACT)

        # 12. Lower Outer Inset (2.5mm thinned wall on bottom 15mm creating overhang)
        with Locations((0, 0, -lid_thick + inset_height / 2.0)):
            with BuildPart(mode=Mode.PRIVATE) as inset:
                Box(lid_w + 1.0, lid_l + 1.0, inset_height)
                Box(lid_w - 2 * inset_depth, lid_l - 2 * inset_depth, inset_height + 1.0, mode=Mode.SUBTRACT)
            add(inset.part, mode=Mode.SUBTRACT)

        # 13. Back Wall Connectivity (USB-C cutouts)
        #with Locations((0, lid_l / 2.0, 0)):
        #    with Locations((-15, 0, 0), (15, 0, 0)):
        #        Box(12, WALL * 10, 6, mode=Mode.SUBTRACT)

        # 14. Corner Mounting Holes (with counterbores) matching case at (+/- 53.0, +/- 53.0)
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                mx = x_sign * (BASE_W / 2.0 - 2.0)
                my = y_sign * (BASE_L / 2.0 - 2.0)
                with Locations((mx, my, -lid_thick / 2.0)):
                    Cylinder(radius=3.5 / 2.0, height=lid_thick * 3.0, mode=Mode.SUBTRACT)
                with Locations((mx, my, -2.5)):
                    Cylinder(radius=6.0 / 2.0, height=5.1, mode=Mode.SUBTRACT)

        # 15. Underside O-Ring Groove
        with Locations((0, 0, -lid_thick)):
            with BuildPart(mode=Mode.PRIVATE) as ogroove:
                with BuildSketch():
                    Rectangle(BASE_W - 8.0 + 1.0, BASE_L - 8.0 + 1.0)
                    Rectangle(BASE_W - 8.0 - 1.0, BASE_L - 8.0 - 1.0, mode=Mode.SUBTRACT)
                extrude(amount=1.5)
            add(ogroove.part, mode=Mode.SUBTRACT)

        # Wire clearance cutout for W_USB passing through lower indexing lip
        try:
            from src.assembly import route_spline, get_wiring_routes
            pts_u, r_u = get_wiring_routes()["W_USB"]
            pts_local_l = [(x, y, z - (PUMP_H + PUMP_LID_THICK + 5.0 + 30.0)) for x, y, z in pts_u]
            w_cut_l = route_spline(pts_local_l, r_u + 0.1)
            add(w_cut_l, mode=Mode.SUBTRACT)
        except Exception:
            pass

        # 16. Internal microfluidic conduit guide channels routing from side ports up into cartridge stack
        try:
            from src.assembly import route_spline, get_tubing_routes
            reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
            z_stack = reader_z_base + 30.0
            for name, pts in get_tubing_routes().items():
                if name == "TUBE_PUMP":
                    continue
                # Slice only the internal routing between the bulkhead panel mount and the cartridge stack
                pts_inside = pts[:4] if name.startswith("TUBE_WASTE") else pts[3:]
                pts_local = [(x, y, z - z_stack) for x, y, z in pts_inside]
                t_conduit = route_spline(pts_local, (TUBE_OD / 2.0) + 0.3)
                add(t_conduit, mode=Mode.SUBTRACT)
        except Exception:
            pass

    return p.part
