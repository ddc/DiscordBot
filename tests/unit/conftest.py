"""
Pytest configuration and fixtures.
Auto-imports all modules for coverage discovery.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import Mock

logger = logging.getLogger(__name__)

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def setup_mocks():
    """Setup mocks for problematic dependencies."""
    sys.modules["ddcDatabases"] = Mock()


def auto_import_modules():
    """Auto-import all source modules for coverage discovery."""
    setup_mocks()

    src_path = Path("src")
    for py_file in src_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or "migrations" in str(py_file):
            continue

        module_parts = py_file.with_suffix("").parts
        module_name = ".".join(module_parts)

        try:
            __import__(module_name)
        except Exception:
            logger.debug("Failed to import %s for coverage discovery", module_name)


auto_import_modules()
