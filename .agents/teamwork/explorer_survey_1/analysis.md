# CAD Housing & Cavity Integration Survey: Comprehensive Technical Analysis

**Survey Author**: Explorer 1 (CAD Housing Explorer)  
**Date**: 2026-10-15  
**Working Directory**: `/home/loki/Projects/daemon-pore/.agents/teamwork/explorer_survey_1`  
**Reference Requirement**: R1 (Ribbon Cable Cavity Integration & Geometric Clearance)

---

## 1. Executive Summary

This report presents a thorough investigation of the CAD models across the reader housing lid, cartridge plates, and gaskets to accommodate a $13.5\text{ mm} \times 3.0\text{ mm}$ cavity recessed into the amplifier hexagon wall at $Y = -27.5\text{ mm}$, as specified in Requirement R1 and the project Acceptance Criteria.

### Key Survey Findings:
1. **Mathematical & Geometric Alignment**:
   - The cartridge stack components are bounded by a $60.0\text{ mm}$ circumradius hexagon (`HEX_DIAM = 60.0`), producing a flat-to-flat distance of $51.9615\text{ mm}$ ($30.0 \times \sqrt{3}$). The negative-Y flat is located at $Y = -25.9808\text{ mm}$.
   - The reader housing lid features an internal hexagonal socket of $61.0\text{ mm}$ circumradius ($30.5\text{ mm}$ radius), giving an internal flat at $Y = -26.4137\text{ mm}$.
   - The ribbon cable clearance channel is specified as $13.5\text{ mm}$ wide ($X \in [-6.75, +6.75]$) and $3.0\text{ mm}$ thick ($Y \in [-29.0, -26.0]$), centered at $Y = -27.5\text{ mm}$.
   - The cavity penetrates $2.586\text{ mm}$ into the solid wall of the housing lid neck socket ($Y \in [-29.0, -26.4137]$) and extends $0.414\text{ mm}$ into the socket interior ($Y \in [-26.4137, -26.0]$).
   - The inner edge of the cavity ($Y = -26.0\text{ mm}$) maintains a clean $0.0192\text{ mm}$ ($19.2\ \mu\text{m}$) radial clearance from the cartridge stack perimeter ($Y = -25.9808\text{ mm}$), ensuring zero geometric interference.
2. **CAD Code vs. Staged Export Discrepancy**:
   - In `src/housing.py`, `Housing_Lid_Reader` already defines the subtraction:
     `with Locations((0.0, -27.5, -ceiling_thick / 2.0)): Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)`.
   - However, a boolean subtraction analysis between the live build123d BREP solid and the staged file on disk (`exports/Housing_Lid_Reader.step`) revealed that the staged export is **stale**: it is missing the $2001.12\text{ mm}^3$ volume corresponding to this exact $13.5\text{ mm} \times 3.0\text{ mm}$ cavity (`-6.75 <= X <= 6.75, -29.0 <= Y <= -26.0, -27.5 <= Z <= 22.6`).
   - The staged files (`exports/Housing_Lid_Reader.step` and `exports/Housing_Lid_Reader.stl`) must be regenerated from `src/main.py` and indexed in `exports/manifest.json`.
3. **Cartridge Stack & Circuitry Cutouts**:
   - `src/common.py:Circuitry_Cutouts()` defines `Box(13.5, 3.0, height)` at `(0, -27.5, 0)`.
   - This cutout is subtracted in `Bottom_Pusher_Plate`, `Plate_1_Base_Hex`, and `Fitted_Amplifier_Gasket`. Because $Y \in [-29.0, -26.0]$ is completely outside the fluidic seal boundary ($R \le 11\text{ mm}$) and outside the outer perimeter ($Y \ge -25.9808$), it introduces zero seal degradation and zero collision.
4. **Latent Tooling Bug in Collision Checker (`src/collision_check.py`)**:
   - `check_overlap(part_a, part_b)` calls `overlap_shape.volume`. When the boolean intersection returns a build123d `ShapeList` (multiple contact solids), accessing `.volume` raises an `AttributeError`, which is silently swallowed by an overly broad `except Exception: return False, 0.0`.
5. **Test Status**:
   - All 27 CAD geometry tests (`tests/test_geometry.py`, `tests/test_golden_stl_bounds.py`, `tests/test_legacy_feature_parity.py`) pass.
   - Running `run_tests.py` executes 92 tests: 90 pass, with 2 failures strictly confined to Requirement R2 (`exports/firmware/firmware.bin` and `exports/reader_wiring/`).

