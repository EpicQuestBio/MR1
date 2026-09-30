# build123d Porting TODO List

This document outlines the step-by-step strategy for porting the Sentinel Nanopore Reader project from OpenSCAD to `build123d` (Python).

## 1. Constants & Core Utilities (`constants.py` and `common.py`)
- [x] Define global parameter dictionaries/dataclasses mirroring `constants.scad`.
- [x] Port physics calculations (stack height, torque limit, material deflection calculations).
- [x] Create `Circuitry_Cutouts` as a reusable `build123d` Subtractive component (a `Part` or `Location` + `Box` elements).
- [x] Create generic utility functions for 1/8" NPT tapped holes, threaded Luer geometry, and finger grip cutouts.

## 2. Nanopore Wafer Mold (`nanopore_wafer_mold.py`)
- [x] Setup `build123d` basic blocks (`Rounded_Mold_Block`, `Rounded_Reservoir_Block`).
- [x] Port `Nanopore_Wafer_Mold_Left` to a `Part`.
    - Apply `Circuitry_Cutouts` subtraction to the mold (fixing the existing bug).
    - Add fluid port channels, wafer pocket, alignment pins, air bleeds, and central sprue.
- [x] Port `Nanopore_Wafer_Mold_Right` to a `Part`.
    - Add clamping plug, reservoir, bolt holes.
    - Apply `Circuitry_Cutouts` if necessary on the matching half.
- [x] Create Python test scripts to export STEP files for the mold halves.

## 3. Cartridge Stack (`cartridge.py`)
- [x] Port `PCB_Rigid_Active` (and other 2D PCB references).
- [x] Port `Cast_Nanopore_Wafer_Gasket` (silicone body, protrusion, cutouts).
- [x] Port `Fitted_Amplifier_Gasket`.
- [x] Port `Plate_1_Base_Hex` (with NPT threads and fluid port layouts).
- [x] Port `Bottom_Pusher_Plate` (TPU seal with cutouts).
- [x] Port `Plate_3_Top_Hex`.
- [x] Port `Pressure_Puck` (pipette access and finger grip recesses).

## 4. Housings (`housing.py`)
- [x] Port `Housing_Pump_Case` (base, walls, handles, feet).
- [x] Port `Housing_Pump_Lid`.
- [x] Port `Housing_Case_Reader` (base with 2.5mm inset/overhang profile).
- [x] Port `Housing_Lid_Reader` (fluid pass-throughs, USB-C cutouts, internal stack clamping mechanics).

## 5. Adapters and Cap (`adapters.py`, `torque_cap.py`)
- [x] Port `Threaded_Luer_Adapter`.
- [x] Port `Elbow_Adapter`.
- [x] Port `Torque_Cap_Inner` and `Torque_Cap_Outer`.
- [x] Implement torque ratchet springs using `build123d` sweeps or extrusions.

## 6. Main Assembly (`main.py`)
- [x] Create the full 3D assembly combining all components.
- [x] Replicate the visual rendering offsets / exploded views.
- [x] Replace `scripts/export_all.js` with a Python script to iterate through the assembly tree and dump `.step` or `.stl` files.

## 7. Advanced Routing: Flexible Tubing, Wiring, and Connectors
- [x] Define physical routing parameters in `constants.py`:
    - `TUBE_OD` and `TUBE_ID` (e.g., 1/8" ID, 1/4" OD).
    - `MIN_BEND_RADIUS_TUBE` for flexible silicone/polyurethane tubing.
    - `WIRE_GAUGE` and `MIN_BEND_RADIUS_WIRE`.
- [x] Model missing hardware and connector bodies in a new `connectors.py`:
    - JST XH 2.54mm pitch downward-facing header and mating plug.
    - Panel mount USB-C breakout boards/connectors.
    - Ditao pump internal motor terminals / wiring posts.
    - 1/8" Hose Barb x Female Luer panel mount bulkheads (reference `BOM.md`).
