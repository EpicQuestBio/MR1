const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Reuse logic from render_test.js to setup environment
// This script runs the render process and saves the file stats to golden_manifest.json

const SCAD_FILE = 'sentinel_nanopore_reader.scad';
const CONSTANTS_FILE = 'constants.scad';
const LIB_DIR = 'libraries/BOSL2';
const OUTPUT_DIR = 'output';
const MANIFEST_FILE = 'tests/golden_manifest.json';

const importOpenSCAD = async () => {
    const mod = await import('openscad-wasm/lib/openscad-wasm/openscad.js');
    return mod.default || mod.createOpenSCAD || mod;
};

async function main() {
  const args = process.argv.slice(2);
  // Optional: Pass specific modes to render via CLI
  const limitModes = args.length > 0 ? args : null;

  console.log('Initializing Golden Master Generation...');

  // 1. Ensure BOSL2 Library exists
  if (!fs.existsSync(LIB_DIR)) {
      console.log('BOSL2 library not found. Cloning...');
      try {
        fs.mkdirSync('libraries', { recursive: true });
        execSync('git clone --depth 1 https://github.com/BOSL2/BOSL2.git libraries/BOSL2', { stdio: 'inherit' });
      } catch (e) {
         console.error('Failed to clone BOSL2');
         process.exit(1);
      }
  }

  // 2. Prepare Output Directory
  if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const createOpenSCAD = await importOpenSCAD();

  // Read SCAD file
  let scadContent = fs.readFileSync(SCAD_FILE, 'utf8');

  // WORKAROUND: Remove projection(cut=false)
  scadContent = scadContent.replace(/projection\(cut=false\)\s*/g, '');

  // Parse modes
  let modeMatch = scadContent.match(/Output_Mode\s*=\s*"[^"]*";\s*\/\/\s*\[(.*?)\]/);
  if (!modeMatch) {
      if (fs.existsSync(CONSTANTS_FILE)) {
          const constantsContent = fs.readFileSync(CONSTANTS_FILE, 'utf8');
          modeMatch = constantsContent.match(/Output_Mode\s*=\s*"[^"]*";\s*\/\/\s*\[(.*?)\]/);
      }
  }

  if (!modeMatch) {
    console.error('Could not find Output_Mode definition.');
    process.exit(1);
  }
  let modes = modeMatch[1].split(',').map(s => s.trim());

  if (limitModes) {
      modes = modes.filter(m => limitModes.includes(m));
  }

  // Load existing manifest if present to append/update
  let manifest = {};
  if (fs.existsSync(MANIFEST_FILE)) {
      try {
        manifest = JSON.parse(fs.readFileSync(MANIFEST_FILE, 'utf8'));
      } catch(e) {}
  }

  for (const mode of modes) {
    console.log(`Rendering ${mode}...`);
    try {
        const wrapper = await createOpenSCAD({ noInitialRun: true });
        const instance = wrapper.getInstance ? wrapper.getInstance() : wrapper;

        // Load files
        instance.FS.writeFile('/' + SCAD_FILE, scadContent);
        if (fs.existsSync(CONSTANTS_FILE)) {
             instance.FS.writeFile('/' + CONSTANTS_FILE, fs.readFileSync(CONSTANTS_FILE));
        }

        // Load other root .scad files (like nanopore_wafer_mold.scad) to the root of the virtual filesystem
        const rootFiles = fs.readdirSync(projectRoot);
        for (const file of rootFiles) {
            if (file.endsWith('.scad') && file !== SCAD_FILE && file !== CONSTANTS_FILE) {
                instance.FS.writeFile('/' + file, fs.readFileSync(path.join(projectRoot, file)));
            }
        }

        function loadDir(localPath, virtualPath) {
            if (!fs.existsSync(localPath)) return;
            try { instance.FS.mkdir(virtualPath); } catch(e) {}
            const items = fs.readdirSync(localPath);
            for (const item of items) {
                const loc = path.join(localPath, item);
                const virt = virtualPath === '/' ? `/${item}` : `${virtualPath}/${item}`;
                const stat = fs.statSync(loc);
                if (stat.isDirectory()) {
                    loadDir(loc, virt);
                } else {
                    instance.FS.writeFile(virt, fs.readFileSync(loc));
                }
            }
        }
        loadDir('libraries', '/libraries');
        loadDir('modules', '/modules');

        let ext = 'stl';
        if (mode.endsWith('_DXF')) ext = 'dxf';
        if (mode === 'Assembly') ext = 'png';
        if (mode.endsWith('_STL')) ext = 'stl';

        if (ext === 'png') continue; // Skip PNG

        const outFile = `${mode}.${ext}`;
        const args = [
            '/' + SCAD_FILE,
            '-D', `Output_Mode="${mode}"`,
            '-o', outFile
        ];

        const ret = instance.callMain(args);

        if (ret === 0 && instance.FS.analyzePath('/' + outFile).exists) {
            const data = instance.FS.readFile('/' + outFile);
            fs.writeFileSync(path.join(OUTPUT_DIR, outFile), data);

            // Populate Manifest
            manifest[outFile] = {
                size: data.length,
            };
            console.log(`  Generated ${outFile} (${data.length} bytes)`);
        } else {
            console.error(`  Failed to generate ${outFile}`);
        }

    } catch (e) {
        console.error(`Exception rendering ${mode}:`, e);
    }
  }

  fs.writeFileSync(MANIFEST_FILE, JSON.stringify(manifest, null, 2));
  console.log(`\nGolden Manifest saved to ${MANIFEST_FILE}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
