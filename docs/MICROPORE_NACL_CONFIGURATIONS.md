# MR1 Nanopore Reader — Micropore & Salt Aperture Configuration Matrix
## Operational Configurations for 10 μm and 100 μm Pores in NaCl / Salt Solutions

**Author:** Molecular Reality Corp / Antigravity  
**Date:** October 2026  
**Status:** Validated against Built-in Multiphysics Simulations  
**Simulation Sources:**
- `simulations/nanopore_electrokinetics.py`
- `simulations/four_electrode_cell_simulation.py`
- `simulations/fluidic_dynamics_nanopore.py`
- `simulations/pore_dac_dynamics.py`

---

## 1. Executive Summary & Physics Architecture

This document establishes the operational parameters and working configuration table for scaling the MR1 platform from nanoscale apertures (2 - 200 nm) to micro-scale apertures (10 μm and 100 μm) in salt electrolytes (specifically **NaCl** at physiological 0.154M, standard 1.0M, and high-ionic strength 3.0M, alongside standard 1.0M KCl).

### Core Physics Governing Micropores

1. **Access Resistance ($R_\text{access}$) vs Lumen Resistance ($R_\text{lumen}$):**
   $$\begin{aligned}
   R_\text{lumen} &= \frac{4 \rho L}{\pi D^2} = \frac{4 L}{\pi \sigma D^2} \\
   R_\text{access} &= \frac{\rho}{D} = \frac{1}{\sigma D} \quad \text{(summed over both cis and trans hemispheres)} \\
   R_\text{total} &= R_\text{lumen} + R_\text{access} = \frac{1}{\sigma D} \left( \frac{4 L}{\pi D} + 1 \right)
   \end{aligned}$$
   - In micro-scale apertures with low aspect ratios ($L \le D$), **access resistance ($R_\text{access}$) dominates or equals lumen resistance**. For a 100 μm aperture in a 10 μm thick membrane, access resistance accounts for **88.7%** of the entire pore resistance.

2. **Conductivity & Solution Resistivity at 25 °C:**
   - **1.0M NaCl:** $\sigma = 8.50\text{ S/m}$ ($\rho = 0.1176\,\Omega\cdot\text{m}$)
   - **0.154M NaCl (Physiological PBS):** $\sigma = 1.54\text{ S/m}$ ($\rho = 0.6494\,\Omega\cdot\text{m}$)
   - **3.0M NaCl:** $\sigma = 20.00\text{ S/m}$ ($\rho = 0.0500\,\Omega\cdot\text{m}$)
   - **1.0M KCl:** $\sigma = 10.50\text{ S/m}$ ($\rho = 0.0952\,\Omega\cdot\text{m}$)

3. **Front-End Amplifier Matching:**
   - **Path 1 (LMP7721, $R_{f1} = 1\text{ G}\Omega$, $V_\text{FS} = \pm 2.048\text{ V}$):**
     - Dynamic limit: $I_\text{max} = \pm 2.048\text{ nA}$.
     - **Result:** **Completely saturated** for all 10 μm and 100 μm pores (which draw $0.2\,\mu\text{A}$ to $> 150\,\mu\text{A}$, over $100\times$ to $75{,}000\times$ above Path 1 saturation).
   - **Path 2 (OPA192 Wideband, $R_{f2} = 100\text{ k}\Omega$, $C_{f2} = 15\text{ pF}$, $f_{-3\text{dB}} \approx 106.1\text{ kHz}$):**
     - Dynamic limit: $I_\text{max} = \pm 20.48\,\mu\text{A}$.
     - **For 10 μm pores:** Operates **completely unsaturated** across the full operating range ($V_\text{bias} \le 200\text{ mV}$ in 1M NaCl yields $I_0 \le 15.1\,\mu\text{A}$ with $\ge 26\%$ headroom).
     - **For 100 μm pores:** Operates unsaturated at low bias ($V_\text{bias} \le 20\text{ mV}$ yields $I_0 \le 15.1\,\mu\text{A}$ with $26.4\%$ headroom). Saturates if $V_\text{bias} \ge 25\text{ mV}$.
   - **Custom Hardware Gain Options for Large Pores / High Bias:**
     - **Option A ($R_f = 10\text{ k}\Omega$, $C_f = 150\text{ pF}$, $f_{-3\text{dB}} = 106\text{ kHz}$):**
       - Dynamic limit: $I_\text{max} = \pm 204.8\,\mu\text{A}$.
       - Allows 100 μm apertures to operate up to 200 mV bias without saturation.
     - **Option B ($R_f = 1\text{ k}\Omega$, $C_f = 1.5\text{ nF}$, $f_{-3\text{dB}} = 106\text{ kHz}$):**
       - Dynamic limit: $I_\text{max} = \pm 2.048\text{ mA}$.
       - Suitable for massive hypertonic apertures (3M NaCl at high voltages).

