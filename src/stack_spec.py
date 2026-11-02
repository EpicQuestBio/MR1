# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
stack_spec.py: single source of truth for the MR1 coax pogo-pin stack.

Pure Python (no build123d / KiCad imports) so CAD, footprint generators, PCB
builders, simulations and tests can all import it cheaply. See REFACTOR_PLAN.md.

Conventions
-----------
* CAD frame: X right, Y up, Z up the stack. KiCad Y = -CAD Y (see `kicad_xy`).
* Cis = top face of the interposer = faces the (inverted) Amplifier board.
  Cis pins are Bank B (CAD Y > 0). Trans pins are Bank A (CAD Y < 0).
* Every coax footprint has Pad 1 = signal / center landing pad (circle or
  square) and Pad 2 = concentric outer ring (net GUARD, GUARD_WIDE or GNDA).
* A ring on the Interposer can't float: each ring net is fed vertically by one or
  more dedicated pogo pins (`RING_FEEDERS`) from the Amplifier's driver.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

IN = 25.4  # mm per inch


# ---------------------------------------------------------------------------
# Pogo pin part
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PogoPinSpec:
    part: str = "LCSC C5221285 (YTC1P-6030-01)"
    free_length: float = 9.0  # mm, uncompressed
    working_height: float = 7.5  # mm, fully compressed (end of stroke)
    base_thickness: float = 2.0  # mm, SMT base
    spring_force: float = 0.8  # N per pin at working compression

    @property
    def stroke(self) -> float:
        return self.free_length - self.working_height


POGO = PogoPinSpec()

# Margin kept at each end of the stroke (mm). The pin must be at least this far
# from bottoming out and must still be compressed by at least this much.
STROKE_MARGIN_MIN = 0.25


# ---------------------------------------------------------------------------
# Pin map (12 pins, P1..P12)
# ---------------------------------------------------------------------------

CIS = "cis"
TRANS = "trans"
CIRCLE = "circle"
SQUARE = "square"
GUARD = "GUARD"
GUARD_WIDE = "GUARD_WIDE"
GNDA = "GNDA"


@dataclass(frozen=True)
class PinSpec:
    number: int
    net: str
    side: str  # CIS | TRANS (Bank B | Bank A)
    x: float  # CAD mm
    y: float  # CAD mm
    role: str  # "signal" | "guard_feed" | "gnd_feed"
    shape: str = CIRCLE  # pad 1 shape
    ring: Optional[str] = None  # pad 2 ring net (None = plain pad, feeds a ring)
    description: str = ""

    @property
    def ref(self) -> str:
        return f"P{self.number}"


PINS: Tuple[PinSpec, ...] = (
    # Bank B: Cis / sensing (CAD Y > 0)
    PinSpec(1, "GNDA_SHLD", CIS, -18.0, 16.0, "gnd_feed", description="Shield anchor on inlet/outlet manifold ground boundary"),
    PinSpec(2, "WS_CIS_WIDE", CIS, -10.0, 15.0, "signal", ring=GUARD_WIDE, description="Path 2 (200 nm) working sense"),
    PinSpec(3, "GUARD_WIDE", CIS, -6.0, 15.0, "guard_feed", description="Feeds the GUARD_WIDE ring around P2"),
    PinSpec(4, "GUARD_CIS_A", CIS, 4.0, 15.0, "guard_feed", description="Flanking guard A, feeds the GUARD ring around P5"),
    PinSpec(5, "WS_CIS", CIS, 8.0, 15.0, "signal", ring=GUARD, description="Path 1 (sub-5 nm) high-Z electrometer node"),
    PinSpec(6, "GUARD_CIS_B", CIS, 12.0, 15.0, "guard_feed", description="Flanking guard B, feeds the GUARD ring around P5"),
    # Bank A: Trans / excitation (CAD Y < 0)
    PinSpec(7, "CE_GNDA", TRANS, -18.0, -16.0, "signal", ring=GNDA, description="Counter electrode return"),
    PinSpec(8, "RE_TRANS", TRANS, -10.0, -15.0, "signal", ring=GNDA, description="Trans reference sense"),
    PinSpec(9, ">PORE_AMP", TRANS, -4.0, -15.0, "signal", ring=GNDA, description="Bias excitation drive"),
    PinSpec(10, "GNDA", TRANS, 3.0, -15.0, "gnd_feed", description="Analog ground fence, feeds GNDA rings"),
    PinSpec(11, "WEEP_SENSE", TRANS, 12.0, -15.0, "signal", ring=GNDA, description="Weep moat detector"),
    PinSpec(12, "GNDA_WEEP", TRANS, 18.0, -16.0, "gnd_feed", description="Perimeter weep drain / chassis tie"),
)

