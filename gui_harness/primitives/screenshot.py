"""
gui_harness.primitives.screenshot — screenshot capture utilities.

Thin wrapper around scripts/platform_input.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def take(path: str = "/tmp/gui_agent_screen.png") -> str:
    """Take a full-screen screenshot. Returns the file path."""
    from platform_input import screenshot as _screenshot
    return _screenshot(path)


def take_window(app_name: str, out_path: str = None) -> str:
    """Capture a specific app window. Returns the file path."""
    from platform_input import capture_window
    return capture_window(app_name, out_path)
