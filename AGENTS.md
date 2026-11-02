# AGENTS.md — Navigating the MR1 Nanopore Reader repo

Guide for AI agents. Distilled from `.jules/memory.md` (archived agent learnings), `README.md`, `CONTRIBUTING.md`, `Makefile`, and the tree. When this file disagrees with the code, trust the code and update this file.

## 1. What this repo is

**MR1 Nanopore Reader** is an open-source, low-noise nanopore sequencer flow cell. It has four parts:
- Parametric CAD (`build123d`, with a legacy OpenSCAD port).
- KiCad electronics (low-current TIA headstage, interposer, main controller, pump board).
- Firmware: ESP32-S3 for the reader, STM32 for the pump.
- Python DAQ, simulation and verification tooling.

The canonical project name is **MR1**. Legacy names ("Sentinel", "Daemon Pore", "daemon-pore") were replaced everywhere in content. The checkout directory is still named `daemon-pore` only because it hasn't been renamed yet. Treat it as `MR1`, and don't use the old name in new content.
- Use `MR1` in UPPER_CASE and PascalCase contexts.
- Use `mr1` in snake_case, kebab-case, camelCase and filenames.

License is CC0-1.0. Source files (`.py`, `.scad`, `.cpp`, `.h`, `.sh`) carry this header:
```
Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
SPDX-License-Identifier: CC0-1.0
```
Some files name a different author, such as Jade O'Neill. Keep the header on new files.

## 2. Directory map

| Path | Contents |
|---|---|
| `src/` | build123d CAD, the primary model. `main.py` (export/`--viewer`), `assembly.py` (`get_tubing_routes()`), `housing.py`, `cartridge.py`, `torque_cap.py`, `connectors.py`, `adapters.py`, `nanopore_wafer_mold.py`, `collision_check.py`, `constants.py`, `common.py` |
| `openscad-legacy/` | Legacy OpenSCAD: `mr1_nanopore_reader.scad`, `constants.scad`, `modules/*.scad`. Submodule `libraries/BOSL2`. Frozen and disconnected (reference only) |
| `Amplifier/` | KiCad cartridge amplifier board (LMP7721 / OPA192 TIA, ADC U13). Holds `footprints.pretty/`, `footprints/`, `symbols/` |
| `Interposer/` | KiCad PTFE interposer (electrodes, guards, fluid holes H1–H4) |
| `MR1/` | KiCad main reader controller board. Also contains an `amplifier.*` copy |
| `Pump/` | KiCad pump/USB-PD board (STM32, motor drivers, pressure sensors) |
| `MR1_firmware/` | PlatformIO ESP32-S3 firmware: `src/{comm,hal,web,main.cpp}`, `include/{config,pinout,protocol}.h` |
| `Pump_firmware/` | PlatformIO STM32 pump firmware |
| `scripts/` | Tooling: `export_manager.py`, `export_all.{js,sh}`, `daq_client.py`, `websocket_bridge.py`, `generate_footprint.py`, `build_interposer_kicad.py`, `build_interposer_symbols.py`, `generate_pump_pcb.py`, `render_flythrough.py`, `render_openscad_animation.py`, `run_python.sh`, `run_e2e_tests.sh`, `lib_setup.js`, `install_libraries.js` |
| `simulations/` | Physics scripts: electrokinetics, fluidics, 4-electrode cell, guard-ring electrostatics, op-amp conditioning, FEA (flexure, G-code), topology optimization |
| `tests/` | unittest/pytest suite, golden manifest (`golden_manifest.json`), helper `.scad` files |
| `docs/` | Specs: DAQ streaming, data exchange, interposer 4-electrode, op-amp conditioning, dual-route amplifier BOM, weep-sense ECO, casting, micropore NaCl configs, OpenAuto CFD |
| `plugins/` | `openauto_cfd_plugin.py` |
| `wiring/` | WireViz YAML: `reader_wiring.yaml`, `reader_tubing.yaml` |
| `exports/`, `renders/`, `build/` | Generated artifacts. Don't hand-edit. `build/*.net` is generated |
| `datasheets/` | Reference PDFs |
| Root docs | `README.md` (long, authoritative overview), `PROJECT.md`, `TODO.md`, `BOM.md`, `EXPORTS.md`, `CASTING.md`, `CONTRIBUTING.md`, `SECURITY.md`, `atlas.project.json`, `openauto.project.json` |
| `.jules/memory.md` | Archived agent notes (bullets, grouped by date). Read it, and append to it when you learn something durable |
| Ignore | `.venv/`, `node_modules/`, `.hypothesis/`, `__pycache__/` |

## 3. Setup and commands

