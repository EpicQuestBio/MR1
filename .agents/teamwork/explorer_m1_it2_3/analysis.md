# Technical Analysis Report: Build Script Protection & Test Suite Blind Spot Remediation

**Author**: Explorer 3 (`explorer_m1_it2_3`)  
**Parent Agent**: `854953a8-2b33-4cc9-9231-ad06cd4c5aac`  
**Milestone**: Milestone 1 Iteration 2  
**Date**: 2026-10-15  
**Working Directory**: `/home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_3`  
**Scope**: Read-only investigation and proposal  

---

## Executive Summary

Following Challenger 2's rejection of Milestone 1 Iteration 1, this investigation performed an in-depth code and physical geometry analysis of:
1. **The destructive overwrite behavior of `scripts/build_interposer_kicad.py`**, which clobbers authoritative production design files in `Interposer/` and induces 3 unit test failures in `tests/test_interposer_kicad.py`.
2. **Two major test suite blind spots**:
   - `tests/test_legacy_feature_parity.py` ribbon cable cavity probe height $Z \in [-10.0, 10.0]\text{ mm}$ failing to reach the upper neck plastic obstruction in $Z \in [22.6, 30.2]\text{ mm}$ ($265.35\text{ mm}^3$ collision).
   - `tests/test_interposer_kicad.py` failing to assert copper zone clearance inside the cavity envelope, allowing 67 stale copper vertices in `Amplifier/Amplifier.kicad_pcb` to pass undetected, alongside missing Edge.Cuts checks on `Interposer/Interposer.kicad_pcb` (which retains 4 open degree-1 endpoints and the outdated 12.0 mm cavity).

This report specifies the concrete architecture to safeguard `scripts/build_interposer_kicad.py`, synchronize its definitions, and expand test coverage across `tests/test_legacy_feature_parity.py` and `tests/test_interposer_kicad.py`.

---

## 1. Investigation of `scripts/build_interposer_kicad.py`

### 1.1 Root Cause of Destructive Overwrite
In commit `8106d73`, `scripts/build_interposer_kicad.py` was introduced as an initial prototype script to bootstrap `Interposer/Interposer.kicad_pcb` and `Interposer/Interposer.kicad_sch` by filtering out active components from an early iteration of `Amplifier.kicad_pcb`.

Since that initial bootstrap:
1. **Evolution of `Interposer/` into Authoritative Design Assets**:
   In commits `96b4287` and `e152223`, `Interposer/` evolved into a dedicated 4-electrode Gamry architecture (WE_POS, WS_CIS, RE_TRANS, CE_GNDA, WEEP_SENSE) with dedicated symbol libraries (`Interposer.kicad_sym`), custom footprints (`Electrode_Guard_Shield`, `PogoPin_Target_6Pin_Array`), and full-board GNDA ground flood planes.
   In `scripts/export_manager.py` (lines 122–128), `Interposer` is registered as one of the four first-class production boards directly exported by KiCad CLI.
2. **Obsolete Component Blacklist in `build_interposer_kicad.py`**:
   Lines 24–29 define `active_refs`:
   ```python
   active_refs = {
       "U2", "U16", "J9",
       "R1", "R3", "R4", "R5", "R6", "R8", "R9",
       "C1", "C2", "C3", "C4", "C5", "C6", "C19", "C20",
       "NT3", "NT4", "NT5"
   }
   ```
   When `Amplifier/Amplifier.kicad_pcb` was subsequently upgraded with digitized ADC circuitry and weep sense buffers (`U6`, `U13`, `U14`, `R44`, `R46`, `C41`, `D82`, `Q3`, `H2`, `H3`, `J7`), none of these new references were included in `active_refs`. Because lines 88–90 contain an unconditional fallback:
   ```python
   else:
       # Any other footprint
       retained_fp_blocks.append(fp_txt)
   ```
   All 40+ active components from `Amplifier.kicad_pcb` are retained and written onto `Interposer.kicad_pcb`.
3. **Missing Retained Footprints**:
   `retained_refs` expects `{"H1", "J1", "J2", "J10", "J11"}` in `Amplifier.kicad_pcb`. Because `J1, J2, J10, J11` only exist in `Interposer.kicad_pcb` (not `Amplifier`), the generated board has no electrode footprints at all.
4. **Obsolete Schematic Generator**:
   Lines 296–368 generate `Interposer.kicad_sch` using generic symbols (`Connector_Generic:Conn_01x06`, `Connector_Generic:Conn_01x02`, `Mechanical:MountingHole`) instead of dedicated `Interposer:*` symbols required by `test_interposer_schematic_feature_symbols`.
