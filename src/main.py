import sys
from build123d.exporters3d import export_step, export_stl
from src.constants import *
from src.nanopore_wafer_mold import Nanopore_Wafer_Mold_Left, Nanopore_Wafer_Mold_Right
from src.cartridge import (
    PCB_Rigid_Active, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket,
    Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Pressure_Puck
)
from src.adapters import Threaded_Luer_Adapter, Elbow_Adapter
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader

def export_all():
    print("Generating Parts...")

    parts = {
        "Nanopore_Wafer_Mold_Left": Nanopore_Wafer_Mold_Left(),
        "Nanopore_Wafer_Mold_Right": Nanopore_Wafer_Mold_Right(),
        "PCB_Rigid_Active": PCB_Rigid_Active(),
        "Cast_Nanopore_Wafer_Gasket": Cast_Nanopore_Wafer_Gasket(),
        "Fitted_Amplifier_Gasket": Fitted_Amplifier_Gasket(),
        "Bottom_Pusher_Plate": Bottom_Pusher_Plate(),
        "Plate_1_Base_Hex": Plate_1_Base_Hex(),
        "Plate_3_Top_Hex": Plate_3_Top_Hex(),
        "Pressure_Puck": Pressure_Puck(),
        "Threaded_Luer_Adapter": Threaded_Luer_Adapter(),
        "Elbow_Adapter": Elbow_Adapter(),
        "Torque_Cap_Outer": Torque_Cap_Outer(),
        "Torque_Cap_Inner": Torque_Cap_Inner(),
        "Housing_Pump_Case": Housing_Pump_Case(),
        "Housing_Pump_Lid": Housing_Pump_Lid(),
        "Housing_Case_Reader": Housing_Case_Reader(),
        "Housing_Lid_Reader": Housing_Lid_Reader(),
    }

    # Optional arguments to filter parts
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    for name, part in parts.items():
        if target == "all" or target == name:
            print(f"Exporting {name}...")
            try:
                export_step(part, f"{name}.step")
                export_stl(part, f"{name}.stl")
            except Exception as e:
                print(f"Failed to export {name}: {e}")

    print("Export Complete.")

if __name__ == "__main__":
    export_all()
