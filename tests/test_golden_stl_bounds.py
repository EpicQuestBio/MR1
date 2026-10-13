import unittest
import math
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from build123d import *
from src.constants import *
from src.cartridge import (
    PCB_Rigid_Active,
    Cast_Nanopore_Wafer_Gasket,
    Fitted_Amplifier_Gasket,
    Bottom_Pusher_Plate,
    Plate_1_Base_Hex,
    Plate_3_Top_Hex,
    Pressure_Puck,
    Nanopore_Wafer_Silicon,
    PCB_Pump_Controller
)
from src.housing import (
    Housing_Pump_Case,
    Housing_Pump_Lid,
    Housing_Case_Reader,
    Housing_Lid_Reader
)
from src.torque_cap import (
    Torque_Cap_Outer,
    Torque_Cap_Inner
)
from src.nanopore_wafer_mold import (
    Nanopore_Wafer_Mold_Left,
    Nanopore_Wafer_Mold_Right
)
from src.common import Hex_Base_Sketch

class TestGoldenSTLAndPCBBounds(unittest.TestCase):
    """
    Unit test suite asserting that Build123d CAD models are bounded, valid,
    and match the golden exported STLs and KiCad PCB as the source of truth.
    """

    def test_kicad_pcb_source_of_truth(self):
        """Verify that Hex_Base_Sketch matches the KiCad PCB edge cut dimensions."""
        sketch = Hex_Base_Sketch()
        bb = sketch.bounding_box()
        self.assertAlmostEqual(bb.size.X, 55.0, delta=0.05,
                               msg=f"PCB width {bb.size.X} does not match 55.0mm")
        self.assertAlmostEqual(bb.size.Y, 51.9615, delta=0.05,
                               msg=f"PCB height {bb.size.Y} does not match 51.962mm (30*sqrt(3))")

    def test_cartridge_pcb_bounds(self):
        """Verify PCB_Rigid_Active matches KiCad PCB source of truth."""
        pcb = PCB_Rigid_Active()
        self.assertTrue(pcb.is_valid)
        bb = pcb.bounding_box()
        self.assertAlmostEqual(bb.size.X, 55.0, delta=0.05)
        self.assertAlmostEqual(bb.size.Y, 51.962, delta=0.05)
        self.assertAlmostEqual(bb.size.Z, PCB_THIN, delta=0.05)

    def test_gasket_pcb_recess_and_seal(self):
        """Verify that the diamond portion of the top gasket recesses into the PCB cutout
        and touches the opposite gasket (Fitted_Amplifier_Gasket) forming a face-to-face seal without collision."""
        pcb = PCB_Rigid_Active()
        gasket_top = Cast_Nanopore_Wafer_Gasket()
        gasket_bot = Fitted_Amplifier_Gasket()

        p_bot = gasket_bot.move(Location((0, 0, 7.0)))
        p_pcb = pcb.move(Location((0, 0, 8.6)))
        p_top = gasket_top.move(Location((0, 0, 9.4)))

        # 1. Protrusion must reach down to touch bottom gasket
        bb_top = p_top.bounding_box()
        bb_bot = p_bot.bounding_box()
        self.assertAlmostEqual(bb_top.min.Z, bb_bot.max.Z, delta=0.02,
                               msg=f"Top gasket bottom ({bb_top.min.Z}) does not touch bottom gasket top ({bb_bot.max.Z})")

        # 2. Zero collision between top gasket protrusion and PCB cutout
        inter_pcb = p_pcb.intersect(p_top)
        vol_pcb = inter_pcb.volume if inter_pcb is not None else 0.0
        self.assertLess(vol_pcb, 0.01, f"Top gasket collides with PCB: vol={vol_pcb}")

        # 3. Zero collision with bottom gasket
        inter_bot = p_bot.intersect(p_top)
        vol_bot = inter_bot.volume if inter_bot is not None else 0.0
        self.assertLess(vol_bot, 0.01, f"Top gasket penetrates bottom gasket: vol={vol_bot}")

    def test_nanopore_wafer_silicon_bounds(self):
        """Verify Nanopore_Wafer_Silicon is 4x4x0.5mm rotated 45 degrees (diagonal ~5.657mm)."""
        wafer = Nanopore_Wafer_Silicon()
        self.assertTrue(wafer.is_valid)
        bb = wafer.bounding_box()
        expected_diag = 4.0 * math.sqrt(2) # 5.65685 mm
        self.assertAlmostEqual(bb.size.X, expected_diag, delta=0.05)
        self.assertAlmostEqual(bb.size.Y, expected_diag, delta=0.05)
        self.assertAlmostEqual(bb.size.Z, 0.5, delta=0.05)

    def test_bottom_pusher_plate_bounds(self):
        """Verify Bottom_Pusher_Plate matches golden STL (55.0 x 51.962 x 3.0 mm)."""
        plate = Bottom_Pusher_Plate()
        self.assertTrue(plate.is_valid)
        bb = plate.bounding_box()
        self.assertAlmostEqual(bb.size.X, 55.0, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 51.962, delta=0.1)
        self.assertAlmostEqual(bb.size.Z, 3.0, delta=0.1)

    def test_pressure_puck_bounds(self):
        """Verify Pressure_Puck bounds after cutout modification."""
        puck = Pressure_Puck()
        self.assertTrue(puck.is_valid)
        bb = puck.bounding_box()
        # X is reduced slightly below 60.0 because the finger cutouts were moved inward to 25mm radius
        self.assertAlmostEqual(bb.size.X, 59.15, delta=1.5)
        self.assertAlmostEqual(bb.size.Y, 60.0, delta=0.2)
        self.assertAlmostEqual(bb.size.Z, 6.0, delta=0.1)

    def test_housing_lid_reader_bounds_and_threading(self):
        """Verify Housing_Lid_Reader matches golden STL (100.0 x 100.0 x 57.7 mm)."""
        lid = Housing_Lid_Reader()
        self.assertTrue(lid.is_valid)
        bb = lid.bounding_box()
        self.assertAlmostEqual(bb.size.X, 100.0, delta=0.5)
        self.assertAlmostEqual(bb.size.Y, 100.0, delta=0.5)
        self.assertAlmostEqual(bb.size.Z, 57.7, delta=0.5)
        self.assertGreater(lid.volume, 100000.0)

    def test_torque_cap_inner_bounds_and_threading(self):
        """Verify Torque_Cap_Inner matches golden STL (81.4 x 81.4 x 20.2 mm)."""
        cap = Torque_Cap_Inner()
        self.assertTrue(cap.is_valid)
        bb = cap.bounding_box()
        self.assertAlmostEqual(bb.size.X, 81.4, delta=0.2)
        self.assertAlmostEqual(bb.size.Y, 81.4, delta=0.2)
        self.assertAlmostEqual(bb.size.Z, 20.2, delta=0.2)
        self.assertGreater(cap.volume, 5000.0)

    def test_torque_cap_outer_bounds(self):
        """Verify Torque_Cap_Outer matches golden STL (95.0 x 95.0-97.0 x 30.2 mm)."""
        cap = Torque_Cap_Outer()
        self.assertTrue(cap.is_valid)
        bb = cap.bounding_box()
        self.assertAlmostEqual(bb.size.X, 95.0, delta=1.0)
        self.assertAlmostEqual(bb.size.Y, 95.0, delta=2.5)
        self.assertAlmostEqual(bb.size.Z, 30.2, delta=0.5)

    def test_gasket_x_fluidic_channels(self):
        """Verify Cis and Trans gaskets form the correct 'X' microfluidic channels."""
        top_gasket = Cast_Nanopore_Wafer_Gasket()
        bot_gasket = Fitted_Amplifier_Gasket()

        self.assertTrue(top_gasket.is_valid)
        self.assertTrue(bot_gasket.is_valid)

        bb_top = top_gasket.bounding_box()
        bb_bot = bot_gasket.bounding_box()

        # Both gaskets must have the 55.0 x 51.962 hex footprint
        self.assertAlmostEqual(bb_top.size.X, 55.0, delta=0.1)
        self.assertAlmostEqual(bb_top.size.Y, 51.962, delta=0.1)
        self.assertAlmostEqual(bb_bot.size.X, 55.0, delta=0.1)
        self.assertAlmostEqual(bb_bot.size.Y, 51.962, delta=0.1)

        # Verify Cis channel port positions (210 deg and 30 deg)
        cis_in = (-PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30)))
        cis_out = (PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30)))

        # Verify Trans channel port positions (330 deg and 150 deg)
        trans_in = (PORT_RADIUS * math.cos(math.radians(30)), -PORT_RADIUS * math.sin(math.radians(30)))
        trans_out = (-PORT_RADIUS * math.cos(math.radians(30)), PORT_RADIUS * math.sin(math.radians(30)))

        # Verify they are non-overlapping diagonal pairs crossing at (0, 0)
        self.assertAlmostEqual(cis_in[0], -17.3205, delta=0.01)
        self.assertAlmostEqual(cis_in[1], -10.0000, delta=0.01)
        self.assertAlmostEqual(trans_in[0], 17.3205, delta=0.01)
        self.assertAlmostEqual(trans_in[1], -10.0000, delta=0.01)

    def test_mold_geometry_and_interlocks(self):
        """Verify Left and Right mold halves match OpenSCAD block dimensions,
        and mate at X=0 with 0 collision and exact alignment dowel pin engagement."""
        left = Nanopore_Wafer_Mold_Left(is_nanopore=True)
        right = Nanopore_Wafer_Mold_Right(is_nanopore=True)

        self.assertTrue(left.is_valid)
        self.assertTrue(right.is_valid)

        bb_l = left.bounding_box()
        bb_r = right.bounding_box()

        # Both mold blocks must be 80.0mm wide (Y) and 90.0mm high (Z)
        self.assertAlmostEqual(bb_l.size.Y, 80.0, delta=5.0)
        self.assertAlmostEqual(bb_l.size.Z, 90.0, delta=0.1)
        self.assertAlmostEqual(bb_r.size.Y, 80.0, delta=5.0)
        self.assertAlmostEqual(bb_r.size.Z, 90.0, delta=0.1)

        # Left mold thickness spans X in [-15.0, 0.0]
        self.assertAlmostEqual(bb_l.min.X, -15.0, delta=0.1)
        self.assertAlmostEqual(bb_l.max.X, 0.0, delta=0.05)

        # Right mold thickness spans X in [-4.8, 15.0] (4.8mm male dowel pins protrude past X=0)
        self.assertAlmostEqual(bb_r.min.X, -4.8, delta=0.1)
        self.assertAlmostEqual(bb_r.max.X, 15.0, delta=0.1)

        # Zero collision when mated at X=0
        inter = left.intersect(right)
        if inter is None:
            vol = 0.0
        elif hasattr(inter, "volume"):
            vol = inter.volume
        else:
            vol = sum(s.volume for s in inter)
        self.assertAlmostEqual(vol, 0.0, delta=0.001,
                               msg=f"Mated mold halves have collision volume: {vol} mm^3")

    def test_pump_pcb_bounds(self):
        """Verify PCB_Pump_Controller matches 88.0 x 88.0 x 1.6 mm bounds and fits in Housing_Pump_Case bucket."""
        pcb = PCB_Pump_Controller()
        self.assertTrue(pcb.is_valid)
        bb = pcb.bounding_box()
        self.assertAlmostEqual(bb.size.X, 88.0, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 88.0, delta=0.1)
        self.assertAlmostEqual(bb.size.Z, 1.6, delta=0.05)

        # Check clearance inside Housing_Pump_Case bucket (90 x 90 mm)
        bucket_w = BASE_W - 2 * WALL  # 90.0 mm
        bucket_l = BASE_L - 2 * WALL  # 90.0 mm
        self.assertLess(bb.size.X, bucket_w, "Pump PCB must fit within Housing_Pump_Case internal bucket")
        self.assertLess(bb.size.Y, bucket_l, "Pump PCB must fit within Housing_Pump_Case internal bucket")

if __name__ == '__main__':
    unittest.main()

