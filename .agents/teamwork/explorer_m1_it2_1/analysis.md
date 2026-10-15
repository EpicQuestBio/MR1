# Geometric & CAD Analysis Report: Housing_Lid_Reader Ribbon Cable Cavity Cutout

**Investigator**: Explorer 1 (`explorer_m1_it2_1`)  
**Parent Agent**: `854953a8-2b33-4cc9-9231-ad06cd4c5aac`  
**Milestone**: Milestone 1 Iteration 2 (Ribbon Cable Cavity Alignment & CAD Verification)  
**Date**: 2026-10-15  
**Target File**: `src/housing.py` (`Housing_Lid_Reader`)  
**Reference File**: `openscad-legacy/modules/housing_reader.scad` (line 65)  

---

## Executive Summary

Challenger 2 identified a critical CAD defect in `Housing_Lid_Reader` (`src/housing.py`): the $13.5\text{ mm} \times 3.0\text{ mm}$ cavity cutout at $Y = -27.5\text{ mm}$ only reached $Z = +22.6\text{ mm}$, leaving a solid plastic blockage of $265.3467\text{ mm}^3$ blocking the upper neck cylinder between $Z = 22.6\text{ mm}$ and $Z = 30.2\text{ mm}$ ($7.6\text{ mm}$ tall).

This investigation performed full 3D CAD modeling, bounding box verification, mating part collision checking, and test suite validation. We determined that updating lines 263–264 of `src/housing.py` to:
```python
with Locations((0.0, -27.5, 0.0)):
    Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)
```
cleanly clears the cavity across the entire vertical span ($Z \in [-27.5, +30.2]\text{ mm}$), matches OpenSCAD legacy reference truth (`tag("remove") translate([0, -27.5, 0]) cube([13.5, 3.0, 200], center=true)`), preserves all Golden STL bounds ($100.0 \times 100.0 \times 57.7\text{ mm}$), introduces zero mating part collisions, and eliminates the $265.35\text{ mm}^3$ blockage.

---

## 1. Exact Geometry Analysis in `src/housing.py`

### 1.1 Structural Layout of `Housing_Lid_Reader`
In `src/housing.py`, `Housing_Lid_Reader()` constructs the upper reader housing via build123d with the following vertical coordinates:
- **Base Plate**: $100.0 \times 100.0 \times 25.0\text{ mm}$, centered at $Z = -\text{lid\_thick}/2.0 = -12.5\text{ mm}$. Extends from $Z = -25.0\text{ mm}$ to $Z = 0.0\text{ mm}$ (top surface at $Z = 0.0\text{ mm}$).
- **Indexing Lip**: $Z \in [-27.5, -25.0]\text{ mm}$ ($2.5\text{ mm}$ height) extending down from the base.
- **Internal Bucket**: Subtracted from bottom, leaving `ceiling_thick = 10.0mm` solid plastic between $Z = -10.0\text{ mm}$ and $Z = 0.0\text{ mm}$.
- **Neck Transition Cone**: $Z \in [0.0, 5.0]\text{ mm}$ ($5.0\text{ mm}$ height, bottom radius $40.0\text{ mm}$, top radius $37.5\text{ mm}$).
- **Neck Cylinder**: Center at $Z = 5.0 + \text{neck\_length}/2.0 = 5.0 + 12.6 = 17.6\text{ mm}$, height $\text{neck\_length} = 25.2\text{ mm}$, radius $\text{neck\_r} = 37.5\text{ mm}$. Extends from $Z = 5.0\text{ mm}$ to $Z = +30.2\text{ mm}$.
- **External M75 Thread**: Extends from $Z = 5.0\text{ mm}$ to $Z = +30.2\text{ mm}$.
- **Inner Hex Socket Bore**: Regular polygon (radius $R = 30.5\text{ mm}$, apothem $r_{\text{in}} = 26.4138\text{ mm}$), extruded starting from $Z = 0.0\text{ mm}$ up by $5.0 + 25.2 + 20.0 = 50.2\text{ mm}$, reaching $Z = +50.2\text{ mm}$.
- **Vertical Fluid Pass-Through Holes**: 4 holes of $D = 10.0\text{ mm}$ at radius $\text{PORT\_RADIUS} = 20.0\text{ mm}$, centered at $Z = -5.0\text{ mm}$, height $55.2\text{ mm}$. Since $20.0 + 5.0 = 25.0\text{ mm} < 26.4138\text{ mm}$, above $Z = 0.0\text{ mm}$ these holes reside entirely within the already-empty hex bore.

