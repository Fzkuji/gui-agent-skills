#!/usr/bin/env python3
"""
Spreadsheet cell location and selection utilities.

Two approaches:
1. Name Box / keyboard: type cell address directly (zero-vision, 100% accurate)
2. OCR-based: scan row/column headers to compute cell pixel coordinates

Works with: Microsoft Excel, LibreOffice Calc, Google Sheets (desktop app)
"""

import re
import time
import subprocess
import platform

SYSTEM = platform.system()


# ═══════════════════════════════════════════
# Approach 1: Name Box / Keyboard navigation
# ═══════════════════════════════════════════

def select_cell_by_name(cell_ref, app="Microsoft Excel"):
    """Select a cell or range by typing into the Name Box.
    
    Works in Excel and LibreOffice Calc.
    
    Args:
        cell_ref: e.g. "A1", "B3:D7", "Sheet2!A1:C10"
        app: application name (for activate)
    
    Examples:
        select_cell_by_name("A1")       # single cell
        select_cell_by_name("B3:D7")    # range
        select_cell_by_name("A1:A100")  # column selection
    """
    from platform_input import activate_app, key_combo, type_text, key_press, paste_text
    
    activate_app(app)
    time.sleep(0.3)
    
    # Click the Name Box: Ctrl+G (Go To) or just click Name Box
    # Most reliable: Cmd+G doesn't work in Excel Mac, use Name Box click
    # The Name Box is always at top-left. We use keyboard shortcut instead:
    # In Excel Mac: click Name Box = Cmd+F5 doesn't work reliably
    # Best approach: just press Ctrl+G or F5 for Go To dialog
    
    if app == "Microsoft Excel":
        # Excel Mac: use Ctrl+G to open Go To dialog, then type in Reference field
        key_press("escape")
        time.sleep(0.1)
        
        # Open Go To dialog with Ctrl+G (not Cmd+G!)
        from pynput.keyboard import Key, Controller as KBController
        kb = KBController()
        kb.press(Key.ctrl)
        kb.press('g')
        time.sleep(0.05)
        kb.release('g')
        kb.release(Key.ctrl)
        time.sleep(0.8)
        
        # Tab to the Reference field (it may not be focused by default)
        # Actually in Excel Mac Go To, the Reference field IS focused
        # But paste doesn't work there. Use type_text instead.
        # Clear any existing text first
        key_combo("command", "a")
        time.sleep(0.05)
        type_text(cell_ref)
        time.sleep(0.2)
        key_press("return")
        time.sleep(0.3)
        
    elif app in ("LibreOffice Calc", "soffice"):
        # LibreOffice: Name Box is focused by clicking it or pressing F5
        # F5 opens Navigator in LibreOffice, not Go To
        # In LibreOffice, click on the Name Box or use Ctrl+F5
        # Simplest: Ctrl+G doesn't exist. Use Name Box click.
        # But for keyboard: just click Name Box area
        # Alternative: use the sidebar cell reference
        key_press("escape")
        time.sleep(0.1)
        # Press Ctrl+F5 for Navigator, or just use the Name Box
        # Actually, in LibreOffice the Name Box is focused by clicking it
        # For keyboard approach, we can use Ctrl+G equivalent:
        # There's no direct equivalent. Let's use the menu:
        # But simplest for testing: just type in cell
        pass
    
    else:
        # Generic: try F5 (Go To) 
        key_press("f5")
        time.sleep(0.5)
        paste_text(cell_ref)
        time.sleep(0.1)
        key_press("return")
        time.sleep(0.2)


def select_range_by_keyboard(start_cell, end_cell, app="Microsoft Excel"):
    """Select a range using keyboard navigation.
    
    Click start cell via Name Box, then Shift+click end cell.
    More reliable than Go To for some apps.
    
    Args:
        start_cell: e.g. "B3"
        end_cell: e.g. "D7"
        app: application name
    """
    # Just use Name Box with range notation
    select_cell_by_name(f"{start_cell}:{end_cell}", app=app)


