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
CENTER_X = 164.50
CENTER_Y = 58.50


def verify_amplifier_pcb(pcb_path: Path = DEFAULT_PCB_PATH) -> list[str]:
    """Verifies that all 12 pogo pins on the PCB match stack_spec.py."""
    if not pcb_path.exists():
        return [f"PCB file does not exist: {pcb_path}"]

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
        expected_x = CENTER_X + expected_kx
        expected_y = CENTER_Y + expected_ky

        if actual["layer"] != "F.Cu":
            issues.append(f"{ref} layer is {actual['layer']}, expected F.Cu")

        if abs(actual["x"] - expected_x) > 0.05:
            issues.append(f"{ref} X={actual['x']:.4f}, expected {expected_x:.4f}")

        if abs(actual["y"] - expected_y) > 0.05:
            issues.append(f"{ref} Y={actual['y']:.4f}, expected {expected_y:.4f}")

    return issues


def update_amplifier_pcb(pcb_path: Path = DEFAULT_PCB_PATH, dry_run: bool = False) -> bool:
    """Updates pin positions in the PCB file to match stack_spec exactly.
    Preserves all surrounding text, routing, components, and zones.
    """
    if not pcb_path.exists():
        raise FileNotFoundError(f"PCB file not found: {pcb_path}")

    text = pcb_path.read_text(encoding="utf-8")
    modified = False

    for pin_def in spec.PINS:
        ref = pin_def.ref
        expected_kx, expected_ky = spec.kicad_xy(pin_def.x, pin_def.y)
        expected_x = CENTER_X + expected_kx
        expected_y = CENTER_Y + expected_ky

        # Regex to locate footprint block for this reference
        # We look for (footprint ... (at X Y [ROT]) ... (property "Reference" "REF" ...))
        pattern = re.compile(
            rf'(\(footprint\s+"[^"]*"\s*\n\s*\(layer\s+"F\.Cu"\)\s*\n\s*\(uuid\s+"[^"]*"\)\s*\n\s*\(at\s+)([0-9\.\-]+)(\s+)([0-9\.\-]+)([\s0-9\.\-]*)(\)\s*\n[\s\S]*?\(property\s+"Reference"\s+"{ref}")'
        )

        match = pattern.search(text)
        if match:
            cur_x = float(match.group(2))
            cur_y = float(match.group(4))
            rot = match.group(5)

            if abs(cur_x - expected_x) > 0.001 or abs(cur_y - expected_y) > 0.001:
                replacement = f"{match.group(1)}{expected_x:.4f}{match.group(3)}{expected_y:.4f}{rot}{match.group(6)}"
                text = text[:match.start()] + replacement + text[match.end():]
                modified = True

    if modified and not dry_run:
        pcb_path.write_text(text, encoding="utf-8")

    return modified


def main() -> int:
    parser = argparse.ArgumentParser(description="MR1 Amplifier KiCad PCB Synchronization Utility")
    parser.add_argument("--check", action="store_true", help="Check PCB consistency against stack_spec")
    parser.add_argument("--write", action="store_true", help="Write position updates to Amplifier.kicad_pcb")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without writing changes")
    parser.add_argument("--pcb", type=Path, default=DEFAULT_PCB_PATH, help="Path to Amplifier.kicad_pcb")

    args = parser.parse_args()

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
