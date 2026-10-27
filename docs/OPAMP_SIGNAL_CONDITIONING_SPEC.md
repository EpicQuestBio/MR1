# MR1 & Cartridge Amplifier — Op-Amp Signal Conditioning & $V_{\text{PORE}}$ Excitation Specification
## End-to-End Transfer Functions, $V_{\text{PORE}}$ Bias Range, Reference Cancellation, and ADC Scaling

**Author:** Molecular Reality Corp / Antigravity  
**Date:** October 2026  
**Status:** Approved Engineering Documentation  
**Related Schematics & Simulations:**
- [`MR1/Ignition.kicad_sch`](file:///home/loki/Projects/daemon-pore/MR1/Ignition.kicad_sch) & [`MR1/Power.kicad_sch`](file:///home/loki/Projects/daemon-pore/MR1/Power.kicad_sch)
- [`Amplifier/Amplifier.kicad_sch`](file:///home/loki/Projects/daemon-pore/Amplifier/Amplifier.kicad_sch)
- [`simulations/opamp_signal_conditioning.py`](file:///home/loki/Projects/daemon-pore/simulations/opamp_signal_conditioning.py)
- [`simulations/pore_dac_dynamics.py`](file:///home/loki/Projects/daemon-pore/simulations/pore_dac_dynamics.py)
- [`simulations/nanopore_electrokinetics.py`](file:///home/loki/Projects/daemon-pore/simulations/nanopore_electrokinetics.py)

---

## 1. End-to-End Signal Conditioning Architecture

The daemon-pore analog signal chain is split across two boards connected via the 4-electrode Kelvin cell interposer:
1. **Excitation Conditioning (`MR1` Board):** Synthesizes an ultra-low-noise, 18.66-bit effective composite bipolar bias potential $V_{\text{PORE}} \in [-2.482\text{ V}, +2.458\text{ V}]$ from a dual 12-bit SPI DAC (`U9` `MCP4822`), precision $+2.048\text{ V}$ voltage reference (`U13` `ADR4520`), and dual JFET-input op-amp (`U3A`/`U3B` `OPA2197`).
2. **Dual-Route Current Readout & ADC Conditioning (`Amplifier` Board):** Converts transmembrane ionic current $I_{\text{pore}}$ into a differential voltage digitized by a 16-bit, 2 MSPS SAR ADC (`U13` `AD4000`) via two software-selectable analog routes (`U17` `ADG1219BRMZ`):
   - **Route 1 (`ROUTE_SEL = 0`):** Femtoampere TIA (`U2` `LMP7721`, $1\text{ G}\Omega \parallel 2\text{ pF}$) + Reference-Cancelling $10.0\times$ Post-Gain Filter (`U16` `LTC6268`, $1\text{ k}\Omega \parallel 100\text{ nF}$).
   - **Route 2 (`ROUTE_SEL = 1`):** Wideband Micropore TIA (`U5A` `OPA2192IDR`, $100\text{ k}\Omega \parallel 15\text{ pF}$) + Active Guard Buffer (`U5B` `OPA2192IDR`).
   - **Common ADC Front-End:** SPDT Route Switch (`U17` `ADG1219BRMZ`) $\rightarrow$ Fully Differential ADC Driver (`U6` `ADA4940-1`) $\rightarrow$ $2.95\text{ MHz}$ Differential RC Anti-Aliasing Filter ($R_{27}, R_{41}, C_{41}$) $\rightarrow$ 16-Bit ADC (`U13` `AD4000`).

```
====================================================================================================
1. MR1 COMPOSITE BIPOLAR EXCITATION CHAIN (MR1/Ignition.kicad_sch)
====================================================================================================
  U13 (ADR4520) ──► +2.048V ──► R13 (10k) ──► U3B (OPA2197, R22=10k) ──► -2.048V
                                                                            │
                                                                        R35 (20k, G = -1.20)
                                                                            ▼
  U9A (MCP4822 Ch A Coarse) ──► R31 (10k, G = -2.40) ──► ┌──────────────────────┐   R43 (27Ω)
                                                         │ U3A (OPA2197 Summer) ├───/\/\/───┬──► >PORE
  U9B (MCP4822 Ch B Vernier) ─► R21 (1M,  G = -0.024) ─► │ Feedback:            │           │    (Cis WE)
                                                         │ R29 (24k) || C43(1nF)│        C29 (100nF)
                                                         └──────────────────────┘           │
                                                                                           GNDA

====================================================================================================
2. AMPLIFIER DUAL-ROUTE READOUT & ADC CHAIN (Amplifier/Amplifier.kicad_sch)
====================================================================================================
  ROUTE 1 (Sub-5nm Nanopores, ±204.8 pA full-scale @ Stage 2):
  /WS_CIS ──► U2 (LMP7721 TIA, R1=1GΩ || C1=2pF, fc1=79.6Hz)
                │  V_U2 = V_bias - I_pore * 1GΩ
                ▼
              R8 (100Ω) / R5 (1kΩ) [Divider = 10/11]
                │
                ▼
              U16 (LTC6268 Post-Gain, R4=100Ω to /Vbias, R3=1kΩ || C9=100nF, fc2=1.59kHz)
                │  V_Route1_OUT = -10.0 * I_pore * 1GΩ  (Exact /Vbias Cancellation!)
                ▼
              U17.7 (SA) ──┐
                           ├──► U17.6 (D: Signal_Return) ──► R45 (499Ω) ──► U6 (ADA4940-1 FDA)
              U17.5 (SB) ──┘                                                   │  R27/R41 (27Ω) + C41 (1nF)
                ▲                                                              ▼  (fc_AA = 2.95 MHz)
  ROUTE 2 (10-100µm Micropores, ±20.48 µA full-scale):                      U13 (AD4000 16-Bit ADC)
  /WS_CIS_WIDE ─► U5A (OPA2192 TIA, R10=100kΩ || C3=15pF, fc=106.1kHz) ──► R32 (49.9Ω)
  /GUARD_WIDE  ◄─ U5B (OPA2192 Unity-Gain Active Guard Buffer from /Vbias, Z_out = 0.03Ω @ 10kHz)
```

---

## 2. Excitation Signal Conditioning & $V_{\text{PORE}}$ Voltage Range (`MR1` Board)

### 2.1 Analog Supply Rails (`MR1/Power.kicad_sch`)
- **Charge-Pump Pre-Regulator (`U1` `LM27762`):** Generates regulated positive and negative pre-rails from USB/5V input.
- **Ultra-Low-Noise Positive LDO (`U4` `LT3045`):** Set by $R_2 = 24.9\text{ k}\Omega$ ($I_{\text{SET}} = 100\,\mu\text{A}$):
  $$\text{VDDA} = 100\,\mu\text{A} \times 24.9\text{ k}\Omega = +2.490\text{ V} \quad (0.8\,\mu\text{V}_{\text{rms}}\text{ noise, } 10\text{ Hz–100 kHz})$$
- **Ultra-Low-Noise Negative LDO (`U2` `LT3094`):** Set by $R_7 = 24.9\text{ k}\Omega$ ($I_{\text{SET}} = 100\,\mu\text{A}$):
  $$\text{VSSA} = -100\,\mu\text{A} \times 24.9\text{ k}\Omega = -2.490\text{ V} \quad (0.8\,\mu\text{V}_{\text{rms}}\text{ noise, } 10\text{ Hz–100 kHz})$$

### 2.2 Precision Reference & Inverting Buffer (`U13` `ADR4520` + `U3B` `OPA2197`)
- **`U13` (`ADR4520`):** Generates a low-drift $+2.048\text{ V}$ reference on `/Ignition/2.048V`.
- **`U3B` (`OPA2197` Unit B):** Configured as a unity-gain inverting amplifier with $+IN$ (Pin 5) tied to `GNDA`, input resistor $R_{13} = 10\text{ k}\Omega\ (1\%)$, feedback resistor $R_{22} = 10\text{ k}\Omega\ (1\%)$, noise-reduction capacitors $C_{24} = 4.7\,\mu\text{F}$ and $C_{26} = 4.7\,\mu\text{F}$, and output isolation resistor $R_{42} = 27\,\Omega$:
  $$V_{\text{U3B}} = -\frac{R_{22}}{R_{13}} V_{\text{REF}} = -\frac{10\text{ k}\Omega}{10\text{ k}\Omega} (2.048\text{ V}) = -2.0480\text{ V}$$

### 2.3 Composite Bipolar Summing Amplifier (`U3A` `OPA2197` + `U9` `MCP4822`)
`U3A` (`OPA2197` Unit A) has its non-inverting input ($+IN$, Pin 3) referenced to `GNDA` ($0\text{ V}$) and sums three currents into its inverting node ($-IN$, Pin 2) across feedback network $R_{29} = 24\text{ k}\Omega \parallel C_{43} = 1\text{ nF}$:

| Input Branch | Source Pin | Series Resistor | Gain ($-R_{29}/R_{\text{in}}$) | Full-Scale Span (1x DAC Mode) | Step Size per LSB |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Coarse Bias (`VA`)** | `U9.8` (`VOUTA`) | $R_{31} = 10\text{ k}\Omega$ | $G_A = -\frac{24\text{ k}\Omega}{10\text{ k}\Omega} = \mathbf{-2.40\text{ V/V}}$ | $0\text{ V} \rightarrow -4.9152\text{ V}$ | $\mathbf{-1.200\text{ mV/LSB}}$ |
| **Fine Vernier (`VB`)** | `U9.6` (`VOUTB`) | $R_{21} = 1\text{ M}\Omega$ | $G_B = -\frac{24\text{ k}\Omega}{1\text{ M}\Omega} = \mathbf{-0.024\text{ V/V}}$ | $0\text{ V} \rightarrow -49.152\text{ mV}$ | $\mathbf{-12.00\,\mu\text{V/LSB}}$ |
| **Bipolar Offset** | `U3B.7` ($-2.048\text{ V}$) | $R_{35} = 20\text{ k}\Omega$ | $G_{\text{off}} = -\frac{24\text{ k}\Omega}{20\text{ k}\Omega} = \mathbf{-1.20\text{ V/V}}$ | Fixed $+2.4576\text{ V}$ offset | Fixed DC offset |

#### Exact $V_{\text{PORE}}$ Transfer Equation
For 12-bit DAC codes $D_A, D_B \in [0, 4095]$ in $1\times$ gain mode ($V_{\text{FS}} = 2.048\text{ V}$, $\text{LSB}_{\text{DAC}} = 0.500\text{ mV}$):
$$V_A = \frac{D_A}{4096} \times 2.048\text{ V}, \qquad V_B = \frac{D_B}{4096} \times 2.048\text{ V}$$
$$V_{\text{PORE}}(V_A, V_B) = +2.4576\text{ V} - 2.40\,V_A - 0.024\,V_B$$
In terms of raw 12-bit integer codes $(D_A, D_B)$:
$$V_{\text{PORE}}(D_A, D_B) = +2.4576\text{ V} - (1.20\text{ mV}) \cdot D_A - (12.0\,\mu\text{V}) \cdot D_B$$

#### $V_{\text{PORE}}$ Operating Voltage Range & Code Mapping Table
| Operating Point | Coarse Code (`D_A`) | Fine Code (`D_B`) | `VA` (V) | `VB` (V) | Ideal $V_{\text{PORE}}$ (V) | Clamped $V_{\text{PORE}}$ (`±2.49V` Rails) | Physical Application |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Max Positive Bias** | `0` | `0` | $0.0000\text{ V}$ | $0.0000\text{ V}$ | **`+2.457600 V`** | `+2.457600 V` ($32.4\text{ mV}$ rail margin) | Positive electroporation / dielectric breakdown |
| **Standard +180 mV DNA Bias** | `1898` | `0` | $0.9490\text{ V}$ | $0.0000\text{ V}$ | **`+0.180000 V`** | `+0.180000 V` | ssDNA / dsDNA translocation capture |
| **Standard +100 mV Micropore** | `1964` | `67` | $0.9820\text{ V}$ | $0.0335\text{ V}$ | **`+0.099996 V`** | `+0.099996 V` | $10\,\mu\text{m}$ / $200\text{ nm}$ baseline bias |
| **Exact Zero Bias (Midscale)** | `2048` | `0` | $1.0240\text{ V}$ | $0.0000\text{ V}$ | **`0.000000 V`** | `0.000000 V` | Open-circuit offset / Ag/AgCl asymmetry nulling |
| **1 Fine Vernier Step** | `2048` | `1` | $1.0240\text{ V}$ | $0.0005\text{ V}$ | **`-0.000012 V`** | `-0.000012 V` ($-12.0\,\mu\text{V}$) | Microvolt electrochemical potential trim |
| **100 Fine Steps = 1 Coarse Step** | `2048` | `100` | $1.0240\text{ V}$ | $0.0500\text{ V}$ | **`-0.001200 V`** | `-0.001200 V` ($-1.20\text{ mV}$) | Seamless $100:1$ vernier handoff |
| **Max Negative (Coarse Only)** | `4095` | `0` | $2.0475\text{ V}$ | $0.0000\text{ V}$ | **`-2.456400 V`** | `-2.456400 V` ($33.6\text{ mV}$ rail margin) | Negative unclogging / reverse translocation |
| **Max Negative (Coarse + Fine)** | `4095` | `2800` | $2.0475\text{ V}$ | $1.4000\text{ V}$ | **`-2.490000 V`** | `-2.490000 V` (`VSSA` rail limit) | Full negative rail limit |

- **Vernier Ratio:** $\left|\frac{G_A}{G_B}\right| = \frac{2.40}{0.024} = \mathbf{100.0}$ ($100$ fine steps on `VB` equal exactly $1$ coarse step on `VA`).
- **Effective Composite Resolution:** $\log_2\left(\frac{4.9644\text{ V}}{12.0\,\mu\text{V}}\right) = \mathbf{18.66\text{ bits}}$.

### 2.4 Excitation Frequency Response & Filtering Poles
1. **Active Summing Feedback Pole (`R29` $\parallel$ `C43`):**
   $$f_{-3\text{dB,U3A}} = \frac{1}{2\pi R_{29} C_{43}} = \frac{1}{2\pi (24\text{ k}\Omega)(1.0\text{ nF})} = \mathbf{6.631\text{ kHz}}$$
   Strips broadband DAC glitch energy and thermal noise above $6.6\text{ kHz}$ while preserving fast bias step settling ($\tau = R_{29} C_{43} = 24\,\mu\text{s}$).
2. **Passive Output Isolation Filter (`R43` + `C29`):**
   $$f_{-3\text{dB,out}} = \frac{1}{2\pi R_{43} C_{29}} = \frac{1}{2\pi (27\,\Omega)(100\text{ nF})} = \mathbf{58.95\text{ kHz}}$$
   Isolates the `OPA2197` output stage from the capacitive double-layer load ($C_{\text{dl}}$) of the flowcell working electrode (`>PORE`), ensuring unconditional phase margin.

---

## 3. Route 1 Femtoampere Readout Conditioning (`Amplifier` Board)

### 3.1 Stage 1: Femtoampere Transimpedance Amplifier (`U2` `LMP7721`)
- **Topology:** Inverting TIA with $+IN$ (Pin 1) biased at `/Vbias` and $-IN$ (Pin 8) connected to `/WS_CIS`.
- **Feedback Network:** $R_1 = 1.0\text{ G}\Omega \parallel C_1 = 2.0\text{ pF}$.
- **Transfer Function:**
  $$V_{\text{U2}}(s) = V_{\text{bias}} - I_{\text{pore}}(s)\frac{R_1}{1 + s R_1 C_1}, \qquad f_{-3\text{dB,1}} = \frac{1}{2\pi R_1 C_1} = \mathbf{79.58\text{ Hz}}$$
- **Passive Guard (`NT3`):** `/GUARD` is passively tied to `/Vbias` via net-tie `NT3`. Because `U2` operates over a low-frequency bandwidth ($79.6\text{ Hz}$) with $1\text{ G}\Omega$ source impedance, passive guarding to the quiet C0G-decoupled `/Vbias` reference eliminates op-amp buffer voltage noise ($e_n$) from coupling across the guard-to-input capacitance $C_{\text{guard-in}}$.

### 3.2 Stage 2: Differential Reference-Cancelling Post-Gain & Filter (`U16` `LTC6268`)
If Stage 2 were a simple non-inverting amplifier referenced to `GNDA`, it would amplify $V_{\text{bias}}$ by $11\times$, immediately saturating the output whenever $V_{\text{bias}} > 220\text{ mV}$. Instead, `U16` (`LTC6268`) is wired as a **matched difference amplifier that cancels $V_{\text{bias}}$**:

- **Non-Inverting Input (`+IN`, Pin 3):** Potential divider formed by $R_8 = 100\,\Omega$ (from `U2` Pin 4) and $R_5 = 1.0\text{ k}\Omega$ (to `GNDA`):
  $$V_+(s) = V_{\text{U2}}(s) \cdot \frac{R_5}{R_8 + R_5} = \frac{1000}{100 + 1000} V_{\text{U2}}(s) = \frac{10}{11} V_{\text{U2}}(s)$$
- **Inverting Input (`-IN`, Pin 2):** Input resistor $R_4 = 100\,\Omega$ returned to `/Vbias`, and feedback impedance $Z_3(s) = \frac{R_3}{1 + s R_3 C_9}$ ($R_3 = 1.0\text{ k}\Omega$, $C_9 = 100\text{ nF}$):
  $$f_{-3\text{dB,2}} = \frac{1}{2\pi R_3 C_9} = \frac{1}{2\pi (1\text{ k}\Omega)(100\text{ nF})} = \mathbf{1591.55\text{ Hz}}$$
- **Exact DC Reference Cancellation ($s \to 0$, $Z_3(0) = R_3 = 1000\,\Omega$):**
  $$V_{\text{Route1\_OUT}} = \left(1 + \frac{R_3}{R_4}\right) V_+ - \frac{R_3}{R_4} V_{\text{bias}} = \left(1 + \frac{1000}{100}\right)\frac{10}{11}\left(V_{\text{bias}} - I_{\text{pore}}R_1\right) - \frac{1000}{100}V_{\text{bias}}$$
  $$V_{\text{Route1\_OUT}} = 11 \cdot \frac{10}{11}\left(V_{\text{bias}} - I_{\text{pore}}R_1\right) - 10\,V_{\text{bias}} = 10\,V_{\text{bias}} - 10\,I_{\text{pore}}R_1 - 10\,V_{\text{bias}} = \mathbf{-10.0\,I_{\text{pore}}R_1}$$
- **Net Route 1 Transimpedance & Linear Dynamic Range:**
  - Effective DC Transimpedance: $Z_{\text{T,Route1}}(0) = -10.0 \times 1.0\text{ G}\Omega = \mathbf{-10.0\text{ G}\Omega}$ ($\mathbf{-10.0\text{ mV/pA}}$ or $\mathbf{-10.0\text{ V/nA}}$).
  - Full-Scale Linear Current Range (for $\pm 2.048\text{ V}$ output swing): $\mathbf{\pm 204.8\text{ pA}}$.
  - Common-Mode $V_{\text{bias}}$ Rejection: Exact ($0.0\text{ V/V}$ feedthrough for matched ratios $\frac{R_8}{R_5} = \frac{R_4}{R_3} = \frac{1}{10}$).

### 3.3 Route 1 Input-Referred Current Noise Budget (`U2` `LMP7721` @ $25\,^\circ\text{C}$)
$$i_n(f) = \sqrt{2 q I_b + \frac{4 k_B T}{R_1} + e_n^2 \left[\frac{1}{R_1^2} + \left(2\pi f (C_{\text{in}} + C_1)\right)^2\right]}$$

| Noise Source | Formula / Parameter | Spectral Density @ $100\text{ Hz}$ ($C_{\text{in}} = 15\text{ pF}$) |
| :--- | :--- | :--- |
| **Input Bias Shot Noise** | $\sqrt{2 q I_b}$ ($I_b = 3\text{ fA}$) | $0.98\text{ fA}/\sqrt{\text{Hz}}$ |
| **Feedback Resistor Thermal Noise** | $\sqrt{4 k_B T / R_1}$ ($R_1 = 1\text{ G}\Omega$) | $4.06\text{ fA}/\sqrt{\text{Hz}}$ |
| **Capacitive Voltage Noise ($e_n C_{\text{tot}}$)** | $2\pi f (C_{\text{in}} + C_1) e_n$ ($e_n = 6.5\text{ nV}/\sqrt{\text{Hz}}$) | $0.07\text{ fA}/\sqrt{\text{Hz}}$ |
| **Total Input-Referred Noise Density** | $\sqrt{\sum i_{n,k}^2}$ | **`4.06 fA/√Hz`** |
| **Integrated RMS Noise ($79.6\text{ Hz}$ BW)** | $\sqrt{\int_0^{79.6\text{ Hz}} i_n^2(f)\,df}$ | **`36.2 fA_rms`** ($0.036\text{ pA}_{\text{rms}}$) |

---

## 4. Route 2 Wideband Micropore Readout & Active Guard (`Amplifier` Board)

### 4.1 Stage 1: Wideband Micropore TIA (`U5A` `OPA2192IDR`)
- **Topology:** Inverting TIA with $+IN$ (Pin 3) biased at `/Vbias` and $-IN$ (Pin 2) connected to `/WS_CIS_WIDE`.
- **Feedback Network:** $R_{10} = 100\text{ k}\Omega \parallel C_3 = 15\text{ pF}$, followed by series isolation resistor $R_{32} = 49.9\,\Omega$ driving `/Route2_OUT`.
- **Transfer Function & Bandwidth:**
  $$V_{\text{Route2\_OUT}}(s) = V_{\text{bias}} - I_{\text{pore}}(s)\frac{R_{10}}{1 + s R_{10} C_3}, \qquad f_{-3\text{dB,Route2}} = \frac{1}{2\pi R_{10} C_3} = \mathbf{106.10\text{ kHz}}$$
- **Full-Scale Current Range (at $V_{\text{bias}} = 0\text{ V}$, $\pm 2.048\text{ V}$ swing):** $\mathbf{\pm 20.48\,\mu\text{A}}$.

### 4.2 Active Guard Buffer (`U5B` `OPA2192IDR`) vs. Route 1 Passive Guard (`NT3`)
- **`U5B` (`OPA2192IDR` Unit B):** Configured as a dedicated unity-gain follower ($+IN$ Pin 5 = `/Vbias`, $-IN$ Pin 6 = `OUT` Pin 7 = `/GUARD_WIDE`, $\text{GBW} = 10\text{ MHz}$, $R_{\text{out,OL}} \approx 30\,\Omega$).
- **Closed-Loop Guard Output Impedance:**
  $$Z_{\text{out,active}}(f) = \frac{R_{\text{out,OL}}}{1 + A_{\text{OL}}(f)}$$
  At $f = 10\text{ kHz}$ ($|A_{\text{OL}}| \approx 1000$):
  $$|Z_{\text{out,active}}(10\text{ kHz})| \approx \mathbf{0.030\,\Omega} \quad \text{vs.} \quad |Z_{\text{guard,passive}}| \approx 200\,\Omega$$
  This provides **$+76.5\text{ dB}$** of additional high-frequency AC capacitive displacement current absorption on `/GUARD_WIDE` across the $106.1\text{ kHz}$ micropore passband, while keeping `U5B`'s switching/output currents completely isolated from Route 1's femtoampere `/GUARD` ring.

---

## 5. Multiplexer (`U17`), Differential ADC Driver (`U6`), and 16-Bit ADC (`U13`)

### 5.1 Route Multiplexer (`U17` `ADG1219BRMZ`) & FDA Input Impedance Interaction
`U17` (`ADG1219BRMZ`) switches either `/Route1_OUT` (`SA`, Pin 7, when `ROUTE_SEL = 0`) or `/Route2_OUT` (`SB`, Pin 5, when `ROUTE_SEL = 1`) to `/Signal_Return` (`D`, Pin 6), which feeds input resistor $R_{45} = 499\,\Omega\ (0.1\%)$ of the fully differential ADC driver `U6` (`ADA4940-1`, configured with $R_{43} = R_{44} = R_{45} = R_{46} = 499\,\Omega$).

Because `U17` has a finite on-resistance $R_{\text{on}} \approx 150\,\Omega$ (and Route 2 includes series resistor $R_{32} = 49.9\,\Omega$) directly in series with $R_{45} = 499\,\Omega$, the effective input resistance of the `U6` inverting signal branch is:
- **Ideal Zero-Impedance FDA Gain:**
  $$G_{\text{FDA,ideal}} = -\frac{R_{46}}{R_{45}} = -\frac{499\,\Omega}{499\,\Omega} = \mathbf{-1.0000\text{ V/V}}$$
- **Actual Hardware FDA Gain (including `U17` $R_{\text{on}} = 150\,\Omega$ and $R_{32}$):**
  - **Route 1 (`ROUTE_SEL = 0`):**
    $$G_{\text{FDA,Route1}} = -\frac{R_{46}}{R_{45} + R_{\text{on,U17}}} = -\frac{499\,\Omega}{499\,\Omega + 150\,\Omega} = \mathbf{-0.7689\text{ V/V}}$$
  - **Route 2 (`ROUTE_SEL = 1`):**
    $$G_{\text{FDA,Route2}} = -\frac{R_{46}}{R_{45} + R_{\text{on,U17}} + R_{32}} = -\frac{499\,\Omega}{499\,\Omega + 150\,\Omega + 49.9\,\Omega} = \mathbf{-0.7140\text{ V/V}}$$

> [!NOTE]
> Firmware calibration on the host/MCU multiplies raw `AD4000` codes by $\frac{1}{0.7689} = 1.3006$ on Route 1 and $\frac{1}{0.7140} = 1.4006$ on Route 2 (or measures a two-point reference step) to account for the series switch resistance of `U17`.

### 5.2 Differential Anti-Aliasing Filter (`R27`, `R41`, `C41`) & `U13` (`AD4000`)
Between `U6` (`ADA4940-1`) differential outputs and `U13` (`AD4000` Pins `IN+`/`IN-`), series resistors $R_{27} = 27\,\Omega$ and $R_{41} = 27\,\Omega$ combine with differential capacitor $C_{41} = 1.0\text{ nF}$:
$$f_{-3\text{dB,AA}} = \frac{1}{2\pi (R_{27} + R_{41}) C_{41}} = \frac{1}{2\pi (54\,\Omega)(1.0\text{ nF})} = \mathbf{2.947\text{ MHz}}$$
This absorbs the switched-capacitor charge kickback of the 2 MSPS `AD4000` SAR ADC while introducing zero phase distortion across the $106.1\text{ kHz}$ analog passband.

### 5.3 End-to-End Signal Chain Summary Table

| Parameter | Excitation (`MR1` `>PORE`) | Readout Route 1 (`ROUTE_SEL = 0`) | Readout Route 2 (`ROUTE_SEL = 1`) |
| :--- | :--- | :--- | :--- |
| **Active Op-Amps** | `U3B` + `U3A` (`OPA2197`) | `U2` (`LMP7721`) + `U16` (`LTC6268`) | `U5A` (`OPA2192` TIA) + `U5B` (`OPA2192` Guard) |
| **Feedback Elements** | $R_{29}=24\text{ k}\Omega \parallel C_{43}=1\text{ nF}$ | Stage 1: $1\text{ G}\Omega \parallel 2\text{ pF}$<br>Stage 2: $1\text{ k}\Omega \parallel 100\text{ nF}$ | Stage 1: $100\text{ k}\Omega \parallel 15\text{ pF}$ |
| **DC Gain / Transimpedance** | $-2.40\text{ V/V}$ (Ch A)<br>$-0.024\text{ V/V}$ (Ch B) | $-1.0\text{ G}\Omega$ (Stage 1)<br>$-10.0\text{ G}\Omega$ (Stage 2 Out) | $-100.0\text{ k}\Omega$ |
| **Primary $-3\text{ dB}$ Bandwidth** | $6.631\text{ kHz}$ | $79.58\text{ Hz}$ (Stage 1)<br>$1.592\text{ kHz}$ (Stage 2) | $106.10\text{ kHz}$ |
| **Secondary / Output Filter** | $58.95\text{ kHz}$ ($27\,\Omega + 100\text{ nF}$) | $2.947\text{ MHz}$ (`AD4000` AA filter) | $2.947\text{ MHz}$ (`AD4000` AA filter) |
| **Guard Ring Topology** | N/A (Low-Z driven WE) | Passive (`NT3` tied to `/Vbias`) | Active (`U5B` `OPA2192` unity buffer, $0.03\,\Omega$) |
| **Full-Scale Signal Span** | $+2.4576\text{ V}$ to $-2.4900\text{ V}$ | $\pm 204.8\text{ pA}$ (at Stage 2 Out) | $\pm 20.48\,\mu\text{A}$ (at $V_{\text{bias}} = 0\text{ V}$) |
| **Ideal LSB Step Size** | $-1.20\text{ mV}$ (Coarse)<br>$-12.0\,\mu\text{V}$ (Fine Vernier) | $6.25\text{ fA/LSB}$ (16-bit ideal)<br>$8.13\text{ fA/LSB}$ (with `U17` $R_{\text{on}}$) | $0.625\text{ nA/LSB}$ (16-bit ideal)<br>$0.875\text{ nA/LSB}$ (with `U17` $R_{\text{on}} + R_{32}$) |

---

## 6. Balancing $V_{\text{PORE}}$ and Dual-TIA Ranges ($5\text{ nm} \to 200\,\mu\text{m}$, Conductive Ionic to Non-Ionic Liquids)

### 6.1 Why a Fixed Bias Voltage Cannot Span 8 Orders of Magnitude of Pore Conductance
Across apertures from $d_p = 5\text{ nm}$ ($L = 20\text{ nm}$) to $d_p = 200\,\mu\text{m}$ ($L = 50\,\mu\text{m}$) and liquids ranging from hypertonic $3.0\text{ M NaCl}$ ($\sigma = 20.0\text{ S/m}$) down to ultrapure DI water / non-ionic solvents ($\sigma = 5.5 \times 10^{-6}\text{ S/m}$), total pore resistance $R_{\text{pore}}$ spans more than **8 orders of magnitude** ($330\,\Omega$ to $> 1\text{ T}\Omega$):
$$R_{\text{pore}} = \frac{4 L}{\pi \sigma_{\text{lumen}} d_p^2} + \frac{1}{\sigma_{\text{access}} d_p}, \qquad \sigma_{\text{lumen}} = \sigma_{\text{bulk}} + \frac{4 |\Sigma_{\text{wall}}| \mu_{\text{counter}}}{d_p}$$

To keep the conditioned TIA output centered at $V_{\text{mux}} \approx -1.20\text{ V}$ ($58.6\%$ of the $\pm 2.048\text{ V}$ ADC full scale, leaving $> 41\%$ headroom for translocation spikes and baseline drift) without saturating either stage, **the `MR1` composite DAC ($V_{\text{PORE}}$) and the `Amplifier` dual-route multiplexer (`ROUTE_SEL`) operate as a coupled 2D gain-and-excitation balancer**:

1. **High-Conductance Corner ($200\,\mu\text{m}$ Pore in $3.0\text{ M NaCl}$, $R_{\text{pore}} = 329.6\,\Omega$):**
   - A standard $100\text{ mV}$ bias would drive $I_{\text{pore}} = 303.4\,\mu\text{A}$, saturating even Route 2 ($\pm 20.48\,\mu\text{A}$ limit).
   - **Balancing Action:** Select **Route 2 (`ROUTE_SEL = 1`, $-100\text{ k}\Omega$)** and use the `MR1` $100:1$ fine vernier DAC (`U9B`, $12.0\,\mu\text{V/LSB}$) to set $V_{\text{PORE}} = \mathbf{3.96\text{ mV}}$ (`D_A = 2044, D_B = 70` — resolved across $330$ discrete vernier steps!). This yields $I_{\text{pore}} = 12.02\,\mu\text{A}$, $V_{\text{Route2\_OUT}} = -1.202\text{ V}$, and $\text{SNR} = \mathbf{99.2\text{ dB}}$ with zero saturation.
2. **Sub-5 nm Nanopore Corner in Conductive Salt ($5\text{ nm}$ Pore in $1.0\text{ M KCl}$, $R_{\text{pore}} = 106.0\text{ M}\Omega$):**
   - Because Route 1 (`U2` `LMP7721` $1\text{ G}\Omega$ + `U16` `LTC6268` $10.0\times$ post-gain) has a net transimpedance of $-10.0\text{ G}\Omega$, its Stage 2 linear input ceiling is $\pm \mathbf{204.8\text{ pA}}$ (whereas Stage 1 `U2` alone allows $\pm 2.048\text{ nA}$).
   - Applying $180\text{ mV}$ on Route 1 produces $I_{\text{pore}} = 1.70\text{ nA}$, which is unsaturated at `U2` ($-1.70\text{ V}$) **but saturates `U16` Stage 2** ($-17.0\text{ V}$ ideal, clipped at $-2.49\text{ V}$ `VSSA`).
   - **Balancing Action:**
     - **Low-Bias Precision Mode (`ROUTE_SEL = 0`):** Set $V_{\text{PORE}} = \mathbf{12.59\text{ mV}}$ (`D_A = 2037, D_B = 51`) to place $I_{\text{pore}} = 120.0\text{ pA}$ at $V_{\text{Route1\_OUT}} = -1.200\text{ V}$ ($\text{SNR} = \mathbf{70.4\text{ dB}}$).
     - **High-Field Electrophoretic Capture Mode ($V_{\text{PORE}} = 180\text{ mV} - 2.45\text{ V}$):** Either switch to **Route 2 (`ROUTE_SEL = 1`)** at high bias ($I_{\text{pore}} = 20 - 40\text{ nA}$), or populate `U16` for unity gain ($R_8 = 1\text{ k}\Omega, R_5 = 100\,\Omega, R_3 = 100\,\Omega$) when full $\pm 2.048\text{ nA}$ swing on Route 1 at $180\text{ mV}$ is desired.
3. **Non-Ionic & Ultrapure Liquid Corner ($5\text{ nm} \to 200\,\mu\text{m}$ Pores in Polar Organic $\sigma = 10^{-4}\text{ S/m}$ & DI Water $\sigma = 5.5\times 10^{-6}\text{ S/m}$):**
   - **Crucial Cross-Route Insight:** In non-ionic liquids and DI water, even a **$100\,\mu\text{m}$ or $200\,\mu\text{m}$ micropore** has a resistance of $65\text{ M}\Omega - 2.6\text{ G}\Omega$ (producing only $50 - 200\text{ pA}$), which would be buried in the noise floor of Route 2 ($100\text{ k}\Omega$).
   - **Balancing Action:** The firmware selects **Route 1 (`ROUTE_SEL = 0`, $-10.0\text{ G}\Omega$ femtoampere TIA)** even for $100 - 200\,\mu\text{m}$ micropores when operating in non-ionic or DI liquids, while scaling $V_{\text{PORE}}$ up to $+1.39\text{ V}$ for $5\text{ nm}$ pores in non-ionic media!

### 6.2 Route Selection & $V_{\text{PORE}}$ Balancing Law
Given measured or estimated pore resistance $R_{\text{pore}}$ and target TIA output magnitude $V_{\text{target}} = 1.20\text{ V}$:
1. Compute the required Route 1 excitation voltage for $I_{\text{target,1}} = \frac{1.20\text{ V}}{10.0\text{ G}\Omega} = 120.0\text{ pA}$:
   $$V_{\text{PORE,R1}}^* = (120.0\text{ pA}) \cdot R_{\text{pore}}$$
2. **Route Decision Criterion:**
   - **If $V_{\text{PORE,R1}}^* \ge 1.20\text{ mV}$ ($R_{\text{pore}} \ge 10.0\text{ M}\Omega$):** Select **Route 1 (`ROUTE_SEL = 0`, $-10.0\text{ G}\Omega$)** and set:
     $$V_{\text{PORE}} = \min\left(2.4576\text{ V},\; V_{\text{PORE,R1}}^*\right)$$
   - **If $V_{\text{PORE,R1}}^* < 1.20\text{ mV}$ ($R_{\text{pore}} < 10.0\text{ M}\Omega$):** Select **Route 2 (`ROUTE_SEL = 1`, $-100.0\text{ k}\Omega$)** and set:
     $$V_{\text{PORE}} = \min\left(2.4576\text{ V},\; (12.0\,\mu\text{A}) \cdot R_{\text{pore}}\right)$$

### 6.3 Complete 42-Point Broad-Range Validation Matrix ($5\text{ nm} \to 200\,\mu\text{m}$, 6 Liquid Classes)

| Liquid Class ($\sigma_{\text{bulk}}$, $\Sigma_{\text{wall}}$) | Pore Size ($d_p$, $L$) | Total $R_{\text{pore}}$ | Active Route (`ROUTE_SEL`) | Balanced $V_{\text{PORE}}$ (`D_A`, `D_B`) | Pore Current $I_{\text{pore}}$ | Mux Output $V_{\text{mux}}$ | ADC Code (16-Bit) | SNR (dB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **3.0M NaCl** ($20\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $57.64\text{ M}\Omega$ | **Route 1** (`0`) | `6.92 mV` (`2042`, `23`) | $120.1\text{ pA}$ | `-1.201 V` | `14769` | `70.4 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $5.63\text{ M}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $436.3\text{ nA}$ | `-0.044 V` | `499` | `70.4 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $313.5\text{ k}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $7.84\,\mu\text{A}$ | `-0.784 V` | `8960` | `95.5 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $113.6\text{ k}\Omega$ | **Route 2** (`1`) | `1363.62 mV` (`911`, `65`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13716` | `99.2 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $11.37\text{ k}\Omega$ | **Route 2** (`1`) | `136.39 mV` (`1934`, `34`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13716` | `99.2 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $818.3\,\Omega$ | **Route 2** (`1`) | `9.82 mV` (`2039`, `82`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13712` | `99.2 dB` | PASS |
| **3.0M NaCl** ($20\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $329.6\,\Omega$ | **Route 2** (`1`) | `3.96 mV` (`2044`, `70`) | $12.02\,\mu\text{A}$ | `-1.202 V` | `13734` | `99.2 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $104.9\text{ M}\Omega$ | **Route 1** (`0`) | `12.59 mV` (`2037`, `51`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $10.58\text{ M}\Omega$ | **Route 1** (`0`) | `1.27 mV` (`2046`, `94`) | $120.2\text{ pA}$ | `-1.202 V` | `14792` | `70.4 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $597.0\text{ k}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $4.12\,\mu\text{A}$ | `-0.412 V` | `4705` | `89.9 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $216.4\text{ k}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $11.36\,\mu\text{A}$ | `-1.136 V` | `12979` | `98.7 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $21.65\text{ k}\Omega$ | **Route 2** (`1`) | `259.79 mV` (`1831`, `51`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13715` | `99.2 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $1.56\text{ k}\Omega$ | **Route 2** (`1`) | `18.71 mV` (`2032`, `41`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13718` | `99.2 dB` | PASS |
| **1.0M KCl** ($10.5\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $627.8\,\Omega$ | **Route 2** (`1`) | `7.54 mV` (`2041`, `72`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13721` | `99.2 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $462.1\text{ M}\Omega$ | **Route 1** (`0`) | `55.46 mV` (`2001`, `78`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $64.06\text{ M}\Omega$ | **Route 1** (`0`) | `7.69 mV` (`2041`, `59`) | $120.1\text{ pA}$ | `-1.201 V` | `14772` | `70.4 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $4.05\text{ M}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $606.1\text{ nA}$ | `-0.061 V` | `693` | `73.3 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $1.47\text{ M}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $1.67\,\mu\text{A}$ | `-0.167 V` | `1905` | `82.0 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $147.6\text{ k}\Omega$ | **Route 2** (`1`) | `1770.80 mV` (`572`, `33`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13716` | `99.2 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $10.63\text{ k}\Omega$ | **Route 2** (`1`) | `127.52 mV` (`1941`, `73`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13716` | `99.2 dB` | PASS |
| **0.154M NaCl** ($1.54\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $4.28\text{ k}\Omega$ | **Route 2** (`1`) | `51.36 mV` (`2005`, `20`) | $12.00\,\mu\text{A}$ | `-1.200 V` | `13715` | `99.2 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $1.52\text{ G}\Omega$ | **Route 1** (`0`) | `182.34 mV` (`1896`, `5`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $648.0\text{ M}\Omega$ | **Route 1** (`0`) | `77.76 mV` (`1983`, `20`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $222.8\text{ M}\Omega$ | **Route 1** (`0`) | `26.74 mV` (`2025`, `72`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $122.9\text{ M}\Omega$ | **Route 1** (`0`) | `14.75 mV` (`2035`, `71`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $14.80\text{ M}\Omega$ | **Route 1** (`0`) | `1.78 mV` (`2046`, `52`) | $120.0\text{ pA}$ | `-1.200 V` | `14761` | `70.4 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $1.09\text{ M}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $2.26\,\mu\text{A}$ | `-0.226 V` | `2583` | `84.6 dB` | PASS |
| **1.0mM KCl** ($0.015\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $438.9\text{ k}\Omega$ | **Route 2** (`1`) | `2457.60 mV` (`0`, `0`) | $5.60\,\mu\text{A}$ | `-0.560 V` | `6400` | `92.5 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $11.62\text{ G}\Omega$ | **Route 1** (`0`) | `1394.78 mV` (`885`, `68`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $5.34\text{ G}\Omega$ | **Route 1** (`0`) | `640.96 mV` (`1513`, `87`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $3.48\text{ G}\Omega$ | **Route 1** (`0`) | `418.00 mV` (`1699`, `67`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $4.26\text{ G}\Omega$ | **Route 1** (`0`) | `511.76 mV` (`1621`, `53`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $1.56\text{ G}\Omega$ | **Route 1** (`0`) | `186.89 mV` (`1892`, `26`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $157.0\text{ M}\Omega$ | **Route 1** (`0`) | `18.84 mV` (`2032`, `30`) | $120.0\text{ pA}$ | `-1.200 V` | `14765` | `70.4 dB` | PASS |
| **Polar Organic** ($10^{-4}\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $64.68\text{ M}\Omega$ | **Route 1** (`0`) | `7.76 mV` (`2041`, `53`) | $120.0\text{ pA}$ | `-1.200 V` | `14769` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $5\text{ nm}$ ($20\text{ nm}$) | $1.55\text{ G}\Omega$ | **Route 1** (`0`) | `186.17 mV` (`1892`, `86`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $20\text{ nm}$ ($20\text{ nm}$) | $715.9\text{ M}\Omega$ | **Route 1** (`0`) | `85.91 mV` (`1976`, `41`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $200\text{ nm}$ ($40\text{ nm}$) | $492.9\text{ M}\Omega$ | **Route 1** (`0`) | `59.15 mV` (`1998`, `71`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $1\,\mu\text{m}$ ($1\,\mu\text{m}$) | $714.5\text{ M}\Omega$ | **Route 1** (`0`) | `85.74 mV` (`1976`, `55`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $10\,\mu\text{m}$ ($10\,\mu\text{m}$) | $702.3\text{ M}\Omega$ | **Route 1** (`0`) | `84.28 mV` (`1977`, `77`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $100\,\mu\text{m}$ ($50\,\mu\text{m}$) | $476.9\text{ M}\Omega$ | **Route 1** (`0`) | `57.23 mV` (`2000`, `31`) | $120.0\text{ pA}$ | `-1.200 V` | `14764` | `70.4 dB` | PASS |
| **DI Water** ($5.5\times 10^{-6}\text{ S/m}$) | $200\,\mu\text{m}$ ($50\,\mu\text{m}$) | $351.5\text{ M}\Omega$ | **Route 1** (`0`) | `42.18 mV` (`2012`, `85`) | $120.0\text{ pA}$ | `-1.200 V` | `14763` | `70.4 dB` | PASS |

---

## 7. Verification & Simulation Commands

Run the standalone op-amp signal conditioning simulation and unit tests with:

```bash
# Run the standalone op-amp signal conditioning & 42-point broad-range balancing summary
.venv/bin/python3 simulations/opamp_signal_conditioning.py

# Run the full physics and op-amp unit test suite (22 tests)
.venv/bin/python3 -m unittest tests/test_physics_and_simulations.py -v
```