```bash
bash ./setup_env.sh          # use `bash`, not ./setup_env.sh (permission errors); Windows: setup_env.ps1
source .venv/bin/activate
./scripts/run_python.sh scripts/<x>.py   # venv wrapper: finds the repo root, sets PYTHONPATH, runs setup_env.sh if .venv is missing
```
```bash
make test                    # python run_tests.py
python run_tests.py          # full suite, including the formal proofs
PYTHONPATH=. .venv/bin/python -m unittest discover tests   # alternative
make test-e2e                # tests/test_exports_e2e.py
make export | export-cad | export-kicad | export-wiring | export-firmware
make check                   # verify the indexed deliverables exist
make manifest                # exports/manifest.json (SHA-256)
make release-gerbers VERSION=v1.0.0
python src/main.py [--viewer|--show]   # CAD export / stream to ocp_viewer (port 3939)
./install.sh [--viewer]
cd MR1_firmware && pio run   # same for Pump_firmware; upload with `--target upload`
```
- `install.sh` and `scripts/export_manager.py` look for PlatformIO in `.venv` first, then on `PATH`.
- Optional simulation extras (`torch`, `dl4to`) live under `[project.optional-dependencies] simulation` in `pyproject.toml`.
- Python is 3.10+. The project targets KiCad 10 (7+ is the minimum the scripts tolerate). `kicad-cli` is needed for BOM/Gerber exports. Graphviz is needed for WireViz.

## 4. Testing notes

- `run_tests.py` loads each test module by file path, to avoid colliding with site-packages `tests`. A new test file must be **added there** to run under `make test`.
- `tests/test_formal_proofs.py` uses `z3-solver` and `hypothesis`. It proves invariants for protocol framing, the state machine, ESTOP, analog and geometry.
- Known and expected, not regressions:
  - `scripts/export_all.js` fails to produce the 2D DXFs (`Plate_1_Base_DXF`, `Gasket_Main_DXF`) because of a "Mixing 2D and 3D objects" warning near line 21 of `mr1_nanopore_reader.scad`.
  - `test_interposer_bom_completeness` and `test_interposer_gerber_exports` are intentionally skipped. They are tracked in `TODO.md` until CI can run `kicad-cli`.
- In build123d tests, `a.intersect(b)` may return a `ShapeList`. Sum the volumes defensively: `sum(s.volume for s in inter) if inter is not None else 0.0`.
- Golden STL bounds (`tests/golden_manifest.json`) and CAD feature tests validate build123d geometry against the golden specifications. Legacy OpenSCAD is frozen and disconnected.

## 5. Conventions and gotchas

### CAD (build123d)
- Use `insert()`, not the deprecated `add()`.
- Inside `with Locations(...)`, don't call `insert()` or `add()` on shapes built in that same context, because the location gets applied twice. Build shapes at the origin first, then place them.
- `Housing_Lid_Reader` has an external thread with 74.5 mm major diameter, 4.75 mm depth and 8.0 mm pitch. The mating `Torque_Cap_Inner` has a 75.5 mm bore. The lid is 35 mm thick and has side fluid ports at Z=-13 and 13 mm vertical pass-throughs. It also has `Weep_Duct_Holes`.
- `Housing_Pump_Lid` is a solid top (no center hole) with a bottom indexing lip that overlaps the lid body, so it forms one solid.
- `Housing_Case_Reader` has USB-C on the back wall at `X=USB_OFFSET_X (-15)`. Its PCB sits on 5 mm standoffs. Its four feet dimples are at (±42.5, ±42.5) and mate with dimples on the pump lid.
- `Torque_Cap_Outer` has 6 PETG flexure arms: 1.8 mm hinge, 2.5 mm root fillet, 1.5 mm pawl radius. The slip torque is about 0.5 N·m (about 33 N clamp). That is enough to compress the 12 pogo pins (about 9.6 N) and seat the gasket.
- `Rigid_Backing_Anvil` is 6 mm Delrin or 6061 aluminum. It backs the PTFE interposer against pogo point loads and prevents creep.
- `get_tubing_routes()` in `src/assembly.py` defines 5 splines: `TUBE_PUMP`, `TUBE_FEED`, `TUBE_TRANS_LINE`, `TUBE_WASTE_1`, `TUBE_WASTE_2`. They pass through Luer bulkheads and the hollow housing without intersecting solids.
- Legacy OpenSCAD: with `Use_Nanopore_Wafer_Gasket=true`, `Gasket_Mold_Top_STL` and `Gasket_Mold_Bottom_STL` output the `Nanopore_Wafer_Mold_Right` and `_Left` halves.

