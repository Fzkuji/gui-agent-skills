"""
gui_harness.primitives.input — mouse and keyboard input.

Thin wrapper around scripts/platform_input.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1):
    """Click at screen coordinates."""
    from platform_input import mouse_click as _click
    _click(x, y, button=button, clicks=clicks)


def mouse_double_click(x: int, y: int):
    """Double click at screen coordinates."""
    from platform_input import mouse_double_click as _dbl
    _dbl(x, y)


def mouse_right_click(x: int, y: int):
    """Right click at screen coordinates."""
    from platform_input import mouse_right_click as _rclick
    _rclick(x, y)


def key_press(key_name: str):
    """Press a single key."""
    from platform_input import key_press as _press
    _press(key_name)


def key_combo(*keys: str):
    """Press a key combination (e.g., key_combo('cmd', 'c'))."""
    from platform_input import key_combo as _combo
    _combo(*keys)


def type_text(text: str):
    """Type text via keyboard."""
    from platform_input import type_text as _type
    _type(text)


def paste_text(text: str):
    """Paste text via clipboard."""
    from platform_input import paste_text as _paste
    _paste(text)


def get_frontmost_app() -> str:
    """Get the name of the frontmost application."""
    from platform_input import get_frontmost_app as _get
    return _get()


def activate_app(app_name: str):
    """Bring an app to the foreground."""
    from platform_input import activate_app as _activate
    _activate(app_name)


def get_window_bounds(app_name: str):
    """Get window bounds for an app. Returns (x, y, w, h) or None."""
    from platform_input import get_window_bounds as _bounds
    return _bounds(app_name)
