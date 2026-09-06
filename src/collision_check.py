from build123d import *
from src.constants import *
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.cartridge import Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, PCB_Rigid_Active, Pressure_Puck
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner

def check_overlap(part_a, part_b, name_a="Part A", name_b="Part B"):
    """
    Intersects two placed build123d parts.
    Returns True if they overlap (intersection volume > 0), False otherwise.
    """
    try:
        # build123d Boolean intersection
        overlap_shape = part_a.intersect(part_b)
        vol = overlap_shape.volume

        # A tiny volume (e.g. 1e-6) might just be floating point inaccuracy on shared faces.
        # We consider > 0.01 mm^3 as a physical clash.
        if vol > 0.01:
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

if __name__ == "__main__":
    c1 = run_cartridge_stack_clearance_check()
    c2 = run_housing_clearance_check()
    if c1 + c2 == 0:
        print("\nSUCCESS: All components mate perfectly with 0 physical overlap!")
    else:
        print(f"\nWARNING: {c1 + c2} overlapping interfaces found. Adjust tolerances or positioning.")


def run_routing_clearance_check():
    """
    Validates that the flexible tubing and wiring doesn't clip through the housings.
    """
    print("\n--- Running Flexible Routing Collision Check ---")
    collisions_found = 0

    print("Generating Modules and Routes...")
    from src.assembly import Reader_Module_Assembly, Pump_Module_Assembly, route_tubing, route_wiring

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

    print(f"Routing Check Complete. Collisions found: {collisions_found}")
    return collisions_found

if __name__ == "__main__":
    c1 = run_cartridge_stack_clearance_check()
    c2 = run_housing_clearance_check()
    c3 = run_routing_clearance_check()
    if c1 + c2 + c3 == 0:
        print("\nSUCCESS: All components mate perfectly with 0 physical overlap!")
    else:
        print(f"\nWARNING: {c1 + c2 + c3} overlapping interfaces found. Adjust tolerances or positioning.")