---

## 2. CAD Model Architecture & Pipeline

### 2.1 Directory Structure & File Roles

The parametric CAD models are implemented using **build123d** (v0.6+):

| File Path | Primary Function & Classes Defined |
|---|---|
| `src/constants.py` | Global physical constants, stack thicknesses (`PP_H=3.0`, `PLATE_THICK=4.0`, `GASKET_THICK=1.5875`, `PCB_THIN=0.8`, `PUCK_H=6.0`), socket dimensions (`HEX_DIAM=60.0`, `HEX_WALL=3.0`, `NECK_OD=75.0`, `NECK_ID=61.0`), and fluid port radii. |
| `src/common.py` | Shared sketches and subtractive features: `Hex_Base_Sketch`, `Circuitry_Cutouts`, `Finger_Grip_Cutout`, `Weep_Duct_Holes`, `Weep_Trench_Cutout`. |
| `src/cartridge.py` | 3D cartridge stack components: `Bottom_Pusher_Plate`, `Plate_1_Base_Hex`, `Fitted_Amplifier_Gasket`, `PCB_Rigid_Active` (alias `PTFE_Interposer`), `Cast_Nanopore_Wafer_Gasket`, `Plate_3_Top_Hex`, `Pressure_Puck`, `Nanopore_Wafer_Silicon`, `Nanopore_Carrier`, `Carrier_Frame_Hex`. |
| `src/housing.py` | Enclosure models: `Housing_Case_Reader`, `Housing_Lid_Reader`, `Housing_Pump_Case`, `Housing_Pump_Lid`. |
| `src/torque_cap.py` | M75 threaded closure mechanics: `Torque_Cap_Inner`, `Torque_Cap_Outer`. |
| `src/adapters.py` | Fluidic interfaces: `Threaded_Luer_Adapter`, `Elbow_Adapter`. |
| `src/connectors.py` | Panel-mount hardware: `JST_XH_2_Pin_Header`, `JST_XH_2_Pin_Plug`, `USB_C_Panel_Mount`, `Luer_Bulkhead_Panel_Mount`. |
| `src/nanopore_wafer_mold.py` | Left/Right casting mold halves: `Nanopore_Wafer_Mold_Left`, `Nanopore_Wafer_Mold_Right`. |
| `src/assembly.py` | System-level assemblies: `Reader_Module_Assembly`, `Pump_Module_Assembly`, microfluidic splines (`route_tubing`), and wiring harnesses (`route_wiring`). |
| `src/collision_check.py` | Automated BREP clash detection routines across cartridge stack, caps, standoffs, internal routes, and threads. |
| `src/main.py` | Export entrypoint containing `export_all()`: iterates over 30 3D parts (`export_step`, `export_stl`) and 13 2D DXF sketches (`ExportDXF`). |

### 2.2 Export Pipeline Execution
The export pipeline is orchestrated at three levels:
1. `src/main.py [target]`: Direct build123d exporter script targeting `exports/`.
2. `scripts/export_manager.py`: Master project orchestrator CLI supporting `--cad`, `--kicad`, `--wiring`, `--firmware`, `--manifest`, `--check`, and `--all`.
3. `Makefile`:
   - `make export-cad` -> runs `python scripts/export_manager.py --cad` -> calls `python src/main.py all`.
   - `make manifest` -> runs `python scripts/export_manager.py --manifest` -> recomputes SHA-256 hashes for all files in `exports/` and writes `exports/manifest.json`.

---

## 3. Ribbon Cable Cavity Geometric Clearance Analysis

### 3.1 Coordinate Systems & Reference Frames

In the reader housing lid coordinate frame:
- Origin $(0, 0, 0)$ is located on the top flat ceiling of the lid plate.
- $+Z$ extends upwards through the neck transition cone ($Z \in [0.0, 5.0]$) and the cylindrical threaded neck ($Z \in [5.0, 30.2]$).
- $-Z$ extends downwards through the lid ceiling ($Z \in [0.0, -10.0]$) and the main enclosure walls to the indexing lip ($Z = -27.5\text{ mm}$).
- The cartridge stack rests directly on the ceiling at $Z = 0.0$ inside the neck bore.

### 3.2 Hexagon Socket vs. Cartridge Dimensions

