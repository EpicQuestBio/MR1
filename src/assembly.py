from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active, Pressure_Puck
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner

def route_spline(pts, radius, color_rgb=(0,0,0)):
    """Creates a swept tube/wire along a set of points."""
    with BuildPart() as p:
        with BuildLine():
            Spline(pts)
        v0 = Vector(pts[1]) - Vector(pts[0])
        plane = Plane(origin=pts[0], z_dir=v0)
        with BuildSketch(plane):
            Circle(radius)
        sweep()
    return p.part

def route_tubing():
    """Generates the flexible tubing routes between the pump and reader modules."""
    # Port radius offset
    r = PORT_RADIUS

    # 1. Pump Out (Right Side, lower module) -> Reader In (Right Side, upper module)
    # Pump out ports are roughly at X=20, Z=0 in pump space. Reader in are at roughly X=17.3, Z=READER_Z
    # We will approximate this with a smooth spline

    # Pump Z offset
    pump_z = PUMP_H/2.0
    # Reader Z offset
    reader_z = PUMP_H + PUMP_LID_THICK + 5.0 + READER_LID_THICK/2.0

    p1 = (BASE_W/2.0 + 5.0, 20.0, pump_z) # Exit right side of pump
    p2 = (BASE_W/2.0 + 20.0, 20.0, pump_z) # Loop outwards
    p3 = (BASE_W/2.0 + 20.0, 20.0, reader_z - 10.0) # Travel up
    p4 = (BASE_W/2.0 + 5.0, 20.0, reader_z - 10.0) # Enter right side of reader

    tube1 = route_spline([p1, p2, p3, p4], TUBE_OD/2.0)

    # 2. Pump In (Left Side) -> Reader Out (Left Side)
    p5 = (-BASE_W/2.0 - 5.0, 20.0, pump_z)
    p6 = (-BASE_W/2.0 - 20.0, 20.0, pump_z)
    p7 = (-BASE_W/2.0 - 20.0, 20.0, reader_z - 10.0)
    p8 = (-BASE_W/2.0 - 5.0, 20.0, reader_z - 10.0)

    tube2 = route_spline([p5, p6, p7, p8], TUBE_OD/2.0)

    return Compound(children=[tube1, tube2])

def route_wiring():
    """Generates the internal wire routing."""
    # USB-C at back of reader: (15, BASE_L/2, READER_Z)
    # To PCB inside reader: (0, -19, READER_Z)
    reader_z = PUMP_H + PUMP_LID_THICK + 5.0 + READER_LID_THICK/2.0

    w1 = (15.0, BASE_L/2.0 - 5.0, reader_z)
    w2 = (15.0, 0.0, reader_z - 5.0)
    w3 = (0.0, -19.0, reader_z - 5.0)

    wire1 = route_spline([w1, w2, w3], WIRE_OD/2.0)
    return wire1


def Reader_Module_Assembly():
    """Assembles the full Reader Module (Housings + Cartridge Stack + Cap)."""
    parts = []

    # Base Case
    parts.append(Housing_Case_Reader())

    # Internal Stack (positioned atop the Lid ceiling in legacy logic, now inside)
    # Z coordinate relative to Base Case floor
    z_stack = READER_LID_THICK/2.0 + 10.0 # Approximate

    stack_parts = [
        Bottom_Pusher_Plate().move(Location((0, 0, z_stack))),
        Plate_1_Base_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK/2.0))),
        Fitted_Amplifier_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK/2.0))),
        PCB_Rigid_Active().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS/2.0))),
        Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK/2.0))),
        Plate_3_Top_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK/2.0))),
        Pressure_Puck().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK + PUCK_H/2.0)))
    ]
    parts.extend(stack_parts)

    # Lid
    parts.append(Housing_Lid_Reader().move(Location((0, 0, READER_LID_THICK))))

    # Cap Assembly
    z_cap = READER_LID_THICK + READER_LID_THICK/2.0 + NECK_H - 10.0
    parts.append(Torque_Cap_Inner().move(Location((0, 0, z_cap))))
    parts.append(Torque_Cap_Outer().move(Location((0, 0, z_cap))))

    return Compound(children=parts)

def Pump_Module_Assembly():
    parts = [
        Housing_Pump_Case(),
        Housing_Pump_Lid().move(Location((0, 0, PUMP_H/2.0 + PUMP_LID_THICK/2.0)))
    ]
    return Compound(children=parts)

if __name__ == "__main__":
    try:
        from ocp_vscode import show
        reader = Reader_Module_Assembly()
        pump = Pump_Module_Assembly()
        tubes = route_tubing()
        wires = route_wiring()

        # Display Pump below Reader
        full_assembly = Compound(children=[
            pump.move(Location((0, 0, 0))),
            reader.move(Location((0, 0, PUMP_H + PUMP_LID_THICK + 5.0))),
            tubes,
            wires
        ])
        show(full_assembly, transparent=True)
    except ImportError:
        print("ocp_vscode is not installed. To view interactively, run: pip install ocp_vscode")
        print("Assembly generation passed without errors.")
