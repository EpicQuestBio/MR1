# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

import unittest
from build123d import *
from src.constants import *
from src.nanopore_wafer_mold import Nanopore_Wafer_Mold_Left, Nanopore_Wafer_Mold_Right
from src.cartridge import PCB_Rigid_Active, Cast_Nanopore_Wafer_Gasket, Fitted_Amplifier_Gasket, Bottom_Pusher_Plate, Plate_1_Base_Hex, Plate_3_Top_Hex, Pressure_Puck, Nanopore_Wafer_Silicon
from src.adapters import Threaded_Luer_Adapter, Elbow_Adapter
from src.housing import Housing_Pump_Case, Housing_Pump_Lid, Housing_Case_Reader, Housing_Lid_Reader
from src.torque_cap import Torque_Cap_Outer, Torque_Cap_Inner
from src.connectors import JST_XH_2_Pin_Header, JST_XH_2_Pin_Plug, USB_C_Panel_Mount, Luer_Bulkhead_Panel_Mount
from src.collision_check import (
    run_cartridge_stack_clearance_check,
    run_housing_clearance_check,
    run_thread_engagement_check,
    run_routing_clearance_check,
    run_standoff_clearance_check,
    run_internal_clearance_check,
)

class TestGeometryGeneration(unittest.TestCase):
    def check_part_validity(self, part, name):
        self.assertIsNotNone(part, f"{name} failed to generate.")
        self.assertTrue(part.is_valid, f"{name} is not a valid BREP solid.")
        self.assertGreater(part.volume, 0, f"{name} has zero volume.")

    def test_molds(self):
        self.check_part_validity(Nanopore_Wafer_Mold_Left(is_nanopore=True), "Mold Left (Nanopore)")
        self.check_part_validity(Nanopore_Wafer_Mold_Right(is_nanopore=True), "Mold Right (Nanopore)")
        self.check_part_validity(Nanopore_Wafer_Mold_Left(is_nanopore=False), "Mold Left (Amplifier)")
        self.check_part_validity(Nanopore_Wafer_Mold_Right(is_nanopore=False), "Mold Right (Amplifier)")

    def test_cartridge_stack(self):
        self.check_part_validity(PCB_Rigid_Active(), "PCB Active")
        self.check_part_validity(Nanopore_Wafer_Silicon(), "Silicon Nanopore Wafer")
        self.check_part_validity(Cast_Nanopore_Wafer_Gasket(), "Top Gasket")
        self.check_part_validity(Fitted_Amplifier_Gasket(), "Bottom Gasket")
        self.check_part_validity(Bottom_Pusher_Plate(), "Bottom Plate")
        self.check_part_validity(Plate_1_Base_Hex(), "Plate 1 Base")
        self.check_part_validity(Plate_3_Top_Hex(), "Plate 3 Top")
        self.check_part_validity(Pressure_Puck(), "Pressure Puck")

    def test_housings(self):
        self.check_part_validity(Housing_Pump_Case(), "Housing Pump Case")
        self.check_part_validity(Housing_Pump_Lid(), "Housing Pump Lid")
        self.check_part_validity(Housing_Case_Reader(), "Housing Reader Case")
        self.check_part_validity(Housing_Lid_Reader(), "Housing Reader Lid")

    def test_adapters_and_caps(self):
        self.check_part_validity(Threaded_Luer_Adapter(), "Threaded Luer")
        self.check_part_validity(Threaded_Luer_Adapter(render_threads=True), "Threaded Luer (Threaded)")
        self.check_part_validity(Elbow_Adapter(), "Elbow Adapter")
        self.check_part_validity(Torque_Cap_Outer(), "Torque Cap Outer")
        self.check_part_validity(Torque_Cap_Inner(), "Torque Cap Inner")

    def test_connectors(self):
        self.check_part_validity(JST_XH_2_Pin_Header(), "JST XH 2-Pin Header")
        self.check_part_validity(JST_XH_2_Pin_Plug(), "JST XH 2-Pin Plug")
        self.check_part_validity(USB_C_Panel_Mount(), "USB-C Panel Mount")
        self.check_part_validity(Luer_Bulkhead_Panel_Mount(), "Luer Bulkhead Panel Mount")

    def test_assembly_collisions(self):
        c1 = run_cartridge_stack_clearance_check()
        self.assertEqual(c1, 0, "Collisions detected in Cartridge Stack!")

        c2 = run_housing_clearance_check()
        self.assertEqual(c2, 0, "Collisions detected in Housing & Caps!")

        c3 = run_thread_engagement_check()
        self.assertEqual(c3, 0, "Collisions detected in Thread Engagement!")

        c4 = run_standoff_clearance_check()
        self.assertEqual(c4, 0, "Collisions detected in PCB Standoffs!")

        c5 = run_internal_clearance_check()
        self.assertEqual(c5, 0, "Collisions detected in Internal Clearances!")

    def test_routing_collisions(self):
        c6 = run_routing_clearance_check()
        self.assertEqual(c6, 0, "Collisions detected in Flexible Routing vs Housings!")

if __name__ == "__main__":
    unittest.main()