5. **Unconditional File Overwrites**:
   - Line 275: `Path("Interposer/Interposer.kicad_pcb").write_text(...)`
   - Line 387: `Path("Interposer/Interposer.kicad_sch").write_text(...)`
   Simply running `.venv/bin/python scripts/build_interposer_kicad.py` immediately overwrites both production assets with corrupted data, causing 3 test failures in `tests/test_interposer_kicad.py`.

### 1.2 Protection Architecture & CLI Interface
To permanently eliminate the risk of accidental clobbering:
1. **Dry-Run by Default**:
   Running `scripts/build_interposer_kicad.py` with zero arguments must NOT modify any file in `Interposer/`. Instead, it must print an informative safeguard notice explaining that `Interposer/` contains authoritative design files and exit with code 0.
2. **Explicit `--write` Flag**:
   Overwriting `Interposer/Interposer.kicad_pcb` and `Interposer/Interposer.kicad_sch` must require an explicit `--write` flag.
3. **Optional `--out-dir <PATH>` Flag**:
   Allows generating/previewing output files in an arbitrary directory (e.g. `exports/preview_interposer/` or a temporary directory) without touching `Interposer/`.

### 1.3 Proposed Code Changes for `scripts/build_interposer_kicad.py`

#### A. CLI Flag Parsing & Safe Dispatch
```python
import argparse
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(
        description="Daemon Pore Interposer KiCad Synchronization Utility.\n"
                    "NOTE: 'Interposer/' contains authoritative production design files."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly allow overwriting authoritative files in Interposer/."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory to write generated output files (does not touch Interposer/ unless specified)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing any files (default behavior when --write and --out-dir are omitted)."
    )
    return parser.parse_args()
```

#### B. Synchronized PCB & Schematic Handling
When writing is explicitly requested via `--write` or `--out-dir`:
1. **Edge.Cuts Alignment without Clobbering Footprints**:
   Rather than attempting to reconstruct the complex 14,800-line interposer from `Amplifier.kicad_pcb` via obsolete regex stripping, the synchronizer should read `Interposer/Interposer.kicad_pcb` as the base, extract the updated cavity segments from `Amplifier/Amplifier.kicad_pcb` (`Edge.Cuts` coordinates around $Y \in [81.0, 85.0]$: $X \in [157.75, 171.25]$ down to $Y = 81.475044$), and replace the cavity lines in `Interposer.kicad_pcb`.
2. **Footprint Whitelisting**:
   If footprint rebuilding is performed, use a strict whitelist:
   `ALLOWED_INTERPOSER_REFS = {"H1", "J_POGO1", "J1", "J2", "J10", "J11", "P1", "P2", "P3", "P4", "W1"}`. Any footprint outside this whitelist is rejected.
3. **Schematic Symbol Alignment**:
   `build_interposer_sch` must emit dedicated library references:
   - `lib_id "Interposer:PogoPin_Target_6Pin_Array"`
   - `lib_id "Interposer:Nanopore_Wafer_Aperture"`
   - `lib_id "Interposer:Electrode_Guard_Shield"`
   - `lib_id "Interposer:Weep_Moat_Sensor"`
   - `lib_id "Interposer:Fluidic_Port_PassThrough"`
   Or preserve `Interposer/Interposer.kicad_sch`.

---

## 2. Investigation & Remediation of Test Suite Blind Spots

### 2.1 Blind Spot 1: Upper Neck Blockage in `tests/test_legacy_feature_parity.py`

#### Empirical Analysis
- In `src/housing.py` (`Housing_Lid_Reader`):
  - Base body ceiling thickness: `ceiling_thick = 10.0`.
  - Neck length: `neck_length = 25.2`.
  - Neck top surface is at $Z = 5.0 + neck\_length = +30.2\text{ mm}$.
  - The subtractive box on lines 263–264 is:
    ```python
    with Locations((0.0, -27.5, -ceiling_thick / 2.0)):
        Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)
    ```
  - Center of box: $Z = -5.0\text{ mm}$.
  - Total height: $H = 25.2 + 30.0 = 55.2\text{ mm}$.
  - Upper bounding limit: $Z_{max} = -5.0 + 55.2 / 2.0 = +22.6\text{ mm}$.
  - **Plastic obstruction**: Solid plastic occupies the cavity volume for $Z \in [22.6, 30.2]\text{ mm}$ ($7.6\text{ mm}$ height, $265.35\text{ mm}^3$ volume).

