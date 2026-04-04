"""
gui_harness.primitives.vm_adapter — VM-based backend for GUI primitives.

Monkey-patches the primitives to work with a remote VM via HTTP API
instead of local macOS operations.

Usage:
    from gui_harness.primitives.vm_adapter import patch_for_vm
    patch_for_vm("http://172.16.105.128:5000")
"""

from __future__ import annotations

import base64
import os
import requests
import time

_VM_URL: str | None = None


def patch_for_vm(vm_url: str):
    """Monkey-patch all primitives to use the VM HTTP API."""
    global _VM_URL
    _VM_URL = vm_url.rstrip("/")

    import gui_harness.primitives.screenshot as _ss
    import gui_harness.primitives.input as _inp

    # Patch screenshot
    _ss.take = vm_screenshot
    _ss.take_window = lambda app, out=None: vm_screenshot(out or "/tmp/gui_agent_screen.png")

    # Patch input functions
    _inp.mouse_click = vm_mouse_click
    _inp.mouse_double_click = vm_mouse_double_click
    _inp.mouse_right_click = vm_mouse_right_click
    _inp.key_press = vm_key_press
    _inp.key_combo = vm_key_combo
    _inp.type_text = vm_type_text
    _inp.paste_text = vm_paste_text
    _inp.get_frontmost_app = lambda: "VM Desktop"


def _vm_exec(command: str, timeout: int = 30) -> dict:
    """Execute a command on the VM."""
    r = requests.post(f"{_VM_URL}/execute", json={"command": command}, timeout=timeout)
    return r.json()


def _vm_exec_script(script: str, timeout: int = 30) -> dict:
    """Write a Python script to the VM and execute it.
    
    More reliable than python3 -c for complex code — avoids
    shell quoting issues with special characters.
    """
    b64 = base64.b64encode(script.encode()).decode()
    cmd = (
        f"python3 -c \""
        f"import base64; "
        f"s=base64.b64decode('{b64}').decode(); "
        f"open('/tmp/_vm_script.py','w').write(s); "
        f"exec(s)"
        f"\""
    )
    return _vm_exec(cmd, timeout=timeout)


def vm_screenshot(path: str = "/tmp/gui_agent_screen.png") -> str:
    """Take a screenshot from the VM and save locally."""
    r = requests.get(f"{_VM_URL}/screenshot", timeout=15)
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def vm_mouse_click(x: int, y: int, button: str = "left", clicks: int = 1):
    btn = "left" if button == "left" else "right"
    cmd = f"python3 -c \"import pyautogui; pyautogui.click({x}, {y}, button='{btn}', clicks={clicks})\""
    _vm_exec(cmd)
    time.sleep(0.3)


def vm_mouse_double_click(x: int, y: int):
    vm_mouse_click(x, y, clicks=2)


def vm_mouse_right_click(x: int, y: int):
    vm_mouse_click(x, y, button="right")


def vm_key_press(key_name: str):
    cmd = f"python3 -c \"import pyautogui; pyautogui.press('{key_name}')\""
    _vm_exec(cmd)
    time.sleep(0.2)


def vm_key_combo(*keys: str):
    key_list = "', '".join(keys)
    cmd = f"python3 -c \"import pyautogui; pyautogui.hotkey('{key_list}')\""
    _vm_exec(cmd)
    time.sleep(0.3)


def vm_type_text(text: str):
    """Type text on the VM using xdotool (preferred) or pyautogui fallback.
    
    xdotool handles all characters natively.
    pyautogui fallback types character by character with shift mapping.
    """
    b64 = base64.b64encode(text.encode()).decode()
    script = f"""
import base64, subprocess, sys

text = base64.b64decode('{b64}').decode()

# Try xdotool first (handles all characters)
try:
    r = subprocess.run(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '25', text],
        capture_output=True, timeout=30
    )
    if r.returncode == 0:
        sys.exit(0)
except FileNotFoundError:
    pass

# Fallback: pyautogui character by character
import pyautogui, time

SHIFT_MAP = {{
    '(': '9', ')': '0', ':': ';', '!': '1', '@': '2', '#': '3',
    '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '_': '-',
    '+': '=', '{{': '[', '}}': ']', '|': '\\\\', '~': '`', '<': ',',
    '>': '.', '?': '/', '"': "'",
}}

for ch in text:
    if ch in SHIFT_MAP:
        pyautogui.hotkey('shift', SHIFT_MAP[ch])
    elif ch == ' ':
        pyautogui.press('space')
    elif ch == '\\n':
        pyautogui.press('return')
    elif ch == '\\t':
        pyautogui.press('tab')
    elif ch.isupper():
        pyautogui.hotkey('shift', ch.lower())
    else:
        try:
            pyautogui.press(ch)
        except Exception:
            pass  # skip unsupported chars
    time.sleep(0.02)
"""
    _vm_exec_script(script)
    time.sleep(0.3)


def vm_paste_text(text: str):
    """Paste text via clipboard on the VM.
    
    Tries xclip → xsel → xdotool type → pyautogui fallback.
    """
    b64 = base64.b64encode(text.encode()).decode()
    script = f"""
import base64, subprocess, sys, time

text = base64.b64decode('{b64}').decode()

# Write to temp file for clipboard tools
with open('/tmp/_vm_clip.txt', 'w') as f:
    f.write(text)

# Try xclip
try:
    r = subprocess.run(
        'xclip -selection clipboard < /tmp/_vm_clip.txt',
        shell=True, capture_output=True, timeout=5
    )
    if r.returncode == 0:
        import pyautogui
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        sys.exit(0)
except Exception:
    pass

# Try xsel
try:
    r = subprocess.run(
        'xsel --clipboard --input < /tmp/_vm_clip.txt',
        shell=True, capture_output=True, timeout=5
    )
    if r.returncode == 0:
        import pyautogui
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        sys.exit(0)
except Exception:
    pass

# Try xdotool type (handles unicode)
try:
    r = subprocess.run(
        ['xdotool', 'type', '--clearmodifiers', '--delay', '25', text],
        capture_output=True, timeout=30
    )
    if r.returncode == 0:
        sys.exit(0)
except FileNotFoundError:
    pass

# Last resort: pyautogui character by character
import pyautogui

SHIFT_MAP = {{
    '(': '9', ')': '0', ':': ';', '!': '1', '@': '2', '#': '3',
    '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '_': '-',
    '+': '=', '{{': '[', '}}': ']', '|': '\\\\', '~': '`', '<': ',',
    '>': '.', '?': '/', '"': "'",
}}

for ch in text:
    if ch in SHIFT_MAP:
        pyautogui.hotkey('shift', SHIFT_MAP[ch])
    elif ch == ' ':
        pyautogui.press('space')
    elif ch == '\\n':
        pyautogui.press('return')
    elif ch == '\\t':
        pyautogui.press('tab')
    elif ch.isupper():
        pyautogui.hotkey('shift', ch.lower())
    else:
        try:
            pyautogui.press(ch)
        except Exception:
            pass
    time.sleep(0.02)
"""
    _vm_exec_script(script)
    time.sleep(0.3)
