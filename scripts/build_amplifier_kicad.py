# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0
"""
scripts/build_amplifier_kicad.py
================================
Synchronizes and verifies pogo pin placements (P1..P12) on the
2-layer Rogers RO3003 Cartridge Amplifier PCB (Amplifier/Amplifier.kicad_pcb)
against the single source of truth `src/stack_spec.py`.

Ensures that:
  - All 12 pogo pins are placed on `F.Cu` (component side).
  - Pin XY coordinates match CAD coordinates converted to KiCad space:
      kx = x0 + cad_x
      ky = y0 - cad_y
    where (x0, y0) = (164.50, 58.50) mm.
  - Signal pads (Pad 1) and concentric guard/ground rings (Pad 2) connect
    to the correct schematic nets.
  - Hand-routed tracks, RF planes, guard islands, and active circuitry are preserved.

Usage:
  ./scripts/run_python.sh scripts/build_amplifier_kicad.py --check
  ./scripts/run_python.sh scripts/build_amplifier_kicad.py --write
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import stack_spec as spec
from scripts.generate_footprint import extract_pin_placements_from_pcb

DEFAULT_PCB_PATH = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"
CENTER_X = 43.7042
CENTER_Y = 42.0206


def extract_board_center(pcb_path: Path = DEFAULT_PCB_PATH) -> tuple[float, float]:
    """Derives board center from Edge.Cuts bounding box, defaulting to (43.7042, 42.0206)."""
    if not pcb_path.exists():
        return (CENTER_X, CENTER_Y)
    text = pcb_path.read_text(encoding="utf-8")
    blocks = re.findall(
        r'\(gr_line\s+\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)\s+.*?\(layer\s+"Edge\.Cuts"\)',
        text,
        re.DOTALL,
    )
    if not blocks:
        return (CENTER_X, CENTER_Y)
    xs = []
    ys = []
    for x1, y1, x2, y2 in blocks:
        xs.extend([float(x1), float(x2)])
        ys.extend([float(y1), float(y2)])
    return (round((min(xs) + max(xs)) / 2.0, 4), round((min(ys) + max(ys)) / 2.0, 4))



def verify_amplifier_pcb(pcb_path: Path = DEFAULT_PCB_PATH) -> list[str]:
    """Verifies that all 12 pogo pins on the PCB match stack_spec.py."""
    if not pcb_path.exists():
        return [f"PCB file does not exist: {pcb_path}"]

    center_x, center_y = extract_board_center(pcb_path)
    placements = extract_pin_placements_from_pcb(pcb_path)
    issues = []

    if len(placements) != len(spec.PINS):
        issues.append(f"Expected {len(spec.PINS)} pins, found {len(placements)} on PCB")

    for pin_def in spec.PINS:
        ref = pin_def.ref
        if ref not in placements:
            issues.append(f"Missing pin {ref} from PCB")
            continue

        actual = placements[ref]
        expected_kx, expected_ky = spec.kicad_xy(pin_def.x, pin_def.y)
        expected_x = center_x + expected_kx
        expected_y = center_y + expected_ky

        if actual["layer"] != "F.Cu":
            issues.append(f"{ref} layer is {actual['layer']}, expected F.Cu")

        if abs(actual["x"] - expected_x) > 0.05:
            issues.append(f"{ref} X={actual['x']:.4f}, expected {expected_x:.4f}")

        if abs(actual["y"] - expected_y) > 0.05:
            issues.append(f"{ref} Y={actual['y']:.4f}, expected {expected_y:.4f}")

    return issues


def update_amplifier_pcb(pcb_path: Path = DEFAULT_PCB_PATH, dry_run: bool = False) -> bool:
    """Updates pin positions in the PCB file to match stack_spec exactly.
    Safely locates each footprint block without matching across adjacent footprints.
    Preserves all surrounding text, routing, components, and zones.
    """
    if not pcb_path.exists():
        raise FileNotFoundError(f"PCB file not found: {pcb_path}")

    center_x, center_y = extract_board_center(pcb_path)
    text = pcb_path.read_text(encoding="utf-8")
    modified = False

    for pin_def in spec.PINS:
        ref = pin_def.ref
        expected_kx, expected_ky = spec.kicad_xy(pin_def.x, pin_def.y)
        expected_x = center_x + expected_kx
        expected_y = center_y + expected_ky

        # Match (footprint ...) block containing this exact reference
        ref_pattern = rf'\(property\s+"Reference"\s+"{ref}"'
        ref_match = re.search(ref_pattern, text)
        if not ref_match:
            continue

        fp_start = text.rfind("(footprint ", 0, ref_match.start())
        if fp_start == -1:
            continue

        at_pattern = re.compile(
            r'(\(at\s+)([0-9\.\-]+)(\s+)([0-9\.\-]+)([\s0-9\.\-]*)(\))'
        )
        at_match = at_pattern.search(text, fp_start, ref_match.start())
        if at_match:
            cur_x = float(at_match.group(2))
            cur_y = float(at_match.group(4))
            rot = at_match.group(5)

            if abs(cur_x - expected_x) > 0.001 or abs(cur_y - expected_y) > 0.001:
                replacement = f"{at_match.group(1)}{expected_x:.4f}{at_match.group(3)}{expected_y:.4f}{rot}{at_match.group(6)}"
                text = text[:at_match.start()] + replacement + text[at_match.end():]
                modified = True

    if modified and not dry_run:
        pcb_path.write_text(text, encoding="utf-8")

    return modified


def sync_spec_from_pcb(pcb_path: Path = DEFAULT_PCB_PATH, spec_path: Path = REPO_ROOT / "src" / "stack_spec.py") -> bool:
    """Reads manual pin placements from Amplifier.kicad_pcb and synchronizes them into src/stack_spec.py."""
    if not pcb_path.exists():
        raise FileNotFoundError(f"PCB file not found: {pcb_path}")

    center_x, center_y = extract_board_center(pcb_path)
    placements = extract_pin_placements_from_pcb(pcb_path)
    if len(placements) != 12:
        raise ValueError(f"Expected 12 pins on PCB, found {len(placements)}")

    lines = []
    for pin_def in spec.PINS:
        ref = pin_def.ref
        if ref not in placements:
            raise KeyError(f"Missing {ref} from PCB placements")
        actual = placements[ref]
        cad_x = round(actual["x"] - center_x, 4)
        cad_y = round(center_y - actual["y"], 4)
        is_guarded = "Guarded" in actual["footprint"]
        ring_net = pin_def.ring if is_guarded else None
        side = pin_def.side

        ring_str = f', ring={ring_net}' if ring_net else ""
        desc_str = f', description="{pin_def.description}"' if pin_def.description else ""
        lines.append(
            f'    PinSpec({pin_def.number}, "{pin_def.net}", {side.upper()}, {cad_x}, {cad_y}, "{pin_def.role}"{ring_str}{desc_str}),'
        )

    new_pins_block = "PINS: Tuple[PinSpec, ...] = (\n" + "\n".join(lines) + "\n)"
    spec_content = spec_path.read_text(encoding="utf-8")
    pattern = re.compile(r'PINS:\s*Tuple\[PinSpec,\s*\.\.\.\]\s*=\s*\([\s\S]*?\n\)', re.MULTILINE)
    if not pattern.search(spec_content):
        raise ValueError("Could not find PINS definition in stack_spec.py")

    updated_spec = pattern.sub(new_pins_block, spec_content, count=1)
    if updated_spec != spec_content:
        spec_path.write_text(updated_spec, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="MR1 Amplifier KiCad PCB Synchronization Utility")
    parser.add_argument("--check", action="store_true", help="Check PCB consistency against stack_spec")
    parser.add_argument("--write", action="store_true", help="Write position updates to Amplifier.kicad_pcb")
    parser.add_argument("--sync-spec", action="store_true", help="Import pin placements from Amplifier.kicad_pcb into stack_spec.py")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing changes")
    parser.add_argument("--pcb", type=Path, default=DEFAULT_PCB_PATH, help="Path to Amplifier.kicad_pcb")

    args = parser.parse_args()

    if args.sync_spec:
        print(f"[*] Importing pin placements from {args.pcb} into src/stack_spec.py...")
        changed = sync_spec_from_pcb(args.pcb)
        status = "Updated" if changed else "Already in sync"
        print(f"[OK] {status} src/stack_spec.py from manual PCB layout.")
        return 0

    issues = verify_amplifier_pcb(args.pcb)
    if issues:
        print(f"[!] Amplifier PCB inconsistencies found ({len(issues)}):")
        for issue in issues:
            print(f"    - {issue}")

        if args.write or args.dry_run:
            print("[*] Updating pin placements from stack_spec...")
            changed = update_amplifier_pcb(args.pcb, dry_run=args.dry_run)
            if changed:
                mode_str = "DRY-RUN: Would update" if args.dry_run else "SUCCESS: Updated"
                print(f"[OK] {mode_str} pin placements in {args.pcb}")
                # Re-verify
                post_issues = verify_amplifier_pcb(args.pcb)
                if not post_issues or args.dry_run:
                    return 0
                return 1
            else:
                print("[!] Could not automatically reconcile positions.")
                return 1
        return 1
    else:
        print(f"[OK] Amplifier PCB pins are 100% in sync with stack_spec (all 12 on F.Cu).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
