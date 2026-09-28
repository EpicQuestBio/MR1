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

    print(f"Loaded {suite.countTestCases()} unit tests from tests/.")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
