const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const importOpenSCAD = async () => {
    const mod = await import('openscad-wasm/lib/openscad-wasm/openscad.js');
    return mod.default || mod.createOpenSCAD || mod;
};

const SCAD_FILE = 'sentinel_nanopore_reader.scad';
const CONSTANTS_FILE = 'constants.scad';
const LIB_DIR = 'libraries/BOSL2';
const OUTPUT_DIR = 'output';

async function main() {
  console.log('Initializing Test Harness...');

  // 1. Ensure BOSL2 Library exists
  if (!fs.existsSync(LIB_DIR)) {
      console.log('BOSL2 library not found. Cloning...');
      try {
        fs.mkdirSync('libraries', { recursive: true });
        execSync('git clone --depth 1 https://github.com/BOSL2/BOSL2.git libraries/BOSL2', { stdio: 'inherit' });
      } catch (e) {
          console.error('Failed to clone BOSL2:', e.message);
          // Try zip download...
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
  scadContent = scadContent.replace(/projection\(cut=false\)\s*/g, '');

  // We use sentinel_nanopore_reader.scad logic to load includes correctly,
  // but we want to render just PCB_Active_Stack_3D.
  // We can inject a call to PCB_Active_Stack_3D() and override Output_Mode logic by defining a custom file that includes everything.

  const testScadContent = `
include <constants.scad>
include <modules/common.scad>
include <modules/cartridge.scad>
// We don't need other modules for this test potentially, but includes are safe.

PCB_Active_Stack_3D();
`;

  console.log('Running focused render test on PCB_Active_Stack_3D...');

  try {
      const wrapper = await createOpenSCAD({ noInitialRun: true });
      const instance = wrapper.getInstance ? wrapper.getInstance() : wrapper;

      // Load files
      instance.FS.writeFile('/test.scad', testScadContent);

      // We need to write ALL dependency files
      instance.FS.writeFile('/' + SCAD_FILE, scadContent);
      if (fs.existsSync(CONSTANTS_FILE)) {
           instance.FS.writeFile('/' + CONSTANTS_FILE, fs.readFileSync(CONSTANTS_FILE));
      }

      // Load other root .scad files (like nanopore_wafer_mold.scad) to the root of the virtual filesystem
      const rootFiles = fs.readdirSync(path.resolve(__dirname, '..'));
      for (const file of rootFiles) {
          if (file.endsWith('.scad') && file !== SCAD_FILE && file !== CONSTANTS_FILE) {
              instance.FS.writeFile('/' + file, fs.readFileSync(path.resolve(__dirname, '..', file)));
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

      const args = [
          '/test.scad',
          '-o', 'test_output.stl'
      ];

      const ret = instance.callMain(args);

      if (ret !== 0) {
          console.error(`  Render failed with exit code ${ret}`);
          process.exit(1);
      } else if (instance.FS.analyzePath('/test_output.stl').exists) {
          console.log(`  Render successful. Output created.`);
      } else {
          console.error(`  Output file was not created.`);
          process.exit(1);
      }

  } catch (e) {
      console.error(`Exception rendering:`, e);
      process.exit(1);
  }

  console.log('\nTest passed successfully.');
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