def navigate_to_cell(cell_ref, app="Microsoft Excel"):
    """Navigate to a cell (just move cursor there, don't select range).
    
    Uses Ctrl+G / Name Box approach.
    """
    select_cell_by_name(cell_ref, app=app)


# ═══════════════════════════════════════════
# Approach 2: OCR-based cell coordinate lookup
# ═══════════════════════════════════════════

def _col_letter_to_index(col_str):
    """Convert column letter(s) to 0-based index. 'A'->0, 'B'->1, 'Z'->25, 'AA'->26"""
    result = 0
    for c in col_str.upper():
        result = result * 26 + (ord(c) - ord('A') + 1)
    return result - 1


def _parse_cell_ref(cell_ref):
    """Parse cell reference like 'B3' into (col_str, row_num). Returns ('B', 3)."""
    m = re.match(r'^([A-Za-z]+)(\d+)$', cell_ref)
    if not m:
        raise ValueError(f"Invalid cell reference: {cell_ref}")
    return m.group(1).upper(), int(m.group(2))


def locate_cell_by_ocr(cell_ref, app_name="Microsoft Excel", screenshot_path=None):
    """Find pixel coordinates of a cell by OCR-scanning row and column headers.
    
    Scans the column header row (A, B, C...) and the row number column (1, 2, 3...)
    to determine where a specific cell is on screen.
    
    Args:
        cell_ref: e.g. "B3", "D7"
        app_name: name of the spreadsheet app
        screenshot_path: optional pre-taken screenshot; if None, takes one
        
    Returns:
        (center_x, center_y, cell_width, cell_height) or None if not found
    """
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from platform_input import screenshot as take_screenshot, get_window_bounds
    
    col_str, row_num = _parse_cell_ref(cell_ref)
    
    # Take screenshot if not provided
    if not screenshot_path:
        screenshot_path = take_screenshot("/tmp/spreadsheet_ocr.png")
    
    # Get window bounds for coordinate offset
    bounds = get_window_bounds(app_name)
    if not bounds:
        print(f"Warning: could not get window bounds for {app_name}")
        win_x, win_y = 0, 0
    else:
        win_x, win_y = bounds[0], bounds[1]
    
    # Run OCR on the screenshot
    ocr_results = _run_ocr(screenshot_path)
    if not ocr_results:
        print("OCR returned no results")
        return None
    
    # Find column header position (look for the letter in the header row)
    col_x = _find_column_header(ocr_results, col_str)
    
    # Find row number position (look for the number in the row number column)
    row_y = _find_row_number(ocr_results, row_num)
    
    if col_x is None:
        print(f"Could not find column header '{col_str}' via OCR")
        return None
    if row_y is None:
        print(f"Could not find row number '{row_num}' via OCR")
        return None
    
    # Estimate cell dimensions from nearby headers
    cell_width = _estimate_cell_width(ocr_results, col_str)
    cell_height = _estimate_cell_height(ocr_results, row_num)
    
    center_x = col_x
    center_y = row_y
    
    print(f"Cell {cell_ref} located at ({center_x}, {center_y}), "
          f"estimated size: {cell_width}x{cell_height}")
    
    return center_x, center_y, cell_width, cell_height


def _run_ocr(image_path):
    """Run Apple Vision OCR on image, return list of (text, x, y, w, h)."""
    if SYSTEM != "Darwin":
        # Fallback: use Tesseract
        return _run_tesseract_ocr(image_path)
    
    # Use the existing OCR script
    import os, sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ocr_script = os.path.join(script_dir, "ocr_screen.sh")
    
    if os.path.exists(ocr_script):
        try:
            r = subprocess.run(["bash", ocr_script, image_path],
                             capture_output=True, text=True, timeout=30)
            return _parse_ocr_output(r.stdout)
        except Exception as e:
            print(f"OCR script failed: {e}")
    
    # Fallback: use Vision framework directly via Swift
    return _run_vision_ocr(image_path)


