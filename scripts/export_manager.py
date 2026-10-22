#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
MR1 Nanopore Reader - Project Export Manager
Orchestrates all project deliverable exports:
- 3D Solids (STEP, STL) & 2D Profiles (DXF) via build123d
- KiCad Gerbers, drill files, BOMs, Pick & Place (POS), and PDF schematics
- WireViz electrical wiring and fluid tubing documentation
- ESP32-S3 firmware build artifact staging
- Manifest generation and SHA-256 integrity tracking
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = REPO_ROOT / "exports"

# -----------------------------------------------------------------------------
# Tool Discovery
# -----------------------------------------------------------------------------
def find_kicad_cli():
    """Locate kicad-cli on PATH or standard installation directories."""
    on_path = shutil.which("kicad-cli") or shutil.which("kicad-cli.exe")
    if on_path:
        return on_path

    # Standard Windows install locations
    win_paths = [
        Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"),
        Path("C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"),
        Path("C:/Program Files/KiCad/8.0/bin/kicad-cli.exe"),
    ]
    for p in win_paths:
        if p.exists():
            return str(p)

    # Standard macOS / Linux locations
    unix_paths = [
        Path("/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"),
        Path("/usr/bin/kicad-cli"),
        Path("/usr/local/bin/kicad-cli"),
    ]
    for p in unix_paths:
        if p.exists():
            return str(p)

    return None


def find_wireviz():
    """Locate wireviz on PATH or in Python Scripts/venv."""
    on_path = shutil.which("wireviz") or shutil.which("wireviz.exe")
    if on_path:
        return on_path
    venv_bin = Path(sys.executable).parent / "wireviz"
    if venv_bin.exists():
        return str(venv_bin)
    venv_exe = Path(sys.executable).parent / "wireviz.exe"
    if venv_exe.exists():
        return str(venv_exe)
    return None


def find_pio():
    """Locate PlatformIO core on PATH or in Python Scripts/venv."""
    on_path = shutil.which("pio") or shutil.which("pio.exe")
    if on_path:
        return on_path
    venv_bin = Path(sys.executable).parent / "pio"
    if venv_bin.exists():
        return str(venv_bin)
    venv_exe = Path(sys.executable).parent / "pio.exe"
    if venv_exe.exists():
        return str(venv_exe)
    return None


