# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# SPDX-License-Identifier: CC0-1.0

import os
import re
import subprocess

def update_footprint_at(txt, ref, new_at):
    ref_str = f"\"Reference\" \"{ref}\""
    idx = txt.find(ref_str)
    if idx == -1:
        raise ValueError(f"Reference {ref} not found")
    fp_start = txt.rfind("(footprint ", 0, idx)
    at_match = re.search(r"\(at ([-\d\.]+)\s+([-\d\.]+)(?: ([\d\.]+))?\)", txt[fp_start:idx])
    if not at_match:
        raise ValueError(f"No at match for {ref}")
    old_at_span = (fp_start + at_match.start(), fp_start + at_match.end())
    return txt[:old_at_span[0]] + new_at + txt[old_at_span[1]:]

def remove_element_by_uuid(txt, u):
    idx = txt.find(f"\"{u}\"")
    if idx == -1:
        return txt, False
    start = txt.rfind("\n\t(segment", 0, idx)
    if start == -1:
        start = txt.rfind("\n\t(via", 0, idx)
    end = txt.find("\n\t)", idx) + 3
    return txt[:start] + txt[end:], True

def update_via(txt, uuid, new_x, new_y, new_net):
    idx = txt.find(f'"{uuid}"')
    if idx == -1:
        return txt, False
    start = txt.rfind("(via", 0, idx)
    end = txt.find("\n\t)", idx)
    snippet = txt[start:end]
    snippet = re.sub(r'\(at\s+[-0-9.]+\s+[-0-9.]+\)', f'(at {new_x:.4f} {new_y:.4f})', snippet)
    snippet = re.sub(r'\(net\s+"[^"]+"\)', f'(net "{new_net}")', snippet)
    return txt[:start] + snippet + txt[end:], True

def build_via(x, y, net, uuid_str, size=0.5, drill=0.3):
    return f"""\t(via
\t\t(at {x:.4f} {y:.4f})
\t\t(size {size})
\t\t(drill {drill})
\t\t(layers "F.Cu" "B.Cu")
\t\t(net "{net}")
\t\t(uuid "{uuid_str}")
\t)"""

def build_segment(x1, y1, x2, y2, layer, net, uuid_str, width=0.15):
    return f"""\t(segment
\t\t(start {x1:.4f} {y1:.4f})
\t\t(end {x2:.4f} {y2:.4f})
\t\t(width {width})
\t\t(layer "{layer}")
\t\t(net "{net}")
\t\t(uuid "{uuid_str}")
\t)"""

