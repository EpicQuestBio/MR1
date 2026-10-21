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
    PCB_Main_Reader,
    Pressure_Puck,
    Nanopore_Wafer_Silicon
)
from simulations.nanopore_electrokinetics import NanoporeElectrokinetics
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
    },
    'gold_metal': {
        'color': '#FFD700',
        'opacity': 1.0,
        'metallic': 0.95,
        'roughness': 0.15,
        'smooth_shading': True
    },
    'chip_black': {
        'color': '#1C1C1C',
        'opacity': 1.0,
        'metallic': 0.2,
        'roughness': 0.4,
        'smooth_shading': True
    },
    'solder_tin': {
        'color': '#D0D5DD',
        'opacity': 1.0,
        'metallic': 0.85,
        'roughness': 0.25,
        'smooth_shading': True
    },
    'sin_membrane': {
        'color': '#3498DB',
        'opacity': 0.8,
        'metallic': 0.6,
        'roughness': 0.15,
        'smooth_shading': True
    },
    'lipid_membrane': {
        'color': '#E67E22',
        'opacity': 0.75,
        'metallic': 0.1,
        'roughness': 0.5,
        'smooth_shading': True
    }
}

# --- 3D PCB Component Models ---

def create_lmp7721_ic_mesh():
    """Creates LMP7721 SOIC-8 low-leakage amplifier IC package."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Main SOIC-8 body: 4.9 x 3.9 x 1.5 mm
        Box(4.9, 3.9, 1.5)
        # Pins (8 pins total, 4 on each long side)
        for side in [-1, 1]:
            for x in [-1.905, -0.635, 0.635, 1.905]:
                with Locations((x, side * 2.4, -0.4)):
                    Box(0.4, 1.0, 0.3)
    return shape_to_pv_mesh(p.part)

def create_pogo_pin_mesh():
    """Creates Mill-Max gold pogo pin connector unit."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Cylinder(radius=0.45, height=3.0)
        with Locations((0, 0, 2.0)):
            Cylinder(radius=0.3, height=2.0)
    return shape_to_pv_mesh(p.part)

def create_usbc_receptacle_mesh():
    """Creates USB-C panel mount / PCB receptacle."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(8.9, 7.3, 3.2)
        with Locations((0, 0, 0)):
            Box(8.3, 6.7, 2.6, mode=Mode.SUBTRACT)
        Box(6.5, 5.0, 0.7)
    return shape_to_pv_mesh(p.part)

def create_smt_passive_mesh():
    """Creates 0805 SMT chip resistor / capacitor body."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(2.0, 1.25, 0.9)
    return shape_to_pv_mesh(p.part)

# --- Multi-Scale Nanopore Substrate Models ---

def create_silicon_die_500um_mesh():
    """500 um thick Silicon Die (4.0 x 4.0 x 0.5 mm) with central thinned window relief."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Box(4.0, 4.0, 0.5)
        # Pyramidal / tapered etch pit relief leading down to membrane window
        with Locations((0, 0, -0.1)):
            Cone(bottom_radius=0.8, top_radius=0.05, height=0.4, mode=Mode.SUBTRACT)
    return shape_to_pv_mesh(p.part)

def create_thinned_membrane_200nm_mesh():
    """10x10 um x 200 nm Silicon Nitride (SiNx) thinned membrane window with 100 nm central nanopore."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Scale magnified for PyVista visibility: 1.0 x 1.0 x 0.05 mm mesh representation
        Box(1.2, 1.2, 0.06)
        Cylinder(radius=0.15, height=0.1, mode=Mode.SUBTRACT)
    return shape_to_pv_mesh(p.part)

