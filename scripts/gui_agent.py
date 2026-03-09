#!/usr/bin/env python3
"""
GUI Agent — Adaptive desktop automation.

Architecture:
  App profiles (apps/*.json)  →  define layout, navigation, input, send, verify
  Generic tasks               →  send_message, read_messages (work for any app)
  Atomic operations           →  click, type, OCR, template match, AppleScript

Usage:
  gui_agent.py task send_message --app WeChat --param contact="宋文涛" --param message="在吗"
  gui_agent.py task send_message --app Discord --param contact="general" --param message="hello"
  gui_agent.py observe --app WeChat
  gui_agent.py exec '{"action": "click_ocr", "text": "hello"}'
  gui_agent.py find "some text" --region '{"x_max": 400}'
  gui_agent.py apps
  gui_agent.py tasks
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
APPS_DIR = SCRIPT_DIR.parent / "apps"
PYTHON = sys.executable

_hidden_apps = []
_focused_app = None


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def osascript(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

def shell(cmd, timeout=15):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"})
    return r.stdout.strip()


# ═══════════════════════════════════════════
# Observation (Level 1→4: fast → slow)
# ═══════════════════════════════════════════

# Level 1: AppleScript (~0.1s)
def check_frontmost():
    return osascript('tell application "System Events" to name of first process whose frontmost is true')

def check_window_title(app):
    try:
        return osascript(f'tell application "System Events" to tell process "{app}" to return name of window 1')
    except:
        return None

def check_window_bounds(app):
    try:
        s = osascript(f'tell application "System Events" to tell process "{app}" to return {{position, size}} of window 1')
        nums = [int(n.strip()) for n in s.split(",") if n.strip()]
        return tuple(nums) if len(nums) == 4 else None
    except:
        return None

# Level 2: Template match (~1.3s)
def check_template(app, name):
    r = shell(f'{PYTHON} {SCRIPT_DIR / "template_match.py"} find --app {app} --name {name}')
    try:
        return json.loads(r)
    except:
        return None

# Level 3: OCR (~1.6s)
def screenshot(path="/tmp/gui_agent_screen.png"):
    subprocess.run(["screencapture", "-x", path], check=True, timeout=5)
    return path

def ocr_full(img_path=None):
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

def ocr_find(keyword, region=None, img_path=None):
    items = ocr_full(img_path)
    matches = []
    for item in items:
        if keyword and keyword.lower() not in item["text"].lower():
            continue
        cx, cy = item["x"] + item["w"] // 2, item["y"] + item["h"] // 2
        if region:
            if region.get("x_min") and cx < region["x_min"]: continue
            if region.get("x_max") and cx > region["x_max"]: continue
            if region.get("y_min") and cy < region["y_min"]: continue
            if region.get("y_max") and cy > region["y_max"]: continue
        matches.append({**item, "cx": cx, "cy": cy})
    return matches

# Level 4: Screenshot for vision
def take_screenshot_jpg(path="/tmp/gui_agent_vision.jpg"):
    raw = screenshot("/tmp/gui_agent_raw.png")
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "60",
                    raw, "--out", path], capture_output=True, timeout=10)
    return path


# ═══════════════════════════════════════════
# Structured observation
# ═══════════════════════════════════════════

def observe(app=None):
    state = {"frontmost": check_frontmost()}
    if app:
        state["target_focused"] = (state["frontmost"] == app)
        bounds = check_window_bounds(app)
        if bounds:
            state["window"] = {"x": bounds[0], "y": bounds[1], "w": bounds[2], "h": bounds[3]}
        state["title"] = check_window_title(app)
    
    img = screenshot()
    items = ocr_full(img)
    
    if "window" in state:
        w = state["window"]
        profile = load_app_profile(app) if app else None
        sidebar_w = profile["layout"].get("sidebar_width", 250) if profile else 250
        
        sidebar, main = [], []
        for item in items:
            cx = item["x"] + item["w"] // 2
            cy = item["y"] + item["h"] // 2
            if w["x"] <= cx <= w["x"] + w["w"] and w["y"] <= cy <= w["y"] + w["h"]:
                if cx < w["x"] + sidebar_w:
                    sidebar.append(item["text"])
                else:
                    main.append(item["text"])
        state["sidebar"] = sidebar[:15]
        state["main"] = main[:20]
    else:
        state["texts"] = [i["text"] for i in items[:30]]
    
    return state

def format_state(state):
    lines = [f"App: {state.get('frontmost', '?')}"]
    if "window" in state:
        w = state["window"]
        lines.append(f"Window: ({w['x']},{w['y']}) {w['w']}x{w['h']}")
    if state.get("title"):
        lines.append(f"Title: {state['title']}")
    if "sidebar" in state:
        lines.append(f"Sidebar: {' | '.join(state['sidebar'][:10])}")
    if "main" in state:
        lines.append(f"Main: {' | '.join(state['main'][:15])}")
    if "texts" in state:
        lines.append(f"Visible: {' | '.join(state['texts'][:20])}")
    return "\n".join(lines)


# ═══════════════════════════════════════════
# Actions
# ═══════════════════════════════════════════

def hide_other_apps(keep):
    global _hidden_apps
    _hidden_apps = []
    try:
        visible = osascript('''
            tell application "System Events"
                set output to ""
                repeat with p in (every process whose visible is true)
                    set output to output & name of p & linefeed
                end repeat
                return output
            end tell
        ''').strip().split("\n")
    except:
        return []
    
    skip = {"Finder", "SystemUIServer", "Window Manager", "Control Center",
            "Spotlight", "NotificationCenter", keep, ""}
    for a in visible:
        a = a.strip()
        if a and a not in skip:
            try:
                osascript(f'tell application "System Events" to tell process "{a}" to set visible to false')
                _hidden_apps.append(a)
            except: pass
    return _hidden_apps

def restore_apps():
    for a in _hidden_apps:
        try: osascript(f'tell application "System Events" to tell process "{a}" to set visible to true')
        except: pass

def activate(app):
    global _focused_app
    osascript(f'tell application "{app}" to activate')
    time.sleep(0.3)
    osascript(f'tell application "System Events" to tell process "{app}" to set frontmost to true')
    time.sleep(0.2)
    _focused_app = app

def click_pos(x, y):
    subprocess.run(["cliclick", f"c:{x},{y}"], check=True)

def paste_text(text):
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE,
                           env={**os.environ, "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"})
    proc.communicate(text.encode("utf-8"))
    time.sleep(0.1)
    osascript('tell application "System Events" to keystroke "v" using command down')

def press_key(key):
    key_map = {"return": "return", "escape": "(ASCII character 27)",
               "tab": "tab", "delete": "(ASCII character 127)", "space": "space"}
    k = key_map.get(key.lower(), f'"{key}"')
    osascript(f'tell application "System Events" to keystroke {k}')

def press_shortcut(key, modifiers):
    mod_str = " & ".join(f"{m} down" for m in modifiers)
    osascript(f'tell application "System Events" to keystroke "{key}" using {{{mod_str}}}')


# ═══════════════════════════════════════════
# Action executor (for LLM single-step calls)
# ═══════════════════════════════════════════

def execute_action(action_dict):
    act = action_dict.get("action")
    try:
        if act == "focus_app":
            activate(action_dict["app"])
            return True, f"Activated {action_dict['app']}"
        elif act == "hide_others":
            hidden = hide_other_apps(action_dict["keep"])
            return True, f"Hid {len(hidden)} apps"
        elif act == "click_ocr":
            matches = ocr_find(action_dict["text"], action_dict.get("region"))
            if not matches: return False, f"OCR: '{action_dict['text']}' not found"
            m = matches[0]
            click_pos(m["cx"], m["cy"])
            return True, f"Clicked '{m['text']}' at ({m['cx']},{m['cy']})"
        elif act == "click_template":
            r = check_template(action_dict["app"], action_dict["name"])
            if not r or not r.get("found"): return False, f"Template '{action_dict['name']}' not found"
            click_pos(r["x"], r["y"])
            return True, f"Clicked template ({r['x']},{r['y']}) conf={r['confidence']}"
        elif act == "click_pos":
            click_pos(action_dict["x"], action_dict["y"])
            return True, f"Clicked ({action_dict['x']},{action_dict['y']})"
        elif act == "click_window":
            bounds = check_window_bounds(action_dict["app"])
            if not bounds: return False, f"No window bounds for {action_dict['app']}"
            wx, wy, ww, wh = bounds
            sw = action_dict.get("sidebar_width", 250)
            bo = action_dict.get("bottom_offset", 80)
            x, y = wx + sw + (ww - sw) // 2, wy + wh - bo
            click_pos(x, y)
            return True, f"Clicked window calc ({x},{y})"
        elif act == "type":
            paste_text(action_dict["text"])
            return True, f"Typed '{action_dict['text'][:30]}'"
        elif act == "key":
            press_key(action_dict["key"])
            return True, f"Pressed {action_dict['key']}"
        elif act == "shortcut":
            press_shortcut(action_dict["key"], action_dict["modifiers"])
            return True, f"Shortcut {'+'.join(action_dict['modifiers'])}+{action_dict['key']}"
        elif act == "delay":
            time.sleep(action_dict.get("seconds", 0.5))
            return True, f"Waited {action_dict.get('seconds', 0.5)}s"
        else:
            return False, f"Unknown action: {act}"
    except Exception as e:
        return False, f"Error: {e}"


# ═══════════════════════════════════════════
# App profiles
# ═══════════════════════════════════════════

_profiles_cache = {}

def load_app_profile(app_name):
    if app_name in _profiles_cache:
        return _profiles_cache[app_name]
    
    # Try exact match then case-insensitive
    for f in APPS_DIR.glob("*.json"):
        data = json.load(open(f))
        if data.get("app", "").lower() == app_name.lower():
            _profiles_cache[app_name] = data
            return data
    return None

def get_profile_or_default(app_name):
    """Load profile or return sensible defaults."""
    profile = load_app_profile(app_name)
    if profile:
        return profile
    return {
        "app": app_name,
        "process_name": app_name,
        "layout": {"sidebar_width": 250, "input_bottom_offset": 70, "sidebar_x_max": 400},
        "navigation": {"method": "sidebar_click", "fallback": "search"},
        "input": {"method": "window_calc"},
        "send": {"key": "return"},
        "verify": {"method": "ocr", "region": "main_area"},
        "quirks": []
    }


# ═══════════════════════════════════════════
# Generic tasks (driven by app profiles)
# ═══════════════════════════════════════════

def _navigate_to_contact(profile, contact, log):
    """Navigate to a contact/channel. Returns True if chat opened."""
    layout = profile["layout"]
    nav = profile.get("navigation", {})
    sidebar_x_max = layout.get("sidebar_x_max", 400)
    
    # Check if already in the right chat
    state = observe(profile["app"])
    main_text = " ".join(state.get("main", []))
    if contact.lower() in main_text.lower():
        log("nav", f"chat with '{contact}' already open")
        return True
    
    # Try sidebar click
    matches = ocr_find(contact, {"x_max": sidebar_x_max})
    if matches:
        m = matches[0]
        log("nav", f"clicking sidebar '{m['text']}' at ({m['cx']},{m['cy']})")
        click_pos(m["cx"], m["cy"])
        time.sleep(0.5)
        return True
    
    # Fallback: search
    if nav.get("fallback") == "search":
        log("nav", f"'{contact}' not in sidebar, searching...")
        
        # Open search
        if nav.get("search_shortcut"):
            sc = nav["search_shortcut"]
            press_shortcut(sc["key"], sc["modifiers"])
            time.sleep(0.3)
        elif nav.get("search_bar", {}).get("template"):
            tpl = check_template(profile["app"], nav["search_bar"]["template"])
            if tpl and tpl.get("found"):
                click_pos(tpl["x"], tpl["y"])
            else:
                search_m = ocr_find("Search", {"x_max": sidebar_x_max, "y_max": 220})
                if search_m:
                    click_pos(search_m[0]["cx"], search_m[0]["cy"])
                else:
                    return False
            time.sleep(0.3)
        
        paste_text(contact)
        time.sleep(1.0)
        
        # Click result (skip search box text and suggestions)
        filt = nav.get("search_result_filter", {})
        skip_y = filt.get("skip_y_max", 220)
        skip_prefix = filt.get("skip_prefix", [])
        
        results = ocr_find(contact)
        for r in results:
            if r["cy"] < skip_y:
                continue
            if any(r["text"].startswith(p) for p in skip_prefix):
                continue
            log("nav", f"clicking result '{r['text']}' at ({r['cx']},{r['cy']})")
            click_pos(r["cx"], r["cy"])
            time.sleep(0.5)
            return True
        
        log("nav", f"'{contact}' not found in search results")
        return False
    
    return False


def _find_input(profile):
    """Find and click the input field. Returns True if clicked."""
    inp = profile.get("input", {})
    method = inp.get("method", "window_calc")
    layout = profile["layout"]
    app = profile["app"]
    
    if method == "ocr" and inp.get("ocr_keyword"):
        matches = ocr_find(inp["ocr_keyword"])
        if matches:
            click_pos(matches[0]["cx"], matches[0]["cy"])
            return True
        if inp.get("fallback") != "window_calc":
            return False
    
    # window_calc
    bounds = check_window_bounds(app)
    if not bounds:
        return False
    wx, wy, ww, wh = bounds
    sw = layout.get("sidebar_width", 250)
    bo = layout.get("input_bottom_offset", 70)
    x = wx + sw + (ww - sw) // 2
    y = wy + wh - bo
    click_pos(x, y)
    return True


def task_send_message(app_name, params, log):
    """Generic send message — works for any app with a profile."""
    contact = params["contact"]
    message = params["message"]
    profile = get_profile_or_default(app_name)
    app = profile["app"]
    
    # 1. Prepare
    log("prepare", f"focusing {app}")
    hide_other_apps(app)
    activate(app)
    
    # 2. Navigate
    if not _navigate_to_contact(profile, contact, log):
        restore_apps()
        return False, f"Could not navigate to '{contact}'"
    
    # 3. Verify chat opened (quick re-observe)
    state = observe(app)
    if not state.get("main"):
        # Main empty — try workaround: click another then click back
        log("retry", "main area empty, trying click-away-and-back")
        sidebar_matches = ocr_find("", {"x_max": profile["layout"].get("sidebar_x_max", 400),
                                         "y_min": 250, "y_max": 700})
        others = [m for m in sidebar_matches if contact.lower() not in m["text"].lower()]
        if others:
            click_pos(others[0]["cx"], others[0]["cy"])
            time.sleep(0.3)
        contact_matches = ocr_find(contact, {"x_max": profile["layout"].get("sidebar_x_max", 400)})
        if contact_matches:
            click_pos(contact_matches[0]["cx"], contact_matches[0]["cy"])
            time.sleep(0.5)
    
    # 4. Find input + type + send
    log("input", "clicking input field")
    if not _find_input(profile):
        restore_apps()
        return False, "Could not find input field"
    time.sleep(0.2)
    
    paste_text(message)
    time.sleep(0.2)
    
    send_key = profile.get("send", {}).get("key", "return")
    press_key(send_key)
    time.sleep(0.3)
    
    # 5. Verify (Level 3: OCR spot check)
    keyword = ''.join(c for c in message[:10] if ord(c) < 0x10000)
    if keyword:
        verify_region = {"x_min": profile["layout"].get("sidebar_width", 250) + 
                         (check_window_bounds(app) or (0,0,0,0))[0]}
        matches = ocr_find(keyword, verify_region)
        if matches:
            log("verify", f"✓ '{matches[0]['text']}' found in chat")
        else:
            log("verify", "⚠ message not found by OCR (may still have sent)")
    
    # 6. Cleanup
    restore_apps()
    return True, f"Sent to {contact}: {message[:40]}"


def task_read_messages(app_name, params, log):
    """Generic read messages from current or specified chat."""
    contact = params.get("contact", "")
    profile = get_profile_or_default(app_name)
    app = profile["app"]
    
    hide_other_apps(app)
    activate(app)
    
    if contact:
        _navigate_to_contact(profile, contact, log)
    
    state = observe(app)
    restore_apps()
    
    messages = state.get("main", state.get("texts", []))
    return True, "\n".join(messages)


def task_scroll_history(app_name, params, log):
    """Scroll up to read older messages. Returns collected text from each page."""
    contact = params.get("contact", "")
    pages = int(params.get("pages", "3"))
    profile = get_profile_or_default(app_name)
    app = profile["app"]
    
    hide_other_apps(app)
    activate(app)
    
    if contact:
        if not _navigate_to_contact(profile, contact, log):
            restore_apps()
            return False, f"Could not navigate to '{contact}'"
        time.sleep(0.5)
    
    # Click chat area to ensure scroll focus is there
    bounds = check_window_bounds(app)
    if bounds:
        wx, wy, ww, wh = bounds
        sw = profile["layout"].get("sidebar_width", 250)
        click_pos(wx + sw + (ww - sw) // 2, wy + wh // 2)
        time.sleep(0.2)
    
    all_messages = []
    
    for i in range(pages):
        # Page Up (key code 116)
        for _ in range(3):
            osascript('tell application "System Events" to key code 116')
            time.sleep(0.2)
        time.sleep(0.3)
        
        state = observe(app)
        page_texts = state.get("main", [])
        log(f"page_{i+1}", f"{len(page_texts)} items: {' | '.join(page_texts[:8])}")
        all_messages.append(f"--- Page {i+1} ---")
        all_messages.extend(page_texts)
    
    # Scroll back to bottom (Cmd+Down or End key)
    osascript('tell application "System Events" to key code 119')  # End key
    time.sleep(0.3)
    
    restore_apps()
    return True, "\n".join(all_messages)


# ═══════════════════════════════════════════
# General-purpose tasks (any app, no profile needed)
# ═══════════════════════════════════════════

def task_open_app(app_name, params, log):
    """Open and focus an app. Hides others for clean workspace."""
    app = params.get("app", app_name)
    hide_other = params.get("hide_others", "true").lower() == "true"
    
    if hide_other:
        hidden = hide_other_apps(app)
        log("prepare", f"hid {len(hidden)} apps")
    
    activate(app)
    
    # Verify
    front = check_frontmost()
    if front == app:
        log("verify", f"✓ {app} is frontmost")
        return True, f"{app} is open and focused"
    else:
        log("verify", f"⚠ frontmost is {front}, not {app}")
        return False, f"Failed to focus {app}, frontmost is {front}"


def task_read_screen(app_name, params, log):
    """Read all visible text on screen. Optionally filter by region."""
    app = params.get("app", app_name)
    region_str = params.get("region", "")
    
    if app and app != "any":
        activate(app)
        time.sleep(0.3)
    
    region = json.loads(region_str) if region_str else None
    
    if region:
        items = ocr_find("", region)
    else:
        items = ocr_full()
    
    log("ocr", f"found {len(items)} text elements")
    
    lines = []
    for item in items:
        cx, cy = item.get("cx", item["x"] + item["w"]//2), item.get("cy", item["y"] + item["h"]//2)
        lines.append(f"({cx},{cy}) {item['text']}")
    
    return True, "\n".join(lines)


def task_click_element(app_name, params, log):
    """Find and click an element by text (OCR) or template."""
    app = params.get("app", app_name)
    text = params.get("text", "")
    template = params.get("template", "")
    region_str = params.get("region", "")
    
    if app and app != "any":
        activate(app)
        time.sleep(0.2)
    
    region = json.loads(region_str) if region_str else None
    
    # Try template first
    if template:
        r = check_template(app, template)
        if r and r.get("found"):
            click_pos(r["x"], r["y"])
            log("click", f"template '{template}' at ({r['x']},{r['y']}) conf={r['confidence']}")
            return True, f"Clicked template '{template}'"
    
    # OCR
    if text:
        matches = ocr_find(text, region)
        if matches:
            m = matches[0]
            click_pos(m["cx"], m["cy"])
            log("click", f"OCR '{m['text']}' at ({m['cx']},{m['cy']})")
            return True, f"Clicked '{m['text']}'"
        else:
            log("click", f"'{text}' not found on screen")
            return False, f"Text '{text}' not found"
    
    return False, "No text or template specified"


def task_type_in_field(app_name, params, log):
    """Find a field by label/placeholder text, click it, and type."""
    app = params.get("app", app_name)
    field = params.get("field", "")
    text = params["text"]
    clear = params.get("clear", "false").lower() == "true"
    submit = params.get("submit", "false").lower() == "true"
    
    if app and app != "any":
        activate(app)
        time.sleep(0.2)
    
    # Find and click field
    if field:
        matches = ocr_find(field)
        if matches:
            m = matches[0]
            click_pos(m["cx"], m["cy"])
            log("field", f"clicked '{m['text']}' at ({m['cx']},{m['cy']})")
        else:
            log("field", f"'{field}' not found")
            return False, f"Field '{field}' not found"
    
    time.sleep(0.2)
    
    if clear:
        press_shortcut("a", ["command"])
        time.sleep(0.1)
    
    paste_text(text)
    log("type", f"typed '{text[:30]}'")
    
    if submit:
        time.sleep(0.2)
        press_key("return")
        log("submit", "pressed return")
    
    return True, f"Typed '{text[:40]}' in field '{field}'"


def task_menu_action(app_name, params, log):
    """Execute a menu bar action via AppleScript. Most reliable for standard operations."""
    app = params.get("app", app_name)
    menu = params["menu"]          # e.g. "File"
    item = params["item"]          # e.g. "New Tab"
    submenu = params.get("submenu", "")  # optional submenu
    
    activate(app)
    time.sleep(0.3)
    
    if submenu:
        script = f'''
            tell application "System Events" to tell process "{app}"
                click menu item "{submenu}" of menu 1 of menu item "{item}" of menu 1 of menu bar item "{menu}" of menu bar 1
            end tell
        '''
    else:
        script = f'''
            tell application "System Events" to tell process "{app}"
                click menu item "{item}" of menu 1 of menu bar item "{menu}" of menu bar 1
            end tell
        '''
    
    try:
        osascript(script)
        log("menu", f"{app} → {menu} → {item}" + (f" → {submenu}" if submenu else ""))
        return True, f"Executed menu: {menu} → {item}"
    except Exception as e:
        log("menu", f"failed: {e}")
        return False, f"Menu action failed: {e}"


def task_list_menus(app_name, params, log):
    """List available menu items for an app. Useful for discovering what actions are available."""
    app = params.get("app", app_name)
    menu = params.get("menu", "")
    
    activate(app)
    time.sleep(0.3)
    
    if menu:
        # List items in specific menu
        script = f'''
            tell application "System Events" to tell process "{app}"
                return name of every menu item of menu 1 of menu bar item "{menu}" of menu bar 1
            end tell
        '''
        result = osascript(script)
        log("menus", f"{menu}: {result}")
        return True, f"{menu}: {result}"
    else:
        # List all menu bar items
        script = f'''
            tell application "System Events" to tell process "{app}"
                return name of every menu bar item of menu bar 1
            end tell
        '''
        result = osascript(script)
        log("menus", result)
        return True, result


def task_scroll(app_name, params, log):
    """Scroll in any direction in the current app."""
    app = params.get("app", app_name)
    direction = params.get("direction", "down")
    amount = int(params.get("amount", "3"))
    
    if app and app != "any":
        activate(app)
        time.sleep(0.2)
    
    # Key codes: Page Up=116, Page Down=121, Up=126, Down=125
    key_codes = {
        "up": 116,      # Page Up
        "down": 121,     # Page Down
        "top": 115,      # Home
        "bottom": 119,   # End
    }
    
    code = key_codes.get(direction, 121)
    
    if direction in ("top", "bottom"):
        osascript(f'tell application "System Events" to key code {code}')
        log("scroll", f"jumped to {direction}")
    else:
        for _ in range(amount):
            osascript(f'tell application "System Events" to key code {code}')
            time.sleep(0.15)
        log("scroll", f"scrolled {direction} × {amount}")
    
    return True, f"Scrolled {direction}"


TASKS = {
    # --- Chat tasks (use app profiles) ---
    "send_message": {
        "fn": task_send_message,
        "params": {"contact": "Target contact/channel name", "message": "Message to send"},
    },
    "read_messages": {
        "fn": task_read_messages,
        "params": {"contact": "Contact name (optional, reads current chat)"},
    },
    "scroll_history": {
        "fn": task_scroll_history,
        "params": {"contact": "Contact name (optional)", "pages": "Number of pages to scroll up (default 3, optional)"},
    },
    # --- General tasks (any app) ---
    "open_app": {
        "fn": task_open_app,
        "params": {"app": "App name (optional, uses --app)", "hide_others": "Hide other apps (default true, optional)"},
    },
    "read_screen": {
        "fn": task_read_screen,
        "params": {"app": "App to focus (optional)", "region": "JSON region filter (optional)"},
    },
    "click_element": {
        "fn": task_click_element,
        "params": {"text": "Text to find and click (optional)", "template": "Template name (optional)", "region": "JSON region filter (optional)"},
    },
    "type_in_field": {
        "fn": task_type_in_field,
        "params": {"field": "Field label/placeholder to click (optional)", "text": "Text to type", "clear": "Clear field first (optional)", "submit": "Press Enter after (optional)"},
    },
    "menu_action": {
        "fn": task_menu_action,
        "params": {"menu": "Menu bar item (e.g. File)", "item": "Menu item (e.g. New Tab)", "submenu": "Submenu item (optional)"},
    },
    "list_menus": {
        "fn": task_list_menus,
        "params": {"menu": "Specific menu to expand (optional, lists all if omitted)"},
    },
    "scroll": {
        "fn": task_scroll,
        "params": {"direction": "up/down/top/bottom (default down, optional)", "amount": "Number of pages (default 3, optional)"},
    },
}


def run_task(task_name, app_name, params):
    if task_name not in TASKS:
        return False, f"Unknown task '{task_name}'. Available: {', '.join(TASKS.keys())}"
    
    task_def = TASKS[task_name]
    logs = []
    def log(step, msg):
        logs.append(f"  [{step}] {msg}")
        print(f"  [{step}] {msg}", flush=True)
    
    print(f"▶ {task_name} ({app_name})")
    print(f"  params: {json.dumps(params, ensure_ascii=False)}")
    
    start = time.time()
    try:
        ok, result = task_def["fn"](app_name, params, log)
    except Exception as e:
        ok, result = False, f"Error: {e}"
    
    elapsed = time.time() - start
    print(f"\n{'✅' if ok else '❌'} {result} ({elapsed:.1f}s)")
    return ok, result


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GUI Agent")
    sub = parser.add_subparsers(dest="cmd")
    
    p_obs = sub.add_parser("observe")
    p_obs.add_argument("--app")
    
    p_exec = sub.add_parser("exec")
    p_exec.add_argument("action_json")
    
    p_task = sub.add_parser("task")
    p_task.add_argument("name")
    p_task.add_argument("--app", required=True)
    p_task.add_argument("--param", action="append", default=[])
    
    p_find = sub.add_parser("find")
    p_find.add_argument("text")
    p_find.add_argument("--region")
    
    sub.add_parser("tasks")
    sub.add_parser("apps")
    sub.add_parser("templates")
    
    args = parser.parse_args()
    
    if args.cmd == "observe":
        print(format_state(observe(args.app)))
    
    elif args.cmd == "exec":
        action = json.loads(args.action_json)
        ok, msg = execute_action(action)
        print(json.dumps({"success": ok, "message": msg}))
    
    elif args.cmd == "task":
        params = {}
        for kv in args.param:
            k, v = kv.split("=", 1)
            params[k] = v
        ok, _ = run_task(args.name, args.app, params)
        sys.exit(0 if ok else 1)
    
    elif args.cmd == "tasks":
        for name, info in TASKS.items():
            print(f"  {name}:")
            for k, v in info["params"].items():
                print(f"    --param {k}=\"...\"  ({v})")
    
    elif args.cmd == "apps":
        if APPS_DIR.exists():
            for f in sorted(APPS_DIR.glob("*.json")):
                data = json.load(open(f))
                quirks = len(data.get("quirks", []))
                print(f"  {data['app']}: nav={data.get('navigation',{}).get('method','?')}, "
                      f"input={data.get('input',{}).get('method','?')}, "
                      f"send={data.get('send',{}).get('key','?')}, "
                      f"{quirks} quirks")
    
    elif args.cmd == "templates":
        tpl_dir = SCRIPT_DIR.parent / "templates"
        if tpl_dir.exists():
            for d in sorted(tpl_dir.iterdir()):
                if d.is_dir() and (d / "index.json").exists():
                    for name in json.load(open(d / "index.json")):
                        print(f"  {d.name}/{name}")
    
    elif args.cmd == "find":
        region = json.loads(args.region) if hasattr(args, 'region') and args.region else None
        for m in ocr_find(args.text, region):
            print(f"  '{m['text']}' at ({m['cx']},{m['cy']})")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
