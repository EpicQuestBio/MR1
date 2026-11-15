# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# SPDX-License-Identifier: CC0-1.0

import os
import sys

def update_amplifier_schematic():
    sch_path = "Amplifier/Amplifier.kicad_sch"
    with open(sch_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find lib_symbol ADR4525
    start_lib = None
    end_lib = None
    for i, line in enumerate(lines):
        if '(symbol "Reference_Voltage:ADR4525"' in line:
            start_lib = i
        if start_lib is not None and '(symbol "Regulator_Linear:LP5907MFX-1.8"' in line:
            end_lib = i
            break

    assert start_lib is not None and end_lib is not None, "Could not locate ADR4525 lib_symbol bounds"

    new_lib_sym = """\t\t(symbol "Reference_Voltage:MAX6070BAUT25+T"
\t\t\t(pin_names
\t\t\t\t(offset 1.016)
\t\t\t)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(in_pos_files yes)
\t\t\t(duplicate_pin_numbers_are_jumpers no)
\t\t\t(property "Reference" "U"
\t\t\t\t(at 1.27 8.89 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t\t(justify left)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Value" "MAX6070BAUT25+T"
\t\t\t\t(at 1.27 6.35 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t\t(justify left)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t\t(at 1.27 -7.62 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t\t(justify left)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Datasheet" "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6070-MAX6071.pdf"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "Description" "Low-Noise, High-Precision Series Voltage Reference, 2.5V, ±0.08%, SOT-23-6"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "ki_keywords" "Low Noise Precision Voltage Reference"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(property "ki_fp_filters" "SOT?23*"
\t\t\t\t(at 0 0 0)
\t\t\t\t(show_name no)
\t\t\t\t(do_not_autoplace no)
\t\t\t\t(hide yes)
\t\t\t\t(effects
\t\t\t\t\t(font
\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "MAX6070BAUT25+T_0_1"
\t\t\t\t(rectangle
\t\t\t\t\t(start -7.62 5.08)
\t\t\t\t\t(end 7.62 -5.08)
\t\t\t\t\t(stroke
\t\t\t\t\t\t(width 0.254)
\t\t\t\t\t\t(type solid)
\t\t\t\t\t)
\t\t\t\t\t(fill
\t\t\t\t\t\t(type background)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "MAX6070BAUT25+T_1_1"
\t\t\t\t(pin passive line
\t\t\t\t\t(at -10.16 -2.54 0)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "FILTER"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "1"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin power_in line
\t\t\t\t\t(at 0 -7.62 90)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "GND"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "2"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin input line
\t\t\t\t\t(at -10.16 2.54 0)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "EN"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "3"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin power_in line
\t\t\t\t\t(at 0 7.62 270)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "VIN"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "4"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin input line
\t\t\t\t\t(at 10.16 -2.54 180)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "OUTS"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "5"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t\t(pin output line
\t\t\t\t\t(at 10.16 2.54 180)
\t\t\t\t\t(length 2.54)
\t\t\t\t\t(name "OUTF"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t\t(number "6"
\t\t\t\t\t\t(effects
\t\t\t\t\t\t\t(font
\t\t\t\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t\t\t\t)
\t\t\t\t\t\t)
\t\t\t\t\t)
\t\t\t\t)
\t\t\t)
\t\t\t(embedded_fonts no)
\t\t)\n"""

    # Replace lib_symbol
    lines[start_lib:end_lib] = [new_lib_sym]

    # Re-find instance bounds
    start_inst = None
    end_inst = None
    for i, line in enumerate(lines):
        if '(lib_id "Reference_Voltage:ADR4525")' in line:
            # backtrack to "(symbol"
            j = i
            while j >= 0 and not lines[j].strip().startswith('(symbol'):
                j -= 1
            start_inst = j
            # find end of instance
            k = start_inst
            depth = 0
            while k < len(lines):
                depth += lines[k].count('(') - lines[k].count(')')
                if depth == 0:
                    end_inst = k + 1
                    break
                k += 1
            break

    assert start_inst is not None and end_inst is not None, "Could not locate U18 instance bounds"

    new_inst = """\t(symbol
\t\t(lib_id "Reference_Voltage:MAX6070BAUT25+T")
\t\t(at 173.99 -17.78 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "562c394a-f2d2-44f4-9b57-ebd6405e749f")
\t\t(property "Reference" "U18"
\t\t\t(at 175.26 -26.67 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "MAX6070BAUT25+T"
\t\t\t(at 175.26 -24.13 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23-6"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6070-MAX6071.pdf"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" "Low-Noise, High-Precision Series Voltage Reference, 2.5V, ±0.08%, SOT-23-6"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "LCSC" "C138814"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "MPN" "MAX6070BAUT25+T"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Mouser PN" "700-MAX6070BAUT25+T"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Manufacturer" "Analog Devices / Maxim Integrated"
\t\t\t(at 173.99 -17.78 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pin "1"
\t\t\t(uuid "4f9e91cd-37a7-44a0-9c50-c7a5f898186d")
\t\t)
\t\t(pin "2"
\t\t\t(uuid "caed0837-d94e-4551-a271-afcaa97bf058")
\t\t)
\t\t(pin "3"
\t\t\t(uuid "42fecfc4-3238-4ac2-9753-949af194316e")
\t\t)
\t\t(pin "4"
\t\t\t(uuid "e8c9ccf6-5eb8-48fc-a856-3cbb2c05de30")
\t\t)
\t\t(pin "5"
\t\t\t(uuid "28319508-15d8-4133-93f8-ddd8fb98961d")
\t\t)
\t\t(pin "6"
\t\t\t(uuid "a60fe23a-ae42-49fa-a34d-6322d04fc016")
\t\t)
\t\t(instances
\t\t\t(project "Amplifier"
\t\t\t\t(path "/0fac162c-ca5e-4358-934a-30718aa12176"
\t\t\t\t\t(reference "U18")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
\t(symbol
\t\t(lib_id "Device:C_Small")
\t\t(at 156.21 -12.7 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(uuid "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d")
\t\t(property "Reference" "C44"
\t\t\t(at 158.75 -13.97 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "100n"
\t\t\t(at 158.75 -11.43 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" "Capacitor_SMD:C_0402_1005Metric"
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" "Capacitor, 0.1uF, 50V, X7R, 0402, MAX6070 noise filter"
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "LCSC" "C15255"
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "MPN" "0402B104K500NT"
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Mouser PN" "581-04025C104KAT2A"
\t\t\t(at 156.21 -12.7 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pin "1"
\t\t\t(uuid "b2c3d4e5-f6a1-4b2c-9d3e-4f5a6b7c8d9e")
\t\t)
\t\t(pin "2"
\t\t\t(uuid "c3d4e5f6-a1b2-4c3d-ae4f-5a6b7c8d9e0f")
\t\t)
\t\t(instances
\t\t\t(project "Amplifier"
\t\t\t\t(path "/0fac162c-ca5e-4358-934a-30718aa12176"
\t\t\t\t\t(reference "C44")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)
\t(symbol
\t\t(lib_id "power:GNDA")
\t\t(at 156.21 -10.16 0)
\t\t(unit 1)
\t\t(body_style 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(in_pos_files yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(uuid "d4e5f6a1-b2c3-4d4e-bf5a-6b7c8d9e0f1a")
\t\t(property "Reference" "#PWR0132"
\t\t\t(at 156.21 -3.81 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Value" "GNDA"
\t\t\t(at 156.21 -4.445 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at 156.21 -10.16 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at 156.21 -10.16 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(property "Description" "Power symbol creates a global label with name \\\"GNDA\\\" , analog ground"
\t\t\t(at 156.21 -10.16 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
\t\t(pin "1"
\t\t\t(uuid "e5f6a1b2-c3d4-4e5f-c06b-7c8d9e0f1a2b")
\t\t)
\t\t(instances
\t\t\t(project "Amplifier"
\t\t\t\t(path "/0fac162c-ca5e-4358-934a-30718aa12176"
\t\t\t\t\t(reference "#PWR0132")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)\n"""

    lines[start_inst:end_inst] = [new_inst]

    full_text = "".join(lines)

    # 3. New Wires & Junctions
    old_wire = """\t(wire
\t\t(pts
\t\t\t(xy 167.64 -25.4) (xy 160.02 -25.4)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "b219db5b-97fa-409c-b67c-973503be8612")
\t)"""

    new_wires = """\t(wire
\t\t(pts
\t\t\t(xy 160.02 -25.4) (xy 163.83 -25.4)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "b219db5b-97fa-409c-b67c-973503be8612")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 163.83 -25.4) (xy 167.64 -25.4)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "f1a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c")
\t)
\t(junction
\t\t(at 163.83 -25.4)
\t\t(diameter 1.016)
\t\t(color 0 0 0 0)
\t\t(uuid "a2b3c4d5-e6f7-4a8b-9c0d-1e2f3a4b5c6d")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 163.83 -25.4) (xy 163.83 -20.32)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "b3c4d5e6-f7a8-4b9c-0d1e-2f3a4b5c6d7e")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 184.15 -20.32) (xy 184.15 -17.78)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "c4d5e6f7-a8b9-4c0d-1e2f-3a4b5c6d7e8f")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 184.15 -17.78) (xy 184.15 -15.24)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "d5e6f7a8-b9c0-4d1e-2f3a-4b5c6d7e8f9a")
\t)
\t(junction
\t\t(at 184.15 -17.78)
\t\t(diameter 1.016)
\t\t(color 0 0 0 0)
\t\t(uuid "e6f7a8b9-c0d1-4e2f-3a4b-5c6d7e8f9a0b")
\t)
\t(wire
\t\t(pts
\t\t\t(xy 156.21 -15.24) (xy 163.83 -15.24)
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "f7a8b9c0-d1e2-4f3a-4b5c-6d7e8f9a0b1c")
\t)"""

    assert old_wire in full_text, "old_wire not found in text"
    full_text = full_text.replace(old_wire, new_wires)

    with open(sch_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print("Amplifier.kicad_sch updated successfully.")

if __name__ == "__main__":
    update_amplifier_schematic()