4. **Kelvin 4-Electrode vs 2-Electrode Remote Configuration:**
   - In 2-electrode mode, remote channel uncompensated resistance ($R_u \approx 8.47\text{ k}\Omega$) plus electrode interfacial charge transfer ($2 R_{ct} = 300\,\Omega$) creates a series parasitic resistance of $\approx 8.77\text{ k}\Omega$.
   - **For 10 μm pores ($R_\text{pore} \approx 13 - 27\text{ k}\Omega$):** 2-electrode mode introduces a **25% - 40% voltage loss** in solution before reaching the pore!
   - **For 100 μm pores ($R_\text{pore} \approx 1.2 - 1.9\text{ k}\Omega$):** 2-electrode mode loses **82% - 88% of the applied voltage** across the channels and electrodes. The pore only sees 12% - 18% of the commanded voltage!
   - **Conclusion:** The **4-electrode concentric Kelvin architecture** (with $R_{u,\text{concentric}} < 10\,\Omega$) is **essential**, ensuring > 99.2% of the commanded voltage drops across the pore.

---

## 2. Master Working Configuration Table

The table below provides simulated configurations generated directly by `simulations/micropore_configuration_table.py` using project multiphysics models across 96 discrete states.

| Pore $D$ | Length $L$ | Electrolyte | $V_{\text{bias}}$ | $R_{\text{total}}$ | $G_{\text{pore}}$ | $I_0$ | Path 2 ($100\text{k}\Omega$) | Alt $R_f$ ($10\text{k}\Omega$) | 2-Elec Error | 4-Elec Error | DAC Code |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 13.26 $\text{k}\Omega$ | 75.4 $\mu\text{S}$ | 0.75 $\mu\text{A}$ | 0.075V (OK, 96% HR) | 0.008V (OK) | 39.8% | 0.07% | 20 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 13.26 $\text{k}\Omega$ | 75.4 $\mu\text{S}$ | 1.51 $\mu\text{A}$ | 0.151V (OK, 93% HR) | 0.015V (OK) | 39.8% | 0.07% | 40 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 13.26 $\text{k}\Omega$ | 75.4 $\mu\text{S}$ | 3.77 $\mu\text{A}$ | 0.377V (OK, 82% HR) | 0.038V (OK) | 39.8% | 0.07% | 100 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 13.26 $\text{k}\Omega$ | 75.4 $\mu\text{S}$ | 7.54 $\mu\text{A}$ | 0.754V (OK, 63% HR) | 0.075V (OK) | 39.8% | 0.07% | 200 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 26.74 $\text{k}\Omega$ | 37.4 $\mu\text{S}$ | 0.37 $\mu\text{A}$ | 0.037V (OK, 98% HR) | 0.004V (OK) | 24.7% | 0.04% | 20 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 26.74 $\text{k}\Omega$ | 37.4 $\mu\text{S}$ | 0.75 $\mu\text{A}$ | 0.075V (OK, 96% HR) | 0.007V (OK) | 24.7% | 0.04% | 40 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 26.74 $\text{k}\Omega$ | 37.4 $\mu\text{S}$ | 1.87 $\mu\text{A}$ | 0.187V (OK, 91% HR) | 0.019V (OK) | 24.7% | 0.04% | 100 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 26.74 $\text{k}\Omega$ | 37.4 $\mu\text{S}$ | 3.74 $\mu\text{A}$ | 0.374V (OK, 82% HR) | 0.037V (OK) | 24.7% | 0.04% | 200 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 86.66 $\text{k}\Omega$ | 11.5 $\mu\text{S}$ | 0.12 $\mu\text{A}$ | 0.012V (OK, 99% HR) | 0.001V (OK) | 9.2% | 0.01% | 20 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 86.66 $\text{k}\Omega$ | 11.5 $\mu\text{S}$ | 0.23 $\mu\text{A}$ | 0.023V (OK, 99% HR) | 0.002V (OK) | 9.2% | 0.01% | 40 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 86.66 $\text{k}\Omega$ | 11.5 $\mu\text{S}$ | 0.58 $\mu\text{A}$ | 0.058V (OK, 97% HR) | 0.006V (OK) | 9.2% | 0.01% | 100 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 86.66 $\text{k}\Omega$ | 11.5 $\mu\text{S}$ | 1.15 $\mu\text{A}$ | 0.115V (OK, 94% HR) | 0.012V (OK) | 9.2% | 0.01% | 200 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 73.20 $\text{k}\Omega$ | 13.7 $\mu\text{S}$ | 0.14 $\mu\text{A}$ | 0.014V (OK, 99% HR) | 0.001V (OK) | 39.1% | 0.07% | 20 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 73.20 $\text{k}\Omega$ | 13.7 $\mu\text{S}$ | 0.27 $\mu\text{A}$ | 0.027V (OK, 99% HR) | 0.003V (OK) | 39.1% | 0.07% | 40 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 73.20 $\text{k}\Omega$ | 13.7 $\mu\text{S}$ | 0.68 $\mu\text{A}$ | 0.068V (OK, 97% HR) | 0.007V (OK) | 39.1% | 0.07% | 100 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 73.20 $\text{k}\Omega$ | 13.7 $\mu\text{S}$ | 1.37 $\mu\text{A}$ | 0.137V (OK, 93% HR) | 0.014V (OK) | 39.1% | 0.07% | 200 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 147.61 $\text{k}\Omega$ | 6.8 $\mu\text{S}$ | 0.07 $\mu\text{A}$ | 0.007V (OK, 100% HR) | 0.001V (OK) | 24.2% | 0.04% | 20 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 147.61 $\text{k}\Omega$ | 6.8 $\mu\text{S}$ | 0.14 $\mu\text{A}$ | 0.014V (OK, 99% HR) | 0.001V (OK) | 24.2% | 0.04% | 40 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 147.61 $\text{k}\Omega$ | 6.8 $\mu\text{S}$ | 0.34 $\mu\text{A}$ | 0.034V (OK, 98% HR) | 0.003V (OK) | 24.2% | 0.04% | 100 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 147.61 $\text{k}\Omega$ | 6.8 $\mu\text{S}$ | 0.68 $\mu\text{A}$ | 0.068V (OK, 97% HR) | 0.007V (OK) | 24.2% | 0.04% | 200 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 478.32 $\text{k}\Omega$ | 2.1 $\mu\text{S}$ | 0.02 $\mu\text{A}$ | 0.002V (OK, 100% HR) | 0.000V (OK) | 9.0% | 0.01% | 20 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 478.32 $\text{k}\Omega$ | 2.1 $\mu\text{S}$ | 0.04 $\mu\text{A}$ | 0.004V (OK, 100% HR) | 0.000V (OK) | 9.0% | 0.01% | 40 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 478.32 $\text{k}\Omega$ | 2.1 $\mu\text{S}$ | 0.10 $\mu\text{A}$ | 0.010V (OK, 99% HR) | 0.001V (OK) | 9.0% | 0.01% | 100 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 478.32 $\text{k}\Omega$ | 2.1 $\mu\text{S}$ | 0.21 $\mu\text{A}$ | 0.021V (OK, 99% HR) | 0.002V (OK) | 9.0% | 0.01% | 200 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 5.64 $\text{k}\Omega$ | 177.4 $\mu\text{S}$ | 1.77 $\mu\text{A}$ | 0.177V (OK, 91% HR) | 0.018V (OK) | 40.9% | 0.07% | 20 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 5.64 $\text{k}\Omega$ | 177.4 $\mu\text{S}$ | 3.55 $\mu\text{A}$ | 0.355V (OK, 83% HR) | 0.035V (OK) | 40.9% | 0.07% | 40 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 5.64 $\text{k}\Omega$ | 177.4 $\mu\text{S}$ | 8.87 $\mu\text{A}$ | 0.887V (OK, 57% HR) | 0.089V (OK) | 40.9% | 0.07% | 100 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 5.64 $\text{k}\Omega$ | 177.4 $\mu\text{S}$ | 17.74 $\mu\text{A}$ | 1.774V (OK, 13% HR) | 0.177V (OK) | 40.9% | 0.07% | 200 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 11.37 $\text{k}\Omega$ | 88.0 $\mu\text{S}$ | 0.88 $\mu\text{A}$ | 0.088V (OK, 96% HR) | 0.009V (OK) | 25.5% | 0.04% | 20 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 11.37 $\text{k}\Omega$ | 88.0 $\mu\text{S}$ | 1.76 $\mu\text{A}$ | 0.176V (OK, 91% HR) | 0.018V (OK) | 25.5% | 0.04% | 40 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 11.37 $\text{k}\Omega$ | 88.0 $\mu\text{S}$ | 4.40 $\mu\text{A}$ | 0.440V (OK, 79% HR) | 0.044V (OK) | 25.5% | 0.04% | 100 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 11.37 $\text{k}\Omega$ | 88.0 $\mu\text{S}$ | 8.80 $\mu\text{A}$ | 0.880V (OK, 57% HR) | 0.088V (OK) | 25.5% | 0.04% | 200 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 36.83 $\text{k}\Omega$ | 27.2 $\mu\text{S}$ | 0.27 $\mu\text{A}$ | 0.027V (OK, 99% HR) | 0.003V (OK) | 9.6% | 0.01% | 20 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 36.83 $\text{k}\Omega$ | 27.2 $\mu\text{S}$ | 0.54 $\mu\text{A}$ | 0.054V (OK, 97% HR) | 0.005V (OK) | 9.6% | 0.01% | 40 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 36.83 $\text{k}\Omega$ | 27.2 $\mu\text{S}$ | 1.36 $\mu\text{A}$ | 0.136V (OK, 93% HR) | 0.014V (OK) | 9.6% | 0.01% | 100 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 36.83 $\text{k}\Omega$ | 27.2 $\mu\text{S}$ | 2.72 $\mu\text{A}$ | 0.272V (OK, 87% HR) | 0.027V (OK) | 9.6% | 0.01% | 200 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 10 mV | 10.74 $\text{k}\Omega$ | 93.1 $\mu\text{S}$ | 0.93 $\mu\text{A}$ | 0.093V (OK, 95% HR) | 0.009V (OK) | 40.0% | 0.07% | 20 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 20 mV | 10.74 $\text{k}\Omega$ | 93.1 $\mu\text{S}$ | 1.86 $\mu\text{A}$ | 0.186V (OK, 91% HR) | 0.019V (OK) | 40.0% | 0.07% | 40 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 50 mV | 10.74 $\text{k}\Omega$ | 93.1 $\mu\text{S}$ | 4.66 $\mu\text{A}$ | 0.466V (OK, 77% HR) | 0.047V (OK) | 40.0% | 0.07% | 100 |
| 10 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 100 mV | 10.74 $\text{k}\Omega$ | 93.1 $\mu\text{S}$ | 9.31 $\mu\text{A}$ | 0.931V (OK, 55% HR) | 0.093V (OK) | 40.0% | 0.07% | 200 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 10 mV | 21.65 $\text{k}\Omega$ | 46.2 $\mu\text{S}$ | 0.46 $\mu\text{A}$ | 0.046V (OK, 98% HR) | 0.005V (OK) | 24.8% | 0.04% | 20 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 20 mV | 21.65 $\text{k}\Omega$ | 46.2 $\mu\text{S}$ | 0.92 $\mu\text{A}$ | 0.092V (OK, 95% HR) | 0.009V (OK) | 24.8% | 0.04% | 40 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 50 mV | 21.65 $\text{k}\Omega$ | 46.2 $\mu\text{S}$ | 2.31 $\mu\text{A}$ | 0.231V (OK, 89% HR) | 0.023V (OK) | 24.8% | 0.04% | 100 |
| 10 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 100 mV | 21.65 $\text{k}\Omega$ | 46.2 $\mu\text{S}$ | 4.62 $\mu\text{A}$ | 0.462V (OK, 77% HR) | 0.046V (OK) | 24.8% | 0.04% | 200 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 10 mV | 70.15 $\text{k}\Omega$ | 14.3 $\mu\text{S}$ | 0.14 $\mu\text{A}$ | 0.014V (OK, 99% HR) | 0.001V (OK) | 9.3% | 0.01% | 20 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 20 mV | 70.15 $\text{k}\Omega$ | 14.3 $\mu\text{S}$ | 0.29 $\mu\text{A}$ | 0.029V (OK, 99% HR) | 0.003V (OK) | 9.3% | 0.01% | 40 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 50 mV | 70.15 $\text{k}\Omega$ | 14.3 $\mu\text{S}$ | 0.71 $\mu\text{A}$ | 0.071V (OK, 97% HR) | 0.007V (OK) | 9.3% | 0.01% | 100 |
| 10 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 100 mV | 70.15 $\text{k}\Omega$ | 14.3 $\mu\text{S}$ | 1.43 $\mu\text{A}$ | 0.143V (OK, 93% HR) | 0.014V (OK) | 9.3% | 0.01% | 200 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 1.19 $\text{k}\Omega$ | 839.3 $\mu\text{S}$ | 8.39 $\mu\text{A}$ | 0.839V (OK, 59% HR) | 0.084V (OK) | 88.0% | 0.81% | 20 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 1.19 $\text{k}\Omega$ | 839.3 $\mu\text{S}$ | 16.79 $\mu\text{A}$ | 1.679V (OK, 18% HR) | 0.168V (OK) | 88.0% | 0.81% | 40 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 1.19 $\text{k}\Omega$ | 839.3 $\mu\text{S}$ | 41.97 $\mu\text{A}$ | **SAT** (4.20V) | 0.420V (OK) | 88.0% | 0.81% | 100 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 1.19 $\text{k}\Omega$ | 839.3 $\mu\text{S}$ | 83.93 $\mu\text{A}$ | **SAT** (8.39V) | 0.839V (OK) | 88.0% | 0.81% | 200 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 1.33 $\text{k}\Omega$ | 754.0 $\mu\text{S}$ | 7.54 $\mu\text{A}$ | 0.754V (OK, 63% HR) | 0.075V (OK) | 86.9% | 0.73% | 20 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 1.33 $\text{k}\Omega$ | 754.0 $\mu\text{S}$ | 15.08 $\mu\text{A}$ | 1.508V (OK, 26% HR) | 0.151V (OK) | 86.9% | 0.73% | 40 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 1.33 $\text{k}\Omega$ | 754.0 $\mu\text{S}$ | 37.70 $\mu\text{A}$ | **SAT** (3.77V) | 0.377V (OK) | 86.9% | 0.73% | 100 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 1.33 $\text{k}\Omega$ | 754.0 $\mu\text{S}$ | 75.40 $\mu\text{A}$ | **SAT** (7.54V) | 0.754V (OK) | 86.9% | 0.73% | 200 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 10 mV | 1.93 $\text{k}\Omega$ | 519.4 $\mu\text{S}$ | 5.19 $\mu\text{A}$ | 0.519V (OK, 75% HR) | 0.052V (OK) | 82.0% | 0.50% | 20 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 20 mV | 1.93 $\text{k}\Omega$ | 519.4 $\mu\text{S}$ | 10.39 $\mu\text{A}$ | 1.039V (OK, 49% HR) | 0.104V (OK) | 82.0% | 0.50% | 40 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 50 mV | 1.93 $\text{k}\Omega$ | 519.4 $\mu\text{S}$ | 25.97 $\mu\text{A}$ | **SAT** (2.60V) | 0.260V (OK) | 82.0% | 0.50% | 100 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M NaCl | 100 mV | 1.93 $\text{k}\Omega$ | 519.4 $\mu\text{S}$ | 51.94 $\mu\text{A}$ | **SAT** (5.19V) | 0.519V (OK) | 82.0% | 0.50% | 200 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 6.58 $\text{k}\Omega$ | 152.1 $\mu\text{S}$ | 1.52 $\mu\text{A}$ | 0.152V (OK, 93% HR) | 0.015V (OK) | 87.7% | 0.81% | 20 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 6.58 $\text{k}\Omega$ | 152.1 $\mu\text{S}$ | 3.04 $\mu\text{A}$ | 0.304V (OK, 85% HR) | 0.030V (OK) | 87.7% | 0.81% | 40 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 6.58 $\text{k}\Omega$ | 152.1 $\mu\text{S}$ | 7.60 $\mu\text{A}$ | 0.760V (OK, 63% HR) | 0.076V (OK) | 87.7% | 0.81% | 100 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 6.58 $\text{k}\Omega$ | 152.1 $\mu\text{S}$ | 15.21 $\mu\text{A}$ | 1.521V (OK, 26% HR) | 0.152V (OK) | 87.7% | 0.81% | 200 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 7.32 $\text{k}\Omega$ | 136.6 $\mu\text{S}$ | 1.37 $\mu\text{A}$ | 0.137V (OK, 93% HR) | 0.014V (OK) | 86.5% | 0.73% | 20 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 7.32 $\text{k}\Omega$ | 136.6 $\mu\text{S}$ | 2.73 $\mu\text{A}$ | 0.273V (OK, 87% HR) | 0.027V (OK) | 86.5% | 0.73% | 40 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 7.32 $\text{k}\Omega$ | 136.6 $\mu\text{S}$ | 6.83 $\mu\text{A}$ | 0.683V (OK, 67% HR) | 0.068V (OK) | 86.5% | 0.73% | 100 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 7.32 $\text{k}\Omega$ | 136.6 $\mu\text{S}$ | 13.66 $\mu\text{A}$ | 1.366V (OK, 33% HR) | 0.137V (OK) | 86.5% | 0.73% | 200 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 10 mV | 10.63 $\text{k}\Omega$ | 94.1 $\mu\text{S}$ | 0.94 $\mu\text{A}$ | 0.094V (OK, 95% HR) | 0.009V (OK) | 81.6% | 0.50% | 20 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 20 mV | 10.63 $\text{k}\Omega$ | 94.1 $\mu\text{S}$ | 1.88 $\mu\text{A}$ | 0.188V (OK, 91% HR) | 0.019V (OK) | 81.6% | 0.50% | 40 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 50 mV | 10.63 $\text{k}\Omega$ | 94.1 $\mu\text{S}$ | 4.70 $\mu\text{A}$ | 0.470V (OK, 77% HR) | 0.047V (OK) | 81.6% | 0.50% | 100 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 0.154M NaCl | 100 mV | 10.63 $\text{k}\Omega$ | 94.1 $\mu\text{S}$ | 9.41 $\mu\text{A}$ | 0.941V (OK, 54% HR) | 0.094V (OK) | 81.6% | 0.50% | 200 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 0.51 $\text{k}\Omega$ | 1974.9 $\mu\text{S}$ | 19.75 $\mu\text{A}$ | 1.975V (OK, 4% HR) | 0.197V (OK) | 88.5% | 0.81% | 20 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 0.51 $\text{k}\Omega$ | 1974.9 $\mu\text{S}$ | 39.50 $\mu\text{A}$ | **SAT** (3.95V) | 0.395V (OK) | 88.5% | 0.81% | 40 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 0.51 $\text{k}\Omega$ | 1974.9 $\mu\text{S}$ | 98.74 $\mu\text{A}$ | **SAT** (9.87V) | 0.987V (OK) | 88.5% | 0.81% | 100 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 0.51 $\text{k}\Omega$ | 1974.9 $\mu\text{S}$ | 197.49 $\mu\text{A}$ | **SAT** (19.75V) | 1.975V (OK) | 88.5% | 0.81% | 200 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 0.56 $\text{k}\Omega$ | 1774.1 $\mu\text{S}$ | 17.74 $\mu\text{A}$ | 1.774V (OK, 13% HR) | 0.177V (OK) | 87.4% | 0.73% | 20 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 0.56 $\text{k}\Omega$ | 1774.1 $\mu\text{S}$ | 35.48 $\mu\text{A}$ | **SAT** (3.55V) | 0.355V (OK) | 87.4% | 0.73% | 40 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 0.56 $\text{k}\Omega$ | 1774.1 $\mu\text{S}$ | 88.71 $\mu\text{A}$ | **SAT** (8.87V) | 0.887V (OK) | 87.4% | 0.73% | 100 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 0.56 $\text{k}\Omega$ | 1774.1 $\mu\text{S}$ | 177.41 $\mu\text{A}$ | **SAT** (17.74V) | 1.774V (OK) | 87.4% | 0.73% | 200 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 10 mV | 0.82 $\text{k}\Omega$ | 1222.0 $\mu\text{S}$ | 12.22 $\mu\text{A}$ | 1.222V (OK, 40% HR) | 0.122V (OK) | 82.7% | 0.50% | 20 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 20 mV | 0.82 $\text{k}\Omega$ | 1222.0 $\mu\text{S}$ | 24.44 $\mu\text{A}$ | **SAT** (2.44V) | 0.244V (OK) | 82.7% | 0.50% | 40 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 50 mV | 0.82 $\text{k}\Omega$ | 1222.0 $\mu\text{S}$ | 61.10 $\mu\text{A}$ | **SAT** (6.11V) | 0.611V (OK) | 82.7% | 0.50% | 100 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 3.0M NaCl | 100 mV | 0.82 $\text{k}\Omega$ | 1222.0 $\mu\text{S}$ | 122.20 $\mu\text{A}$ | **SAT** (12.22V) | 1.222V (OK) | 82.7% | 0.50% | 200 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 10 mV | 0.96 $\text{k}\Omega$ | 1036.8 $\mu\text{S}$ | 10.37 $\mu\text{A}$ | 1.037V (OK, 49% HR) | 0.104V (OK) | 88.1% | 0.81% | 20 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 20 mV | 0.96 $\text{k}\Omega$ | 1036.8 $\mu\text{S}$ | 20.74 $\mu\text{A}$ | **SAT** (2.07V) | 0.207V (OK) | 88.1% | 0.81% | 40 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 50 mV | 0.96 $\text{k}\Omega$ | 1036.8 $\mu\text{S}$ | 51.84 $\mu\text{A}$ | **SAT** (5.18V) | 0.518V (OK) | 88.1% | 0.81% | 100 |
| 100 $\mu\text{m}$ | 1 $\mu\text{m}$ | 1.0M KCl | 100 mV | 0.96 $\text{k}\Omega$ | 1036.8 $\mu\text{S}$ | 103.68 $\mu\text{A}$ | **SAT** (10.37V) | 1.037V (OK) | 88.1% | 0.81% | 200 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 10 mV | 1.07 $\text{k}\Omega$ | 931.4 $\mu\text{S}$ | 9.31 $\mu\text{A}$ | 0.931V (OK, 55% HR) | 0.093V (OK) | 87.0% | 0.73% | 20 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 20 mV | 1.07 $\text{k}\Omega$ | 931.4 $\mu\text{S}$ | 18.63 $\mu\text{A}$ | 1.863V (OK, 9% HR) | 0.186V (OK) | 87.0% | 0.73% | 40 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 50 mV | 1.07 $\text{k}\Omega$ | 931.4 $\mu\text{S}$ | 46.57 $\mu\text{A}$ | **SAT** (4.66V) | 0.466V (OK) | 87.0% | 0.73% | 100 |
| 100 $\mu\text{m}$ | 10 $\mu\text{m}$ | 1.0M KCl | 100 mV | 1.07 $\text{k}\Omega$ | 931.4 $\mu\text{S}$ | 93.14 $\mu\text{A}$ | **SAT** (9.31V) | 0.931V (OK) | 87.0% | 0.73% | 200 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 10 mV | 1.56 $\text{k}\Omega$ | 641.6 $\mu\text{S}$ | 6.42 $\mu\text{A}$ | 0.642V (OK, 69% HR) | 0.064V (OK) | 82.1% | 0.50% | 20 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 20 mV | 1.56 $\text{k}\Omega$ | 641.6 $\mu\text{S}$ | 12.83 $\mu\text{A}$ | 1.283V (OK, 37% HR) | 0.128V (OK) | 82.1% | 0.50% | 40 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 50 mV | 1.56 $\text{k}\Omega$ | 641.6 $\mu\text{S}$ | 32.08 $\mu\text{A}$ | **SAT** (3.21V) | 0.321V (OK) | 82.1% | 0.50% | 100 |
| 100 $\mu\text{m}$ | 50 $\mu\text{m}$ | 1.0M KCl | 100 mV | 1.56 $\text{k}\Omega$ | 641.6 $\mu\text{S}$ | 64.16 $\mu\text{A}$ | **SAT** (6.42V) | 0.642V (OK) | 82.1% | 0.50% | 200 |