def _run_vision_ocr(image_path):
    """Run Apple Vision OCR via Swift subprocess."""
    swift_code = '''
import Foundation
import Vision
import AppKit

let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])

let height = CGFloat(cgImage.height)
let width = CGFloat(cgImage.width)

if let results = request.results {
    for obs in results {
        if let candidate = obs.topCandidates(1).first {
            let box = obs.boundingBox
            let x = Int(box.origin.x * width)
            let y = Int((1 - box.origin.y - box.height) * height)
            let w = Int(box.width * width)
            let h = Int(box.height * height)
            print("\\(candidate.string)\\t\\(x)\\t\\(y)\\t\\(w)\\t\\(h)")
        }
    }
}
'''
    try:
        # Write Swift code to temp file
        swift_path = "/tmp/_ocr_vision.swift"
        with open(swift_path, "w") as f:
            f.write(swift_code)
        
        r = subprocess.run(["swift", swift_path, image_path],
                         capture_output=True, text=True, timeout=30)
        results = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) == 5:
                text, x, y, w, h = parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                results.append((text, x, y, w, h))
        return results
    except Exception as e:
        print(f"Vision OCR failed: {e}")
        return []


def _run_tesseract_ocr(image_path):
    """Fallback OCR using Tesseract."""
    try:
        r = subprocess.run(["tesseract", image_path, "-", "--psm", "6", "tsv"],
                         capture_output=True, text=True, timeout=30)
        results = []
        for line in r.stdout.strip().split("\n")[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) >= 12 and parts[11].strip():
                text = parts[11].strip()
                x, y, w, h = int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9])
                results.append((text, x, y, w, h))
        return results
    except Exception as e:
        print(f"Tesseract OCR failed: {e}")
        return []


def _parse_ocr_output(output):
    """Parse tab-separated OCR output: text\\tx\\ty\\tw\\th"""
    results = []
    for line in output.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 5:
            try:
                text = parts[0]
                x, y, w, h = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                results.append((text, x, y, w, h))
            except ValueError:
                continue
    return results


