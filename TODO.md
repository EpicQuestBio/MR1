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
