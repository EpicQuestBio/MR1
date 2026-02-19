const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const LIB_DIR = 'libraries/BOSL2';
const REPO_URL = 'https://github.com/BOSL2/BOSL2.git';
const ZIP_URL = 'https://github.com/BelfrySCAD/BOSL2/archive/refs/heads/master.zip';

function ensureDir(dir) {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
}

async function ensureBOSL2() {
    console.log('Checking BOSL2 installation...');

    // If strictly valid install exists
    if (fs.existsSync(path.join(LIB_DIR, 'std.scad'))) {
        console.log('BOSL2 appears to be installed at ' + LIB_DIR);
        return;
    }

    ensureDir('libraries');

    // 1. Try Git Submodule (Preferred for Git Repos)
    const isGitRepo = fs.existsSync('.git');
    if (isGitRepo) {
        console.log('Git repository detected. Attempting to use git submodule...');
        try {
            // Check if submodule is already registered in .gitmodules
            let gitmodules = '';
            if (fs.existsSync('.gitmodules')) {
                gitmodules = fs.readFileSync('.gitmodules', 'utf8');
            }

            if (gitmodules.includes('libraries/BOSL2')) {
                console.log('Submodule registered. Updating...');
                execSync('git submodule update --init --recursive libraries/BOSL2', { stdio: 'inherit' });
            } else {
                console.log('Adding BOSL2 as submodule...');
                // Force adding is needed because libraries/* is ignored
                execSync(`git submodule add -f ${REPO_URL} libraries/BOSL2`, { stdio: 'inherit' });
            }

            // Double check
            if (fs.existsSync(path.join(LIB_DIR, 'std.scad'))) {
                console.log('BOSL2 submodule setup complete.');
                return;
            }
        } catch (e) {
            console.warn('Git submodule setup failed or was skipped:', e.message);
            console.warn('Falling back to direct download/clone.');
            // Clean up partial failure if directory is empty or broken
            if (fs.existsSync(LIB_DIR) && !fs.existsSync(path.join(LIB_DIR, 'std.scad'))) {
                // If it's a broken submodule, git might complain if we just rm -rf it.
                // But for now, let's try to remove the folder.
                try {
                    fs.rmSync(LIB_DIR, { recursive: true, force: true });
                } catch(err) {
                    console.warn("Could not remove failed submodule dir:", err.message);
                }
            }
        }
    }

    // 2. Try Git Clone (Fallback)
    try {
        console.log('Attempting git clone...');
        execSync(`git clone --depth 1 ${REPO_URL} ${LIB_DIR}`, { stdio: 'inherit' });
        console.log('BOSL2 cloned successfully.');
        return;
    } catch (e) {
        console.warn('Git clone failed:', e.message);
    }

    // 3. Try Zip Download (Last Resort)
    console.log('Attempting zip download...');
    try {
        const zipFile = 'bosl2.zip';
        // Download
        execSync(`curl -L -o ${zipFile} ${ZIP_URL}`, { stdio: 'inherit' });

        // Unzip
        // Check for unzip availability or use simple node script if needed?
        // We assume 'unzip' is available as per previous export script.
        execSync(`unzip -q ${zipFile} -d libraries/`, { stdio: 'inherit' });

        // Rename folder
        // GitHub zip usually extracts to BOSL2-master
        const extractedPath = 'libraries/BOSL2-master';
        if (fs.existsSync(extractedPath)) {
            if (fs.existsSync(LIB_DIR)) {
                 fs.rmSync(LIB_DIR, { recursive: true, force: true });
            }
            fs.renameSync(extractedPath, LIB_DIR);
        } else {
            throw new Error(`Expected extraction to ${extractedPath} failed.`);
        }

        fs.unlinkSync(zipFile);
        console.log('BOSL2 downloaded and extracted.');
    } catch (e) {
        console.error('Failed to download BOSL2:', e.message);
        throw e;
    }
}

module.exports = { ensureBOSL2 };
