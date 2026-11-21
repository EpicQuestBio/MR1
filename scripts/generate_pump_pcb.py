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


import re
import sys
import uuid
from pathlib import Path

def gen_uuid():
    return str(uuid.uuid4())

def make_seg(x1, y1, x2, y2, width, layer, net_id):
    return f'\t(segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width}) (layer "{layer}") (net {net_id}) (uuid "{gen_uuid()}"))'

def make_via(vx, vy, size, drill, net_id):
    return f'\t(via (at {vx:.4f} {vy:.4f}) (size {size}) (drill {drill}) (layers "F.Cu" "B.Cu") (net {net_id}) (uuid "{gen_uuid()}"))'

def generate_pump_clean():
    CX, CY = 100.0, 100.0
    HALF_SIZE = 44.0
    x1, y1 = CX - HALF_SIZE, CY - HALF_SIZE
    x2, y2 = CX + HALF_SIZE, CY + HALF_SIZE

    lines = []
    lines.append('(kicad_pcb')
    lines.append('\t(version 20241229)')
    lines.append('\t(generator "pcbnew")')
    lines.append('\t(generator_version "10.0")')
    lines.append('\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)')
    lines.append('\t(paper "A4")')

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
    lines.append('\t\t\t(disableapertmacros no)\n\t\t\t(usegerberextensions no)\n\t\t\t(usegerberattributes yes)\n\t\t\t(usegerberadvancedattributes yes)\n\t\t\t(creategerberjobfile yes)\n\t\t\t(mode 1)\n\t\t\t(outputformat 1)\n\t\t)\n\t)')

    nets = [
        (0, ""), (1, "GND"), (2, "+VBUS_PD"), (3, "VMOTOR"), (4, "+5V_MR1_CLEAN"), (5, "+3V3"),
        (6, "HOST_D+"), (7, "HOST_D-"), (8, "MR1_D+"), (9, "MR1_D-"), (10, "PD_CC1"), (11, "PD_CC2"),
        (12, "SBU1_HOST"), (13, "SBU2_HOST"), (14, "SBU1_MR1"), (15, "SBU2_MR1"),
        (16, "PUMP1_OUT1"), (17, "PUMP1_OUT2"), (18, "PUMP2_OUT1"), (19, "PUMP2_OUT2"),
        (20, "PRESS_I2C_SCL"), (21, "PRESS_I2C_SDA"), (22, "PRESS_ALERT_"), (23, "PD_I2C_SCL"),
        (24, "PD_I2C_SDA"), (25, "PD_ALERT_"), (26, "MR1_PWR_EN"), (27, "USB_SEL_PASS"),
        (28, "ESTOP_TRIGGER_"), (29, "SWDIO"), (30, "SWCLK"), (31, "NRST"),
        (32, "OSC_IN"), (33, "OSC_OUT"), (34, "PUMP1_PWM"), (35, "PUMP1_DIR"),
        (36, "PUMP2_PWM"), (37, "PUMP2_DIR"), (38, "SW_NODE"),
    ]
    for nid, nname in nets:
        lines.append(f'\t(net {nid} "{nname}")')

    lines.append('\t(net_class "Default" "This is the default net class."')
    lines.append('\t\t(clearance 0.12)\n\t\t(trace_width 0.2)\n\t\t(via_dia 0.6)\n\t\t(via_drill 0.3)\n\t)')

    # Board edge
    lines.append(f'\t(gr_line (start {x1 + 2.0} {y1}) (end {x2 - 2.0} {y1}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2 - 2.0} {y1}) (end {x2} {y1 + 2.0}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2} {y1 + 2.0}) (end {x2} {y2 - 2.0}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2} {y2 - 2.0}) (end {x2 - 2.0} {y2}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x2 - 2.0} {y2}) (end {x1 + 2.0} {y2}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1 + 2.0} {y2}) (end {x1} {y2 - 2.0}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1} {y2 - 2.0}) (end {x1} {y1 + 2.0}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')
    lines.append(f'\t(gr_line (start {x1} {y1 + 2.0}) (end {x1 + 2.0} {y1}) (stroke (width 0.15)) (layer "Edge.Cuts") (uuid "{gen_uuid()}"))')

    # Silkscreen text (placed in open spaces, away from pads)
    lines.append(f'\t(gr_text "MR1 PUMP & USB-PD HUB REV 1.0" (at {CX} {CY - 29.0}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.2 1.2) (thickness 0.18))))')
    lines.append(f'\t(gr_text "MR1 PROJECT - DUAL DC / STEPPER READY" (at {CX} {y2 - 2.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.1 1.1) (thickness 0.18))))')
    lines.append(f'\t(gr_text "HOST USB-PD IN" (at {CX - 15.0} {y1 + 11.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "MR1 READER OUT" (at {CX + 15.0} {y1 + 11.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "PUMP 1 (CIS)" (at {CX - 25.0} {CY + 36.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "PUMP 2 (TRANS)" (at {CX + 25.0} {CY + 36.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "CIS PRESS" (at {CX - 32.0} {CY - 6.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')
    lines.append(f'\t(gr_text "TRANS PRESS" (at {CX + 32.0} {CY - 6.5}) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1.0 1.0) (thickness 0.18))))')

    # Mounting holes
    for hx, hy, ref in [
        (CX - 38.0, CY - 38.0, "MH1"),
        (CX + 38.0, CY - 38.0, "MH2"),
        (CX - 38.0, CY + 38.0, "MH3"),
        (CX + 38.0, CY + 38.0, "MH4"),
    ]:
        lines.append(f'\t(footprint "MountingHole:MountingHole_3.2mm_M3_Pad"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {hx} {hy})')
        lines.append(f'\t\t(property "Reference" "{ref}" (at 0 -4.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" thru_hole circle (at 0 0) (size 6.0 6.0) (drill 3.2) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # USB-C J1_HOST (Top-left at X = 85.0, Y = 60.5)
    # Using 10 primary active pins to avoid duplicate/unconnected B6/B7
    lines.append(f'\t(footprint "Connector_USB:USB_C_Receptacle_GCT_USB4085"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX - 15.0} {y1 + 4.5} 180)')
    lines.append(f'\t\t(property "Reference" "J1_HOST" (at 0 -4.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "USB_C_HOST" (at 0 4.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "SH1" thru_hole oval (at -4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "SH2" thru_hole oval (at 4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A1" smd rect (at -3.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A4" smd rect (at -2.45 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B8" smd rect (at -1.75 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 13 "SBU2_HOST") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A5" smd rect (at -1.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 10 "PD_CC1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A6" smd rect (at -0.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 6 "HOST_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A7" smd rect (at 0.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 7 "HOST_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A8" smd rect (at 1.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 12 "SBU1_HOST") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B5" smd rect (at 1.75 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 11 "PD_CC2") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A9" smd rect (at 2.45 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A12" smd rect (at 3.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # USB-C J2_MR1 (Top-right at X = 115.0, Y = 60.5)
    lines.append(f'\t(footprint "Connector_USB:USB_C_Receptacle_GCT_USB4085"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX + 15.0} {y1 + 4.5} 180)')
    lines.append(f'\t\t(property "Reference" "J2_MR1" (at 0 -4.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "USB_C_MR1_OUT" (at 0 4.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "SH1" thru_hole oval (at -4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "SH2" thru_hole oval (at 4.32 -0.8) (size 1.2 1.8) (drill oval 0.8 1.4) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A1" smd rect (at -3.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A4" smd rect (at -2.45 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "B8" smd rect (at -1.75 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 15 "SBU2_MR1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A6" smd rect (at -0.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 8 "MR1_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A7" smd rect (at 0.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 9 "MR1_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A8" smd rect (at 1.25 2.8) (size 0.28 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 14 "SBU1_MR1") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A9" smd rect (at 2.45 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "A12" smd rect (at 3.25 2.8) (size 0.3 1.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U1_MCU (STM32G431CBU6)
    lines.append(f'\t(footprint "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX} {CY})')
    lines.append(f'\t\t(property "Reference" "U1_MCU" (at 0 -4.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'\t\t(property "Value" "STM32G431CBU6" (at 0 4.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 1 1) (thickness 0.15))))')

    qfn_coords = [-2.75 + i * 0.5 for i in range(12)]
    for i, y_off in enumerate(qfn_coords, start=1):
        nid, nname = (1, "GND") if i in (8, 23, 35, 47) else (5, "+3V3") if i in (9, 24, 36, 48) else (0, "")
        lines.append(f'\t\t(pad "{i}" smd rect (at -3.45 {y_off:.2f}) (size 0.7 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net {nid} "{nname}") (uuid "{gen_uuid()}"))')
    for i, x_off in enumerate(qfn_coords, start=13):
        nid, nname = (1, "GND") if i in (8, 23, 35, 47) else (5, "+3V3") if i in (9, 24, 36, 48) else (0, "")
        lines.append(f'\t\t(pad "{i}" smd rect (at {x_off:.2f} 3.45) (size 0.25 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net {nid} "{nname}") (uuid "{gen_uuid()}"))')
    for i, y_off in enumerate(reversed(qfn_coords), start=25):
        nid, nname = (1, "GND") if i in (8, 23, 35, 47) else (5, "+3V3") if i in (9, 24, 36, 48) else (0, "")
        lines.append(f'\t\t(pad "{i}" smd rect (at 3.45 {y_off:.2f}) (size 0.7 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net {nid} "{nname}") (uuid "{gen_uuid()}"))')
    for i, x_off in enumerate(reversed(qfn_coords), start=37):
        nid, nname = (1, "GND") if i in (8, 23, 35, 47) else (5, "+3V3") if i in (9, 24, 36, 48) else (0, "")
        lines.append(f'\t\t(pad "{i}" smd rect (at {x_off:.2f} -3.45) (size 0.25 0.7) (layers "F.Cu" "F.Paste" "F.Mask") (net {nid} "{nname}") (uuid "{gen_uuid()}"))')

    lines.append(f'\t\t(pad "49" smd rect (at 0 0) (size 5.6 5.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # Decoupling Caps C1_MCU..C4_MCU
    for c_idx, (cx_off, cy_off) in enumerate([(-6.0, -3.5), (-6.0, 3.5), (6.0, -3.5), (6.0, 3.5)], start=1):
        lines.append(f'\t(footprint "Capacitor_SMD:C_0402_1005Metric"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX + cx_off} {CY + cy_off})')
        lines.append(f'\t\t(property "Reference" "C{c_idx}_MCU" (at 0 1.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(property "Value" "100nF" (at 0 -1.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" smd roundrect (at -0.48 0) (size 0.54 0.64) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" smd roundrect (at 0.48 0) (size 0.54 0.64) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # Pull-Ups R1_PU..R4_PU
    for r_idx, r_net, rx_off in [(1, "PRESS_I2C_SCL", -7.5), (2, "PRESS_I2C_SDA", -4.5), (3, "SBU1_HOST", 4.5), (4, "SBU2_HOST", 7.5)]:
        lines.append(f'\t(footprint "Resistor_SMD:R_0402_1005Metric"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX + rx_off} {CY - 8.0})')
        lines.append(f'\t\t(property "Reference" "R{r_idx}_PU" (at 0 -1.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(property "Value" "4.7k" (at 0 1.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" smd roundrect (at -0.48 0) (size 0.54 0.64) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" smd roundrect (at 0.48 0) (size 0.54 0.64) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 "{r_net}") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # Y1_HSE Crystal
    lines.append(f'\t(footprint "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX + 8.5} {CY})')
    lines.append(f'\t\t(property "Reference" "Y1_HSE" (at 0 -2.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "8.000MHz" (at 0 2.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" smd rect (at -1.1 0.8) (size 1.2 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 "OSC_IN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at 1.1 0.8) (size 1.2 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "3" smd rect (at 1.1 -0.8) (size 1.2 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 "OSC_OUT") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "4" smd rect (at -1.1 -0.8) (size 1.2 0.9) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U5_REG (TLV70233)
    lines.append(f'\t(footprint "Package_TO_SOT_SMD:SOT-23-5"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX - 8.5} {CY})')
    lines.append(f'\t\t(property "Reference" "U5_REG" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "TLV70233_3V3_ANA" (at 0 2.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" smd rect (at -0.95 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at 0 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "3" smd rect (at 0.95 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at -0.95 1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U2_PD (STUSB4500)
    lines.append(f'\t(footprint "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX - 18.0} {CY - 22.0})')
    lines.append(f'\t\t(property "Reference" "U2_PD" (at 0 -3.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "STUSB4500" (at 0 3.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "25" smd rect (at 0 0) (size 2.6 2.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U3_BUCK (TPS54302)
    lines.append(f'\t(footprint "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX - 18.0} {CY - 8.0})')
    lines.append(f'\t\t(property "Reference" "U3_BUCK" (at 0 -3.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "TPS54302" (at 0 3.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" smd rect (at -2.6 -1.905) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at -2.6 -0.635) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 2 "+VBUS_PD") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at 2.6 1.905) (size 1.5 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U4_LDO (LD39050)
    lines.append(f'\t(footprint "Package_TO_SOT_SMD:SOT-23-5"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX} {CY - 22.0})')
    lines.append(f'\t\t(property "Reference" "U4_LDO" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "LD39050_3V3" (at 0 2.5 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" smd rect (at -0.95 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 4 "+5V_MR1_CLEAN") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd rect (at 0 -1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd rect (at -0.95 1.35) (size 0.6 1.05) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U6_MUX (TS3USB221)
    lines.append(f'\t(footprint "Package_DFN_QFN:Texas_UQFN-10_1.5x2mm_P0.5mm"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX} {CY - 34.0})')
    lines.append(f'\t\t(property "Reference" "U6_MUX" (at 0 -2.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(property "Value" "TS3USB221" (at 0 2.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" smd roundrect (at -0.675 -0.75) (size 0.55 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 6 "HOST_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" smd roundrect (at -0.675 -0.25) (size 0.55 0.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 7 "HOST_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "9" smd roundrect (at 0.675 -0.25) (size 0.55 0.2) (layers "F.Cu" "F.Paste" "F.Mask") (net 9 "MR1_D-") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "10" smd roundrect (at 0.675 -0.75) (size 0.55 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 8 "MR1_D+") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "5" smd roundrect (at 0 0.9) (size 0.3 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # U7_DRV1 & U8_DRV2 (Texas DSG0008A WSON-8)
    for dx, ref in [(CX - 25.0, "U7_DRV1"), (CX + 25.0, "U8_DRV2")]:
        lines.append(f'\t(footprint "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {dx} {CY + 18.0})')
        lines.append(f'\t\t(property "Reference" "{ref}" (at 0 -2.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(property "Value" "DRV8837C" (at 0 2.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" smd roundrect (at -0.95 -0.75) (size 0.6 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 3 "VMOTOR") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "4" smd roundrect (at -0.95 0.75) (size 0.6 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "9" smd rect (at 0 0) (size 0.9 1.6) (layers "F.Cu" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # J_PUMP1 & J_PUMP2
    for px, pref, out1, out2 in [(CX - 25.0, "J_PUMP1", 16, 17), (CX + 25.0, "J_PUMP2", 18, 19)]:
        lines.append(f'\t(footprint "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {px} {CY + 30.0})')
        lines.append(f'\t\t(property "Reference" "{pref}" (at 0 -3.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(property "Value" "PUMP_MOTOR" (at 0 3.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" thru_hole rect (at -1.25 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {out1} "") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" thru_hole oval (at 1.25 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net {out2} "") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # U9_SENS1 & U10_SENS2 (Pressure sensors)
    for sx, sref, sval in [(CX - 32.0, "U9_SENS1", "ABP2_015PG_CIS"), (CX + 32.0, "U10_SENS2", "ABP2_005PG_TRANS")]:
        lines.append(f'\t(footprint "Sensor_Pressure:Honeywell_ABP_SMD"')
        lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {sx} {CY})')
        lines.append(f'\t\t(property "Reference" "{sref}" (at 0 -5.0 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(property "Value" "{sval}" (at 0 5.0 0) (layer "F.Fab") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
        lines.append(f'\t\t(pad "1" smd rect (at -3.5 -2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "2" smd rect (at -3.5 0) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "3" smd rect (at -3.5 2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 21 "PRESS_I2C_SDA") (uuid "{gen_uuid()}"))')
        lines.append(f'\t\t(pad "4" smd rect (at 3.5 2.54) (size 1.5 0.8) (layers "F.Cu" "F.Paste" "F.Mask") (net 20 "PRESS_I2C_SCL") (uuid "{gen_uuid()}"))')
        lines.append('\t)')

    # J_SWD
    lines.append(f'\t(footprint "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"')
    lines.append(f'\t\t(layer "F.Cu") (uuid "{gen_uuid()}") (at {CX} {CY + 18.0})')
    lines.append(f'\t\t(property "Reference" "J_SWD" (at 0 -2.5 0) (layer "F.SilkS") (uuid "{gen_uuid()}") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'\t\t(pad "1" thru_hole rect (at -3.81 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 5 "+3V3") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "2" thru_hole oval (at -1.27 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 29 "SWDIO") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "3" thru_hole oval (at 1.27 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 30 "SWCLK") (uuid "{gen_uuid()}"))')
    lines.append(f'\t\t(pad "4" thru_hole oval (at 3.81 0) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask") (net 1 "GND") (uuid "{gen_uuid()}"))')
    lines.append('\t)')

    # Zones
    lines.append(f'\t(zone (net 1) (net_name "GND") (layer "In1.Cu") (uuid "{gen_uuid()}")')
    lines.append('\t\t(hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.2)')
    lines.append(f'\t\t(polygon (pts (xy {x1 + 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y2 - 0.5}) (xy {x1 + 0.5} {y2 - 0.5}))))')

    lines.append(f'\t(zone (net 4) (net_name "+5V_MR1_CLEAN") (layer "In2.Cu") (uuid "{gen_uuid()}")')
    lines.append('\t\t(hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.2)')
    lines.append(f'\t\t(polygon (pts (xy {x1 + 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y2 - 0.5}) (xy {x1 + 0.5} {y2 - 0.5}))))')

    lines.append(f'\t(zone (net 1) (net_name "GND") (layer "B.Cu") (uuid "{gen_uuid()}")')
    lines.append('\t\t(hatch edge 0.5) (connect_pads (clearance 0.2)) (min_thickness 0.2)')
    lines.append(f'\t\t(polygon (pts (xy {x1 + 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y1 + 0.5}) (xy {x2 - 0.5} {y2 - 0.5}) (xy {x1 + 0.5} {y2 - 0.5}))))')

    # Routing segments & vias
    routes = [
        # 1. GND via escapes to planes
        make_via(CX, CY, 0.6, 0.3, 1),
        make_via(CX - 1.2, CY - 1.2, 0.6, 0.3, 1),
        make_via(CX + 1.2, CY + 1.2, 0.6, 0.3, 1),
        make_seg(CX - 3.45, CY + 0.75, CX - 2.8, CY + 0.75, 0.25, "F.Cu", 1), # MCU Pin 8
        make_seg(CX + 2.25, CY + 3.45, CX + 2.25, CY + 2.8, 0.25, "F.Cu", 1), # MCU Pin 23
        make_seg(CX + 3.45, CY - 2.25, CX + 2.8, CY - 2.25, 0.25, "F.Cu", 1), # MCU Pin 35
        make_seg(CX - 2.25, CY - 3.45, CX - 2.25, CY - 2.8, 0.25, "F.Cu", 1), # MCU Pin 47
        make_via(CX - 6.0 + 0.48, CY - 3.5, 0.6, 0.3, 1), # C1_MCU
        make_via(CX - 6.0 + 0.48, CY + 3.5, 0.6, 0.3, 1), # C2_MCU
        make_via(CX + 6.0 + 0.48, CY - 3.5, 0.6, 0.3, 1), # C3_MCU
        make_via(CX + 6.0 + 0.48, CY + 3.5, 0.6, 0.3, 1), # C4_MCU
        make_via(CX - 8.5, CY - 1.35, 0.6, 0.3, 1), # U5_REG
        make_via(CX, CY - 22.0 - 1.35, 0.6, 0.3, 1), # U4_LDO
        make_via(CX - 18.0, CY - 22.0, 0.6, 0.3, 1), # U2_PD
        make_via(CX - 18.0 - 2.6, CY - 8.0 - 1.905, 0.6, 0.3, 1), # U3_BUCK
        make_via(CX, CY - 34.0 + 0.9, 0.6, 0.3, 1), # U6_MUX
        make_via(CX - 25.0, CY + 18.0, 0.6, 0.3, 1), # U7_DRV1
        make_via(CX + 25.0, CY + 18.0, 0.6, 0.3, 1), # U8_DRV2
        make_via(CX - 32.0 - 3.5, CY - 2.54, 0.6, 0.3, 1), # U9_SENS1
        make_via(CX + 32.0 - 3.5, CY - 2.54, 0.6, 0.3, 1), # U10_SENS2
        make_via(CX + 8.5 + 1.1, CY + 0.8, 0.6, 0.3, 1), # Y1_HSE Pin 2
        make_via(CX + 8.5 - 1.1, CY - 0.8, 0.6, 0.3, 1), # Y1_HSE Pin 4
        # USB-C GND connections to Shell
        make_seg(88.25, 57.70, 89.32, 61.30, 0.4, "F.Cu", 1), # J1 A1 -> SH1
        make_seg(81.75, 57.70, 80.68, 61.30, 0.4, "F.Cu", 1), # J1 A12 -> SH2
        make_seg(118.25, 57.70, 119.32, 61.30, 0.4, "F.Cu", 1), # J2 A1 -> SH1
        make_seg(111.75, 57.70, 110.68, 61.30, 0.4, "F.Cu", 1), # J2 A12 -> SH2

        # 2. +5V_MR1_CLEAN via drops to In2.Cu plane
        make_via(85.5, 93.905, 0.6, 0.3, 4), # U3_BUCK Pad 5
        make_seg(84.60, 93.905, 85.5, 93.905, 0.4, "F.Cu", 4),
        make_via(89.5, 98.65, 0.6, 0.3, 4), # U5_REG Pad 1
        make_seg(89.5, 98.65, 90.55, 98.65, 0.35, "F.Cu", 4),
        make_seg(90.55, 98.65, 92.45, 98.65, 0.35, "F.Cu", 4), # U5_REG Pad 1 -> Pad 3
        make_via(97.2, 76.65, 0.6, 0.3, 4), # U4_LDO Pad 1
        make_seg(98.10, 76.65, 97.2, 76.65, 0.35, "F.Cu", 4),
        make_via(112.55, 59.5, 0.6, 0.3, 4), # J2_MR1 A9
        make_via(117.45, 59.5, 0.6, 0.3, 4), # J2_MR1 A4
        make_seg(112.55, 57.70, 112.55, 59.5, 0.4, "F.Cu", 4),
        make_seg(117.45, 57.70, 117.45, 59.5, 0.4, "F.Cu", 4),

        # 3. +VBUS_PD (Net 2) - Route on B.Cu clearing U2_PD
        make_via(82.55, 59.5, 0.6, 0.3, 2), # J1 A9
        make_via(87.45, 59.5, 0.6, 0.3, 2), # J1 A4
        make_seg(82.55, 57.70, 82.55, 59.5, 0.4, "F.Cu", 2),
        make_seg(87.45, 57.70, 87.45, 59.5, 0.4, "F.Cu", 2),
        make_seg(82.55, 59.5, 87.45, 59.5, 0.5, "B.Cu", 2),
        make_seg(82.55, 59.5, 77.0, 59.5, 0.5, "B.Cu", 2),
        make_seg(77.0, 59.5, 77.0, 88.0, 0.5, "B.Cu", 2),
        make_seg(77.0, 88.0, 79.40, 91.365, 0.5, "B.Cu", 2),
        make_via(79.40, 91.365, 0.6, 0.3, 2), # U3_BUCK Pad 2 via to B.Cu

        # 4. USB High-Speed Diff Pairs to U6_MUX (Clean orthogonal, uncrossed)
        make_seg(85.25, 57.70, 85.25, 63.2, 0.25, "F.Cu", 6), # J1 D+
        make_seg(85.25, 63.2, 99.325, 63.2, 0.25, "F.Cu", 6),
        make_seg(99.325, 63.2, 99.325, 65.25, 0.25, "F.Cu", 6),
        make_seg(84.75, 57.70, 84.75, 64.0, 0.25, "F.Cu", 7), # J1 D-
        make_seg(84.75, 64.0, 98.2, 64.0, 0.25, "F.Cu", 7),
        make_seg(98.2, 64.0, 98.2, 65.75, 0.25, "F.Cu", 7),
        make_seg(98.2, 65.75, 99.325, 65.75, 0.25, "F.Cu", 7),

        make_seg(115.25, 57.70, 115.25, 63.2, 0.25, "F.Cu", 8), # J2 D+
        make_seg(115.25, 63.2, 100.675, 63.2, 0.25, "F.Cu", 8),
        make_seg(100.675, 63.2, 100.675, 65.25, 0.25, "F.Cu", 8),
        make_seg(114.75, 57.70, 114.75, 64.0, 0.25, "F.Cu", 9), # J2 D-
        make_seg(114.75, 64.0, 101.5, 64.0, 0.25, "F.Cu", 9),
        make_seg(101.5, 64.0, 101.5, 65.75, 0.25, "F.Cu", 9),
        make_seg(101.5, 65.75, 100.675, 65.75, 0.25, "F.Cu", 9),

        # 5. +3V3 Power Distribution
        make_seg(99.05, 79.35, 99.05, 91.0, 0.4, "F.Cu", 5), # U4_LDO Pad 5 -> Pull-up bus
        make_seg(92.02, 91.0, 107.02, 91.0, 0.35, "F.Cu", 5), # R1_PU..R4_PU bus
        make_seg(92.02, 91.0, 92.02, 92.0, 0.25, "F.Cu", 5),
        make_seg(95.02, 91.0, 95.02, 92.0, 0.25, "F.Cu", 5),
        make_seg(104.02, 91.0, 104.02, 92.0, 0.25, "F.Cu", 5),
        make_seg(107.02, 91.0, 107.02, 92.0, 0.25, "F.Cu", 5),

        # MCU Pin 48 (97.25, 96.55) to 3V3 bus
        make_seg(97.25, 91.0, 97.25, 96.55, 0.35, "F.Cu", 5),
        make_seg(97.25, 91.0, 104.5, 91.0, 0.35, "F.Cu", 5),
        make_seg(104.5, 91.0, 104.5, 96.50, 0.25, "F.Cu", 5), # -> MCU Pin 36 area

        # MCU Pin 36 (103.45, 97.25) -> C3_MCU
        make_seg(103.45, 97.25, 104.5, 97.25, 0.25, "F.Cu", 5),
        make_seg(104.5, 97.25, 104.5, 96.50, 0.25, "F.Cu", 5),
        make_seg(104.5, 96.50, 105.52, 96.50, 0.25, "F.Cu", 5), # C3_MCU Pad 1
        make_via(104.5, 96.50, 0.6, 0.3, 5), # Via to B.Cu

        # MCU Pin 9 (96.55, 101.25) -> C1_MCU, C2_MCU, U5_REG
        make_seg(96.55, 101.25, 94.5, 101.25, 0.25, "F.Cu", 5),
        make_seg(94.5, 101.25, 94.5, 96.50, 0.25, "F.Cu", 5),
        make_seg(94.5, 96.50, 93.52, 96.50, 0.25, "F.Cu", 5), # C1_MCU Pad 1
        make_seg(94.5, 101.25, 94.5, 103.50, 0.25, "F.Cu", 5),
        make_seg(94.5, 103.50, 93.52, 103.50, 0.25, "F.Cu", 5), # C2_MCU Pad 1
        make_seg(94.5, 101.25, 90.55 - 0.95, 101.35, 0.25, "F.Cu", 5), # U5_REG Pad 5
        make_via(94.5, 101.25, 0.6, 0.3, 5), # Via to B.Cu

        # MCU Pin 24 (102.75, 103.45) -> C4_MCU & J_SWD
        make_seg(102.75, 103.45, 104.5, 103.45, 0.25, "F.Cu", 5),
        make_seg(104.5, 103.45, 105.52, 103.50, 0.25, "F.Cu", 5), # C4_MCU Pad 1
        make_via(104.5, 103.45, 0.6, 0.3, 5),
        make_seg(104.5, 103.45, 104.5, 96.50, 0.3, "B.Cu", 5), # Connect Pin 24 to Pin 36 on B.Cu
        make_seg(104.5, 103.45, 96.19, 116.5, 0.3, "B.Cu", 5), # -> J_SWD Pad 1
        make_seg(96.19, 116.5, 96.19, 118.0, 0.3, "F.Cu", 5),
        make_via(96.19, 116.5, 0.6, 0.3, 5),

        # +3V3 to Sensors on B.Cu
        make_via(64.5, 98.0, 0.6, 0.3, 5),
        make_seg(94.5, 101.25, 64.5, 98.0, 0.35, "B.Cu", 5),
        make_seg(64.5, 98.0, 64.5, 100.0, 0.35, "F.Cu", 5), # U9_SENS1 Pad 2

        make_via(128.5, 98.0, 0.6, 0.3, 5),
        make_seg(104.5, 96.50, 128.5, 98.0, 0.35, "B.Cu", 5),
        make_seg(128.5, 98.0, 128.5, 100.0, 0.35, "F.Cu", 5), # U10_SENS2 Pad 2

        # 6. VMOTOR (Net 3) on B.Cu - Routed clear of J_SWD
        make_via(74.05 - 1.0, 117.25, 0.6, 0.3, 3),
        make_via(124.05 - 1.0, 117.25, 0.6, 0.3, 3),
        make_seg(74.05, 117.25, 74.05 - 1.0, 117.25, 0.5, "F.Cu", 3),
        make_seg(124.05, 117.25, 124.05 - 1.0, 117.25, 0.5, "F.Cu", 3),
        make_seg(74.05 - 1.0, 117.25, 74.05 - 1.0, 122.0, 0.6, "B.Cu", 3),
        make_seg(74.05 - 1.0, 122.0, 124.05 - 1.0, 122.0, 0.6, "B.Cu", 3),
        make_seg(124.05 - 1.0, 122.0, 124.05 - 1.0, 117.25, 0.6, "B.Cu", 3),

        # 7. I2C Lines on B.Cu (Y = 107.0, 108.5)
        make_via(71.5, 107.0, 0.6, 0.3, 20),
        make_via(135.5, 107.0, 0.6, 0.3, 20),
        make_seg(71.5, 102.54, 71.5, 107.0, 0.25, "F.Cu", 20),
        make_seg(135.5, 102.54, 135.5, 107.0, 0.25, "F.Cu", 20),
        make_seg(71.5, 107.0, 135.5, 107.0, 0.25, "B.Cu", 20),

        make_via(64.5, 108.5, 0.6, 0.3, 21),
        make_via(128.5, 108.5, 0.6, 0.3, 21),
        make_seg(64.5, 102.54, 64.5, 108.5, 0.25, "F.Cu", 21),
        make_seg(128.5, 102.54, 128.5, 108.5, 0.25, "F.Cu", 21),
        make_seg(64.5, 108.5, 128.5, 108.5, 0.25, "B.Cu", 21),
    ]
    for r in routes:
        lines.append(r)

    lines.append(')')
    lines.append('')
    return '\n'.join(lines)


def generate_pcb():
    """Back-compat alias used by tests and export tooling."""
    return generate_pump_clean()


if __name__ == '__main__':
    out_path = Path(__file__).resolve().parent.parent / "Pump" / "Pump.kicad_pcb"
    content = generate_pcb()
    out_path.write_text(content, encoding='utf-8')
    print(f"Generated {out_path} ({len(content)} bytes)")
