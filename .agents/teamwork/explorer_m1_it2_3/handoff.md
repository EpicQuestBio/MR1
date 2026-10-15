# Handoff Report — Build Script Protection & Test Suite Blind Spot Remediation

**Agent**: Explorer 3 (`explorer_m1_it2_3`)  
**Parent Agent**: `854953a8-2b33-4cc9-9231-ad06cd4c5aac`  
**Milestone**: Milestone 1 Iteration 2  
**Date**: 2026-10-15  
**Handoff Type**: Hard (Task Complete)  
**Deliverables Produced**:
- Analysis: `/home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_3/analysis.md`
- Handoff: `/home/loki/Projects/daemon-pore/.agents/teamwork/explorer_m1_it2_3/handoff.md`

---

## 1. Observation

Direct empirical observations and measurements from the repository:

1. **`scripts/build_interposer_kicad.py` (lines 20–91, 275, 387)**:
   - Line 275 unconditionally executes `Path("Interposer/Interposer.kicad_pcb").write_text(...)` and line 387 executes `Path("Interposer/Interposer.kicad_sch").write_text(...)`.
   - `active_refs` (lines 24–29) only filters out 21 legacy references (`U2`, `U16`, `J9`, `R1..R9`, `C1..C6`, `C19`, `C20`, `NT3..NT5`).
   - Line 88 falls back to `retained_fp_blocks.append(fp_txt)` for all other footprints, capturing all newly digitized components from `Amplifier.kicad_pcb` (`U6`, `U13`, `U14`, `R44`, `R46`, `C41`, `D82`, `Q3`, `H2`, `H3`, `J7`).
   - Lines 73–87 expect `J1`, `J2`, `J10`, `J11` in `Amplifier.kicad_pcb`. They are not present in `Amplifier.kicad_pcb`, leaving the generated board without electrode pads.
   - Lines 278–386 generate `Interposer.kicad_sch` using generic library symbols (`Connector_Generic:Conn_01x06`, etc.) instead of dedicated `Interposer:*` symbols.
   - When `.venv/bin/python scripts/build_interposer_kicad.py` is executed, running `.venv/bin/python -m unittest tests/test_interposer_kicad.py` immediately fails with 3 errors:
     ```
     FAIL: test_interposer_footprints_and_active_removal: AssertionError: 'J1' not found in ['R44', 'H2', 'C41', ...]
     FAIL: test_interposer_gnda_copper_flood_and_weep_traces: AssertionError: 0 not greater than or equal to 5 (weep_fcu)
     FAIL: test_interposer_schematic_feature_symbols: AssertionError: 'lib_id "Interposer:PogoPin_Target_6Pin_Array"' not found
     ```

2. **`tests/test_legacy_feature_parity.py` (lines 167–172)**:
   - Ribbon cable probe is defined as:
     ```python
     cable_probe = Solid.make_box(8.0, 2.0, 20.0).move(Location((-4.0, -28.5, -10.0)))
     ```
   - Probe Z bounds: $[-10.0, +10.0]\text{ mm}$.
   - `src/housing.py` `Housing_Lid_Reader` neck cylinder extends to $Z = 5.0 + 25.2 = +30.2\text{ mm}$, while the subtractive box `Box(13.5, 3.0, 55.2)` centered at $Z = -5.0\text{ mm}$ terminates at $Z = +22.6\text{ mm}$.
   - Upper neck region $Z \in [22.6, 30.2]\text{ mm}$ contains $265.35\text{ mm}^3$ of solid plastic obstruction ($121.60\text{ mm}^3$ overlapping with an 8x2 probe).
   - Because the probe capped out at $Z = +10.0\text{ mm}$, `lid.intersect(cable_probe)` returned volume $0.000\text{ mm}^3$, masking the upper neck obstruction.

