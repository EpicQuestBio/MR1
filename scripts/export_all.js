
const fs = require('fs');
const path = require('path');

// Change working directory to project root if executed from scripts folder
const projectRoot = path.resolve(__dirname, '..');
if (process.cwd() !== projectRoot && fs.existsSync(path.join(projectRoot, 'package.json'))) {
    process.chdir(projectRoot);
}

const { ensureBOSL2 } = require('./lib_setup');

const importOpenSCAD = async () => {
    // Dynamic import is needed for ESM modules in CommonJS
    const filePath = path.resolve(projectRoot, 'node_modules/openscad-wasm/lib/openscad-wasm/openscad.js');
    const mod = await import('file://' + filePath);
    return mod.default || mod.createOpenSCAD || mod;
};

const SCAD_FILE = 'sentinel_nanopore_reader.scad';
const CONSTANTS_FILE = 'constants.scad';
const OUTPUT_DIR = 'exports';

async function main() {
  console.log('Initializing Export Script...');

  // 1. Ensure BOSL2 Library exists
  await ensureBOSL2();

  // 2. Prepare Output Directory
  if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const createOpenSCAD = await importOpenSCAD();

  // Read SCAD file
  let scadContent = fs.readFileSync(SCAD_FILE, 'utf8');

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
      if (requested.length > 0 && !requested.includes('all')) {
          modes = modes.filter(m => requested.includes(m));
          console.log(`Filtering to: ${modes.join(', ')}`);
      } else if (requested.includes('all')) {
          console.log('Exporting all modes.');
      }
  }

  console.log(`Found ${modes.length} output modes to export.`);

  for (const mode of modes) {
    console.log(`Exporting ${mode}...`);
    try {
        const wrapper = await createOpenSCAD({ noInitialRun: true });
        const instance = typeof wrapper.getInstance === 'function' ? wrapper.getInstance() : wrapper;

        // Workaround for "[OpenSCAD]: Could not initialize localization" warning
        try {
            instance.FS.mkdir('/locale');
        } catch (e) {
            // Ignore if directory exists
        }

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
                // Force forward slashes for VFS paths (Windows compatibility)
                const virt = virtualPath === '/' ? `/${item}` : `${virtualPath}/${item}`;
                const stat = fs.statSync(loc);
                if (stat.isDirectory()) {
                    loadDir(loc, virt);
                } else {
                    instance.FS.writeFile(virt, fs.readFileSync(loc));
                }
            }
        }

        // Mount 'libraries' to '/libraries' so 'include <libraries/BOSL2/std.scad>' works
        loadDir('libraries', '/libraries');
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