# -----------------------------------------------------------------------------
# Exporters
# -----------------------------------------------------------------------------
def export_cad(verbose=True):
    """Export 3D STEP/STL and 2D DXF profiles using build123d."""
    if verbose:
        print("\n[1/5] Exporting 3D Models & 2D DXF Profiles...")
    cmd = [sys.executable, str(REPO_ROOT / "src" / "main.py"), "all"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error exporting CAD:\n{res.stderr}")
        return False
    if verbose:
        print("  [OK] CAD export completed successfully.")
    return True


def export_kicad(verbose=True):
    """Export Gerbers, drill, pos, BOM, and PDF schematics for MR1 and Amplifier."""
    if verbose:
        print("\n[2/5] Exporting KiCad Manufacturing Deliverables...")
    kicad_cli = find_kicad_cli()
    if not kicad_cli:
        print("  [WARN] Warning: kicad-cli not found. Skipping KiCad exports.")
        return False

    if verbose:
        print(f"  Using KiCad CLI: {kicad_cli}")

    boards = [
        {
            "name": "MR1",
            "pcb": REPO_ROOT / "MR1" / "MR1.kicad_pcb",
            "sch": REPO_ROOT / "MR1" / "MR1.kicad_sch",
            "gerber_dir": EXPORTS_DIR / "gerbers_mr1",
            "pos_dir": EXPORTS_DIR / "pos_mr1",
            "zip_name": "MR1_Gerbers.zip",
        },
        {
            "name": "Amplifier",
            "pcb": REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb",
            "sch": REPO_ROOT / "Amplifier" / "Amplifier.kicad_sch",
            "gerber_dir": EXPORTS_DIR / "gerbers_amplifier",
            "pos_dir": EXPORTS_DIR / "pos_amplifier",
            "zip_name": "Amplifier_Gerbers.zip",
        },
        {
            "name": "Pump",
            "pcb": REPO_ROOT / "Pump" / "Pump.kicad_pcb",
            "sch": REPO_ROOT / "Pump" / "Pump.kicad_sch",
            "gerber_dir": EXPORTS_DIR / "gerbers_pump",
            "pos_dir": EXPORTS_DIR / "pos_pump",
            "zip_name": "Pump_Gerbers.zip",
        },
        {
            "name": "Interposer",
            "pcb": REPO_ROOT / "Interposer" / "Interposer.kicad_pcb",
            "sch": REPO_ROOT / "Interposer" / "Interposer.kicad_sch",
            "gerber_dir": EXPORTS_DIR / "gerbers_interposer",
            "pos_dir": EXPORTS_DIR / "pos_interposer",
            "zip_name": "Interposer_Gerbers.zip",
        },
    ]

    schematics_dir = EXPORTS_DIR / "schematics"
    bom_dir = EXPORTS_DIR / "bom"
    schematics_dir.mkdir(parents=True, exist_ok=True)
    bom_dir.mkdir(parents=True, exist_ok=True)

    success = True
    for b in boards:
        b_name = b["name"]
        b["gerber_dir"].mkdir(parents=True, exist_ok=True)
        b["pos_dir"].mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"  Processing {b_name}...")

        # 1. Gerbers
        g_cmd = [kicad_cli, "pcb", "export", "gerbers", "--output", str(b["gerber_dir"]) + os.sep, str(b["pcb"])]
        subprocess.run(g_cmd, check=True, capture_output=True)

        # 2. Drill
        d_cmd = [kicad_cli, "pcb", "export", "drill", "--output", str(b["gerber_dir"]) + os.sep, str(b["pcb"])]
        subprocess.run(d_cmd, check=True, capture_output=True)

        # 3. Position / Pick and place
        pos_out = b["pos_dir"] / f"{b_name}-pos.csv"
        p_cmd = [kicad_cli, "pcb", "export", "pos", "--output", str(pos_out), "--format", "csv", "--units", "mm", str(b["pcb"])]
        subprocess.run(p_cmd, check=True, capture_output=True)

        # 4. Schematic PDF
        pdf_out = schematics_dir / f"{b_name}.pdf"
        s_cmd = [kicad_cli, "sch", "export", "pdf", "--output", str(pdf_out), str(b["sch"])]
        subprocess.run(s_cmd, check=True, capture_output=True)

        # 5. Bill of Materials CSV
        bom_out = bom_dir / f"{b_name}_BOM.csv"
        b_cmd = [kicad_cli, "sch", "export", "bom", "--output", str(bom_out), str(b["sch"])]
        subprocess.run(b_cmd, check=True, capture_output=True)

        # 6. Create ready-to-order Gerber ZIP archive
        zip_path = EXPORTS_DIR / b["zip_name"]
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for g_file in b["gerber_dir"].iterdir():
                if g_file.is_file():
                    zf.write(g_file, arcname=g_file.name)

        if verbose:
            print(f"  [OK] {b_name}: Gerbers, Drill, POS, PDF, BOM, and {b['zip_name']} created.")

    return success


def export_wiring(verbose=True):
    """Render WireViz diagrams for reader wiring harness and fluid tubing."""
    if verbose:
        print("\n[3/5] Exporting Wiring and Tubing Documentation...")
    wv = find_wireviz()
    if not wv:
        print("  [WARN] Warning: wireviz not found. Skipping wiring documentation.")
        return False

    targets = [
        ("wiring/reader_wiring.yaml", EXPORTS_DIR / "reader_wiring"),
        ("wiring/reader_tubing.yaml", EXPORTS_DIR / "reader_tubing"),
    ]

    env = os.environ.copy()
    venv_dir = str(Path(sys.executable).parent)
    if venv_dir not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = venv_dir + os.pathsep + env.get("PATH", "")
    if not shutil.which("dot", path=env.get("PATH", "")):
        candidate_paths = [
            Path.home() / "miniconda3" / "bin",
            Path.home() / "anaconda3" / "bin",
            Path.home() / ".local" / "bin",
            Path("/usr/bin"),
            Path("/usr/local/bin"),
            Path("/opt/homebrew/bin"),
        ]
        for extra in candidate_paths:
            if (extra / "dot").exists():
                env["PATH"] = str(extra) + os.pathsep + env.get("PATH", "")
                break

    for yaml_rel, out_dir in targets:
        yaml_path = REPO_ROOT / yaml_rel
        out_dir.mkdir(parents=True, exist_ok=True)
        cmd = [wv, str(yaml_path), "-o", str(out_dir)]
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, env=env)
        if res.returncode == 0:
            if verbose:
                print(f"  [OK] Rendered {yaml_path.name} -> {out_dir.relative_to(REPO_ROOT)}")
        else:
            print(f"  [FAIL] Failed rendering {yaml_path.name}:\n{res.stderr}")

    return True


