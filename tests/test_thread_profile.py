import unittest
from build123d import *
from src.housing import Housing_Lid_Reader
from src.torque_cap import Torque_Cap_Inner
from src.adapters import Threaded_Luer_Adapter
from src.common import generate_helical_thread

class TestThreadProfile(unittest.TestCase):
    """Unit tests verifying proper thread profile formation, core shaft connection,
    and lead-in / lead-out tapers at top and bottom.
    """

    def test_thread_generator_bounds_and_validity(self):
        pitch = 8.0
        depth = 4.75
        length = 25.2
        core_radius = 32.5

        # External thread
        ext_thread = generate_helical_thread(
            pitch=pitch,
            depth=depth,
            length=length,
            core_radius=core_radius,
            is_internal=False
        )
        self.assertTrue(ext_thread.is_valid, "External thread should be topologically valid")
        bbox = ext_thread.bounding_box()
        # Thread ridge should stay strictly within Z: 0 to length (with micro-float precision)
        self.assertGreaterEqual(bbox.min.Z, -1e-5, "External thread should not overhang below Z=0")
        self.assertLessEqual(bbox.max.Z, length + 1e-5, "External thread should not overhang above Z=length")

        # Internal thread
        int_thread = generate_helical_thread(
            pitch=pitch,
            depth=depth,
            length=20.2,
            core_radius=37.75,
            is_internal=True
        )
        self.assertTrue(int_thread.is_valid, "Internal thread should be topologically valid")
        int_bbox = int_thread.bounding_box()
        self.assertGreaterEqual(int_bbox.min.Z, -1e-5, "Internal thread should not overhang below Z=0")
        self.assertLessEqual(int_bbox.max.Z, 20.2 + 1e-5, "Internal thread should not overhang above Z=length")

    def test_shaft_connection_and_solid_union(self):
        # Verify that attaching thread to shaft produces a single valid solid without disjoint bodies
        neck_length = 25.2
        outer_thread_od = 74.5
        depth = 4.75
        neck_r = outer_thread_od / 2.0
        neck_core_r = neck_r - depth
        pitch = 8.0

        thread = generate_helical_thread(
            pitch=pitch,
            depth=depth,
            length=neck_length,
            core_radius=neck_core_r,
            is_internal=False
        )

        with BuildPart() as shaft_builder:
            Cylinder(radius=neck_core_r, height=neck_length, align=(Align.CENTER, Align.CENTER, Align.MIN))
            insert(thread, mode=Mode.ADD)

        shaft_with_thread = shaft_builder.part
        self.assertTrue(shaft_with_thread.is_valid, "Shaft with thread should be valid")
        self.assertEqual(len(shaft_with_thread.solids()), 1, "Shaft with thread should form a single solid")

    def test_housing_and_cap_assemblies(self):
        lid = Housing_Lid_Reader()
        self.assertTrue(lid.is_valid, "Housing_Lid_Reader should be valid")
        self.assertEqual(len(lid.solids()), 1, "Housing_Lid_Reader should be a single solid")

        cap = Torque_Cap_Inner()
        self.assertTrue(cap.is_valid, "Torque_Cap_Inner should be valid")
        self.assertEqual(len(cap.solids()), 1, "Torque_Cap_Inner should be a single solid")

        adapter = Threaded_Luer_Adapter(render_threads=True)
        self.assertTrue(adapter.is_valid, "Threaded_Luer_Adapter should be valid")
        self.assertEqual(len(adapter.solids()), 1, "Threaded_Luer_Adapter should be a single solid")

if __name__ == "__main__":
    unittest.main()
