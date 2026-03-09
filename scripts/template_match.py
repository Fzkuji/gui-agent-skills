#!/usr/bin/env python3
"""
GUI Template Matching - Learn once, match forever.

Usage:
  # Save a template (crop from current screen)
  python template_match.py save --app WeChat --name search_bar --region 100,200,300,250
  
  # Save with click offset (where to click within the template)
  python template_match.py save --app WeChat --name search_bar --region 100,200,300,250 --click 150,225
  
  # Find a template on current screen
  python template_match.py find --app WeChat --name search_bar
  
  # Find and click
  python template_match.py click --app WeChat --name search_bar
  
  # List all saved templates
  python template_match.py list [--app WeChat]
  
  # Auto-learn: screenshot + vision model identified coords, save as template
  python template_match.py learn --app WeChat --name search_bar --center 485,244 --size 200,40

Output (find/click):
  JSON with matched position: {"found": true, "x": 485, "y": 244, "confidence": 0.95}
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Template storage directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
SCREENSHOT_PATH = "/tmp/gui_template_screen.png"


def get_screen_resolution():
    """Get logical screen resolution."""
    result = subprocess.run(
        ["system_profiler", "SPDisplaysDataType"],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if "Resolution" in line:
            # e.g., "Resolution: 3024 x 1964 Retina"
            parts = line.split()
            idx = parts.index("x")
            phys_w, phys_h = int(parts[idx - 1]), int(parts[idx + 1])
            is_retina = "Retina" in line
            if is_retina:
                return phys_w // 2, phys_h // 2
            return phys_w, phys_h
    return 1512, 982  # default MacBook Pro


def take_screenshot(path=SCREENSHOT_PATH):
    """Take a screenshot and return the image."""
    subprocess.run(["screencapture", "-x", path], check=True)
    img = cv2.imread(path)
    return img


def get_index_path(app_name):
    """Get the index.json path for an app."""
    app_dir = TEMPLATE_DIR / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir / "index.json"


def load_index(app_name):
    """Load the template index for an app."""
    path = get_index_path(app_name)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_index(app_name, index):
    """Save the template index for an app."""
    path = get_index_path(app_name)
    with open(path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def cmd_save(args):
    """Save a template by cropping from current screen."""
    img = take_screenshot()
    
    # Parse region: x,y,w,h (in logical pixels, but screenshot is retina)
    x, y, w, h = map(int, args.region.split(","))
    
    # Retina: multiply by 2 for actual pixel coords in screenshot
    scale = img.shape[1] / get_screen_resolution()[0]
    sx, sy, sw, sh = int(x * scale), int(y * scale), int(w * scale), int(h * scale)
    
    template = img[sy:sy+sh, sx:sx+sw]
    
    # Save template image
    app_dir = TEMPLATE_DIR / args.app
    app_dir.mkdir(parents=True, exist_ok=True)
    template_path = app_dir / f"{args.name}.png"
    cv2.imwrite(str(template_path), template)
    
    # Determine click offset (center of template by default)
    if args.click:
        click_x, click_y = map(int, args.click.split(","))
        click_offset = [click_x - x, click_y - y]
    else:
        click_offset = [w // 2, h // 2]
    
    # Update index
    index = load_index(args.app)
    index[args.name] = {
        "template": f"{args.name}.png",
        "click_offset": click_offset,
        "original_region": [x, y, w, h],
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_matched": None,
        "match_count": 0,
        "threshold": args.threshold
    }
    save_index(args.app, index)
    
    print(json.dumps({
        "saved": True,
        "app": args.app,
        "name": args.name,
        "path": str(template_path),
        "region": [x, y, w, h],
        "click_offset": click_offset
    }))


def cmd_learn(args):
    """Auto-learn: given a center point and size, crop and save template."""
    img = take_screenshot()
    
    cx, cy = map(int, args.center.split(","))
    tw, th = map(int, args.size.split(","))
    
    # Region in logical pixels
    x = cx - tw // 2
    y = cy - th // 2
    
    # Retina scaling
    scale = img.shape[1] / get_screen_resolution()[0]
    sx, sy, sw, sh = int(x * scale), int(y * scale), int(tw * scale), int(th * scale)
    
    # Clamp to image bounds
    sx = max(0, sx)
    sy = max(0, sy)
    sw = min(sw, img.shape[1] - sx)
    sh = min(sh, img.shape[0] - sy)
    
    template = img[sy:sy+sh, sx:sx+sw]
    
    if template.size == 0:
        print(json.dumps({"saved": False, "error": "Empty template region"}))
        return
    
    # Save
    app_dir = TEMPLATE_DIR / args.app
    app_dir.mkdir(parents=True, exist_ok=True)
    template_path = app_dir / f"{args.name}.png"
    cv2.imwrite(str(template_path), template)
    
    # Click offset is center
    click_offset = [tw // 2, th // 2]
    
    index = load_index(args.app)
    index[args.name] = {
        "template": f"{args.name}.png",
        "click_offset": click_offset,
        "original_region": [x, y, tw, th],
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_matched": None,
        "match_count": 0,
        "threshold": args.threshold
    }
    save_index(args.app, index)
    
    print(json.dumps({
        "saved": True,
        "app": args.app,
        "name": args.name,
        "center": [cx, cy],
        "size": [tw, th],
        "click_offset": click_offset
    }))


def find_template(app_name, element_name, screenshot=None, multi_scale=True):
    """Find a template on screen. Returns (x, y, confidence) or None."""
    index = load_index(app_name)
    if element_name not in index:
        return None
    
    entry = index[element_name]
    template_path = TEMPLATE_DIR / app_name / entry["template"]
    
    if not template_path.exists():
        return None
    
    template = cv2.imread(str(template_path))
    if screenshot is None:
        screenshot = take_screenshot()
    
    threshold = entry.get("threshold", 0.85)
    click_offset = entry.get("click_offset", [0, 0])
    screen_w = get_screen_resolution()[0]
    scale = screenshot.shape[1] / screen_w
    
    best_val = 0
    best_loc = None
    best_scale_factor = 1.0
    
    # Multi-scale matching for robustness
    # Only use multi-scale for larger templates; small ones get false positives
    scales = [1.0]
    if multi_scale:
        tmpl_min_dim = min(template.shape[0], template.shape[1])
        if tmpl_min_dim > 80:  # Only multi-scale for templates > 80px (retina)
            scales = [0.9, 0.95, 1.0, 1.05, 1.1]
        # Always try exact match first (scale=1.0 is already in list)
    
    gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    for s in scales:
        if s != 1.0:
            new_w = int(gray_template.shape[1] * s)
            new_h = int(gray_template.shape[0] * s)
            if new_w < 10 or new_h < 10:
                continue
            scaled_template = cv2.resize(gray_template, (new_w, new_h))
        else:
            scaled_template = gray_template
        
        if (scaled_template.shape[0] > gray_screen.shape[0] or
            scaled_template.shape[1] > gray_screen.shape[1]):
            continue
        
        result = cv2.matchTemplate(gray_screen, scaled_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale_factor = s
    
    if best_val < threshold:
        return None
    
    # Click position: template top-left (in retina pixels) + click_offset (in logical) * scale
    # Then convert everything back to logical
    logical_x = int(best_loc[0] / scale) + click_offset[0]
    logical_y = int(best_loc[1] / scale) + click_offset[1]
    
    # Update stats
    index[element_name]["last_matched"] = time.strftime("%Y-%m-%d %H:%M:%S")
    index[element_name]["match_count"] = index[element_name].get("match_count", 0) + 1
    save_index(app_name, index)
    
    return {
        "found": True,
        "x": logical_x,
        "y": logical_y,
        "confidence": round(best_val, 4),
        "scale": round(best_scale_factor, 2)
    }


def cmd_find(args):
    """Find a template on current screen."""
    result = find_template(args.app, args.name)
    if result:
        print(json.dumps(result))
    else:
        print(json.dumps({"found": False, "app": args.app, "name": args.name}))


def cmd_click(args):
    """Find and click a template."""
    result = find_template(args.app, args.name)
    if not result:
        print(json.dumps({"clicked": False, "found": False, "app": args.app, "name": args.name}))
        return
    
    x, y = result["x"], result["y"]
    subprocess.run(["cliclick", f"c:{x},{y}"], check=True)
    
    print(json.dumps({
        "clicked": True,
        "x": x,
        "y": y,
        "confidence": result["confidence"]
    }))


def cmd_list(args):
    """List all saved templates."""
    if args.app:
        apps = [args.app]
    else:
        if not TEMPLATE_DIR.exists():
            print(json.dumps({"templates": {}}))
            return
        apps = [d.name for d in TEMPLATE_DIR.iterdir() if d.is_dir()]
    
    templates = {}
    for app in apps:
        index = load_index(app)
        if index:
            templates[app] = index
    
    print(json.dumps({"templates": templates}, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="GUI Template Matching")
    sub = parser.add_subparsers(dest="command", required=True)
    
    # save
    p_save = sub.add_parser("save", help="Save template from screen region")
    p_save.add_argument("--app", required=True, help="App name")
    p_save.add_argument("--name", required=True, help="Element name")
    p_save.add_argument("--region", required=True, help="x,y,w,h in logical pixels")
    p_save.add_argument("--click", help="Click position x,y in logical pixels (default: center)")
    p_save.add_argument("--threshold", type=float, default=0.85, help="Match threshold")
    
    # learn
    p_learn = sub.add_parser("learn", help="Auto-learn from center point")
    p_learn.add_argument("--app", required=True, help="App name")
    p_learn.add_argument("--name", required=True, help="Element name")
    p_learn.add_argument("--center", required=True, help="Center x,y in logical pixels")
    p_learn.add_argument("--size", default="80,40", help="Template w,h (default: 80,40)")
    p_learn.add_argument("--threshold", type=float, default=0.85, help="Match threshold")
    
    # find
    p_find = sub.add_parser("find", help="Find template on screen")
    p_find.add_argument("--app", required=True, help="App name")
    p_find.add_argument("--name", required=True, help="Element name")
    
    # click
    p_click = sub.add_parser("click", help="Find and click template")
    p_click.add_argument("--app", required=True, help="App name")
    p_click.add_argument("--name", required=True, help="Element name")
    
    # list
    p_list = sub.add_parser("list", help="List saved templates")
    p_list.add_argument("--app", help="Filter by app")
    
    args = parser.parse_args()
    
    if args.command == "save":
        cmd_save(args)
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "find":
        cmd_find(args)
    elif args.command == "click":
        cmd_click(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