- [x] Implement flexible routing sweeps in `assembly.py`:
    - Use `build123d` splines (`Spline`) to sweep tubular profiles connecting the Pump module's Luer bulkheads to the Reader module's side inlet/outlet ports.
    - Model the internal wiring harness connecting the USB-C panel mounts to the Pump motor and the PCB active circuitry.

## 8. Routing Implementation
- [x] Connect the Luer bulkhead models to the `Housing_Pump_Case` and `Housing_Case_Reader` side cutouts.
- [x] Implement `build123d` splines for wire routing from USB-C ports to internal PCB and Motor.
- [x] Implement splines for fluid tubing (1/8" ID x 1/4" OD) connecting adapters to Luer bulkheads.

---

## 9. Collision Checks & Bend Radius Validation (`collision_check.py`)
- [x] Fix duplicate `if __name__ == "__main__":` block (lines 112–119 vs 151–158).
- [x] Add M75×8mm / M76×8mm helical thread engagement check:
    - Test `Housing_Lid_Reader` external thread against `Torque_Cap_Inner` internal thread.
    - Verify zero interference when assembled at nominal engagement depth.
- [x] Implement spline curvature / bend radius validation:
    - Walk each routed spline and compute the instantaneous radius of curvature at sampled points.
    - Assert all bend radii ≥ `MIN_BEND_RADIUS_TUBE` (10 mm) for tubing.
    - Assert all bend radii ≥ `MIN_BEND_RADIUS_WIRE` (10 mm) for wiring.
- [x] Add PCB standoff clearance check:
    - Test tubing envelopes against `Housing_Case_Reader` internal PCB standoff bosses.
- [x] Add internal component clearance checks:
    - Test wiring routes against the cartridge stack solids inside the Reader module.
    - Test tubing against `Plate_1_Base_Hex` NPT adapter protrusions.

## 10. Production-Fidelity Routing (`assembly.py` ↔ `wiring/*.yaml`)
- [x] Upgrade `route_tubing()` to implement all 5 fluid lines from `reader_tubing.yaml`:
    - All lines use standardized **1/8" barb fittings** (uniform 1/8" ID × 1/4" OD cross-section).
    - `TUBE_PUMP`: PharMed BPT (0.12 m) — Buffer reservoir → Peristaltic pump.
    - `TUBE_FEED`: FEP (0.22 m) — Pump → Cis inlet (210°).
    - `TUBE_TRANS_LINE`: PEEK (0.18 m) — Trans outlet (150°) → Waste.
    - `TUBE_WASTE_LINES` (×2): Silicone (0.25 m each) — Cis outlet (30°) → Waste, Trans inlet (330°) → Buffer recirculation.
- [x] Terminate spline endpoints at physical port positions:
    - Use `PORT_RADIUS = 20 mm` and angles (210°, 30°, 330°, 150°) from `constants.py`.
    - Anchor endpoints to actual Luer bulkhead barb positions on housing walls.
- [x] Upgrade `route_wiring()` to implement all 3 electrical harnesses from `reader_wiring.yaml`:
    - `W_USB`: 28 AWG shielded (0.08 m) — USB-C receptacle → MR1 `J_MR1_PWR`.
    - `W_MOTOR`: 24 AWG shielded twisted pair (0.12 m) — MR1 `J_MR1_MOTOR` → Pump DC motor.
    - `W_POGO_ANALOG`: 30 AWG ultra-low-noise (0.09 m) — Mill-Max pogo block → LMP7721 PCB test pads.
- [x] Apply per-harness wire OD and color from YAML specs to swept profiles.

## 11. Export Pipeline & Project Manifests (`main.py`, `package.json`, `*.project.json`)
- [x] Fix export destination: write STEP/STL files to `exports/` directory (not project root).
- [x] Add DXF 2D profile export support (for KiCad PCB ↔ mechanical interface):
    - `Plate_1_Base_DXF`, `Plate_3_Top_DXF`, `Bottom_Pusher_Plate_DXF`.
    - `Gasket_Bottom_DXF`, `Gasket_Main_DXF`, `Gasket_Top_DXF`.
    - `PCB_DXF`, `PCB_Amplifier_DXF`, `PCB_Main_Reader_DXF`.
