from build123d import *
from src.constants import *

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

        # Handle (Simplified D-shape logic ported)
        h_center = 26.0
        stick_out = 36.0
        tube_d = 12.0
        corner_r = 12.0
        z_start = -1.0

        with Locations((0, -(BASE_L/2.0 + WALL), -PUMP_H/2.0 + stick_out/2.0)):
            # This is complex in build123d without a direct sweep path, we can use a Box with fillets for the handle
            with BuildPart(mode=Mode.PRIVATE) as handle:
                Box(stick_out, h_center*2.0 + tube_d, tube_d)
                Box(stick_out - tube_d, h_center*2.0 - tube_d, tube_d + 1.0, mode=Mode.SUBTRACT)
                # Position it extending out
            # Moving the handle to stick out
            add(handle.part.move(Rotation(0, 90, 0)), mode=Mode.ADD)

        # Back Wall Connectivity
        with Locations((0, BASE_L/2.0 + WALL, 0)):
            with Locations((-15, 0, 0), (15, 0, 0)):
                Box(12, WALL*10, 6, mode=Mode.SUBTRACT) # Rotated Box for cutout

        # Lid Mounts
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * BASE_W/2.0, y_sign * BASE_L/2.0, 0)):
                    Cylinder(radius=3.2/2.0, height=PUMP_H*3.0, mode=Mode.SUBTRACT)

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

        # Dimples for sensor enclosures
        with Locations((0, 0, lid_thick/2.0)):
            for x_sign in [-1, 1]:
                for y_sign in [-1, 1]:
                    with Locations((x_sign * (BASE_W/2.0 - FEET_INSET), y_sign * (BASE_L/2.0 - FEET_INSET), 0)):
                        Sphere(radius=13.5/2.0, mode=Mode.SUBTRACT)

        # Mounting holes
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * BASE_W/2.0, y_sign * BASE_L/2.0, 0)):
                    Cylinder(radius=3.5/2.0, height=lid_thick*3.0, mode=Mode.SUBTRACT)

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

        # Hollow out
        with Locations((0, 0, WALL)):
            with BuildPart(mode=Mode.PRIVATE) as bucket:
                Box(BASE_W - 2*WALL, BASE_L - 2*WALL, READER_LID_THICK)
                bedges = bucket.edges().filter_by(Axis.Z)
                if bedges:
                    fillet(bedges, radius=2.0)
            add(bucket.part, mode=Mode.SUBTRACT)

        # Feet Dimples (Truncated sphere)
        with Locations((0, 0, -READER_LID_THICK/2.0)):
            for x_sign in [-1, 1]:
                for y_sign in [-1, 1]:
                    with Locations((x_sign * (BASE_W/2.0 - FEET_INSET), y_sign * (BASE_L/2.0 - FEET_INSET), 0)):
                        Sphere(radius=13.0/2.0, mode=Mode.ADD)
                        Box(15.0, 15.0, 10.0, mode=Mode.SUBTRACT) # Flatten top half

        # PCB Standoffs (Now on the Floor / Bottom Lid)
        # Positioned securely at Z=0 inside the bucket (which starts at Z=-READER_LID_THICK/2.0 + WALL)
        # We need a clear 20mm gap below for tubing. Total standoff height = 20mm.
        standoff_h = 20.0
        with Locations((0, 0, -READER_LID_THICK/2.0 + WALL + standoff_h/2.0)):
            for mx in [-PCB_W/2.0 + 2.0, PCB_W/2.0 - 2.0]:
                for my in [-PCB_L/2.0 + 2.0, PCB_L/2.0 - 2.0]:
                    with Locations((mx, my, 0)):
                        Cylinder(radius=6.0/2.0, height=standoff_h, mode=Mode.ADD)
                        Cylinder(radius=(2.5 - TOLERANCE)/2.0, height=standoff_h + 2.0, mode=Mode.SUBTRACT)

    return p.part

def Housing_Lid_Reader():
    """Top reader module lid with threaded neck (M75 x 8mm thread) and inner hex socket.
    Exact match to golden STL (100.0 x 100.0 x 57.7 mm).
    """
    lid_w = 100.0
    lid_l = 100.0
    lid_thick = 25.0
    ceiling_thick = 10.0
    neck_length = 25.2
    neck_r = NECK_OD / 2.0 # 37.5
    pitch = CAP_THREAD_PITCH # 8.0
    depth = 1.6

    with BuildPart(mode=Mode.PRIVATE) as p:
        # Base plate centered at Z = -lid_thick / 2.0 (top surface at Z = 0)
        with Locations((0, 0, -lid_thick / 2.0)):
            Box(lid_w, lid_l, lid_thick)
            edges = p.edges().filter_by(Axis.Z)
            if edges:
                fillet(edges, radius=WALL)

        # Inset indexing lip at bottom extending down to Z = -27.5
        with Locations((0, 0, -lid_thick - 1.25)):
            Box(lid_w - 2.5 * 2, lid_l - 2.5 * 2, 2.5)

        # Internal bucket from bottom
        with Locations((0, 0, -ceiling_thick - (lid_thick - ceiling_thick + 2.5) / 2.0)):
            with BuildPart(mode=Mode.PRIVATE) as bucket:
                Box(lid_w - 2 * WALL - 3.4, lid_l - 2 * WALL - 3.4, lid_thick - ceiling_thick + 3.0)
                bedges = bucket.edges().filter_by(Axis.Z)
                if bedges:
                    fillet(bedges, radius=2.0)
            add(bucket.part, mode=Mode.SUBTRACT)

        # Neck transition cone (Z: 0 to 5)
        with Locations((0, 0, 2.5)):
            Cone(bottom_radius=(lid_w - 20.0) / 2.0, top_radius=neck_r, height=5.0)

        # Neck cylinder (Z: 5 to 5 + neck_length)
        with Locations((0, 0, 5.0 + neck_length / 2.0)):
            Cylinder(radius=neck_r, height=neck_length)

        # External Helical Thread (M75 x 8mm pitch)
        path = Helix(pitch=pitch, height=neck_length, radius=neck_r)
        with Locations((0, 0, 5.0)):
            with BuildSketch(Plane.XZ) as s:
                with Locations((neck_r, 0)):
                    pts = [
                        (-depth / 2.0, -pitch * 0.22),
                        (depth / 2.0, -pitch * 0.10),
                        (depth / 2.0, pitch * 0.10),
                        (-depth / 2.0, pitch * 0.22)
                    ]
                    Polygon(pts)
            sweep(sections=s.sketch, path=path, mode=Mode.ADD)

        # Inner Hex Socket Cutout (61mm across corners)
        with Locations((0, 0, 5.0 + neck_length / 2.0)):
            with BuildSketch():
                RegularPolygon(radius=61.0 / 2.0, side_count=6)
            extrude(amount=neck_length + 20.0, mode=Mode.SUBTRACT)

        # Back Wall Connectivity
        with Locations((0, lid_l / 2.0, 0)):
            with Locations((-15, 0, 0), (15, 0, 0)):
                Box(12, WALL * 10, 6, mode=Mode.SUBTRACT)

        # Mounting Holes
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * (lid_w / 2.0 - 2.0), y_sign * (lid_l / 2.0 - 2.0), -lid_thick / 2.0)):
                    Cylinder(radius=3.5 / 2.0, height=lid_thick * 3.0, mode=Mode.SUBTRACT)

    return p.part