# Which pogo pins carry each ring net across the air gap (pin numbers).
RING_FEEDERS: Dict[str, Tuple[int, ...]] = {
    GUARD: (4, 6),
    GUARD_WIDE: (3,),
    GNDA: (1, 10, 12),
}

# High-impedance nets that need a guard/ground ring and low-leakage mask rules.
HIGH_Z_NETS = frozenset({">PORE_AMP", "WS_CIS", "WS_CIS_WIDE", "WEEP_SENSE"})


def pin(number: int) -> PinSpec:
    for p in PINS:
        if p.number == number:
            return p
    raise KeyError(number)


def pins_by_side(side: str) -> List[PinSpec]:
    return [p for p in PINS if p.side == side]


def pogo_xy() -> List[Tuple[float, float]]:
    """CAD (x, y) of every pin, in pin-number order."""
    return [(p.x, p.y) for p in PINS]


def kicad_xy(x: float, y: float) -> Tuple[float, float]:
    """Convert CAD (Y up) to KiCad board coordinates (Y down)."""
    return (x, -y if y else 0.0)


# ---------------------------------------------------------------------------
# Fluidics
# ---------------------------------------------------------------------------

FLUID_DRILL_DIA = 2.1
FLUID_PORT_X = 17.3205
FLUID_PORT_Y = 10.0
# H1..H4 CAD positions. Cis flow H1->H2, Trans flow H3->H4 (forms an X).
FLUID_HOLES: Dict[str, Tuple[float, float]] = {
    "H1": (-FLUID_PORT_X, FLUID_PORT_Y),
    "H2": (FLUID_PORT_X, -FLUID_PORT_Y),
    "H3": (-FLUID_PORT_X, -FLUID_PORT_Y),
    "H4": (FLUID_PORT_X, FLUID_PORT_Y),
}
CIS_FLOW = ("H1", "H2")
TRANS_FLOW = ("H3", "H4")


# ---------------------------------------------------------------------------
# Spacers and gap budget
# ---------------------------------------------------------------------------

GASKET_THICK = 1.5875  # 1/16", same gasket on both interposer faces
GASKET_CRUSH_FRAC = 0.10  # assumed compression of the gasket under clamp (verify, P7.3)

# Stock spacers (user-supplied 2026-11-01).
DELRIN_THIN = 0.125 * IN  # 3.175 mm
DELRIN_THICK = 0.270 * IN  # 6.858 mm
PP_SHIM = 0.030 * IN  # 0.762 mm, solid polypropylene
# 3D-printed adjustable spacer (user, 2026-11-01): printed at standard FDM layer
# heights (0.1 to 0.2 mm), so it is adjustable in layer-height steps. It fills the
# margins around the Amplifier's parts and must be at least 3 mm to cover the
# components. PRINTED_MAX is a practical upper bound, not a user figure.
PRINTED_LAYER = 0.1  # mm; use 0.2 for coarse steps
PRINTED_MIN = 3.0
PRINTED_MAX = 8.0
PRINTED_STEP = PRINTED_LAYER

