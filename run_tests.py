import sys
import os
import unittest
import importlib.util

# Ensure repo root is first on sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Load local test modules directly by path to prevent collision with site-packages 'tests'
    t1 = load_module('test_golden_stl_bounds', os.path.join(REPO_ROOT, 'tests', 'test_golden_stl_bounds.py'))
    suite.addTests(loader.loadTestsFromModule(t1))

    t2 = load_module('test_geometry', os.path.join(REPO_ROOT, 'tests', 'test_geometry.py'))
    suite.addTests(loader.loadTestsFromModule(t2))

    t3 = load_module('test_connector_bounds', os.path.join(REPO_ROOT, 'tests', 'test_connector_bounds.py'))
    suite.addTests(loader.loadTestsFromModule(t3))

    t4 = load_module('test_firmware_protocol', os.path.join(REPO_ROOT, 'tests', 'test_firmware_protocol.py'))
    suite.addTests(loader.loadTestsFromModule(t4))

    t5 = load_module('test_exports_e2e', os.path.join(REPO_ROOT, 'tests', 'test_exports_e2e.py'))
    suite.addTests(loader.loadTestsFromModule(t5))

    t6 = load_module('test_legacy_feature_parity', os.path.join(REPO_ROOT, 'tests', 'test_legacy_feature_parity.py'))
    suite.addTests(loader.loadTestsFromModule(t6))

    t7 = load_module('test_daq_client', os.path.join(REPO_ROOT, 'tests', 'test_daq_client.py'))
    suite.addTests(loader.loadTestsFromModule(t7))

    t8 = load_module('test_interposer_kicad', os.path.join(REPO_ROOT, 'tests', 'test_interposer_kicad.py'))
    suite.addTests(loader.loadTestsFromModule(t8))

    t9 = load_module('test_pump_firmware', os.path.join(REPO_ROOT, 'tests', 'test_pump_firmware.py'))
    suite.addTests(loader.loadTestsFromModule(t9))

    t10 = load_module('test_physics_and_simulations', os.path.join(REPO_ROOT, 'tests', 'test_physics_and_simulations.py'))
    suite.addTests(loader.loadTestsFromModule(t10))

    print(f"Loaded {suite.countTestCases()} unit and E2E tests from tests/.")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
