#!/usr/bin/env python3
"""
Workflow Runner - Execute structured GUI automation workflows.

Usage:
  python workflow_runner.py run <workflow> --param key=value ...
  python workflow_runner.py list
  python workflow_runner.py show <workflow>

Actions:
  focus_app        - Activate app, hide others, ensure frontmost
  click            - Click an element (template → OCR → vision fallback chain)
  click_and_type   - Click + paste text (atomic operation)
  key              - Press a key
  delay            - Wait N seconds
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

WORKFLOW_DIR = Path(__file__).parent.parent / "workflows"
SCRIPT_DIR = Path(__file__).parent
PYTHON = sys.executable

_hidden_apps = []
_focused_app = None


# ─── Helpers ───

def osascript(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

def shell(cmd, timeout=10):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"})
    return r.stdout.strip()

def screenshot(path="/tmp/wf_screen.png"):
    subprocess.run(["/usr/sbin/screencapture", "-x", path], check=True)
    return path

def ocr(img_path=None):
    """OCR → list of {text, x, y, w, h} in logical pixels."""
    if img_path is None:
        img_path = screenshot()
    swift = '''
import Vision; import AppKit
let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url),
      let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let W = Double(cg.width); let H = Double(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hans", "en"]
try! VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
for obs in req.results ?? [] {
    if let c = obs.topCandidates(1).first {
        let b = obs.boundingBox
        print("\\(c.string)|\\(Int(b.origin.x*W/2))|\\(Int((1-b.origin.y-b.height)*H/2))|\\(Int(b.width*W/2))|\\(Int(b.height*H/2))")
    }
}'''
    r = subprocess.run(["swift", "-", img_path], input=swift, capture_output=True, text=True, timeout=15)
    items = []
    for line in r.stdout.strip().split("\n"):
        parts = line.split("|")
        if len(parts) == 5:
            items.append({"text": parts[0], "x": int(parts[1]), "y": int(parts[2]),
                         "w": int(parts[3]), "h": int(parts[4])})
    return items

def click(x, y):
    subprocess.run(["cliclick", f"c:{x},{y}"], check=True)

def paste(text):
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE,
                           env={**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"})
    proc.communicate(text.encode("utf-8"))
    time.sleep(0.1)
    osascript('tell application "System Events" to keystroke "v" using command down')

def resolve(text, params):
    if not isinstance(text, str): return text
    for k, v in params.items():
        text = text.replace(f"{{{{{k}}}}}", str(v))
    return text

def resolve_target(target, params):
    """Resolve a target dict, replacing param placeholders."""
    if isinstance(target, str):
        return {"ocr": resolve(target, params)}
    resolved = {}
    for k, v in target.items():
        resolved[k] = resolve(v, params) if isinstance(v, str) else v
    return resolved


# ─── Locate element ───

def locate(target):
    """
    Find element position. Returns (x, y) or None.
    Target is a dict with priority: template → ocr → position.
    """
    # Try template first
    if "template" in target:
        app = target.get("app", "")
        name = target["template"]
        r = shell(f'{PYTHON} {SCRIPT_DIR / "template_match.py"} find --app {app} --name {name}')
        try:
            data = json.loads(r)
            if data.get("found"):
                return data["x"], data["y"], f"template({name}) conf={data['confidence']}"
        except:
            pass
    
    # Try OCR
    ocr_keyword = target.get("ocr") or target.get("fallback_ocr")
    if ocr_keyword:
        img = screenshot()
        items = ocr(img)
        
        skip_first = target.get("skip_first", False)
        y_min_offset = target.get("y_min_offset", 0)
        found_count = 0
        
        # If we have a previous click target, use its y as baseline
        y_baseline = target.get("_y_baseline", 0)
        
        for item in items:
            if ocr_keyword.lower() in item["text"].lower():
                cy = item["y"] + item["h"] // 2
                
                # Apply y_min_offset: skip items too close to top / previous action
                if y_min_offset and cy < y_baseline + y_min_offset:
                    continue
                
                found_count += 1
                if skip_first and found_count == 1:
                    continue
                
                cx = item["x"] + item["w"] // 2
                return cx, cy, f"ocr('{item['text']}' at {cx},{cy})"
    
    # Try window-calculated position (for known UI layouts)
    if target.get("window_calc"):
        app = target.get("app", _focused_app or "")
        if app:
            pos_str = osascript(f'''
                tell application "System Events" to tell process "{app}"
                    return {{position, size}} of window 1
                end tell
            ''')
            nums = [int(n.strip()) for n in pos_str.split(",")]
            if len(nums) == 4:
                wx, wy, ww, wh = nums
                sidebar_w = target.get("sidebar_width", 250)
                bottom_off = target.get("bottom_offset", 80)
                # Center of chat area, near bottom
                ax = wx + sidebar_w + (ww - sidebar_w) // 2
                ay = wy + wh - bottom_off
                return ax, ay, f"window_calc → ({ax},{ay})"
    
    # Limit OCR matches by x range
    if "x_max" in target:
        pass  # handled in OCR section below
    
    # Try window-relative position
    if target.get("window_relative"):
        app = target.get("app", _focused_app or "")
        if app:
            pos_str = osascript(f'''
                tell application "System Events" to tell process "{app}"
                    return {{position, size}} of window 1
                end tell
            ''')
            # Parse: "x, y, w, h"
            nums = [int(n.strip()) for n in pos_str.split(",")]
            if len(nums) == 4:
                wx, wy, ww, wh = nums
                rx = target.get("rx", 0.5)
                ry = target.get("ry", 0.5)
                ax = int(wx + ww * rx)
                ay = int(wy + wh * ry)
                return ax, ay, f"window_rel({rx},{ry}) → ({ax},{ay})"
    
    # Try fixed position
    if "x" in target and "y" in target:
        return target["x"], target["y"], "fixed"
    
    return None


# ─── Actions ───

def do_focus_app(step, params):
    global _focused_app
    app = resolve(step["app"], params)
    
    # Hide other apps
    visible = osascript('''
        tell application "System Events"
            set output to ""
            repeat with p in (every process whose visible is true)
                set output to output & name of p & "|"
            end repeat
            return output
        end tell
    ''').split("|")
    
    skip = {"Finder", "SystemUIServer", "Window Manager", "Control Center", 
            "Spotlight", "NotificationCenter", app, ""}
    for a in visible:
        a = a.strip()
        if a and a not in skip:
            try:
                osascript(f'tell application "System Events" to tell process "{a}" to set visible to false')
                _hidden_apps.append(a)
            except: pass
    
    osascript(f'tell application "{app}" to activate')
    time.sleep(0.3)
    osascript(f'tell application "System Events" to tell process "{app}" to set frontmost to true')
    time.sleep(0.3)
    _focused_app = app
    return f"focused {app}, hid {len(_hidden_apps)} apps"


def do_click(step, params):
    target = resolve_target(step["target"], params)
    result = locate(target)
    if not result:
        return None  # Signal failure
    x, y, method = result
    click(x, y)
    time.sleep(step.get("delay_after", 0.3))
    return f"clicked ({x},{y}) via {method}"


def do_click_and_type(step, params):
    target = resolve_target(step["target"], params)
    text = resolve(step["text"], params)
    
    # Locate and click
    result = locate(target)
    if not result:
        return None
    x, y, method = result
    click(x, y)
    time.sleep(0.3)
    
    # Clear existing text if needed
    if step.get("clear_first"):
        osascript('tell application "System Events" to keystroke "a" using command down')
        time.sleep(0.1)
    
    # Paste text
    paste(text)
    time.sleep(step.get("delay_after", 0.3))
    
    # Send (press Enter) if flagged
    if step.get("send"):
        osascript('tell application "System Events" to keystroke return')
        time.sleep(0.3)
    
    send_str = " + sent" if step.get("send") else ""
    return f"clicked ({x},{y}) via {method}, typed '{text[:30]}{'...' if len(text)>30 else ''}'{send_str}"


def do_key(step, params):
    key = resolve(step["key"], params)
    osascript(f'tell application "System Events" to keystroke {key}')
    time.sleep(step.get("delay_after", 0.3))
    return f"pressed {key}"


def do_delay(step, params):
    secs = step.get("seconds", 1)
    time.sleep(secs)
    return f"waited {secs}s"


ACTIONS = {
    "focus_app": do_focus_app,
    "click": do_click,
    "click_and_type": do_click_and_type,
    "key": do_key,
    "delay": do_delay,
}


# ─── Runner ───

def run_workflow(workflow, params):
    print(f"▶ {workflow['name']}")
    print(f"  params: {json.dumps(params, ensure_ascii=False)}")
    print(f"  steps: {len(workflow['steps'])}")
    print()
    
    start = time.time()
    
    for step in workflow["steps"]:
        sid = step.get("id", "?")
        action = step["action"]
        handler = ACTIONS.get(action)
        
        if not handler:
            print(f"  [{sid}] ❌ unknown action: {action}")
            break
        
        result = handler(step, params)
        if result is None:
            print(f"  [{sid}] ❌ {action} failed — element not found")
            break
        
        print(f"  [{sid}] ✓ {result}")
    else:
        elapsed = time.time() - start
        print(f"\n✅ Done in {elapsed:.1f}s")
        # Restore hidden apps
        for app in _hidden_apps:
            try: osascript(f'tell application "System Events" to tell process "{app}" to set visible to true')
            except: pass
        return True
    
    # Failed — still restore
    for app in _hidden_apps:
        try: osascript(f'tell application "System Events" to tell process "{app}" to set visible to true')
        except: pass
    print(f"\n❌ Failed")
    return False


# ─── CLI ───

def main():
    parser = argparse.ArgumentParser(description="GUI Workflow Runner")
    sub = parser.add_subparsers(dest="cmd", required=True)
    
    p_run = sub.add_parser("run")
    p_run.add_argument("workflow")
    p_run.add_argument("--param", action="append", default=[])
    
    p_list = sub.add_parser("list")
    p_show = sub.add_parser("show")
    p_show.add_argument("workflow")
    
    args = parser.parse_args()
    
    if args.cmd == "list":
        for f in sorted(WORKFLOW_DIR.glob("*.json")):
            wf = json.load(open(f))
            print(f"  {f.stem}: {wf.get('description', '')}")
            for k, v in wf.get("params", {}).items():
                print(f"    {k}: {v}")
        return
    
    if args.cmd == "show":
        p = WORKFLOW_DIR / f"{args.workflow}.json"
        if not p.exists(): p = Path(args.workflow)
        print(json.dumps(json.load(open(p)), indent=2, ensure_ascii=False))
        return
    
    # Run
    p = WORKFLOW_DIR / f"{args.workflow}.json"
    if not p.exists(): p = WORKFLOW_DIR / args.workflow
    if not p.exists(): p = Path(args.workflow)
    
    wf = json.load(open(p))
    params = {}
    for kv in args.param:
        k, v = kv.split("=", 1)
        params[k] = v
    
    missing = [k for k in wf.get("params", {}) if k not in params]
    if missing:
        print(f"Missing params: {missing}")
        sys.exit(1)
    
    ok = run_workflow(wf, params)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