def export_firmware(verbose=True):
    """Compile and stage ESP32-S3 firmware binaries."""
    if verbose:
        print("\n[4/5] Building & Staging ESP32-S3 Firmware...")
    pio = find_pio()
    if not pio:
        print("  [WARN] Warning: PlatformIO (pio) not found. Skipping firmware build.")
        return False

    fw_dir = REPO_ROOT / "MR1_firmware" if (REPO_ROOT / "MR1_firmware").exists() else REPO_ROOT / "firmware"
    out_fw_dir = EXPORTS_DIR / "firmware"
    out_fw_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    venv_dir = str(Path(sys.executable).parent)
    if venv_dir not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = venv_dir + os.pathsep + env.get("PATH", "")

    cmd = [pio, "run"]
    res = subprocess.run(cmd, cwd=fw_dir, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"  [FAIL] Firmware build failed:\n{res.stderr}")
        return False

    # Stage binaries
    build_dir = fw_dir / ".pio" / "build" / "esp32s3"
    staged = []
    for bin_name in ["firmware.bin", "bootloader.bin", "partitions.bin"]:
        src_bin = build_dir / bin_name
        if src_bin.exists():
            dst_bin = out_fw_dir / bin_name
            shutil.copy2(src_bin, dst_bin)
            staged.append(bin_name)

    if verbose:
        print(f"  [OK] Staged firmware binaries to {out_fw_dir.relative_to(REPO_ROOT)}: {', '.join(staged)}")

    return True


def get_git_short_sha():
    """Retrieve git short commit SHA or 'unknown' if not a git repo."""
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def archive_release(version, verbose=True):
    """Bundle board Gerbers, drill, and BOM into a release archive with SHA256SUMS.txt."""
    if verbose:
        print(f"\n[RELEASE] Archiving Hardware Release Artifacts for version: {version}...")

    # Ensure KiCad exports are built
    export_kicad(verbose=verbose)

    sha = get_git_short_sha()
    release_dir = REPO_ROOT / "releases" / version
    release_dir.mkdir(parents=True, exist_ok=True)

    boards = ["MR1", "Amplifier", "Pump", "Interposer"]
    release_files = []

    for b_name in boards:
        src_zip = EXPORTS_DIR / f"{b_name}_Gerbers.zip"
        dst_zip_name = f"{b_name}_Gerbers_{sha}.zip"
        dst_zip = release_dir / dst_zip_name

        if src_zip.exists():
            shutil.copy2(src_zip, dst_zip)
            release_files.append(dst_zip)
            if verbose:
                print(f"  [OK] Bundled {b_name} -> releases/{version}/{dst_zip_name}")
        else:
            print(f"  [WARN] Source Gerber zip {src_zip.name} not found!")

        bom_src = EXPORTS_DIR / "bom" / f"{b_name}_BOM.csv"
        if bom_src.exists():
            dst_bom = release_dir / f"{b_name}_BOM_{sha}.csv"
            shutil.copy2(bom_src, dst_bom)
            release_files.append(dst_bom)

        sch_src = EXPORTS_DIR / "schematics" / f"{b_name}.pdf"
        if sch_src.exists():
            dst_sch = release_dir / f"{b_name}_Schematic_{sha}.pdf"
            shutil.copy2(sch_src, dst_sch)
            release_files.append(dst_sch)

    # Generate SHA256SUMS.txt
    sha256_path = release_dir / "SHA256SUMS.txt"
    with open(sha256_path, "w", encoding="utf-8") as fh:
        for fpath in sorted(release_files):
            h = hashlib.sha256()
            with open(fpath, "rb") as sf:
                while chunk := sf.read(65536):
                    h.update(chunk)
            fh.write(f"{h.hexdigest()}  {fpath.name}\n")

    if verbose:
        print(f"  [OK] Created {sha256_path.relative_to(REPO_ROOT)}")
        print("\n=================================================================")
        print(f"  [RELEASE BUNDLE CREATED] -> releases/{version}/")
        print("  To lock this hardware fabrication bundle in Git, execute:")
        print(f"    git tag -a hw-{version}-revA -m \"Hardware Fabrication Release {version} (commit {sha})\"")
        print(f"    git push origin hw-{version}-revA")
        print("=================================================================\n")

    return True


