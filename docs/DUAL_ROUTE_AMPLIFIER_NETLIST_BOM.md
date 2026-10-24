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

### B. Route Two Netlist (OPA192 Wideband & Micropore TIA)

| Net Name | Origin Pin | Destination Pins | Function / Routing Rule |
| :--- | :--- | :--- | :--- |
| **`WS_CIS_WIDE`** | `J_POGO1.10` | `U17.2` (`-IN`), `Rf2.1`, `Cf2.1` | **Micropore Current Node:** Carries microampere currents from $10\,\mu\text{m}$ / $100\,\mu\text{m}$ pores. Short direct trace. |
| **`GUARD_WIDE`** | `J_POGO1.9` | Coplanar Shield Traces | **Wideband Shield:** Flanks `WS_CIS_WIDE` to prevent high-frequency capacitive crosstalk. |
| **`GNDA`** | Star Ground | `U17.3` (`+IN`) | **Virtual Ground Reference:** Non-inverting input tied to analog ground. |
| **`Path2_OUT`** | `U17.6` (`VOUT`) | `Rf2.2`, `Cf2.2`, ADC Input / Mux | **Route 2 Output:** Voltage scaled at $100\text{ mV}/\mu\text{A}$ ($V_{\text{out}} = -I_{\text{pore}} \times 100\text{ k}\Omega$). |
| **`VDDA`** | Positive Rail | `U17.7` (`V+`), `C19.1` | Positive Supply ($+2.5\text{V}$ / $+5.0\text{V}$). |
| **`VSSA`** | Negative Rail | `U17.4` (`V-`), `C20.1` | Negative Supply ($-2.5\text{V}$ / $-5.0\text{V}$). |

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
| **`U17`** | 2 | Precision Rail-to-Rail Op-Amp | **TI OPA192** | — | $\pm 18\text{V}$ | $5\,\mu\text{V}$ offset, $10\text{ MHz}$ GBW | SOIC-8 / MSOP-8 |
| **`Rf2`** | 2 | Wideband Feedback Resistor | **$100.0\text{ k}\Omega$** | **$\pm 0.1\%$** | $50\text{V}$ | **$\pm 25\text{ ppm/}^\circ\text{C}$ Thin Film** | 0603 / 0805 SMD |
| **`Cf2`** | 2 | Wideband Feedback Capacitor | **$15.0\text{ pF}$** | **$\pm 1.0\%$** | $50\text{V}$ | **C0G / NP0** ($Q > 1000$) | 0603 SMD |
| **`C19`** | 2 | Positive Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |
| **`C20`** | 2 | Negative Rail Decoupling | **$100\text{ nF}$** | $\pm 10\%$ | $25\text{V}$ | X7R Ceramic | 0402 SMD |

---

## 4. Recommended Manufacturer Parts List (BOM)

| Item | Component | Manufacturer | Manufacturer Part Number (MPN) | Distributor Source | Function & Selection Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **`U2`** | Texas Instruments | **`LMP7721MA/NOPB`** | Mouser: `926-LMP7721MA/NOPB`<br>DigiKey: `296-LMP7721MA/NOPB-ND` | Guaranteed $3\text{ fA}$ bias current; dedicated guard driver pins 2 and 7 flanking input pin 8. |
| **2** | **`R1`** | Ohmite / TE Connectivity | **`MOX-300001007FE`** or **`HB1100MFZRE`** | Mouser: `588-MOX-300001007FE`<br>DigiKey: `A106041-ND` | $1\text{ G}\Omega \pm 1\%$, ultra-low shunt capacitance ($< 0.1\text{ pF}$), rated for high-impedance electrometer circuits. |
| **3** | **`C1`** | Murata | **`GJM1555C1H2R0BB01D`** | Mouser: `81-GJM1555C1H2R0BB01D`<br>DigiKey: `490-GJM1555C1H2R0BB01D-ND` | $2\text{ pF} \pm 0.1\text{ pF}$, C0G/NP0 dielectric completely prevents piezoelectric pump vibration microphonics. |
| **4** | **`U17`** | Texas Instruments | **`OPA192IDR`** | Mouser: `595-OPA192IDR`<br>DigiKey: `296-OPA192IDR-ND` | e-trim precision CMOS/Bipolar; $5\,\mu\text{V}$ offset, $10\text{ MHz}$ GBW, handles $\pm 20.48\,\mu\text{A}$ without distortion. |
| **5** | **`Rf2`** | Susumu / Panasonic | **`RG1608P-104-B-T5`** or **`ERA-3AEB104V`** | Mouser: `754-RG1608P-104-B-T5`<br>DigiKey: `P100KBCT-ND` | $100\text{ k}\Omega \pm 0.1\%$, $\pm 25\text{ ppm/}^\circ\text{C}$ thin film prevents baseline gain drift during ambient temperature shifts. |
| **6** | **`Cf2`** | TDK / KEMET | **`C0603C150J5GACTU`** | Mouser: `80-C0603C150J5G`<br>DigiKey: `399-C0603C150J5GACTU-ND` | $15\text{ pF} \pm 5\%$, C0G dielectric; sets exact $-3\text{dB}$ cutoff to $106.1\text{ kHz}$ ($f_c = \frac{1}{2\pi R_{f2} C_{f2}}$). |
| **7** | **`J_POGO1`** | Mill-Max | **`821-22-012-10-000101`** | Mouser: `575-8212201210000101`<br>DigiKey: `ED1352-12-ND` | 12-Pin precision gold-plated beryllium copper spring-loaded header ($> 50\,\mu\text{in}$ Au over Ni). |

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
