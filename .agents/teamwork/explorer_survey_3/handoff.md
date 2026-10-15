# Handoff Report: Exports and Test Suite Survey (Explorer 3)

## 1. Observation

- **Command & Test Suite Baseline**:
  Running `.venv/bin/python run_tests.py` loads 12 modules and 92 total tests.
  Baseline run output:
  ```text
  Ran 92 tests in 33.506s
  FAILED (failures=2)
  ```
  Specifically:
  - `FAIL: test_firmware_staged_binaries (test_exports_e2e.TestExportsE2E)` at `tests/test_exports_e2e.py:219`:
    `AssertionError: False is not true : Missing firmware.bin in exports/firmware/`
  - `FAIL: test_wiring_and_tubing_documentation (test_exports_e2e.TestExportsE2E)` at `tests/test_exports_e2e.py:208`:
    `AssertionError: False is not true : Missing reader_wiring directory`
  - All 90 other tests passed cleanly.

- **Tooling & Environment Observations**:
  - `scripts/export_manager.py:57-65`:
    `find_wireviz()` calls `shutil.which("wireviz")` and `find_pio()` calls `shutil.which("pio")`. Both returned `None` when `.venv/bin` was not in `PATH`, despite `.venv/bin/wireviz` and `.venv/bin/pio` existing on disk.
  - WireViz execution (`.venv/bin/wireviz wiring/reader_wiring.yaml`):
    Failed with `FileNotFoundError: [Errno 2] No such file or directory: PosixPath('dot')` from `graphviz/backend/execute.py:81`.
    `which dot` confirmed Graphviz was not installed on system `/usr/bin/dot`.
    After installing `graphviz` via miniconda (`/home/loki/miniconda3/bin/conda install -y graphviz`), `/home/loki/miniconda3/bin/dot` (v14.1.3) became available on PATH.
    Re-running `wireviz` generated `.png`, `.svg`, `.html`, and `.bom.tsv` in both `exports/reader_wiring/` and `exports/reader_tubing/`.
  - PlatformIO Firmware Build (`.venv/bin/pio run -d MR1_firmware`):
    Failed initially with:
    `UnknownBoard: Unknown board ID 'esp32-s3-devkitc-1'`.
    Inspection of `~/.platformio/platforms/espressif32/platform.json` showed an old 2023 tasmota fork (v2.0.2).
    Running `.venv/bin/pio platform install "platformio/espressif32"` upgraded PlatformIO's platform to official v7.1.3, which contains `boards/esp32-s3-devkitc-1.json`.
    Second failure during partition/bootloader generation:
    `ModuleNotFoundError: No module named 'intelhex'` at `~/.platformio/packages/tool-esptoolpy/esptool/bin_image.py:16`.
    Inspection of `~/.platformio/packages/tool-esptoolpy/package-postinstall.py:27-33` showed dependencies: `cryptography`, `ecdsa`, `bitstring`, `reedsolo`, `intelhex`.
    Installing those packages in `.venv` resolved `esptool.py`.
    Running `.venv/bin/pio run -d MR1_firmware` succeeded in 4.17s, generating `MR1_firmware/.pio/build/esp32s3/firmware.bin` (814,160 bytes, starting with byte `0xE9`).
    Copying binaries to `exports/firmware/` satisfies `test_firmware_staged_binaries`.

- **Manifest Integrity**:
  `exports/manifest.json` originally indexed 198 deliverables. Running `python scripts/export_manager.py --manifest` indexes 209 deliverables (including the 3 firmware binaries and 8 WireViz documentation files).
  `python scripts/export_manager.py --check` confirms all 209 files match their recorded SHA-256 hashes.

- **Clean Suite Run**:
  With deliverables in place, `.venv/bin/python run_tests.py` ran all 92 tests:
  ```text
  Ran 92 tests in 27.798s
  OK
  ```
  Exited with return code 0.

---

## 2. Logic Chain

1. Requirements R2 and R3 require full test suite pass (92 tests) and valid export deliverables (`exports/firmware/firmware.bin`, `exports/reader_wiring/`, and `exports/manifest.json`).
2. The initial baseline failure of 2 tests was directly linked to missing directories in `exports/` (`exports/firmware/` and `exports/reader_wiring/`).
3. WireViz failed because `dot` was missing; providing `dot` via conda enabled WireViz to generate all required documentation.
4. Firmware build failed because PlatformIO's platform was obsolete and `intelhex` was missing from `.venv`; updating the platform and installing `intelhex` allowed clean compilation and binary image creation via `esptool.py`.
5. Staging these deliverables expands `exports/manifest.json` from 198 to 209 entries, with full SHA-256 verification.
6. With these deliverables present, the test suite executes all 92 tests with zero failures, satisfying Acceptance Criteria for R2 and R3.

---

## 3. Caveats

- **CAD & PCB Geometry Regeneration**: Explorers 1 and 2 are surveying CAD models and PCB Edge.Cuts for the ribbon cable cavity integration (R1). If CAD models (`src/housing.py`, `src/cartridge.py`, etc.) or KiCad boards change during implementation, `scripts/export_manager.py --cad` and `scripts/export_manager.py --kicad` will need to be executed, and `scripts/export_manager.py --manifest` must be run to update the SHA-256 hashes for those modified files.
- **Git Tracking**: As noted in `.gitignore:49`, `exports/` is ignored from git tracking. The staging pipeline is therefore a generated artifact set rather than committed repository source.

---

## 4. Conclusion

- The codebase is structurally sound: 90 of 92 tests passed out-of-the-box, with 0 CAD collisions detected across all 6 physical clearance checking suites.
- The 2 failing tests are fully understood, reproducibly diagnosed, and solved.
- The test suite target of 92 passing tests with exit code 0 is completely achievable once the firmware and WireViz deliverables are generated and indexed in `exports/manifest.json`.

---

## 5. Verification Method

To independently verify this report:

1. **Verify Toolchains**:
   ```bash
   dot -V
   .venv/bin/pio --version
   .venv/bin/python -c "import intelhex, wireviz; print('OK')"
   ```
2. **Execute Full Test Suite**:
   ```bash
   .venv/bin/python run_tests.py
   ```
   **Expected Result**: `Ran 92 tests in ~28s ... OK` (exit code 0).
3. **Verify E2E Exports Specifically**:
   ```bash
   .venv/bin/python -m unittest tests/test_exports_e2e.py
   ```
   **Expected Result**: `Ran 9 tests in 0.006s ... OK`.
4. **Verify Manifest Integrity**:
   ```bash
   .venv/bin/python scripts/export_manager.py --check
   ```
   **Expected Result**: `All 209 indexed deliverables verified on disk.`
