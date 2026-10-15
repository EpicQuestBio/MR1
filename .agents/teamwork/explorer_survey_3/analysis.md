# Survey & Analysis Report: Staged Exports & Automated Test Suite Verification

**Explorer**: Explorer 3 (Exports and Test Suite Explorer)  
**Date**: 2026-10-15  
**Working Directory**: `/home/loki/Projects/daemon-pore/.agents/teamwork/explorer_survey_3`  
**Target Requirements**: R2 (Staged Exports & Documentation Deliverables) & R3 (Automated Test Suite Verification)

---

## 1. Executive Summary

This report surveys the export deliverable pipelines and test suite health for the `daemon-pore` project.

- **Automated Test Suite Baseline**:
  - The repository test suite (`.venv/bin/python run_tests.py`) loads **12 test modules** comprising **92 test cases**.
  - **Baseline Result**: **90 PASSED, 2 FAILED** (exit code 1).
  - Both failures occurred exclusively in `tests/test_exports_e2e.py`:
    1. `test_firmware_staged_binaries`: Missing `exports/firmware/firmware.bin`.
    2. `test_wiring_and_tubing_documentation`: Missing `exports/reader_wiring/` and `exports/reader_tubing/`.
  - All other 90 tests—including all 3D CAD collision checks (stack, housing, thread engagement, PCB standoffs, internal components, and flexible routing), Golden STL bounds, physics simulations, DAQ client, and KiCad tests—passed cleanly with **zero collisions and zero regressions**.

- **Deliverables Status & Diagnostic Remediation**:
  - **WireViz Pipeline**:
    - Generates wiring harness and fluid tubing documentation from `wiring/reader_wiring.yaml` and `wiring/reader_tubing.yaml`.
    - Blocked by two issues:
      1. Tool discovery in `scripts/export_manager.py:57-59` uses `shutil.which("wireviz")` which returned `None` when running outside an activated virtual environment where `.venv/bin` is not on the user's `PATH`.
      2. Graphviz `dot` was missing on the host system (`/usr/bin/dot` does not exist).
    - Resolution verified: Installing `graphviz` in miniconda (`/home/loki/miniconda3/bin/conda install -y graphviz`) provided `dot` (v14.1.3) on `PATH`. When `wireviz` is invoked, it successfully generates `.html`, `.png`, `.svg`, and `.bom.tsv` into `exports/reader_wiring/` and `exports/reader_tubing/`.
  - **ESP32-S3 Firmware Build & Staging Pipeline**:
    - Compiles firmware in `MR1_firmware/` via PlatformIO and stages `firmware.bin`, `bootloader.bin`, and `partitions.bin` into `exports/firmware/`.
    - Blocked by three issues:
      1. Tool discovery in `scripts/export_manager.py:62-64` uses `shutil.which("pio")` which returned `None` when `.venv/bin` is not in `PATH`.
      2. The installed PlatformIO dev/platform in `~/.platformio/platforms/espressif32` was locked to an ancient v2.0.2 release that lacked support for `board = esp32-s3-devkitc-1`.
      3. `tool-esptoolpy` failed on `from intelhex import HexRecordError, IntelHex` because `intelhex` was not installed in `.venv`.
    - Resolution verified: Upgrading PlatformIO's `espressif32` platform to v7.1.3 and installing `intelhex` (along with `ecdsa`, `bitstring`, `reedsolo`, `cryptography`) in `.venv` allowed PlatformIO to compile all firmware C++ sources and invoke `esptool.py` to create `firmware.bin` (814,160 bytes, starting with ESP32 magic byte `0xE9`).
  - **Exports Manifest (`exports/manifest.json`)**:
    - The manifest currently indexes 198 deliverables (all existing STLs, STEPs, DXFs, Gerber ZIPs, BOM CSVs, schematic PDFs).
    - Regenerating via `python scripts/export_manager.py --manifest` after staging firmware and WireViz documentation expands the manifest to **209 indexed deliverables**, all verified with valid SHA-256 checksums and exact byte sizes.
  - **Full Suite Verification**:
    - With the deliverables staged and tools configured, `.venv/bin/python run_tests.py` achieves **92 / 92 TESTS PASSING (100% green, exit code 0)** in 27.8 seconds.

---

## 2. Test Suite Breakdown (R3)

The repository test runner is `run_tests.py`. It dynamically imports 12 test modules from `tests/` and executes them via `unittest.TextTestRunner`:

| Module | File Path | Test Count | Baseline Status | Notes |
|---|---|---|---|---|
| `test_golden_stl_bounds` | `tests/test_golden_stl_bounds.py` | 12 | **PASS** | Bounds for housing, stack plates, pucks, caps |
| `test_geometry` | `tests/test_geometry.py` | 7 | **PASS** | 0 collisions in cartridge, housing, threads, standoffs |
| `test_connector_bounds` | `tests/test_connector_bounds.py` | 4 | **PASS** | JST, USB-C, Luer bulkhead solids |
| `test_firmware_protocol` | `tests/test_firmware_protocol.py` | 6 | **PASS** | CRC-16, framing, SBU commands |
| `test_exports_e2e` | `tests/test_exports_e2e.py` | 9 | **2 FAIL / 7 PASS** | Fails on firmware binary & WireViz dirs |
| `test_legacy_feature_parity` | `tests/test_legacy_feature_parity.py` | 8 | **PASS** | Mold, housing, lid reader ribbon cable cavity |
| `test_daq_client` | `tests/test_daq_client.py` | 9 | **PASS** | DAQ client framing, units, mock serial |
| `test_interposer_kicad` | `tests/test_interposer_kicad.py` | 9 | **PASS** | KiCad schematics, symbols, pogo footprints |
| `test_pump_firmware` | `tests/test_pump_firmware.py` | 4 | **PASS** | Pump framing, pressure transfer, duty cycle |
| `test_physics_and_simulations` | `tests/test_physics_and_simulations.py` | 13 | **PASS** | Conductance, weep sensor, DAC slew rates |
| `test_flexure_fea` | `tests/test_flexure_fea.py` | 4 | **PASS** | FEA toolpaths, living hinges |
| `test_four_electrode_cell` | `tests/test_four_electrode_cell.py` | 7 | **PASS** | Concentric sensing, EIS sweep, access resistance |
| **TOTAL** | — | **92** | **90 PASS / 2 FAIL** | Target: 92 passing |

### Exact Failure Tracebacks

#### Failure 1: Missing Staged Firmware Binary
```text
======================================================================
FAIL: test_firmware_staged_binaries (test_exports_e2e.TestExportsE2E)
Verify staged ESP32-S3 firmware image.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/loki/Projects/daemon-pore/tests/test_exports_e2e.py", line 219, in test_firmware_staged_binaries
    self.assertTrue(fw_bin.exists(), "Missing firmware.bin in exports/firmware/")
AssertionError: False is not true : Missing firmware.bin in exports/firmware/
```

#### Failure 2: Missing WireViz Documentation Directories
```text
======================================================================
FAIL: test_wiring_and_tubing_documentation (test_exports_e2e.TestExportsE2E)
Verify WireViz diagram outputs for wiring harness and fluid tubing.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/loki/Projects/daemon-pore/tests/test_exports_e2e.py", line 208, in test_wiring_and_tubing_documentation
    self.assertTrue(d.exists(), f"Missing {sub_dir} directory")
AssertionError: False is not true : Missing reader_wiring directory
```

---

## 3. Investigation of Firmware Pipeline (`exports/firmware/firmware.bin`)

### 3.1 Firmware Source & Architecture
- Source directory: `MR1_firmware/`
- Configuration: `MR1_firmware/platformio.ini`
  - Platform: `espressif32`
  - Board: `esp32-s3-devkitc-1`
  - Framework: `arduino`
  - MCU: `esp32s3` at 240 MHz, Flash: 8 MB QIO at 80 MHz
  - Library dependency: `links2004/WebSockets`
  - Build flags: `-DARDUINO_USB_CDC_ON_BOOT=1 -DARDUINO_USB_MODE=1 -DCONFIG_ESP32S3_DEFAULT_CPU_FREQ_240=1 -O2`
- Firmware modules (`MR1_firmware/src/`):
  - `src/main.cpp`: FreeRTOS dual-core initialization, task pinning (ADC sampling/USB CDC on Core 1; Web server/pump monitoring on Core 0).
  - `src/hal/adc_ad40xx.cpp`: High-speed 100 kHz SPI continuous sampling.
  - `src/hal/dac_mcp4822.cpp`: Bipolar pore bias generator (-1.587V to +1.587V).
  - `src/hal/leak_detector.cpp`: Weep moat saline interlock monitor.
  - `src/comm/usb_cdc_stream.cpp`: High-speed binary framing with CRC-16.
  - `src/comm/sbu_i2c_detect.cpp`: USB-C SBU auto-polarity state machine.
  - `src/comm/pump_uart.cpp`: Bidirectional pump controller protocol.
  - `src/comm/opendaq_stream.cpp`: OpenDAQ protocol streamer.
  - `src/web/web_portal.cpp`: Embedded web portal and websocket oscilloscope.