### 1.2 Mathematical Derivation of the Defect
On lines 263–264 of `src/housing.py`:
```python
# Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
with Locations((0.0, -27.5, -ceiling_thick / 2.0)):
    Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)
```
- **Cavity footprint**: $X \in [-6.75, +6.75]\text{ mm}$ (width $13.5\text{ mm}$), $Y \in [-29.0, -26.0]\text{ mm}$ (depth $3.0\text{ mm}$, centered at $Y = -27.5\text{ mm}$).
- **Radial relationship**: The inner hex socket flat at $Y \approx -26.4138\text{ mm}$ transitions to the solid neck wall extending out to $Y \approx -37.5\text{ mm}$. The cavity is recessed into this wall by $Y \in [-29.0, -26.0]\text{ mm}$.
- **Subtractive Box center**: $Z_{\text{center}} = -\text{ceiling\_thick} / 2.0 = -5.0\text{ mm}$.
- **Subtractive Box height**: $H = \text{neck\_length} + \text{ceiling\_thick} \times 3.0 = 25.2 + 30.0 = 55.2\text{ mm}$.
- **Subtractive Box vertical extent**:
  $$Z_{\min} = -5.0 - 55.2 / 2.0 = -32.6\text{ mm}$$
  $$Z_{\max} = -5.0 + 55.2 / 2.0 = +22.6\text{ mm}$$
- **Neck cylinder vertical extent**:
  $$Z_{\text{top}} = 5.0 + \text{neck\_length} = 5.0 + 25.2 = +30.2\text{ mm}$$
- **The Gap**:
  $$\Delta Z = Z_{\text{top}} - Z_{\max} = 30.2 - 22.6 = 7.6\text{ mm}$$
For the vertical interval $Z \in [22.6, 30.2]\text{ mm}$, no subtraction took place! Because $Y \in [-29.0, -26.0]\text{ mm}$ is outside the hex socket apothem ($26.41\text{ mm}$), the solid cylindrical neck wall was left untouched.

Empirical volumetric overlap with a probe of $13.5 \times 3.0 \times 7.6\text{ mm}$ placed in $Z \in [22.6, 30.2]\text{ mm}$:
$$\text{Blocked Volume} = \mathbf{265.3467\text{ mm}^3}$$

---

## 2. Legacy Reference Analysis (`openscad-legacy`)

In `openscad-legacy/modules/housing_reader.scad` (line 65):
```scad
// Clearance channel for ribbon cable recessed into hexagon wall
tag("remove") translate([0, -27.5, 0]) cube([13.5, 3.0, 200], center=true);
```
In OpenSCAD:
1. `translate([0, -27.5, 0]) cube([13.5, 3.0, 200], center=true);` places a cube centered at $(0.0, -27.5, 0.0)$ with height $200.0\text{ mm}$.
2. Its $Z$ extents are $[-100.0, +100.0]\text{ mm}$.
3. This cuts completely through the entire vertical span of the housing lid (which only extends from $Z = -27.5\text{ mm}$ to $Z = +30.2\text{ mm}$).
4. The legacy reference was a "through-all" vertical cutout that left zero solid plastic blocking the neck.

---

## 3. Subtractive Box Modification Determination

In build123d, `Box(length, width, height)` is centered at the local coordinate system origin of the active `Locations` context.

