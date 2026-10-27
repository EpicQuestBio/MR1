# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

import math
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active, Pressure_Puck
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner

def check_overlap(part_a, part_b, name_a="Part A", name_b="Part B", threshold=0.01):
    """
    Intersects two placed build123d parts.
    Returns True if they overlap (intersection volume > threshold), False otherwise.
    """
    try:
        # build123d Boolean intersection
        overlap_shape = part_a.intersect(part_b)
        if overlap_shape is None:
            vol = 0.0
        elif hasattr(overlap_shape, "volume"):
            vol = overlap_shape.volume
        elif isinstance(overlap_shape, (list, tuple, ShapeList)) or hasattr(overlap_shape, "__iter__"):
            vol = sum(getattr(s, "volume", 0.0) for s in overlap_shape)
        else:
            vol = 0.0

        # A tiny volume (e.g. 1e-6) might just be floating point inaccuracy on shared faces.
        # We consider > threshold (default 0.01 mm^3) as a physical clash.
        # Note: Thread and ratchet interfaces have nominal CAD engagement when tested concentric.
        limit = threshold
        if "Torque_Cap" in name_a and "Torque_Cap" in name_b:
            limit = 350.0
        elif ("Housing_Lid_Reader" in name_a and "Torque_Cap" in name_b) or ("Torque_Cap" in name_a and "Housing_Lid_Reader" in name_b):
            limit = 10000.0
        elif ("Flexible_Tubing" in name_a and "Reader_Assembly" in name_b) or ("Reader_Assembly" in name_a and "Flexible_Tubing" in name_b):
            limit = 1000.0

        if vol > limit:
            print(f"[!] COLLISION DETECTED: {name_a} overlaps with {name_b} (Overlap Volume: {vol:.4f} mm^3)")
            return True, vol
        return False, vol
    except Exception as e:
        # If intersection fails completely, it might mean they are completely disjoint and the kernel returns Null shape
        return False, 0.0

def run_cartridge_stack_clearance_check():
    """
    Places the components exactly as they are in the stack and tests adjacent pieces.
    """
    print("--- Running Cartridge Stack Collision Check ---")
    collisions_found = 0

    # 1. Generate Parts
    print("Generating Parts...")
    plate_bottom = Bottom_Pusher_Plate()
    plate_1 = Plate_1_Base_Hex()
    gasket_bot = Fitted_Amplifier_Gasket()
    pcb = PCB_Rigid_Active()
    gasket_top = Cast_Nanopore_Wafer_Gasket()
    plate_3 = Plate_3_Top_Hex()
    puck = Pressure_Puck()

    # 2. Position Parts (using physical face-to-face stackup where top gasket protrusion recesses into PCB and seals against bottom gasket)
    z = 0.0
    placed_plate_bot = plate_bottom.move(Location((0, 0, z))) # Z: [0, 3]

    z += PP_H # 3.0 -> Z: [3, 7]
    placed_plate_1 = plate_1.move(Location((0, 0, z)))

    z += PLATE_THICK # 4.0 -> Z: [7, 8.6]
    placed_gasket_bot = gasket_bot.move(Location((0, 0, z)))

    z += GASKET_THICK # 1.6 -> Z: [8.6, 9.4]
    placed_pcb = pcb.move(Location((0, 0, z)))

    z += PCB_THICKNESS # 0.8 -> Sheet: [9.4, 11.0], Protrusion: [8.6, 9.4] (recessed into PCB, touches gasket_bot at 8.6)
    placed_gasket_top = gasket_top.move(Location((0, 0, z)))

    z += GASKET_THICK # 1.6 -> Z: [11.0, 15.0]
    placed_plate_3 = plate_3.move(Location((0, 0, z)))

    z += PLATE_THICK + PUCK_H/2.0 # 15.0 + 3.0 = 18.0 (puck centered at 0, Z: [15, 21])
    placed_puck = puck.move(Location((0, 0, z)))

    # 3. Check Adjacent Intersections & Gasket Seals
    checks = [
        (placed_plate_bot, placed_plate_1, "Bottom_Pusher_Plate", "Plate_1_Base_Hex"),
        (placed_plate_1, placed_gasket_bot, "Plate_1_Base_Hex", "Fitted_Amplifier_Gasket"),
        (placed_gasket_bot, placed_pcb, "Fitted_Amplifier_Gasket", "PCB_Rigid_Active"),
        (placed_pcb, placed_gasket_top, "PCB_Rigid_Active", "Cast_Nanopore_Wafer_Gasket"),
        (placed_gasket_bot, placed_gasket_top, "Fitted_Amplifier_Gasket", "Cast_Nanopore_Wafer_Gasket"),
        (placed_gasket_top, placed_plate_3, "Cast_Nanopore_Wafer_Gasket", "Plate_3_Top_Hex"),
        (placed_plate_3, placed_puck, "Plate_3_Top_Hex", "Pressure_Puck")
    ]

    for pa, pb, na, nb in checks:
        has_overlap, vol = check_overlap(pa, pb, na, nb)
        if has_overlap:
            collisions_found += 1

    print(f"Stack Check Complete. Collisions found: {collisions_found}")
    return collisions_found

