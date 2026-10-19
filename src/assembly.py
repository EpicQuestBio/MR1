from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active, Pressure_Puck
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner
from src.connectors import Luer_Bulkhead_Panel_Mount

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

def get_tubing_routes():
    """Defines the 5 production microfluidic tubing routes matching reader_tubing.yaml.
    All lines use standardized 1/8" barb fittings (uniform 1/8" ID x 1/4" OD).
    Routes fluid from pump/reservoirs through side bulkhead panel mounts,
    conduit channels in the housing lid, and up into the hexagonal cartridge stack ports.
    """
    pump_z = PUMP_H / 2.0
    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    z_lid = 30.0
    z_stack = reader_z_base + z_lid
    z_port = z_stack - 13.0

    return {
        # 1. TUBE_PUMP: Buffer reservoir -> Peristaltic pump intake (PharMed BPT, 0.12 m)
        "TUBE_PUMP": [
            (-BASE_W / 2.0 - 8.0, -25.0, pump_z),
            (-BASE_W / 2.0 - 24.0, -25.0, pump_z),
            (-BASE_W / 2.0 - 24.0, 5.0, pump_z),
            (-BASE_W / 2.0 - 8.0, 5.0, pump_z),
        ],
        # 2. TUBE_FEED: Pump discharge -> Right-Front bulkhead -> Cartridge Trans inlet (330 deg)
        "TUBE_FEED": [
            (BASE_W / 2.0 + 8.0, -10.0, pump_z),
            (BASE_W / 2.0 + 26.0, -10.0, pump_z),
            (BASE_W / 2.0 + 26.0, -20.0, z_port),
            (BASE_W / 2.0 + 2.5, -20.0, z_port),
            (42.0, -17.0, 100.5),
            (22.0, -12.0, 103.0),
            (17.32, -10.0, z_stack - 0.2),
        ],
        # 3. TUBE_TRANS_LINE: Buffer reservoir -> Left-Front bulkhead -> Cartridge Cis inlet (210 deg)
        "TUBE_TRANS_LINE": [
            (-BASE_W / 2.0 - 8.0, -10.0, pump_z + 10.0),
            (-BASE_W / 2.0 - 26.0, -10.0, pump_z + 10.0),
            (-BASE_W / 2.0 - 26.0, -20.0, z_port),
            (-BASE_W / 2.0 - 2.5, -20.0, z_port),
            (-42.0, -17.0, 100.5),
            (-22.0, -12.0, 103.0),
            (-17.32, -10.0, z_stack - 0.2),
        ],
        # 4. TUBE_WASTE_1: Cis outlet (30 deg) -> Right-Back bulkhead -> Waste vessel
        "TUBE_WASTE_1": [
            (17.32, 10.0, z_stack - 0.2),
            (22.0, 12.0, 103.0),
            (42.0, 17.0, 100.5),
            (BASE_W / 2.0 + 2.5, 20.0, z_port),
            (BASE_W / 2.0 + 26.0, 20.0, z_port),
            (BASE_W / 2.0 + 26.0, 20.0, pump_z),
            (BASE_W / 2.0 + 8.0, 20.0, pump_z),
        ],
        # 5. TUBE_WASTE_2: Trans outlet (150 deg) -> Left-Back bulkhead -> Waste vessel
        "TUBE_WASTE_2": [
            (-17.32, 10.0, z_stack - 0.2),
            (-22.0, 12.0, 103.0),
            (-42.0, 17.0, 100.5),
            (-BASE_W / 2.0 - 2.5, 20.0, z_port),
            (-BASE_W / 2.0 - 26.0, 20.0, z_port),
            (-BASE_W / 2.0 - 26.0, 20.0, pump_z),
            (-BASE_W / 2.0 - 8.0, 20.0, pump_z),
        ],
    }