Modifying lines 263–264 to:
```python
# Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
with Locations((0.0, -27.5, 0.0)):
    Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)
```
- **Center**: $(0.0, -27.5, 0.0)$
- **Vertical span**: $Z \in [-50.0, +50.0]\text{ mm}$
- **Coverage**:
  - Part bottom: $Z = -27.5\text{ mm}$ (clearance below: $22.5\text{ mm}$)
  - Part top: $Z = +30.2\text{ mm}$ (clearance above: $19.8\text{ mm}$)
- **Comparison with $H = 200.0\text{ mm}$**:
  Testing both $H = 100.0\text{ mm}$ and $H = 200.0\text{ mm}$ in OpenCASCADE yields an identical solid to $0.000000\text{ mm}^3$ difference (`diff: 0.000000e+00`), since both encompass the full part height ($57.7\text{ mm}$). $H = 100.0\text{ mm}$ is preferred as it conforms to the standard $100\text{ mm}$ through-all conventions in the repository (e.g. vertical fluid ports).

---

## 4. Golden STL Bounds & Mating Part Verification

We conducted rigorous empirical 3D Boolean verification comparing the original `Housing_Lid_Reader` vs the modified `Housing_Lid_Reader`:

### 4.1 Golden STL Bounding Box & Volume
| Metric | Original Lid | Modified Lid | Spec / Tolerance | Result |
|---|---|---|---|---|
| **Bounding Box Min** | `(-50.0, -50.0, -27.5)` | `(-50.0, -50.0, -27.5)` | N/A | **PASS** (identical) |
| **Bounding Box Max** | `(50.0, 50.0, 30.2)` | `(50.0, 50.0, 30.2)` | N/A | **PASS** (identical) |
| **Size X** | $100.000\text{ mm}$ | $100.000\text{ mm}$ | $100.0 \pm 0.5\text{ mm}$ | **PASS** ($\Delta = 0.0$) |
| **Size Y** | $100.000\text{ mm}$ | $100.000\text{ mm}$ | $100.0 \pm 0.5\text{ mm}$ | **PASS** ($\Delta = 0.0$) |
| **Size Z** | $57.700\text{ mm}$ | $57.700\text{ mm}$ | $57.7 \pm 0.5\text{ mm}$ | **PASS** ($\Delta = 0.0$) |
| **Solid Volume** | $320,398.2981\text{ mm}^3$ | $320,132.8454\text{ mm}^3$ | $> 100,000.0\text{ mm}^3$ | **PASS** |
| **Volume Difference** | — | $-265.4527\text{ mm}^3$ | Removed solid obstruction | **PASS** |

### 4.2 Neck Obstruction Probe
- Probe geometry: $13.5\text{ mm} \times 3.0\text{ mm} \times 7.6\text{ mm}$ placed at $X = 0.0, Y = -27.5, Z \in [22.6, 30.2]\text{ mm}$.
- Original Lid: `[!] COLLISION DETECTED: Overlap Volume: 265.3467 mm^3`
- Modified Lid: `Overlap Volume: 0.0000 mm^3 (has_overlap=False)`

### 4.3 Full Vertical Height Cavity Probe
- Probe geometry: $13.5\text{ mm} \times 3.0\text{ mm} \times 55.2\text{ mm}$ spanning $Z \in [-25.0, 30.2]\text{ mm}$.
- Original Lid: `Blocked volume: 265.3467 mm^3`
- Modified Lid: `Blocked volume: 0.0000 mm^3`

### 4.4 Mating Part Collision Checks
All mating interfaces were evaluated using `src/collision_check.py` Boolean algorithms:
1. **Lower Cartridge Stack Seating**:
   - `Bottom_Pusher_Plate` (at $Z = 0.0$): **$0.0000\text{ mm}^3$ overlap**
   - `Plate_1_Base_Hex` (at $Z = 3.0$): **$0.0000\text{ mm}^3$ overlap**
   - `Fitted_Amplifier_Gasket` (at $Z = 4.0$): **$0.0000\text{ mm}^3$ overlap**
   - `PCB_Rigid_Active` (at $Z = 5.6$): **$0.0000\text{ mm}^3$ overlap**
   - `Cast_Nanopore_Wafer_Gasket` (at $Z = 6.4$): **$0.0000\text{ mm}^3$ overlap**
   - `Plate_3_Top_Hex` (at $Z = 8.0$): **$0.0000\text{ mm}^3$ overlap**
