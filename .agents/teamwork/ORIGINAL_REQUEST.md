# Original User Request

## 2026-10-15T01:05:44Z

Finalize and verify the daemon-pore production hardware engineering suite: complete CAD/PCB cavity alignments for the ribbon cable, resolve all remaining export/firmware deliverables, and achieve full end-to-end verification across the repository test suite.

Working directory: /home/loki/Projects/daemon-pore
Integrity mode: development

## Requirements

### R1. Ribbon Cable Cavity Integration & Geometric Clearance
Update and verify CAD models across the reader housing lid, cartridge plates, and gaskets to accommodate a 13.5mm x 3.0mm cavity recessed into the amplifier hexagon wall. Align the PCB Edge.Cuts geometry to ensure a continuous closed boundary matching the recessed cavity without floating lines or geometric interference.

### R2. Staged Exports & Documentation Deliverables
Regenerate and validate all manufacturing and assembly deliverables, ensuring the staged ESP32-S3 firmware image (`exports/firmware/firmware.bin`) and WireViz wiring/tubing diagrams (`exports/reader_wiring/`) are properly generated, verified, and indexed with valid checksums in `exports/manifest.json`.

### R3. Automated Test Suite Verification
Verify the entire repository test suite passes with zero failures, zero regressions, and zero CAD collision errors.

## Verification Resources
- Test Runner: `.venv/bin/python run_tests.py`
- Geometric Collision Checker: `.venv/bin/python -m unittest tests/test_geometry.py`
- Golden STL Bounds: `.venv/bin/python -m unittest tests/test_golden_stl_bounds.py`
- Feature Parity Tests: `.venv/bin/python -m unittest tests/test_legacy_feature_parity.py`
- Exports E2E Suite: `.venv/bin/python -m unittest tests/test_exports_e2e.py`

## Acceptance Criteria

### CAD & PCB Geometry
- [ ] No mechanical collisions or interferences detected across cartridge stack and housing assembly.
- [ ] PCB Edge.Cuts contour in `Amplifier/Amplifier.kicad_pcb` forms a continuous closed loop with 0 degree != 2 endpoints.
- [ ] Housing lid reader ribbon cable cavity matches 13.5mm x 3.0mm recessed into the hexagon wall at Y = -27.5mm.

### Export Deliverables
- [ ] Staged firmware binary exists at `exports/firmware/firmware.bin`.
- [ ] Reader wiring documentation directory exists at `exports/reader_wiring/`.
- [ ] `exports/manifest.json` accurately records all files and SHA-256 hashes.

### Automated Testing
- [ ] `.venv/bin/python run_tests.py` executes all 92 tests and exits with code 0 (all tests passing).