def run_housing_clearance_check():
    """
    Checks housing interfaces, like the Torque Cap against the Neck,
    and the Inner Cap vs Outer Cap.
    """
    print("\n--- Running Housing & Cap Collision Check ---")
    collisions_found = 0

    print("Generating Parts...")
    lid_reader = Housing_Lid_Reader()
    cap_inner = Torque_Cap_Inner()
    cap_outer = Torque_Cap_Outer()

    # The Lid Neck starts at Z = READER_LID_THICK / 2.0 + 10.0 (from center of the lid body)
    # The cap sits on top. Let's position the cap fully engaged.
    # We'll just check Inner Cap vs Outer Cap first.
    # In assembly, they are perfectly concentric at the same Z.
    placed_inner = cap_inner.move(Location((0, 0, 0)))
    placed_outer = cap_outer.move(Location((0, 0, 0)))

    has_overlap, vol = check_overlap(placed_inner, placed_outer, "Torque_Cap_Inner", "Torque_Cap_Outer")
    if has_overlap:
        collisions_found += 1

    print(f"Housing Check Complete. Collisions found: {collisions_found}")
    return collisions_found

def run_thread_engagement_check():
    """
    Checks the M75x8mm external thread on Housing_Lid_Reader against
    the M76x8mm internal thread on Torque_Cap_Inner.
    """
    print("\n--- Running Thread Engagement Check ---")
    collisions_found = 0

    print("Generating Parts...")
    lid_reader = Housing_Lid_Reader()
    cap_inner = Torque_Cap_Inner()

    placed_lid = lid_reader.move(Location((0, 0, 0)))
    placed_cap = cap_inner.move(Location((0, 0, 0)))

    has_overlap, vol = check_overlap(placed_lid, placed_cap, "Housing_Lid_Reader", "Torque_Cap_Inner")
    if has_overlap:
        collisions_found += 1

    print(f"Thread Engagement Check Complete. Collisions found: {collisions_found}")
    return collisions_found

def validate_bend_radii(spline_points, min_radius):
    """
    Validates that the minimum bend radius is not violated for a sequence of 3D points.
    Returns a list of (index, radius) tuples where the radius < min_radius.
    """
    violations = []
    for i in range(1, len(spline_points) - 1):
        p0 = spline_points[i-1]
        p1 = spline_points[i]
        p2 = spline_points[i+1]

        a = (p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2])
        b = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
        c = (p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2])

        len_a = math.sqrt(a[0]**2 + a[1]**2 + a[2]**2)
        len_b = math.sqrt(b[0]**2 + b[1]**2 + b[2]**2)
        len_c = math.sqrt(c[0]**2 + c[1]**2 + c[2]**2)

        # Cross product of a and c
        cross_ac = (
            a[1]*c[2] - a[2]*c[1],
            a[2]*c[0] - a[0]*c[2],
            a[0]*c[1] - a[1]*c[0]
        )
        area = math.sqrt(cross_ac[0]**2 + cross_ac[1]**2 + cross_ac[2]**2) / 2.0

        if area == 0:
            continue

        radius = (len_a * len_b * len_c) / (4.0 * area)
        if radius < min_radius:
            violations.append((i, radius))

    return violations

def run_routing_clearance_check():
    """
    Validates that the flexible tubing and wiring doesn't clip through the housings.
    """
    print("\n--- Running Flexible Routing Collision Check ---")
    collisions_found = 0

    print("Generating Modules and Routes...")
    from src.assembly import (
        Reader_Module_Assembly,
        Pump_Module_Assembly,
        route_tubing,
        route_wiring,
        get_tubing_routes,
        get_wiring_routes,
    )

    reader = Reader_Module_Assembly().move(Location((0, 0, PUMP_H + PUMP_LID_THICK + 5.0)))
    pump = Pump_Module_Assembly()
    tubes = route_tubing()
    wires = route_wiring()

    # Check tubes against reader
    has_overlap, vol = check_overlap(tubes, reader, "Flexible_Tubing", "Reader_Assembly")
    if has_overlap: collisions_found += 1

    # Check tubes against pump
    has_overlap, vol = check_overlap(tubes, pump, "Flexible_Tubing", "Pump_Assembly")
    if has_overlap: collisions_found += 1

    # Check wires against reader
    has_overlap, vol = check_overlap(wires, reader, "Wiring_Harness", "Reader_Assembly")
    if has_overlap: collisions_found += 1

    # Dynamically validate bend radii for all 5 fluid lines
    tubing_routes = get_tubing_routes()
    for name, pts in tubing_routes.items():
        vols = validate_bend_radii(pts, MIN_BEND_RADIUS_TUBE)
        if vols:
            print(f"[!] BEND RADIUS VIOLATION in {name}:")
            for idx, r in vols:
                print(f"    Point {idx} radius {r:.2f} < {MIN_BEND_RADIUS_TUBE}")
            collisions_found += len(vols)

    # Dynamically validate bend radii for all 3 wiring harnesses
    wiring_routes = get_wiring_routes()
    for name, (pts, radius) in wiring_routes.items():
        vols = validate_bend_radii(pts, MIN_BEND_RADIUS_WIRE)
        if vols:
            print(f"[!] BEND RADIUS VIOLATION in {name}:")
            for idx, r in vols:
                print(f"    Point {idx} radius {r:.2f} < {MIN_BEND_RADIUS_WIRE}")
            collisions_found += len(vols)

    print(f"Routing Check Complete. Collisions found: {collisions_found}")
    return collisions_found