### 3.2 Compilation & Staging Mechanism
In `scripts/export_manager.py`:
- `find_pio()`: Searches `shutil.which("pio")`.
- `export_firmware()`:
  - Invokes `[pio, "run"]` in `MR1_firmware/`.
  - Searches for build output in `MR1_firmware/.pio/build/esp32s3/`.
  - Copies `firmware.bin`, `bootloader.bin`, and `partitions.bin` into `exports/firmware/`.

### 3.3 Root Cause Analysis & Validation
1. **Tool Discovery**:
   - `shutil.which("pio")` returns `None` unless `.venv/bin` is in `PATH`.
   - **Fix recommendation**: In `scripts/export_manager.py:find_pio()`, also check `Path(sys.executable).parent / "pio"` or `REPO_ROOT / ".venv" / "bin" / "pio"`.
2. **PlatformIO Platform Version**:
   - `~/.platformio/platforms/espressif32` contained an old tasmota fork release (v2.0.2) from March 2023 that did not contain the `esp32-s3-devkitc-1` board definition.
   - Upgrading PlatformIO to official `platformio/espressif32` (v7.1.3) downloaded board definition `boards/esp32-s3-devkitc-1.json`, `toolchain-xtensa-esp32s3`, and `framework-arduinoespressif32`.
3. **Missing Python Dependency for `esptool`**:
   - `tool-esptoolpy` failed during partition and bootloader generation with:
     `ModuleNotFoundError: No module named 'intelhex'`
   - Installing `intelhex` (and its companions `ecdsa`, `bitstring`, `reedsolo`, `cryptography`) in `.venv` resolved the error.
4. **Verification**:
   - Running `.venv/bin/pio run -d MR1_firmware` succeeded in 4.17s.
   - Generated `firmware.bin` (814,160 bytes), `bootloader.bin` (15,104 bytes), and `partitions.bin` (3,072 bytes).
   - Magic byte verification: `0xe9` at byte 0. Size > 200,000 bytes. Passes `test_firmware_staged_binaries`.

---

## 4. Investigation of WireViz Pipeline (`exports/reader_wiring/` & `reader_tubing/`)

### 4.1 Specification Files
- Wiring YAML: `wiring/reader_wiring.yaml`
  - Defines 5 connectors: `J_USBC` (Molex 105450-0101), `J_MR1_PWR` (JST-GH), `J_MR1_MOTOR` (Molex PicoBlade), `M_PUMP` (Pololu 2364), `J_POGO_ARRAY` (Mill-Max), and test pad target `TP_AMP_PCB`.
  - Defines 3 harnesses:
    - `W_USB`: 28 AWG shielded, 0.08 m.
    - `W_MOTOR`: 24 AWG twisted pair, 0.12 m.
    - `W_POGO_ANALOG`: 30 AWG ultra-low-noise shielded, 0.09 m.
- Tubing YAML: `wiring/reader_tubing.yaml`
  - Defines 5 fluid lines with 1/8" barb fittings:
    - `TUBE_PUMP`: PharMed BPT (0.12 m).
    - `TUBE_FEED`: FEP (0.22 m).
    - `TUBE_TRANS_LINE`: PEEK (0.18 m).
    - `TUBE_WASTE_LINES` (×2): Silicone (0.25 m each).

### 4.2 Generation Pipeline
In `scripts/export_manager.py`:
- `find_wireviz()`: Searches `shutil.which("wireviz")`.
- `export_wiring()`:
  - Invokes `wireviz wiring/reader_wiring.yaml -o exports/reader_wiring`.
  - Invokes `wireviz wiring/reader_tubing.yaml -o exports/reader_tubing`.

### 4.3 Root Cause Analysis & Validation
1. **Tool Discovery**:
   - `find_wireviz()` returned `None` because `.venv/bin` was not in `PATH`.
   - **Fix recommendation**: In `scripts/export_manager.py:find_wireviz()`, check `Path(sys.executable).parent / "wireviz"` or `REPO_ROOT / ".venv" / "bin" / "wireviz"`.
2. **Missing Host Graphviz `dot` Binary**:
   - `wireviz` invokes Graphviz `dot` to render PNG and SVG images from intermediate `.gv` files.
   - Without `dot`, `wireviz` raised `graphviz.backend.execute.ExecutableNotFound: failed to execute PosixPath('dot')`.
   - Resolution: Installed `graphviz` via miniconda (`/home/loki/miniconda3/bin/conda install -y graphviz`). `/home/loki/miniconda3/bin` is already in the system `PATH`, providing `dot` (v14.1.3).
