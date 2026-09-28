#!/usr/bin/env python3
import os
import sys
import math
import numpy as np
import pyvista as pv
import imageio.v2 as imageio
from build123d import *

# Ensure src import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import (
    Bottom_Pusher_Plate,
    Plate_1_Base_Hex,
    Plate_3_Top_Hex,
    Cast_Nanopore_Wafer_Gasket,
    Fitted_Amplifier_Gasket,
    PCB_Rigid_Active,
    Pressure_Puck
)
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner
from src.assembly import route_tubing, route_wiring

def shape_to_pv_mesh(shape, linear_deflection=0.1, angular_deflection=0.2):
    """Converts a build123d shape (Part/Solid/Compound) into a PyVista PolyData mesh."""
    vertices = []
    triangles = []
    v_offset = 0

    if hasattr(shape, 'solids'):
        solids = shape.solids()
    else:
        solids = [shape]

    for solid in solids:
        try:
            tess = solid.tessellate(linear_deflection, angular_deflection)
            pts = tess[0]
            faces = tess[1]

            for p in pts:
                vertices.append([p.X, p.Y, p.Z])

            for f in faces:
                triangles.append([3, f[0] + v_offset, f[1] + v_offset, f[2] + v_offset])

            v_offset += len(pts)
        except Exception as e:
            # Fallback for individual faces if solid tessellation has issues
            for face in solid.faces():
                try:
                    ftess = face.tessellate(linear_deflection, angular_deflection)
                    opts = ftess[0]
                    ofaces = ftess[1]
                    for p in opts:
                        vertices.append([p.X, p.Y, p.Z])
                    for f in ofaces:
                        triangles.append([3, f[0] + v_offset, f[1] + v_offset, f[2] + v_offset])
                    v_offset += len(opts)
                except Exception:
                    pass

    if not vertices:
        return None

    faces_array = np.hstack(triangles)
    vertices_array = np.array(vertices, dtype=np.float32)
    mesh = pv.PolyData(vertices_array, faces_array)
    mesh = mesh.clean()
    mesh.compute_normals(inplace=True)
    return mesh

# Custom PBR Material definitions
MATERIALS = {
    'silicone_translucent': {
        'color': '#E0E8EF',
        'opacity': 0.75,
        'metallic': 0.1,
        'roughness': 0.3,
        'smooth_shading': True
    },
    'tpu_black': {
        'color': '#2B2D2F',
        'opacity': 1.0,
        'metallic': 0.05,
        'roughness': 0.5,
        'smooth_shading': True
    },
    'polypropylene_grey': {
        'color': '#4A5056',
        'opacity': 1.0,
        'metallic': 0.1,
        'roughness': 0.4,
        'smooth_shading': True
    },
    'pcb_fr4_green': {
        'color': '#1B4D2E',
        'opacity': 1.0,
        'metallic': 0.2,
        'roughness': 0.3,
        'smooth_shading': True
    },
    'silicon_wafer': {
        'color': '#465666',
        'opacity': 1.0,
        'metallic': 0.9,
        'roughness': 0.1,
        'smooth_shading': True
    },
    'housing_dark': {
        'color': '#36393E',
        'opacity': 1.0,
        'metallic': 0.15,
        'roughness': 0.35,
        'smooth_shading': True
    },
    'cap_blue': {
        'color': '#1D6F93',
        'opacity': 1.0,
        'metallic': 0.3,
        'roughness': 0.25,
        'smooth_shading': True
    },
    'tubing_clear': {
        'color': '#EBF5FB',
        'opacity': 0.6,
        'metallic': 0.1,
        'roughness': 0.15,
        'smooth_shading': True
    },
    'wiring_copper': {
        'color': '#B87333',
        'opacity': 1.0,
        'metallic': 0.85,
        'roughness': 0.2,
        'smooth_shading': True
    }
}

def create_nanopore_wafer_mesh():
    """Generates the nanopore wafer silicon mesh from the canonical source model."""
    from src.cartridge import Nanopore_Wafer_Silicon
    wafer = Nanopore_Wafer_Silicon()
    return shape_to_pv_mesh(wafer)