- [x] Add `JST_XH_2_Pin_Plug` to the export inventory.
- [x] Wire `npm test` in `package.json` to `python run_tests.py`.
- [x] Update `atlas.project.json` mechanical section:
    - Replace monolithic `sentinel_nanopore_reader.stl` and `nanopore_wafer_mold.stl` references with per-part modular exports from `exports/`.
- [x] Update `openauto.project.json`:
    - Ensure all 20+ Build123d parts are listed with correct relative paths in `exports/`.
    - Modularized mold references to point to `exports/Nanopore_Wafer_Mold_Left.stl` and `Right.stl`.

## 12. Connector & Housing Integration (`connectors.py`, `housing.py`, `adapters.py`)
- [x] Replace generic 12×6 mm rectangular cutouts in `Housing_Pump_Case` and `Housing_Lid_Reader` with exact snap-in mounts sized to `USB_C_Panel_Mount()` and `JST_XH_2_Pin_Header()`.
- [x] Add USB-C breakout mounting screw bosses (M2 or M2.5) to housing walls.
- [x] Model swept 1/8" NPT helical threads on `Threaded_Luer_Adapter` (replace simplistic cylinder when `render_threads=True`).
- [x] Improve `Elbow_Adapter` internal geometry:
    - Replace abrupt 90° internal corner with a swept elbow (minimum internal radius to avoid fluidic dead zones / stagnation).

## 13. Parameter Consistency & Cleanup
- [x] Document `PP_H` as a tunable design parameter:
    - `PP_H` (pusher plate height) can grow or shrink based on design needs.
    - Hard constraints: PCB thickness is fixed (0.8 mm); PP sheet stock for plates 1 & 3 comes in standard thicknesses.
    - Current value: `PP_H = 3.0` (matches golden STL and part implementation).
- [x] Audit `render_flythrough.py`:
    - Replace internal `create_nanopore_wafer_mesh()` with direct import from `src.cartridge.Nanopore_Wafer_Silicon()`.
    - Replace hardcoded stack elevation offsets with imports from `assembly.py` constants.

## 14. Test Coverage Expansion (`tests/`)
- [x] Add geometry validation tests for `connectors.py` parts:
    - `JST_XH_2_Pin_Header`, `JST_XH_2_Pin_Plug`, `USB_C_Panel_Mount`, `Luer_Bulkhead_Panel_Mount`.
    - Verify each solid is valid (non-zero volume, manifold BREP).
- [x] Add golden bounds tests for connector parts (match manufacturer datasheets).
- [x] Add bend radius regression test:
    - Asserts all routed splines pass bend radius validation across all 5 fluid lines and 3 wiring harnesses.
- [x] Add production routing collision test:
    - Tests all 5 tubing lines + 3 wiring harnesses against housing/stack solids.

## 15. ESP32-S3 Firmware Architecture & Subsystems (`firmware/`)
- [x] Configure PlatformIO build environment (`platformio.ini`):
    - Target `esp32-s3-devkitc-1` / `esp32s3` with 8MB flash and native USB CDC-ACM on boot.
- [x] Map hardware pinout from KiCad MR1 schematics (`include/pinout.h`):
    - ADC AD40xx SPI bus: CNV (GPIO11), SCK (GPIO10), SDO (GPIO9).
    - DAC MCP4822 SPI bus: CS_ (GPIO6), SCK (GPIO7), SDI (GPIO8), LDAC_ (GPIO5).
    - Native USB CDC: D- (GPIO19), D+ (GPIO20).
    - Pump module UART: TX (GPIO17), RX (GPIO47).
    - Leak detection sensor / weep moat: GPIO1 (ADC1_CH0 / digital pull-up).
- [x] Implement MCP4822 DAC Driver & Pulse Generator (`src/hal/dac_mcp4822.cpp`):
    - Bipolar pore bias voltage setting (-1.587V to +1.587V).
    - Pulse injection logic for pore wetting, unblocking, and translocation tests.
- [x] Implement AD40xx High-Speed ADC Driver (`src/hal/adc_ad40xx.cpp`):
    - Hardware timer + SPI DMA double-buffering for uniform 100 kHz continuous sampling.
    - Decimation engine for low-bandwidth visualization while streaming full rate over USB.
