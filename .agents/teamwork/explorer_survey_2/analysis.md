# PCB Geometry & Edge.Cuts Survey Report (Explorer 2)

**Document**: `analysis.md`  
**Date**: 2026-10-15  
**Investigator**: Explorer 2 (PCB Geometry Explorer)  
**Target**: `Amplifier/Amplifier.kicad_pcb` & KiCad PCB Test Suite  

---

## 1. Executive Summary

This investigation analyzed the KiCad PCB `Edge.Cuts` geometry for the R1 reader ribbon cable cavity integration, verified current contour topology and continuity, surveyed repository automated tests, and audited related generator scripts and downstream boards (`Interposer`).

### Core Findings
1. **Current Working Tree Status in `Amplifier/Amplifier.kicad_pcb`**:
   - The working tree version of `Amplifier/Amplifier.kicad_pcb` **already contains the exact 13.5mm x 3.0mm recessed cavity** alignment along lines 55361–55410.
   - The two previous floating lines (`uuid "fe78e0c3-9029-46ee-acff-aa3bfbf54f90"` and `uuid "6fb7a02f-0472-4bd8-b68e-54c937384c69"`) were successfully excised.
   - Graph topology analysis confirms **66 segments**, **66 unique vertices**, and **exactly 0 vertices with degree != 2**. The contour forms a mathematically continuous, single closed planar loop.
   - Bounding box dimensions: **Width = 55.0034 mm**, **Height = 51.9616 mm**, Center = **(164.5000, 58.4942)**, matching the 60mm hexagon across flats ($30\sqrt{3} \approx 51.9615$ mm) with $R=5$ mm finger notches at $X = \pm 25$ mm.
   - Zero geometric interference with copper tracks, vias, or SMD components inside the cavity clearance volume.
2. **Comparison with Git HEAD (`4935a67`)**:
   - In HEAD, `Amplifier/Amplifier.kicad_pcb` had 68 segments and **10 open/degree-1 vertices** due to coordinate rounding discrepancies (gaps of 0.001–0.010 mm) and 2 floating lines outside the board perimeter.
   - The cavity in HEAD was only 12.0mm wide by 2.49mm deep. The working tree changes resolved all 10 non-degree-2 vertices.
