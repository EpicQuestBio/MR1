const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const importOpenSCAD = async () => {
    // Dynamic import is needed for ESM modules in CommonJS
    const mod = await import('openscad-wasm');
    return mod.createOpenSCAD;
};

const SCAD_FILE = 'sentinel_nanopore_reader.scad';
const CONSTANTS_FILE = 'constants.scad';
const LIB_DIR = 'libraries/BOSL2';
const OUTPUT_DIR = 'exports';

async function main() {
  console.log('Initializing Export Script...');

  // 1. Ensure BOSL2 Library exists
  if (!fs.existsSync(LIB_DIR)) {
      console.log('BOSL2 library not found. Cloning...');
      try {
        fs.mkdirSync('libraries', { recursive: true });
        execSync('git clone --depth 1 https://github.com/BOSL2/BOSL2.git libraries/BOSL2', { stdio: 'inherit' });
        console.log('BOSL2 cloned successfully.');
      } catch (e) {
          console.error('Failed to clone BOSL2:', e.message);
          // Fallback logic
          console.log('Attempting alternative download (zip)...');
          try {
             execSync('curl -L -o bosl2.zip https://github.com/BelfrySCAD/BOSL2/archive/refs/heads/master.zip');
             execSync('unzip -q bosl2.zip -d libraries/ && rm -rf libraries/BOSL2 && mv libraries/BOSL2-master libraries/BOSL2 && rm bosl2.zip');
          } catch(e2) {
             console.error('Failed to download BOSL2 zip:', e2.message);
             process.exit(1);
          }
      }
  }

  // 2. Prepare Output Directory
  if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const createOpenSCAD = await importOpenSCAD();

  // Read SCAD file
  let scadContent = fs.readFileSync(SCAD_FILE, 'utf8');

  // WORKAROUND: openscad-wasm compatibility
  console.log('Applying in-memory patch for WASM compatibility...');
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
    console.error('Could not find Output_Mode definition in SCAD file or constants.scad.');
    process.exit(1);
  }
  let modes = modeMatch[1].split(',').map(s => s.trim());

  // Command line filtering
  const args = process.argv.slice(2);
  if (args.length > 0) {
      const requested = args.filter(a => !a.startsWith('-'));
      if (requested.length > 0) {
          modes = modes.filter(m => requested.includes(m));
          console.log(`Filtering to: ${modes.join(', ')}`);
      }
  }

  console.log(`Found ${modes.length} output modes to export.`);

  for (const mode of modes) {
    console.log(`Exporting ${mode}...`);
    try {
        const wrapper = await createOpenSCAD({ noInitialRun: true });
        const instance = wrapper.getInstance();

        // Load files
        instance.FS.writeFile('/' + SCAD_FILE, scadContent);
        if (fs.existsSync(CONSTANTS_FILE)) {
             instance.FS.writeFile('/' + CONSTANTS_FILE, fs.readFileSync(CONSTANTS_FILE));
        }

        // Load BOSL2 & Modules
        function loadDir(localPath, virtualPath) {
            if (!fs.existsSync(localPath)) return;
            try { instance.FS.mkdir(virtualPath); } catch(e) {}
            const items = fs.readdirSync(localPath);
            for (const item of items) {
                const loc = path.join(localPath, item);
                const virt = path.join(virtualPath, item);
                const stat = fs.statSync(loc);
                if (stat.isDirectory()) {
                    loadDir(loc, virt);
                } else {
                    instance.FS.writeFile(virt, fs.readFileSync(loc));
                }
            }
        }
        loadDir(LIB_DIR, '/BOSL2');
        loadDir('modules', '/modules');

        let ext = 'stl';
        if (mode.endsWith('_DXF')) ext = 'dxf';
        if (mode === 'Assembly') ext = 'png';
        if (mode.endsWith('_STL')) ext = 'stl';

        if (ext === 'png') {
            console.log(`  Skipping PNG render for ${mode} (headless unsupported)`);
            continue;
        }

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
            console.log(`  Saved ${outFile}`);
        } else {
            console.error(`  Failed to generate ${outFile}`);
        }

    } catch (e) {
        console.error(`Exception rendering ${mode}:`, e);
    }
  }

  console.log('\nExport complete.');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