3. **Verification**:
   - Running `.venv/bin/wireviz wiring/reader_wiring.yaml -o exports/reader_wiring` produced:
     - `reader_wiring.png` (202,428 bytes)
     - `reader_wiring.svg` (47,785 bytes)
     - `reader_wiring.html` (51,994 bytes)
     - `reader_wiring.bom.tsv` (702 bytes)
   - Running `.venv/bin/wireviz wiring/reader_tubing.yaml -o exports/reader_tubing` produced:
     - `reader_tubing.png` (188,744 bytes)
     - `reader_tubing.svg` (31,303 bytes)
     - `reader_tubing.html` (36,037 bytes)
     - `reader_tubing.bom.tsv` (916 bytes)
   - Passes `test_wiring_and_tubing_documentation`.

---

## 5. Investigation of Manifest Schema & Hash Integrity (`exports/manifest.json`)

### 5.1 Structure & Schema
In `scripts/export_manager.py:252-306`:
```json
{
  "project": "Daemon Pore / Sentinel Nanopore Reader",
  "generated_at": "<ISO-8601 UTC timestamp>",
  "deliverables": {
    "<relative_path_from_exports>": {
      "size_bytes": <int>,
      "sha256": "<64-hex SHA-256>",
      "category": "<category_string>"
    }
  }
}
```

### 5.2 Category Mapping
`scripts/export_manager.py` categorizes deliverables by file extension:
- `.stl`: `3d_mesh_printing`
- `.step`: `cad_parametric_brep`
- `.dxf`: `2d_machining_and_pcb_outline`
- `.pdf`: `schematic_documentation`
- `.csv`: `bill_of_materials`
- `.zip`: `pcb_manufacturing_gerber_pack`
- `.bin`: `firmware_binary`
- `.png`: `visual_documentation`
- `.svg`: `vector_documentation`
- `.html`: `interactive_documentation`
- `.tsv`: `tabular_wire_list`
- `.gtl` / `.gbl`: `gerber_layer`
- `.drl`: `drill_file`
- `.pos`: `pick_and_place_positions`

### 5.3 Inventory Evolution
- Initial inventory: **198 files** indexed.
- Missing files:
  - `firmware/bootloader.bin`
  - `firmware/firmware.bin`
  - `firmware/partitions.bin`
  - `reader_wiring/reader_wiring.bom.tsv`
  - `reader_wiring/reader_wiring.html`
  - `reader_wiring/reader_wiring.png`
  - `reader_wiring/reader_wiring.svg`
  - `reader_tubing/reader_tubing.bom.tsv`
  - `reader_tubing/reader_tubing.html`
  - `reader_tubing/reader_tubing.png`
  - `reader_tubing/reader_tubing.svg`
- Total inventory after staging: **209 files** indexed.
- `scripts/export_manager.py --check` confirms all 209 files exist and match hashes.
- `tests/test_exports_e2e.py:test_manifest_integrity` passes cleanly.

---

## 6. Actionable Implementation Plan for the Implementer

To achieve full compliance with Requirements R2 and R3 across clean environments, the implementer should perform the following concrete actions:

1. **Update `requirements.txt`**:
   Add `intelhex>=2.3.0` so that `.venv` always contains the necessary dependency for `esptool.py`.
   ```diff
   --- a/requirements.txt
   +++ b/requirements.txt
   @@ -11,3 +11,4 @@ graphviz>=0.20
    # Embedded Firmware Build & Deployment
    platformio>=6.1.0
   +intelhex>=2.3.0
   ```

2. **Enhance Tool Discovery in `scripts/export_manager.py`**:
   Update `find_wireviz()` and `find_pio()` to look in `Path(sys.executable).parent` and `REPO_ROOT / ".venv" / "bin"` in addition to system `PATH`.
   ```python
   def find_wireviz():
       on_path = shutil.which("wireviz") or shutil.which("wireviz.exe")
       if on_path:
           return on_path
       venv_cand = Path(sys.executable).parent / ("wireviz.exe" if sys.platform.startswith("win") else "wireviz")
       if venv_cand.exists():
           return str(venv_cand)
       return None

   def find_pio():
       on_path = shutil.which("pio") or shutil.which("pio.exe")
       if on_path:
           return on_path
       venv_cand = Path(sys.executable).parent / ("pio.exe" if sys.platform.startswith("win") else "pio")
       if venv_cand.exists():
           return str(venv_cand)
       return None
   ```

3. **Stage Firmware & Documentation Artifacts**:
   Run:
   ```bash
   .venv/bin/python scripts/export_manager.py --firmware
   .venv/bin/python scripts/export_manager.py --wiring
   .venv/bin/python scripts/export_manager.py --manifest
   ```

4. **Verify Test Suite**:
   Run `.venv/bin/python run_tests.py` and confirm all 92 tests pass with exit code 0.