---

## 3. Operational Guidelines for 10 μm and 100 μm Salt Pores

### A. 10 μm Pore Operating Regimes

1. **Recommended Buffer:** 1.0M NaCl (or 0.154M physiological saline for live cell analysis).
2. **Bias Voltage Range:** 10 mV to 100 mV (20 mV typical).
   - At 20 mV in 1.0M NaCl ($L = 10\,\mu\text{m}$):
     - $R_\text{total} = 26.74\text{ k}\Omega$
     - $I_0 = 0.75\,\mu\text{A}$ ($748\text{ nA}$)
     - Path 2 ($100\text{ k}\Omega$) Output: $0.075\text{ V}$ ($96.3\%$ headroom)
     - MCP4822 12-bit DAC Code (1x gain): **Code 40** (at $0.5\text{ mV/LSB}$)
3. **Bandwidth:** $\sim 106.1\text{ kHz}$ ($R_{f2} = 100\text{ k}\Omega$, $C_{f2} = 15\text{ pF}$).
4. **Coulter Sizing Capabilities:**
   - Detectable range: 1.0 μm to 8.0 μm particles / cells (e.g. erythrocytes, platelets, bacteria, microplastics).
   - A 2.0 μm particle produces $\Delta I \approx 3.4\text{ nA}$ ($0.45\%$ fractional blockade).
   - A 7.0 μm red blood cell produces $\Delta I \approx 140\text{ nA}$ ($18.8\%$ fractional blockade).