#### Cause of the Test Blind Spot
In `tests/test_legacy_feature_parity.py` (lines 167–172):
```python
cable_probe = Solid.make_box(8.0, 2.0, 20.0).move(Location((-4.0, -28.5, -10.0)))
inter_cable = lid.intersect(cable_probe)
vol_cable = inter_cable.volume if inter_cable is not None else 0.0
self.assertLess(vol_cable, 0.5, "Housing_Lid_Reader is missing ribbon cable cavity at (0, -27.5).")
```
- Probe extents: $X \in [-4.0, 4.0]$, $Y \in [-28.5, -26.5]$, $Z \in [-10.0, +10.0]\text{ mm}$.
- Because the probe capped out at $Z = +10.0\text{ mm}$, it evaluated strictly inside the clear region ($Z \le 22.6\text{ mm}$).
- The test was completely blind to the upper $20.2\text{ mm}$ of the neck ($Z \in [10.0, 30.2]\text{ mm}$).

#### Proposed Test Coverage Extension
In `tests/test_legacy_feature_parity.py`:
1. Implement a helper `_shape_volume(shape)` to handle both `Solid` and `ShapeList` / `Compound` results from `lid.intersect()` without throwing `AttributeError`.
2. Expand the probe to cover the full vertical pass-through span of the neck and ceiling: $Z \in [-10.0, 30.2]\text{ mm}$ (height $40.2\text{ mm}$).
3. Add a dedicated assertion testing the upper neck region $Z \in [22.0, 30.2]\text{ mm}$.

```python
# 2. Test ribbon cable clearance cavity at (0, -27.5) across the full vertical height of lid & neck
# Neck extends to Z = 5.0 + 25.2 = 30.2mm; ceiling extends down to Z = -10.0mm.
def _get_shape_vol(shape):
    if shape is None:
        return 0.0
    if hasattr(shape, "volume"):
        return shape.volume
    if hasattr(shape, "__iter__"):
        return sum(getattr(s, "volume", 0.0) for s in shape)
    return 0.0

# 2a. Full vertical pass-through probe (Z in [-10.0, 30.2] mm)
cable_probe = Solid.make_box(8.0, 2.0, 40.2).move(Location((-4.0, -28.5, -10.0)))
inter_cable = lid.intersect(cable_probe)
vol_cable = _get_shape_vol(inter_cable)
self.assertLess(vol_cable, 0.5,
                f"Housing_Lid_Reader has solid obstruction in ribbon cable cavity (blocked volume: {vol_cable:.4f} mm^3).")

# 2b. Upper neck clearance probe (Z in [22.0, 30.2] mm)
neck_probe = Solid.make_box(8.0, 2.0, 8.2).move(Location((-4.0, -28.5, 22.0)))
inter_neck = lid.intersect(neck_probe)
vol_neck = _get_shape_vol(inter_neck)
self.assertLess(vol_neck, 0.5,
                f"Housing_Lid_Reader has solid obstruction in upper neck ribbon cavity (blocked volume: {vol_neck:.4f} mm^3).")
```

#### Verification against CAD Fix
Changing `src/housing.py` line 264 to:
```python
with Locations((0.0, -27.5, 0.0)):
    Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)
```
drops `vol_cable` and `vol_neck` to exactly `0.0000 mm^3`.

---

### 2.2 Blind Spot 2: Stale Copper Flood Points in `tests/test_interposer_kicad.py`

#### Empirical Analysis
1. **`Amplifier/Amplifier.kicad_pcb`**:
   - `Edge.Cuts` was moved from $X \in [158.5, 170.5]$ to $[157.75, 171.25]$ and floor from $Y = 81.99$ to $81.475044$.
   - The cached `(filled_polygon (pts ...))` blocks in lines 58221–58700 were not refilled.
   - Exact measurement: 67 coordinate vertices (37 on `F.Cu`, 30 on `B.Cu`) sit inside $[157.75, 171.25] \times [81.475, 84.475]\text{ mm}$.
   - If widened to the contract envelope $[157.5, 171.5] \times [81.3, 85.0]$, 79 vertices are present.