STOCK_SPACERS: Dict[str, float] = {
    "delrin_0.125in": DELRIN_THIN,
    "delrin_0.270in": DELRIN_THICK,
    "pp_0.030in": PP_SHIM,
}


@dataclass(frozen=True)
class SpacerStack:
    delrin_thin: bool = False
    delrin_thick: bool = False
    pp_shim: bool = False
    printed: float = 0.0  # mm

    @property
    def stock_height(self) -> float:
        return (
            (DELRIN_THIN if self.delrin_thin else 0.0)
            + (DELRIN_THICK if self.delrin_thick else 0.0)
            + (PP_SHIM if self.pp_shim else 0.0)
        )

    @property
    def height(self) -> float:
        return self.stock_height + self.printed


def pin_gap(stack: SpacerStack) -> float:
    """Amplifier underside -> interposer top face, with the Cis gasket crushed."""
    return stack.height + GASKET_THICK * (1.0 - GASKET_CRUSH_FRAC)


def pin_compression(gap: float, pin_spec: PogoPinSpec = POGO) -> float:
    """How far the pin is compressed at the given gap (mm). Negative = no contact."""
    return pin_spec.free_length - gap


def gap_window(pin_spec: PogoPinSpec = POGO) -> Tuple[float, float]:
    """Allowed gap range (mm): at least STROKE_MARGIN_MIN compressed, and at least
    STROKE_MARGIN_MIN short of bottoming out."""
    return (
        pin_spec.working_height + STROKE_MARGIN_MIN,
        pin_spec.free_length - STROKE_MARGIN_MIN,
    )


def feasible_stacks(pin_spec: PogoPinSpec = POGO) -> List[SpacerStack]:
    """Every stock-spacer combination that has a printed spacer value (within
    its range and step) putting the gap inside `gap_window`. Returned with the
    printed height centered in the window."""
    lo, hi = gap_window(pin_spec)
    mid = 0.5 * (lo + hi)
    out: List[SpacerStack] = []
    for a, b, c in itertools.product((False, True), repeat=3):
        base = SpacerStack(a, b, c)
        gap0 = pin_gap(base)
        need = mid - gap0
        steps = round(need / PRINTED_STEP)
        printed = min(max(steps * PRINTED_STEP, PRINTED_MIN), PRINTED_MAX)
        printed = round(printed, 4)
        cand = SpacerStack(a, b, c, printed)
        if lo - 1e-9 <= pin_gap(cand) <= hi + 1e-9:
            out.append(cand)
    return out


# Default build selection. Chosen so the default gap sits mid-window.
DEFAULT_SPACERS = SpacerStack(delrin_thin=True, delrin_thick=False, pp_shim=False, printed=3.6)


# ---------------------------------------------------------------------------
# Pad geometry shared by footprints and CAD
# ---------------------------------------------------------------------------

PAD_SIZE = 2.0  # signal pad diameter / side (mm)
RING_INNER_R = 1.6  # ring inner radius (mm)
RING_WIDTH = 0.5  # ring copper width (mm)
RING_OUTER_R = RING_INNER_R + RING_WIDTH
PAD_CLEARANCE = 0.3  # min copper-to-copper gap between neighbouring pin sites (mm)