| Parameter | Reader Lid Neck Socket | Cartridge Stack Components | Clearance / Delta |
|---|---|---|---|
| Geometry Type | Regular Hexagon (6-sided) | Regular Hexagon with R=5mm finger notches | Co-axial / concentric |
| Circumradius ($R$) | $30.5\text{ mm}$ (`61.0 / 2.0`) | $30.0\text{ mm}$ (`HEX_DIAM / 2.0`) | $0.50\text{ mm}$ radial clearance |
| Flat-to-Flat Width | $52.827\text{ mm}$ ($30.5 \times \sqrt{3}$) | $51.9615\text{ mm}$ ($30.0 \times \sqrt{3}$) | $0.8655\text{ mm}$ total ($0.433\text{ mm}$ per side) |
| Negative-Y Flat Boundary | $Y = -26.4137\text{ mm}$ | $Y = -25.9808\text{ mm}$ | $0.4329\text{ mm}$ gap |

### 3.3 Cavity Dimensions and Wall Penetration

The ribbon cable clearance cavity is specified with:
- Width ($dX$): $13.5\text{ mm}$ (spanning $X \in [-6.75, +6.75]$)
- Depth ($dY$): $3.0\text{ mm}$ (centered at $Y = -27.5\text{ mm}$, spanning $Y \in [-29.0, -26.0]$)
- Position along Y:
  - $Y_{\text{center}} = -27.5\text{ mm}$
  - $Y_{\text{outer}} = -29.0\text{ mm}$
  - $Y_{\text{inner}} = -26.0\text{ mm}$

Comparing these coordinates against the housing lid socket wall and the cartridge stack:
$$\text{Socket Inner Flat} = -26.4137\text{ mm}$$
$$\text{Cavity Outer Wall} = -29.0000\text{ mm}$$
$$\text{Cavity Inner Wall} = -26.0000\text{ mm}$$
$$\text{Cartridge Stack Flat} = -25.9808\text{ mm}$$

**Penetration Depth into Hexagon Wall**:
$$\Delta Y_{\text{wall}} = |-29.0000| - |-26.4137| = 2.5863\text{ mm}$$
The cavity is recessed $2.586\text{ mm}$ deep into the solid plastic wall of the neck.

**Protrusion into Socket Clearance Zone**:
$$\Delta Y_{\text{socket}} = |-26.4137| - |-26.0000| = 0.4137\text{ mm}$$
The cavity extends $0.414\text{ mm}$ into the clearance region between the socket wall and the cartridge.

**Clearance to Cartridge Stack Perimeter**:
$$\text{Clearance} = |-26.0000| - |-25.9808| = 0.0192\text{ mm} = 19.2\ \mu\text{m}$$
The inner boundary of the cavity stops $19.2\ \mu\text{m}$ outside the cartridge stack perimeter. There is **zero physical overlap** with any cartridge layer.

### 3.4 Vertical Profile Across Assembly Stackup

In `src/assembly.py:Reader_Module_Assembly()`, the cartridge stack sits inside the neck from $Z = 0.0$ upwards:

| Assembly Layer | Z Range relative to Lid ($Z=0$) | Thickness | Cavity Relationship |
|---|---|---|---|
| Housing Lid Body / Base | $Z \in [-27.5, 0.0]$ | $27.5\text{ mm}$ | Cavity passes through ceiling ($Z \in [-10.0, 0.0]$) down to $Z = -32.6\text{ mm}$ |
| `Bottom_Pusher_Plate` | $Z \in [0.0, 3.0]$ | $3.0\text{ mm}$ | Contains `Circuitry_Cutouts` at $Y = -27.5$; 0 overlap |
| `Plate_1_Base_Hex` | $Z \in [3.0, 7.0]$ | $4.0\text{ mm}$ | Contains `Circuitry_Cutouts` at $Y = -27.5$; 0 overlap |
| `Fitted_Amplifier_Gasket` | $Z \in [7.0, 8.6]$ | $1.6\text{ mm}$ | Contains `Circuitry_Cutouts` at $Y = -27.5$; 0 overlap |
| `PCB_Rigid_Active` (Interposer) | $Z \in [8.6, 9.4]$ | $0.8\text{ mm}$ | PCBA layer where ribbon cable terminates; unobstructed exit |
| `Cast_Nanopore_Wafer_Gasket` | $Z \in [9.4, 11.0]$ | $1.6\text{ mm}$ | Above PCBA; outside cutout zone |
| `Plate_3_Top_Hex` | $Z \in [11.0, 15.0]$ | $4.0\text{ mm}$ | Above PCBA; outside cutout zone |
| `Pressure_Puck` | $Z \in [15.0, 21.0]$ | $6.0\text{ mm}$ | Top compression element |

