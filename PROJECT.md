# Project: daemon-pore

## Architecture
- CAD / Mechanical Housing & Cartridge Stack: Python (build123d / CadQuery) modeling in `src/`, generating STEP, STL, and DXF deliverables in `exports/`.
- PCB Layout: KiCad v8 PCB definitions (`Amplifier/Amplifier.kicad_pcb` and `Interposer/Interposer.kicad_pcb`), outlining Edge.Cuts with exact cavity clearances and connector alignments.
- Staged Manufacturing Exports: Automated export management via `scripts/export_manager.py`, compiling firmware via PlatformIO, rendering wiring diagrams via WireViz, and indexing SHA-256 hashes in `exports/manifest.json`.
- Test Suite & Physical Validation: Python unittest suite (`tests/`) containing 92+ tests covering geometric collision checking, golden STL bounds, legacy feature parity, and E2E export validation.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Ribbon Cable Cavity Integration & Geometric Clearance | Housing lid reader, cartridge plates, and gaskets accommodate 13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5mm with 0 collisions. Fix ShapeList volume check in collision_check.py and hex socket Z-origin in housing.py. | M1 | ORIGINAL_REQUEST §R1 |
| 2 | PCB Edge.Cuts Geometry Alignment & Validation | Ensure `Amplifier/Amplifier.kicad_pcb` Edge.Cuts is a continuous closed loop with 0 vertices of degree != 2, 0 floating lines, and matching 13.5mm x 3.0mm cavity. Fix casing bug in `scripts/build_interposer_kicad.py` and add explicit unit test for Edge.Cuts continuity. | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Staged Exports & Documentation Deliverables | Staged ESP32-S3 firmware image (`exports/firmware/firmware.bin`), WireViz diagrams (`exports/reader_wiring/`), regenerated CAD STEP/STL exports, and full SHA-256 indexing in `exports/manifest.json`. | M2 | ORIGINAL_REQUEST §R2 |
| 4 | Automated Test Suite Verification | Verify all 92 tests in `.venv/bin/python run_tests.py` pass with zero failures, zero regressions, and zero CAD collisions. | M3 | ORIGINAL_REQUEST §R3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Ribbon Cable Cavity & PCB Clearance Alignment | Update `src/collision_check.py`, `src/housing.py`, `scripts/build_interposer_kicad.py`, verify `Amplifier.kicad_pcb`, and add PCB Edge.Cuts continuity test in `tests/`. | none | DONE |
| 2 | CAD Staged Exports & Manifest Generation | Regenerate all 3D/2D CAD exports (`python src/main.py all`), build & stage firmware binary and WireViz diagrams, update `exports/manifest.json`. | M1 | DONE |
| 3 | E2E Repository Verification & Gate Hardening | Execute full test runner (`run_tests.py`), verify all 95 tests pass, run independent Reviewers, Challengers, and Forensic Auditor. | M2 | DONE |

## Interface Contracts
### CAD Model ↔ Housing & Cartridge Stack
- Cavity location: centered at X = 0.0, Y = -27.5mm, depth = 3.0mm (Y in [-29.0, -26.0]mm), width = 13.5mm (X in [-6.75, 6.75]mm).
- Height: spans across the housing lid neck and cartridge base hexagon walls.
- Clearance: >= 19.2 microns radial clearance from cartridge stack flat (Y = -25.9808mm).
- Overlap collision threshold: volume < 0.01 mm^3.

### PCB Edge.Cuts ↔ Housing Cavity
- Outline contour: in KiCad coordinates, centered at X = 164.5000mm, cavity opening Y in [81.475044, 84.475044]mm, width 13.5mm (X in [157.75, 171.25]mm), depth 3.0mm.
- Graph topology: strictly 2-regular connected graph (every node degree == 2, exactly 0 endpoints with degree != 2).
- Copper clearance: 0 traces or vias inside the cavity volume [157.5, 171.5] x [81.3, 85.0].

### Staged Deliverables ↔ Manifest
- Firmware: `exports/firmware/firmware.bin` (ESP32-S3 binary, valid magic byte 0xE9, > 800 KB).
- Wiring: `exports/reader_wiring/` containing `.png`, `.svg`, `.html`, and `.bom.tsv`.
- Manifest: `exports/manifest.json` indexing every staged artifact with valid `"sha256"`.

## Code Layout
- `src/`: CAD source code (`housing.py`, `cartridge.py`, `common.py`, `collision_check.py`, `main.py`).
- `Amplifier/`: KiCad PCB project and layouts (`Amplifier.kicad_pcb`, `Amplifier.kicad_sch`).
- `Interposer/`: Interposer PCB layouts.
- `scripts/`: Build and staging scripts (`export_manager.py`, `build_interposer_kicad.py`).
- `MR1_firmware/`: PlatformIO ESP32-S3 firmware project.
- `wiring/`: WireViz specification files.
- `exports/`: Staged manufacturing exports, firmware, wiring docs, and `manifest.json`.
- `tests/`: Automated test suite (92 tests across geometry, golden STL bounds, parity, exports).