2. **`Interposer/Interposer.kicad_pcb`**:
   - `Edge.Cuts` was never updated in Iteration 1. It still possesses the older 12.0 mm cavity ($X \in [158.5, 170.5], Y_{floor} = 81.99$).
   - Graph continuity analysis revealed 4 open degree-1 endpoints due to a 4-micron gap:
     - `(158.5, 81.99)` vs `(158.5, 81.994)`
     - `(170.5, 81.99)` vs `(170.5, 81.994)`
   - The test `test_amplifier_pcb_edge_cuts_continuity` only inspected `Amplifier.kicad_pcb`, completely missing the defects in `Interposer.kicad_pcb`.

#### Proposed Test Coverage Extension
In `tests/test_interposer_kicad.py`, add two comprehensive test methods:

#### A. Copper Clearance Test (`test_pcb_cavity_copper_clearance`)
Checks traces, vias, and zone filled polygon vertices against the cavity boundary across both `Amplifier.kicad_pcb` and `Interposer.kicad_pcb`:
```python
def test_pcb_cavity_copper_clearance(self):
    """Ensure no copper traces, vias, or zone filled_polygon points intrude into
    the ribbon cable cavity envelope [157.75, 171.25] x [81.475, 84.475]mm in
    Amplifier.kicad_pcb and Interposer.kicad_pcb."""
    cavity_x_min = 157.75
    cavity_x_max = 171.25
    cavity_y_min = 81.475
    cavity_y_max = 84.475

    for pcb_name, pcb_rel in [("Amplifier", "Amplifier/Amplifier.kicad_pcb"), ("Interposer", "Interposer/Interposer.kicad_pcb")]:
        pcb_path = REPO_ROOT / pcb_rel
        self.assertTrue(pcb_path.exists(), f"{pcb_rel} must exist")
        txt = pcb_path.read_text(encoding="utf-8")

        # 1. Traces inside cavity
        segments = re.findall(r'\(segment\s+\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', txt)
        intruding_segments = []
        for x1, y1, x2, y2 in segments:
            p1_in = (cavity_x_min < float(x1) < cavity_x_max) and (cavity_y_min < float(y1) < cavity_y_max)
            p2_in = (cavity_x_min < float(x2) < cavity_x_max) and (cavity_y_min < float(y2) < cavity_y_max)
            if p1_in or p2_in:
                intruding_segments.append(((x1, y1), (x2, y2)))
        self.assertEqual(len(intruding_segments), 0,
                         f"{pcb_name} PCB has traces inside cavity envelope: {intruding_segments}")

        # 2. Vias inside cavity
        vias = re.findall(r'\(via\s+\(at\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', txt)
        intruding_vias = [v for v in vias if (cavity_x_min < float(v[0]) < cavity_x_max and cavity_y_min < float(v[1]) < cavity_y_max)]
        self.assertEqual(len(intruding_vias), 0,
                         f"{pcb_name} PCB has vias inside cavity envelope: {intruding_vias}")

        # 3. Zone filled_polygon vertices inside cavity
        fps = re.findall(r'\(filled_polygon[\s\S]*?\n\t\t\)', txt)
        intruding_copper_pts = []
        for fp in fps:
            for x_str, y_str in re.findall(r'\(xy\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', fp):
                x, y = float(x_str), float(y_str)
                if cavity_x_min < x < cavity_x_max and cavity_y_min < y < cavity_y_max:
                    intruding_copper_pts.append((x, y))
        self.assertEqual(len(intruding_copper_pts), 0,
                         f"{pcb_name} PCB has {len(intruding_copper_pts)} copper filled_polygon points inside cavity envelope (e.g. {intruding_copper_pts[:5]})")
```