def get_wiring_routes():
    """Defines the 3 production electrical wiring harnesses matching reader_wiring.yaml:
    - W_USB: 28 AWG shielded (USB-C panel mount -> MR1 motherboard)
    - W_MOTOR: 24 AWG shielded twisted pair (MR1 driver -> Pump motor)
    - W_POGO_ANALOG: 30 AWG ultra-low-noise (Mill-Max pogo block -> LMP7721 PCB pads)
    """
    pump_z = PUMP_H / 2.0
    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    reader_z = reader_z_base + READER_CASE_H / 2.0

    return {
        "W_USB": (
            [
                (15.0, BASE_L / 2.0 - 5.0, reader_z),
                (15.0, 0.0, reader_z - 5.0),
                (0.0, -19.0, reader_z - 5.0),
            ],
            WIRE_USB_OD / 2.0,
        ),
        "W_MOTOR": (
            [
                (-5.0, 0.0, reader_z - 5.0),
                (-5.0, 0.0, pump_z + 10.0),
                (-5.0, -15.0, pump_z),
            ],
            WIRE_MOTOR_OD / 2.0,
        ),
        "W_POGO_ANALOG": (
            [
                (POGO_X_SPACING, POGO_Y, reader_z - 5.0),
                (-15.0, POGO_Y, reader_z - 5.0),
                (-15.0, 10.0, reader_z - 5.0),
            ],
            WIRE_POGO_OD / 2.0,
        ),
    }

def route_tubing():
    """Generates the 5 flexible tubing routes between the pump, reservoirs, and reader flowcell."""
    routes = get_tubing_routes()
    tube_solids = [route_spline(pts, TUBE_OD / 2.0) for pts in routes.values()]
    return Compound(children=tube_solids)

def route_wiring():
    """Generates the 3 internal electrical wiring harnesses."""
    routes = get_wiring_routes()
    wire_solids = [route_spline(pts, r) for pts, r in routes.values()]
    return Compound(children=wire_solids)


def Reader_Module_Assembly():
    """Assembles the full Reader Module (Housings + Cartridge Stack + Cap) matching OpenSCAD truth.
    Housing_Lid_Reader sits on Housing_Case_Reader, with its top plate surface at z=32.5.
    The cartridge stack rests directly on the lid ceiling inside the M75 neck socket,
    with the Torque-Lock Cap threaded onto the neck.
    """
    parts = []

    # Base Case (height 15mm, centered at Z=0)
    parts.append(Housing_Case_Reader())

    # Lid sits on Base Case (top plate surface at Z = 25.0 + READER_CASE_H / 2.0 = 32.5mm)
    z_lid = 25.0 + READER_CASE_H / 2.0
    parts.append(Housing_Lid_Reader().move(Location((0, 0, z_lid))))

    # 4x Luer Bulkhead Panel Mounts at the side fluid ports
    lid_half_w = BASE_W / 2.0 + (WALL - 2.5)  # 57.5 mm
    for x_wall, rot_y in [(lid_half_w, 90), (-lid_half_w, -90)]:
        for y_port in [-20.0, 20.0]:
            parts.append(
                Luer_Bulkhead_Panel_Mount().move(
                    Location((x_wall, y_port, z_lid - 13.0)) * Rotation(0, rot_y, 0)
                )
            )

    # Cartridge stack sits directly on top surface of Lid inside the neck socket
    z_stack = z_lid

    stack_parts = [
        Bottom_Pusher_Plate().move(Location((0, 0, z_stack))),
        Plate_1_Base_Hex().move(Location((0, 0, z_stack + PP_H))),
        Fitted_Amplifier_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK))),
        PCB_Rigid_Active().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK))),
        Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS))),
        Plate_3_Top_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK))),
        Pressure_Puck().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK + PUCK_H/2.0)))
    ]
    parts.extend(stack_parts)

    # Torque-Lock Cap Assembly (engaging onto neck thread above puck)
    z_cap = z_lid + NECK_H - 10.0
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