def build_exploded_cartridge_components():
    """Builds exploded cartridge components along Z axis for Shot 1."""
    components = []
    z_spacing = 16.0  # Exploded separation distance

    # 1. Bottom Pusher Plate
    bpp = Bottom_Pusher_Plate().move(Location((0, 0, 0 * z_spacing)))
    components.append((shape_to_pv_mesh(bpp), MATERIALS['tpu_black']))

    # 2. Plate 1 Base Hex
    p1 = Plate_1_Base_Hex().move(Location((0, 0, 1 * z_spacing)))
    components.append((shape_to_pv_mesh(p1), MATERIALS['polypropylene_grey']))

    # 3. Fitted Amplifier Gasket
    gasket1 = Fitted_Amplifier_Gasket().move(Location((0, 0, 2 * z_spacing)))
    components.append((shape_to_pv_mesh(gasket1), MATERIALS['silicone_translucent']))

    # 4. PCB Active
    pcb = PCB_Rigid_Active().move(Location((0, 0, 3 * z_spacing)))
    components.append((shape_to_pv_mesh(pcb), MATERIALS['pcb_fr4_green']))

    # 5. Nanopore Wafer (Centered at PCB wafer pocket)
    wafer_mesh = create_nanopore_wafer_mesh()
    if wafer_mesh:
        wafer_mesh.translate((0, 0, 3 * z_spacing + 0.4), inplace=True)
        components.append((wafer_mesh, MATERIALS['silicon_wafer']))

    # 6. Cast Nanopore Wafer Gasket
    gasket2 = Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, 4 * z_spacing)))
    components.append((shape_to_pv_mesh(gasket2), MATERIALS['silicone_translucent']))

    # 7. Plate 3 Top Hex
    p3 = Plate_3_Top_Hex().move(Location((0, 0, 5 * z_spacing)))
    components.append((shape_to_pv_mesh(p3), MATERIALS['polypropylene_grey']))

    # 8. Pressure Puck
    puck = Pressure_Puck().move(Location((0, 0, 6 * z_spacing)))
    components.append((shape_to_pv_mesh(puck), MATERIALS['tpu_black']))

    return components

def build_assembled_device_components():
    """Builds fully assembled Sentinel Nanopore Reader device for Shot 2."""
    components = []

    # Pump Case & Lid
    pump_case = Housing_Pump_Case().move(Location((0, 0, 0)))
    pump_lid = Housing_Pump_Lid().move(Location((0, 0, PUMP_H/2.0 + PUMP_LID_THICK/2.0)))
    components.append((shape_to_pv_mesh(pump_case), MATERIALS['housing_dark']))
    components.append((shape_to_pv_mesh(pump_lid), MATERIALS['housing_dark']))

    # Reader Case & Lid
    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    reader_case = Housing_Case_Reader().move(Location((0, 0, reader_z_base)))
    reader_lid = Housing_Lid_Reader().move(Location((0, 0, reader_z_base + READER_LID_THICK)))
    components.append((shape_to_pv_mesh(reader_case), MATERIALS['housing_dark']))
    components.append((shape_to_pv_mesh(reader_lid), MATERIALS['housing_dark']))

    # Torque Cap
    z_cap = reader_z_base + READER_LID_THICK + READER_LID_THICK/2.0 + NECK_H - 10.0
    cap_inner = Torque_Cap_Inner().move(Location((0, 0, z_cap)))
    cap_outer = Torque_Cap_Outer().move(Location((0, 0, z_cap)))
    components.append((shape_to_pv_mesh(cap_inner), MATERIALS['housing_dark']))
    components.append((shape_to_pv_mesh(cap_outer), MATERIALS['cap_blue']))

    # Internal Stack
    z_stack = reader_z_base + READER_LID_THICK/2.0 + 10.0
    stack_parts = [
        (Bottom_Pusher_Plate().move(Location((0, 0, z_stack))), MATERIALS['tpu_black']),
        (Plate_1_Base_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK/2.0))), MATERIALS['polypropylene_grey']),
        (Fitted_Amplifier_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK/2.0))), MATERIALS['silicone_translucent']),
        (PCB_Rigid_Active().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS/2.0))), MATERIALS['pcb_fr4_green']),
        (Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK/2.0))), MATERIALS['silicone_translucent']),
        (Plate_3_Top_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK/2.0))), MATERIALS['polypropylene_grey']),
        (Pressure_Puck().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK + PUCK_H/2.0))), MATERIALS['tpu_black'])
    ]

    for part, mat in stack_parts:
        components.append((shape_to_pv_mesh(part), mat))

    # Nanopore Wafer
    wafer_mesh = create_nanopore_wafer_mesh()
    if wafer_mesh:
        wafer_mesh.translate((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS/2.0 + 0.4), inplace=True)
        components.append((wafer_mesh, MATERIALS['silicon_wafer']))

    # Tubing and Wiring
    tubes = route_tubing()
    wires = route_wiring()
    components.append((shape_to_pv_mesh(tubes), MATERIALS['tubing_clear']))
    components.append((shape_to_pv_mesh(wires), MATERIALS['wiring_copper']))

    return components

def setup_plotter():
    """Configures PyVista Plotter with studio PBR lighting and background."""
    plotter = pv.Plotter(off_screen=True, window_size=[1280, 720])
    plotter.set_background('#1A1D20', top='#2D3238')  # Studio dark gradient background
    plotter.enable_anti_aliasing('ssaa')

    # Studio Lighting Setup
    plotter.remove_all_lights()
    key_light = pv.Light(position=(200, 200, 300), focal_point=(0, 0, 50), intensity=1.2, color='white')
    fill_light = pv.Light(position=(-200, -150, 150), focal_point=(0, 0, 50), intensity=0.5, color='#B0C4DE')
    rim_light = pv.Light(position=(0, -300, -100), focal_point=(0, 0, 50), intensity=0.8, color='#4682B4')
    plotter.add_light(key_light)
    plotter.add_light(fill_light)
    plotter.add_light(rim_light)

    return plotter

