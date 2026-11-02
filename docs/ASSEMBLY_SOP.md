# Standard Operating Procedure (SOP): MR1 Inverted Flowcell Stack Assembly

**Document ID:** SOP-MR1-001  
**Version:** 2.0.0  
**Author:** Molecular Reality Corp / MR1 Project Team  
**Scope:** Assembly, inspection, torque clamping, and priming of the inverted low-noise nanopore flowcell cartridge.

---

## 1. Overview & Mechanical Layup

The MR1 Nanopore Reader flowcell utilizes an **inverted cartridge architecture**:
- **Amplifier Isolation:** The low-noise Cartridge Amplifier board is mounted upside down at the top of the stack, placing active electronics (LMP7721, ADA4940, AD40xx ADC) above the fluidics to eliminate fluid immersion risk.
- **Wicking Prevention:** A hydrophobic $0.030"$ ($0.762\text{ mm}$) solid Polypropylene (PP) shim paired with an adjustable 3D-printed spacer ($\ge 3.0\text{ mm}$) provides physical clearance for SMD components and creates a capillary depression barrier (water contact angle $\theta \approx 100^\circ$) preventing saline from wicking up the pogo pins.
- **Vertical Connection:** 12 discrete coax pogo pins (LCSC C5221285 / YTC1P-6030-01) on `F.Cu` span the $7.5\text{ mm}$ air gap to mate with gold target pads on the PTFE interposer.
- **Crossed Microfluidic Channels ("X" Topology):**
  - **Cis Channel (Top Gasket):** $H_1$ ($210^\circ$) $\to$ Nanopore Chamber $\to$ $H_2$ ($30^\circ$).
  - **Trans Channel (Bottom Gasket):** $H_3$ ($330^\circ$) $\to$ Nanopore Chamber $\to$ $H_4$ ($150^\circ$).

```
[TOP / DRY SIDE]
  1. Torque Cap Outer & Inner (M75x8 mm thread, 6-arm flexure ratchet)
  2. Pressure Puck (3D printed PETG / Polycarbonate)
  3. Rigid Backing Anvil (6.0 mm Delrin POM-H / 6061-T6 Aluminum)
  4. Cartridge Amplifier PCB (Inverted, F.Cu component side facing DOWN)
  5. 12x Coaxial Pogo Pins (7.5 mm working compressed length, 0.8 N/pin)
  6. 3D-Printed Adjustable Spacer (PETG, height >= 3.0 mm, component relief)
  7. Polypropylene (PP) Anti-Wicking Shim (0.030" / 0.762 mm solid PP)
  8. Top Cis Gasket (Cast PDMS 1.5875 mm + 4x4x0.5 mm Nanopore Chip)
  9. PTFE Interposer Board (0.8 mm Rogers RO3003/PTFE, Ag/AgCl ribbons)
 10. Bottom Trans Gasket (Cast PDMS 1.5875 mm, Trans X-channel)
 11. Plate 1 Base Hex (PP base with 4x flush screw-in fluidic fittings)
 12. Bottom Pusher Plate (TPU compliance gasket)
[BOTTOM / FLUIDIC INLET SIDE]
```

---

## 2. Required Equipment, Tools & Materials

### 2.1 Hardware Components
- 1× Housing Lid Reader with M75×8 external threads.
- 1× Torque Cap (Inner and Outer ratchet assembly).
- 1× Pressure Puck.
- 1× 6.0 mm Delrin Backing Anvil.
- 1× Assembled Cartridge Amplifier PCB with 12× soldered SMT pogo pins (`P1`–`P12`, LCSC C5221285).
- 1× 3D-Printed Spacer ($\ge 3.0\text{ mm}$, printed at 0.1–0.2 mm layer height).
- 1× Precision CNC/die-cut $0.030"$ solid PP Shim.
- 1× Top Cis PDMS Gasket with embedded $4\times 4\times 0.5\text{ mm}$ SiNx nanopore wafer.
- 1× PTFE Interposer PCB (Rogers RO3003 / PTFE, ENIG pads, sintered Ag/AgCl strips).
- 1× Bottom Trans PDMS Gasket.
- 1× Plate 1 Base Hex with 4× flush 1/8" NPT to 1/8" barb fittings.
- 1× Bottom TPU Pusher Plate.

