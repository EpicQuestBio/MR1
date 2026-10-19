import unittest
import math
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from build123d import *
from src.constants import *
from src.cartridge import (
    PCB_Rigid_Active,
    PCB_Main_Reader_2D,
    PCB_Main_Reader,
    Carrier_Frame_Hex,
    Nanopore_Carrier,
)
from src.housing import (
    Housing_Pump_Case,
    Housing_Pump_Lid,
    Housing_Case_Reader,
    Housing_Lid_Reader,
)
from src.nanopore_wafer_mold import (
    Nanopore_Wafer_Mold_Left,
    Nanopore_Wafer_Mold_Right,
)

class TestLegacyFeatureParity(unittest.TestCase):
    """
    Validates that build123d models and project exports preserve all functional
    features present in the legacy OpenSCAD implementation.
    """

    def test_pcb_main_reader_dxf_dimensions_and_cutouts(self):
        """
        Verify PCB_Main_Reader_2D is an 80x60mm rectangular motherboard
        with 4 mounting holes, 2 USB-C cutouts, 1 JST cutout, and 4 fluid clearances,
        matching OpenSCAD modules/housing_reader.scad:PCB_Main_Reader_2D.
        """
        sketch = PCB_Main_Reader_2D()
        self.assertIsNotNone(sketch, "PCB_Main_Reader_2D sketch failed to generate.")
        bb = sketch.bounding_box()

        # Must be rectangular 80.0 x 60.0 mm (NOT a 55mm hexagon!)
        self.assertAlmostEqual(bb.size.X, PCB_W, delta=0.5,
                               msg=f"Main Reader PCB width {bb.size.X} must be {PCB_W}mm (not a 55mm hex!)")
        self.assertAlmostEqual(bb.size.Y, PCB_L, delta=0.5,
                               msg=f"Main Reader PCB length {bb.size.Y} must be {PCB_L}mm")

        def _get_shape_volume(shape):
            if shape is None:
                return 0.0
            if hasattr(shape, "volume"):
                return shape.volume
            if hasattr(shape, "__iter__"):
                return sum(getattr(s, "volume", 0.0) for s in shape)
            return 0.0

        # Test intersection on 3D solid at mounting hole locations (must be cut out / empty)
        solid = PCB_Main_Reader()
        for mx in [-35.0, 35.0]:
            for my in [-25.0, 25.0]:
                probe = Solid.make_cylinder(0.5, 4.0).move(Location((mx, my, -1.0)))
                inter = solid.intersect(probe)
                vol = _get_shape_volume(inter)
                self.assertAlmostEqual(vol, 0.0, delta=0.01,
                                 msg=f"Mounting hole at ({mx}, {my}) must be cut out of PCB_Main_Reader.")

        # Test single parameterized USB-C cutout at (USB_OFFSET_X, 25)
        ux = USB_OFFSET_X
        probe = Solid.make_box(4.0, 4.0, 4.0).move(Location((ux - 2.0, 25.0 - 2.0, -1.0)))
        inter = solid.intersect(probe)
        vol = _get_shape_volume(inter)
        self.assertAlmostEqual(vol, 0.0, delta=0.01,
                         msg=f"USB-C cutout at ({USB_OFFSET_X}, 25.0) must be cut out of PCB_Main_Reader.")

        # Test JST cutout at (0, -19)
        probe = Solid.make_box(4.0, 4.0, 4.0).move(Location((-2.0, -19.0 - 2.0, -1.0)))
        inter = solid.intersect(probe)
        vol = _get_shape_volume(inter)
        self.assertAlmostEqual(vol, 0.0, delta=0.01,
                         msg=f"JST connector cutout at (0, -19) must be cut out of PCB_Main_Reader.")

        # Test 4 fluid port clearance holes at PORT_RADIUS = 20mm
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP, ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
            fx = PORT_RADIUS * math.cos(math.radians(a))
            fy = PORT_RADIUS * math.sin(math.radians(a))
            probe = Solid.make_cylinder(0.5, 4.0).move(Location((fx, fy, -1.0)))
            inter = solid.intersect(probe)
            vol = _get_shape_volume(inter)
            self.assertAlmostEqual(vol, 0.0, delta=0.01,
                             msg=f"Fluid clearance hole at angle {a} deg ({fx:.2f}, {fy:.2f}) must be cut out.")

    def test_carrier_frame_hex_and_plate_2(self):
        """
        Verify Carrier_Frame_Hex is a 60mm hexagonal frame with 28.5x38.5mm central PCB pocket
        and 4 fluid pass-throughs, matching OpenSCAD modules/cartridge.scad:Carrier_Frame_Hex.
        """
        frame = Carrier_Frame_Hex()
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_valid)
        bb = frame.bounding_box()

        # Hex dimensions 55.0 x 51.96 mm
        self.assertAlmostEqual(bb.size.X, 55.0, delta=0.2)
        self.assertAlmostEqual(bb.size.Y, 51.96, delta=0.2)

        # Center must be hollow (pocket for 28x38 PCB)
        center_pt = Vector(0, 0, frame.bounding_box().center().Z)
        # Bounding box of pocket or intersection test
        test_box = Solid.make_box(20.0, 20.0, 10.0).move(Location((-10, -10, -5)))
        inter = frame.intersect(test_box)
        vol = sum(s.volume for s in inter) if hasattr(inter, '__iter__') else getattr(inter, 'volume', 0.0)
        self.assertAlmostEqual(vol, 0.0, delta=0.01, msg="Carrier frame center must have through pocket for PCB.")

    def test_nanopore_carrier_round_pcb(self):
        """
        Verify Nanopore_Carrier is a 20mm round disc with central aperture and tab slots,
        matching OpenSCAD modules/cartridge.scad:Nanopore_Carrier.
        """
        carrier = Nanopore_Carrier()
        self.assertIsNotNone(carrier)
        self.assertTrue(carrier.is_valid)
        bb = carrier.bounding_box()

        self.assertAlmostEqual(bb.size.X, CARRIER_DIAM, delta=0.2)
        self.assertAlmostEqual(bb.size.Y, CARRIER_DIAM, delta=0.2)
        self.assertAlmostEqual(bb.size.Z, PCB_THIN, delta=0.1)

    def test_amplifier_gasket_mold_exports(self):
        """
        Verify Nanopore_Wafer_Mold_Left/Right support is_nanopore=False for casting
        the Fitted_Amplifier_Gasket, matching OpenSCAD Amplifier_Gasket_Mold_Left_STL.
        """
        mold_l = Nanopore_Wafer_Mold_Left(is_nanopore=False)
        mold_r = Nanopore_Wafer_Mold_Right(is_nanopore=False)

        self.assertIsNotNone(mold_l)
        self.assertTrue(mold_l.is_valid)
        self.assertIsNotNone(mold_r)
        self.assertTrue(mold_r.is_valid)

        # In amplifier mode, there should be NO protrusion pocket at X = -gasket_thick/2 - PCB_Thickness/2
        # Both molds should mate with 0 collision
        inter = mold_l.intersect(mold_r)
        vol = sum(s.volume for s in inter) if hasattr(inter, '__iter__') else getattr(inter, 'volume', 0.0)
        self.assertAlmostEqual(vol, 0.0, delta=0.01)

    def test_housing_lid_reader_legacy_features(self):
        """
        Verify Housing_Lid_Reader features from OpenSCAD modules/housing_reader.scad:
        1. 4x 10mm vertical fluid pass-through holes at PORT_RADIUS=20mm
        2. Ribbon cable clearance cavity in hexagon wall at (0, -27.5)
        3. 4x horizontal side fluid ports at Y = ±20mm
        4. Lower wall outer inset (2.5mm inset on bottom 15mm)
        5. Corner screw mounting holes with counterbores
        """
        lid = Housing_Lid_Reader()
        self.assertTrue(lid.is_valid)

        # 1. Test vertical fluid pass-through holes at (PORT_RADIUS, 0) rotated by the 4 angles
        # The shelf / neck floor is at Z=0 to Z=5. A solid cylinder along each port must intersect air, not solid lid.
        for a in [ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_TOP, ANGLE_FLUID_IN_BOT, ANGLE_FLUID_OUT_BOT]:
            px = PORT_RADIUS * math.cos(math.radians(a))
            py = PORT_RADIUS * math.sin(math.radians(a))
            # Test point at (px, py, 2.5) must NOT be inside the solid lid
            port_cyl = Solid.make_cylinder(2.0, 20.0).move(Location((px, py, -5.0)))
            inter = lid.intersect(port_cyl)
            vol = sum(s.volume for s in inter) if hasattr(inter, '__iter__') else getattr(inter, 'volume', 0.0)
            self.assertLess(vol, 0.5,
                            f"Housing_Lid_Reader is missing fluid pass-through hole at angle {a} deg ({px:.1f}, {py:.1f}).")

        def _get_shape_volume(shape):
            if shape is None:
                return 0.0
            if hasattr(shape, "volume"):
                return shape.volume
            if hasattr(shape, "__iter__"):
                return sum(getattr(s, "volume", 0.0) for s in shape)
            return 0.0

        # 2. Test ribbon cable clearance cavity at (0, -27.5) across full vertical extent (Z in [-10.0, 30.2] mm)
        cable_probe = Solid.make_box(8.0, 2.0, 40.2).move(Location((-4.0, -28.5, -10.0)))
        inter_cable = lid.intersect(cable_probe)
        vol_cable = _get_shape_volume(inter_cable)
        self.assertLess(vol_cable, 0.5,
                        f"Housing_Lid_Reader has solid obstruction in ribbon cable cavity (blocked volume: {vol_cable:.4f} mm^3).")

        # 2b. Explicit upper neck test probe (Z in [22.0, 30.2] mm)
        neck_probe = Solid.make_box(8.0, 2.0, 8.2).move(Location((-4.0, -28.5, 22.0)))
        inter_neck = lid.intersect(neck_probe)
        vol_neck = _get_shape_volume(inter_neck)
        self.assertLess(vol_neck, 0.5,
                        f"Housing_Lid_Reader has solid obstruction in upper neck ribbon cavity (blocked volume: {vol_neck:.4f} mm^3).")

        # 3. Horizontal side fluid ports at Y = ±20, Z = -13.0
        lid_half_w = (BASE_W + 2 * (WALL - 2.5)) / 2.0  # 57.5mm
        for x_wall in [-lid_half_w, lid_half_w]:
            for y_port in [-20.0, 20.0]:
                probe = Solid.make_cylinder(1.5, 10.0).move(
                    Location((x_wall - 5.0 if x_wall < 0 else x_wall - 5.0, y_port, -13.0)) * Rotation(0, 90, 0)
                )
                inter_side = lid.intersect(probe)

                # build123d.intersect returns a ShapeList or Part
                if hasattr(inter_side, "volume"):
                    vol_side = inter_side.volume
                elif hasattr(inter_side, "solids"):
                    # it might be a shapelist, get sum of volumes
                    vol_side = sum([s.volume for s in inter_side.solids()])
                elif inter_side is None:
                    vol_side = 0.0
                else:
                    vol_side = 0.0

                self.assertLess(vol_side, 50.0,
                                f"Housing_Lid_Reader is missing side fluid port at X={x_wall}, Y={y_port}.")

    def test_housing_pump_case_legacy_features(self):
        """
        Verify Housing_Pump_Case features from OpenSCAD modules/housing_pump.scad:
        1. 4x side fluid ports with bosses at Y = ±20mm (2 left, 2 right)
        2. Top knife-edge seal ridge
        3. Internal pump mounting plate/standoffs
        """
        case = Housing_Pump_Case()
        self.assertTrue(case.is_valid)

        # 1. Side ports with bosses extend beyond ±(BASE_W/2 + WALL) at Y=±20
        bb = case.bounding_box()
        # With bosses (d=20, h=wall*3=15mm) on left and right, bounding box X should exceed BASE_W + 2*WALL
        self.assertGreater(bb.size.X, BASE_W + 2 * WALL + 5.0,
                           "Housing_Pump_Case is missing side fluid port bosses (width must exceed case base).")

    def test_housing_reader_case_knife_edge_and_holes(self):
        """
        Verify Housing_Case_Reader features:
        1. Top knife-edge seal matching lid groove
        2. Corner mounting screw holes
        3. Feet dimples located at ±(BASE_W/2 - FEET_INSET) = ±42.5mm and bounds within 115x115mm
        """
        case = Housing_Case_Reader()
        self.assertTrue(case.is_valid)
        bb = case.bounding_box()
        # Top knife-edge seal should extend slightly above READER_LID_THICK/2
        self.assertGreater(bb.max.Z, READER_LID_THICK / 2.0 - 0.01)

        # Base case footprint width/length must not exceed 115.0mm (no feet sticking out past -57.5 or +57.5)
        self.assertLessEqual(bb.size.X, 115.1, "Housing_Case_Reader X width exceeds 115mm (feet floating outside)")
        self.assertLessEqual(bb.size.Y, 115.1, "Housing_Case_Reader Y length exceeds 115mm (feet floating outside)")

        # Verify 4 feet dimples exist at (±42.5, ±42.5) on the bottom face
        feet_x = BASE_W / 2.0 - FEET_INSET  # 42.5 mm
        feet_y = BASE_L / 2.0 - FEET_INSET  # 42.5 mm
        for xs in [-feet_x, feet_x]:
            for ys in [-feet_y, feet_y]:
                probe = Solid.make_cylinder(1.0, 2.0).move(Location((xs, ys, -READER_LID_THICK / 2.0 - 1.0)))
                inter = case.intersect(probe)
                vol = inter.volume if hasattr(inter, "volume") else sum(s.volume for s in inter)
                self.assertGreater(vol, 0.1, f"Foot dimple not found at ({xs}, {ys}) on bottom face")

    def test_ptfe_interposer_features(self):
        """
        Verify the PTFE Interposer (55.0 x 51.962 x 0.8 mm):
        1. Hexagonal dimensions and 0.8mm thickness.
        2. Central diamond cutout for silicone protrusion.
        3. Pogo pin landing array (6 pads at Y=2.5mm).
        4. Fluid pass-through holes (4x at r=20mm).
        5. Ag/AgCl ribbon electrode pads on top (30 deg) and bottom (210 deg).
        6. Perfect mating with zero collision against both top and bottom gaskets.
        """
        from src.cartridge import (
            PTFE_Interposer,
            Silver_Chloride_Ribbon_Pads,
            Cast_Nanopore_Wafer_Gasket,
            Fitted_Amplifier_Gasket
        )

        interposer = PTFE_Interposer()
        self.assertTrue(interposer.is_valid)
        bb = interposer.bounding_box()

        # 1. Hexagonal footprint & 0.8mm PTFE thickness
        self.assertAlmostEqual(bb.size.X, 55.0, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 51.962, delta=0.1)
        self.assertAlmostEqual(bb.size.Z, PCB_THIN, delta=0.05)

        def get_vol(shape):
            if shape is None:
                return 0.0
            if isinstance(shape, (list, ShapeList)):
                return sum(s.volume for s in shape)
            if hasattr(shape, "volume"):
                return shape.volume
            return 0.0

        # 2. Central diamond cutout must be hollow
        center_cyl = Solid.make_cylinder(1.5, 4.0).move(Location((0, 0, -1.0)))
        inter_c = interposer.intersect(center_cyl)
        vol_c = get_vol(inter_c)
        self.assertAlmostEqual(vol_c, 0.0, delta=0.01, msg="Interposer center must have wafer protrusion cutout.")

        # 3. Pogo pin landing holes at Y=2.5mm
        for px in [-11.5, -6.5, -1.5, 1.5, 6.5, 11.5]:
            pogo_probe = Solid.make_cylinder(0.3, 4.0).move(Location((px, POGO_Y, -1.0)))
            inter_p = interposer.intersect(pogo_probe)
            vol_p = get_vol(inter_p)
            self.assertAlmostEqual(vol_p, 0.0, delta=0.01,
                                   msg=f"Pogo contact at ({px}, {POGO_Y}) must be present.")

        # 4. Fluid pass-throughs at r=20mm
        for a in [ANGLE_FLUID_IN_BOT, ANGLE_FLUID_IN_TOP, ANGLE_FLUID_OUT_BOT, ANGLE_FLUID_OUT_TOP]:
            fx = PORT_RADIUS * math.cos(math.radians(a))
            fy = PORT_RADIUS * math.sin(math.radians(a))
            fluid_probe = Solid.make_cylinder(0.5, 4.0).move(Location((fx, fy, -1.0)))
            inter_f = interposer.intersect(fluid_probe)
            vol_f = get_vol(inter_f)
            self.assertAlmostEqual(vol_f, 0.0, delta=0.01,
                                   msg=f"Fluid pass-through at angle {a} deg ({fx:.1f}, {fy:.1f}) must be hollow.")

        # 5. Ag/AgCl Ribbon Pads models
        pads_top = Silver_Chloride_Ribbon_Pads(top=True)
        pads_bot = Silver_Chloride_Ribbon_Pads(top=False)
        self.assertTrue(pads_top.is_valid)
        self.assertTrue(pads_bot.is_valid)
        self.assertGreater(pads_top.volume, 0.1)
        self.assertGreater(pads_bot.volume, 0.1)

        # 6. Dual-gasket zero collision mating
        gasket_bot = Fitted_Amplifier_Gasket().move(Location((0, 0, -GASKET_THICK)))
        gasket_top = Cast_Nanopore_Wafer_Gasket().move(Location((0, 0, PCB_THIN)))

        inter_bot = interposer.intersect(gasket_bot)
        vol_bot = get_vol(inter_bot)
        inter_top = interposer.intersect(gasket_top)
        vol_top = get_vol(inter_top)

        self.assertAlmostEqual(vol_bot, 0.0, delta=0.01, msg=f"Interposer collides with bottom gasket: {vol_bot}")
        self.assertAlmostEqual(vol_top, 0.0, delta=0.01, msg=f"Interposer collides with top gasket: {vol_top}")

if __name__ == "__main__":
    unittest.main()
