#!/usr/bin/env python3
# Created by Lawrence R. Kincheloe III / Molecular Reality Corp (2026).
# Dedicated to the public domain under CC0 1.0 Universal (CC0-1.0).
# SPDX-License-Identifier: CC0-1.0

"""
Single-File Bundler for MR1 Signal Viewer
========================================
Inlines styles.css, src/signal.js, and src/app.js into signal-viewer/standalone.html
and provides verification (--check) to ensure standalone.html is synchronized.
"""

import os
import sys
import re
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VIEWER_DIR = os.path.join(REPO_ROOT, "signal-viewer")

INDEX_HTML_PATH = os.path.join(VIEWER_DIR, "index.html")
STYLES_CSS_PATH = os.path.join(VIEWER_DIR, "styles.css")
SIGNAL_JS_PATH = os.path.join(VIEWER_DIR, "src", "signal.js")
APP_JS_PATH = os.path.join(VIEWER_DIR, "src", "app.js")
STANDALONE_HTML_PATH = os.path.join(VIEWER_DIR, "standalone.html")


def generate_bundle() -> str:
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    with open(STYLES_CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    with open(SIGNAL_JS_PATH, "r", encoding="utf-8") as f:
        signal_js = f.read()

    with open(APP_JS_PATH, "r", encoding="utf-8") as f:
        app_js = f.read()

    # Clean exports and imports from JS files for inlining
    # Remove imports from app.js (e.g. import { ... } from './signal.js';)
    cleaned_app_js = re.sub(r'import\s+\{[^}]*\}\s+from\s+[\'"][^\'"]*[\'"];?\n?', '', app_js)
    # Remove export keywords from app_js and signal_js
    cleaned_signal_js = re.sub(r'\bexport\s+(class|const|function|let|var)\b', r'\1', signal_js)
    cleaned_app_js = re.sub(r'\bexport\s+(class|const|function|let|var)\b', r'\1', cleaned_app_js)

    combined_js = (
        "// Inlined from src/signal.js\n"
        + cleaned_signal_js.strip()
        + "\n\n// Inlined from src/app.js\n"
        + cleaned_app_js.strip()
    )

    # Replace <link rel="stylesheet" href="./styles.css"> with <style>...</style>
    css_tag = f"<style>\n{css.strip()}\n  </style>"
    bundled = re.sub(r'<link\s+rel=["\']stylesheet["\']\s+href=["\']\./styles\.css["\']\s*/?>', css_tag, html)

    # Replace <script type="module" src="./src/app.js"></script> with <script>...</script>
    js_tag = f"<script>\n{combined_js}\n  </script>"
    bundled = re.sub(r'<script\s+type=["\']module["\']\s+src=["\']\./src/app\.js["\']\s*></script>', js_tag, bundled)

    return bundled


def main():
    parser = argparse.ArgumentParser(description="MR1 Signal Viewer Bundler")
    parser.add_argument("--check", action="store_true", help="Check if standalone.html matches bundle")
    parser.add_argument("--write", action="store_true", default=True, help="Write bundle to standalone.html")
    args = parser.parse_args()

    bundle = generate_bundle()

    if args.check:
        if not os.path.exists(STANDALONE_HTML_PATH):
            print(f"[ERROR] {STANDALONE_HTML_PATH} does not exist.")
            sys.exit(1)
        with open(STANDALONE_HTML_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
        if existing.strip() != bundle.strip():
            print("[ERROR] standalone.html is out of sync with index.html, styles.css, or src/*. Run python3 scripts/bundle_signal_viewer.py --write.")
            sys.exit(1)
        print("[OK] standalone.html is perfectly synchronized.")
        sys.exit(0)

    with open(STANDALONE_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(bundle)
    print(f"[OK] Wrote bundled standalone file to {STANDALONE_HTML_PATH}")


if __name__ == "__main__":
    main()
