const { execSync } = require('child_process');

try {
  console.log("Rendering Housing_Reader_Case_STL...");
  execSync('node scripts/export_all.js Housing_Reader_Case_STL', {stdio: 'inherit'});
  console.log("Done");
} catch(e) {
  console.error("Error", e);
}