def render_shot1_exploded_flythrough(output_webm, output_gif, num_frames=300):
    """Renders Shot 1: 360 Orbit & Fly-Through Zoom onto Nanopore Wafer."""
    print("Generating Shot 1: Exploded Nanopore Wafer Fly-Through...")
    components = build_exploded_cartridge_components()
    plotter = setup_plotter()

    for mesh, mat in components:
        if mesh is not None:
            plotter.add_mesh(
                mesh,
                color=mat['color'],
                opacity=mat['opacity'],
                metallic=mat['metallic'],
                roughness=mat['roughness'],
                smooth_shading=mat['smooth_shading']
            )

    # Focal point: Nanopore Wafer at (0, 0, 3 * 16.0 + 0.4) = (0, 0, 48.4)
    wafer_center = np.array([0.0, 0.0, 48.4])

    frames = []
    for frame in range(num_frames):
        t = frame / (num_frames - 1)

        # Smooth camera trajectory: 360-degree spiral zoom in
        angle = 2 * math.pi * t
        radius = 180.0 * (1.0 - 0.95 * (t ** 1.5)) + 12.0  # From 192mm down to ~21mm
        cam_z = wafer_center[2] + 120.0 * (1.0 - t ** 1.2) + 8.0  # Zoom down towards wafer

        cam_x = wafer_center[0] + radius * math.cos(angle)
        cam_y = wafer_center[1] + radius * math.sin(angle)

        camera_pos = [cam_x, cam_y, cam_z]
        view_up = [0, 0, 1]

        plotter.camera_position = [camera_pos, wafer_center, view_up]
        plotter.render()

        img = plotter.screenshot(return_img=True)
        frames.append(img)

        if frame % 60 == 0:
            print(f"  Shot 1: Processed frame {frame}/{num_frames}")

    plotter.close()

    print(f"Saving Shot 1 WebM: {output_webm}")
    imageio.mimsave(output_webm, frames, fps=30, codec='vp9')
    print(f"Saving Shot 1 GIF: {output_gif}")
    imageio.mimsave(output_gif, frames, fps=30)
    print("Shot 1 Complete!\n")

def render_shot2_assembled_orbit(output_webm, output_gif, num_frames=300):
    """Renders Shot 2: Assembled Sentinel Nanopore Reader 360 Orbit."""
    print("Generating Shot 2: Assembled Sentinel Device 360 Orbit...")
    components = build_assembled_device_components()
    plotter = setup_plotter()

    for mesh, mat in components:
        if mesh is not None:
            plotter.add_mesh(
                mesh,
                color=mat['color'],
                opacity=mat['opacity'],
                metallic=mat['metallic'],
                roughness=mat['roughness'],
                smooth_shading=mat['smooth_shading']
            )

    focal_center = np.array([0.0, 0.0, 45.0])
    radius = 240.0
    cam_z = 110.0

    frames = []
    for frame in range(num_frames):
        t = frame / (num_frames - 1)
        angle = 2 * math.pi * t + math.pi / 4

        cam_x = focal_center[0] + radius * math.cos(angle)
        cam_y = focal_center[1] + radius * math.sin(angle)

        camera_pos = [cam_x, cam_y, cam_z]
        view_up = [0, 0, 1]

        plotter.camera_position = [camera_pos, focal_center, view_up]
        plotter.render()

        img = plotter.screenshot(return_img=True)
        frames.append(img)

        if frame % 60 == 0:
            print(f"  Shot 2: Processed frame {frame}/{num_frames}")

    plotter.close()

    print(f"Saving Shot 2 WebM: {output_webm}")
    imageio.mimsave(output_webm, frames, fps=30, codec='vp9')
    print(f"Saving Shot 2 GIF: {output_gif}")
    imageio.mimsave(output_gif, frames, fps=30)
    print("Shot 2 Complete!\n")

def main():
    os.makedirs("renders", exist_ok=True)

    shot1_webm = "renders/nanopore_exploded_flythrough.webm"
    shot1_gif = "renders/nanopore_exploded_flythrough.gif"

    shot2_webm = "renders/sentinel_device_assembled_orbit.webm"
    shot2_gif = "renders/sentinel_device_assembled_orbit.gif"

    render_shot1_exploded_flythrough(shot1_webm, shot1_gif, num_frames=300)
    render_shot2_assembled_orbit(shot2_webm, shot2_gif, num_frames=300)

    print("All renders completed successfully!")

if __name__ == "__main__":
    main()
