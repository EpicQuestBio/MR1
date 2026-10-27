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
| **Solid-State Nanopore Chips** | 4x4 x 0.5 mm Silicon die. Options: (a) Commercial SiNx (10-50 nm membrane, 2-10 nm pore); (b) Kent reference die (200 nm membrane, 10 µm window, 100 nm pore) | As needed | Central sensing element with sub-10 nm or 100 nm nanopore aperture |
| **Ag/AgCl Ribbon Electrode Foil** | 0.25 mm x 1.0 mm Silver/Silver Chloride | 0.5 m | Dual-sided Cis and Trans internal chamber electrodes |

---

## 4. Custom Printed Circuit Boards (PCBs)

| Board Name | Substrate & Layer Stackup | Dimensions | Description & Role | Fabrication Package |
| :--- | :--- | :---: | :--- | :--- |
| **MR1 Main Board** | 4-Layer FR4 High-TG, ENIG finish, 1.6 mm | 80.0 x 60.0 mm | Core ESP32-S3 DAQ motherboard with split GNDA/GND & VDDA/3V3 planes, dual DAC, USB-C | `exports/MR1_Gerbers.zip` |
| **Cartridge Amplifier** | 2-Layer 0.8 mm FR4/Rogers, ENIG, guarded | 55.0 x 51.96 mm | Femtoampere LMP7721 transimpedance amplifier mounted beneath cell | `exports/Amplifier_Gerbers.zip` |
| **PTFE Interposer** | 2-Layer Rogers RO4350B / PTFE (0.8 mm, er=2.1) | 55.0 x 51.96 mm | Passive microfluidic flowcell barrier with 12-pin guarded pogo target | `Interposer/Interposer.kicad_pcb` |
| **Rigid Backing Anvil** | 6.0 mm Delrin (POM-H) / Anodized Aluminum 6061-T6 | 55.0 x 51.96 mm | Clamps 2-layer PTFE interposer against 12 pogo spring loads (~9.6 N total load) preventing viscoelastic creep | `exports/Bottom_Pusher_Plate.step` |
| **Pump Controller Hub** | 4-Layer FR4 High-TG, 1.6 mm, 2 oz copper | 88.0 x 88.0 mm | STM32G431 MCU, STUSB4500 USB-PD sink, dual DRV8837C, ABP2 sensors | `Pump/Pump.kicad_pcb` |

---

## 5. Critical Active & Passive Electronic Components

