# Contributing to MR1 Nanopore Reader (MR1)

Thank you for your interest in contributing to the **MR1 Nanopore Reader** project! We are building an open-source, reproducible, high-throughput solid-state and biological nanopore sequencer, low-noise analog transimpedance amplifier, and automated microfluidic control system.

We welcome contributions across mechanical engineering (CAD), analog and digital electronics (KiCad EDA), embedded firmware (ESP32-S3 / STM32), data acquisition software (Python / WebSockets), and documentation.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all community members with respect, kindness, and professional courtesy.

---

## Getting Started

### 1. Prerequisites

Before developing, ensure your local system has the required toolchains:

- **Python**: 3.10 or newer
- **KiCad**: Version 7.0 or newer (v8/v10 recommended for EDA layout and scripting exports)
- **PlatformIO Core (CLI)**: For compiling and uploading ESP32-S3 and STM32 firmware
- **Graphviz (`dot`)**: Required for rendering WireViz electrical and fluidic harness diagrams
- **Git**: For version control

### 2. Environment Setup

Clone your fork of the repository and initialize the Python virtual environment:

```bash
# Clone the repository
git clone https://github.com/<your-username>/mr1.git
cd mr1

# Run the environment bootstrap script
# On Linux / macOS / Git Bash:
chmod +x setup_env.sh install.sh
./setup_env.sh

# On Windows (PowerShell):
.\setup_env.ps1

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
```

Verify that all tools and dependencies are correctly installed:

```bash
./setup_env.sh --check
```

---

## Architecture & Domain Guidelines

The project spans five tightly coupled engineering domains. When contributing, please follow the conventions for each domain:

### 1. Parametric CAD Modeling (`src/`)
- All mechanical models are constructed procedurally in Python using **`build123d`**.
- **No hardcoded dimensions**: All dimensions, tolerances, wall thicknesses, and port angles must be parameterized in [`src/constants.py`](src/constants.py).
- **Zero-Collision Rule**: Every component must pass automated 3D BREP intersection testing. Mating parts must have clean zero-interference interfaces (except intentional seal compression).
- **Spline & Tubing Clearance**: Swept flexible lines (tubing and wiring) in [`src/assembly.py`](src/assembly.py) must adhere to minimum bend radii ($R \ge 10\text{ mm}$).
- **Fillets & Machinability**: Ensure outer and inner corners have appropriate radii for CNC milling (PP plates) or SLA resin casting (molds).

### 2. Electronics & Printed Circuit Boards (`MR1/`, `Amplifier/`, `Interposer/`, `Pump/`)
- Schematics and layouts are authored in **KiCad**.
- **Edge.Cuts Topology**: All PCB board outlines must form strictly continuous, closed 2-regular loops (0 endpoints with degree $\ne 2$, 0 floating lines).
- **Ultra-Low Leakage**: The LMP7721 transimpedance amplifier input node operates at femtoampere current levels ($10^{-15}\text{ A}$). High-impedance traces (`WS_CIS`, `>PORE_AMP`) must be surrounded by driven `GUARD` rings on all layers without solder mask apertures over guarded areas.
- **Paths**: Never save hardcoded absolute machine paths (`/home/...` or `C:\...`) in `.kicad_pcb` or `.kicad_pro` project settings.

### 3. Embedded Firmware (`MR1_firmware/`, `Pump_firmware/`)
- Built with **PlatformIO**.
- **Dual-Core Partitioning (ESP32-S3)**:
  - **Core 1**: Dedicated hard real-time loop executing continuous 100 kHz SPI DMA ADC sampling and native high-speed USB CDC binary streaming. No blocking heap allocations or Wi-Fi operations on Core 1.
  - **Core 0**: Asynchronous web server, WebSocket oscilloscope streaming, SBU I2C polarity detection, and pump UART telemetry.
- **Protocol Framing**: All high-speed streaming packets must adhere to the 146-byte `StreamFrame` specification defined in [`docs/DAQ_STREAMING_SPEC.md`](docs/DAQ_STREAMING_SPEC.md) with valid `"SENT"` magic word and CRC-16-CCITT checksums.

### 4. Data Ingestion & Host Client (`scripts/daq_client.py`)
- Python scripts must follow PEP 8 and include type annotations.
- The DAQ client must support both live hardware streaming over USB CDC-ACM and `--mock` simulation mode for offline integration testing.

---

## Automated Testing & Quality Gates

Every pull request must pass the automated test runner before merging:

```bash
# Run the complete test suite
python run_tests.py
```

### Specific Test Suites:
```bash
# 1. 3D BREP Geometric Collision & Clearance Checks
python -m unittest tests/test_geometry.py

# 2. Golden STL & Component Dimensional Bounds
python -m unittest tests/test_golden_stl_bounds.py

# 3. KiCad Netlist, Footprint, and Edge.Cuts Continuity
python -m unittest tests/test_interposer_kicad.py

# 4. Legacy OpenSCAD Feature Parity Assertions
python -m unittest tests/test_legacy_feature_parity.py

# 5. Firmware Protocol, CRC-16, and DAC Scaling
python -m unittest tests/test_firmware_protocol.py

# 6. Deliverables & Staged Exports Validation
python -m unittest tests/test_exports_e2e.py
```

---

## Development & Export Workflow

To regenerate all manufacturing deliverables, CAD solids, and wiring diagrams:

```bash
# Regenerate all exports and update the SHA-256 manifest
make export

# Or run individual export domains:
make export-cad        # Generate STEP, STL, and DXF files
make export-kicad      # Export Gerbers, Drill, POS, and PDF schematics
make export-wiring     # Render WireViz wiring and tubing diagrams
make export-firmware   # Compile and stage firmware binaries
```

---

## Submitting Pull Requests

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-enhancement
   ```
2. **Commit Changes**: Use clear, conventional commit messages:
   - `feat:` A new hardware feature, model, or firmware capability
   - `fix:` A bug fix or geometric alignment correction
   - `docs:` Documentation improvements or additions
   - `refactor:` Code refactoring with no functional change
   - `test:` Adding or updating test suites
3. **Sign Your Work (DCO)**: We require the Developer Certificate of Origin (DCO). Sign your commits using `git commit -s`.
4. **Push and Open PR**:
   ```bash
   git push origin feature/my-enhancement
   ```
   Open a pull request against the `main` branch. Provide a clear description of the mechanical, electrical, or software changes made, and include photos, renders, or test outputs where applicable.

---

## Questions & Community

- **Issue Tracker**: [GitHub Issues](https://github.com/LokiMetaSmith/mr1/issues)
- **Discussions**: [GitHub Discussions](https://github.com/LokiMetaSmith/mr1/discussions)
- **Security Vulnerabilities**: Please review our [Security Policy](SECURITY.md) for reporting vulnerabilities.
