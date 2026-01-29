const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = 'output';
const MANIFEST_FILE = 'tests/golden_manifest.json';

function main() {
    console.log('Verifying outputs against Golden Manifest...');

    if (!fs.existsSync(MANIFEST_FILE)) {
        console.error('Golden Manifest not found. Run generate_golden.js first.');
        process.exit(1);
    }

    const manifest = JSON.parse(fs.readFileSync(MANIFEST_FILE, 'utf8'));
    let errors = 0;

    for (const [filename, expected] of Object.entries(manifest)) {
        const filePath = path.join(OUTPUT_DIR, filename);

        if (!fs.existsSync(filePath)) {
            console.error(`[FAIL] ${filename}: File missing.`);
            errors++;
            continue;
        }

        const stats = fs.statSync(filePath);
        const actualSize = stats.size;

        // Tolerance: +/- 1% or 10 bytes (whichever is larger) for non-deterministic headers
        const tolerance = Math.max(10, expected.size * 0.01);
        const diff = Math.abs(actualSize - expected.size);

        if (diff > tolerance) {
            console.error(`[FAIL] ${filename}: Size mismatch. Expected ${expected.size}, got ${actualSize} (Diff: ${diff}).`);
            errors++;
        } else {
            console.log(`[PASS] ${filename}`);
        }
    }

    if (errors > 0) {
        console.error(`\nVerification failed with ${errors} errors.`);
        process.exit(1);
    } else {
        console.log('\nAll outputs matched Golden Master.');
    }
}

main();