| Component Reference | Manufacturer & Part Number | LCSC Part # / Equivalent | Package | Qty | Subsystem & Function |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **U2 (Amplifier)** | TI LMP7721MA/NOPB | [`C124427`](https://www.lcsc.com/search?q=C124427) (`LMP7721MA/NOPB`) | SOIC-8 | 1 | Route 1 (Path 1): 3 fA ultra-low input bias current precision TIA for sub-5 nm pores |
| **R1 (Amplifier)** | Ohmite MOX-300001007FE / TE HB1100MFZRE | `HVC0805T1007JET` / 10× [`C25488`](https://www.lcsc.com/search?q=C25488) | 0805/1206 | 1 | Route 1 (Path 1): 1.0 GΩ ±1.0% precision high-megohm TIA feedback resistor |
| **C1 (Amplifier)** | Murata GJM1555C1H2R0BB01D | [`C161316`](https://www.lcsc.com/search?q=C161316) / [`C1544`](https://www.lcsc.com/search?q=C1544) (Basic) | 0402 | 1 | Route 1 (Path 1): 2.0 pF ±0.1 pF C0G/NP0 non-piezoelectric feedback capacitor |
| **U5 (Amplifier)** | TI OPA2192IDR | [`C110074`](https://www.lcsc.com/search?q=C110074) (`OPA2192IDR`) | SOIC-8 | 1 | Route 2 (Path 2): Dual precision op-amp (Unit 1 = Micropore TIA, Unit 2 = Low-Z Guard Buffer driving GUARD_WIDE) |
| **U17 (Amplifier)** | ADI ADG1219BRMZ | [`C206796`](https://www.lcsc.com/search?q=C206796) (`ADG419BRMZ` eq.) / [`C2879206`](https://www.lcsc.com/search?q=C2879206) (`TMUX1108`) | MSOP-8 | 1 | Precision low-leakage SPDT analog multiplexer switching Route 1 (LMP7721+LTC6268) vs Route 2 (OPA2192) into ADC (`Signal_Return`) |
| **R10 (Amplifier)** | Yageo RC0402FR-07100KL | [`C60491`](https://www.lcsc.com/search?q=C60491) / [`C25741`](https://www.lcsc.com/search?q=C25741) (Basic) | 0402 | 1 | Route 2 Micropore TIA: 100.0 kΩ ±1.0% thin film feedback resistor (±20.48 µA full scale) |
| **C3 (Amplifier)** | Wurth 885012005058 / Murata GRM1555C1H150JA01D | [`C33148`](https://www.lcsc.com/search?q=C33148) / [`C1556`](https://www.lcsc.com/search?q=C1556) (Basic) | 0402 | 1 | Route 2 Micropore TIA: 15.0 pF ±5% C0G/NP0 feedback capacitor (106.1 kHz bandwidth) |
| **U16 (Amplifier)** | ADI LTC6268IS8#TRPBF | [`C689169`](https://www.lcsc.com/search?q=C689169) (`LTC6268IS8#TRPBF`) | SOIC-8 | 1 | 500 MHz ultra-low bias current FET-input post-gain amplifier |
| **U6 (Amplifier)** | ADI ADA4940-1ACPZ-R7 | [`C529241`](https://www.lcsc.com/search?q=C529241) (`ADA4940-1ACPZ-R7`) | LFCSP-16 | 1 | Ultra-low power, low-distortion fully differential ADC driver |
| **U13 (Amplifier)** | Analog Devices AD4000BRMZ / AD4020 | [`C539308`](https://www.lcsc.com/search?q=C539308) (`AD4000BRMZ-RL7`) | MSOP-10 | 1 | 16/18-Bit 2 MSPS pseudo-differential SAR ADC mounted on Amplifier board |
| **U14 (Amplifier)** | TI LP5907MFX-1.8/NOPB | [`C92498`](https://www.lcsc.com/search?q=C92498) (`LP5907MFX-1.8/NOPB`) | SOT-23-5 | 1 | 250 mA ultra-low-noise 1.8V LDO regulator for ADC supply |
| **U9 (MR1)** | Microchip MCP4822-E/SN | [`C16040`](https://www.lcsc.com/search?q=C16040) (`MCP4822-E/SN`) | SOIC-8 | 1 | Dual 12-bit SPI DAC with internal 2.048V bandgap reference for pore bias |
| **U8 (MR1)** | Espressif ESP32-S3-MINI-1U-N8 | [`C2980299`](https://www.lcsc.com/search?q=C2980299) (`ESP32-S3-MINI-1U-N8`) | Module | 1 | 240 MHz dual-core MCU with native USB CDC-ACM and Wi-Fi |
| **U1 (MR1)** | TI LM27762DSSR | [`C473398`](https://www.lcsc.com/search?q=C473398) (`LM27762DSSR`) | WSON-12 | 1 | Low-noise positive/negative charge-pump regulated dual supply |
| **U2 (MR1)** | ADI LT3094EDD#TRPBF | [`C670493`](https://www.lcsc.com/search?q=C670493) (`LT3094EDD#TRPBF`) | DFN-12 | 1 | Ultra-low noise, high-PSRR negative linear regulator (`VSSA`) |
| **U4 (MR1)** | ADI LT3045EDD#TRPBF | [`C514420`](https://www.lcsc.com/search?q=C514420) (`LT3045EDD#TRPBF`) | DFN-12 | 1 | Ultra-low noise, high-PSRR positive linear regulator (`VDDA`) |
| **U3 (MR1)** | TI OPA197IDGKT | [`C133554`](https://www.lcsc.com/search?q=C133554) (`OPA197IDGKT`) | VSSOP-8 | 1 | 36V precision rail-to-rail analog conditioning operational amplifier |
| **U13 (MR1)** | ADI ADR4520ARZ-R7 | [`C659578`](https://www.lcsc.com/search?q=C659578) (`ADR4520ARZ-R7`) | SOIC-8 | 1 | Ultra-low noise, high-accuracy 2.048V precision voltage reference |
| **U7, U12 (MR1)** | TI SN65220DBVR | [`C21787`](https://www.lcsc.com/search?q=C21787) (`SN65220DBVR`) | SOT-23-6 | 2 | Single USB port transient voltage suppressor (TVS) |
| **U33 (MR1)** | ON Semi NCP114ASN330T1G | [`C156285`](https://www.lcsc.com/search?q=C156285) (`NCP114ASN330T1G`) | SOT-23-5 | 1 | 300 mA low-noise 3.3V LDO linear regulator |
| **U1 (Pump)** | STMicroelectronics STM32G431CBU6 | [`C529356`](https://www.lcsc.com/search?q=C529356) (`STM32G431CBU6`) | UFQFPN-48 | 1 | 170 MHz ARM Cortex-M4 motor control & pressure telemetry MCU |
| **U2 (Pump)** | STMicroelectronics STUSB4500QTR | [`C2678061`](https://www.lcsc.com/search?q=C2678061) (`STUSB4500QTR`) | QFN-24 | 1 | Autonomous USB-PD Sink controller (negotiates 9V/12V/15V/20V) |
| **U3 (Pump)** | Texas Instruments TPS54302DDAR | [`C9864`](https://www.lcsc.com/search?q=C9864) (`TPS54302DDAR`) | SOIC-8 | 1 | 4.5V to 28V input, 3A synchronous step-down buck converter |
| **U4 (Pump)** | STMicroelectronics LD39050PU33R | [`C91206`](https://www.lcsc.com/search?q=C91206) (`LD39050PU33R`) | SOT-23-5/DFN | 1 | 500 mA low-noise 3.3V LDO regulator for Pump MCU |
| **U5 (Pump)** | Texas Instruments TPS22916 / TPS22918 | [`C131941`](https://www.lcsc.com/search?q=C131941) (`TPS22918DBVR` eq.) | WLCSP/SOT | 1 | 5.5V, 2A low-leakage controlled load switch |
| **U6 (Pump)** | Texas Instruments TS3USB221RSER | [`C130085`](https://www.lcsc.com/search?q=C130085) (`TS3USB221RSER`) | QFN-10 | 1 | >1.1 GHz USB 2.0 high-speed signal multiplexer |
| **U7, U8 (Pump)** | Texas Instruments DRV8837CDSGR | [`C191000`](https://www.lcsc.com/search?q=C191000) (`DRV8837CDSGR`) | WSON-8 | 2 | 1.8A low-voltage H-bridge motor drivers with PWM interface |
| **U9 / SEN1 (Pump)** | Honeywell ABP2DANT015PGAA3XX | `GZP6847D-C100KPP` (0–100 kPa I2C eq.) | SMT Barb | 1 | 0-15 psi gauge digital I2C pressure sensor (Cis line) |
| **U10 / SEN2 (Pump)** | Honeywell ABP2DANT005PGAA3XX | `GZP6847D-C040KPP` (0–40 kPa I2C eq.) | SMT Barb | 1 | 0-5 psi gauge digital I2C pressure sensor (Trans line) |
| **J_POGO1 (Amp/Int)**| Mill-Max 821-22-012-10-000101 / 824-22-012 | [`C49451500`](https://www.lcsc.com/search?q=C49451500) (`PG2541` series eq.) | 12-Pin DIL | 1 pr | 12-Pin guarded spring pogo header & ENIG target pad array |
| **Motors** | Diitao / Kamoer 12V Peristaltic Pump | — | DC Gearbox | 2 | Peristaltic pump heads for Cis and Trans automated fluid delivery |
