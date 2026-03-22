---
name: gui-act
description: "Execute GUI actions — click, type, send messages. Includes detection, memory matching, execution, state recording, and memory saving as one unified flow."
---

# Act — Detect, Match, Execute, Record, Save

This is the core action loop. **Detection, execution, and memory saving are ONE step, not separate steps.**
Every action follows this complete flow. Do not skip any part.

---

## The Complete Action Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DETECT: Screenshot → OCR + GPA-GUI-Detector             │
│ 2. MATCH:  Compare detected elements against saved memory   │
│            → Known components? Use template match directly  │
│            → New components? Continue with detection coords  │
│ 3. DECIDE: Which element to interact with                   │
│            → If all known from memory: skip image tool      │
│            → If uncertain: use image tool for understanding │
│ 4. EXECUTE: Click/type/interact at detected coordinates     │
│ 5. DETECT AGAIN: Screenshot → OCR + GPA-GUI-Detector       │
│ 6. DIFF:   Compare before vs after                          │
│            → Which components DISAPPEARED? (= old state)    │
│            → Which components APPEARED? (= new state)       │
│            → Which components stayed? (= persistent UI)     │
│ 7. SAVE:   Update memory with everything learned            │
│            → New components → crop + save + label            │
│            → State transition → record in profile.json      │
│            → Page screenshot → save to pages/               │
└─────────────────────────────────────────────────────────────┘
```

**This is ONE atomic operation. You do ALL 7 sub-steps every time you act. Not 1-4 then "maybe later" for 5-7.**

---

## Step 1: DETECT (before action)

Take a screenshot. Run detection on it:

```python
from scripts.ui_detector import detect_text, detect_icons

# OCR: get all text elements with coordinates
ocr_results = detect_text(screenshot_path)
# Returns: [{"label": "Travel info", "cx": 661, "cy": 188, "x": ..., "y": ..., "w": ..., "h": ...}, ...]

# GPA-GUI-Detector: get all UI components with coordinates
icon_results = detect_icons(screenshot_path)
# Returns: [{"cx": 849, "cy": 783, "x": ..., "y": ..., "w": ..., "h": ..., "confidence": 0.85, "label": null}, ...]
```

## Step 2: MATCH against saved memory

Before doing anything else, check if you already know these elements:

```python
from scripts.app_memory import load_profile, match_components

profile = load_profile(app_name)  # or app_name + site domain for websites
# Template match saved components against current screenshot
matched = match_components(app_name, screenshot_path)
# Returns: {"travel_info_btn": (661, 188, 0.95), "book_btn": (490, 283, 0.92), ...}
```

**If components match from memory:**
- You already know what they are (they have labels from previous saves)
- You already know their coordinates (from template matching)
- **Skip GPA-GUI-Detector** — template matching is more precise
- **Skip image tool** — you already know what everything is
- Go directly to Step 4 (EXECUTE)

**If components are NEW (not in memory):**
- GPA-GUI-Detector coordinates are your source
- Use image tool if needed to understand what the new elements are
- After execution, these will be saved with labels (Step 7)

## Step 3: DECIDE what to interact with

Based on detection + memory matching + (if needed) image tool understanding:
- Identify the target element
- Get its coordinates from: template match (preferred) > OCR > GPA-GUI-Detector
- **NEVER from image tool** (understanding only, no coordinates)

## Step 4: EXECUTE

```python
# For known components (template matched):
from scripts.app_memory import click_component
ok, msg = click_component(app_name, component_name)

# For dynamic/new elements (detected coordinates):
from scripts.app_memory import click_and_record
ok, msg, visible = click_and_record(app_name, "element_label", x, y)
```

**CRITICAL: Never use raw `click_at()` from platform_input directly.**
Always use `click_and_record()` or `click_component()` — these automatically handle state recording.

## Step 5: DETECT AGAIN (after action)

Take another screenshot. Run detection again:
```python
ocr_after = detect_text(screenshot_after_path)
icons_after = detect_icons(screenshot_after_path)
```

## Step 6: DIFF — Compare before vs after

This is how you understand what your action did:

```
Before click: components A, B, C, D visible
After click:  components A, B, E, F visible

