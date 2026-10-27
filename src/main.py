# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

import os
import sys
from build123d import *
from build123d.exporters3d import export_step, export_stl

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import *
from src.nanopore_wafer_mold import (
    Nanopore_Wafer_Mold_Left,
    Nanopore_Wafer_Mold_Right,
    Concentric_Guard_Mold_Plate_Top,
    Bottom_Fluidic_Electrode_Mold_Plate,
    MidLayer_PVA_Alignment_Frame
)
from src.cartridge import (
    PCB_Rigid_Active, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket,
    Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Pressure_Puck,
    Nanopore_Wafer_Silicon, PCB_Main_Reader_2D, PCB_Main_Reader,
    Carrier_Frame_Hex, Nanopore_Carrier, PTFE_Interposer, Interposer,
    Silver_Chloride_Ribbon_Pads, PCB_Pump_Controller_2D, PCB_Pump_Controller
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
        "Amplifier_Gasket_Mold_Left": Nanopore_Wafer_Mold_Left(is_nanopore=False),
        "Amplifier_Gasket_Mold_Right": Nanopore_Wafer_Mold_Right(is_nanopore=False),
        "Concentric_Guard_Mold_Plate_Top": Concentric_Guard_Mold_Plate_Top(),
        "Bottom_Fluidic_Electrode_Mold_Plate": Bottom_Fluidic_Electrode_Mold_Plate(),
        "MidLayer_PVA_Alignment_Frame": MidLayer_PVA_Alignment_Frame(),
        "PCB_Rigid_Active": PCB_Rigid_Active(),
        "PTFE_Interposer": PTFE_Interposer(render_electrodes=True),
        "Silver_Chloride_Ribbon_Pads_Top": Silver_Chloride_Ribbon_Pads(top=True),
        "Silver_Chloride_Ribbon_Pads_Bottom": Silver_Chloride_Ribbon_Pads(top=False),
        "PCB_Main_Reader": PCB_Main_Reader(),
        "Carrier_Frame_Hex": Carrier_Frame_Hex(),
        "Nanopore_Carrier": Nanopore_Carrier(),
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
        "PCB_Pump_Controller": PCB_Pump_Controller(),
        "JST_XH_2_Pin_Header": JST_XH_2_Pin_Header(),
        "JST_XH_2_Pin_Plug": JST_XH_2_Pin_Plug(),
        "USB_C_Panel_Mount": USB_C_Panel_Mount(),
        "Luer_Bulkhead_Panel_Mount": Luer_Bulkhead_Panel_Mount(),
    }

    # 2. 2D DXF Profiles (for KiCad PCB Edge.Cuts & keepout synchronization)
    parts_dxf = {
        "PCB_DXF": PCB_Main_Reader_2D(),
        "PCB_Amplifier_DXF": parts_3d["PCB_Rigid_Active"],
        "Interposer_DXF": parts_3d["PTFE_Interposer"],
        "PCB_Interposer_DXF": parts_3d["PTFE_Interposer"],
        "PCB_Main_Reader_DXF": PCB_Main_Reader_2D(),
        "PCB_Pump_Controller_DXF": PCB_Pump_Controller_2D(),
        "Plate_1_Base_DXF": parts_3d["Plate_1_Base_Hex"],
        "Plate_2_Channel_DXF": parts_3d["Carrier_Frame_Hex"],
        "Plate_3_Top_DXF": parts_3d["Plate_3_Top_Hex"],
        "PCB_Nanopore_Carrier_DXF": parts_3d["Nanopore_Carrier"],
        "Bottom_Pusher_Plate_DXF": parts_3d["Bottom_Pusher_Plate"],
        "Gasket_Top_DXF": parts_3d["Cast_Nanopore_Wafer_Gasket"],
        "Gasket_Bottom_DXF": parts_3d["Fitted_Amplifier_Gasket"],
        "Gasket_Main_DXF": parts_3d["Cast_Nanopore_Wafer_Gasket"],
    }

    enable_viewer = any(arg in sys.argv for arg in ("--viewer", "--show", "-v"))
    cli_args = [arg for arg in sys.argv[1:] if arg not in ("--viewer", "--show", "-v")]
    target = cli_args[0] if len(cli_args) > 0 else "all"

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
                exporter = ExportDXF(unit=Unit.MM)
                if isinstance(part, Sketch):
                    exporter.add_shape(part)
                elif hasattr(part, "faces"):
                    z_faces = part.faces().filter_by(Axis.Z)
                    main_face = max(z_faces, key=lambda f: f.area) if z_faces else part.faces().sort_by(Axis.Z)[0]
                    with BuildSketch() as s:
                        add(main_face)
                    exporter.add_shape(s.sketch)
                else:
                    exporter.add_shape(part)
                dxf_path = os.path.join(exports_dir, f"{name}.dxf")
                exporter.write(dxf_path)
            except Exception as e:
                print(f"Failed to export DXF {name}: {e}")

    print("Export Complete.")

    if enable_viewer:
        try:
            from ocp_viewer import show, show_object, set_port
            set_port(3939)
            if target in parts_3d:
                show_object(parts_3d[target], name=target)
                print(f"Pushed '{target}' to ocp_viewer on port 3939.")
            else:
                assembly = Compound(children=list(parts_3d.values()))
                show(assembly, names=["MR1 Parts Inventory"], transparent=True)
                print("Pushed 3D parts to ocp_viewer on port 3939.")
        except ImportError:
            print("ocp_viewer is not installed. To view interactively, run: pip install ocp_viewer")
        except Exception as e:
            print(f"Could not push to ocp_viewer: {e}")

if __name__ == "__main__":
    export_all()
