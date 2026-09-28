import unittest
from build123d import *
from src.connectors import (
    JST_XH_2_Pin_Header,
    JST_XH_2_Pin_Plug,
    USB_C_Panel_Mount,
    Luer_Bulkhead_Panel_Mount,
)

class TestConnectorBounds(unittest.TestCase):
    def test_jst_xh_header_bounds(self):
        header = JST_XH_2_Pin_Header()
        bb = header.bounding_box()
        self.assertAlmostEqual(bb.size.X, 7.5, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 5.7, delta=0.1)
        self.assertAlmostEqual(bb.size.Z, 11.3, delta=0.1)  # 9.8mm body + 1.5mm pin extension
        self.assertTrue(header.is_valid)

    def test_jst_xh_plug_bounds(self):
        plug = JST_XH_2_Pin_Plug()
        bb = plug.bounding_box()
        self.assertAlmostEqual(bb.size.X, 5.7, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 5.7, delta=0.1)
        self.assertAlmostEqual(bb.size.Z, 10.5, delta=0.1)  # 8.0mm body + 2.5mm wire extension
        self.assertTrue(plug.is_valid)

    def test_usbc_panel_mount_bounds(self):
        usbc = USB_C_Panel_Mount()
        bb = usbc.bounding_box()
        self.assertAlmostEqual(bb.size.X, 14.0, delta=0.1)
        self.assertAlmostEqual(bb.size.Y, 18.5, delta=0.2)  # 15mm board + receptacle protrusion
        self.assertAlmostEqual(bb.size.Z, 4.0, delta=0.1)   # 1.6mm PCB centered + 3.2mm receptacle
        self.assertTrue(usbc.is_valid)

    def test_luer_bulkhead_bounds(self):
        luer = Luer_Bulkhead_Panel_Mount()
        bb = luer.bounding_box()
        self.assertAlmostEqual(bb.size.X, 14.0, delta=0.1)  # 14mm corner-to-corner hex
        self.assertAlmostEqual(bb.size.Y, 12.12, delta=0.1) # 12.12mm flat-to-flat hex (14*sqrt(3)/2)
        self.assertGreater(bb.size.Z, 20.0)                 # Total vertical assembly height
        self.assertTrue(luer.is_valid)

if __name__ == '__main__':
    unittest.main()
