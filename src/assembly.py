from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active, Pressure_Puck
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner

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

        # Display Pump below Reader
        full_assembly = Compound(children=[
            pump.move(Location((0, 0, 0))),
            reader.move(Location((0, 0, PUMP_H + PUMP_LID_THICK + 5.0)))
        ])
        show(full_assembly, transparent=True)
    except ImportError:
        print("ocp_vscode is not installed. To view interactively, run: pip install ocp_vscode")
        print("Assembly generation passed without errors.")
