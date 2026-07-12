
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
    const createOpenSCAD = await importOpenSCAD();
    const wrapper = await createOpenSCAD({ noInitialRun: true });
    const instance = wrapper.getInstance ? wrapper.getInstance() : wrapper;

    let scadContent = fs.readFileSync(SCAD_FILE, 'utf8');
    scadContent = scadContent.replace(/projection\(cut=false\)\s*/g, '');

    instance.FS.writeFile('/' + SCAD_FILE, scadContent);
    if (fs.existsSync(CONSTANTS_FILE)) instance.FS.writeFile('/' + CONSTANTS_FILE, fs.readFileSync(CONSTANTS_FILE));

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

    // Mount 'libraries' to '/libraries' so 'include <libraries/BOSL2/std.scad>' works
    loadDir('libraries', '/libraries');
    loadDir('modules', '/modules');

    const mode = 'Housing_Reader_Lid_STL';
    console.log('Rendering ' + mode + '...');
    const args = ['/' + SCAD_FILE, '-D', `Output_Mode="${mode}"`, '-o', mode + '.stl'];
    const ret = instance.callMain(args);

    if (ret !== 0) { console.error('Failed'); process.exit(1); }
    else { console.log('Success'); }
}
main();
