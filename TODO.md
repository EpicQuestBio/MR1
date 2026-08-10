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
- [ ] Add collision checks for flexible routes in `collision_check.py`:
    - Ensure tubing doesn't clip through the baseplates, housing walls, or PCB standoffs.
    - Validate that bend radii do not exceed the minimum thresholds.

## 8. Routing Implementation
- [x] Connect the Luer bulkhead models to the `Housing_Pump_Case` and `Housing_Case_Reader` side cutouts.
- [x] Implement `build123d` splines for wire routing from USB-C ports to internal PCB and Motor.
- [x] Implement splines for fluid tubing (1/8" ID x 1/4" OD) connecting adapters to Luer bulkheads.
