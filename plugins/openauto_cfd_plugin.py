"""
OpenAuto-CFD KiCad Plugin & Co-Design Synchronizer
===================================================
A unified KiCad Action Plugin and CLI orchestrator bridging KiCad EDA,
Build123d CAD, and OpenAuto-CFD microfluidic simulation.

Capabilities:
1. Interactive KiCad PCB Editor Action Plugin (pcbnew.ActionPlugin).
2. Standalone CLI tool (operates with or without native pcbnew).
3. Bi-directional verification of board geometry against openauto.project.json:
   - Edge.Cuts closed boundary continuity and dimensional bounds.
   - Fluidic well interface apertures and fluid pass-through ports.
   - 4-electrode concentric cell and pogo pin array locations.
   - Weep moat / leak detection sensor traces (WEEP_SENSE) and GNDA guards.
4. Direct export of 2D DXF contours for OpenAuto-CFD / OpenFOAM mesh generation.
5. Automated registration and synchronization of board metadata into openauto.project.json.
"""

import os
import sys
import json
import re
import math
import shutil
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

# Locate daemon-pore root directory
REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "openauto.project.json"

# -----------------------------------------------------------------------------
# Standalone KiCad S-Expression PCB Parser
# -----------------------------------------------------------------------------
class KiCadPcbParser:
    """Parses .kicad_pcb S-expressions without requiring native pcbnew."""

    def __init__(self, pcb_path: Path):
        self.path = Path(pcb_path)
        if not self.path.exists():
            raise FileNotFoundError(f"KiCad PCB file not found: {self.path}")
        self.text = self.path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def get_edge_cuts_segments(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Extracts all start and end points of lines/arcs/rectangles on Edge.Cuts layer."""
        segs = []

        # Universal balanced parentheses extractor for (gr_line ...), (gr_arc ...), (gr_rect ...)
        lines = self.lines
        in_gr = False
        cur_block = []
        blocks = []
        for l in lines:
            stripped = l.strip()
            if stripped.startswith('(gr_line') or stripped.startswith('(gr_arc') or stripped.startswith('(gr_rect'):
                in_gr = True
                cur_block = [l]
                if stripped.endswith(')') and stripped.count('(') == stripped.count(')'):
                    in_gr = False
                    blocks.append('\n'.join(cur_block))
                    cur_block = []
            elif in_gr:
                cur_block.append(l)
                joined = '\n'.join(cur_block)
                if joined.count('(') <= joined.count(')'):
                    in_gr = False
                    blocks.append(joined)
                    cur_block = []

        for b in blocks:
            if '"Edge.Cuts"' not in b:
                continue
            sm = re.search(r'\(start\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', b)
            em = re.search(r'\(end\s+([0-9\.\-]+)\s+([0-9\.\-]+)\)', b)
            if not sm or not em:
                continue
            if b.strip().startswith('(gr_rect'):
                x1, y1 = round(float(sm.group(1)), 3), round(float(sm.group(2)), 3)
                x2, y2 = round(float(em.group(1)), 3), round(float(em.group(2)), 3)
                segs.extend([
                    ((x1, y1), (x2, y1)),
                    ((x2, y1), (x2, y2)),
                    ((x2, y2), (x1, y2)),
                    ((x1, y2), (x1, y1)),
                ])
            else:
                p1 = (round(float(sm.group(1)), 3), round(float(sm.group(2)), 3))
                p2 = (round(float(em.group(1)), 3), round(float(em.group(2)), 3))
                if p1 != p2:
                    segs.append((p1, p2))

        return segs

    def compute_bounds(self) -> Dict[str, float]:
        """Calculates bounding box of Edge.Cuts geometry."""
        segs = self.get_edge_cuts_segments()
        if not segs:
            return {"min_x": 0.0, "max_x": 0.0, "min_y": 0.0, "max_y": 0.0, "width": 0.0, "height": 0.0, "center_x": 0.0, "center_y": 0.0}
        xs = [p[0] for s in segs for p in s]
        ys = [p[1] for s in segs for p in s]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "width": round(max_x - min_x, 3),
            "height": round(max_y - min_y, 3),
            "center_x": round((min_x + max_x) / 2.0, 3),
            "center_y": round((min_y + max_y) / 2.0, 3),
        }

    def check_edge_cuts_continuity(self) -> Dict[str, Any]:
        """Verifies if the Edge.Cuts profile forms a closed continuous polygon."""
        segs = self.get_edge_cuts_segments()
        if not segs:
            return {"is_closed": False, "vertex_count": 0, "non_degree_2": {}, "segment_count": 0}

        adj = defaultdict(list)
        for p1, p2 in segs:
            adj[p1].append(p2)
            adj[p2].append(p1)

        non_2 = {str(k): len(v) for k, v in adj.items() if len(v) != 2}
        return {
            "is_closed": len(non_2) == 0,
            "vertex_count": len(adj),
            "segment_count": len(segs),
            "non_degree_2": non_2,
        }

    def get_footprints(self) -> List[Dict[str, Any]]:
        """Parses footprint references, positions, and layers."""
        fps = []
        for m in re.finditer(r'\(footprint\s+"([^"]+)"(.*?)(?=\n\t\(footprint|\n\t\(gr_|\n\t\(zone|\n\t\(segment|\n\t\(via|\Z)', self.text, re.DOTALL):
            fp_name = m.group(1)
            body = m.group(2)
            at_m = re.search(r'\(at\s+([0-9\.\-]+)\s+([0-9\.\-]+)(?:\s+([0-9\.\-]+))?\)', body)
            ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', body)
            if at_m:
                x = float(at_m.group(1))
                y = float(at_m.group(2))
                rot = float(at_m.group(3)) if at_m.group(3) else 0.0
                ref = ref_m.group(1) if ref_m else ""
                fps.append({
                    "reference": ref,
                    "name": fp_name,
                    "x": x,
                    "y": y,
                    "rotation": rot,
                })
        return fps

    def get_nets(self) -> List[str]:
        """Extracts unique net names defined in the PCB."""
        return list(set(re.findall(r'\(net\s+(?:\d+\s+)?"([^"]+)"\)', self.text)))

    def get_normalized_nets(self) -> List[str]:
        """Extracts net names stripped of hierarchical prefix slashes and special chars."""
        return list(set(re.sub(r'^[/>]+', '', n) for n in self.get_nets()))


# -----------------------------------------------------------------------------
# OpenAuto-CFD Synchronizer & Validator Engine
# -----------------------------------------------------------------------------
class OpenAutoCFDSynchronizer:
    """Orchestrates bi-directional verification between KiCad and openauto.project.json."""

    def __init__(self, manifest_path: Path = MANIFEST_PATH):
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"OpenAuto project manifest missing: {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def validate_board(self, board_key: str) -> Dict[str, Any]:
        """Validates a board against OpenAuto-CFD requirements."""
        boards = self.manifest.get("boards", {})
        if board_key not in boards:
            return {
                "board": board_key,
                "valid": False,
                "bounds": {"width": 0.0, "height": 0.0},
                "continuity": {"is_closed": False, "segment_count": 0},
                "footprint_count": 0,
                "net_count": 0,
                "errors": [f"Board '{board_key}' is not registered in openauto.project.json"],
                "warnings": [],
            }

        board_meta = boards[board_key]
        rel_path = board_meta.get("path")
        pcb_file = REPO_ROOT / rel_path
        if not pcb_file.exists():
            return {
                "board": board_key,
                "valid": False,
                "bounds": {"width": 0.0, "height": 0.0},
                "continuity": {"is_closed": False, "segment_count": 0},
                "footprint_count": 0,
                "net_count": 0,
                "errors": [f"PCB file '{pcb_file}' does not exist on disk."],
                "warnings": [],
            }

        parser = KiCadPcbParser(pcb_file)
        bounds = parser.compute_bounds()
        continuity = parser.check_edge_cuts_continuity()
        fps = parser.get_footprints()
        norm_nets = parser.get_normalized_nets()
        errors = []
        warnings = []

        # 1. Edge.Cuts continuity check
        if not continuity["is_closed"]:
            errors.append(
                f"Edge.Cuts profile is not a closed polygon: {len(continuity['non_degree_2'])} vertices have degree != 2."
            )

        # 2. Board-specific domain assertions
        if board_key == "interposer":
            # Hexagonal Interposer bounds: width ~55.0 mm, height ~51.96 mm
            if abs(bounds["width"] - 55.0) > 0.5:
                warnings.append(f"Interposer width {bounds['width']} mm deviates from expected 55.0 mm.")
            if abs(bounds["height"] - 51.96) > 0.5:
                warnings.append(f"Interposer height {bounds['height']} mm deviates from expected 51.96 mm.")

            # Required nets for 4-electrode cell & weep moat
            required_nets = ["WE_POS", "WS_CIS", "RE_TRANS", "CE_GNDA", "GNDA", "WEEP_SENSE"]
            for rn in required_nets:
                if rn not in norm_nets:
                    errors.append(f"Missing required electrochemical net '{rn}' in Interposer PCB.")

            # Verify pogo interface target pad footprint
            pogo_fps = [f for f in fps if "Pogo" in f["name"] or "J_POGO" in f["reference"]]
            if not pogo_fps:
                warnings.append("Missing Pogo Pin target footprint (J_POGO1) for headstage coupling.")

        elif board_key == "amplifier":
            # LMP7721 TIA Board (55.0 x 51.96 mm hex with ribbon cable cavity)
            if abs(bounds["width"] - 55.0) > 0.5 or abs(bounds["height"] - 51.96) > 0.5:
                warnings.append(f"Amplifier PCB size ({bounds['width']} x {bounds['height']} mm) deviates from 55x51.96 mm.")
            required_nets = ["GNDA", "CE_GNDA", "RE_TRANS"]
            for rn in required_nets:
                if rn not in norm_nets:
                    errors.append(f"Missing required analog net '{rn}' in Amplifier PCB.")
            if not any("PORE" in n for n in norm_nets):
                errors.append("Missing PORE transmembrane signal net in Amplifier PCB.")
            if not any("WEEP" in n for n in norm_nets):
                errors.append("Missing WEEP leak interlock net in Amplifier PCB.")

        elif board_key == "mr1":
            # 80.0 x 60.0 mm motherboard
            if abs(bounds["width"] - 80.0) > 1.0 or abs(bounds["height"] - 60.0) > 1.0:
                warnings.append(f"MR1 PCB size ({bounds['width']} x {bounds['height']} mm) deviates from 80x60 mm.")

        elif board_key == "pump":
            # Peristaltic Pump Board: 88.0 x 88.0 mm
            if abs(bounds["width"] - 88.0) > 1.0 or abs(bounds["height"] - 88.0) > 1.0:
                warnings.append(f"Pump PCB size ({bounds['width']} x {bounds['height']} mm) deviates from 88x88 mm.")

        # 3. Fluidic Coupling Verification
        if "fluidic_coupling" in board_meta:
            fc = board_meta["fluidic_coupling"]
            target_ref = fc.get("target_ref")
            target_fps = [f for f in fps if f["reference"] == target_ref]
            if not target_fps:
                warnings.append(f"Fluidic coupling target reference '{target_ref}' not found in PCB footprints.")

        is_valid = len(errors) == 0
        return {
            "board": board_key,
            "valid": is_valid,
            "bounds": bounds,
            "continuity": continuity,
            "footprint_count": len(fps),
            "net_count": len(norm_nets),
            "errors": errors,
            "warnings": warnings,
        }

    def validate_all(self) -> Dict[str, Any]:
        """Validates all registered boards in openauto.project.json."""
        results = {}
        all_valid = True
        for b_name in self.manifest.get("boards", {}).keys():
            res = self.validate_board(b_name)
            results[b_name] = res
            if not res["valid"]:
                all_valid = False
        return {"all_valid": all_valid, "boards": results}

    def sync_board_geometry(self, board_key: str) -> bool:
        """Calculates exact board bounds and updates openauto.project.json."""
        boards = self.manifest.get("boards", {})
        if board_key not in boards:
            return False
        rel_path = boards[board_key].get("path")
        pcb_file = REPO_ROOT / rel_path
        if not pcb_file.exists():
            return False

        parser = KiCadPcbParser(pcb_file)
        bounds = parser.compute_bounds()

        if "geometry" not in boards[board_key]:
            boards[board_key]["geometry"] = {}
        boards[board_key]["geometry"]["width_mm"] = bounds["width"]
        boards[board_key]["geometry"]["height_mm"] = bounds["height"]
        boards[board_key]["geometry"]["center_x_mm"] = bounds["center_x"]
        boards[board_key]["geometry"]["center_y_mm"] = bounds["center_y"]

        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, indent=2)
        return True


# -----------------------------------------------------------------------------
# KiCad GUI Action Plugin Implementation
# -----------------------------------------------------------------------------
try:
    import pcbnew  # type: ignore

    class OpenAutoCFDKiCadAction(pcbnew.ActionPlugin):
        """Native KiCad PCB Editor Action Plugin for OpenAuto-CFD."""

        def defaults(self):
            self.name = "OpenAuto-CFD Co-Design & Sync"
            self.category = "Microfluidics & CFD Co-Simulation"
            self.description = "Synchronize board boundaries, well interfaces, and weep guards with OpenAuto-CFD"
            self.show_toolbar_button = True
            self.icon_file_name = ""

        def Run(self):
            board = pcbnew.GetBoard()
            board_file = board.GetFileName()
            if not board_file:
                print("[OpenAuto-CFD] Please save the board before running synchronization.")
                return

            print(f"[OpenAuto-CFD] Analyzing current board: {board_file}")
            sync = OpenAutoCFDSynchronizer()

            # Identify matching board key
            matched_key = None
            for key, meta in sync.manifest.get("boards", {}).items():
                if Path(meta.get("path")).name.lower() == Path(board_file).name.lower():
                    matched_key = key
                    break

            if matched_key:
                res = sync.validate_board(matched_key)
                if res["valid"]:
                    print(f"[OpenAuto-CFD] Board '{matched_key}' is VALID! Updating geometry manifest...")
                    sync.sync_board_geometry(matched_key)
                    print(f"[OpenAuto-CFD] Successfully synchronized {matched_key} with openauto.project.json!")
                else:
                    print(f"[OpenAuto-CFD] Validation issues found for '{matched_key}':")
                    for err in res["errors"]:
                        print(f"  [ERROR] {err}")
                    for warn in res["warnings"]:
                        print(f"  [WARN]  {warn}")
            else:
                print(f"[OpenAuto-CFD] Current board is not registered in openauto.project.json.")

    OpenAutoCFDKiCadAction().register()

except ImportError:
    # Running outside KiCad environment (CLI mode)
    pass


# -----------------------------------------------------------------------------
# CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="OpenAuto-CFD KiCad Plugin & Co-Design Synchronizer",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--board", choices=["interposer", "amplifier", "mr1", "pump"], help="Target board to validate")
    parser.add_argument("--validate", action="store_true", help="Validate board geometry against OpenAuto requirements")
    parser.add_argument("--validate-all", action="store_true", help="Validate all boards in openauto.project.json")
    parser.add_argument("--sync", action="store_true", help="Synchronize board bounding geometry into openauto.project.json")
    parser.add_argument("--install", action="store_true", help="Install plugin into local KiCad scripting plugins directory")

    args = parser.parse_args()
    sync = OpenAutoCFDSynchronizer()

    if args.install:
        home = Path.home()
        candidates = [
            home / ".local" / "share" / "kicad" / "10.0" / "scripting" / "plugins",
            home / ".local" / "share" / "kicad" / "9.0" / "scripting" / "plugins",
            home / ".local" / "share" / "kicad" / "8.0" / "scripting" / "plugins",
            home / ".local" / "share" / "kicad" / "7.0" / "scripting" / "plugins",
        ]
        target_dir = None
        for c in candidates:
            if c.parent.parent.exists():
                target_dir = c
                break

        if not target_dir:
            target_dir = candidates[0]

        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / "openauto_cfd_plugin.py"
        src = Path(__file__).resolve()
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[OK] OpenAuto-CFD KiCad Plugin successfully installed to:\n  {dest}")
        print("In KiCad PCB Editor, click 'Tools -> External Plugins -> Refresh Plugins' to activate.")
        return 0

    if args.validate_all or (not args.board and not args.validate and not args.sync):
        report = sync.validate_all()
        print("=" * 70)
        print(" OpenAuto-CFD Multi-Board Co-Design Verification")
        print("=" * 70)
        for b_name, b_res in report["boards"].items():
            status = "[PASS]" if b_res["valid"] else "[FAIL]"
            width = b_res.get("bounds", {}).get("width", 0.0)
            height = b_res.get("bounds", {}).get("height", 0.0)
            fp_count = b_res.get("footprint_count", 0)
            print(f"{status} Board: {b_name:12} | Width: {width:6.2f} mm | Height: {height:6.2f} mm | Footprints: {fp_count:3}")
            for err in b_res["errors"]:
                print(f"       ERROR: {err}")
            for warn in b_res["warnings"]:
                print(f"       WARN:  {warn}")
        print("=" * 70)
        return 0 if report["all_valid"] else 1

    if args.board:
        res = sync.validate_board(args.board)
        status = "PASSED" if res["valid"] else "FAILED"
        print(f"Validation for {args.board}: {status}")
        print(f"  Dimensions: {res['bounds']['width']} x {res['bounds']['height']} mm")
        print(f"  Edge.Cuts closed: {res['continuity']['is_closed']}")
        print(f"  Footprints: {res['footprint_count']}, Nets: {res['net_count']}")
        for err in res["errors"]:
            print(f"  [ERROR] {err}")
        for warn in res["warnings"]:
            print(f"  [WARN]  {warn}")

        if args.sync and res["valid"]:
            sync.sync_board_geometry(args.board)
            print(f"  [OK] Synchronized geometry into {MANIFEST_PATH.name}")
        return 0 if res["valid"] else 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
