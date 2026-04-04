"""macOS local backend — uses pynput for input, screencapture for screenshots."""

import subprocess
import sys
import os


def click(x, y):
    from gui_harness.action.input import click_at
    click_at(int(x), int(y))
    print(f"clicked ({x}, {y})")


def double_click(x, y):
    from gui_harness.action.input import click_at
    click_at(int(x), int(y))
    import time; time.sleep(0.05)
    click_at(int(x), int(y))
    print(f"double_clicked ({x}, {y})")


def right_click(x, y):
    from gui_harness.action.input import mouse_right_click
    mouse_right_click(int(x), int(y))
    print(f"right_clicked ({x}, {y})")


def type_text(text):
    from gui_harness.action.input import paste_text
    paste_text(text)
    print(f"typed: {text[:50]}{'...' if len(text) > 50 else ''}")


def key(keyname):
    from gui_harness.action.input import key_press
    key_press(keyname)
    print(f"key: {keyname}")


def shortcut(keys):
    from gui_harness.action.input import key_combo
    key_list = keys.replace("+", " ").split()
    # Map common names: ctrl→control, cmd→command
    mapping = {"ctrl": "control", "cmd": "command", "alt": "option"}
    key_list = [mapping.get(k.lower(), k.lower()) for k in key_list]
    key_combo(key_list)
    print(f"shortcut: {keys}")


def screenshot(path="/tmp/gui_screenshot.png"):
    subprocess.run(["/usr/sbin/screencapture", "-x", path], capture_output=True)
    if os.path.exists(path):
        print(f"screenshot: {path}")
    else:
        print(f"screenshot failed: {path}")


def focus(title):
    subprocess.run(["osascript", "-e", f'tell application "{title}" to activate'], capture_output=True)
    print(f"focused: {title}")


def close(title):
    subprocess.run(["osascript", "-e",
        f'tell application "{title}" to close (every window whose name contains "{title}")'],
        capture_output=True)
    print(f"closed: {title}")


def list_windows():
    result = subprocess.run(["osascript", "-e",
        'tell application "System Events" to get name of every window of every process whose visible is true'],
        capture_output=True, text=True)
    print(result.stdout.strip())
