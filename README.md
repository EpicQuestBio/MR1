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


BOM
Female Luer Fitting Female Luer Thread Style Panel Mount 1/4-28 UNF to Barb, 1/8" (3.2 mm) ID Tubing, White Nylon
https://www.fluidcontrol24.com/ftllb230-1-female-luer-fitting-female-luer-thread-style-panel-mount-1-4-28-unf-to-barb-1-8-3-2-mm-id-tubing-white-nylon.html?q=Female+Luer+panel+mount&noindex=true
Article no FTLLB230-1
	1/4-28 UNF
	Luer female
    Colour	Clear
Tubing size	1/8" (3.2mm)

QTY, 4 for reader and 4 for pump

Hose connector plastic, L-piece, for hose connections Ø 3mm
Material 
Nylon
 Tubing size 
1/8" (3.2mm)
The primary benefits of kentSystems L-piece fittings are their robust construction. They offer a cost-effective variant for connecting two hoses at a 90 ° angle.

1/8" Hose Barb x Female Lug Natural Polypropylene Bulkhead Luer
Item 96547
Out of Stock (On Order)
$0.54/Each

1/8" Hose Barb x Female Threaded Natural Polypropylene Bulkhead Luer
Item 96550
In Stock
$0.54/Each