def main():
    pcb_path = "MR1/MR1.kicad_pcb"
    subprocess.run(["git", "checkout", pcb_path], check=True)

    with open(pcb_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Remove legacy shorting segments
    uuids_to_remove = [
        "af363a56-98bd-4c4d-954e-dd0da69c1fc9", # U13 pad 2 short to VDDA
        "51cc66e2-d6a0-4ee4-9647-627546769dfc", # U13 to U3 track on VDDA
        "cf9c666c-eb62-42d7-a337-e1895a164741", # C24 pad 1 short to U3B--
        "ee198f29-8f36-436d-be1d-054fa38a0882", # C24 pad 1 short to U3B--
        "4ff2a2e6-4c2d-4f39-82f3-a9fcda8f8124", # +Vp_cm F.Cu bottleneck above U1 pad 12
        "fea49921-fab0-4282-bf68-1ca73f83ee3f", # diagonal Net-(D1-K) track crossing +Vp_cm corridor
        "7ca4631a-5d01-4ffa-a72c-0b3053b798d3", # Dangling via Net-(U3B--) @ (65.95, 63.50) colliding with U13-OUT
    ]
    for u in uuids_to_remove:
        text, ok = remove_element_by_uuid(text, u)

    # 2. Update isolated GND stitching vias in GNDA power region to GNDA and clear PG_VSSA corridor
    text, ok = update_via(text, "5a20826b-9b73-405e-929d-8371b480645e", 73.80, 78.8756, "GNDA")
    text, ok = update_via(text, "79d91556-ab7c-4ee1-8819-2bd1bf5f0ab0", 73.80, 80.3000, "GNDA")
    text, ok = update_via(text, "d5248ed1-d9c6-4128-85b1-0373327484ba", 73.80, 81.8256, "GNDA")
    text, ok = update_via(text, "1e396fd1-a3cb-4e11-91f2-31da327b8601", 81.80, 82.1000, "GNDA")

    # 3. Relocate unplaced components
    # R49: South of C40 in empty margin, horizontal (rot=180)
    text = update_footprint_at(text, "R49", "(at 76.0 89.2 180)")
    
    # R50: East of Q1 at (81.5, 75.5, rot=90)
    text = update_footprint_at(text, "R50", "(at 81.5 75.5 90)")
    
    # R22: at (67.1 65.04 90)
    text = update_footprint_at(text, "R22", "(at 67.1 65.04 90)")

    # Eastern margin pull-ups (Y=86.0, rot=270):
    text = update_footprint_at(text, "R44", "(at 81.5 86.0 270)")
    text = update_footprint_at(text, "R45", "(at 83.0 86.0 270)")
    text = update_footprint_at(text, "R46", "(at 84.5 86.0 270)")

    # Damping resistors directly below pull-ups (Y=88.2, rot=270):
    text = update_footprint_at(text, "R59", "(at 81.5 88.2 270)")
    text = update_footprint_at(text, "R58", "(at 83.0 88.2 270)")
    text = update_footprint_at(text, "R57", "(at 84.5 88.2 270)")

    # 3.5 Specific DRC corrections
    # A. Fix C14 pad 2 starved thermal relief by setting solid connection (zone_connect 1)
    c14_pad2_target = '(net "GNDA")\n\t\t\t(pintype "passive")\n\t\t\t(uuid "3a37d980-f2e7-4f03-af22-848d04068716")'
    c14_pad2_replacement = '(net "GNDA")\n\t\t\t(pintype "passive")\n\t\t\t(zone_connect 1)\n\t\t\t(uuid "3a37d980-f2e7-4f03-af22-848d04068716")'
    if c14_pad2_target in text:
        text = text.replace(c14_pad2_target, c14_pad2_replacement)

    # B. Relocate GNDA stitching via at (69.70, 55.55) to (69.70, 55.00) to clear hole-to-hole spacing
    via_5555_target = '(at 69.7 55.55)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(free yes)\n\t\t(net "GNDA")'
    via_5555_replacement = '(at 69.7 55.0)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(free yes)\n\t\t(net "GNDA")'
    if via_5555_target in text:
        text = text.replace(via_5555_target, via_5555_replacement)

    # C. Nudge track /Power/+Vp 0.05 mm south to clear U4 Pad 3
    track_vp_target1 = '(start 71.131081 84.45)\n\t\t(end 73.45 84.45)'
    track_vp_replacement1 = '(start 71.131081 84.5)\n\t\t(end 73.45 84.5)'
    track_vp_target2 = '(start 73.45 84.45)\n\t\t(end 73.65 84.65)'
    track_vp_replacement2 = '(start 73.45 84.5)\n\t\t(end 73.65 84.65)'
    if track_vp_target1 in text:
        text = text.replace(track_vp_target1, track_vp_replacement1)
    if track_vp_target2 in text:
        text = text.replace(track_vp_target2, track_vp_replacement2)

    # D. Connect +Vp_cm F.Cu trace to relocated via at (78.00, 82.15)
    seg_vpcm_target = '(start 79.29 83.5)\n\t\t(end 77.715 81.925)'
    seg_vpcm_replacement = '(start 79.29 83.5)\n\t\t(end 78.65 82.8)\n\t)\n\t(segment\n\t\t(start 78.65 82.8)\n\t\t(end 78 82.15)'
    if seg_vpcm_target in text:
        text = text.replace(seg_vpcm_target, seg_vpcm_replacement)

    # 4. Routing elements
    elements = []
    e_idx = 100

    def get_id():
        nonlocal e_idx
        e_idx += 1
        return f"b0b0b0b0-cccc-dddd-eeee-{e_idx:012d}"

    # A. C33 & NT2 GND connections
    elements.append(build_via(70.89, 66.6, "GND", get_id()))
    elements.append(build_segment(70.89, 65.4556, 70.89, 66.6, "F.Cu", "GND", get_id(), width=0.25))
    elements.append(build_segment(70.89, 66.6, 72.0, 66.6, "B.Cu", "GND", get_id(), width=0.25))
    elements.append(build_segment(72.0, 66.6, 72.0, 64.0256, "B.Cu", "GND", get_id(), width=0.25))
    elements.append(build_via(72.0, 64.0256, "GND", get_id()))
    elements.append(build_segment(71.95, 64.0256, 72.0, 64.0256, "F.Cu", "GND", get_id(), width=0.25))

    # B. U13 pin 8 (+3V3) connection (drops west to X=62.50 to clear Net-(U13-OUT) on B.Cu)
    elements.append(build_segment(63.775, 59.585, 62.50, 59.585, "F.Cu", "+3V3", get_id(), width=0.2))
    elements.append(build_via(62.50, 59.585, "+3V3", get_id()))
    elements.append(build_segment(62.50, 59.585, 62.50, 68.50, "B.Cu", "+3V3", get_id(), width=0.25))
    elements.append(build_segment(62.50, 68.50, 74.287685, 68.50, "B.Cu", "+3V3", get_id(), width=0.25))
    elements.append(build_segment(74.287685, 68.50, 74.287685, 66.195, "B.Cu", "+3V3", get_id(), width=0.25))

    # C. C24 & R35 connection on Net-(C24-Pad1)
    elements.append(build_segment(65.0, 64.37, 65.5, 64.87, "F.Cu", "Net-(C24-Pad1)", get_id()))
    elements.append(build_segment(65.5, 64.87, 66.05, 65.23, "F.Cu", "Net-(C24-Pad1)", get_id()))

    # D. Net-(U3B--): U3 pad 6 (66.5365, 61.898) connects south to (65.80, 64.53) on F.Cu clearing Pad 5 and Via U13-OUT
    elements.append(build_segment(66.5365, 61.898, 66.5365, 62.75, "F.Cu", "Net-(U3B--)", get_id(), width=0.15))
    elements.append(build_segment(66.5365, 62.75, 65.80, 63.4865, "F.Cu", "Net-(U3B--)", get_id(), width=0.15))
    elements.append(build_segment(65.80, 63.4865, 65.80, 64.53, "F.Cu", "Net-(U3B--)", get_id(), width=0.15))
    # Connect (65.80, 64.53) to R22 pad 2 (67.10, 64.53) on F.Cu: route east
    elements.append(build_segment(65.80, 64.53, 67.10, 64.53, "F.Cu", "Net-(U3B--)", get_id(), width=0.15))
    # Connect R13 pad 1 (65.06, 65.34) via B.Cu jumper to via (65.20, 63.41):
    elements.append(build_segment(65.06, 65.34, 65.20, 65.40, "F.Cu", "Net-(U3B--)", get_id(), width=0.15))
    elements.append(build_via(65.20, 65.40, "Net-(U3B--)", get_id()))
    elements.append(build_segment(65.20, 65.40, 65.20, 63.41, "B.Cu", "Net-(U3B--)", get_id(), width=0.15))
    elements.append(build_via(65.20, 63.41, "Net-(U3B--)", get_id()))

    # E. Net-(U13-OUT): C26 pad 1 connection via clean B.Cu jumper
    elements.append(build_via(63.30, 62.00, "Net-(U13-OUT)", get_id()))
    elements.append(build_segment(63.30, 62.00, 63.30, 61.20, "B.Cu", "Net-(U13-OUT)", get_id(), width=0.15))
    elements.append(build_segment(63.30, 61.20, 66.50, 61.20, "B.Cu", "Net-(U13-OUT)", get_id(), width=0.15))
    elements.append(build_segment(66.50, 61.20, 66.50, 63.59, "B.Cu", "Net-(U13-OUT)", get_id(), width=0.15))
    elements.append(build_via(66.50, 63.59, "Net-(U13-OUT)", get_id()))
    elements.append(build_segment(66.50, 63.59, 67.07, 63.59, "F.Cu", "Net-(U13-OUT)", get_id(), width=0.15))

    # F. U4 pin 4 (/Power/+Vp) connects on F.Cu at X=72.25 clearing R19 pad 1
    elements.append(build_segment(71.1055, 83.5256, 72.25, 83.5256, "F.Cu", "/Power/+Vp", get_id(), width=0.15))
    elements.append(build_segment(72.25, 83.5256, 72.25, 82.50, "F.Cu", "/Power/+Vp", get_id(), width=0.15))
    elements.append(build_segment(72.25, 82.50, 72.10, 82.50, "F.Cu", "/Power/+Vp", get_id(), width=0.15))

    # G. U4 pin 11 (VDDA)
    elements.append(build_segment(68.2555, 84.5256, 68.2305, 84.9006, "F.Cu", "VDDA", get_id()))

    # H. R49 connections and Net-(D1-K) clean jumper:
    # 1. R49 Pad 2 (Net-(D1-K)) at (75.49, 89.2) connects straight north on F.Cu to C40 pad 1 at (75.425, 86.90):
    elements.append(build_segment(75.49, 89.20, 75.425, 86.90, "F.Cu", "Net-(D1-K)", get_id(), width=0.15))

    # 2. Net-(D1-K) B.Cu jumper to connect C40 pad 1 to Q2 pad 1:
    elements.append(build_segment(75.425, 86.90, 75.425, 85.80, "F.Cu", "Net-(D1-K)", get_id(), width=0.15))
    elements.append(build_via(75.425, 85.80, "Net-(D1-K)", get_id()))
    elements.append(build_segment(75.425, 85.80, 77.325, 85.80, "B.Cu", "Net-(D1-K)", get_id(), width=0.15))
    elements.append(build_via(77.325, 85.80, "Net-(D1-K)", get_id()))
    elements.append(build_segment(77.325, 85.80, 77.4875, 85.00, "F.Cu", "Net-(D1-K)", get_id(), width=0.15))

    # 3. R49 Pad 1 (/Power/+Vp_cm) at (76.51, 89.20) connects straight north on F.Cu at X=76.45:
    elements.append(build_segment(76.51, 89.20, 76.45, 89.20, "F.Cu", "/Power/+Vp_cm", get_id(), width=0.15))
    elements.append(build_segment(76.45, 89.20, 76.45, 84.05, "F.Cu", "/Power/+Vp_cm", get_id(), width=0.15))

    # I. R50 connections on F.Cu:
    # Pad 1 connects to Q1 pad 3 at (79.688, 75.80):
    elements.append(build_segment(81.5, 75.98, 79.868, 75.98, "F.Cu", "/Power/-Vp_cm", get_id(), width=0.2))
    elements.append(build_segment(79.868, 75.98, 79.688, 75.80, "F.Cu", "/Power/-Vp_cm", get_id(), width=0.2))
    # Pad 2 connects to Net-(D2-A) track at (79.475, 74.05):
    elements.append(build_segment(81.5, 75.02, 80.445, 75.02, "F.Cu", "Net-(D2-A)", get_id(), width=0.2))
    elements.append(build_segment(80.445, 75.02, 79.475, 74.05, "F.Cu", "Net-(D2-A)", get_id(), width=0.2))

    # J. J7 shield mounting pads (/Insturmentation/SHIELD)
    elements.append(build_segment(74.4754, 67.8, 76.5, 67.8, "F.Cu", "/Insturmentation/SHIELD", get_id()))
    elements.append(build_via(76.5, 67.8, "/Insturmentation/SHIELD", get_id()))
    elements.append(build_segment(76.5, 67.8, 76.5, 56.8, "B.Cu", "/Insturmentation/SHIELD", get_id()))
    elements.append(build_via(76.5, 56.8, "/Insturmentation/SHIELD", get_id()))
    elements.append(build_segment(76.5, 56.8, 74.4754, 56.8, "F.Cu", "/Insturmentation/SHIELD", get_id()))

    # K. U2 pin 7 to R20 pad 1 (/Power/-VIOC) via clean B.Cu jumper bypassing south of U2 at Y=75.20
    elements.append(build_segment(68.775, 77.685, 67.90, 76.50, "F.Cu", "/Power/-VIOC", get_id(), width=0.15))
    elements.append(build_via(67.90, 76.50, "/Power/-VIOC", get_id()))
    elements.append(build_segment(67.90, 76.50, 67.90, 75.20, "B.Cu", "/Power/-VIOC", get_id(), width=0.15))
    elements.append(build_segment(67.90, 75.20, 76.19, 75.20, "B.Cu", "/Power/-VIOC", get_id(), width=0.15))
    elements.append(build_segment(76.19, 75.20, 76.19, 77.50, "B.Cu", "/Power/-VIOC", get_id(), width=0.15))
    elements.append(build_via(76.19, 77.50, "/Power/-VIOC", get_id()))
    elements.append(build_segment(76.19, 77.50, 76.19, 77.985, "F.Cu", "/Power/-VIOC", get_id(), width=0.15))

    # L. +3V3 pull-up bus: runs on F.Cu at Y=85.49 across X=[81.5, 85.0]
    elements.append(build_segment(81.50, 85.49, 85.00, 85.49, "F.Cu", "+3V3", get_id(), width=0.2))
    elements.append(build_via(85.00, 85.49, "+3V3", get_id()))

    # M. Pull-up to Damping resistor vertical ties
    elements.append(build_segment(81.5, 86.51, 81.5, 87.69, "F.Cu", "/Power/PG_CP", get_id()))
    elements.append(build_segment(83.0, 86.51, 83.0, 87.69, "F.Cu", "/Power/PG_VDDA", get_id()))
    elements.append(build_segment(84.5, 86.51, 84.5, 87.69, "F.Cu", "/Power/PG_VSSA", get_id()))

    # N. Power Good sources into pull-ups
    # 1. PG_CP: from (81.6555, 81.2811) on F.Cu -> via at (82.40, 84.95) -> hops to (81.50, 86.51) on B.Cu directly into R44 Pad 2 via
    elements.append(build_segment(81.6555, 81.2811, 82.40, 81.2811, "F.Cu", "/Power/PG_CP", get_id(), width=0.15))
    elements.append(build_segment(82.40, 81.2811, 82.40, 84.95, "F.Cu", "/Power/PG_CP", get_id(), width=0.15))
    elements.append(build_via(82.40, 84.95, "/Power/PG_CP", get_id()))
    elements.append(build_segment(82.40, 84.95, 81.50, 86.51, "B.Cu", "/Power/PG_CP", get_id(), width=0.15))
    elements.append(build_via(81.50, 86.51, "/Power/PG_CP", get_id()))

    # 2. PG_VDDA: U4 pin 5 (71.1055, 83.0256) -> via (71.68, 83.0256) -> B.Cu (X=71.68 south to Y=84.40) -> east along Y=84.40 to (83.00, 84.40) -> (83.00, 86.51) into R45 Pad 2
    elements.append(build_segment(71.1055, 83.0256, 71.68, 83.0256, "F.Cu", "/Power/PG_VDDA", get_id(), width=0.15))
    elements.append(build_via(71.68, 83.0256, "/Power/PG_VDDA", get_id()))
    elements.append(build_segment(71.68, 83.0256, 71.68, 84.40, "B.Cu", "/Power/PG_VDDA", get_id(), width=0.15))
    elements.append(build_segment(71.68, 84.40, 83.00, 84.40, "B.Cu", "/Power/PG_VDDA", get_id(), width=0.15))
    elements.append(build_segment(83.00, 84.40, 83.00, 86.51, "B.Cu", "/Power/PG_VDDA", get_id(), width=0.15))
    elements.append(build_via(83.00, 86.51, "/Power/PG_VDDA", get_id()))

    # 3. PG_VSSA: from U2 pin 4 (71.675, 78.585) -> via (73.00, 78.75) -> south along X=73.00 to Y=83.355 (clears shifted GNDA vias and -Vp track)
    elements.append(build_segment(71.675, 78.585, 72.50, 78.585, "F.Cu", "/Power/PG_VSSA", get_id(), width=0.15))
    elements.append(build_segment(72.50, 78.585, 72.665, 78.75, "F.Cu", "/Power/PG_VSSA", get_id(), width=0.15))
    elements.append(build_segment(72.665, 78.75, 73.00, 78.75, "F.Cu", "/Power/PG_VSSA", get_id(), width=0.15))
    elements.append(build_via(73.00, 78.75, "/Power/PG_VSSA", get_id()))
    elements.append(build_segment(73.00, 78.75, 73.00, 83.355026, "B.Cu", "/Power/PG_VSSA", get_id(), width=0.15))

    # O. Damping outputs to ESP32 (GPIO3, GPIO2, GPIO1) strictly planar
    # Column 1 (X=89.20): GPIO3 from R59 (X=81.5) -> via (81.5, 88.60) -> B.Cu (89.20, 88.60) -> peels off at Y=61.50 -> U8 pin 7 (88.969, 61.50)
    elements.append(build_segment(81.5, 88.71, 81.5, 88.60, "F.Cu", "/Microcontroller/GPIO3", get_id()))
    elements.append(build_via(81.5, 88.60, "/Microcontroller/GPIO3", get_id()))
    elements.append(build_segment(81.5, 88.60, 89.20, 88.60, "B.Cu", "/Microcontroller/GPIO3", get_id(), width=0.15))
    elements.append(build_segment(89.20, 88.60, 89.20, 61.50, "B.Cu", "/Microcontroller/GPIO3", get_id(), width=0.15))
    elements.append(build_via(89.20, 61.50, "/Microcontroller/GPIO3", get_id()))
    elements.append(build_segment(89.20, 61.50, 88.969, 61.50, "F.Cu", "/Microcontroller/GPIO3", get_id(), width=0.15))

    # Column 2 (X=89.55): GPIO2 from R58 (X=83.0) -> via (83.0, 89.15) -> B.Cu (89.55, 89.15) -> peels off at Y=60.65 -> U8 pin 6 (88.969, 60.65)
    elements.append(build_segment(83.0, 88.71, 83.0, 89.15, "F.Cu", "/Microcontroller/GPIO2", get_id()))
    elements.append(build_via(83.0, 89.15, "/Microcontroller/GPIO2", get_id()))
    elements.append(build_segment(83.0, 89.15, 89.55, 89.15, "B.Cu", "/Microcontroller/GPIO2", get_id(), width=0.15))
    elements.append(build_segment(89.55, 89.15, 89.55, 60.65, "B.Cu", "/Microcontroller/GPIO2", get_id(), width=0.15))
    elements.append(build_via(89.55, 60.65, "/Microcontroller/GPIO2", get_id()))
    elements.append(build_segment(89.55, 60.65, 88.969, 60.65, "F.Cu", "/Microcontroller/GPIO2", get_id(), width=0.15))

    # Column 3 (X=89.90): GPIO1 from R57 (X=84.5) -> via (84.5, 89.70) -> B.Cu (89.90, 89.70) -> peels off at Y=59.80 -> U8 pin 5 (88.969, 59.80)
    elements.append(build_segment(84.5, 88.71, 84.5, 89.70, "F.Cu", "/Microcontroller/GPIO1", get_id()))
    elements.append(build_via(84.5, 89.70, "/Microcontroller/GPIO1", get_id()))
    elements.append(build_segment(84.5, 89.70, 89.90, 89.70, "B.Cu", "/Microcontroller/GPIO1", get_id(), width=0.15))
    elements.append(build_segment(89.90, 89.70, 89.90, 59.80, "B.Cu", "/Microcontroller/GPIO1", get_id(), width=0.15))
    elements.append(build_via(89.90, 59.80, "/Microcontroller/GPIO1", get_id()))
    elements.append(build_segment(89.90, 59.80, 88.969, 59.80, "F.Cu", "/Microcontroller/GPIO1", get_id(), width=0.15))

    # P. +Vp_cm jumper on B.Cu replacing F.Cu track:
    elements.append(build_via(78.00, 82.15, "/Power/+Vp_cm", get_id()))
    elements.append(build_segment(78.00, 82.15, 78.00, 82.40, "B.Cu", "/Power/+Vp_cm", get_id(), width=0.2))
    elements.append(build_segment(78.00, 82.40, 75.345, 82.40, "B.Cu", "/Power/+Vp_cm", get_id(), width=0.2))
    elements.append(build_segment(75.345, 82.40, 75.345, 81.925, "B.Cu", "/Power/+Vp_cm", get_id(), width=0.2))
    elements.append(build_via(75.345, 81.925, "/Power/+Vp_cm", get_id()))

    # Q. U1 EN- (Pin 8) and EN+ (Pin 12) tied to VBUS
    # VBUS source at Pad 3 via (79.62, 80.50), routes south along Y=78.20 on B.Cu clearing thermal pad 13 and -VIOC
    elements.append(build_via(79.62, 80.50, "VBUS", get_id()))
    elements.append(build_segment(79.62, 80.50, 79.62, 78.20, "B.Cu", "VBUS", get_id(), width=0.15))
    elements.append(build_segment(79.62, 78.20, 75.80, 78.20, "B.Cu", "VBUS", get_id(), width=0.15))
    elements.append(build_segment(75.80, 78.20, 75.80, 79.50, "B.Cu", "VBUS", get_id(), width=0.15))
    elements.append(build_via(75.80, 79.50, "VBUS", get_id()))
    elements.append(build_segment(75.80, 79.50, 76.70, 79.50, "F.Cu", "VBUS", get_id(), width=0.15))
    # Route north on B.Cu from (75.80, 79.50) to (76.50, 81.85) for Pin 12:
    elements.append(build_segment(75.80, 79.50, 75.80, 81.85, "B.Cu", "VBUS", get_id(), width=0.15))
    elements.append(build_segment(75.80, 81.85, 76.50, 81.85, "B.Cu", "VBUS", get_id(), width=0.15))
    elements.append(build_via(76.50, 81.85, "VBUS", get_id()))
    elements.append(build_segment(76.50, 81.85, 76.70, 81.50, "F.Cu", "VBUS", get_id(), width=0.15))

    # Insert into PCB
    block = "\n" + "\n".join(elements) + "\n"
    last_paren = text.rfind(")")
    text = text[:last_paren] + block + text[last_paren:]

    with open(pcb_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Applied {len(elements)} clean routing elements to {pcb_path}.")

if __name__ == "__main__":
    main()