### B. 100 μm Pore Operating Regimes

1. **Recommended Buffer:** 1.0M NaCl (or 0.154M PBS).
2. **Hardware Configuration Selection:**
   - **Mode 1 (Standard Unmodified Hardware):** Use **Low-Bias Mode** ($V_\text{bias} = 10\text{ mV}$ to $20\text{ mV}$).
     - At 10 mV in 1.0M NaCl ($L = 10\,\mu\text{m}$):
       - $R_\text{total} = 1.33\text{ k}\Omega$
       - $I_0 = 7.54\,\mu\text{A}$
       - Path 2 ($100\text{ k}\Omega$) Output: $0.754\text{ V}$ ($63.2\%$ headroom)
       - MCP4822 DAC Code: **Code 20**
     - At 20 mV: $I_0 = 15.08\,\mu\text{A}$, Output: $1.508\text{ V}$ ($26.4\%$ headroom, Code 40).
   - **Mode 2 (High-Bias / High-Signal Hardware Rework):** Swap Path 2 feedback resistor to $R_f = 10\text{ k}\Omega$ (0805 / 0603 footprint) and $C_f = 150\text{ pF}$ (C0G/NP0 dielectric).
     - Full-scale current increases to $204.8\,\mu\text{A}$.
     - Allows 50 mV to 200 mV bias with clean headroom.
