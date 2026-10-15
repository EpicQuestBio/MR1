# Handoff Report: CAD Housing & Cavity Integration Survey (Explorer 1)

## 1. Observation

1. **CAD Model Definition Files**:
   - `src/housing.py` (lines 252–255): `Housing_Lid_Reader` defines:
     ```python
     # Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
     with Locations((0.0, -27.5, -ceiling_thick / 2.0)):
         Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)
     ```
   - `src/common.py` (lines 16–17): `Circuitry_Cutouts` defines:
     ```python
     # Ribbon Cable Clearance Channel against hexagon wall
     with Locations((0, -27.5, 0)):
         Box(13.5, 3.0, height)
     ```
   - `src/cartridge.py`: `Circuitry_Cutouts` is subtracted from `Bottom_Pusher_Plate` (line 351), `Plate_1_Base_Hex` (line 376), and `Fitted_Amplifier_Gasket` (line 319).
   - `src/main.py` (lines 23–116): Implements `export_all()` which exports 30 3D solids to STEP/STL and 13 2D profiles to DXF.

2. **Staged CAD Export Discrepancy on Disk**:
   - Running boolean subtraction between live BREP `Housing_Lid_Reader()` and `import_step("exports/Housing_Lid_Reader.step")`:
     `missing = step_lid.cut(lid)`
     **Output**: `In step lid but not in current lid: 2001.1201999589093 mm^3, BB: bbox: -6.75 <= x <= 6.75, -29.0 <= y <= -26.0, -27.5 <= z <= 22.6`.
   - The staged STEP/STL files on disk do NOT have the $13.5\text{ mm} \times 3.0\text{ mm}$ cavity; they contain solid material in this exact box.
   - Current hashes in `exports/manifest.json`:
     - `Housing_Lid_Reader.step`: `ad48a7156ea6f3079a3aad4bca71a428106c31ddba5ada1f959ce9da617c8e71`
     - `Housing_Lid_Reader.stl`: `1fc7fd0939e72bd32e2349fe63175247526dadd3265f091e0ac27f4cdfc10168`

3. **Collision Detection Bug in `src/collision_check.py`**:
   - Lines 23–24:
     ```python
     overlap_shape = part_a.intersect(part_b)
     vol = overlap_shape.volume
     ```
   - When `overlap_shape` is a `ShapeList` (multiple solids returned by OpenCASCADE intersection), accessing `.volume` throws `AttributeError: 'ShapeList' object has no attribute 'volume'`. Line 32 catches all exceptions and silently returns `False, 0.0`.

4. **Geometry Tests Execution**:
   - Command: `.venv/bin/python -m unittest tests/test_geometry.py tests/test_golden_stl_bounds.py tests/test_legacy_feature_parity.py`
     **Result**: `Ran 27 tests in 31.745s - OK`
   - Command: `.venv/bin/python run_tests.py`
     **Result**: `Ran 92 tests in 28.517s - FAILED (failures=2)`
     The only 2 failures are in `tests/test_exports_e2e.py` (`Missing firmware.bin in exports/firmware/` and `Missing reader_wiring directory`). All CAD, geometry, FEA, and simulation tests pass.

---

## 2. Logic Chain

1. **Geometric Non-Interference**:
   - The cartridge stack hex boundary has circumradius $R = 30.0\text{ mm}$, flat-to-flat distance $51.9615\text{ mm}$, and bottom flat at $Y = -25.9808\text{ mm}$ (Obs 1).
   - The housing lid socket has circumradius $R = 30.5\text{ mm}$, flat-to-flat distance $52.827\text{ mm}$, and socket wall flat at $Y = -26.4137\text{ mm}$ (Obs 1).
   - The ribbon cable cavity is centered at $Y = -27.5\text{ mm}$ with depth $3.0\text{ mm}$, spanning $Y \in [-29.0, -26.0]\text{ mm}$ and $X \in [-6.75, +6.75]\text{ mm}$ (Obs 1).
   - Because $Y_{\text{inner}} = -26.0\text{ mm}$ is strictly less than $Y_{\text{cartridge}} = -25.9808\text{ mm}$, there is a $19.2\ \mu\text{m}$ clearance gap.
   - The cavity penetrates $2.586\text{ mm}$ into the solid housing neck wall ($Y \in [-29.0, -26.4137]\text{ mm}$).
   - Therefore, the cavity accommodates the ribbon cable passing from the amplifier PCBA through the wall without colliding with the cartridge stack or compromising the gasket fluidic seals ($R \le 11\text{ mm}$).