3. **`tests/test_interposer_kicad.py` & PCB Cavity Envelope**:
   - In `Amplifier/Amplifier.kicad_pcb` lines 58221–58700, 67 `filled_polygon` coordinate vertices (37 on `F.Cu`, 30 on `B.Cu`) reside within $X \in [157.75, 171.25], Y \in [81.475, 84.475]\text{ mm}$.
   - In `Interposer/Interposer.kicad_pcb`, `Edge.Cuts` was not updated to $13.5\text{ mm} \times 3.0\text{ mm}$ (it retains the old $12.0\text{ mm} \times 2.5\text{ mm}$ cavity), and graph degree analysis revealed 4 open degree-1 endpoints at $(158.5, 81.99)$ vs $(158.5, 81.994)$ and $(170.5, 81.99)$ vs $(170.5, 81.994)$.
   - `test_interposer_kicad.py` contains no assertions testing copper elements (`segment`, `via`, `filled_polygon`) in the cavity envelope, and only checks `Edge.Cuts` on `Amplifier.kicad_pcb`, ignoring `Interposer.kicad_pcb`.

---

## 2. Logic Chain

1. **Why `scripts/build_interposer_kicad.py` must be protected**:
   - `Interposer/` files are not transient build products; they are production hardware files with manual/verified routing and 4-electrode Gamry circuitry directly referenced by `scripts/export_manager.py`.
   - The script was written for an obsolete repo state and lacks CLI safety guards. Any invocation without arguments clobbers production design files.
   - Enforcing a default dry-run mode and requiring `--write` ensures no automated script or engineer can accidentally clobber `Interposer/`.
   - Updating the script's internal logic ensures that if `--write` is invoked, it synchronizes Edge.Cuts without clobbering the 4-electrode cell, footprints, and dedicated schematic symbols.

2. **Why `tests/test_legacy_feature_parity.py` missed the neck obstruction**:
   - Testing only $Z \in [-10.0, 10.0]\text{ mm}$ left the upper $20.2\text{ mm}$ of the neck ($Z \in [10.0, 30.2]\text{ mm}$) unprobed.
   - Extending the probe across the full vertical pass-through ($Z \in [-10.0, 30.2]\text{ mm}$) and adding a dedicated upper neck check ($Z \in [22.0, 30.2]\text{ mm}$) guarantees permanent detection of neck cavity blockages.

3. **Why `tests/test_interposer_kicad.py` must check copper and Interposer Edge.Cuts**:
   - Modifying `Edge.Cuts` in KiCad files without updating or clearing pre-calculated `filled_polygon` blocks leaves copper islands inside mechanical cutouts.
   - An explicit test asserting 0 segments, 0 vias, and 0 filled polygon vertices in $[157.75, 171.25] \times [81.475, 84.475]\text{ mm}$ catches stale copper immediately.
   - Checking `Interposer/Interposer.kicad_pcb`'s `Edge.Cuts` graph degree enforces that both boards have continuous, closed loops matching the 13.5mm cavity.

---

## 3. Caveats

1. **Read-Only Investigation**:
   In strict accordance with the explorer role, no source code, test files, or PCB design files in the repository were modified. Proposed code changes and test additions are provided as implementation blueprints.
2. **KiCad Zone Refilling**:
   KiCad CLI does not offer an in-place zone recalculation command for `.kicad_pcb` without running an export or DRC. The implementing worker can either remove/clip the stale filled polygon coordinates in text or use `kicad-cli pcb export gerbers --check-zones` or KiCad GUI zone re-pour.

---

## 4. Conclusion

1. **`scripts/build_interposer_kicad.py` Safeguard Blueprint**:
   - Integrate `argparse`: default to dry-run (exit 0, no file modifications).
   - Require `--write` to modify `Interposer/Interposer.kicad_pcb` and `Interposer/Interposer.kicad_sch`.
   - Support `--out-dir <path>` for isolated generation/previewing.
   - Synchronize definitions to preserve `Interposer/` 4-electrode architecture, footprints, and dedicated schematic symbols.