3. **Fluidic Balancing & Isobaric Requirement:**
   - Hydrodynamic resistance of a 100 μm pore drops to $R_\text{hyd} \approx 7 \times 10^9\text{ Pa}\cdot\text{s/m}^3$.
   - Any differential pressure across Cis and Trans chambers will cause severe convective leakage ($> 5\text{ mL/min}$ per 0.1 psi).
   - **Protocol:** Cis and Trans chambers must be primed and equalized before acquisition, or recorded under static bath / zero transmembrane differential pressure.
4. **Coulter Sizing Capabilities:**
   - Detectable range: 10 μm to 70 μm particles / cells (mammalian cell lines, cancer cells, microcarriers, pollen, organoids).
   - A 20 μm cell at 20 mV bias ($I_0 = 15.1\,\mu\text{A}$) yields $\Delta I \approx 123\text{ nA}$ ($0.82\%$ blockade).
   - A 50 μm bead yields $\Delta I \approx 1.92\,\mu\text{A}$ ($12.7\%$ blockade).

---

## 4. Verification & Reproduction

To reproduce these simulation numbers or recalculate with custom electrolyte concentrations, run:

```bash
python3 simulations/micropore_configuration_table.py
```

All calculations are covered under unit test suite `tests/test_physics_and_simulations.py`.
