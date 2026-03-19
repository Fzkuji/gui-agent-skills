---
name: gui-act
description: "Execute GUI actions — click components, type text, send messages. Includes pre-action verification, post-action verification, and async wait handling."
---

# Act — Execute and Verify

Detection priority: **Template Match on full screen (0.3s) → YOLO (0.3s) → LLM (last resort)**

> **OCR is removed.** Do NOT use OCR coordinates for clicking. Use template matching
> (saved component images matched on full-screen screenshot) or visual analysis via
> the `image` tool. OCR text is unreliable for positioning (mixes content from
> overlapping windows, wrong coordinate systems).

## MANDATORY: Screenshot Before AND After Every Click

```
1. Screenshot (full screen) → analyze with image tool
2. Confirm target is visible and correct
3. Click via template match (app_memory.py click) or calculated position
4. Screenshot (full screen) → analyze with image tool
5. Confirm screen changed as expected
6. If NO change → click failed. Re-analyze, don't repeat blindly.
7. If WRONG app in front → Esc, re-activate target app, re-analyze.
```

This is NOT optional. Every single click gets a before/after screenshot.
`click_component` does this automatically. Manual clicks must do it explicitly.

## Pre-Click Verify (before every click)

1. Is the element actually on screen RIGHT NOW? (screenshot + image analysis)
2. Is it the CORRECT element (not similar name in another window)?
3. Is the TARGET APP in the foreground? (check menu bar in screenshot)
4. If ANY is NO → re-observe. Do not click.

## Clicking a Known Component

```bash
python3 scripts/agent.py click --app AppName --component ButtonName
```

This does full-screen template matching automatically:
```
1. Take full-screen screenshot (before)
2. Template match component on full screen → screen logical coordinates
3. If matched (conf > 0.7): click at logical coordinates
4. Take full-screen screenshot (after)
5. Verify screen changed + correct app still in front
6. If not matched → learn the app, then retry
```

### For elements NOT in memory (dynamic content):

```
1. Screenshot full screen
2. Crop the relevant region (e.g., search results area)
3. Use `image` tool on crop to identify what's there
4. Calculate screen coordinates: crop_origin + element_position_in_crop
5. Click at calculated coordinates
6. Screenshot to verify
```

**NEVER ask the `image` tool for coordinates on a full screenshot.** Vision models
can't reliably pinpoint pixels on large images. Always crop first, then analyze.

## Input Methods (via platform_input.py)

All input goes through `platform_input.py` (cross-platform, uses pynput):

```python
from platform_input import click_at, type_text, paste_text, key_press, key_combo, set_clipboard, screenshot

# Click (logical screen coords)
click_at(x, y)

# Type ASCII
type_text("hello")

# Paste CJK/special chars (clipboard + Cmd+V)
paste_text("中文")

# Key press
key_press("return")   # also: esc, tab, delete, space

# Key combo
key_combo("command", "v")
key_combo("command", "shift", "s")

# Screenshot (for verification)
screenshot("/tmp/check.png")
```

**Never use cliclick or osascript for input.** Those are macOS-only and removed.

## Sending Messages

**No hardcoded flow.** Sending messages is a WORKFLOW, not a built-in action.
New AI must explore the app to learn how to send, then save as workflow.

`agent.py send_message` prints step-by-step guidance but does NOT execute.
The agent must execute each step manually with screenshot verification.

### Generic steps (adapt per app):
```
1. SCREENSHOT → confirm app is frontmost
2. Find contact (search bar or scroll chat list)
3. SCREENSHOT → verify contact found (not internet search suggestion!)
4. Click contact
5. SCREENSHOT → verify chat header shows correct name
6. Click message input field
7. Paste message (set_clipboard + Cmd+V)
8. SCREENSHOT → verify text is in input field
9. Press Enter to send
10. SCREENSHOT → verify message appears as sent bubble
```

### After first success → save workflow:
```bash
python3 agent.py save_workflow --app AppName --name send_message --steps '[...]'
```

Next time, `agent.py send_message` will load the saved workflow.

## Waiting for Async UI Changes

When an action triggers a slow process (scan, download, loading):

```bash
python3 scripts/agent.py wait_for --app AppName --component ComponentName
```

- Template match polls every 10s (~0.3s/check), 120s timeout
- On success → returns coordinates, proceed
- On timeout → saves screenshot. **Do NOT blind-click** — inspect and decide
- Never use `sleep(60)` + blind click

## Post-Action Verify (after every action)

1. Screenshot again
2. Did the expected change happen?
3. Am I in the expected next state?
4. If NOT → re-observe and decide

## Web Form Input Quirks

- **Autocomplete fields** (e.g., station selectors): typing alone is NOT enough — must click the dropdown suggestion
- **Chinese input in web forms**: System IME interferes with autocomplete. Switch to English, type pinyin, let website autocomplete handle it
- **Cmd+V in web forms**: May garble text. Use `type_text("text")` for ASCII/pinyin
- **Date pickers**: Usually need calendar UI clicks, not typed dates