def generate_manifest(verbose=True):
    """Generate SHA-256 integrity manifest for all files in exports/."""
    if verbose:
        print("\n[5/5] Generating Exports Manifest (SHA-256 Tracking)...")

    manifest = {
        "project": "MR1 / MR1 Nanopore Reader",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "deliverables": {}
    }

    categories = {
        ".stl": "3d_mesh_printing",
        ".step": "cad_parametric_brep",
        ".dxf": "2d_machining_and_pcb_outline",
        ".pdf": "schematic_documentation",
        ".csv": "bill_of_materials",
        ".zip": "pcb_manufacturing_gerber_pack",
        ".bin": "firmware_binary",
        ".png": "visual_documentation",
        ".svg": "vector_documentation",
        ".html": "interactive_documentation",
        ".tsv": "tabular_wire_list",
        ".gtl": "gerber_layer",
        ".gbl": "gerber_layer",
        ".drl": "drill_file",
        ".pos": "pick_and_place_positions",
    }

    for root, _, files in os.walk(EXPORTS_DIR):
        for f in sorted(files):
            if f == "manifest.json":
                continue
            f_path = Path(root) / f
            rel_path = f_path.relative_to(EXPORTS_DIR).as_posix()
            ext = f_path.suffix.lower()
            cat = categories.get(ext, "other")

            h = hashlib.sha256()
            with open(f_path, "rb") as fh:
                while True:
                    chunk = fh.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)

            manifest["deliverables"][rel_path] = {
                "size_bytes": f_path.stat().st_size,
                "sha256": h.hexdigest(),
                "category": cat,
            }

    manifest_path = EXPORTS_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    if verbose:
        print(f"  [OK] Manifest generated: {len(manifest['deliverables'])} files indexed in {manifest_path.name}")

    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description="MR1 Deliverables Export Manager")
    parser.add_argument("--all", action="store_true", help="Run all export targets")
    parser.add_argument("--cad", action="store_true", help="Export 3D STL/STEP and 2D DXF models")
    parser.add_argument("--kicad", action="store_true", help="Export KiCad Gerbers, BOM, POS, and PDFs")
    parser.add_argument("--wiring", "--wireviz", dest="wiring", action="store_true", help="Export WireViz harness diagrams")
    parser.add_argument("--firmware", action="store_true", help="Build and stage ESP32-S3 firmware")
    parser.add_argument("--manifest", action="store_true", help="Generate exports/manifest.json")
    parser.add_argument("--check", action="store_true", help="Validate existing exports integrity")
    parser.add_argument("--release-tag", "--archive-release", dest="release_tag", metavar="VERSION", type=str, help="Bundle and lock release Gerbers in releases/<version>/")

    args = parser.parse_args()

    if args.release_tag:
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        archive_release(args.release_tag)
        sys.exit(0)

    # Default to all if no specific target selected
    if not (args.all or args.cad or args.kicad or args.wiring or args.firmware or args.manifest or args.check):
        args.all = True

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("  MR1 Nanopore Reader - Project Deliverables Exporter")
    print("=================================================================")

    if args.all or args.cad:
        export_cad()
    if args.all or args.kicad:
        export_kicad()
    if args.all or args.wiring:
        export_wiring()
    if args.all or args.firmware:
        export_firmware()
    if args.all or args.manifest:
        generate_manifest()

    if args.check:
        print("\nVerifying Export Deliverables...")
        manifest_file = EXPORTS_DIR / "manifest.json"
        if not manifest_file.exists():
            print("  [FAIL] manifest.json does not exist. Run with --manifest first.")
            sys.exit(1)
        with open(manifest_file, "r") as fh:
            data = json.load(fh)
        missing = []
        hash_mismatches = []
        for path_str, meta in data["deliverables"].items():
            fpath = EXPORTS_DIR / path_str
            if not fpath.exists():
                missing.append(path_str)
            else:
                h = hashlib.sha256()
                with open(fpath, "rb") as fh:
                    while chunk := fh.read(65536):
                        h.update(chunk)
                if h.hexdigest() != meta.get("sha256"):
                    hash_mismatches.append(path_str)
        if missing:
            print(f"  [FAIL] {len(missing)} files missing from exports: {missing[:5]}...")
            sys.exit(1)
        if hash_mismatches:
            print(f"  [FAIL] {len(hash_mismatches)} files have SHA-256 mismatches: {hash_mismatches[:5]}...")
            sys.exit(1)
        print(f"  [OK] All {len(data['deliverables'])} indexed deliverables verified on disk (existence & SHA-256).")

    print("\n[SUCCESS] Export operations completed.")


if __name__ == "__main__":
    main()