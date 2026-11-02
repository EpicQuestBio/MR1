# MR1 Physical Stack Layup & Mechanical Reference

> **Stack Architecture:** Inverted Cartridge Amplifier with multi-pin coax pogo pin bridge, adjustable spacer block, dual identical gaskets with captured nanopore wafer, and bottom fluidic compression manifold.

---

## 1. Physical Stack Overview (Bottom to Top)

The assembly arranges fluidics at the bottom and sensitive high-Z electronics inverted on the top, completely isolating precision front-end circuitry from liquid risks.

```
[TOP CLAMP]           Torque-Lock Ratchet Cap (Outer + Inner M75 helical thread)
                           │
[PRESSURE PUCK]       Delrin / TPU Pressure Puck (with central pipette & probe port)
                           │
[RIGID ANVIL]         Rigid Backing Anvil (Delrin 6.0 mm or 6061-T6 Aluminum)
                           │
[AMPLIFIER PCB]       Amplifier Cartridge Board (Inverted, F.Cu component side facing down)
                      - SMT discrete pogo pins soldered on F.Cu
                      - Sensitive components (LMP7721, AD4000, passives) face down into spacer cavity
                           │
[SPACER STACK]        Adjustable Spacer Block:
                      - 3D-printed spacer (>= 3.0 mm) with component clearance cavities & wicking gap
                      - Polypropylene (PP) 0.030" (0.762 mm) chemical barrier shim
                      - Optional coarse Delrin blocks (0.125" / 3.175 mm or 0.270" / 6.858 mm)
                           │
[POGO BRIDGE]         12x C5221285 Gold-Plated Pogo Pins (~7.5 mm working compressed height)
                      - Signal center pins + Flanking 3D driven guard / ground cages
                           │
[CIS GASKET]          Cis Silicone / PDMS Gasket (Captures Silicon Nanopore Wafer)
                      - Fluid microchannels contact the top (Cis) face of the Interposer
                           │
[PTFE INTERPOSER]     2-Layer PTFE Interposer (Rogers RO3003 / PTFE 1.6 mm):
                      - Cis Face (Top): ENIG pads + Ag/AgCl ribbons (H1 -> H2 channel)
                      - Trans Face (Bottom): ENIG pads + Ag/AgCl ribbons (H3 -> H4 channel)
                      - Microfluidic "X" cross-channel architecture
                           │
[TRANS GASKET]        Trans Silicone / PDMS Gasket (Identical to Cis gasket)
                      - Fluid microchannels contact the bottom (Trans) face of the Interposer
                           │
[FITTINGS PLATE]      Bottom Plate 1 (Hex PP sheet):
                      - 4x Flush-mounted threaded fluidic fittings screwed from bottom
                      - Compression fits against the Trans gasket for liquid-tight seal
                           │
[BOTTOM PUSHER]       Bottom Pusher Plate & Reader Housing Lid / Neck Socket
```

---

## 2. Layer Dimensions & Compression Physics

| Layer Name | Material | Nominal Thickness | Compressed Thickness | Function |
|---|---|:---:|:---:|---|
| **Puck & Top Anvil** | Delrin / Aluminum | $6.0\text{ mm}$ | $6.0\text{ mm}$ | Clamps stack under torque cap |
| **Amplifier PCB** | Rogers RO3003 (2L) | $1.6\text{ mm}$ | $1.6\text{ mm}$ | Precision electrometer, flipped component-side down |
| **Pogo Air Gap** | Air + Spacers | $8.2\text{ mm}$ | $8.2\text{ mm}$ | Accommodates 7.5 mm working pin height |
| **Spacer Block** | 3D Printed + PP | $3.0 - 7.0\text{ mm}$ | $3.0 - 7.0\text{ mm}$ | Fills margins, shields components, isolates wicking |
| **Cis Gasket** | Silicone (50A) | $1.5875\text{ mm}$ ($1/16"$) | $\approx 1.43\text{ mm}$ ($10\%$ crush) | Seals Cis chamber & captures wafer |
| **Interposer** | PTFE / RO3003 | $1.6\text{ mm}$ | $1.6\text{ mm}$ | Mating ENIG pads, fluid pass-throughs H1–H4 |
| **Trans Gasket** | Silicone (50A) | $1.5875\text{ mm}$ ($1/16"$) | $\approx 1.43\text{ mm}$ ($10\%$ crush) | Seals Trans chamber against bottom plate |
| **Plate 1 Base** | Polypropylene | $4.0\text{ mm}$ | $4.0\text{ mm}$ | Flush mounting plate for 4 screwed fittings |
| **Bottom Pusher** | TPU | $3.0\text{ mm}$ | $\approx 2.9\text{ mm}$ | Base seal & reaction pad in neck socket |

---

## 3. Microfluidic "X" Channel Geometry

Fluid enters and drains exclusively from the bottom plate through 4 flush fittings:

1. **Cis Flow ($H_1 \to H_2$):**
   - Inflow at $H_1$ $(-17.32, +10.0\text{ mm})$, rises through Interposer via $2.1\text{ mm}$ drill hole.
   - Flows across the Cis (top) face along the diagonal path towards $H_2$ $(+17.32, -10.0\text{ mm})$.
   - Drops down through $H_2$ to the bottom plate drain fitting.

2. **Trans Flow ($H_3 \to H_4$):**
   - Inflow at $H_3$ $(-17.32, -10.0\text{ mm})$ directly into the bottom gasket channel.
   - Flows across the Trans (bottom) face along the opposing diagonal path towards $H_4$ $(+17.32, +10.0\text{ mm})$.
   - Exits directly into the bottom plate drain fitting at $H_4$.

The two channels cross at the central nanopore aperture without intersecting, creating the fluidic "X".

---

## 4. Electrical Pogo Pin & Guard Bridge

The 12 pogo pins are arranged along two parallel lines ($Y = \pm 15.0\text{ mm}$ in KiCad):

- **Bank B (Cis / Sensing, CAD $Y > 0$):**
  - $P_1$: `GNDA_SHLD` $(-18, +16)$ — Ground anchor.
  - $P_2$: `WS_CIS_WIDE` $(-10, +15)$ — Path 2 working sense (coax ring: `GUARD_WIDE`).
  - $P_3$: `GUARD_WIDE` $(-6, +15)$ — Active guard feeder for $P_2$ ring.
  - $P_4$: `GUARD_CIS_A` $(+4, +15)$ — Flanking guard feeder A for $P_5$ ring.
  - $P_5$: `WS_CIS` $(+8, +15)$ — Path 1 electrometer high-Z node (coax ring: `GUARD`).
  - $P_6$: `GUARD_CIS_B` $(+12, +15)$ — Flanking guard feeder B for $P_5$ ring.

- **Bank A (Trans / Excitation, CAD $Y < 0$):**
  - $P_7$: `CE_GNDA` $(-18, -16)$ — Counter electrode (coax ring: `GNDA`).
  - $P_8$: `RE_TRANS` $(-10, -15)$ — Reference electrode (coax ring: `GNDA`).
  - $P_9$: `>PORE_AMP` $(-4, -15)$ — Bias drive (coax ring: `GNDA`).
  - $P_{10}$: `GNDA` $(+3, -15)$ — Ground fence feeder.
  - $P_{11}$: `WEEP_SENSE` $(+12, -15)$ — Moisture sense (coax ring: `GNDA`).
  - $P_{12}$: `GNDA_WEEP` $(+18, -16)$ — Perimeter weep drain feeder.
