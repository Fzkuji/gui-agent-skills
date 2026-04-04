#!/usr/bin/env python3
"""
gui_harness.action.input — mouse, keyboard, clipboard, and window management.

Moved from scripts/platform_input.py (all non-screenshot functions).
"""

from __future__ import annotations

import platform
import subprocess
import time

SYSTEM = platform.system()  # "Darwin", "Windows", "Linux"


# ═══════════════════════════════════════════
# Mouse operations (pynput)
# ═══════════════════════════════════════════

def mouse_click(x, y, button="left", clicks=1):
    """Click at screen coordinates (logical pixels, integers).
    After clicking, moves cursor to corner so it doesn't pollute screenshots."""
    from pynput.mouse import Button, Controller
    mouse = Controller()
    mouse.position = (int(x), int(y))
    time.sleep(0.05)
    btn = Button.right if button == "right" else Button.left
    mouse.click(btn, int(clicks))
    time.sleep(0.1)
    mouse.position = (1500, 970)


def mouse_move(x, y):
    """Move mouse to screen coordinates."""
    from pynput.mouse import Controller
    mouse = Controller()
    mouse.position = (int(x), int(y))


def mouse_double_click(x, y):
    """Double click at screen coordinates."""
    mouse_click(x, y, clicks=2)


def mouse_right_click(x, y):
    """Right click at screen coordinates."""
    mouse_click(x, y, button="right")


def mouse_drag(start_x, start_y, end_x, end_y, duration=0.5, button="left"):
    """Drag from (start_x, start_y) to (end_x, end_y)."""
    from pynput.mouse import Button, Controller
    mouse = Controller()
    btn = Button.right if button == "right" else Button.left

    mouse.position = (int(start_x), int(start_y))
    time.sleep(0.1)
    mouse.press(btn)
    time.sleep(0.05)

    steps = max(20, int(duration * 60))
    for i in range(1, steps + 1):
        progress = i / steps
        x = start_x + (end_x - start_x) * progress
        y = start_y + (end_y - start_y) * progress
        mouse.position = (int(x), int(y))
        time.sleep(duration / steps)

    mouse.position = (int(end_x), int(end_y))
    time.sleep(0.05)
    mouse.release(btn)
    time.sleep(0.1)
    mouse.position = (1500, 970)


# ═══════════════════════════════════════════
# Keyboard operations (pynput)
# ═══════════════════════════════════════════

def _resolve_key(name):
    """Resolve a key name string to pynput Key or KeyCode."""
    from pynput.keyboard import Key, KeyCode

    key_map = {
        "return": Key.enter, "enter": Key.enter,
        "tab": Key.tab,
        "esc": Key.esc, "escape": Key.esc,
        "space": Key.space,
        "delete": Key.backspace, "backspace": Key.backspace,
        "fwd-delete": Key.delete,
        "up": Key.up, "arrow-up": Key.up,
        "down": Key.down, "arrow-down": Key.down,
        "left": Key.left, "arrow-left": Key.left,
        "right": Key.right, "arrow-right": Key.right,
        "home": Key.home, "end": Key.end,
        "page-up": Key.page_up, "page-down": Key.page_down,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
        "shift": Key.shift, "ctrl": Key.ctrl, "control": Key.ctrl,
        "alt": Key.alt, "option": Key.alt,
        "command": Key.cmd, "cmd": Key.cmd, "super": Key.cmd,
    }

    lower = name.lower()
    if lower in key_map:
        return key_map[lower]

    if len(name) == 1:
        return KeyCode.from_char(name)

    return None


def key_press(key_name):
    """Press and release a single key."""
    from pynput.keyboard import Controller
    kb = Controller()
    key = _resolve_key(key_name)
    if key:
        kb.press(key)
        kb.release(key)
    else:
        raise ValueError(f"Unknown key: {key_name}")


def key_combo(*keys):
    """Press a key combination.

    Examples: key_combo("command", "v"), key_combo("command", "shift", "s")
    """
    from pynput.keyboard import Controller
    kb = Controller()
    resolved = [_resolve_key(k) for k in keys]
    if any(k is None for k in resolved):
        bad = [keys[i] for i, k in enumerate(resolved) if k is None]
        raise ValueError(f"Unknown keys: {bad}")

    for k in resolved:
        kb.press(k)
    time.sleep(0.05)
    for k in reversed(resolved):
        kb.release(k)