2. **Root Cause of Acceptance Criteria Failure**:
   - The Python model in `src/housing.py` already includes the $13.5\text{ mm} \times 3.0\text{ mm}$ cavity at $Y = -27.5\text{ mm}$ (Obs 1).
   - However, `exports/Housing_Lid_Reader.step` and `exports/Housing_Lid_Reader.stl` on disk were exported prior to adding this feature, as demonstrated by the missing $2001.12\text{ mm}^3$ volume in the STEP diff (Obs 2).
   - The implementation step must re-run `python src/main.py all` (or `python scripts/export_manager.py --cad`) followed by `python scripts/export_manager.py --manifest` to synchronize the exported solids and manifest checksums.

3. **Collision Tooling Reliability**:
   - Because `check_overlap` in `src/collision_check.py` fails on `ShapeList` objects due to an unhandled `AttributeError` (Obs 3), complex multi-solid contacts can silently report zero collision. Hardening `check_overlap` ensures accurate collision detection across future assembly modifications.

---

## 3. Caveats

1. The KiCad PCB Edge.Cuts contour alignment in `Amplifier/Amplifier.kicad_pcb` is being surveyed in depth by Explorer 2. Our survey verified that the CAD `Hex_Base_Sketch` matches KiCad flat dimensions ($55.0034\text{ mm} \times 51.9616\text{ mm}$), and that KiCad Edge.Cuts currently forms a closed loop of 66 segments with 0 degree != 2 endpoints.
2. Firmware binaries and WireViz deliverables are outside Explorer 1 scope and are being surveyed by Explorer 3.

---

## 4. Conclusion

The CAD models in `src/housing.py` and `src/cartridge.py` are geometrically sound and correctly position the $13.5\text{ mm} \times 3.0\text{ mm}$ ribbon cable cavity at $Y = -27.5\text{ mm}$, recessed $2.586\text{ mm}$ into the amplifier hexagon wall with $19.2\ \mu\text{m}$ radial clearance to the cartridge stack.
The primary actions needed for the implementer are:
1. Fix the `ShapeList` volume check in `src/collision_check.py`.
2. Start the inner hex socket cutout at $Z = 0.0$ in `src/housing.py` so the socket cleanly seats the cartridge stack.
3. Regenerate CAD exports via `python src/main.py all`.
4. Re-generate `exports/manifest.json` via `python scripts/export_manager.py --manifest`.

---

## 5. Verification Method

To independently verify all findings:
1. **Verify Live Model Cavity**:
   ```bash
   .venv/bin/python -m unittest tests/test_legacy_feature_parity.py -k test_housing_lid_reader_legacy_features
   ```
2. **Verify Staged STEP File Stale Status**:
   ```bash
   .venv/bin/python -c "from build123d import *; from src.housing import Housing_Lid_Reader; lid = Housing_Lid_Reader(); step = import_step('exports/Housing_Lid_Reader.step'); diff = step.cut(lid); print('Missing cavity vol:', sum(s.volume for s in diff))"
   ```
   (Outputs `~2001.12 mm^3` missing in the step file on disk).
3. **Verify Geometry Test Suite**:
   ```bash
   .venv/bin/python -m unittest tests/test_geometry.py tests/test_golden_stl_bounds.py tests/test_legacy_feature_parity.py
   ```
4. **Invalidation Condition**:
   If re-exporting `Housing_Lid_Reader.step` causes `test_golden_stl_bounds.py` or `test_geometry.py` to fail, or if overlap volume between `Housing_Lid_Reader` and `PCB_Rigid_Active` exceeds $0.01\text{ mm}^3$.