3. **Repository Test Suite Status**:
   - Executing `.venv/bin/python run_tests.py` runs 92 tests: **90 pass, 2 fail** (`test_firmware_staged_binaries` and `test_wiring_and_tubing_documentation` in `test_exports_e2e.py`, belonging to Explorer 3's deliverable scope).
   - **Gap Identified**: No test in `tests/*.py` currently asserts the graph topology, continuity, or endpoint degrees of `Amplifier/Amplifier.kicad_pcb`. `test_kicad_pcb_source_of_truth` in `test_golden_stl_bounds.py` only validates the Build123d `Hex_Base_Sketch()`.
4. **Generator Script & Downstream Board Defect**:
   - `scripts/build_interposer_kicad.py` fails on line 21 with `FileNotFoundError` due to casing: `Path("Amplifier/amplifier.kicad_pcb")` instead of `Path("Amplifier/Amplifier.kicad_pcb")`.
   - `Interposer/Interposer.kicad_pcb` was built from the old HEAD coordinates and still exhibits **4 degree-1 endpoints** (gaps at $Y = 81.99$ vs $81.994244$) and the old 12.0mm x 2.48mm cavity dimensions.

---

## 2. Requirement Analysis (R1 Ribbon Cable Cavity Integration)

### 2.1 Authoritative Requirements & Acceptance Criteria
- **R1 Scope**:
  > "Update and verify CAD models across the reader housing lid, cartridge plates, and gaskets to accommodate a 13.5mm x 3.0mm cavity recessed into the amplifier hexagon wall. Align the PCB Edge.Cuts geometry to ensure a continuous closed boundary matching the recessed cavity without floating lines or geometric interference."
- **Acceptance Criteria**:
  - `[ ]` PCB Edge.Cuts contour in `Amplifier/Amplifier.kicad_pcb` forms a continuous closed loop with 0 degree != 2 endpoints.
  - `[ ]` Housing lid reader ribbon cable cavity matches 13.5mm x 3.0mm recessed into the hexagon wall at Y = -27.5mm.
  - `[ ]` No mechanical collisions or interferences detected across cartridge stack and housing assembly.

### 2.2 Coordinate System Mapping (CAD vs KiCad PCB)
| Dimension / Reference | CAD System (`src/common.py`, `src/housing.py`) | KiCad PCB System (`Amplifier.kicad_pcb`) |
|---|---|---|
| **Origin $(0, 0)$** | Center of 60mm Hexagon | Top-left of drawing sheet |
| **Hexagon Center** | $(0.000, 0.000)$ | $(164.5000, 58.494244)$ |
| **Y-Axis Direction** | $+Y$ up/rear, $-Y$ down/front | $+Y$ down, $-Y$ up |
| **Bottom Hex Edge** | $Y = -25.9808$ mm ($-\frac{30\sqrt{3}}{2}$) | $Y = 58.494244 + 25.980800 = 84.475044$ mm |
| **Cavity Position** | Centered at $X = 0$, against bottom wall | Centered at $X = 164.5000$, $Y = 84.475044$ |
| **Cavity Width** | $13.500$ mm ($X \in [-6.75, +6.75]$) | $13.500$ mm ($X \in [157.750, 171.250]$) |
| **Cavity Depth** | $3.000$ mm into wall ($Y \in [-25.981, -22.981]$) | $3.000$ mm upwards into board ($Y \in [84.475044, 81.475044]$) |

---

## 3. Detailed Survey of `Amplifier/Amplifier.kicad_pcb` Edge.Cuts Contour

### 3.1 Topology & Graph Metric Comparison

A complete topological graph analysis was conducted by parsing every `(gr_line ...)` segment on `(layer "Edge.Cuts")`, building an undirected adjacency graph where vertices are rounded to $0.001$ mm, and computing the degree (incident segment count) for each vertex.

| Metric | Git HEAD (`4935a67`) | Working Tree (`Amplifier.kicad_pcb`) | Status |
|---|---|---|---|
| **Total `gr_line` on Edge.Cuts** | 68 segments | 66 segments | Corrected (-2 floating lines) |
| **Unique Vertices** | 73 vertices | 66 vertices | 1:1 segment-to-vertex ratio |
| **Vertices with Degree == 2** | 63 vertices | 66 vertices (100%) | Fully 2-regular graph |
| **Vertices with Degree != 2** | **10 vertices** (all degree 1) | **0 vertices** | **0 degree != 2 endpoints achieved** |
| **Closed Continuous Loops** | 0 (broken open boundary) | 1 (single closed boundary) | **Continuous closed loop achieved** |
| **Cavity Width** | 12.000 mm | 13.500 mm | Exact match to R1 |
| **Cavity Depth** | 2.485 mm | 3.000 mm | Exact match to R1 |
| **Floating Disconnected Lines** | 2 lines near $(185, 30)$ | 0 | Excised |

### 3.2 Exact Segment Coordinates in `Amplifier/Amplifier.kicad_pcb`

The 5 contiguous segments forming the bottom hexagon edge and the recessed ribbon cable cavity are located at lines 55361–55410:

```lisp
	(gr_line
		(start 149.5 84.475044)
		(end 157.75 84.475044)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "Edge.Cuts")
		(uuid "5e7853f8-d372-4e0e-b7ba-bfb13b3ec416")
	)
	(gr_line
		(start 157.75 81.475044)
		(end 157.75 84.475044)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "Edge.Cuts")
		(uuid "35cf1926-3f26-4032-90ba-5415037af3d6")
	)
	(gr_line
		(start 157.75 81.475044)
		(end 171.25 81.475044)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "Edge.Cuts")
		(uuid "38c81db8-aa9e-4bf4-82ee-268fc419e231")
	)
	(gr_line
		(start 171.25 81.475044)
		(end 171.25 84.475044)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "Edge.Cuts")
		(uuid "41e2b493-3096-4231-ba9f-22a13eeb2543")
	)
	(gr_line
		(start 171.25 84.475044)
		(end 179.5 84.475044)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "Edge.Cuts")
		(uuid "5e0c830b-9bef-4078-83a9-080531030dba")
	)
```

#### Step-by-Step Traversal of Cavity Contour
1. Line 55071: Slanted hex edge ends at $(149.5000, 84.475044)$.
2. Line 55361: Bottom baseline runs right to left notch boundary: $(149.5000, 84.475044) \rightarrow (157.7500, 84.475044)$ (length: 8.250 mm).
3. Line 55371: Left vertical step recedes into board: $(157.7500, 84.475044) \rightarrow (157.7500, 81.475044)$ (length: 3.000 mm).
4. Line 55381: Horizontal floor of cavity runs across width: $(157.7500, 81.475044) \rightarrow (171.2500, 81.475044)$ (length: 13.500 mm).
5. Line 55391: Right vertical step returns to hex baseline: $(171.2500, 81.475044) \rightarrow (171.2500, 84.475044)$ (length: 3.000 mm).
6. Line 55401: Bottom baseline continues to right hex corner: $(171.2500, 84.475044) \rightarrow (179.5000, 84.475044)$ (length: 8.250 mm).
7. Line 55421: Slanted hex edge continues upward from $(179.5000, 84.475044)$.

Every endpoint matches its neighbor with 0.000000 mm error.

### 3.3 Excised Floating Line Segments
In HEAD commit `4935a67`, two extraneous lines were present outside the board near $Y = 30$:
- Line 55428 in HEAD: `(start 185.06 30.415044)` to `(end 194.06 30.415044)` (`uuid "fe78e0c3-9029-46ee-acff-aa3bfbf54f90"`).
- Line 55728 in HEAD: `(start 194.06 30.415044)` to `(end 194.06 27.934244)` (`uuid "6fb7a02f-0472-4bd8-b68e-54c937384c69"`).
Both segments have been deleted in the working tree, eliminating the disconnected endpoints.

---

## 4. Geometric Interference & Clearances Audit

A spatial query was run against all elements inside the cavity box $X \in [157.5, 171.5]$, $Y \in [81.3, 85.0]$:

| Element Type | Elements Inside Cavity | Clearance Finding |
|---|---|---|
| **Copper Tracks (`segment`)** | 0 | None. All tracks keep > 0.45 mm clearance from Edge.Cuts. |
| **Vias (`via`)** | 0 | Zero vias inside the cavity zone. |
| **Components (`footprint`)** | 0 inside cavity | `J7` (14-pin FFC connector) is located at $(165.755, 82.968)$ on the board side, facing the cavity. `C39` (0402 cap) is located at $(156.775, 82.693)$, cleanly to the left of $X=157.75$. |
| **KiCad DRC Outline Errors** | 0 | `kicad-cli pcb drc` reports zero outline errors, zero open contours, zero disjoint geometries. |

---

## 5. Repository Test Suite Analysis & Execution

### 5.1 Test Execution Results (`run_tests.py`)
Command: `.venv/bin/python run_tests.py`
- Total tests executed: 92
- Results: **90 passing, 2 failing**
- Failures:
  1. `FAIL: test_firmware_staged_binaries (test_exports_e2e.TestExportsE2E)`: Missing `exports/firmware/firmware.bin`.
  2. `FAIL: test_wiring_and_tubing_documentation (test_exports_e2e.TestExportsE2E)`: Missing `exports/reader_wiring/` directory.
- Geometry & CAD tests:
  - `test_golden_stl_bounds.py`: 12/12 PASS
  - `test_geometry.py`: 7/7 PASS (including assembly collision checks, standoff clearance, internal clearance, and flexible routing clearance)
  - `test_legacy_feature_parity.py`: 12/12 PASS

### 5.2 Test Gap & Proposed Unit Test

Currently, no test in `tests/*.py` inspects the actual `Amplifier/Amplifier.kicad_pcb` file for `Edge.Cuts` loop closure or degree != 2 endpoints.

To satisfy the Acceptance Criterion permanently and prevent regressions, the following test method should be added to `tests/test_interposer_kicad.py` (or `tests/test_golden_stl_bounds.py`):

```python
    def test_amplifier_pcb_edge_cuts_continuity(self):
        """Verify Amplifier/Amplifier.kicad_pcb Edge.Cuts forms a continuous closed loop
        with 0 degree != 2 endpoints and matches 13.5mm x 3.0mm ribbon cavity."""
        pcb_path = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"
        self.assertTrue(pcb_path.exists(), "Amplifier.kicad_pcb must exist")
        text = pcb_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        blocks = []
        current = []
        in_block = False
        for line in lines:
            if line.startswith("\t(gr_line"):
                in_block = True
                current = [line]
            elif in_block:
                current.append(line)
                if line.startswith("\t)"):
                    in_block = False
                    blocks.append("\n".join(current))

        ec_blocks = [b for b in blocks if '(layer "Edge.Cuts")' in b]
        self.assertGreaterEqual(len(ec_blocks), 60, "Amplifier Edge.Cuts must have perimeter segments")

        segments = []
        for b in ec_blocks:
            sm = re.search(r"\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)", b)
            em = re.search(r"\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)", b)
            self.assertIsNotNone(sm)
            self.assertIsNotNone(em)
            p1 = (float(sm.group(1)), float(sm.group(2)))
            p2 = (float(em.group(1)), float(em.group(2)))
            segments.append((p1, p2))

        # Adjacency graph
        adj = defaultdict(list)
        for p1, p2 in segments:
            k1 = (round(p1[0], 3), round(p1[1], 3))
            k2 = (round(p2[0], 3), round(p2[1], 3))
            adj[k1].append(k2)
            adj[k2].append(k1)

        non_2 = {k: len(v) for k, v in adj.items() if len(v) != 2}
        self.assertEqual(len(non_2), 0, f"Edge.Cuts contour has endpoints with degree != 2: {non_2}")

        # Bounds check
        all_x = [pt[0] for s in segments for pt in s]
        all_y = [pt[1] for s in segments for pt in s]
        w = max(all_x) - min(all_x)
        h = max(all_y) - min(all_y)
        self.assertAlmostEqual(w, 55.0, delta=0.05, msg=f"Width {w} != 55.0mm")
        self.assertAlmostEqual(h, 51.962, delta=0.05, msg=f"Height {h} != 51.962mm")

        # Cavity floor segment: 13.5mm width at Y=81.475mm
        cavity_floors = [s for s in segments if math.isclose(s[0][1], 81.475044, abs_tol=1e-3) and math.isclose(s[1][1], 81.475044, abs_tol=1e-3)]
        self.assertEqual(len(cavity_floors), 1, "Must have exactly 1 horizontal cavity floor segment")
        c_len = abs(cavity_floors[0][1][0] - cavity_floors[0][0][0])
        self.assertAlmostEqual(c_len, 13.5, delta=0.001, msg=f"Cavity width {c_len} != 13.5mm")
```

---

## 6. Generator Scripts & Downstream Interposer Audit

### 6.1 `scripts/build_interposer_kicad.py` Casing Bug
- **Issue**: Line 21 specifies `src_pcb = Path("Amplifier/amplifier.kicad_pcb").read_text(encoding="utf-8")`.
- On Linux case-sensitive filesystems, this throws `FileNotFoundError: [Errno 2] No such file or directory: 'Amplifier/amplifier.kicad_pcb'`.
- **Remedy**: Change line 21 to `Path("Amplifier/Amplifier.kicad_pcb")`.

### 6.2 `Interposer/Interposer.kicad_pcb` Edge.Cuts Status
- `Interposer/Interposer.kicad_pcb` lines 4718–4765 still contain the old unaligned segments from earlier git revisions:
  - `(start 149.5 84.475044)` to `(end 158.5 84.475044)` (`fe78e0c3`)
  - `(start 158.5 81.99)` to `(end 170.5 81.99)` (`38c81db8`)
  - `(start 158.5 84.475044)` to `(end 158.5 81.994244)` (`6fb7a02f`)
  - `(start 170.5 81.994244)` to `(end 170.5 84.475044)` (`41e2b493`)
- This causes **4 open degree-1 endpoints** in Interposer:
  - `(158.5, 81.99)` (deg 1) vs `(158.5, 81.9942)` (deg 1)
  - `(170.5, 81.99)` (deg 1) vs `(170.5, 81.9942)` (deg 1)
- Once `scripts/build_interposer_kicad.py` is patched to read `Amplifier/Amplifier.kicad_pcb`, regenerating `Interposer.kicad_pcb` or synchronizing the outer boundary will resolve the Interposer geometry automatically.

---

## 7. Actionable Recommendations for Implementation Phase

1. **Retain Working Tree Changes in `Amplifier/Amplifier.kicad_pcb`**:
   The current working tree modifications for lines 55361–55410 and the deletion of the 2 floating lines are verified, clean, and 100% compliant with R1. Stage and preserve these changes.
2. **Fix `scripts/build_interposer_kicad.py`**:
   Update line 21 from `Amplifier/amplifier.kicad_pcb` to `Amplifier/Amplifier.kicad_pcb`.
3. **Synchronize `Interposer/Interposer.kicad_pcb`**:
   Update `Interposer/Interposer.kicad_pcb` lines 4718–4765 to match the 13.5mm x 3.0mm cavity coordinates and excise the 2 floating lines, eliminating all 4 degree-1 endpoints on Interposer.
4. **Add Automated Unit Test**:
   Integrate `test_amplifier_pcb_edge_cuts_continuity` into `tests/test_interposer_kicad.py` or `tests/test_golden_stl_bounds.py` so that `.venv/bin/python run_tests.py` explicitly validates the Edge.Cuts loop topology and 0 degree != 2 endpoints.