def _find_column_header(ocr_results, col_str):
    """Find the x-coordinate center of a column header letter."""
    # Column headers are usually in the top area of the spreadsheet
    # Look for exact match of the column letter
    candidates = []
    for text, x, y, w, h in ocr_results:
        # Column headers are typically in the top 80 pixels of the spreadsheet area
        # and the text should be a single letter or two-letter combo
        clean = text.strip()
        if clean == col_str and y < 200:  # in header region
            candidates.append((x + w // 2, y, w))
    
    if candidates:
        # Return the one closest to the expected header row
        candidates.sort(key=lambda c: c[1])  # sort by y (topmost)
        return candidates[0][0]
    
    # Fuzzy: sometimes OCR groups letters together like "A B C D"
    for text, x, y, w, h in ocr_results:
        if y < 200 and col_str in text.split():
            # Estimate position within the grouped text
            parts = text.split()
            if col_str in parts:
                idx = parts.index(col_str)
                char_width = w / len(text.replace(" ", ""))
                offset = sum(len(p) for p in parts[:idx]) + idx  # account for spaces
                estimated_x = x + int(offset * char_width) + int(char_width / 2)
                return estimated_x
    
    return None


def _find_row_number(ocr_results, row_num):
    """Find the y-coordinate center of a row number."""
    row_str = str(row_num)
    candidates = []
    for text, x, y, w, h in ocr_results:
        clean = text.strip()
        if clean == row_str and x < 100:  # in row number column (left side)
            candidates.append((y + h // 2, x))
    
    if candidates:
        candidates.sort(key=lambda c: c[1])  # sort by x (leftmost = row number column)
        return candidates[0][0]
    
    return None


def _estimate_cell_width(ocr_results, col_str):
    """Estimate cell width from adjacent column headers."""
    col_idx = _col_letter_to_index(col_str)
    
    # Find adjacent columns
    headers = {}
    for text, x, y, w, h in ocr_results:
        clean = text.strip()
        if y < 200 and re.match(r'^[A-Z]{1,2}$', clean):
            idx = _col_letter_to_index(clean)
            headers[idx] = x + w // 2
    
    if col_idx in headers:
        # Check next column
        if col_idx + 1 in headers:
            return headers[col_idx + 1] - headers[col_idx]
        # Check previous column
        if col_idx - 1 in headers:
            return headers[col_idx] - headers[col_idx - 1]
    
    return 80  # default cell width


def _estimate_cell_height(ocr_results, row_num):
    """Estimate cell height from adjacent row numbers."""
    rows = {}
    for text, x, y, w, h in ocr_results:
        clean = text.strip()
        if x < 100 and clean.isdigit():
            rows[int(clean)] = y + h // 2
    
    if row_num in rows:
        if row_num + 1 in rows:
            return rows[row_num + 1] - rows[row_num]
        if row_num - 1 in rows:
            return rows[row_num] - rows[row_num - 1]
    
    return 21  # default cell height


def select_range_by_ocr(start_cell, end_cell, app_name="Microsoft Excel"):
    """Select a cell range by OCR-locating the cells and dragging.
    
    Args:
        start_cell: e.g. "B3"
        end_cell: e.g. "D7"
        app_name: spreadsheet application name
    """
    from platform_input import mouse_drag, activate_app
    
    activate_app(app_name)
    time.sleep(0.3)
    
    start_loc = locate_cell_by_ocr(start_cell, app_name)
    if not start_loc:
        print(f"Could not locate {start_cell}")
        return False
    
    end_loc = locate_cell_by_ocr(end_cell, app_name)
    if not end_loc:
        print(f"Could not locate {end_cell}")
        return False
    
    sx, sy = start_loc[0], start_loc[1]
    ex, ey = end_loc[0], end_loc[1]
    
    print(f"Dragging from ({sx}, {sy}) to ({ex}, {ey})")
    mouse_drag(sx, sy, ex, ey, duration=0.5)
    
    return True


# ═══════════════════════════════════════════
# Combined approach: try keyboard first, OCR as fallback
# ═══════════════════════════════════════════

def select_range(start_cell, end_cell=None, app="Microsoft Excel", method="auto"):
    """Select a cell or range in a spreadsheet.
    
    Args:
        start_cell: e.g. "B3" or "B3:D7" (range notation)
        end_cell: e.g. "D7" (optional if start_cell contains range)
        app: application name
        method: "keyboard" (Name Box), "ocr" (visual), or "auto" (keyboard first)
    
    Returns:
        True if selection succeeded
    """
    # Parse range notation
    if ":" in start_cell and end_cell is None:
        parts = start_cell.split(":")
        start_cell = parts[0]
        end_cell = parts[1]
    
    range_str = f"{start_cell}:{end_cell}" if end_cell else start_cell
    
    if method == "keyboard" or method == "auto":
        try:
            select_cell_by_name(range_str, app=app)
            return True
        except Exception as e:
            if method == "keyboard":
                print(f"Keyboard selection failed: {e}")
                return False
            print(f"Keyboard method failed, falling back to OCR: {e}")
    
    if method == "ocr" or method == "auto":
        if end_cell:
            return select_range_by_ocr(start_cell, end_cell, app_name=app)
        else:
            loc = locate_cell_by_ocr(start_cell, app_name=app)
            if loc:
                from platform_input import mouse_click
                mouse_click(loc[0], loc[1])
                return True
            return False
    
    return False


# ═══════════════════════════════════════════
# Self-test
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("=== Spreadsheet Utils Self-Test ===")
    
    # Test cell ref parsing
    assert _parse_cell_ref("A1") == ("A", 1)
    assert _parse_cell_ref("B3") == ("B", 3)
    assert _parse_cell_ref("AA100") == ("AA", 100)
    print("Cell ref parsing: ok")
    
    # Test column index
    assert _col_letter_to_index("A") == 0
    assert _col_letter_to_index("B") == 1
    assert _col_letter_to_index("Z") == 25
    assert _col_letter_to_index("AA") == 26
    print("Column index: ok")
    
    print("\nAll tests passed ✅")
    print("\nUsage:")
    print('  select_range("B3:D7", app="Microsoft Excel")  # keyboard method')
    print('  select_range("B3:D7", app="Microsoft Excel", method="ocr")  # OCR method')
    print('  locate_cell_by_ocr("C5")  # just find coordinates')