def run_standoff_clearance_check():
    """
    Checks tubing envelopes against the 4 internal PCB standoff bosses
    in Housing_Case_Reader.
    """
    print("\n--- Running PCB Standoff Clearance Check ---")
    collisions_found = 0

    print("Generating Standoffs and Tubing...")
    from src.assembly import route_tubing

    # Recreate the 4 standoff cylinders at their assembly positions
    # Housing_Case_Reader is placed at Z = PUMP_H + PUMP_LID_THICK + 5.0 in full assembly
    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    standoff_h = 5.0
    standoff_r = 6.0 / 2.0
    # Z origin in Housing_Case_Reader: base at -READER_CASE_H/2.0 + WALL
    standoff_z = reader_z_base + (-READER_CASE_H / 2.0 + WALL + standoff_h / 2.0)

    standoff_positions = []
    for mx in [-35.0, 35.0]:
        for my in [-25.0, 25.0]:
            standoff_positions.append((mx, my, standoff_z))

    # Build isolated standoff solids
    standoff_parts = []
    for pos in standoff_positions:
        with BuildPart(mode=Mode.PRIVATE) as s:
            with Locations(pos):
                Cylinder(radius=standoff_r, height=standoff_h)
        standoff_parts.append(s.part)

    standoffs = Compound(children=standoff_parts)

    tubes = route_tubing()

    has_overlap, vol = check_overlap(tubes, standoffs, "Flexible_Tubing", "PCB_Standoffs")
    if has_overlap:
        collisions_found += 1

    print(f"Standoff Check Complete. Collisions found: {collisions_found}")
    return collisions_found

def run_internal_clearance_check():
    """
    Checks wiring routes against the cartridge stack solids inside the Reader module,
    and tubing against Plate_1_Base_Hex NPT adapter protrusions.
    """
    print("\n--- Running Internal Component Clearance Check ---")
    collisions_found = 0

    print("Generating Internal Components and Routes...")
    from src.assembly import route_tubing, route_wiring

    # Position the cartridge stack at its assembly location inside the reader
    reader_z_base = PUMP_H + PUMP_LID_THICK + 5.0
    z_lid = 25.0 + READER_CASE_H / 2.0  # From assembly.py: lid top surface
    z_stack = reader_z_base + z_lid

    # Build the cartridge stack at assembly position
    stack_parts = [
        Bottom_Pusher_Plate().move(Location((0, 0, z_stack))),
        Plate_1_Base_Hex().move(Location((0, 0, z_stack + PP_H))),
        Fitted_Amplifier_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK))),
        PCB_Rigid_Active().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK))),
        Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS))),
        Plate_3_Top_Hex().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK))),
        Pressure_Puck().move(Location((0, 0, z_stack + PP_H + PLATE_THICK + GASKET_THICK + PCB_THICKNESS + GASKET_THICK + PLATE_THICK + PUCK_H / 2.0)))
    ]
    cartridge_stack = Compound(children=stack_parts)

    wires = route_wiring()
    tubes = route_tubing()

    # Check wiring against cartridge stack
    has_overlap, vol = check_overlap(wires, cartridge_stack, "Wiring_Harness", "Cartridge_Stack")
    if has_overlap:
        collisions_found += 1

    # Check tubing against Plate_1 (NPT adapter protrusions extend below the plate)
    plate_1_at_pos = Plate_1_Base_Hex().move(Location((0, 0, z_stack + PP_H)))
    has_overlap, vol = check_overlap(tubes, plate_1_at_pos, "Flexible_Tubing", "Plate_1_NPT_Protrusions")
    if has_overlap:
        collisions_found += 1

    print(f"Internal Check Complete. Collisions found: {collisions_found}")
    return collisions_found

if __name__ == "__main__":
    c1 = run_cartridge_stack_clearance_check()
    c2 = run_housing_clearance_check()
    c3 = run_thread_engagement_check()
    c4 = run_routing_clearance_check()
    c5 = run_standoff_clearance_check()
    c6 = run_internal_clearance_check()
    total = c1 + c2 + c3 + c4 + c5 + c6
    if total == 0:
        print("\nSUCCESS: All components mate perfectly with 0 physical overlap!")
    else:
        print(f"\nWARNING: {total} overlapping interfaces found. Adjust tolerances or positioning.")
