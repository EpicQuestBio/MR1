# MR1 Cartridge Amplifier — Dual-Route TIA Netlist, Specifications & BOM
## Comprehensive Hardware Architecture for Route One (LMP7721) and Route Two (OPA192)

**Author:** Molecular Reality Corp / Antigravity  
**Date:** October 2026  
**Status:** Approved Engineering Documentation  
**Related Schematics:**
- [`Amplifier/Amplifier.kicad_sch`](file:///home/loki/Projects/daemon-pore/Amplifier/Amplifier.kicad_sch)
- [`Interposer/Interposer.kicad_sch`](file:///home/loki/Projects/daemon-pore/Interposer/Interposer.kicad_sch)
- [`BOM.md`](file:///home/loki/Projects/daemon-pore/BOM.md)

---

## 1. System Overview & Dual-Route Architecture

The MR1 Cartridge Amplifier implements a **dual-route front-end architecture** designed to bridge femtoampere single-molecule nanopore physics with microampere cell-counting / micropore physics:

```
                  4-ELECTRODE KELVIN CELL (PTFE INTERPOSER)
                  ┌────────────────────────────────────────┐
                  │ Pin 1:  CE_GNDA   (Counter Current Ret)│
                  │ Pin 2:  RE_TRANS  (Trans Sense Buffer) │
                  │ Pin 3:  >PORE     (Cis Bias Driver WE) │
                  │ Pin 6:  WS_CIS    (Route 1 Nano Sense) │
                  │ Pin 10: WS_CIS_WIDE (Route 2 Micro In) │
                  └────┬──────────────────────────────┬────┘
                       │                              │
                       │ J_POGO1 (Pins 5-7 Guarded)   │ J_POGO1 (Pins 8-10 Guarded)
                       ▼                              ▼
      ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
      │       ROUTE ONE (PATH 1)        │   │       ROUTE TWO (PATH 2)        │
      │  TI LMP7721 Ultra-Low-Noise     │   │  TI OPA192 Wideband Micropore   │
      │  R_f1 = 1.0 GΩ, C_f1 = 2.0 pF   │   │  R_f2 = 100 kΩ, C_f2 = 15.0 pF  │
      │  Range: ±2.048 nA (62.5 fA/LSB) │   │  Range: ±20.48 µA (0.625 nA/LSB)│
      │  Bandwidth: ~1 - 10 kHz         │   │  Bandwidth: 106.1 kHz (-3dB)    │
      │  Apertures: Sub-5 nm (DNA/RNA)  │   │  Apertures: 10 µm - 120 µm+     │
      └─────────────────────────────────┘   └─────────────────────────────────┘
```

### Route Selection Criteria

- **Route One (Path 1 — Sub-5 nm Nanopores):**  
  Optimized for biological nanopores (MspA, $\alpha$-Hemolysin, aerolysin) and sub-5 nm SiNx solid-state membranes. The ultra-low input bias current of `U2` ($3\text{ fA}$ typ.) and $1\text{ G}\Omega$ feedback resistor allow resolving single-molecule translocations. It saturates if current exceeds $\pm 2.048\text{ nA}$.
- **Route Two (Path 2 — $10\,\mu\text{m}$ & $100\,\mu\text{m}$ Micropores):**  
  Optimized for microscale salt apertures, cell counting, and Coulter analysis. The $100\text{ k}\Omega$ feedback resistor provides a linear measurement span of $\pm 20.48\,\mu\text{A}$ at $106.1\text{ kHz}$ bandwidth. It operates without modification for $10\,\mu\text{m}$ pores (up to $200\text{ mV}$ bias) and $100\,\mu\text{m}$ pores (at $\le 20\text{ mV}$ bias).

---

## 2. Point-to-Point Netlists

### A. Route One Netlist (LMP7721 Femtoampere TIA)

| Net Name | Origin Pin | Destination Pins | Function / Routing Rule |
| :--- | :--- | :--- | :--- |
| **`/WS_CIS`** | `J_POGO1.6` | `U2.8` (`-IN`), `R1.1`, `C1.1` | **Sensitive Summing Node:** Carries pore current. Must be fully surrounded by `/GUARD` on all layers. No solder mask. |
| **`/GUARD`** | `U2.2`, `U2.7` | `J_POGO1.5`, `J_POGO1.7`, Guard Ring Traces | **Driven Guard Shield:** Actively driven to match `/WS_CIS` potential, eliminating dielectric surface leakage. |
| **`/Vbias`** | MCP4822 DAC / Amp | `U2.1` (`+IN`), `R6.1` (1k) | **Non-Inverting Reference:** Defines virtual ground / cell bias. Decoupled with ultra-low ESR C0G capacitor. |
| **`Net-(C1-Pad1)`** | `U2.4` (`VOUT`) | `R1.2`, `C1.2`, ADC Driver Input (`U6A`) | **Route 1 Output:** Inverted voltage representation of current: $V_{\text{out}} = -I_{\text{pore}} \times 10^9\,\Omega$. |
| **`VDDA`** | TPS7A94 Output | `U2.6` (`V+`), `C10.1`, `C11.1` | **Positive Analog Rail:** $+2.5\text{V}$ / $+5.0\text{V}$ filtered analog supply. |
| **`VSSA`** | LT3094 Output | `U2.3` (`V-`), `C12.1` | **Negative Analog Rail:** $-2.5\text{V}$ / $-5.0\text{V}$ filtered analog supply. |
| **`GNDA`** | Main Star Ground | Decoupling caps return, Shield planes | Clean analog ground return. Decoupled from digital switching noise. |

---

### B. Route Two Netlist (OPA2192 Dual Micropore TIA & Active Guard Buffer) and Route Multiplexer (ADG1219)

| Net Name | Origin Pin | Destination Pins | Function / Routing Rule |
| :--- | :--- | :--- | :--- |
| **`WS_CIS_WIDE`** | `J_POGO1.10` / `J_PAD1.1` | `U5.2` (`-IN`), `R10.2`, `C3.2` | **Micropore Current Summing Node:** Carries microampere currents from $10\,\mu\text{m}$ / $100\,\mu\text{m}$ pores into inverting input. Dedicated $100\text{ k}\Omega \parallel 15\text{ pF}$ feedback loop. |
| **`GUARD_WIDE`** | `U5.7` (`OUT_B`) | `U5.6` (`-IN_B`), `J_POGO1.9`, `J_PAD1.2` | **Active Wideband Guard Shield:** Driven by low-impedance follower `U5B` ($< 0.1\,\Omega$) to eliminate capacitive crosstalk from microamp currents. Completely isolated from Route 1 passive guard. |
| **`Vbias`** | MCP4822 / Summer | `U5.3` (`+IN_A`), `U5.5` (`+IN_B`), `R9.1` (1k) | **Quiet Non-Inverting Bias Reference:** Defines cell reference / virtual ground; decoupled with C0G cap `C14` to GNDA. |
| **`Net-(U5A-~)`** | `U5.1` (`OUT_A`) | `R10.1`, `C3.1`, `R32.1` (49.9Ω) | **Route 2 Raw TIA Output:** Low-impedance op-amp output drives local feedback loop ($R_{10} \parallel C_3$) and isolation resistor `R32`. |
| **`Route2_OUT`** | `R32.2` (49.9Ω) | `U17.5` (`SB`) | **Route 2 Mux Input:** Output of Route 2 OPA2192 TIA feeding Channel B (`SB`) of `U17`. Isolated from `Signal_Return`. |
| **`Route1_OUT`** | `U16.6` (`OUT`) | `R3.1` (1k), `C9.1` (100nF), `U17.7` (`SA`) | **Route 1 Mux Input:** Output of Route 1 post-gain stage (`U16` LTC6268) feeding Channel A (`SA`) of `U17`. Isolated from `Signal_Return`. |
| **`Signal_Return`**| `U17.6` (`D`) | `R45.1` (499Ω) | **Multiplexed ADC Input:** Multiplexer common drain output driving the `U6` differential ADC driver input resistor. |
| **`/ROUTE_SEL`** | `J7.4` (via `R33` 27Ω) | `U17.8` (`IN`) | **Route Multiplexer Control:** 3.3V CMOS digital input from MCU/ESP32. Logic 0 (`ROUTE_SEL = 0`) = Route 1 (LMP7721 femtoamp TIA + LTC6268); Logic 1 (`ROUTE_SEL = 1`) = Route 2 (OPA2192 micropore TIA). |
| **`+3V3`** | 3.3V Digital Rail | `U17.1` (`EN`) | **Switch Active-High Enable:** Permanently tied high to keep multiplexer active. |
| **`VDDA`** | Positive Rail | `U5.8` (`V+`), `U17.2` (`VDD`), `C19.1`, `C40.1` | Positive Supply ($+2.5\text{V}$ / $+5.0\text{V}$). |
| **`VSSA`** | Negative Rail | `U5.4` (`V-`), `U17.4` (`VSS`), `C20.1`, `C42.1` | Negative Supply ($-2.5\text{V}$ / $-5.0\text{V}$). |
| **`GNDA`** | Main Star Ground | `U17.3` (`GND`), `C40.2`, `C42.2` | Clean analog ground return. |

---

### C. 4-Electrode Kelvin Pogo Interface (`J_POGO1`)

| Pin | Net Name | Interposer Cell Ring | Kelvin 4-Electrode Function |
| :---: | :---: | :---: | :--- |
| **1** | `CE_GNDA` | Outer Counter Ring (CE) | **Counter Current Return:** Sinks cell drive current directly to analog ground. |
| **2** | `RE_TRANS` | Inner Reference Ring (RE) | **Potential Sense Reference:** Zero-current potential pickoff on trans side. Rejects electrode polarization. |
| **3** | `>PORE` | Outer Working Ring (WE Drive) | **Working Drive Excitation:** Injects excitation potential from MCP4822 DAC. |
| **4** | `GNDA` | Guard Shield | Electrostatic guard between excitation drive and sensing inputs. |
| **5** | `GUARD` | Route 1 Guard Shield | Driven guard trace flanking Route 1 high-gain sense line. |
| **6** | `WS_CIS` | Inner Working Sense Ring (WS) | **Route 1 Input:** High-gain nano-aperture sense line to LMP7721 Pin 8. |
| **7** | `GUARD` | Route 1 Guard Shield | Driven guard trace flanking Route 1 high-gain sense line. |
| **8** | `GNDA` | Channel Separator | Ground shield isolating Route 1 from Route 2. |
| **9** | `GUARD_WIDE`| Route 2 Guard Shield | Shield trace for wideband micropore input line. |
| **10**| `WS_CIS_WIDE`| Inner Working Sense Ring (WS) | **Route 2 Input:** Wideband micropore current line to OPA192 Pin 2. |
| **11**| `GNDA` | Perimeter Shield | Ground ring surrounding outer perimeter of the cartridge. |
| **12**| `WEEP_SENSE`| Weep Moat Trace | Saline breach detector. Trips hardware interlock on 1M NaCl leakage. |

---

## 3. Component Values, Tolerances & Ratings

| Ref Des | Route | Component Type | Value | Tolerance | Rating | Tempco / Dielectric | Package / Footprint |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`U2`** | 1 | Precision Electrometer Op-Amp | **TI LMP7721** | — | $\pm 5.5\text{V}$ | $3\text{ fA}$ bias, $1.5\text{ fA}/\sqrt{\text{Hz}}$ | SOIC-8 (Guarded pinout) |
| **`R1`** | 1 | High-Megohm Feedback Resistor | **$1.0\text{ G}\Omega$** | **$\pm 1.0\%$** | $50\text{V}$ | $\pm 50\text{ ppm/}^\circ\text{C}$ Thick/Thin Film | 0805 / 1206 (Low stray C) |
| **`C1`** | 1 | Feedback Capacitor | **$2.0\text{ pF}$** | **$\pm 0.1\text{ pF}$** | $50\text{V}$ | **C0G / NP0** (Non-piezoelectric) | 0402 SMD |
| **`R6`** | 1 | Non-Inverting Protection Resistor| **$1.0\text{ k}\Omega$** | $\pm 0.1\%$ | $50\text{V}$ | $\pm 25\text{ ppm/}^\circ\text{C}$ Thin Film | 0402 SMD |
| **`C10`** | 1 | High-Frequency Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`C11`** | 1 | Bulk Analog Rail Decoupling | **$4.7\,\mu\text{F}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0805 SMD |
| **`C12`** | 1 | Negative Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`U5`** | 2 | Dual Precision Rail-to-Rail Op-Amp | **TI OPA2192IDR** | — | $\pm 18\text{V}$ | $5\,\mu\text{V}$ offset, $10\text{ MHz}$ GBW | SOIC-8 |
| **`U17`** | Both | Precision Low-Leakage SPDT Analog Switch | **ADI ADG1219BRMZ** | — | $\pm 16.5\text{V}$ | $< 1\text{ pA}$ leakage, $1.0\text{ pF}$ $C_\text{off}$, $< 1\text{ pC}$ $Q_\text{inj}$ | MSOP-8 |
| **`R10`** | 2 | Wideband Micropore Feedback Resistor | **$100.0\text{ k}\Omega$** | **$\pm 1.0\%$** | $50\text{V}$ | **$\pm 25\text{ ppm/}^\circ\text{C}$ Thin Film** | 0402 SMD |
| **`C3`** | 2 | Wideband Micropore Feedback Capacitor | **$15.0\text{ pF}$** | **$\pm 1.0\%$** | $50\text{V}$ | **C0G / NP0** ($Q > 1000$) | 0402 SMD |
| **`R32`** | 2 | Output Isolation Damping Resistor | **$49.9\ \Omega$** | **$\pm 1.0\%$** | $50\text{V}$ | Thick Film | 0402 SMD |
| **`C19`** | 2 | Positive Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`C20`** | 2 | Negative Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`C40`** | Both | Mux VDDA Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`C42`** | Both | Mux VSSA Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |

---

## 4. Recommended Manufacturer Parts List (BOM)

| Item | Component | Manufacturer | Manufacturer Part Number (MPN) | Distributor Source | Function & Selection Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **`U2`** | Texas Instruments | **`LMP7721MA/NOPB`** | Mouser: `926-LMP7721MA/NOPB`<br>DigiKey: `296-LMP7721MA/NOPB-ND` | Guaranteed $3\text{ fA}$ bias current; dedicated guard driver pins 2 and 7 flanking input pin 8. |
| **2** | **`R1`** | Ohmite / TE Connectivity | **`MOX-300001007FE`** or **`HB1100MFZRE`** | Mouser: `588-MOX-300001007FE`<br>DigiKey: `A106041-ND` | $1\text{ G}\Omega \pm 1\%$, ultra-low shunt capacitance ($< 0.1\text{ pF}$), rated for high-impedance electrometer circuits. |
| **3** | **`C1`** | Murata | **`GJM1555C1H2R0BB01D`** | Mouser: `81-GJM1555C1H2R0BB01D`<br>DigiKey: `490-GJM1555C1H2R0BB01D-ND` | $2\text{ pF} \pm 0.1\text{ pF}$, C0G/NP0 dielectric completely prevents piezoelectric pump vibration microphonics. |
| **4** | **`U5`** | Texas Instruments | **`OPA2192IDR`** | Mouser: `595-OPA2192IDR`<br>DigiKey: `296-48590-1-ND` | Dual precision e-trim op-amp (SOIC-8): Unit 1 = Micropore TIA; Unit 2 = Low-Z Guard Buffer driving `GUARD_WIDE`. |
| **5** | **`U17`** | Analog Devices | **`ADG1219BRMZ`** | Mouser: `584-ADG1219BRMZ`<br>DigiKey: `ADG1219BRMZ-ND` | High-voltage iCMOS SPDT 2:1 precision switch (MSOP-8): $< 1\text{ pA}$ leakage, $1.0\text{ pF}$ $C_\text{off}$, selects Route 1 vs Route 2 into ADC. |
| **6** | **`R10`** | Yageo / Susumu | **`RC0402FR-07100KL`** | Mouser: `603-RC0402FR-07100KL`<br>DigiKey: `311-100KLRTR-ND` | $100\text{ k}\Omega \pm 1\%$, micropore TIA feedback ($\pm 20.48\,\mu\text{A}$ range, $106.1\text{ kHz}$). |
| **7** | **`C3`** | Wurth / Murata | **`885012005058`** | Mouser: `710-885012005058`<br>DigiKey: `732-885012005058-ND` | $15\text{ pF} \pm 5\%$ C0G 0402; sets exact $-3\text{dB}$ cutoff to $106.1\text{ kHz}$ for Route 2 TIA. |
| **8** | **`R32`** | Yageo | **`RC0402FR-0749R9L`** | Mouser: `603-RC0402FR-0749R9L`<br>DigiKey: `311-49.9LRTR-ND` | $49.9\ \Omega \pm 1\%$ isolation and transmission damping resistor for Route 2 output. |
| **9** | **`J_POGO1`** | Mill-Max | **`821-22-012-10-000101`** | Mouser: `575-8212201210000101`<br>DigiKey: `ED1352-12-ND` | 12-Pin precision gold-plated beryllium copper spring-loaded header ($> 50\,\mu\text{in}$ Au over Ni). |

---

## 5. Critical Assembly, PCB Layout & Cleaning Rules

1. **Guarded Solder Mask Cutout on Route One:**  
   Solder mask must be completely stripped on top and bottom layers over `U2` Pin 8 (`/WS_CIS`) and the surrounding guard ring. Solder mask polymers absorb moisture and degrade surface resistivity below $10^{14}\,\Omega$.
2. **Dielectric Purity (C0G/NP0 Only):**  
   Never place X7R, X5R, or Y5V capacitors in the feedback loop (`C1` or `Cf2`). Piezoelectric microphonics from fluidic pump motors will inject false translocation pulses into the signal path.
3. **Solvent Cleaning Protocol:**  
   After SMT reflow, the Cartridge Amplifier must be cleaned via:
   - 10 min ultrasonic bath in HPLC-grade Isopropanol (> 99.8%).
   - 5 min ultrasonic rinse in Milli-Q deionized water ($18.2\text{ M}\Omega\cdot\text{cm}$).
   - 60 min dry bake at $80^\circ\text{C}$ to purge ionic contaminants.
