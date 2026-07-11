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
const TARGET_MODE = 'Gasket_Main_DXF';

async function main() {
  console.log('Verifying Gasket Integration...');

  if (!fs.existsSync(OUTPUT_DIR)) {
      fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const createOpenSCAD = await importOpenSCAD();

  // Read SCAD file
  let scadContent = fs.readFileSync(SCAD_FILE, 'utf8');

  // Apply the same patch as render_test.js
  scadContent = scadContent.replace(/projection\(cut=false\)\s*/g, '');

  const wrapper = await createOpenSCAD({ noInitialRun: true });
  const instance = wrapper.getInstance ? wrapper.getInstance() : wrapper;

  instance.FS.writeFile('/' + SCAD_FILE, scadContent);
  if (fs.existsSync(CONSTANTS_FILE)) {
       instance.FS.writeFile('/' + CONSTANTS_FILE, fs.readFileSync(CONSTANTS_FILE));
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

  const outFile = `${TARGET_MODE}.dxf`;
  console.log(`Rendering ${TARGET_MODE}...`);

  const args = [
      '/' + SCAD_FILE,
      '-D', `Output_Mode="${TARGET_MODE}"`,
      '-o', outFile
  ];

  const start = Date.now();
  const ret = instance.callMain(args);
  const end = Date.now();

  if (ret !== 0) {
      console.error(`Render failed with code ${ret}`);
      process.exit(1);
  } else if (instance.FS.analyzePath('/' + outFile).exists) {
      const data = instance.FS.readFile('/' + outFile);
      fs.writeFileSync(path.join(OUTPUT_DIR, outFile), data);
      console.log(`Success! Saved ${outFile} (${data.length} bytes) in ${(end-start)/1000}s`);
  } else {
      console.error(`Output file ${outFile} not found.`);
      process.exit(1);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