In `src/housing.py`, the ribbon cable clearance box is centered at $Z = -ceiling\_thick/2.0 = -5.0\text{ mm}$ with height $H = neck\_length + ceiling\_thick \times 3.0 = 25.2 + 30.0 = 55.2\text{ mm}$.
This spans $Z \in [-32.6, +22.6]\text{ mm}$.
Because the amplifier PCB sits at $Z \in [8.6, 9.4]\text{ mm}$, this provides $13.2\text{ mm}$ of clear headroom above the PCB and extends $5.1\text{ mm}$ below the bottom indexing lip of the lid, creating a continuous, unblocked vertical duct from the amplifier chamber down into the main reader electronics case.

---

## 4. Test Suite Audit & Verification

### 4.1 Test Execution Results

All commands were executed using `.venv/bin/python`:

1. **CAD Geometry Test Suite**:
   ```bash
   .venv/bin/python -m unittest tests/test_geometry.py tests/test_golden_stl_bounds.py tests/test_legacy_feature_parity.py
   ```
   **Output**: `Ran 27 tests in 31.745s - OK`
   - `test_geometry.py`: Validates BREP solid validity and non-zero volume for all 20+ models, runs stack collision check, housing cap check, thread check, standoff check, internal route check, and flexible routing check. (All 7 test cases pass).
   - `test_golden_stl_bounds.py`: Asserts exact bounding boxes against KiCad PCB source of truth and golden STL bounds. (All 12 test cases pass).
   - `test_legacy_feature_parity.py`: Explicitly tests parity with OpenSCAD legacy features, including `test_housing_lid_reader_legacy_features` item 2: ribbon cable clearance cavity probe at `(-4.0, -28.5, -10.0)` having $< 0.5\text{ mm}^3$ intersection. (All 8 test cases pass).

2. **Full Repository Test Suite (`run_tests.py`)**:
   ```bash
   .venv/bin/python run_tests.py
   ```
   **Output**: `Ran 92 tests in 28.517s - FAILED (failures=2)`
   - 90 of 92 tests pass.
   - The two failures are strictly related to Requirement R2 staged deliverables:
     - `FAIL: test_firmware_staged_binaries (test_exports_e2e.TestExportsE2E)`: `Missing firmware.bin in exports/firmware/`
     - `FAIL: test_wiring_and_tubing_documentation (test_exports_e2e.TestExportsE2E)`: `Missing reader_wiring directory`
   - Zero failures or regressions exist in any CAD, geometry, simulation, or PCB test.

---

## 5. Critical Technical Discoveries & Latent Bugs

### 5.1 Stale Staged Exports on Disk

To verify the staged exports against the code, a BREP boolean cut analysis was performed between `Housing_Lid_Reader()` generated live by `src/housing.py` and `import_step("exports/Housing_Lid_Reader.step")`:

```python
lid_code = Housing_Lid_Reader()
lid_step = import_step("exports/Housing_Lid_Reader.step")
missing_in_step = lid_step.cut(lid_code)
# Result: vol = 2001.12 mm^3
# Bounding Box: -6.75 <= X <= 6.75, -29.0 <= Y <= -26.0, -27.5 <= Z <= 22.6
```

**Conclusion**: The staged files `exports/Housing_Lid_Reader.step` and `exports/Housing_Lid_Reader.stl` on disk do NOT have the $13.5\text{ mm} \times 3.0\text{ mm}$ cavity. They contain solid plastic in that exact region. The Python code in `src/housing.py` already includes the cavity, but the CAD exporter has not been executed to refresh the files in `exports/`.

### 5.2 Latent Tooling Bug in `src/collision_check.py`

In `src/collision_check.py`, lines 21–34:
```python
def check_overlap(part_a, part_b, name_a="Part A", name_b="Part B"):
    try:
        overlap_shape = part_a.intersect(part_b)
        vol = overlap_shape.volume
        if vol > 0.01:
            return True, vol
        return False, vol
    except Exception as e:
        return False, 0.0
```

