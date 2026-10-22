# =============================================================================
# MR1 Nanopore Reader ? Project Makefile
# =============================================================================

# Detect virtual environment Python if present
ifeq ($(OS),Windows_NT)
    VENV_PYTHON := $(wildcard .venv/Scripts/python.exe)
else
    VENV_PYTHON := $(wildcard .venv/bin/python)
endif

ifneq ($(VENV_PYTHON),)
    PYTHON ?= $(VENV_PYTHON)
else
    PYTHON ?= python
endif

.PHONY: all export export-cad export-kicad export-wiring export-firmware manifest check test test-e2e clean help

all: export

export:
	$(PYTHON) scripts/export_manager.py --all

export-cad:
	$(PYTHON) scripts/export_manager.py --cad

export-kicad:
	$(PYTHON) scripts/export_manager.py --kicad

export-wiring:
	$(PYTHON) scripts/export_manager.py --wiring

export-firmware:
	$(PYTHON) scripts/export_manager.py --firmware

manifest:
	$(PYTHON) scripts/export_manager.py --manifest

check:
	$(PYTHON) scripts/export_manager.py --check

test:
	$(PYTHON) run_tests.py

test-e2e:
	$(PYTHON) tests/test_exports_e2e.py

clean:
	git clean -fxd exports/ firmware/.pio/

help:
	@echo "MR1 Nanopore Reader ? Build & Export Commands:"
	@echo "  make export          Export all deliverables (CAD, KiCad, Wiring, Firmware)"
	@echo "  make export-cad      Export 3D solids (STEP, STL) & 2D profiles (DXF)"
	@echo "  make export-kicad    Export KiCad Gerbers, Drill, POS, BOM, and PDF schematics"
	@echo "  make export-wiring   Export WireViz wiring harness and fluid tubing diagrams"
	@echo "  make export-firmware Compile and stage ESP32-S3 firmware binaries"
	@echo "  make manifest        Generate exports/manifest.json with SHA-256 hashes"
	@echo "  make check           Verify that all indexed deliverables exist on disk"
	@echo "  make test            Run unit tests and CAD collision clearance checks"
	@echo "  make test-e2e        Run end-to-end deliverables validation test"
	@echo "  make clean           Remove generated build artifacts and staged exports"