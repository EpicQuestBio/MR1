# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Generates the KiCad PCB layout file for the MR1 Pump & USB-PD Hub board (Pump/Pump.kicad_pcb).
Matches physical housing constraints:
- Board size: 88.0 x 88.0 mm (fitting within 89.0 x 89.0 mm Housing_Pump_Case bucket)
- Mounting holes: 4x M3 at (+/-38.0, +/-38.0) mm from center
- Dual USB-C connectors:
    * J1_HOST at X = -15.0 mm, Y = -44.0 mm (top edge)
    * J2_MR1  at X = +15.0 mm, Y = -44.0 mm (top edge)
  Matching Housing_Pump_Case back wall cutouts at X = +/-15.0 mm
- Peristaltic pump headers:
    * J_PUMP1 at X = -25.0 mm, Y = 25.0 mm
    * J_PUMP2 at X = +25.0 mm, Y = 25.0 mm
- STM32G431 MCU at center (0, 0)
- STUSB4500 USB-PD Sink controller
- Synchronous Buck Converter + Clean 5V Output filter
- Dual Honeywell TruStability/ABP2 pressure sensors
- TS3USB221 USB 2.0 High-Speed Switch
"""

import sys
import uuid
from pathlib import Path

def gen_uuid():
    return str(uuid.uuid4())

def generate_pcb():
    # Board centered at (100, 100)
    CX = 100.0
    CY = 100.0
    HALF_SIZE = 44.0  # 88x88 mm board
    
    x1, y1 = CX - HALF_SIZE, CY - HALF_SIZE  # 56.0, 56.0
    x2, y2 = CX + HALF_SIZE, CY + HALF_SIZE  # 144.0, 144.0
    
    # Mounting holes at +/- 38 mm from center
    mount_holes = [
        (CX - 38.0, CY - 38.0, "MH1"),
        (CX + 38.0, CY - 38.0, "MH2"),
        (CX - 38.0, CY + 38.0, "MH3"),
        (CX + 38.0, CY + 38.0, "MH4"),
    ]
    
    lines = []
    lines.append('(kicad_pcb')
    lines.append('\t(version 20241229)')
    lines.append('\t(generator "pcbnew")')
    lines.append('\t(generator_version "10.0")')
    lines.append('\t(general')
    lines.append('\t\t(thickness 1.6)')
    lines.append('\t\t(legacy_teardrops no)')
    lines.append('\t)')
    lines.append('\t(paper "A4")')
    
    # Layers (4 copper layers + silk, mask, edge cuts, etc.)
    lines.append('\t(layers')
    lines.append('\t\t(0 "F.Cu" signal)')
    lines.append('\t\t(4 "In1.Cu" signal)')
    lines.append('\t\t(6 "In2.Cu" signal)')
    lines.append('\t\t(2 "B.Cu" signal)')
    lines.append('\t\t(9 "F.Adhes" user "F.Adhesive")')
    lines.append('\t\t(11 "B.Adhes" user "B.Adhesive")')
    lines.append('\t\t(13 "F.Paste" user)')
    lines.append('\t\t(15 "B.Paste" user)')
    lines.append('\t\t(5 "F.SilkS" user "F.Silkscreen")')
    lines.append('\t\t(7 "B.SilkS" user "B.Silkscreen")')
    lines.append('\t\t(1 "F.Mask" user)')
    lines.append('\t\t(3 "B.Mask" user)')
    lines.append('\t\t(17 "Dwgs.User" user "User.Drawings")')
    lines.append('\t\t(19 "Cmts.User" user "User.Comments")')
    lines.append('\t\t(21 "Eco1.User" user "User.Eco1")')
    lines.append('\t\t(23 "Eco2.User" user "User.Eco2")')
    lines.append('\t\t(25 "Edge.Cuts" user)')
    lines.append('\t\t(27 "Margin" user)')
    lines.append('\t\t(31 "F.CrtYd" user "F.Courtyard")')
    lines.append('\t\t(29 "B.CrtYd" user "B.Courtyard")')
    lines.append('\t\t(35 "F.Fab" user)')
    lines.append('\t\t(33 "B.Fab" user)')
    lines.append('\t)')
    
    # Setup
    lines.append('\t(setup')
    lines.append('\t\t(stackup')
    lines.append('\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))')
    lines.append('\t\t\t(layer "F.Paste" (type "Top Solder Paste"))')
    lines.append('\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))')
    lines.append('\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))')
    lines.append('\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5))')
    lines.append('\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.035))')
    lines.append('\t\t\t(layer "dielectric 2" (type "core") (thickness 1.2) (material "FR4") (epsilon_r 4.5))')
    lines.append('\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.035))')
    lines.append('\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.1) (material "FR4") (epsilon_r 4.5))')
    lines.append('\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))')
    lines.append('\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))')
    lines.append('\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))')
    lines.append('\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))')
    lines.append('\t\t\t(copper_finish "None")')
    lines.append('\t\t\t(dielectric_constraints yes)')
    lines.append('\t\t)')
    lines.append('\t\t(pad_to_mask_clearance 0)')
    lines.append('\t\t(pcbplotparams')
    lines.append('\t\t\t(layerselection 0x00000000_00000000_55555555_5755f5ff)')
    lines.append('\t\t\t(disableapertmacros no)')
    lines.append('\t\t\t(usegerberextensions no)')
    lines.append('\t\t\t(usegerberattributes yes)')
    lines.append('\t\t\t(usegerberadvancedattributes yes)')
    lines.append('\t\t\t(creategerberjobfile yes)')
    lines.append('\t\t\t(mode 1)')
    lines.append('\t\t\t(outputformat 1)')
    lines.append('\t\t)')
    lines.append('\t)')
    
    # Net definitions
    nets = [
        (0, ""),
        (1, "GND"),
        (2, "+VBUS_PD"),
        (3, "VMOTOR"),
        (4, "+5V_MR1_CLEAN"),
        (5, "+3V3"),
        (6, "HOST_D+"),
        (7, "HOST_D-"),
        (8, "MR1_D+"),
        (9, "MR1_D-"),
        (10, "PD_CC1"),
        (11, "PD_CC2"),
        (12, "SBU1_HOST"),
        (13, "SBU2_HOST"),
        (14, "SBU1_MR1"),
        (15, "SBU2_MR1"),
        (16, "PUMP1_OUT1"),
        (17, "PUMP1_OUT2"),
        (18, "PUMP2_OUT1"),
        (19, "PUMP2_OUT2"),
        (20, "PRESS_I2C_SCL"),
        (21, "PRESS_I2C_SDA"),
        (22, "PRESS_ALERT_"),
        (23, "PD_I2C_SCL"),
        (24, "PD_I2C_SDA"),
        (25, "PD_ALERT_"),
        (26, "MR1_PWR_EN"),
        (27, "USB_SEL_PASS"),
        (28, "ESTOP_TRIGGER_"),
        (29, "SWDIO"),
        (30, "SWCLK"),
        (31, "NRST"),
    ]
    for nid, nname in nets:
        lines.append(f'\t(net {nid} "{nname}")')

    # Edge Cuts: 88.0 x 88.0 mm rectangle with 2.0 mm corner chamfers
    corner_radius = 2.0
    lines.append(f'\t(gr_line (start {x1 + corner_radius} {y1}) (end {x2 - corner_radius} {y1}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2 - corner_radius} {y1}) (end {x2} {y1 + corner_radius}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2} {y1 + corner_radius}) (end {x2} {y2 - corner_radius}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2} {y2 - corner_radius}) (end {x2 - corner_radius} {y2}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2 - corner_radius} {y2}) (end {x1 + corner_radius} {y2}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1 + corner_radius} {y2}) (end {x1} {y2 - corner_radius}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1} {y2 - corner_radius}) (end {x1} {y1 + corner_radius}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1} {y1 + corner_radius}) (end {x1 + corner_radius} {y1}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')

    # Silk text
    lines.append(f'\t(gr_text "MR1 PUMP & USB-PD HUB REV 1.0" (at {CX} {y1 + 4.0}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.5 1.5) (thickness 0.25))))')
    lines.append(f'\t(gr_text "MR1 PROJECT" (at {CX} {y2 - 4.0}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.2 1.2) (thickness 0.2))))')
    lines.append(f'\t(gr_text "HOST USB-PD IN" (at {CX - 15.0} {y1 + 10.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "MR1 READER OUT" (at {CX + 15.0} {y1 + 10.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "PUMP 1 (CIS)" (at {CX - 25.0} {CY + 37.0}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "PUMP 2 (TRANS)" (at {CX + 25.0} {CY + 37.0}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "CIS PRESS" (at {CX - 32.0} {CY}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "TRANS PRESS" (at {CX + 32.0} {CY}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')

    # Mounting holes
    for hx, hy, ref in mount_holes:
        lines.append(f'\t(footprint "MountingHole:MountingHole_3.2mm_M3_Pad"')
        lines.append(f'\t\t(layer "F.Cu")')
        lines.append(f'\t\t(uuid "{gen_uuid()}")')
        lines.append(f'\t\t(at {hx} {hy})')
        lines.append(f'\t\t(property "Reference" "{ref}" (at 0 -3.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
        lines.append(f'\t\t(pad "1" thru_hole circle (at 0 0) (size 6.0 6.0) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t)')

    # Footprint: J1_HOST (USB-C Receptacle at X = -15mm, top edge)
    lines.append(f'\t(footprint "Connector_USB:USB_C_Receptacle_GCT_USB4085"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX - 15.0} {y1 + 4.5} 180)')
    lines.append(f'\t\t(property "Reference" "J1_HOST" (at 0 -4.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "USB_C_HOST" (at 0 4.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    # USB-C shield & ground pads
    lines.append(f'\t\t(pad "SH1" thru_hole oval (at -4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "SH2" thru_hole oval (at 4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A1" smd rect (at -3.2 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A4" smd rect (at -2.4 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A5" smd rect (at -1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 10 "PD_CC1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A6" smd rect (at -0.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 6 "HOST_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A7" smd rect (at 0.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 7 "HOST_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A8" smd rect (at 1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 12 "SBU1_HOST") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A9" smd rect (at 2.4 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A12" smd rect (at 3.2 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B5" smd rect (at 1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 11 "PD_CC2") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B8" smd rect (at -1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 13 "SBU2_HOST") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: J2_MR1 (USB-C Receptacle at X = +15mm, top edge)
    lines.append(f'\t(footprint "Connector_USB:USB_C_Receptacle_GCT_USB4085"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX + 15.0} {y1 + 4.5} 180)')
    lines.append(f'\t\t(property "Reference" "J2_MR1" (at 0 -4.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "USB_C_MR1_OUT" (at 0 4.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "SH1" thru_hole oval (at -4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "SH2" thru_hole oval (at 4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A1" smd rect (at -3.2 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A4" smd rect (at -2.4 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A6" smd rect (at -0.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 8 "MR1_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A7" smd rect (at 0.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 9 "MR1_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A8" smd rect (at 1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 14 "SBU1_MR1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A9" smd rect (at 2.4 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A12" smd rect (at 3.2 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B8" smd rect (at -1.6 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 15 "SBU2_MR1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U1_MCU (STM32G431CBU6, UFQFPN-48, 7x7 mm) at board center
    lines.append(f'\t(footprint "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX} {CY})')
    lines.append(f'\t\t(property "Reference" "U1_MCU" (at 0 -4.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "STM32G431CBU6" (at 0 4.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "49" smd rect (at 0 0) (size 5.6 5.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U2_PD (STUSB4500, QFN-24, 4x4 mm)
    lines.append(f'\t(footprint "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX - 18.0} {CY - 22.0})')
    lines.append(f'\t\t(property "Reference" "U2_PD" (at 0 -3.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "STUSB4500" (at 0 3.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "25" smd rect (at 0 0) (size 2.6 2.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U3_BUCK (TPS54302, SOIC-8)
    lines.append(f'\t(footprint "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX - 18.0} {CY - 8.0})')
    lines.append(f'\t\t(property "Reference" "U3_BUCK" (at 0 -3.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "TPS54302" (at 0 3.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "1" smd rect (at -2.6 -1.905) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at -2.6 -0.635) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at 2.6 1.905) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U4_LDO (LD39050 / AP2112K 3.3V LDO)
    lines.append(f'\t(footprint "Package_TO_SOT_SMD:SOT-23-5"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX} {CY - 22.0})')
    lines.append(f'\t\t(property "Reference" "U4_LDO" (at 0 -2.2 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "LD39050_3V3" (at 0 2.2 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "1" smd rect (at -0.95 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at 0 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at -0.95 1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U6_MUX (TS3USB221 USB 2.0 High-Speed Switch)
    lines.append(f'\t(footprint "Package_DFN_QFN:QFN-10_1.5x2mm_P0.4mm"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX} {CY - 34.0})')
    lines.append(f'\t\t(property "Reference" "U6_MUX" (at 0 -2.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.9 0.9) (thickness 0.14))))')
    lines.append(f'\t\t(property "Value" "TS3USB221" (at 0 2.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.9 0.9) (thickness 0.14))))')
    lines.append(f'\t\t(pad "1" smd rect (at -0.8 -0.8) (size 0.5 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 6 "HOST_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at -0.8 -0.4) (size 0.5 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 7 "HOST_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at 0.8 -0.8) (size 0.5 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 8 "MR1_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "6" smd rect (at 0.8 -0.4) (size 0.5 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 9 "MR1_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "10" smd rect (at 0 1.0) (size 0.25 0.5) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Footprint: U7_DRV1 & U8_DRV2 (TI DRV8837C H-Bridge Motor Drivers)
    for dx, ref, pwr_net in [
        (CX - 25.0, "U7_DRV1", "PUMP1_OUT"),
        (CX + 25.0, "U8_DRV2", "PUMP2_OUT"),
    ]:
        lines.append(f'\t(footprint "Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"')
        lines.append(f'\t\t(layer "F.Cu")')
        lines.append(f'\t\t(uuid "{gen_uuid()}")')
        lines.append(f'\t\t(at {dx} {CY + 18.0})')
        lines.append(f'\t\t(property "Reference" "{ref}" (at 0 -2.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.9 0.9) (thickness 0.14))))')
        lines.append(f'\t\t(property "Value" "DRV8837C" (at 0 2.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.9 0.9) (thickness 0.14))))')
        lines.append(f'\t\t(pad "1" smd rect (at -0.9 -0.75) (size 0.6 0.3) (layers "F.Cu" "F.Paste" "F.Mask") (net 3 "VMOTOR") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "4" smd rect (at -0.9 0.75) (size 0.6 0.3) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "9" smd rect (at 0 0) (size 0.9 1.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t)')

    # Footprint: J_PUMP1 & J_PUMP2 (JST-XH 2-pin 2.5mm connectors)
    for px, pref, out1, out2 in [
        (CX - 25.0, "J_PUMP1", 16, 17),
        (CX + 25.0, "J_PUMP2", 18, 19),
    ]:
        lines.append(f'\t(footprint "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"')
        lines.append(f'\t\t(layer "F.Cu")')
        lines.append(f'\t\t(uuid "{gen_uuid()}")')
        lines.append(f'\t\t(at {px} {CY + 30.0})')
        lines.append(f'\t\t(property "Reference" "{pref}" (at 0 -3.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
        lines.append(f'\t\t(property "Value" "PUMP_MOTOR" (at 0 3.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
        lines.append(f'\t\t(pad "1" thru_hole rect (at -1.25 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {out1} "") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" thru_hole oval (at 1.25 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {out2} "") (uuid "{gen_uuid()}"))')
        lines.append(f'\t)')

    # Footprint: U9_SENS1 & U10_SENS2 (Honeywell ABP2/TruStability Pressure Sensors)
    for sx, sref, sval in [
        (CX - 32.0, "U9_SENS1", "ABP2_015PG_CIS"),
        (CX + 32.0, "U10_SENS2", "ABP2_005PG_TRANS"),
    ]:
        lines.append(f'\t(footprint "Sensor_Pressure:Honeywell_ABP_SMD"')
        lines.append(f'\t\t(layer "F.Cu")')
        lines.append(f'\t\t(uuid "{gen_uuid()}")')
        lines.append(f'\t\t(at {sx} {CY})')
        lines.append(f'\t\t(property "Reference" "{sref}" (at 0 -5.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
        lines.append(f'\t\t(property "Value" "{sval}" (at 0 5.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.9 0.9) (thickness 0.14))))')
        lines.append(f'\t\t(pad "1" smd rect (at -3.5 -2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" smd rect (at -3.5 0) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "3" smd rect (at -3.5 2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 21 "PRESS_I2C_SDA") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "4" smd rect (at 3.5 2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 20 "PRESS_I2C_SCL") (uuid "{gen_uuid()}"))')
        lines.append(f'\t)')

    # Footprint: J_SWD (4-pin 2.54mm programming header)
    lines.append(f'\t(footprint "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"')
    lines.append(f'\t\t(layer "F.Cu")')
    lines.append(f'\t\t(uuid "{gen_uuid()}")')
    lines.append(f'\t\t(at {CX} {CY + 18.0})')
    lines.append(f'\t\t(property "Reference" "J_SWD" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(pad "1" thru_hole rect (at -3.81 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" thru_hole oval (at -1.27 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 29 "SWDIO") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "3" thru_hole oval (at 1.27 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 30 "SWCLK") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "4" thru_hole oval (at 3.81 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t)')

    # Ground Plane Zone on In1.Cu
    lines.append(f'\t(zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{gen_uuid()}")')
    lines.append(f'\t\t(hatch edge 0.5)')
    lines.append(f'\t\t(connect_pads (clearance 0.25))')
    lines.append(f'\t\t(min_thickness 0.2)')
    lines.append(f'\t\t(polygon')
    lines.append(f'\t\t\t(pts')
    lines.append(f'\t\t\t\t(xy {x1 + 0.5} {y1 + 0.5})')
    lines.append(f'\t\t\t\t(xy {x2 - 0.5} {y1 + 0.5})')
    lines.append(f'\t\t\t\t(xy {x2 - 0.5} {y2 - 0.5})')
    lines.append(f'\t\t\t\t(xy {x1 + 0.5} {y2 - 0.5})')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    lines.append(f'\t)')

    # Power Plane Zone on In2.Cu
    lines.append(f'\t(zone (net 4) (net_name "+5V_MR1_CLEAN") (layer "In2.Cu") (uuid "{gen_uuid()}")')
    lines.append(f'\t\t(hatch edge 0.5)')
    lines.append(f'\t\t(connect_pads (clearance 0.25))')
    lines.append(f'\t\t(min_thickness 0.2)')
    lines.append(f'\t\t(polygon')
    lines.append(f'\t\t\t(pts')
    lines.append(f'\t\t\t\t(xy {x1 + 0.5} {y1 + 0.5})')
    lines.append(f'\t\t\t\t(xy {x2 - 0.5} {y1 + 0.5})')
    lines.append(f'\t\t\t\t(xy {x2 - 0.5} {y2 - 0.5})')
    lines.append(f'\t\t\t\t(xy {x1 + 0.5} {y2 - 0.5})')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    lines.append(f'\t)')

    lines.append(')')
    lines.append('')
    return '\n'.join(lines)

if __name__ == '__main__':
    out_path = Path(__file__).resolve().parent.parent / "Pump" / "Pump.kicad_pcb"
    content = generate_pcb()
    out_path.write_text(content, encoding='utf-8')
    print(f"Generated {out_path} ({len(content)} bytes)")
