"""
gui_harness.primitives.template_match — template matching utilities.

Thin wrapper around scripts/template_match.py.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _tm():
    return importlib.import_module("template_match")


def find_template(app_name: str, template_name: str,
                  screen_path: str = None, threshold: float = 0.8) -> dict:
    """Find a template on screen.

    Returns:
        dict with keys: found (bool), x, y, confidence
    """
    return _tm().find_template(app_name, template_name,
                               screen_path=screen_path, threshold=threshold)


def click_template(app_name: str, template_name: str) -> bool:
    """Find and click a template. Returns True if found and clicked."""
    return _tm().click_template(app_name, template_name)


def list_templates(app_name: str = None) -> list[dict]:
    """List saved templates."""
    return _tm().list_templates(app_name)
