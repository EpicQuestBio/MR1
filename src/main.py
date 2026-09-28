import os
import sys
from build123d import *
from build123d.exporters3d import export_step, export_stl

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import *
from src.nanopore_wafer_mold import Nanopore_Wafer_Mold_Left, Nanopore_Wafer_Mold_Right
from src.cartridge import (
    PCB_Rigid_Active, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket,
    Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Pressure_Puck,
    Nanopore_Wafer_Silicon
)
from src.adapters import Threaded_Luer_Adapter, Elbow_Adapter
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.connectors import JST_XH_2_Pin_Header, JST_XH_2_Pin_Plug, USB_C_Panel_Mount, Luer_Bulkhead_Panel_Mount

def export_all():
    exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    print(f"Exporting CAD assets to: {exports_dir}")

    # 1. 3D Parts Inventory
    print("Generating 3D Parts...")
    parts_3d = {
        "Nanopore_Wafer_Mold_Left": Nanopore_Wafer_Mold_Left(),
        "Nanopore_Wafer_Mold_Right": Nanopore_Wafer_Mold_Right(),
        "PCB_Rigid_Active": PCB_Rigid_Active(),
        "Nanopore_Wafer_Silicon": Nanopore_Wafer_Silicon(),
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
        "JST_XH_2_Pin_Header": JST_XH_2_Pin_Header(),
        "JST_XH_2_Pin_Plug": JST_XH_2_Pin_Plug(),
        "USB_C_Panel_Mount": USB_C_Panel_Mount(),
        "Luer_Bulkhead_Panel_Mount": Luer_Bulkhead_Panel_Mount(),
    }

    # 2. 2D DXF Profiles (for KiCad PCB Edge.Cuts & keepout synchronization)
    parts_dxf = {
        "PCB_DXF": parts_3d["PCB_Rigid_Active"],
        "PCB_Amplifier_DXF": parts_3d["PCB_Rigid_Active"],
        "PCB_Main_Reader_DXF": parts_3d["PCB_Rigid_Active"],
        "Plate_1_Base_DXF": parts_3d["Plate_1_Base_Hex"],
        "Plate_3_Top_DXF": parts_3d["Plate_3_Top_Hex"],
        "Bottom_Pusher_Plate_DXF": parts_3d["Bottom_Pusher_Plate"],
        "Gasket_Top_DXF": parts_3d["Cast_Nanopore_Wafer_Gasket"],
        "Gasket_Bottom_DXF": parts_3d["Fitted_Amplifier_Gasket"],
        "Gasket_Main_DXF": parts_3d["Cast_Nanopore_Wafer_Gasket"],
    }

    # Optional argument to filter parts
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Export 3D Solids
    for name, part in parts_3d.items():
        if target in ("all", name, "3d"):
            print(f"Exporting 3D: {name}...")
            try:
                step_path = os.path.join(exports_dir, f"{name}.step")
                stl_path = os.path.join(exports_dir, f"{name}.stl")
                export_step(part, step_path)
                export_stl(part, stl_path)
            except Exception as e:
                print(f"Failed to export {name}: {e}")

    # Export 2D DXF Sketches
    for name, part in parts_dxf.items():
        if target in ("all", name, "dxf"):
            print(f"Exporting DXF: {name}...")
            try:
                with BuildSketch() as s:
                    add(part.faces().sort_by(Axis.Z)[0])
                exporter = ExportDXF(unit=Unit.MM)
                exporter.add_shape(s.sketch)
                dxf_path = os.path.join(exports_dir, f"{name}.dxf")
                exporter.write(dxf_path)
            except Exception as e:
                print(f"Failed to export DXF {name}: {e}")

    print("Export Complete.")

if __name__ == "__main__":
    export_all()
