# MR1 Nanopore Reader (MR1)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![build123d](https://img.shields.io/badge/CAD-build123d-orange.svg)](https://github.com/gumyr/build123d)
[![KiCad 10.0](https://img.shields.io/badge/EDA-KiCad%2010.0-blueviolet.svg)](https://kicad.org/)
[![PlatformIO](https://img.shields.io/badge/Firmware-PlatformIO%20ESP32--S3-yellowgreen.svg)](https://platformio.org/)
[![Tests](https://img.shields.io/badge/Tests-100%20Passing%20(0%20Collisions)-brightgreen.svg)](#testing--verification)

The **MR1 Nanopore Reader** is an open-source, ultra-low-noise solid-state and biological nanopore sequencer flow cell, low-current transimpedance amplifier, and automated fluidic control system. It integrates high-precision parametric CAD models (`build123d`), ultra-low-leakage analog front-end electronics (KiCad), an automated dual-pump fluidic handler, and an ESP32-S3 high-speed continuous streaming firmware stack.

## Architecture & Overview
The system uses a complete **4-electrode topology** (Working Electrode `WE_POS`, Working Sense `WS_CIS`, Reference Electrode `RE_TRANS`, Counter Electrode `CE_GNDA`) combined with explicitly driven guards (`GUARD`, `GUARD_TRANS`) across a 12-pin interface to achieve sub-picoampere sensitivity while neutralizing the effects of stray capacitance and dielectric surface leakage.

The architecture consists of:
- **Headstage Hardware**: A custom, low-parasitic PTFE/Rogers interposer cartridge that seats a 4x4mm nanopore wafer clamped within silicone PDMS gaskets. It interfaces via gold-plated pogo pins to a low-bias-current transimpedance amplifier (LMP7721) mounted beneath the flowcell.
- **Reader Hardware (MR1)**: An ESP32-S3-driven core processing node operating a continuous 100 kHz SPI DMA data acquisition sequence, dual DACs for precision transmembrane voltage bias, and USB CDC-ACM streaming logic.
- **Pump / Power Subsystem**: A dedicated USB-PD powered board managing automated fluidic dispensing (peristaltic motors), pressure sensing, and SBU-based I2C communication back to the main MR1 host.
- **Data Ingestion Pipeline**: High-throughput IPC software utilizing python scripts (`daq_client.py`) and zeroMQ / WebSocket endpoints to reliably process, structure, decode, and log the real-time electrical data for machine learning basecalling or browser visualization.

## Setup & Prerequisites
To build, modify, or interact with this repository, ensure your environment meets these requirements.

### Toolchain Prerequisites
- **Python**: 3.10+
- **KiCad**: Version 7.0+ (For PCB design modifications and scripting exports)
- **PlatformIO Core (CLI)**: For firmware compilation (`pio run`)
- **OpenSCAD / build123d**: For generating solid body parts.
- **Node.js**: v18+ (For UI and test automation dependencies)

### Environment Setup
Run the bootstrap setup scripts depending on your OS to establish a clean python virtual environment and node module cache.
```bash
# On Linux/macOS
./setup_env.sh

# On Windows (PowerShell)
.\setup_env.ps1
```

Activate the python virtual environment:
```bash
source .venv/bin/activate
```

### Build & Test
You can trigger the comprehensive unit, integration, and dimension-parity tests using the included test suite.
```bash
# Ensure you have activated the virtual environment and built assets
python run_tests.py
# Or directly via pytest
pytest tests/
```

To build and upload firmware to the MR1 reader or the Pump board:
```bash
# Navigate to the target directory
cd MR1_firmware  # or cd Pump_firmware
pio run --target upload
```

## License

This project is released under the **GNU Affero General Public License v3.0 (AGPLv3)**.

Copyright (C) 2026 Lawrence R. Kincheloe III / Molecular Reality Corp.
See the `LICENSE` file for the full text.


---



## Table of Contents

- [Architecture & Overview](#architecture--overview)
- [Setup & Prerequisites](#setup--prerequisites)
- [License](#license)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Quick Start & Environment Setup](#quick-start--environment-setup)
- [Deliverables & Export System](#deliverables--export-system)
- [OpenAuto-CFD & Co-Design](#openauto-cfd--co-design)
- [3D Visualizer & Interactive Inspection](#3d-visualizer--interactive-inspection)
- [KiCad Action Plugin & CLI](#kicad-action-plugin--cli)
- [Testing & Verification](#testing--verification)
- [Hardware & Electronics](#hardware--electronics)
- [ESP32-S3 Firmware](#esp32-s3-firmware)
- [Fluidic Routing & Mold Casting](#fluidic-routing--mold-casting)
- [Documentation Index](#documentation-index)

## System Architecture

```
                       +---------------------------------------+
                       |           Host PC / Laptop            |
                       |  (High-Throughput Binary Telemetry)   |
                       +-------------------+-------------------+
                                           | J1_HOST (USB-C Cable: USB-PD Sink + High-Speed Data)
                                           v
                       +---------------------------------------+
                       |      Pump Module Board (Pump/)        |
                       |  - STUSB4500 Autonomous USB-PD Sink   |
                       |  - TS3USB221 USB 2.0 Streaming Pass   |
                       |  - STM32G431 Control MCU @ 170 MHz    |
                       |  - Dual Honeywell ABP2 Pressure Sens  |
                       |  - Dual DRV8837C Peristaltic Drivers  |
                       |  - Clean Regulated 5V Output Filter   |
                       +-------------------+-------------------+
                                           | J2_MR1 (USB-C Link: +5V_MR1_CLEAN + SBU I2C + USB)
                                           v
                       +---------------------------------------+
                       |         ESP32-S3 MCU (MR1)            |
                       |  Core 1: ADC SPI DMA & USB CDC Stream |
                       |  Core 0: Web Server, Leak & Pump Ctrl |
                       +---------+-------------------+---------+
                                 |                   |
            SPI Bus (100 kHz)    |                   | UART (J22) / SBU I2C
                                 v                   v
     +-----------------------------+        +--------------------------+
     |     AD40xx 16/18-Bit ADC    |        |  Dual Peristaltic Pumps  |
     |   LMP7721 Ultra-Low-Noise   |        |  (Cis & Trans Chambers)  |
     |     Cartridge Amplifier     |        +--------------------------+
     +--------------+--------------+
                    | Gold Pogo Pins (Ultra-low noise shielded)
                    v
     +---------------------------------------------------------+
     |              Hexagonal Cartridge Flow Cell              |
     |  - Cis & Trans Fluidic Chambers ('X' microfluidic)      |
     |  - Cast Silicone Gasket with Nanopore Silicon Wafer     |
     |  - M75x8mm Clamping Torque Cap & Pressure Puck          |
     |  - Conductive Weep Moat / Leak Detection Sensor         |
     +---------------------------------------------------------+
```

---

## Project Structure

```
mr1/
├── src/                          # Parametric CAD models (build123d / Python)
│   ├── cartridge.py              # Flow cell cartridge stack & PCB models
│   ├── housing.py                # Reader and Pump housings, lids, mounting
│   ├── nanopore_wafer_mold.py    # Interlocking two-part resin casting mold
│   ├── torque_cap.py             # M75/M76 ratcheting torque limiter cap
│   ├── adapters.py               # Luer-lock and threaded NPT fluidic adapters
│   ├── connectors.py             # USB-C, JST XH, and bulkhead panel mounts
│   ├── assembly.py               # Full 3D assembly & 3D spline routing sweeps
│   ├── collision_check.py        # Automated 3D BREP collision & clearance checker
│   └── constants.py              # Central engineering & physical parameters
├── MR1/                          # KiCad 10.0 project for Main Reader Board (6-Layer)
├── Amplifier/                    # KiCad 10.0 project for Cartridge Transimpedance Amp (2-Layer)
├── Pump/                         # KiCad 10.0 project for Pump Controller & USB-PD Hub (4-Layer)
├── MR1_firmware/                 # ESP32-S3 C++ firmware (PlatformIO)
│   ├── include/                  # Pinout mapping, binary protocol framing, web portal
│   ├── src/hal/                  # AD40xx SPI DMA ADC, MCP4822 DAC, Leak Detector
│   ├── src/comm/                 # High-speed USB CDC streaming & UART Pump protocol
│   └── src/web/                  # Embedded Web Portal with WebSocket Oscilloscope
├── wiring/                       # WireViz electrical and fluidic harness specs
│   ├── reader_wiring.yaml        # USB-C, motor, and analog pogo wiring harnesses
│   └── reader_tubing.yaml        # FEP, PharMed BPT, and silicone fluidic tubing specs
├── tests/                        # Automated unit, CAD bounds, firmware, and E2E tests
│   ├── test_geometry.py          # Geometric validity and collision regression
│   ├── test_golden_stl_bounds.py # Dimensional assertions against golden models
│   ├── test_connector_bounds.py  # Connector mounting dimensional checks
│   ├── test_firmware_protocol.py # Binary framing, CRC-16, and DAC mapping tests
│   └── test_exports_e2e.py       # Full deliverables validation (141 files)
├── scripts/                      # Build, export, and testing automation
│   ├── export_manager.py         # Universal multi-domain export orchestrator
│   ├── export_all.sh             # POSIX bash export runner
│   └── run_e2e_tests.sh          # POSIX bash end-to-end test runner
├── exports/                      # Generated release deliverables & manifest
├── requirements.txt              # Pinned Python virtual environment dependencies
├── setup_env.sh                  # Virtual environment manager (Linux/macOS/Bash)
├── setup_env.ps1                 # Virtual environment manager (Windows PowerShell)
├── Makefile                      # Standard project build and export targets
├── EXPORTS.md                    # Detailed deliverables and ordering documentation
├── BOM.md                        # Mechanical bill of materials & sourcing links
└── CASTING.md                    # PDMS/Silicone flow cell casting guidelines
```

---

## Quick Start & Environment Setup

### 1. Initialize Python Virtual Environment

The project uses a local virtual environment (`.venv`) for all Python CAD generation, export pipelines, and test suites.

**On Windows (PowerShell):**
```powershell
.\setup_env.ps1
```

**On Linux / macOS / Git Bash:**
```bash
chmod +x setup_env.sh install.sh
./setup_env.sh
```

To verify environment health at any time:
```bash
./setup_env.sh --check        # or powershell -File .\setup_env.ps1 -Check
```

### 2. Required External Tools (Optional for specific export domains)
- **KiCad 10.0 CLI** (`kicad-cli`): Required to generate Gerbers, Drill files, Pick & Place CSVs, BOMs, and PDF schematics.
- **Graphviz** (`dot`): Required by WireViz for rendering graphical wiring and tubing diagrams.
- **PlatformIO Core** (`pio`): Required to compile ESP32-S3 firmware binaries.

---

## Deliverables & Export System

The repository features an automated multi-domain export orchestrator (`scripts/export_manager.py`) managed via GNU Make, shell scripts, or npm:

### Common Commands

```bash
# Export all project deliverables (CAD, KiCad, Wiring, Firmware, and Manifest)
make export

# Or export specific domains
make export-cad        # 3D Solids (STEP/STL) & 2D CNC Profiles (DXF)
make export-kicad      # Gerbers, Drill, POS, BOM, and PDF schematics
make export-wiring     # WireViz wiring harness and fluidic diagrams
make export-firmware   # Compile and stage ESP32-S3 firmware binaries

# Verify manifest and deliverables
make check             # Verify all 141 indexed deliverables exist on disk
make test              # Run unit tests and CAD collision clearance checks
make test-e2e          # Run end-to-end deliverables validation test
```

### Generated Deliverables Inventory (`exports/`)
- **30 STL Meshes**: Ready for 3D printing (SLA resin molds, TPU pusher plates, PETG housings, and PTFE interposer models).
- **22 STEP Models**: Parametric BREP solids for mechanical assembly and CAD exchange.
- **13 DXF Profiles**: 2D profiles for CNC milling polypropylene sheet stock and synchronizing KiCad PCB `Edge.Cuts` (including `Interposer_DXF.dxf` and `Plate_2_Channel_DXF.dxf`).
- **Fab-Ready PCB Archives**: `MR1_Gerbers.zip` (6-layer main board) and `Amplifier_Gerbers.zip` (2-layer amplifier).
- **Manufacturing Documentation**: Pick-and-Place (POS) coordinates, BOM CSVs, and multi-sheet schematic PDFs.
- **Harness Documentation**: WireViz diagrams for internal wiring and 1/8" barb fluidic tubing.
- **ESP32-S3 Firmware**: Staged `firmware.bin`, `bootloader.bin`, and `partitions.bin`.
- **SHA-256 Manifest**: `exports/manifest.json` tracks file sizes and cryptographic hashes for all 159 files for drift detection.

See [EXPORTS.md](EXPORTS.md) for full details and PCB fabrication recommendations.

---

## OpenAuto-CFD & Co-Design

The **Sentinel Nanopore Reader** incorporates the **OpenAuto-CFD** co-design framework ([`openauto.project.json`](openauto.project.json) / [`atlas.project.json`](atlas.project.json)) to bridge Electrical CAD (KiCad), Mechanical CAD (Build123d / OpenSCAD), and Microfluidic Multiphysics into a single automated pipeline.

### Why OpenAuto-CFD?
Nanopore sensing demands precise hydrodynamic and electro-chemical alignment:
1. **Laminar Stokes Flow ($\text{Re} \ll 1$):** With $50\,\mu\text{m} \times 25\,\mu\text{m}$ channels and $10\,\mu\text{L/min}$ delivery, OpenAuto-CFD calculates viscous pressure drops ($\Delta P \approx 6.2\text{ kPa}$) and eliminates turbulent vortex formation.
2. **SiN Membrane Burst Safety:** Free-standing $20\text{ nm}$ silicon nitride membranes rupture at differential pressures $\Delta P_{\text{burst}} \sim 10\text{ mbar}$. OpenAuto-CFD co-simulation balances hydrodynamic resistance across Cis and Trans chambers to prevent wafer fracture.
3. **Dead-Volume & Bubble Prevention:** Eliminates stagnation recirculation zones ($\vec{v} < 0.01 \cdot v_{\text{bulk}}$) that trap air microbubbles or cause analyte sample carryover.
4. **Concentric Kelvin Cell Coupling:** Aligns the 4-electrode Kelvin sensing array on the PTFE interposer directly with the microfluidic chamber aperture.

See the comprehensive [OpenAuto-CFD Guide](docs/OPENAUTO_CFD.md) for full physical derivations and co-simulation specs.

---

## 3D Visualizer & Interactive Inspection

The repository provides a rich multi-layer 3D visualizer powered by `build123d` and `ocp_vscode`:

```bash
# Launch interactive 3D assembly visualizer
npm run visualize
# Or via Python directly:
python src/assembly.py

# Or launch via install script diagnostic flag:
./install.sh --viewer
```

### Visualizer Features
- **Full System Assembly:** Displays the Peristaltic Pump base module, Reader Housing & Tower, 4× Luer Bulkhead Panel Mounts, 7-layer Cartridge Stack (Bottom Pusher Plate, Base Hex Plate, Fitted Gasket, Active PCB, Wafer Gasket, Top Hex Plate, Pressure Puck), and Torque-Lock Cap.
- **3D Swept Tubing Routes:** Renders actual 3D splines for all 5 fluidic paths (`TUBE_PUMP`, `TUBE_FEED`, `TUBE_TRANS_LINE`, `TUBE_WASTE_1`, `TUBE_WASTE_2`) with verified bend radii.
- **X-Ray & Clipping Plane Inspection:** Enables cross-sectional slicing to verify internal gasket compression and pogo pin deflection.
- **WireViz Electrical & Tubing Harnesses:** Generates SVG and HTML diagrams for internal wiring (`wiring/reader_wiring.yaml`) and fluid lines (`wiring/reader_tubing.yaml`) via `npm run export:wiring`.
- **Automated 360° Flythrough Video:** Renders photorealistic rotating orbits using PyVista VTK via `npm run render:flythrough`.

---

## KiCad Action Plugin & CLI

The repository includes a dedicated KiCad Action Plugin and CLI verification engine ([`plugins/openauto_cfd_plugin.py`](plugins/openauto_cfd_plugin.py)) ensuring PCB layouts strictly comply with mechanical, fluidic, and manifest constraints.

### How to Install the Plugin into KiCad
```bash
# Install plugin into active KiCad installation (~/.local/share/kicad/ or %APPDATA%/kicad/)
npm run openauto:install-plugin
# Or via Python:
python plugins/openauto_cfd_plugin.py --install
```

### Using Inside KiCad PCB Editor (GUI)
1. Open any board (`Amplifier.kicad_pcb`, `MR1.kicad_pcb`, `Pump.kicad_pcb`, or `Interposer.kicad_pcb`).
2. Navigate to **Tools $\to$ External Plugins $\to$ OpenAuto-CFD: Co-Design & Clearance Verifier**.
3. The plugin parses the board, checks Edge.Cuts continuity, verifies bounding dimensions against `openauto.project.json`, and displays a comprehensive verification report.

### Standalone CLI & CI/CD Verification
```bash
# Validate all 4 boards in headless mode (Edge.Cuts continuity, dimensions, and net mapping)
npm run openauto:validate

# Synchronize Edge.Cuts dimensions back into the openauto.project.json manifest
npm run openauto:sync
```

---

## Testing & Verification

The project enforces zero physical interference and strict dimensional fidelity across all hardware interfaces:

```bash
# Run the complete test suite (Unit Tests, Collision Checks, Firmware Protocol, Parity, and E2E)
python run_tests.py
```

### Automated Validation Includes:
1. **Golden STL & PCB Bounds**: Asserts dimensions of all generated CAD models against benchmark constraints.
2. **BREP Collision Clearance (6 Independent Suites)**:
   - Cartridge stack component alignment.
   - Housing and lid clearances.
   - M75×8mm external / M76×8mm internal helical thread engagement (0 interference volume).
   - PCB standoff clearances against fluidic lines.
   - Internal component clearance (wiring vs. cartridge solids).
   - Flexible routing collision sweeps against module envelopes.
3. **Spline Bend Radius Validation**: Computes instantaneous curvature along swept routes and verifies compliance with minimum bend radii (Silicone/FEP tubing $\ge 10\text{ mm}$, Wiring $\ge 10\text{ mm}$).
4. **Legacy OpenSCAD Parity Suite**: Validates 80x60mm rectangular motherboard, hexagonal carrier frame, circular nanopore carrier, mold modes, lid cutouts, and pump case bosses.
5. **Firmware Protocol Tests**: CRC-16 integrity, binary packet serialization (`StreamFrame`), pump packet XOR checksums, and DAC voltage-to-code mapping.
6. **E2E Deliverables Tests**: Validates headers, non-zero file sizes, and SHA-256 hashes of all 159 export deliverables.

---

## Hardware & Electronics

- **MR1 Main Controller Board** (`MR1/`):
  - 6-Layer stackup with dedicated ground and power planes.
  - ESP32-S3-WROOM-1 MCU with native high-speed USB CDC.
  - Dedicated SPI bus for high-speed ADC sampling.
  - Dual MCP4822 12-bit DACs providing bipolar pore bias voltages (-1.587V to +1.587V) and unblocking pulses.
  - Conductive weep-hole leak detection sensing on GPIO1.
- **PTFE Interposer Circuit Board** (`Interposer/` & `src/cartridge.py`):
  - 55.0 × 51.962 × 0.8 mm hexagonal substrate fabricated on ultra-low-loss PTFE / Rogers RO4350B.
  - Physical and electrical barrier dividing Cis (top) and Trans (bottom) microfluidic chambers.
  - Dual-sided silver chloride (Ag/AgCl) ribbon electrode pads positioned inside the Cis ($30^\circ$) and Trans ($210^\circ$) flow channels.
  - Central 6.20 × 6.20 mm diamond cutout ($45^\circ$) allowing the silicone gasket protrusion to seal directly around the silicon nanopore wafer.
  - 12-pin guarded ENIG landing array (`PogoPin_Target_12Pin_Distributed`) flanking high-impedance sense lines (`WS_CIS`, `RE_TRANS`) with driven low-impedance `GUARD` pins.
  - Hermetically clamped between `Cast_Nanopore_Wafer_Gasket` (top) and `Fitted_Amplifier_Gasket` (bottom).
- **Cartridge Transimpedance Amplifier** (`Amplifier/`):
  - 2-Layer 0.8 mm ultra-thin board designed for direct insertion into the flow cell stack.
  - LMP7721 ultra-low input bias current amplifier (sub-femtoampere leakage).
  - Low-leakage guard rings and driven shields guarding the high-impedance nanopore input node.
  - Direct connection to flow cell via gold-plated Mill-Max pogo pins.
- **Pump Controller & USB-PD Hub Board** (`Pump/` & `src/cartridge.py`):
  - 4-Layer 1.6 mm board (88.0 × 88.0 mm) fitting within the `Housing_Pump_Case` internal pocket.
  - **Dual USB-C Receptacles**:
    - `J1_HOST` at $X = -15.0\text{ mm}$ (top edge): USB-PD Sink + Host laptop data interface.
    - `J2_MR1` at $X = +15.0\text{ mm}$ (top edge): Regulated clean 5V power output to MR1 Reader + SBU I2C control link.
    - Perfectly aligned to the $12 \times 6\text{ mm}$ cutouts on `Housing_Pump_Case` rear wall ($Y = 55.0\text{ mm}$).
  - **High-Speed USB 2.0 Pass-Through**: TI TS3USB221 multiplexer (>1.1 GHz bandwidth, insertion loss < 0.5 dB) passes 100 kHz continuous ADC telemetry straight through to the laptop without MCU latency.
  - **STUSB4500 Autonomous USB-PD Sink**: Automatically negotiates 9V/12V/15V/20V profiles from USB-PD power sources.
  - **Clean +5V Output Subsystem**: Synchronous step-down buck converter (36V/3A) + TPS22916 soft-start load switch + LC $\pi$-filter ensuring ultra-low ripple 5V power for MR1's analog frontend.
  - **STM32G431CBU6 Control MCU**: ARM Cortex-M4 @ 170 MHz orchestrating precision TIM1 PWM peristaltic velocity control, I2C telemetry, and hardware emergency stop gating.
  - **Dual Honeywell TruStability / ABP2 Pressure Transducers**:
    - Transducer 1 (0-15 psi gauge): Real-time pressure monitoring on Cis chamber feed line.
    - Transducer 2 (0-5 psi gauge): Real-time pressure monitoring on Trans chamber recirculation line.
  - **Dual TI DRV8837C Motor Drivers**: 1.8A peak H-bridge drivers with hardware shutdown interlock directly connected to the weep moat leak detector.

---

## ESP32-S3 Firmware

Located in `MR1_firmware/` (ESP32-S3 Main Reader) and `Pump_firmware/` (STM32G431 Peristaltic Pump & USB-PD Hub):
- **Dual-Core Architecture**:
  - **Core 1**: Dedicated to continuous 100 kHz SPI DMA ADC sampling and high-throughput USB CDC streaming.
  - **Core 0**: Handles Wi-Fi AP/station management, AsyncWebServer, WebSocket oscilloscope telemetry, and pump control.
- **High-Throughput Binary Protocol**: Frames of 64 decimated/raw samples packed with sequence IDs, 64-bit microsecond timestamps, and CRC-16 checksums.
- **USB-C SBU Auto-Polarity Detection**: Dynamic GPIO-matrix sensing on SBU1/SBU2 pins automatically determines clock (SCL) and data (SDA) orientation for I2C communication to external pump modules, working seamlessly regardless of cable flip.
- **Embedded Web Oscilloscope**: Live HTML5 Canvas visualization accessible via browser over Wi-Fi without needing host drivers.

### Host 100 kHz Streaming DAQ Client (`scripts/daq_client.py`)

A high-performance Python client for acquiring continuous 100 kHz binary telemetry from the MR1 Reader:

```bash
# Live acquisition with terminal dashboard and CSV logging
python scripts/daq_client.py --port COM3 --bias 180.0 --output data.csv

# Run mock simulation mode (generates baseline ionic current & DNA translocation events)
python scripts/daq_client.py --mock --duration 5.0 --output simulation.csv

# Execute SBU I2C polarity auto-detection and start pump
python scripts/daq_client.py --port COM3 --sbu-detect --pump 60
```

- **Binary Frame Synchronization**: Synchronizes on `"SENT"` magic word (`0x53454E54` / little-endian `b"TNES"`).
- **CRC-16-CCITT Verification**: 100% integrity validation on every 146-byte packet.
- **Pore Current Conversion**: Converts differential 16-bit counts to Amperes ($I_{\text{pore}} = V_{\text{adc}} / R_f$, default $R_f = 1\text{ G}\Omega \implies 1\text{ V}/1\text{ nA}$).
- **Real-Time Telemetry Dashboard**: Live sample rate (kS/s), data throughput (KB/s), dropped frame count, RMS current noise, pump status, and leak monitoring.

---

## Fluidic Routing & Mold Casting

- **Standardized Tubing**: All microfluidic connections standardize on **1/8" ID $\times$ 1/4" OD** tubing and 1/8" hose barb panel-mount fittings.
- **Fluid Lines**:
  - `TUBE_PUMP`: PharMed BPT (0.12 m) — Buffer reservoir $\to$ Peristaltic pump.
  - `TUBE_FEED`: FEP (0.22 m) — Pump $\to$ Cis chamber inlet ($210^\circ$).
  - `TUBE_TRANS_LINE`: PEEK (0.18 m) — Trans chamber outlet ($150^\circ$) $\to$ Waste.
  - `TUBE_WASTE_LINES` ($\times 2$): Silicone (0.25 m) — Cis outlet ($30^\circ$) and Trans inlet ($330^\circ$).
- **Gasket Fabrication**: Two-part resin casting mold (`Nanopore_Wafer_Mold_Left` and `Right`) designed for casting degassed PDMS (Sylgard 184) or high-compliance silicone around the silicon nanopore wafer. See [CASTING.md](CASTING.md) for detailed surface preparation, degassing, and curing procedures.

---

## Documentation Index

### Open Source Governance & Policies
- [CONTRIBUTING.md](CONTRIBUTING.md): Engineering guidelines, code style, and pull request workflow.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): Contributor Covenant v2.1 standards and pledge.
- [SECURITY.md](SECURITY.md): Security vulnerability reporting policy and electrical safety bounds.
- [CITATION.cff](CITATION.cff): Academic citation metadata for research and publications.
- [LICENSE](LICENSE): GNU Affero General Public License v3.0 (AGPLv3).

### Hardware & Manufacturing Specifications
- [BOM.md](BOM.md): Complete mechanical, fluidic, PCB, and active electronic bill of materials with sourcing links.
- [EXPORTS.md](EXPORTS.md): Complete export deliverables catalog, fab ordering specifications, and drift tracking.
- [CASTING.md](CASTING.md): Engineering guide for casting ultra-low-noise PDMS gaskets.
- [PROJECT.md](PROJECT.md): Project architecture, interface contracts, and milestone tracking.
- [TODO.md](TODO.md): Development roadmap and completed porting phases.

### Firmware & Protocols
- [MR1 Reader Firmware](MR1_firmware/README.md): ESP32-S3 dual-core firmware architecture, SPI DMA ADC, and web oscilloscope.
- [Pump Hub Firmware](Pump_firmware/README.md): STM32G431 peristaltic motor control, STUSB4500 USB-PD, and pressure monitoring.
- [DAQ Streaming Protocol](docs/DAQ_STREAMING_SPEC.md): Binary stream framing, CRC-16 checksums, and 100 kHz sample encoding.
- [MR1 Data Exchange Spec](docs/MR1_DATA_EXCHANGE_SPEC.md): Inter-board SBU I2C and UART communications.
- [Interposer 4-Electrode Spec](docs/INTERPOSER_FOUR_ELECTRODE_SPEC.md): Gamry 4-electrode topology and driven guard architectures.
- [Weep Moat Interlock Spec](docs/ECO_WEEP_SENSE_BUFFER_INTERLOCK.md): Leak detection sensor and hardware power cutoff circuitry.

### Co-Design, Simulation & Tools
- [OpenAuto-CFD & 3D Visualizer Guide](docs/OPENAUTO_CFD.md): Multiphysics co-simulation, interactive 3D assembly visualizer (`ocp_vscode`), and KiCad action plugin documentation.
- [OpenAuto Project Manifest](openauto.project.json): Single-source-of-truth hardware manifest linking ECAD, MCAD, fluidics, and harnesses.
