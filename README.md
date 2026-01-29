# daemon-pore

## Exporting Files

This project includes a script to automatically export all defined parts (STLs and DXFs) from the OpenSCAD source.

### Setup

Ensure dependencies are installed:
```bash
npm install
```

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
