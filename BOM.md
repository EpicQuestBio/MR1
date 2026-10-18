# Bill of Materials (BOM) — MR1 Nanopore Reader

This document provides the complete, authoritative Bill of Materials for the **MR1 Nanopore Reader (MR1)** system, organized across mechanical components, fluidic fittings, raw stock materials, custom printed circuit boards, and key active electronic components.

---

## 1. Mechanical Components & Fasteners

| Item Description | Sourcing / Specification | Qty | Role & Notes | Sourcing Link |
| :--- | :--- | :---: | :--- | :--- |
| **M3 Heat-Set Threaded Inserts** | Brass, M3 x 4mm x 5mm OD | 16 | Installs into `Housing_Case_Reader`, `Housing_Lid_Reader`, and `Housing_Pump_Case` | [Generic / McMaster 94180A333](https://www.mcmaster.com/94180A333/) |
| **M3x10mm Socket Head Cap Screws** | Stainless Steel 304/316 | 16 | Case assembly, lid clamping, and corner fastening | [Generic / McMaster 91292A113](https://www.mcmaster.com/91292A113/) |
| **M3x16mm Socket Head Cap Screws** | Stainless Steel 304/316 | 4 | Long corner mounting fasteners through housing standoffs | [Generic / McMaster 91292A115](https://www.mcmaster.com/91292A115/) |
| **Silicone O-Rings (CS 1.78mm)** | AS568-011, 50A/70A Silicone | 8 | Seals 1/8" NPT adapters and flowcell fluid port interfaces | [McMaster 1173N011](https://www.mcmaster.com/1173N011/) |
| **M75×8mm Torque Cap & Ratchet** | 3D Printed PETG / Nylon | 1 | Parametric clamping cap with built-in spring ratchet (`src/torque_cap.py`) | Staged STL in `exports/stl/` |
| **Pressure Puck & Finger Grips** | 3D Printed PETG / Polycarbonate | 1 | Distributes even compressive clamping force across flowcell stack | Staged STL in `exports/stl/` |

---

## 2. Microfluidic Tubing, Adapters & Fittings

| Item Description | Sourcing / Part Number | Qty | Role & Notes | Sourcing Link |
| :--- | :--- | :---: | :--- | :--- |
| **1/8" ID x 1/8" NPT Natural PP Adapter** | U.S. Plastic Item 64774 | 4 | Threads into Plate 1 Base Hex for bottom fluidic coupling | [U.S. Plastic 64774](https://www.usplastic.com/catalog/item.aspx?itemid=28545&catid=551) |
| **Alternative 1/8" NPT PP Adapter** | Industrial Spec BFA-18-2-PP | 4 | Drop-in alternative for threaded fluid ports | [Industrial Spec BFA-18-2-PP](https://www.industrialspec.com/shop/plastic-fittings/plastic-tube-fittings/plastic-tube-connectors/male-thread-x-barb-plastic-tube-connectors/bfa-series-npt-threads/bfa-18-2-pp.html) |
| **Female Luer Panel Mount to 1/8" Barb** | FluidControl24 FTLLB230-1 | 8 | 1/4-28 UNF panel mount. 4 for Reader side wall, 4 for Pump housing | [FluidControl24 FTLLB230-1](https://www.fluidcontrol24.com/ftllb230-1-female-luer-fitting-female-luer-thread-style-panel-mount-1-4-28-unf-to-barb-1-8-3-2-mm-id-tubing-white-nylon.html) |
| **Bulkhead Luer Lock Adapter** | Ark-Plas LJX39-PP0 / Item 96550 | 8 | ISO standard precision-molded luer lock bulkheads | [Ark-Plas Fitting](https://www.ark-plas.com/) |
| **FEP Tubing (1/8" ID x 1/4" OD)** | Chemfluor / Saint-Gobain | 1 m | Low-protein-binding feed line from pump to Cis chamber ($210^\circ$) | [McMaster 52365K13](https://www.mcmaster.com/52365K13/) |
| **PharMed BPT Peristaltic Tubing (1/8" ID)** | Saint-Gobain PharMed BPT | 1 m | High-fatigue-life tubing installed inside peristaltic pump rollers | [Cole-Parmer 96880-06](https://www.coleparmer.com/) |
| **Silicone Tubing (1/8" ID x 1/4" OD)** | Platinum-Cured Lab Grade | 2 m | Flexible drain lines for Cis outlet ($30^\circ$) and Trans inlet ($330^\circ$) | [McMaster 5188K42](https://www.mcmaster.com/5188K42/) |
| **PEEK Tubing (1/8" OD)** | High-Purity Chromatography | 1 m | Rigid inert line for Trans chamber recirculation/waste ($150^\circ$) | [Cole-Parmer PEEK](https://www.coleparmer.com/) |

---

## 3. Raw Stock Materials & Casting Reagents

| Item Description | Specification | Qty | Application |
| :--- | :--- | :---: | :--- |
| **Polypropylene (PP) Sheet** | 1/4" (6.35 mm) x 12" x 12" Natural PP | 1 | CNC milled into Plate 1 Base Hex and Plate 3 Top Hex |
| **Translucent Silicone Sheet** | 1/16" (1.5875 mm) x 3" x 9", 50A Durometer | 1 | Laser-cut / punch-cut into intermediate sealing gaskets |
| **PDMS Casting Kit** | Dow Sylgard 184 (Base + Curing Agent) | 0.5 kg | Casts high-precision `Cast_Nanopore_Wafer_Gasket` in SLA mold |
| **Solid-State Nanopore Chips** | 4x4 mm SiNx membrane window (10-50 nm thick) | As needed | Central sensing element with 2-10 nm nanopore aperture |
| **Ag/AgCl Ribbon Electrode Foil** | 0.25 mm x 1.0 mm Silver/Silver Chloride | 0.5 m | Dual-sided Cis and Trans internal chamber electrodes |

---

## 4. Custom Printed Circuit Boards (PCBs)

| Board Name | Substrate & Layer Stackup | Dimensions | Description & Role | Fabrication Package |
| :--- | :--- | :---: | :--- | :--- |
| **MR1 Main Board** | 6-Layer FR4 High-TG, ENIG finish, 1.6 mm | 80.0 x 60.0 mm | Core ESP32-S3 DAQ motherboard, 100 kHz SPI ADC, dual DACs, USB-C | `exports/MR1_Gerbers.zip` |
| **Cartridge Amplifier** | 2-Layer 0.8 mm FR4/Rogers, ENIG, guarded | 55.0 x 51.96 mm | Femtoampere LMP7721 transimpedance amplifier mounted beneath cell | `exports/Amplifier_Gerbers.zip` |
| **PTFE Interposer** | 2-Layer Rogers RO4350B / PTFE (0.8 mm, er=2.1) | 55.0 x 51.96 mm | Passive microfluidic flowcell barrier with 12-pin guarded pogo target | `Interposer/Interposer.kicad_pcb` |
| **Pump Controller Hub** | 4-Layer FR4 High-TG, 1.6 mm, 2 oz copper | 88.0 x 88.0 mm | STM32G431 MCU, STUSB4500 USB-PD sink, dual DRV8837C, ABP2 sensors | `Pump/Pump.kicad_pcb` |

---

## 5. Critical Active & Passive Electronic Components

| Component Reference | Manufacturer & Part Number | Package | Qty | Subsystem & Function |
| :--- | :--- | :---: | :---: | :--- |
| **U2 (Amplifier)** | TI LMP7721MA/NOPB | SOIC-8 | 1 | 3 fA ultra-low input bias current precision amplifier |
| **U10 (MR1)** | Analog Devices AD4000BCPZ / AD4020 | LFCSP-10 | 1 | 16/18-Bit 2 MSPS pseudo-differential SAR ADC |
| **U11, U12 (MR1)** | Microchip MCP4822-E/MS | MSOP-8 | 2 | Dual 12-bit SPI DACs with internal 2.048V bandgap reference |
| **U1 (MR1)** | Espressif ESP32-S3-WROOM-1-N16R8 | Module | 1 | 240 MHz dual-core MCU with native USB CDC-ACM and Wi-Fi |
| **U1 (Pump)** | STMicroelectronics STM32G431CBU6 | UFQFPN-48 | 1 | 170 MHz ARM Cortex-M4 motor control & pressure telemetry MCU |
| **U2 (Pump)** | STMicroelectronics STUSB4500QTR | QFN-24 | 1 | Autonomous USB-PD Sink controller (negotiates 9V/12V/15V/20V) |
| **U3, U4 (Pump)** | Texas Instruments DRV8837CDSGR | WSON-8 | 2 | 1.8A low-voltage H-bridge motor drivers with PWM interface |
| **U5 (Pump)** | Texas Instruments TS3USB221RSER | QFN-10 | 1 | >1.1 GHz USB 2.0 high-speed signal multiplexer |
| **SEN1 (Pump)** | Honeywell ABP2DANT015PGAA3XX | SMT Barb | 1 | 0-15 psi gauge digital I2C pressure sensor (Cis line) |
| **SEN2 (Pump)** | Honeywell ABP2DANT005PGAA3XX | SMT Barb | 1 | 0-5 psi gauge digital I2C pressure sensor (Trans line) |
| **J_POGO1 (Amp/Int)**| Mill-Max 821-22-012-10-000101 / 824-22-012 | 12-Pin DIL | 1 pr | 12-Pin guarded spring pogo header & ENIG target pad array |
| **Motors** | Diitao / Kamoer 12V Peristaltic Pump | DC Gearbox | 2 | Peristaltic pump heads for Cis and Trans automated fluid delivery |