2. **Housing & Cap Interfaces**:
   - `Torque_Cap_Inner`: concentric engagement volume remains exactly $3634.1895\text{ mm}^3$ (identical to pre-fix, well within the $4000.0\text{ mm}^3$ nominal thread threshold). Outer threads are unaffected by the cavity cutout at $Y = -27.5\text{ mm}$.
   - `Torque_Cap_Outer`: unaffected ($0.0000\text{ mm}^3$ direct contact).
   - `Housing_Case_Reader`: indexing lip engagement volume is identical to pre-fix ($10374.4554\text{ mm}^3$).
3. **Flexible Routing**:
   - `Flexible_Tubing`: **$0.0000\text{ mm}^3$ overlap**
   - `Wiring_Harness`: **$0.0000\text{ mm}^3$ overlap**

### 4.5 Repository Test Suite Execution
Running the 27 tests across `test_geometry.py`, `test_golden_stl_bounds.py`, and `test_legacy_feature_parity.py` against the modified `Housing_Lid_Reader` passes completely:
```
Ran 27 tests in 27.585s
OK (Failures: 0, Errors: 0)
```

---

## 5. Test Suite Parity Enhancement

In `tests/test_legacy_feature_parity.py` lines 167–172:
The legacy probe was:
```python
cable_probe = Solid.make_box(8.0, 2.0, 20.0).move(Location((-4.0, -28.5, -10.0)))
```
This probe spanned only $Z \in [-10.0, +10.0]\text{ mm}$, leaving the upper neck untested.
By updating this probe to span $Z \in [-10.0, +30.2]\text{ mm}$ (height $40.2\text{ mm}$), the test verifies both the ceiling pass-through and the upper neck:
- Pre-fix: fails with $118.4000\text{ mm}^3$ overlap.
- Post-fix: passes with $0.0000\text{ mm}^3$ overlap.

---

## 6. Recommended Code Changes for Worker

### Target 1: `src/housing.py`
Replace lines 262–265:

```python
<<<<
        # Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
        with Locations((0.0, -27.5, -ceiling_thick / 2.0)):
            Box(13.5, 3.0, neck_length + ceiling_thick * 3.0, mode=Mode.SUBTRACT)
====
        # Ribbon Cable Clearance Channel (13.5mm x 3.0mm cavity recessed into hexagon wall at Y = -27.5)
        with Locations((0.0, -27.5, 0.0)):
            Box(13.5, 3.0, 100.0, mode=Mode.SUBTRACT)
>>>>
```

### Target 2: `tests/test_legacy_feature_parity.py`
Replace lines 167–173:

```python
<<<<
        # 2. Test ribbon cable clearance cavity at (0, -27.5, 0)
        cable_probe = Solid.make_box(8.0, 2.0, 20.0).move(Location((-4.0, -28.5, -10.0)))
        inter_cable = lid.intersect(cable_probe)
        vol_cable = inter_cable.volume if inter_cable is not None else 0.0
        self.assertLess(vol_cable, 0.5,
                        "Housing_Lid_Reader is missing ribbon cable cavity at (0, -27.5).")
====
        # 2. Test ribbon cable clearance cavity at (0, -27.5, 0) across full neck height (Z in [-10.0, 30.2] mm)
        cable_probe = Solid.make_box(8.0, 2.0, 40.2).move(Location((-4.0, -28.5, -10.0)))
        inter_cable = lid.intersect(cable_probe)
        vol_cable = sum(s.volume for s in inter_cable) if isinstance(inter_cable, (list, tuple, ShapeList)) or hasattr(inter_cable, "__iter__") else (inter_cable.volume if inter_cable is not None else 0.0)
        self.assertLess(vol_cable, 0.5,
                        f"Housing_Lid_Reader has solid obstruction in ribbon cable cavity (blocked volume: {vol_cable:.4f} mm^3).")
>>>>
```
