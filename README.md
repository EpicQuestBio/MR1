# daemon-pore

## Exporting Files

This project includes a script to automatically export all defined parts (STLs and DXFs) from the OpenSCAD source.

### Setup

Run the installation script to set up dependencies and the BOSL2 library:
```bash
./install.sh
```
This script handles:
- Checking for Node.js (required for exports).
- Installing NPM dependencies.
- Installing the BOSL2 library (as a git submodule or local download) into `libraries/`.

If you do not have Node.js, the script will still attempt to download the BOSL2 library so you can open the SCAD files in the OpenSCAD GUI.

### Usage

**Export all parts:**
```bash
npm run export
```
This will generate all files defined in the `Output_Mode` list in `constants.scad` and save them to the `exports/` directory.

**Export specific part:**
You can pass the name of the `Output_Mode` as an argument:
```bash
npm run export -- Plate_1_Base_DXF
```
