const { ensureBOSL2 } = require('./lib_setup');

(async () => {
    try {
        await ensureBOSL2();
        console.log('Libraries installed successfully.');
    } catch (error) {
        console.error('Failed to install libraries:', error);
        process.exit(1);
    }
})();