def site_radius(ring: Optional[str]) -> float:
    """Outer copper radius of a pin site (ring if present, else the pad)."""
    return RING_OUTER_R if ring else PAD_SIZE / 2.0


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate(stack: SpacerStack = DEFAULT_SPACERS) -> List[str]:
    """Return human-readable problems (empty list = valid)."""
    errs: List[str] = []
    nums = [p.number for p in PINS]
    if sorted(nums) != list(range(1, len(PINS) + 1)):
        errs.append(f"pin numbers must be 1..N contiguous, got {nums}")
    if len({p.net for p in PINS}) != len(PINS):
        errs.append("duplicate net names in pin map")

    for p in PINS:
        if p.side == CIS and not p.y > 0:
            errs.append(f"{p.ref} is Cis but CAD Y <= 0")
        if p.side == TRANS and not p.y < 0:
            errs.append(f"{p.ref} is Trans but CAD Y >= 0")
        if p.shape not in (CIRCLE, SQUARE):
            errs.append(f"{p.ref} bad shape {p.shape}")
        if p.ring not in (None, GUARD, GUARD_WIDE, GNDA):
            errs.append(f"{p.ref} bad ring {p.ring}")
        if p.net in HIGH_Z_NETS and p.ring is None:
            errs.append(f"{p.ref} ({p.net}) is high-Z but has no ring")
        if p.role == "signal" and p.ring is None:
            errs.append(f"{p.ref} signal pin has no ring")

    # Every ring net in use must have at least one feeder pin on the same side
    # group and that feeder must exist.
    for ring in {p.ring for p in PINS if p.ring}:
        feeders = RING_FEEDERS.get(ring, ())
        if not feeders:
            errs.append(f"ring {ring} has no feeder pin (interposer ring would float)")
        for f in feeders:
            try:
                pin(f)
            except KeyError:
                errs.append(f"ring {ring} feeder P{f} does not exist")
    for ring, feeders in RING_FEEDERS.items():
        for f in feeders:
            fp = pin(f)
            if fp.role == "signal":
                errs.append(f"ring {ring} feeder {fp.ref} is a signal pin")

    for a, b in itertools.combinations(PINS, 2):
        d = ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
        need = site_radius(a.ring) + site_radius(b.ring) + PAD_CLEARANCE
        if d < need - 1e-9:
            errs.append(f"{a.ref}-{b.ref} pitch {d:.2f} mm < required {need:.2f} mm")

    # Clearance to fluid channels and ports
    # Channel width = 1.4 mm (half-width 0.7 mm)
    channel_half_w = 0.7
    min_channel_clearance = 2.0  # mm minimum copper-to-fluid-boundary clearance
    for p in PINS:
        r_site = site_radius(p.ring)
        # Distance to Cis line: x - sqrt(3)*y = 0
        d_cis = abs(p.x - math.sqrt(3.0) * p.y) / 2.0 - channel_half_w - r_site
        # Distance to Trans line: x + sqrt(3)*y = 0
        d_trans = abs(p.x + math.sqrt(3.0) * p.y) / 2.0 - channel_half_w - r_site
        if d_cis < min_channel_clearance:
            errs.append(f"{p.ref} too close to Cis channel: clearance {d_cis:.2f} mm < {min_channel_clearance:.2f} mm")
        if d_trans < min_channel_clearance:
            errs.append(f"{p.ref} too close to Trans channel: clearance {d_trans:.2f} mm < {min_channel_clearance:.2f} mm")

        for hid, hpos in FLUID_HOLES.items():
            dh = math.hypot(p.x - hpos[0], p.y - hpos[1]) - (FLUID_DRILL_DIA / 2.0) - r_site
            if dh < min_channel_clearance:
                errs.append(f"{p.ref} too close to fluid hole {hid}: clearance {dh:.2f} mm < {min_channel_clearance:.2f} mm")

    lo, hi = gap_window()
    gap = pin_gap(stack)
    if not lo - 1e-9 <= gap <= hi + 1e-9:
        errs.append(f"pin gap {gap:.3f} mm outside allowed window [{lo:.3f}, {hi:.3f}] mm")
    if PRINTED_MIN > stack.printed or stack.printed > PRINTED_MAX:
        errs.append(f"printed spacer {stack.printed} outside [{PRINTED_MIN}, {PRINTED_MAX}]")

    if set(FLUID_HOLES) != {"H1", "H2", "H3", "H4"}:
        errs.append("fluid holes must be H1..H4")
    return errs


def assert_valid(stack: SpacerStack = DEFAULT_SPACERS) -> None:
    errs = validate(stack)
    if errs:
        raise ValueError("stack_spec invalid:\n  " + "\n  ".join(errs))