2. **`tests/test_legacy_feature_parity.py` Extension**:
   - Add `_get_shape_volume()` helper to safely sum `ShapeList` / `Compound` objects.
   - Extend `cable_probe` to $Z \in [-10.0, 30.2]\text{ mm}$ (height 40.2mm).
   - Add explicit upper neck test probe spanning $Z \in [22.0, 30.2]\text{ mm}$.
3. **`tests/test_interposer_kicad.py` Extension**:
   - Add `test_pcb_cavity_copper_clearance` asserting 0 traces, vias, or filled polygon points inside $[157.75, 171.25] \times [81.475, 84.475]\text{ mm}$ across both `Amplifier` and `Interposer`.
   - Add `test_interposer_pcb_edge_cuts_continuity` asserting 0 non-2 degree vertices, 1 continuous component, and 13.5mm x 3.0mm cavity floor on `Interposer.kicad_pcb`.

---

## 5. Verification Method

To independently verify all findings and test proposals:

1. **Verify `scripts/build_interposer_kicad.py` Behavior**:
   ```bash
   # Check that running without args currently modifies Interposer/:
   git status --porcelain Interposer/
   .venv/bin/python scripts/build_interposer_kicad.py
   git status --porcelain Interposer/ # Shows modified files
   git restore Interposer/
   ```

2. **Verify Upper Neck Blockage in `tests/test_legacy_feature_parity.py`**:
   ```bash
   .venv/bin/python -c "
   from build123d import *
   from src.housing import Housing_Lid_Reader
   lid = Housing_Lid_Reader()
   probe_full = Solid.make_box(8.0, 2.0, 40.2).move(Location((-4.0, -28.5, -10.0)))
   inter = lid.intersect(probe_full)
   vol = sum(getattr(s, 'volume', 0.0) for s in inter) if hasattr(inter, '__iter__') else getattr(inter, 'volume', 0.0)
   print(f'Blocked volume in cavity: {vol:.4f} mm^3')
   assert vol > 100.0, 'Expected >100 mm^3 blockage in neck'
   "
   ```

3. **Verify Stale Copper Flood in `Amplifier.kicad_pcb`**:
   ```bash
   .venv/bin/python -c "
   import re
   from pathlib import Path
   txt = Path('Amplifier/Amplifier.kicad_pcb').read_text()
   fps = re.findall(r'\(filled_polygon[\s\S]*?\n\t\t\)', txt)
   pts = [p for fp in fps for p in re.findall(r'\(xy\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', fp)]
   in_cav = [(float(x), float(y)) for x, y in pts if 157.75 <= float(x) <= 171.25 and 81.475 <= float(y) <= 84.475]
   print(f'Cavity copper points in Amplifier: {len(in_cav)}')
   assert len(in_cav) == 67
   "
   ```

4. **Verify Disconnected Degree-1 Vertices in `Interposer.kicad_pcb`**:
   ```bash
   .venv/bin/python -c "
   import re
   from collections import defaultdict
   from pathlib import Path
   txt = Path('Interposer/Interposer.kicad_pcb').read_text()
   lines = txt.splitlines()
   blocks, cur, in_b = [], [], False
   for l in lines:
       if l.startswith('\t(gr_line') or l.startswith('\t(gr_arc'):
           in_b = True; cur = [l]
       elif in_b:
           cur.append(l)
           if l.startswith('\t)'):
               in_b = False; blocks.append('\n'.join(cur))
   ec_blocks = [b for b in blocks if '(layer \"Edge.Cuts\")' in b]
   segs = []
   for b in ec_blocks:
       sm = re.search(r'\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', b)
       em = re.search(r'\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', b)
       if sm and em:
           segs.append(((round(float(sm.group(1)), 3), round(float(sm.group(2)), 3)), (round(float(em.group(1)), 3), round(float(em.group(2)), 3))))
   adj = defaultdict(list)
   for p1, p2 in segs:
       adj[p1].append(p2); adj[p2].append(p1)
   non_2 = {k: len(v) for k, v in adj.items() if len(v) != 2}
   print(f'Interposer non-2 degree nodes: {len(non_2)}')
   assert len(non_2) == 4
   "
   ```