def type_text(text):
    """Type text character by character. Works for ASCII.
    For CJK/special chars, use paste_text() instead.
    """
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(text)


def paste_text(text):
    """Paste text via clipboard (works for all languages including CJK)."""
    set_clipboard(text)
    time.sleep(0.1)
    key_combo("command" if SYSTEM == "Darwin" else "ctrl", "v")


# ═══════════════════════════════════════════
# Clipboard operations
# ═══════════════════════════════════════════

def set_clipboard(text):
    """Set clipboard content."""
    if SYSTEM == "Darwin":
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE,
                              env={"LANG": "en_US.UTF-8"})
        p.communicate(text.encode("utf-8"))
    elif SYSTEM == "Windows":
        subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
    else:
        subprocess.run(["xclip", "-selection", "clipboard"],
                       input=text.encode("utf-8"), check=True)


def get_clipboard():
    """Get clipboard content."""
    if SYSTEM == "Darwin":
        r = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return r.stdout
    elif SYSTEM == "Windows":
        r = subprocess.run(["powershell", "-command", "Get-Clipboard"],
                            capture_output=True, text=True)
        return r.stdout.strip()
    else:
        r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                            capture_output=True, text=True)
        return r.stdout


# ═══════════════════════════════════════════
# Window management (platform-specific)
# ═══════════════════════════════════════════

def get_frontmost_app():
    """Get the name of the currently frontmost application."""
    if SYSTEM == "Darwin":
        try:
            r = subprocess.run(["osascript", "-e",
                'tell application "System Events" to return name of first process whose frontmost is true'],
                capture_output=True, text=True, timeout=5)
            return r.stdout.strip()
        except:
            return "unknown"
    else:
        raise NotImplementedError(f"{SYSTEM} get_frontmost_app not yet implemented")


def verify_frontmost(expected_app):
    """Check if the expected app is still frontmost. Returns (is_correct, actual_app)."""
    actual = get_frontmost_app()
    return actual == expected_app, actual


def activate_app(app_name):
    """Bring app window to front."""
    if SYSTEM == "Darwin":
        try:
            subprocess.run(["osascript", "-e",
                f'tell application "System Events" to set frontmost of process "{app_name}" to true'],
                capture_output=True, timeout=5)
            time.sleep(0.3)
        except:
            subprocess.run(["open", "-a", app_name], capture_output=True, timeout=5)
            time.sleep(0.5)
    elif SYSTEM == "Windows":
        raise NotImplementedError("Windows activate_app not yet implemented")
    else:
        raise NotImplementedError("Linux activate_app not yet implemented")


def get_window_bounds(app_name):
    """Get window position and size: (x, y, w, h)."""
    if SYSTEM == "Darwin":
        try:
            r = subprocess.run(["osascript", "-l", "JavaScript", "-e", f'''
var se = Application("System Events");
var ws = se.processes["{app_name}"].windows();
var best = null;
var bestArea = 0;
for (var i = 0; i < ws.length; i++) {{
    try {{
        var p = ws[i].position();
        var s = ws[i].size();
        var area = s[0] * s[1];
        if (area > bestArea) {{
            bestArea = area;
            best = [p[0], p[1], s[0], s[1]];
        }}
    }} catch(e) {{}}
}}
if (best) best.join(","); else "";
'''], capture_output=True, text=True, timeout=5)
            parts = r.stdout.strip().split(",")
            if len(parts) == 4:
                return tuple(int(x) for x in parts)
        except:
            pass
        return None
    else:
        raise NotImplementedError(f"{SYSTEM} get_window_bounds not yet implemented")


# ═══════════════════════════════════════════
# Convenience / high-level
# ═══════════════════════════════════════════

def click_at(x, y):
    """Simple left click (most common operation)."""
    mouse_click(x, y)


def send_keys(combo_string):
    """Parse and execute a key combo string like "command-v", "command-shift-s", "return"."""
    parts = combo_string.lower().split("-")
    if len(parts) == 1:
        key_press(parts[0])
    else:
        key_combo(*parts)