def create_pore_100um_mesh():
    """100 um micro-aperture substrate model."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        Cylinder(radius=2.0, height=0.2)
        Cylinder(radius=0.6, height=0.4, mode=Mode.SUBTRACT)
    return shape_to_pv_mesh(p.part)

def create_pore_1nm_mesh():
    """1 nm sub-nanometer / biological channel substrate model embedded in lipid membrane."""
    with BuildPart(mode=Mode.PRIVATE) as p:
        # Lipid bilayer disk
        Cylinder(radius=1.5, height=0.1)
        # Alpha-hemolysin / MspA barrel pore geometry
        Cylinder(radius=0.35, height=0.25)
        Cylinder(radius=0.08, height=0.4, mode=Mode.SUBTRACT)
    return shape_to_pv_mesh(p.part)

def create_nanopore_wafer_mesh():
    """Generates the nanopore wafer silicon mesh from the canonical source model."""
    wafer = Nanopore_Wafer_Silicon()
    return shape_to_pv_mesh(wafer)

def ease_out_cubic(x):
    """Cubic easing function for smooth deceleration."""
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3

def transform_mesh(mesh, final_pos, explode_offset, final_rot=0.0, explode_rot=180.0, progress=1.0):
    """Interpolates mesh position and rotation from exploded state to assembled state."""
    if mesh is None:
        return None
    m = mesh.copy()
    e = 1.0 - ease_out_cubic(progress)

    pos = np.array(final_pos) + np.array(explode_offset) * e
    rot = final_rot + explode_rot * e

    if abs(rot) > 1e-3:
        m.rotate_z(rot, inplace=True)
    m.translate(pos, inplace=True)
    return m

def build_reverse_explosion_scene(progress):
    """
    Generates all MR1 system components (housing, stack, tubing, wiring, and PCB components)
    interpolated at assembly state progress t in [0.0, 1.0].
    """
    components = []

    # Pre-mesh components
    pump_case_m = shape_to_pv_mesh(Housing_Pump_Case())
    pump_lid_m = shape_to_pv_mesh(Housing_Pump_Lid())
    reader_case_m = shape_to_pv_mesh(Housing_Case_Reader())
    reader_lid_m = shape_to_pv_mesh(Housing_Lid_Reader())
    cap_inner_m = shape_to_pv_mesh(Torque_Cap_Inner())
    cap_outer_m = shape_to_pv_mesh(Torque_Cap_Outer())

    bpp_m = shape_to_pv_mesh(Bottom_Pusher_Plate())
    p1_m = shape_to_pv_mesh(Plate_1_Base_Hex())
    g1_m = shape_to_pv_mesh(Fitted_Amplifier_Gasket())
    pcb_amp_m = shape_to_pv_mesh(PCB_Rigid_Active())
    pcb_reader_m = shape_to_pv_mesh(PCB_Main_Reader())
    g2_m = shape_to_pv_mesh(Cast_Nanopore_Wafer_Gasket())
    p3_m = shape_to_pv_mesh(Plate_3_Top_Hex())
    puck_m = shape_to_pv_mesh(Pressure_Puck())
    wafer_m = create_nanopore_wafer_mesh()

    # PCB components
    ic_m = create_lmp7721_ic_mesh()
    pogo_m = create_pogo_pin_mesh()
    usbc_m = create_usbc_receptacle_mesh()
    smt_m = create_smt_passive_mesh()

    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    z_cap = reader_z_base + READER_LID_THICK + READER_LID_THICK/2.0 + NECK_H - 10.0
    z_stack = reader_z_base + READER_LID_THICK/2.0 + 10.0

    # 1. Housing Modules
    components.append((transform_mesh(pump_case_m, (0, 0, 0), (0, 0, -180), explode_rot=90, progress=progress), MATERIALS['housing_dark']))
    components.append((transform_mesh(pump_lid_m, (0, 0, PUMP_H/2.0 + PUMP_LID_THICK/2.0), (0, 0, -100), explode_rot=-90, progress=progress), MATERIALS['housing_dark']))
    components.append((transform_mesh(reader_case_m, (0, 0, reader_z_base), (0, 0, -40), explode_rot=45, progress=progress), MATERIALS['housing_dark']))
    components.append((transform_mesh(reader_lid_m, (0, 0, reader_z_base + READER_LID_THICK), (0, 0, 160), explode_rot=-45, progress=progress), MATERIALS['housing_dark']))
    components.append((transform_mesh(cap_inner_m, (0, 0, z_cap), (0, 0, 220), explode_rot=360, progress=progress), MATERIALS['housing_dark']))
    components.append((transform_mesh(cap_outer_m, (0, 0, z_cap), (0, 0, 240), explode_rot=-360, progress=progress), MATERIALS['cap_blue']))

    # 2. Main Reader PCB & SMT Components
    components.append((transform_mesh(pcb_reader_m, (0, 0, reader_z_base - 5.0), (0, -120, -50), explode_rot=180, progress=progress), MATERIALS['pcb_fr4_green']))
    components.append((transform_mesh(usbc_m, (-15.0, 25.0, reader_z_base - 3.5), (-120, 60, 20), explode_rot=90, progress=progress), MATERIALS['solder_tin']))

    # 3. Cartridge Stack
    components.append((transform_mesh(bpp_m, (0, 0, z_stack), (-100, -80, 40), explode_rot=120, progress=progress), MATERIALS['tpu_black']))
    components.append((transform_mesh(p1_m, (0, 0, z_stack + PP_H + PLATE_THICK/2.0), (120, -60, 60), explode_rot=-120, progress=progress), MATERIALS['polypropylene_grey']))
    components.append((transform_mesh(g1_m, (0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK/2.0), (-120, 60, 80), explode_rot=180, progress=progress), MATERIALS['silicone_translucent']))

    # Amplifier Interposer PCB & ICs/Pogo pins
    pcb_z = z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS/2.0
    components.append((transform_mesh(pcb_amp_m, (0, 0, pcb_z), (140, 0, 100), explode_rot=-180, progress=progress), MATERIALS['pcb_fr4_green']))
    components.append((transform_mesh(ic_m, (0, -5.0, pcb_z + 1.2), (180, 40, 120), explode_rot=270, progress=progress), MATERIALS['chip_black']))

    # 12 Mill-Max Gold Pogo Pins flying into place
    for x in [-11.0, -9.0, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0, 9.0, 11.0]:
        components.append((transform_mesh(pogo_m, (x, POGO_Y, pcb_z - 2.0), (x * 12, 100, 150), explode_rot=360, progress=progress), MATERIALS['gold_metal']))

    components.append((transform_mesh(g2_m, (0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK/2.0), (-100, -100, 140), explode_rot=180, progress=progress), MATERIALS['silicone_translucent']))
    components.append((transform_mesh(p3_m, (0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK/2.0), (100, 100, 160), explode_rot=-180, progress=progress), MATERIALS['polypropylene_grey']))
    components.append((transform_mesh(puck_m, (0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK + PUCK_H/2.0), (0, 0, 200), explode_rot=360, progress=progress), MATERIALS['tpu_black']))

    # Silicon Nanopore Wafer
    components.append((transform_mesh(wafer_m, (0, 0, pcb_z + 0.4), (0, 0, 250), explode_rot=720, progress=progress), MATERIALS['silicon_wafer']))

    # 4. Routing Harnesses (appear as stack finishes assembling, progress > 0.6)
    if progress > 0.6:
        tubes_m = shape_to_pv_mesh(route_tubing())
        wires_m = shape_to_pv_mesh(route_wiring())
        alpha_route = (progress - 0.6) / 0.4
        components.append((transform_mesh(tubes_m, (0, 0, 0), (0, 0, 0), progress=alpha_route), MATERIALS['tubing_clear']))
        components.append((transform_mesh(wires_m, (0, 0, 0), (0, 0, 0), progress=alpha_route), MATERIALS['wiring_copper']))

    return components

def build_assembled_device_components():
    """Builds fully assembled MR1 Nanopore Reader device for Shot 2."""
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

import matplotlib.pyplot as plt
from PIL import Image

def generate_simulated_signal_trace(pore_diam_nm, num_pts=200):
    """Generates time and current vectors with translocation events for given pore scale."""
    sim = NanoporeElectrokinetics(pore_diameter_nm=pore_diam_nm)
    base = sim.calculate_baseline_current(180.0)
    i0 = base["i_baseline_pa"]

    time_ms = np.linspace(0, 10, num_pts)
    # White noise ~ 2%
    noise = np.random.normal(0, i0 * 0.02, num_pts)
    current = i0 + noise

    unit = "pA"
    if abs(i0) >= 1000.0:
        current /= 1000.0
        i0 /= 1000.0
        unit = "nA"
    if abs(i0) >= 1000.0:
        current /= 1000.0
        i0 /= 1000.0
        unit = "uA"

    # Add translocation blockade pulses
    if pore_diam_nm <= 200.0:
        block = sim.calculate_dna_blockade(180.0, "dsDNA" if pore_diam_nm > 2.0 else "ssDNA")
        delta_i = block["blockade_depth_pa"]
        if unit == "nA":
            delta_i /= 1000.0
        elif unit == "uA":
            delta_i /= 1e6

        # Inject 2 translocation events
        current[40:55] -= delta_i
        current[120:140] -= delta_i

    return time_ms, current, unit, i0

def draw_signal_overlay(image_array, title, pore_diam_nm):
    """Draws a clean oscilloscope HUD overlay on the PyVista screenshot frame."""
    time_ms, current_vals, unit, i0 = generate_simulated_signal_trace(pore_diam_nm)

    fig, ax = plt.subplots(figsize=(3.8, 2.0), dpi=100)
    fig.patch.set_facecolor('#0B0E11')
    fig.patch.set_alpha(0.85)

    ax.set_facecolor('#12161A')
    ax.plot(time_ms, current_vals, color='#00FFCC', linewidth=1.5)
    ax.set_title(title, color='#FFFFFF', fontsize=8, fontweight='bold', pad=3)
    ax.set_xlabel("Time (ms)", color='#8A9BA8', fontsize=6)
    ax.set_ylabel(f"Current ({unit})", color='#8A9BA8', fontsize=6)
    ax.tick_params(colors='#8A9BA8', labelsize=5)
    for spine in ax.spines.values():
        spine.set_color('#2A323D')
    ax.grid(True, color='#1E2631', linestyle='--', linewidth=0.5)

    info_text = f"Pore: {pore_diam_nm:g} nm | Baseline: {i0:.1f} {unit}"
    ax.text(0.04, 0.08, info_text, transform=ax.transAxes, color='#FFD700', fontsize=6, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#12161A', edgecolor='#2A323D', alpha=0.9))

    plt.tight_layout()

    fig.canvas.draw()
    rgba_buf = fig.canvas.buffer_rgba()
    overlay_img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), rgba_buf, "raw", "RGBA", 0, 1)
    plt.close(fig)

    base_img = Image.fromarray(image_array)
    w_base, h_base = base_img.size
    w_over, h_over = overlay_img.size

    pos = (w_base - w_over - 20, h_base - h_over - 20)
    base_img.paste(overlay_img, pos, overlay_img)
    return np.array(base_img)

def render_shot1_reverse_explosion(output_webm, output_gif, num_frames=120):
    """Renders Shot 1: Reverse Explosion where all components fly in and assemble."""
    print("Generating Shot 1: Reverse Explosion Assembly...")
    plotter = setup_plotter()
    frames = []

    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    focal_center = np.array([0.0, 0.0, reader_z_base / 2.0])

    for frame in range(num_frames):
        t = frame / (num_frames - 1)
        plotter.clear()

        # Build reverse explosion components at progress t
        components = build_reverse_explosion_scene(progress=t)
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

        angle = 2 * math.pi * t + math.pi / 4
        radius = 280.0 - 60.0 * t
        cam_z = 140.0 + 20.0 * math.sin(math.pi * t)

        cam_x = focal_center[0] + radius * math.cos(angle)
        cam_y = focal_center[1] + radius * math.sin(angle)

        plotter.camera_position = [[cam_x, cam_y, cam_z], focal_center, [0, 0, 1]]
        plotter.render()

        img = plotter.screenshot(return_img=True)
        frames.append(img)

        if frame % 30 == 0:
            print(f"  Shot 1: Frame {frame}/{num_frames}")

    plotter.close()

    imageio.mimsave(output_webm, frames, fps=30, codec='vp9')
    imageio.mimsave(output_gif, frames, fps=30)
    print("Shot 1 Complete!\n")

def render_shot2_nanopore_zoom(output_webm, output_gif, num_frames=120):
    """Renders Shot 2: Deep zoom down to 500 um Silicon Die, 10x10 um Thinned Window & 100 nm Pore."""
    print("Generating Shot 2: Nanopore Zoom (500 um die -> 10x10 um window -> 100 nm pore)...")
    plotter = setup_plotter()
    frames = []

    die_mesh = create_silicon_die_500um_mesh()
    mem_mesh = create_thinned_membrane_200nm_mesh()

    plotter.add_mesh(die_mesh, color=MATERIALS['silicon_wafer']['color'], metallic=0.9, roughness=0.1)
    plotter.add_mesh(mem_mesh, color=MATERIALS['sin_membrane']['color'], opacity=0.85, metallic=0.6)

    focal_point = np.array([0.0, 0.0, 0.0])

    for frame in range(num_frames):
        t = frame / (num_frames - 1)

        # Exponential camera zoom from 15 mm down to 0.8 mm
        dist = 15.0 * (0.05 ** t)
        angle = math.pi / 4 + math.pi * 0.5 * t

        cam_x = focal_point[0] + dist * math.cos(angle)
        cam_y = focal_point[1] + dist * math.sin(angle)
        cam_z = focal_point[2] + dist * 0.7

        plotter.camera_position = [[cam_x, cam_y, cam_z], focal_point, [0, 0, 1]]
        plotter.render()

        img = plotter.screenshot(return_img=True)

        # Add simulated signal HUD overlay for 100 nm solid-state pore
        img_overlay = draw_signal_overlay(img, "100 nm Pore in 200 nm Membrane", pore_diam_nm=100.0)
        frames.append(img_overlay)

        if frame % 30 == 0:
            print(f"  Shot 2: Frame {frame}/{num_frames}")

    plotter.close()

    imageio.mimsave(output_webm, frames, fps=30, codec='vp9')
    imageio.mimsave(output_gif, frames, fps=30)
    print("Shot 2 Complete!\n")

def render_shot3_scale_showcase(output_webm, output_gif, num_frames=120):
    """Renders Shot 3: Pores from 100 um down to 1 nm with representative substrates & signals."""
    print("Generating Shot 3: Scale Showcase (100 um -> 100 nm -> 1 nm)...")
    frames = []

    scales = [
        ("100 um Micro-Aperture", 100000.0, create_pore_100um_mesh(), MATERIALS['polypropylene_grey']),
        ("100 nm Solid-State Pore (SiNx)", 100.0, create_thinned_membrane_200nm_mesh(), MATERIALS['sin_membrane']),
        ("1 nm Biological Channel (Lipid)", 1.0, create_pore_1nm_mesh(), MATERIALS['lipid_membrane'])
    ]

    frames_per_scale = num_frames // len(scales)

    for scale_idx, (title, pore_nm, mesh, mat) in enumerate(scales):
        plotter = setup_plotter()
        plotter.add_mesh(
            mesh,
            color=mat['color'],
            opacity=mat['opacity'],
            metallic=mat['metallic'],
            roughness=mat['roughness'],
            smooth_shading=mat['smooth_shading']
        )

        focal_pt = np.array([0.0, 0.0, 0.0])

        for f in range(frames_per_scale):
            t = f / (frames_per_scale - 1)
            angle = 2 * math.pi * t

            dist = 5.0 if pore_nm > 1000.0 else (2.0 if pore_nm > 10.0 else 1.2)
            cam_x = focal_pt[0] + dist * math.cos(angle)
            cam_y = focal_pt[1] + dist * math.sin(angle)
            cam_z = focal_pt[2] + dist * 0.6

            plotter.camera_position = [[cam_x, cam_y, cam_z], focal_pt, [0, 0, 1]]
            plotter.render()

            img = plotter.screenshot(return_img=True)
            img_overlay = draw_signal_overlay(img, title, pore_diam_nm=pore_nm)
            frames.append(img_overlay)

        plotter.close()
        print(f"  Shot 3: Completed scale {scale_idx + 1}/{len(scales)} ({title})")

    imageio.mimsave(output_webm, frames, fps=30, codec='vp9')
    imageio.mimsave(output_gif, frames, fps=30)
    print("Shot 3 Complete!\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MR1 Photorealistic Fly-Through & Multi-Scale Renderer")
    parser.add_argument("--test", action="store_true", help="Run fast dry-run test (10 frames/shot)")
    parser.add_argument("--frames", type=int, default=120, help="Frames per shot (default: 120)")
    args = parser.parse_args()

    num_frames = 10 if args.test else args.frames

    os.makedirs("renders", exist_ok=True)

    shot1_webm = "renders/nanopore_reverse_explosion.webm"
    shot1_gif = "renders/nanopore_reverse_explosion.gif"

    shot2_webm = "renders/nanopore_wafer_zoom.webm"
    shot2_gif = "renders/nanopore_wafer_zoom.gif"

    shot3_webm = "renders/nanopore_scale_showcase.webm"
    shot3_gif = "renders/nanopore_scale_showcase.gif"

    render_shot1_reverse_explosion(shot1_webm, shot1_gif, num_frames=num_frames)
    render_shot2_nanopore_zoom(shot2_webm, shot2_gif, num_frames=num_frames)
    render_shot3_scale_showcase(shot3_webm, shot3_gif, num_frames=num_frames)

    print("All photorealistic fly-through renders completed successfully!")

if __name__ == "__main__":
    main()
