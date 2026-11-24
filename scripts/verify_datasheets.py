#!/usr/bin/env python3
"""
Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
SPDX-License-Identifier: CC0-1.0

Download manufacturer datasheets for all BOM parts across MR1 boards, extract
key specifications (package, pin configuration, supply/voltage/value ratings)
via pdftotext + LCSC catalog metadata, and cross-check against KiCad
schematics/PCBs.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BOM_GLOB = str(REPO_ROOT / "exports" / "bom" / "*_BOM.csv")
CATALOG_DIR = REPO_ROOT / "datasheets" / "catalog"
AMPLIFIER_DIR = REPO_ROOT / "datasheets" / "amplifier"
INDEX_PATH = CATALOG_DIR / "index.json"
REPORT_PATH = REPO_ROOT / "docs" / "DATASHEET_VERIFICATION_REPORT.md"

LCSC_DETAIL_URL = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={code}"

# Extra non-LCSC / manufacturer fallback URLs for parts not stocked in LCSC
FALLBACK_PDF_URLS: dict[str, str] = {
    "LMP7721": "https://www.ti.com/lit/ds/symlink/lmp7721.pdf",
    "OPA2192IDR": "https://www.ti.com/lit/ds/symlink/opa2192.pdf",
    "LP5907MFX-1.8/NOPB": "https://www.ti.com/lit/ds/symlink/lp5907.pdf",
    "NDS7002A": "https://www.onsemi.com/pdf/datasheet/nds7002a-d.pdf",
    "MMBT3906": "https://www.onsemi.com/pdf/datasheet/mmbt3906lt1-d.pdf",
    "MBR0540": "https://www.onsemi.com/pdf/datasheet/mbr0540t1-d.pdf",
}


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")


def fetch_lcsc_detail(code: str) -> dict[str, Any]:
    url = LCSC_DETAIL_URL.format(code=code)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        res = data.get("result") or {}
        if not res:
            return {"lcsc": code, "status": "NOT_IN_LCSC"}
        params = {
            p.get("paramNameEn", ""): p.get("paramValueEn", "")
            for p in (res.get("paramVOList") or [])
            if p.get("paramNameEn")
        }
        return {
            "lcsc": code,
            "status": "OK",
            "mpn": res.get("productModel") or "",
            "brand": res.get("brandNameEn") or "",
            "package": res.get("encapStandard") or "",
            "stock": res.get("stockNumber"),
            "pdf_url": res.get("pdfUrl") or "",
            "params": params,
        }
    except Exception as exc:
        return {"lcsc": code, "status": f"ERROR: {exc}"}


def is_valid_pdf(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    with open(path, "rb") as f:
        return f.read(5) == b"%PDF-"


def download_pdf(url: str, dest: Path) -> tuple[bool, str]:
    if is_valid_pdf(dest):
        return True, "cached"
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "25", "-A", "Mozilla/5.0", url, "-o", str(dest)],
        capture_output=True,
    )
    if r.returncode == 0 and is_valid_pdf(dest):
        return True, "downloaded"
    if dest.exists():
        dest.unlink()
    return False, f"download_failed(rc={r.returncode})"


def extract_pdf_summary(pdf_path: Path) -> dict[str, Any]:
    r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], capture_output=True)
    if r.returncode != 0:
        return {"ok": False, "error": f"pdftotext rc={r.returncode}"}
    text = r.stdout.decode("utf-8", errors="ignore")
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]

    # Extract lines mentioning Pin Configuration / Pin Description / Absolute Maximum
    pin_lines: list[str] = []
    abs_max_lines: list[str] = []
    for i, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in ("pin description", "pin configuration", "pin functions", "pinout")):
            pin_lines.extend(lines[i : min(i + 20, len(lines))])
            if len(pin_lines) >= 35:
                break
    for i, line in enumerate(lines):
        low = line.lower()
        if "absolute maximum" in low:
            abs_max_lines.extend(lines[i : min(i + 12, len(lines))])
            break

    return {
        "ok": True,
        "chars": len(text),
        "lines": len(lines),
        "title_sample": lines[:5],
        "pin_snippet": pin_lines[:35],
        "abs_max_snippet": abs_max_lines[:12],
    }


def load_boms(board_filter: str | None = None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for path in sorted(glob.glob(BOM_GLOB)):
        board = Path(path).stem.replace("_BOM", "")
        if board_filter and board.lower() != board_filter.lower():
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                items.append(
                    {
                        "board": board,
                        "designator": row["Designator"].strip(),
                        "comment": row["Comment"].strip(),
                        "footprint": row["Footprint"].strip(),
                        "lcsc": row["LCSC Part #"].strip(),
                    }
                )
    return items


def check_package_match(footprint: str, pkg: str) -> str:
    if not pkg:
        return "NO_PKG_META"
    fp_l = footprint.lower()
    pkg_l = pkg.lower()
    # Direct size/package checks
    for token in ("0402", "0603", "0805", "1206", "sod-123", "sot-23-5", "sot-23-6", "sot-23", "soic-8", "msop-8", "msop-10", "lfcsp-16"):
        if token in pkg_l:
            if token == "soic-8" and ("so-8" in fp_l or "soic-8" in fp_l):
                return "OK"
            if token == "sot-23" and ("sot-23-5" in fp_l or "sot-23-6" in fp_l):
                return f"MISMATCH({pkg} vs {footprint})"
            if token in fp_l:
                return "OK"
            return f"MISMATCH({pkg} vs {footprint})"
    return f"CHECK({pkg} vs {footprint})"


def extract_amplifier_pcb_pins() -> dict[str, list[tuple[str, str]]]:
    pcb_path = REPO_ROOT / "Amplifier" / "Amplifier.kicad_pcb"
    text = pcb_path.read_text(encoding="utf-8")
    out: dict[str, list[tuple[str, str]]] = {}
    for fp in text.split("\n\t(footprint ")[1:]:
        m_ref = re.search(r'"Reference" "([^"]+)"', fp)
        if not m_ref:
            continue
        ref = m_ref.group(1)
        if ref[0] not in ("U", "Q", "D", "J"):
            continue
        pads = re.findall(r'\(pad "([^"]+)" smd[\s\S]*?\(net "([^"]+)"\)', fp)
        if pads:
            out[ref] = sorted(set(pads), key=lambda x: (int(x[0]) if x[0].isdigit() else 999, x[0]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and verify datasheets for MR1 BOMs.")
    parser.add_argument("--board", help="Filter to a single board (e.g. Amplifier, MR1, Pump, Interposer)")
    parser.add_argument("--skip-download", action="store_true", help="Use cached LCSC index/PDFs only")
    args = parser.parse_args()

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    bom_items = load_boms(args.board)
    unique_lcsc = sorted({it["lcsc"] for it in bom_items if re.fullmatch(r"C\d+", it["lcsc"])})

    index: dict[str, Any] = {}
    if INDEX_PATH.exists():
        index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    if not args.skip_download:
        to_fetch = [c for c in unique_lcsc if c not in index or index[c].get("status") != "OK"]
        if to_fetch:
            print(f"[LCSC] Fetching metadata for {len(to_fetch)} parts...")
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(fetch_lcsc_detail, c): c for c in to_fetch}
                for fut in as_completed(futs):
                    meta = fut.result()
                    index[meta["lcsc"]] = meta

        # Download PDFs for all OK entries
        dl_jobs: list[tuple[str, str, Path]] = []
        for code in unique_lcsc:
            meta = index.get(code, {})
            pdf_url = meta.get("pdf_url")
            if pdf_url:
                mpn = sanitize_filename(meta.get("mpn") or code)
                dest = CATALOG_DIR / f"{code}_{mpn}.pdf"
                meta["pdf_file"] = str(dest.relative_to(REPO_ROOT))
                if not is_valid_pdf(dest):
                    dl_jobs.append((code, pdf_url, dest))

        if dl_jobs:
            print(f"[PDF] Downloading {len(dl_jobs)} datasheets...")
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(download_pdf, url, dest): (code, dest) for code, url, dest in dl_jobs}
                for fut in as_completed(futs):
                    code, dest = futs[fut]
                    ok, msg = fut.result()
                    index[code]["pdf_status"] = msg
                    if not ok:
                        print(f"  [WARN] {code}: {msg}")

        # Ensure cached PDFs have pdf_status set
        for code in unique_lcsc:
            meta = index.get(code, {})
            pf = meta.get("pdf_file")
            if pf and is_valid_pdf(REPO_ROOT / pf):
                meta["pdf_status"] = "OK"

        INDEX_PATH.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")

    # Extract text summaries for Amplifier active parts (plus any valid PDF in catalog)
    pdf_summaries: dict[str, Any] = {}
    for code in unique_lcsc:
        meta = index.get(code, {})
        pf = meta.get("pdf_file")
        if pf and is_valid_pdf(REPO_ROOT / pf):
            pdf_summaries[code] = extract_pdf_summary(REPO_ROOT / pf)

    # Check Amplifier PCB pins
    amp_pcb_pins = extract_amplifier_pcb_pins()

    # Build Markdown verification report
    lines: list[str] = [
        "# MR1 Datasheet & Part Verification Report",
        "",
        f"Generated by `scripts/verify_datasheets.py` from `{len(bom_items)}` BOM lines across `{len(unique_lcsc)}` unique LCSC parts.",
        "",
        "## 1. BOM Package & Datasheet Coverage",
        "",
        "| Board | Ref | BOM Comment | Footprint | LCSC | MPN (LCSC) | Package Check | Datasheet PDF |",
        "|---|---|---|---|---|---|---|---|",
    ]

    pkg_mismatches = 0
    missing_pdfs = 0
    for it in bom_items:
        code = it["lcsc"]
        meta = index.get(code, {})
        mpn = meta.get("mpn", "—")
        pkg = meta.get("package", "")
        pkg_chk = check_package_match(it["footprint"], pkg) if code.startswith("C") and code[1:].isdigit() else "NON_LCSC"
        if pkg_chk.startswith("MISMATCH"):
            pkg_mismatches += 1
        pf = meta.get("pdf_file", "")
        if pf and is_valid_pdf(REPO_ROOT / pf):
            ds_cell = f"`{Path(pf).name}`"
        else:
            ds_cell = "MISSING"
            if it["designator"][0] in ("U", "Q", "D", "J", "P") or it["designator"] == "R1":
                missing_pdfs += 1
        lines.append(
            f"| {it['board']} | {it['designator']} | {it['comment']} | `{it['footprint']}` | `{code}` | `{mpn}` | {pkg_chk} | {ds_cell} |"
        )

    lines.extend([
        "",
        "## 2. Amplifier Active / Connector Pin Nets (From `Amplifier.kicad_pcb`)",
        "",
        "Verify every row below directly against the downloaded PDF pin table:",
        "",
    ])
    for ref in sorted(amp_pcb_pins):
        pin_str = ", ".join(f"**{p}**=`{n}`" for p, n in amp_pcb_pins[ref])
        lines.append(f"- **`{ref}`**: {pin_str}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {REPORT_PATH.relative_to(REPO_ROOT)} | pkg_mismatches={pkg_mismatches} | missing_active_pdfs={missing_pdfs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