### 2.2 Reagents & Consumables
- HPLC-grade Isopropanol (IPA).
- $18.2\text{ M}\Omega\cdot\text{cm}$ Milli-Q deionized water.
- 1.0 M KCl sensing electrolyte buffer ($10\text{ mM Tris-HCl}$, $1\text{ mM EDTA}$, pH 8.0), $0.2\,\mu\text{m}$ vacuum filtered.
- Powder-free nitrile gloves.
- Precision ESD tweezers (carbon-fiber tipped).
- Digital Multimeter with fine micro-probe tips ($> 10\text{ G}\Omega$ input impedance mode).

---

## 3. Step-by-Step Assembly Procedure

### Step 3.1: Pre-Cleaning & Substrate Preparation
1. Clean the PTFE Interposer, PP Shim, and Delrin Anvil in an ultrasonic bath:
   - 10 minutes in HPLC-grade IPA.
   - 10 minutes in Milli-Q water.
   - Blow dry with filtered dry nitrogen gas ($N_2$).
2. Visually inspect the 12 ENIG landing pads under a stereo microscope ($10\times\text{--}20\times$) for dust, oxidation, or solder flux residue.

### Step 3.2: Fluidic Manifold & Bottom Plate Setup
1. Insert the 4× 1/8" NPT fluid fittings into the bottom face of **Plate 1 Base Hex**.
2. Thread until the fitting flanges seat completely **flush** within the 11.5 mm counterbore recesses.
3. Place the **Bottom Pusher Plate** (TPU) into the base nest of the reader housing lid.
4. Align Plate 1 Base Hex over the pusher plate with fluid ports matching the housing side-port angles.

### Step 3.3: Lower Fluidic Layer Layup
1. Place the **Bottom Trans PDMS Gasket** flat on Plate 1 Base Hex:
   - Align the Trans channel along the $330^\circ \leftrightarrow 150^\circ$ diagonal.
   - Confirm weep duct holes and perimeter grip cutouts seat without wrinkles.
2. Seat the **PTFE Interposer Board** on top of the Trans Gasket:
   - Verify Cis side (Bank B pads, CAD $Y > 0$) faces UP toward the amplifier.
   - Ensure the central $6.2\text{ mm}$ diamond aperture is concentric with the chamber center.
   - Solder/anchor sintered silver ribbon electrodes in the fluid path.

### Step 3.4: Nanopore Wafer Placement & Cis Gasket Layup
1. Using ESD vacuum pick-up or fine carbon tweezers, position the $4.0\times 4.0\times 0.5\text{ mm}$ silicon nanopore chip into the square pocket of the **Top Cis PDMS Gasket**.
2. Carefully invert and lower the Cis Gasket onto the PTFE Interposer:
   - The central silicone protrusion ($6.0\times 6.0\text{ mm}$, $45^\circ$) nests through the interposer diamond aperture, bringing the bottom face of the nanopore chip in contact with the Trans chamber.
   - Align the Cis microfluidic channel along the $210^\circ \leftrightarrow 30^\circ$ diagonal.