#### B. Interposer Edge.Cuts Continuity Test (`test_interposer_pcb_edge_cuts_continuity`)
Validates that `Interposer/Interposer.kicad_pcb` matches the 13.5 mm x 3.0 mm cavity and forms a strictly closed 2-regular loop:
```python
def test_interposer_pcb_edge_cuts_continuity(self):
    """Verify that Interposer/Interposer.kicad_pcb Edge.Cuts forms a continuous closed loop
    with 0 vertices of degree != 2, 0 floating lines, and matches the 13.5x3.0mm cavity."""
    pcb_path = REPO_ROOT / "Interposer" / "Interposer.kicad_pcb"
    self.assertTrue(pcb_path.exists(), "Interposer.kicad_pcb must exist")

    text = pcb_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks = []
    cur = []
    in_b = False
    for l in lines:
        if l.startswith("\t(gr_line") or l.startswith("\t(gr_arc"):
            in_b = True
            cur = [l]
        elif in_b:
            cur.append(l)
            if l.startswith("\t)"):
                in_b = False
                blocks.append("\n".join(cur))

    ec_blocks = [b for b in blocks if '(layer "Edge.Cuts")' in b]
    self.assertGreater(len(ec_blocks), 0, "Edge.Cuts layer must contain segments")

    segs = []
    for b in ec_blocks:
        sm = re.search(r"\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)", b)
        em = re.search(r"\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)", b)
        self.assertIsNotNone(sm, f"Segment missing start coordinates: {b}")
        self.assertIsNotNone(em, f"Segment missing end coordinates: {b}")
        p1 = (round(float(sm.group(1)), 3), round(float(sm.group(2)), 3))
        p2 = (round(float(em.group(1)), 3), round(float(em.group(2)), 3))
        self.assertNotEqual(p1, p2, f"Degenerate zero-length segment: {b}")
        segs.append((p1, p2))

    adj = defaultdict(list)
    for p1, p2 in segs:
        adj[p1].append(p2)
        adj[p2].append(p1)

    # 1. Degree check: 0 endpoints with degree != 2
    non_2 = {k: len(v) for k, v in adj.items() if len(v) != 2}
    self.assertEqual(len(non_2), 0, f"Found {len(non_2)} vertices with degree != 2 in Interposer: {non_2}")

    # 2. Cavity verification (13.5mm x 3.0mm cavity recessed into hexagon wall)
    cavity_floor = [(p1, p2) for p1, p2 in segs if (p1[1] == 81.475 and p2[1] == 81.475)]
    self.assertEqual(len(cavity_floor), 1, "Interposer must have exactly 1 cavity floor segment at Y=81.475mm")
    cp1, cp2 = cavity_floor[0]
    x_min, x_max = min(cp1[0], cp2[0]), max(cp1[0], cp2[0])
    self.assertAlmostEqual(x_max - x_min, 13.5, delta=0.01, msg=f"Cavity width must be 13.5mm, got {x_max - x_min}")
    self.assertAlmostEqual((x_min + x_max) / 2.0, 164.5, delta=0.01, msg="Cavity must be centered at X=164.5mm")
```

---

## 3. Summary of Implementation Recommendations for Worker

| Target File | Recommended Action | Purpose |
|-------------|-------------------|---------|
| `scripts/build_interposer_kicad.py` | Add `argparse` with `--write`, `--out-dir`, and `--dry-run` default; synchronize definitions. | Prevent catastrophic overwrite of `Interposer/` design assets when run without `--write`. |
| `src/housing.py` (line 264) | Change cutout to `with Locations((0.0, -27.5, 0.0)): Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)`. | Eliminate $265.35\text{ mm}^3$ solid plastic obstruction in upper neck ($Z \in [22.6, 30.2]\text{ mm}$). |
| `Amplifier/Amplifier.kicad_pcb` | Re-flood / prune copper zone `filled_polygon` points inside $X \in [157.75, 171.25], Y \in [81.475, 84.475]$. | Eliminate 67 points of stale copper fill invading the ribbon cable clearance volume. |
| `Interposer/Interposer.kicad_pcb` | Update `Edge.Cuts` cavity contour to $13.5\text{ mm} \times 3.0\text{ mm}$ and resolve the 4 degree-1 gap vertices. | Restore closed boundary and align cavity with housing. |
| `tests/test_legacy_feature_parity.py` | Extend `cable_probe` to $Z \in [-10.0, 30.2]$ and add upper neck probe $Z \in [22.0, 30.2]$. | Permanently catch neck blockage regressions. |
| `tests/test_interposer_kicad.py` | Add `test_pcb_cavity_copper_clearance` and `test_interposer_pcb_edge_cuts_continuity`. | Permanently prevent copper intrusion and Interposer Edge.Cuts disconnects. |

---

## 4. Verification Commands

1. **Verify `scripts/build_interposer_kicad.py` Protection**:
   ```bash
   # Running without flags should succeed cleanly and NOT modify Interposer/
   git status --porcelain Interposer/
   .venv/bin/python scripts/build_interposer_kicad.py
   git status --porcelain Interposer/ # Must remain empty (0 changes)
   ```

2. **Verify Test Suite Blind Spot Failures on Current Branch**:
   ```bash
   # Run parity probe against current housing.py -> fails on blocked upper neck
   # Run copper clearance check -> fails on 67 copper points in Amplifier.kicad_pcb
   ```