- [x] Implement Native USB CDC High-Speed Streaming & Command Parser (`src/comm/usb_cdc_stream.cpp`):
    - High-throughput binary framing (64 samples/frame, timestamp, CRC-16).
    - Bidirectional ASCII/JSON control channel (bias, sample rate, pump, telemetry).
- [x] Implement External Pump Control & Emergency Safety Protocol (`src/comm/pump_uart.cpp`, `src/hal/leak_detector.cpp`):
    - Bidirectional UART protocol to external pump module over J22.
    - Weep moat / leak sensor monitoring with sub-millisecond pump cutoff and DAC zeroing.
- [x] Implement Web Portal & Embedded Oscilloscope (`src/web/web_portal.cpp`):
    - Wi-Fi AP and station mode with embedded async web server and WebSocket stream.
    - Canvas oscilloscope graticule, voltage slider (-1.587V to +1.587V), pulse buttons, pump controls.
- [x] Dual-Core Task Management & Wi-Fi Contention Handling:
    - Pin high-speed ADC sampling + USB streaming to Core 1.
    - Pin Wi-Fi, Web Server, pump supervision to Core 0.
    - Gracefully throttle or pause Wi-Fi radio during 100 kHz continuous acquisition.

## 16. Universal Project Export System & E2E Deliverables Testing (`exports/`)
- [x] Create Unified Cross-Platform Export Orchestrator (`scripts/export_manager.py`):
    - Auto-detects `build123d`, `kicad-cli`, `wireviz`, Graphviz `dot`, and PlatformIO `pio`.
    - Supports modular domain flags (`--cad`, `--kicad`, `--wiring`, `--firmware`, `--manifest`, `--check`).
- [x] Implement KiCad Manufacturing & Ordering Deliverables:
    - Gerbers, NC drill, Pick-and-Place (POS), BOM CSV, and PDF schematics for MR1 and Amplifier.
    - Automated creation of fab-ready zip bundles (`MR1_Gerbers.zip`, `Amplifier_Gerbers.zip`).
- [x] Implement WireViz Harness & Fluidic Documentation:
    - Automated rendering of `reader_wiring.yaml` and `reader_tubing.yaml` to PNG, SVG, HTML, TSV.
- [x] Implement ESP32-S3 Firmware Build & Artifact Staging:
    - Automatically builds firmware via PlatformIO and stages `firmware.bin`, `bootloader.bin`, `partitions.bin`.
- [x] Implement Project Makefile (`Makefile`):
    - Standard targets: `export`, `export-cad`, `export-kicad`, `export-wiring`, `export-firmware`, `manifest`, `check`, `test`, `test-e2e`.
- [x] Update Universal Bash Scripts:
    - `install.sh`: Environment diagnostics, tool detection, and dependency installation.
    - `scripts/export_all.sh`: POSIX bash export runner with colorized output and flag support.
    - `scripts/run_e2e_tests.sh`: End-to-end regression and verification test runner.
- [x] Implement E2E Deliverables Test Suite (`tests/test_exports_e2e.py`):
    - 9 comprehensive tests validating STL meshes, STEP BREP headers, 2D DXF sections, KiCad Gerbers/drill, fab zip integrity, BOM/PDF headers, WireViz docs, firmware ESP32 magic byte (0xE9), and manifest SHA-256 hashes.
- [x] Document Export Architecture (`EXPORTS.md`):
    - Complete guide for human engineers and AI agents covering commands, inventory, breaking change detection, fab ordering, and 3D printing specs.
- [x] Integrate E2E Deliverables Validation into `run_tests.py` and `package.json`.

## 17. Python Virtual Environment Management (`setup_env.sh`, `setup_env.ps1`)
- [x] Create project `requirements.txt` with locked minimum dependency versions:
    - `build123d>=0.5.0`, `wireviz>=0.4.1`, `graphviz>=0.20`, `platformio>=6.1.0`.
