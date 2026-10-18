# Project Deliverables & Export System ? MR1

This document details the automated export pipeline, deliverables inventory, manufacturing packages, and regression-tracking workflows for the **MR1 Nanopore Reader (MR1)**.

---

## 1. Quickstart Commands

The export system can be executed through any of three interfaces:

### Via GNU Make
```bash
# Export all deliverables (CAD, KiCad, Wiring, Firmware, and Manifest)
make export

# Export specific domains
make export-cad        # 3D Solids (STEP/STL) & 2D Profiles (DXF)
make export-kicad      # Gerbers, Drill, POS, BOM, and PDF schematics
make export-wiring     # WireViz wiring and tubing diagrams
make export-firmware   # Compile and stage ESP32-S3 firmware binaries

# Verification and integrity checks
make check             # Verify all indexed deliverables exist on disk
make test              # Run unit tests and CAD collision checks
make test-e2e          # Run end-to-end deliverables validation test
```

### Via Bash Script
```bash
# Make script executable (first time only)
chmod +x scripts/export_all.sh scripts/run_e2e_tests.sh

# Run all exports
./scripts/export_all.sh --all

# Run E2E test verification
./scripts/run_e2e_tests.sh
```

### Via Python Directly (Virtual Environment)
```bash
# Windows (PowerShell):
.\.venv\Scripts\python.exe scripts/export_manager.py --all
.\.venv\Scripts\python.exe scripts/export_manager.py --check

# Linux / macOS / Bash:
./.venv/bin/python scripts/export_manager.py --all
./.venv/bin/python scripts/export_manager.py --check

# Or activate environment in current shell:
# Windows: & .\.venv\Scripts\Activate.ps1
# POSIX:   source .venv/bin/activate
# Then run: python scripts/export_manager.py --all
```

### Via npm
```bash
npm run export        # Runs export_manager.py --all
npm test              # Runs full test suite
```

---

## 2. Deliverables Directory Layout (`exports/`)

```
exports/
├── manifest.json                  # SHA-256 integrity catalog of all deliverables
├── MR1_Gerbers.zip                # Fab-ready zip archive for MR1 main board
├── Amplifier_Gerbers.zip          # Fab-ready zip archive for cartridge amplifier
├── Pump_Gerbers.zip               # Fab-ready zip archive for peristaltic pump & USB-PD hub
├── Interposer_Gerbers.zip         # Fab-ready zip archive for PTFE microfluidic interposer
│
├── *.stl                          # 3D printable meshes (30 components)
├── *.step                         # Parametric STEP solids for CAD exchange (28 components)
├── *.dxf                          # 2D CNC profiles for PP sheet stock and KiCad Edge.Cuts (11 profiles)
│
├── gerbers_mr1/                   # Raw Gerber layers & NC drill for MR1 (6-layer board)
├── gerbers_amplifier/             # Raw Gerber layers & NC drill for Amplifier (2-layer board)
├── gerbers_pump/                  # Raw Gerber layers & NC drill for Pump Controller (4-layer board)
├── gerbers_interposer/            # Raw Gerber layers & NC drill for PTFE Interposer (2-layer board)
├── pos_mr1/                       # Pick-and-place XY coordinates (CSV) for MR1
├── pos_amplifier/                 # Pick-and-place XY coordinates (CSV) for Amplifier
├── pos_pump/                      # Pick-and-place XY coordinates (CSV) for Pump Controller
├── pos_interposer/                # Pick-and-place XY coordinates (CSV) for PTFE Interposer
│
├── schematics/
│   ├── MR1.pdf                    # Complete multi-sheet schematic for MR1
│   ├── Amplifier.pdf              # Schematic for analog transimpedance amplifier
│   ├── Pump.pdf                   # Schematic for peristaltic pump & USB-PD hub
│   └── Interposer.pdf             # Schematic for PTFE microfluidic interposer
│
├── bom/
│   ├── MR1_BOM.csv                # Component bill of materials for MR1
│   ├── Amplifier_BOM.csv          # Component bill of materials for Amplifier
│   ├── Pump_BOM.csv               # Component bill of materials for Pump Controller
│   └── Interposer_BOM.csv         # Component bill of materials for PTFE Interposer
│
├── reader_wiring/                 # Electrical harness documentation (HTML, PNG, SVG, TSV)
├── reader_tubing/                 # Fluidic tubing routing documentation (HTML, PNG, SVG, TSV)
│
└── firmware/                      # Staged ESP32-S3 firmware release binaries
    ├── firmware.bin               # Application binary
    ├── bootloader.bin             # 2nd stage bootloader
    └── partitions.bin             # Partition table
```

---

## 3. Detecting Breaking Changes (For Agents & Humans)

The repository maintains an automated drift detection mechanism using `exports/manifest.json`.

### How It Works:
1. Every deliverable generated is hashed using **SHA-256** and recorded in `manifest.json` with its file size in bytes and category.
2. In git, running `git diff exports/manifest.json` immediately reveals:
   - Added deliverables (new parts, new layers).
   - Removed deliverables (unintended regressions or missing files).
   - Modified deliverables (geometry changes, schematic revisions, routing modifications).
3. The automated test `tests/test_exports_e2e.py` enforces:
   - Non-zero file sizes for all critical deliverables.
   - Valid binary/ASCII headers (STL triangle headers, STEP ISO headers, DXF sections, PDF magic bytes, ESP32 binary magic byte `0xE9`).
   - Hash match between disk files and the manifest.

```bash
# Check if any indexed deliverable is missing or corrupted:
python scripts/export_manager.py --check

# Run the full automated validation suite:
python tests/test_exports_e2e.py
```

---

## 4. Manufacturing & Ordering Guides

### PCB Fabrication (JLCPCB / PCBWay / OSHPark)
* **MR1 Main Board**:
  - File: `exports/MR1_Gerbers.zip`
  - Layers: **6 Layers** (F_Cu, In1_Cu, In2_Cu, In3_Cu, In4_Cu, B_Cu)
  - Surface Finish: **ENIG** (Electroless Nickel Immersion Gold) recommended for nanoamp/picoamp sensitivity and flat SMT pads.
  - Solder Mask: Matte Black or Green.
  - Pick and Place: `exports/pos_mr1/MR1-pos.csv`
  - BOM: `exports/bom/MR1_BOM.csv`

* **Amplifier Board**:
  - File: `exports/Amplifier_Gerbers.zip`
  - Layers: **2 Layers** (F_Cu, B_Cu)
  - PCB Thickness: **0.8 mm** (Critical for stack elevation in the cartridge!).
  - Surface Finish: **ENIG** (Mandatory for direct contact with golden pogo pins).

### 3D Printing Specifications
* **Nanopore Silicone Wafer Molds** (`Nanopore_Wafer_Mold_Left.stl`, `Right.stl`):
  - Recommended Process: **SLA / DLP Resin** (Formlabs / Elegoo 50?m or 25?m layer height).
  - Material: Tough / Rigid resin. Smooth optical finish prevents air pocket adhesion during silicone curing.
* **Seals & Gaskets** (`Bottom_Pusher_Plate.stl`, `Cast_Nanopore_Wafer_Gasket.stl`):
  - Material: **TPU 85A / 95A** (FDM) or cast liquid silicone (Sorta-Clear 37 / Dragon Skin 20).
* **Structural Housings** (`Housing_Case_Reader.stl`, `Housing_Lid_Reader.stl`, `Torque_Cap_*.stl`):
  - Material: **PETG, ABS, or Polypropylene**.
  - Infill: 30?50% Gyroid for fluidic and clamping rigidity.