→ DISAPPEARED: C, D  (these belong to the OLD state/page)
→ APPEARED: E, F     (these belong to the NEW state/page)
→ PERSISTED: A, B    (these are persistent UI — toolbar, nav bar, etc.)
```

This mapping tells you:
- **C, D are associated with the state BEFORE the click** — they're part of that page
- **E, F are associated with the state AFTER the click** — they're part of the new page
- **A, B are global/persistent** — they appear across states
- **The click created a TRANSITION**: state(A,B,C,D) → click(target) → state(A,B,E,F)

## Step 7: SAVE to memory

**Do this EVERY time. This is not optional.**

### 7a: Save new components
For any newly detected elements that aren't in memory yet:
- Crop the element from the screenshot (using bounding box from detection)
- Save to `components/<label>.png`
- Add to profile.json with: type, coordinates, confidence, label

### 7b: Label components
Give meaningful names to detected elements based on:
- OCR text (if the element has text → use the text as label)
- Visual understanding from image tool (if used in Step 3)
- Position/context ("top_nav_3rd_item", "booking_form_submit")

**Labeled components can be matched by template in future sessions without re-running GPA or image tool.**

### 7c: Record state transition
```json
{
  "from": "homepage",
  "click": "travel_info_menu",
  "to": "travel_info_dropdown",
  "appeared": ["baggage_link", "flight_status_link", "..."],
  "disappeared": ["promo_banner"],
  "timestamp": "2026-03-22T23:45:00"
}
```

### 7d: Save page screenshot
Save to `pages/<state_name>.png` for future reference.

### 7e: For browser websites
All of the above goes into `memory/apps/<browser>/sites/<domain>/`:
```
memory/apps/chromium/sites/united.com/
├── profile.json          # Updated with new components, states, transitions
├── components/           # Cropped UI element templates
│   ├── travel_info_menu.png
│   ├── baggage_link.png
│   └── ...
└── pages/
    ├── homepage.png
    └── travel_info_dropdown.png
```

---

## The Payoff: Why This Matters

After saving memory for a website/app:

**First visit to united.com:**
```
Screenshot → GPA-GUI-Detector (slow) → image tool "what is this?" (expensive)
→ click → save components with labels → save state transition
```

**Second visit to united.com:**
```
Screenshot → template match against saved components (fast, precise)
→ "I see travel_info_menu at (661, 188), baggage_link at (650, 250)"
→ click directly. No GPA. No image tool. No guessing.
```

**This is the entire point of the memory system.** If you don't save, every visit starts from scratch.

---

## How Coordinates Work

| Content type | Method | Precision |
|---|---|---|
| Saved component | Template matching (`click_component`) | Pixel-precise (conf≈1.0) |
| Dynamic content (menu, search result) | GPA-GUI-Detector/OCR detection (`click_and_record`) | Bbox-precise |
| Unknown element | Learn first, then template match | Pixel-precise |

**`image` tool = understanding only.** Never use it for coordinates.

## Not Found?

Component not matching (conf < 0.8) means it's **not on screen** in its saved form:
- Different visual state (selected vs unselected tab)
- Different page
- App not in foreground

**Don't lower the threshold.** Re-learn current state to discover what IS on screen.

## Input Methods (platform_input.py)

```python
click_at(x, y)                    # Left click
mouse_right_click(x, y)           # Right click (context menus)
paste_text("中文")                 # Clipboard + Cmd+V (CJK safe)
type_text("hello")                # Direct typing (ASCII only)
key_press("return")               # Single key
key_combo("command", "v")         # Key combination
set_clipboard("text")             # Set clipboard
get_clipboard()                   # Read clipboard
screenshot("/tmp/check.png")      # Full screen capture
```

## Sending Messages

No hardcoded flow. First time: follow steps manually with screenshot verification at each step. After success: save as workflow for replay.

Generic steps:
1. Find contact (search or scroll) — use GPA-GUI-Detector/OCR detection for coordinates
2. Verify chat header shows correct contact — `image` tool for understanding
3. Click input field — template match or GPA-GUI-Detector detection
4. Paste message — `paste_text()`
5. Verify text in input — `image` tool or `get_clipboard()`
6. Send — `key_press("return")`
7. Verify sent — `image` tool
