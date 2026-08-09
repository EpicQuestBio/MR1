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

    return p.part

def Housing_Lid_Reader():
    """Top reader module lid with threaded neck."""
    lid_thick = 25.0
    ceiling_thick = 10.0
    inset_depth = 2.5
    inset_height = 15.0
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(BASE_W + 2*WALL, BASE_L + 2*WALL, lid_thick)
        edges = p.edges().filter_by(Axis.Z)
        if edges:
            fillet(edges, radius=WALL)

        # Internal Bucket
        with Locations((0, 0, -ceiling_thick/2.0)):
            with BuildPart(mode=Mode.PRIVATE) as bucket:
                Box(BASE_W - 2*WALL - 3.4, BASE_L - 2*WALL - 3.4, lid_thick - ceiling_thick + WALL)
                bedges = bucket.edges().filter_by(Axis.Z)
                if bedges:
                    fillet(bedges, radius=2.0)
            add(bucket.part, mode=Mode.SUBTRACT)

        # Neck Transition
        with Locations((0, 0, lid_thick/2.0)):
            Cone(bottom_radius=(BASE_W-10)/2.0, top_radius=NECK_OD/2.0, height=10.0)
            with Locations((0, 0, 10.0)):
                Cylinder(radius=NECK_OD/2.0, height=NECK_H) # Neck Thread Body

        # Hex Socket Cutout
        with Locations((0, 0, lid_thick/2.0)):
            with BuildSketch():
                RegularPolygon(radius=(HEX_DIAM + 1.0)/2.0, side_count=6)
            extrude(amount=NECK_H + 20.0, mode=Mode.SUBTRACT)

        # Back Wall Connectivity
        with Locations((0, BASE_L/2.0 + WALL, 0)):
            with Locations((-15, 0, 0), (15, 0, 0)):
                Box(12, WALL*10, 6, mode=Mode.SUBTRACT)

        # Lid Mounting Holes
        for x_sign in [-1, 1]:
            for y_sign in [-1, 1]:
                with Locations((x_sign * (BASE_W/2.0 - 2.0), y_sign * (BASE_L/2.0 - 2.0), 0)):
                    Cylinder(radius=3.5/2.0, height=lid_thick*3.0, mode=Mode.SUBTRACT)

        # PCB Standoffs (Underside of Ceiling)
        with Locations((0, 0, lid_thick/2.0 - ceiling_thick)):
            for mx in [-PCB_W/2.0 + 2.0, PCB_W/2.0 - 2.0]:
                for my in [-PCB_L/2.0 + 2.0, PCB_L/2.0 - 2.0]:
                    with Locations((mx, my, -5.0/2.0)):
                        Cylinder(radius=6.0/2.0, height=5.0)
                        Cylinder(radius=2.5/2.0, height=8.0, mode=Mode.SUBTRACT)

    return p.part