### KiCad
- File and project names are capitalized, e.g. `Amplifier.kicad_pcb`, `MR1.kicad_pcb`. Use those in scripts. Note that `MR1/amplifier.*` is lowercase, so check before assuming.
- `.history/`, `*.bak`, `*.net`, `*.kicad_prl` and backups are gitignored. Never track `.history` as a submodule.
- KiCad 8 `.kicad_mod`: `zone_connect` tokens inside pad definitions are invalid.
- `scripts/generate_footprint.py` regenerates the pogo-pin and fluid-overlay footprints. It supports `--pin-coords` and `--read-pcb`. Output must stay in sync across `Amplifier/footprints.pretty/`, `Amplifier/footprints/` and `Interposer/footprints.pretty/`. The default output is `Interposer/footprints.pretty/PogoPin_Target_6Pin_Distributed.kicad_mod`.
- The Amplifier board is **single-sided**. All parts and 12 discrete Mill-Max SMT pogo pins (`P1`–`P12`, 1-pin footprints `PogoPin_MillMax_SMT_1Pin[_Guarded]`) are on `F.Cu`. Multi-pin header banks are deprecated. The interposer mating pad `J_PAD1` is `PogoPin_Target_Landing_1Pin_Guarded`: pin 1 `>PORE_AMP`, pin 2 `GUARD`.
- The Amplifier stackup is 2-layer, 1.5 mm Rogers PTFE (RO3003 / ZYF255DA). It has mask exclusions over the LMP7721 guard region, a `GNDA` keepout on B.Cu, and a `GUARD` island on B.Cu.
- The pogo pin is LCSC C5221285 (YTC1P-6030-01): 9.0 mm free length, 7.5 mm working height, 2.0 mm base.
- On the interposer, Cis flow runs H1→H2 and Trans flow runs H3→H4.

### Electrical and firmware
- The 4-electrode net names are fixed: `WS_CIS` (working sense), `WE_POS` (working electrode, `>PORE_AMP`), `RE_TRANS` (reference), `CE_GNDA` (counter) and `GUARD`. Variants are `WS_CIS_WIDE`, `GUARD_WIDE`, `GUARD_CIS_A` and `GUARD_CIS_B`. Do not rename them.
- The ADC **U13 (AD40xx)** is on the Cartridge Amplifier board. The dual DAC **U9 (MCP4822)** is on the MR1 main controller board.
- Dual-route readout is selected by `PIN_ROUTE_SEL` (GPIO2), which drives the U17 SPDT switch:
  - Route 1 is 10 GΩ, LMP7721, `ROUTE_SEL` LOW.
  - Route 2 is 100 kΩ, OPA2192/LTC6268, `ROUTE_SEL` HIGH. It is the 200 nm wide-pore path on `WS_CIS_WIDE`, about 106 kHz bandwidth.
  - Protocol pieces are `STATUS_ROUTE2_ACTIVE = (1<<7)`, `SET:ROUTE:<1|2>`, `GET:ROUTE` and `/api/route`.
  - `daq_client.py` auto-adjusts transimpedance gain from the stream telemetry.
- The default 1 GΩ TIA gives about ±2.048 nA range. Larger pores need a lower bias or a smaller Rf (100 M, 10 M or 1 MΩ).
- Firmware protocol constants live in `MR1_firmware/include/protocol.h` and `pinout.h`. `tests/test_firmware_protocol.py` and `test_pump_firmware.py` check them against the Python side. Change both together.
- `scripts/websocket_bridge.py` batches 16 USB frames per message by default (`--batch-frames`). Each message is 4104 bytes: a `<Q` µs timestamp followed by 1024 float32 samples in pA, at about 97.66 Hz. It has a mock mode.
- The streaming spec is in `docs/DAQ_STREAMING_SPEC.md`. Check it before touching framing.

### Rendering
- `render_flythrough.py` uses PyVista (1080p, SSAA, background #0E1114→#1B2026, key/fill/rim/overhead lights). It supports `--test` and `--frames`.
- In `imageio.mimsave`, set `macro_block_size=1` for 1080p VP9 WebM output.

## 6. Workflow tips

1. Read `.jules/memory.md`, plus the relevant file in `docs/`, before changing a subsystem.
2. After changes, run `python run_tests.py`. For CAD changes also check the collision tests. For KiCad script changes run `tests/test_interposer_kicad.py` and `test_kicad_library_validation.py`.
3. Don't commit generated output (`exports/`, `renders/`, `build/`, `.venv`, `node_modules`).
4. Keep CAD, legacy SCAD, firmware, tests and docs consistent. The README has a test-count badge that may go stale.
5. Record durable discoveries as one-line bullets in `.jules/memory.md`. Don't duplicate existing ones.
6. One memory note refers to a Jules sandbox venv at `/app/.venv`. Locally, use `.venv/`.