### Step 3.5: Anti-Wicking Barrier & Spacer Installation
1. Lay the clean **Polypropylene (PP) Shim** ($0.030" / 0.762\text{ mm}$) directly on top of the Cis gasket.
2. Align the 12 pogo pin pass-through holes and fluid port clearances.
3. Place the **3D-Printed Adjustable Spacer** ($\ge 3.0\text{ mm}$) over the PP shim:
   - Ensure component relief cavities face UP toward the incoming amplifier board.
   - Verify the 12 pogo pin guide channels align with the underlying interposer pads.

### Step 3.6: Amplifier Board & Pogo Array Engagement
1. Hold the **Cartridge Amplifier PCB** with `F.Cu` (component side and 12 pogo pins) facing **DOWN**.
2. Gently guide the 12 pogo pin tips into the spacer guide channels until the pin barrels enter the spacer cavities.
3. Verify that all 12 pogo pins seat onto their respective ENIG landing pads:
   - $P_1 \dots P_6$: Trans bank ($Y = -15.0\text{ mm}$).
   - $P_7 \dots P_{12}$: Cis bank ($Y = +15.0\text{ mm}$).

### Step 3.7: Anvil, Puck & Torque Cap Closure
1. Place the **Rigid Backing Anvil** ($6.0\text{ mm}$ Delrin) directly against the flat top (bare `B.Cu` ground plane) of the inverted amplifier board.
2. Place the **Pressure Puck** centrally on the anvil.
3. Thread the **Torque Cap** onto the Housing Lid Reader M75×8 external thread:
   - Rotate clockwise by hand until finger-tight resistance is met.
   - Continue rotating the Torque Cap Outer ring until all 6 internal PETG flexure pawls **slip and click**.
   - The ratchet slip torque ($\approx 0.5\text{ N}\cdot\text{m}$) delivers exactly $33\text{ N}$ of axial clamping force:
     - $9.6\text{ N}$ compresses the 12 pogo pins to their nominal $7.5\text{ mm}$ working stroke.
     - $\approx 23.4\text{ N}$ compresses the dual PDMS gaskets by $10\%$ ($1.588\text{ mm} \to 1.43\text{ mm}$), forming a liquid-tight hermetic seal.

---

## 4. Electrical Pre-Flight Verification

Before introducing conductive saline buffer into the flowcell, perform dry electrical checks via the reader test points:

| Measurement Check | Probe Nodes | Expected Reading | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Pogo Contact Resistance** | Amplifier test pad $\leftrightarrow$ Interposer strip | $< 50\text{ m}\Omega$ | Low-resistance gold contact verified on all 12 pins |
| **Pore Node DC Isolation** | `WS_CIS` (Pin 5) $\leftrightarrow$ `GNDA` | $> 10\text{ G}\Omega$ | Open circuit; no dielectric leakage across PP shim |
| **Driven Guard Isolation** | `GUARD` (Pin 4/6) $\leftrightarrow$ `WS_CIS` (Pin 5) | $> 10\text{ G}\Omega$ (dry) | High-impedance dry isolation between signal and guard |
| **Weep Moat Quiescent State**| `WEEP_SENSE` (Pin 11) $\leftrightarrow$ `GNDA` | $> 10\text{ M}\Omega$ (dry) | Open spark gap; LP5907 EN pin reads $+3.3\text{ V}$ |
| **LDO Rail Quiescent State** | $V_{LDO}$ (LP5907 output) | $+1.80\text{ V} \pm 10\text{ mV}$ | Clean 1.8V ADC power rail active |

---

## 5. Microfluidic Priming & Baseline Calibration

1. **Bubble-Free Wetting:**
   - Connect FEP feed tubing to Trans inlet ($H_3$, $330^\circ$) and Cis inlet ($H_1$, $210^\circ$).
   - Flush with $50\%$ ethanol/Milli-Q water at $50\,\mu\text{L/min}$ for 2 minutes to wet hydrophobic PDMS channel walls.
   - Flush with degassed 1.0 M KCl buffer at $25\,\mu\text{L/min}$ for 5 minutes.
2. **Current Baseline Measurement:**
   - Launch DAQ streaming: `./scripts/run_python.sh scripts/daq_client.py --bias 100`
   - Apply $+100\text{ mV}$ transmembrane bias voltage.
   - Verify steady DC baseline:
     - Sub-5 nm solid-state pore: $I_{baseline} \approx 50\text{ pA} - 1.5\text{ nA}$ with RMS noise $< 2.0\text{ pA}$.
     - 200 nm wide pore (Route 2): $I_{baseline} \approx 10 - 25\,\mu\text{A}$ with RMS noise $< 100\text{ nA}$.
3. **Leak Alarm ESTOP Check:**
   - If any fluid breaches the PDMS seal, the weep moat resistance collapses to $< 1\text{ k}\Omega$, pulling LP5907 EN LOW, instantly tripping the hardware ESTOP, halting ADC sampling, and halting pump rotation.
