#!/bin/bash
# gui_actions.sh — Execute a batch of GUI actions from a JSON action plan
# Usage: echo '<json>' | ./gui_actions.sh
# Or:    ./gui_actions.sh action_plan.json
#
# Action types:
#   activate <app>        — Bring app to foreground
#   paste <text>          — Copy text to clipboard and Cmd+V
#   key <key>             — Press a key (return, tab, escape, space, etc.)
#   hotkey <mod+key>      — Press hotkey (cmd+v, cmd+a, etc.)
#   click <x> <y>         — Click at screen coordinates
#   type <text>           — Type text via AppleScript keystroke (ASCII only)
#   delay <seconds>       — Wait
#   ocr                   — Take screenshot + OCR, output text
#
# JSON format:
# { "actions": [
#     {"type": "activate", "app": "WeChat"},
#     {"type": "delay", "seconds": 0.5},
#     {"type": "paste", "text": "Hello!"},
#     {"type": "key", "key": "return"},
#     {"type": "ocr"}
# ]}

set -euo pipefail

# Fix locale for CJK clipboard support (pbcopy/pbpaste)
export LANG="${LANG:-en_US.UTF-8}"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Read JSON from stdin or file
if [ -n "${1:-}" ] && [ -f "$1" ]; then
    JSON=$(cat "$1")
else
    JSON=$(cat)
fi

# Parse and execute actions using python3 + osascript
export GUI_JSON="$JSON"
export GUI_SCRIPT_DIR="$SCRIPT_DIR"
python3 << 'PYEOF'
import json, os, subprocess, time

data = json.loads(os.environ["GUI_JSON"])
script_dir = os.environ["GUI_SCRIPT_DIR"]
actions = data.get("actions", [])

def run_osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        print(f"  osascript error: {r.stderr.strip()}", flush=True)
    return r

def run_ocr():
    r = subprocess.run(
        ["swift", os.path.join(script_dir, "ocr_screen.swift")],
        capture_output=True, text=True, timeout=30
    )
    return r.stdout

for i, action in enumerate(actions):
    atype = action["type"]
    print(f"[{i+1}/{len(actions)}] {atype}", end="", flush=True)

    if atype == "activate":
        app = action["app"]
        print(f" → {app}", flush=True)
        run_osa(f'tell application "{app}" to activate')
        time.sleep(0.5)

    elif atype == "paste":
        text = action["text"]
        preview = text[:50] + ("..." if len(text) > 50 else "")
        print(f' → "{preview}"', flush=True)
        # Use pbcopy for reliable Unicode support
        p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"))
        time.sleep(0.1)
        run_osa('tell application "System Events" to keystroke "v" using command down')
        time.sleep(0.3)

    elif atype == "key":
        key = action["key"]
        print(f" → {key}", flush=True)
        run_osa(f'tell application "System Events" to key code {_key_code(key)}' if False else
                f'tell application "System Events" to keystroke return' if key == "return" else
                f'tell application "System Events" to keystroke tab' if key == "tab" else
                f'tell application "System Events" to key code 53' if key == "escape" else
                f'tell application "System Events" to keystroke " "' if key == "space" else
                f'tell application "System Events" to keystroke "{key}"')
        time.sleep(0.2)

    elif atype == "hotkey":
        combo = action["combo"]  # e.g. "cmd+a", "cmd+shift+v"
        parts = combo.lower().split("+")
        key_char = parts[-1]
        mods = parts[:-1]
        print(f" → {combo}", flush=True)
        mod_str = " using {"
        mod_map = {"cmd": "command down", "shift": "shift down", "alt": "option down", "ctrl": "control down"}
        mod_str += ", ".join(mod_map.get(m, m) for m in mods)
        mod_str += "}"
        run_osa(f'tell application "System Events" to keystroke "{key_char}"{mod_str}')
        time.sleep(0.3)

    elif atype == "click":
        x, y = action["x"], action["y"]
        print(f" → ({x}, {y})", flush=True)
        run_osa(f'''
            do shell script "cliclick c:{x},{y}"
        ''')
        time.sleep(0.3)

    elif atype == "type":
        text = action["text"]
        print(f' → "{text}"', flush=True)
        run_osa(f'tell application "System Events" to keystroke "{text}"')
        time.sleep(0.2)

    elif atype == "delay":
        secs = action.get("seconds", 1)
        print(f" → {secs}s", flush=True)
        time.sleep(secs)

    elif atype == "ocr":
        print(" → capturing...", flush=True)
        text = run_ocr()
        print("--- OCR START ---")
        print(text)
        print("--- OCR END ---")

    else:
        print(f" → unknown action type: {atype}", flush=True)

print("\n✅ All actions complete.", flush=True)
PYEOF
