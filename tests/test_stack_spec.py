# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""Tests for src/stack_spec.py (single source of truth for the pogo stack)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import stack_spec as S  # noqa: E402


class TestStackSpec(unittest.TestCase):
    def test_default_is_valid(self):
        self.assertEqual(S.validate(), [])

    def test_twelve_pins_contiguous(self):
        self.assertEqual([p.number for p in S.PINS], list(range(1, 13)))

    def test_banks_match_convention(self):
        self.assertEqual(len(S.pins_by_side(S.CIS)), 6)
        self.assertEqual(len(S.pins_by_side(S.TRANS)), 6)

    def test_fixed_net_names_present(self):
        nets = {p.net for p in S.PINS}
        for n in ("WS_CIS", "WS_CIS_WIDE", "RE_TRANS", "CE_GNDA", ">PORE_AMP",
                  "GUARD_CIS_A", "GUARD_CIS_B", "GUARD_WIDE"):
            self.assertIn(n, nets)

    def test_rings_have_feeders(self):
        for p in S.PINS:
            if p.ring:
                self.assertTrue(S.RING_FEEDERS[p.ring], p.ref)
        self.assertEqual(S.RING_FEEDERS[S.GUARD], (4, 6))
        self.assertEqual(S.RING_FEEDERS[S.GUARD_WIDE], (3,))
        self.assertEqual(S.RING_FEEDERS[S.GNDA], (1, 10, 12))

    def test_high_z_pins_are_ringed(self):
        for p in S.PINS:
            if p.net in S.HIGH_Z_NETS:
                self.assertIsNotNone(p.ring, p.ref)

    def test_spacer_values(self):
        self.assertAlmostEqual(S.DELRIN_THIN, 3.175, places=3)
        self.assertAlmostEqual(S.DELRIN_THICK, 6.858, places=3)
        self.assertAlmostEqual(S.PP_SHIM, 0.762, places=3)

    def test_gap_math(self):
        self.assertAlmostEqual(S.POGO.stroke, 1.5)
        lo, hi = S.gap_window()
        self.assertLess(lo, hi)
        self.assertTrue(lo <= S.pin_gap(S.DEFAULT_SPACERS) <= hi)

    def test_feasible_stacks_nonempty_and_in_window(self):
        stacks = S.feasible_stacks()
        self.assertTrue(stacks)
        lo, hi = S.gap_window()
        for st in stacks:
            self.assertTrue(lo - 1e-6 <= S.pin_gap(st) <= hi + 1e-6)

    def test_printed_spacer_covers_components(self):
        self.assertGreaterEqual(S.PRINTED_MIN, 3.0)
        self.assertIn(S.PRINTED_STEP, (0.1, 0.2))
        for st in S.feasible_stacks():
            self.assertGreaterEqual(st.printed, 3.0)
        under = S.SpacerStack(delrin_thin=True, printed=2.0)
        self.assertTrue(any("printed" in e for e in S.validate(under)))

    def test_bad_stack_rejected(self):
        bad = S.SpacerStack(delrin_thin=True, delrin_thick=True, pp_shim=True, printed=3.0)
        self.assertTrue(any("gap" in e for e in S.validate(bad)))

    def test_kicad_xy_flips_y(self):
        self.assertEqual(S.kicad_xy(1.0, 15.0), (1.0, -15.0))
        self.assertEqual(S.kicad_xy(0.0, 0.0), (0.0, 0.0))

    def test_fluid_x_topology(self):
        self.assertEqual(S.CIS_FLOW, ("H1", "H2"))
        self.assertEqual(S.TRANS_FLOW, ("H3", "H4"))

    def test_pins_clear_fluid_channels_and_ports(self):
        """Verify that every pogo pin site maintains safe clearance from microfluidic channels and ports."""
        errs = S.validate()
        self.assertFalse(any("too close" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