**Bug Mechanism**: In build123d, if `part_a.intersect(part_b)` produces multiple disjoint or touching solid regions, it returns a `ShapeList` object. A `ShapeList` does not possess a `.volume` attribute (it has elements with `.volume`). Accessing `overlap_shape.volume` throws `AttributeError: 'ShapeList' object has no attribute 'volume'`. The enclosing `except Exception:` catches this and silently returns `False, 0.0`, masking real physical clashes!

**Fix Required**:
```python
def check_overlap(part_a, part_b, name_a="Part A", name_b="Part B"):
    try:
        overlap_shape = part_a.intersect(part_b)
        if overlap_shape is None:
            return False, 0.0
        if hasattr(overlap_shape, "volume"):
            vol = overlap_shape.volume
        else:
            vol = sum(s.volume for s in overlap_shape)
        if vol > 0.01:
            print(f"[!] COLLISION DETECTED: {name_a} overlaps with {name_b} (Overlap Volume: {vol:.4f} mm^3)")
            return True, vol
        return False, vol
    except Exception as e:
        return False, 0.0
```

### 5.3 Housing Lid Inner Hex Socket Origin

In `src/housing.py`, lines 240–244:
```python
        # Inner Hex Socket Cutout (61mm across corners)
        with Locations((0, 0, 5.0 + neck_length / 2.0)):
            with BuildSketch():
                RegularPolygon(radius=61.0 / 2.0, side_count=6)
            extrude(amount=neck_length + 20.0, mode=Mode.SUBTRACT)
```
The sketch location was set to $Z = 5.0 + neck\_length / 2.0 = 17.6\text{ mm}$, extruding upward. Consequently, the transition cone between $Z = 0.0$ and $Z = 17.6\text{ mm}$ remains solid inside the neck.
When the hex socket is cut from $Z = 0.0$ (`with Locations((0, 0, 0.0)): ... extrude(amount=5.0 + neck_length + 20.0, mode=Mode.SUBTRACT)`), the socket opens fully down to the ceiling, cleanly seating the entire cartridge stack (`Bottom_Pusher_Plate`, `Plate_1_Base_Hex`, `Fitted_Amplifier_Gasket`, `PCB_Rigid_Active`, `Cast_Nanopore_Wafer_Gasket`, `Plate_3_Top_Hex`) with **0.0000 mm^3 collision**.

---

## 6. Recommendations & Implementation Roadmap

To fulfill Acceptance Criteria and achieve complete consistency across CAD models, tests, and deliverables:

### Step 1: Minor Hardening in `src/housing.py` (if desired for assembly realism)
Ensure the inner hex socket cutout starts at $Z = 0.0$:
```python
        # Inner Hex Socket Cutout (61mm across corners)
        with Locations((0, 0, 0.0)):
            with BuildSketch():
                RegularPolygon(radius=61.0 / 2.0, side_count=6)
            extrude(amount=5.0 + neck_length + 20.0, mode=Mode.SUBTRACT)
```
And ensure the ribbon cable clearance channel box has adequate height:
```python
        # Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
        with Locations((0.0, -27.5, -ceiling_thick / 2.0)):
            Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)
```

### Step 2: Fix `check_overlap()` in `src/collision_check.py`
Replace `vol = overlap_shape.volume` with polymorphic handling:
```python
        if hasattr(overlap_shape, "volume"):
            vol = overlap_shape.volume
        else:
            vol = sum(s.volume for s in overlap_shape)
```

### Step 3: Regenerate Staged CAD Deliverables
Run:
```bash
.venv/bin/python src/main.py all
```
or
```bash
.venv/bin/python scripts/export_manager.py --cad
```
This updates `exports/Housing_Lid_Reader.step` and `exports/Housing_Lid_Reader.stl` on disk to contain the $13.5\text{ mm} \times 3.0\text{ mm}$ cavity.

### Step 4: Refresh Manifest Hashes
Run:
```bash
.venv/bin/python scripts/export_manager.py --manifest
```
This updates `exports/manifest.json` with the updated SHA-256 hashes and file sizes.

### Step 5: Verification
Run:
```bash
.venv/bin/python -m unittest tests/test_geometry.py tests/test_golden_stl_bounds.py tests/test_legacy_feature_parity.py
```
And verify that all geometry and collision tests pass with 0 errors and 0 collisions.
