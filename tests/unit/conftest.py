"""
Pytest configuration and fixtures.
Auto-imports all modules for coverage discovery.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Ensure the project root is on sys.path so `from src...` imports work
# regardless of whether pytest was invoked via `python -m pytest` or `pytest`
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# Mock problematic imports before any test modules are loaded
def setup_mocks():
    """Setup mocks for problematic dependencies."""
    sys.modules['ddcDatabases'] = Mock()


def auto_import_modules():
    """Auto-import all source modules for coverage discovery."""
    setup_mocks()

    src_path = Path("src")
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or "migrations" in str(py_file):
            continue

        # Convert file path to module path
        module_parts = py_file.with_suffix("").parts
        module_name = ".".join(module_parts)

        try:
            __import__(module_name)
        except Exception:
            # Silently ignore import failures
            pass


# Run auto-import during pytest collection
auto_import_modules()