- [x] Create POSIX Bash Virtual Environment Manager (`setup_env.sh`):
    - Automates `.venv` creation, pip upgrading, dependency installation, and health checks (`--check`, `--recreate`).
- [x] Create Windows PowerShell Virtual Environment Manager (`setup_env.ps1`):
    - Robust Windows-native environment setup with automated execution policy handling and diagnostic checks.
- [x] Integrate `.venv` Auto-Detection into Project Tooling:
    - Updated `Makefile` to detect and use `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (POSIX).
    - Updated `scripts/export_all.sh` and `scripts/run_e2e_tests.sh` to prioritize `.venv` over global Python.
    - Updated `install.sh` to delegate environment configuration to `setup_env.sh` rather than modifying global site-packages.
- [x] Fix Build123d 0.12+ `Helix` compatibility:
    - Wrapped `Helix` curve generation in `with BuildLine():` contexts across `src/housing.py`, `src/torque_cap.py`, and `src/adapters.py`.
- [x] Verify Full Test Suite & Manifest inside `.venv`:
    - All 35 unit/E2E tests pass cleanly (100% green).
    - 0 collisions detected across all 6 physical clearance checking suites.

## 18. Legacy OpenSCAD Feature Parity & Export Deliverable Restoration
- [x] Create automated legacy parity unit test suite (`tests/test_legacy_feature_parity.py`):
    - Assert all critical mechanical and electrical interface features from `openscad-legacy/` that were missing in early build123d exports.
- [x] Restore `PCB_Main_Reader_2D` and `PCB_Main_Reader` in `src/cartridge.py`:
    - 80.0 x 60.0 mm rectangular motherboard (replacing invalid 55mm hex sketch).
    - 4x corner standoff mounting holes at `(±38.0, ±28.0)`.
    - 2x USB-C back edge cutouts at `(±15.0, 25.0)`.
    - 1x JST vertical connector cutout at `(0.0, -19.0)`.
    - 4x fluid port clearance holes (D=6.0 mm at `PORT_RADIUS = 20.0 mm`).
- [x] Restore `Carrier_Frame_Hex` (`Plate_2_Channel_DXF`) and `Nanopore_Carrier` (`PCB_Nanopore_Carrier_DXF`):
    - 60mm hexagonal frame with 28.5 x 38.5 mm central pocket and 4 fluid pass-throughs.
    - 20.0 mm circular carrier PCB with 1.5mm central chip aperture and side tab slots.
- [x] Restore `Amplifier_Gasket_Mold_Left` / `Right` exports:
    - Added `is_nanopore=False` mold exports to produce flat gaskets for the amplifier chamber.
- [x] Restore full legacy features on `Housing_Lid_Reader`:
    - 4x vertical fluid pass-through holes (d=10.0 mm at `PORT_RADIUS = 20.0 mm`).
    - Downward JST connector clearance cutout at `(0.0, -19.0)`.
    - 4x horizontal side fluid ports (d=6.35 mm at `Y = ±20.0 mm`).
    - 2.5 mm lower outer wall inset / splash overhang profile.
    - Underside O-ring seal groove and corner screw counterbores.
- [x] Restore full legacy features on `Housing_Pump_Case`:
    - 4x side fluid port bosses (D=20.0 mm, length = 15.0 mm matching OpenSCAD `wall*3`) and through-bores (d=6.35 mm) at `Y = ±20.0 mm`.
    - Internal pump mounting floor plate with dual peristaltic pump cutouts and standoffs.
    - Top knife-edge seal ridge.
- [x] Restore sealing ridges and indexing lips:
    - Added top knife-edge seal ridge to `Housing_Case_Reader`.
    - Added bottom indexing lip (5mm height) and corner counterbores to `Housing_Pump_Lid`.
- [x] Update Export Inventories (`src/main.py` & `scripts/export_manager.py`):
    - Added `Carrier_Frame_Hex`, `Nanopore_Carrier`, `PCB_Main_Reader`, `Amplifier_Gasket_Mold_Left`, and `Amplifier_Gasket_Mold_Right` to 3D parts list.
    - Corrected DXF profile mapping: `PCB_Main_Reader_DXF` and `PCB_DXF` now map to rectangular motherboard; `Plate_2_Channel_DXF` and `PCB_Nanopore_Carrier_DXF` included.
- [x] Update E2E Deliverables Test Suite (`tests/test_exports_e2e.py`):
    - Expanded STL checks from 22 to 27 required solid files.
    - Added `Plate_2_Channel_DXF.dxf` and `PCB_Nanopore_Carrier_DXF.dxf` to DXF verification list.
- [x] Full Verification:
    - All 42 unit and E2E tests pass (100% green).
    - 0 physical collisions across cartridge stack, housing, threading, routing, standoffs, and internals.
    - All 151 export files generated and verified in `exports/manifest.json`.

## 19. PTFE Interposer Architecture & Dual-Sided Ag/AgCl Electrode Synchronization
- [x] Formally define `PTFE_Interposer()` in `src/cartridge.py`:
    - 55.0 x 51.962 x 0.8 mm hexagonal PTFE substrate (Rogers RO4350B / PTFE natural).
    - Central opened 6.20 x 6.20 mm diamond cutout (45 deg) for silicone gasket protrusion.
    - 4 fluid pass-through holes ($d = 2.0\text{ mm}$ clearance) at `PORT_RADIUS = 20.0 mm`.
    - Pogo pin landing array (6 gold pads at $Y = 2.5\text{ mm}$, $X = \pm 1.5, \pm 6.5, \pm 11.5\text{ mm}$).
    - Dual-sided silver chloride (Ag/AgCl) ribbon electrode pads:
        * Top surface (Cis chamber): 2 pads along 30 deg at $r = 12\text{ mm}$ and $r = 17\text{ mm}$.
        * Bottom surface (Trans chamber): 2 pads along 210 deg at $r = 12\text{ mm}$ and $r = 17\text{ mm}$.
    - Weep duct moisture pass-throughs for early leak detection.
    - Established `PCB_Rigid_Active` and `Interposer` as functional aliases of `PTFE_Interposer`.
- [x] Model standalone `Silver_Chloride_Ribbon_Pads` for CAD visualization and assembly:
    - Top ($30^\circ$) and Bottom ($210^\circ$) electrode ribbon strips fitting inside open microfluidic channels.
- [x] Update Export Pipeline (`src/main.py` & `scripts/export_manager.py`):
    - Added `PTFE_Interposer`, `Silver_Chloride_Ribbon_Pads_Top`, and `Silver_Chloride_Ribbon_Pads_Bottom` to 3D STLs and STEPs.
    - Added `Interposer_DXF` and `PCB_Interposer_DXF` to 2D DXF profiles.
    - Regenerated exports manifest: 159 deliverables indexed and verified.
- [x] Expand Test Suites (`tests/test_legacy_feature_parity.py` & `tests/test_exports_e2e.py`):
    - Added `test_ptfe_interposer_features` verifying dimensions, pogo pins, Ag/AgCl pads, and zero collision with top & bottom gaskets.
    - Expanded STL checks to 30 required STL models and 13 DXF profiles.
- [x] Full Verification:
    - 43 / 43 tests pass (100% green).
    - 0 collisions across all 6 physical clearance suites.

## 20. USB-C SBU Auto-Orientation & I2C Polarity Detection (`firmware/src/comm/sbu_i2c_detect.cpp`)
- [x] Configure SBU pinout in firmware (`firmware/include/pinout.h`):
    - `PIN_USB_SBU1` (GPIO12), `PIN_USB_SBU2` (GPIO13), and optional hardware `PIN_SBU_MUX_SEL` (GPIO14).
- [x] Define I2C SBU timing & target addresses (`firmware/include/config.h`):
    - 100 kHz standard-mode I2C frequency, probe timeouts, target addresses (`0x38`, `0x60`, `0x48`).
- [x] Implement SBU Auto-Orientation State Machine (`firmware/src/comm/sbu_i2c_detect.h` / `.cpp`):
    - `SbuI2cDetector` class with dynamic ESP32-S3 GPIO-matrix mapping.
    - Probes Normal orientation (`SBU2 = SDA`, `SBU1 = SCL`) vs Inverted 180° orientation (`SBU1 = SDA`, `SBU2 = SCL`).
    - Recovers gracefully from bus timeouts and reports `NORMAL`, `INVERTED`, `DISCONNECTED`, or `UNKNOWN`.
    - Integrated full address bus scan (`scan_bus()`) across `0x01` to `0x7F`.
- [x] Integrate SBU CLI Commands into USB CDC Streamer (`firmware/src/comm/usb_cdc_stream.cpp`):
    - Added `SBU:DETECT`, `SBU:STATUS`, and `SBU:SCAN` commands.
    - Included SBU connection status and orientation in `STATUS?` JSON telemetry.
- [x] Integrate SBU Detection into Boot Sequence (`firmware/src/main.cpp`):
    - `SbuDetector.begin()` and initial auto-orientation probe run in `setup()`.
- [x] Expand Unit Tests (`tests/test_firmware_protocol.py`):
    - Added `test_sbu_orientation_detection_logic` and `test_sbu_command_protocol`.

## 21. High-Speed 100 kHz Streaming Host DAQ Client (`scripts/daq_client.py`)
- [x] Implement High-Throughput Binary Telemetry Consumer (`scripts/daq_client.py`):
    - Native USB CDC virtual serial connection (921,600+ baud).
    - Little-endian frame synchronization on `"SENT"` magic word (`0x53454E54` -> `b"TNES"`).
    - CRC-16-CCITT packet verification matching firmware polynomial (`0x1021`, init `0xFFFF`).
    - Real-time frame sequence continuity and drop tracking.
- [x] Physical Nanopore Current Calculation & Formatting:
    - Mathematical conversion from 16-bit differential counts to Amperes ($I_{\text{pore}} = V_{\text{adc}} / R_f$).
    - Transimpedance feedback resistor scaling ($1\text{ G}\Omega \implies 1\text{ nA}/1\text{ V}$).
    - Automatic engineering unit formatting (pA, nA, $\mu$A, mA).
- [x] Live Terminal Dashboard & Logging:
    - Real-time CLI telemetry: kS/s sample rate, KB/s bandwidth, packet drops, mean $I_{\text{pore}}$, RMS noise, pump and leak flags.
    - High-speed logging to CSV (`timestamp_us,frame_index,sample_in_frame,raw_adc,current_pa,status_flags`) or raw binary (`.bin`).
- [x] High-Fidelity Mock Simulation Mode (`--mock` / `--sim`):
    - Generates realistic baseline ionic pore currents with noise and simulated transient DNA translocation blockade events (~30% drop, 250 $\mu$s).
    - Emulates all firmware commands for off-target validation and CI.
- [x] Comprehensive DAQ Client Unit & Integration Tests (`tests/test_daq_client.py`):
    - 8 / 8 tests validating CRC16, pack/unpack, corruption rejection, math conversions, mock serial commands, and end-to-end streaming.
- [x] Full Project Test Suite Integration (`run_tests.py`):
    - Expanded test suite to **53 passing tests** (100% green).

## 22. External Pump Controller KiCad Board Architecture (Stretch Goal Roadmap)
- [ ] Mechanical Form Factor:
    - Sized to fit `Housing_Pump_Case` floor plate ($68.0 \times 88.0\text{ mm}$) with M3 mounting holes matching internal standoffs.
- [ ] USB-C Cable Interface & Power Delivery:
    - USB-C receptacle accepting power and data from Reader module.
    - SBU1 / SBU2 lines routed to local I2C slave interface.
    - Hardware USB-PD Sink controller (e.g., CH224K or FUSB302) configured to negotiate 9V or 12V VBUS for pump motors.
- [ ] Motor Drive Stages:
    - Dual H-bridge motor drivers (e.g., TI DRV8837 or DRV8871) or stepper drivers (TMC2209) for peristaltic pumps.
    - Hardware emergency disable input wired directly to leak sensor cutoff.
- [ ] Peripheral Sensors:
    - I2C pressure transducer / bubble sensor interfaces.


