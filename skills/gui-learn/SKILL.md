---
name: gui-learn
description: "Learn a new app's UI — detect all components, identify, filter, save to visual memory. Run before operating any app not yet in memory."
---

# Learn — Build Visual Memory

Learning detects and saves all UI components for future template matching. Run this whenever:
- App not in `memory/apps/<appname>/` → full learn
- New page/state in known app → `learn --page <pagename>`
- Match rate < 80% on eval → incremental re-learn

## Command

```bash
python3 scripts/agent.py learn --app AppName
```

## What Happens

```
1. Activate app, ensure window ≥ 800x600
2. agent.py runs learn:
   a. Takes full-screen screenshot, crops window region
   b. Runs GPA-GUI-Detector (YOLO) → icons, buttons, UI elements
   c. Merges results with IoU dedup
   d. Crops each element → saves to memory/apps/<appname>/components/
   e. Reports unlabeled icons
3. YOU identify all components:
   a. Use `image` tool to view each cropped image (**one at a time** for accuracy)
   b. For each: read text, describe icon, determine actual name
   c. Only label GENERIC UI components (buttons, icons, tabs, nav)
   d. DELETE temporary/dynamic content (to prevent storage bloat)
   e. Verify _find_nearest_text names (often wrong in dense UIs)
   f. Rename: app_memory.py rename --old X --new Y
4. After identification + task complete:
   a. Run: agent.py cleanup --app AppName
   b. Remove dynamic content (timestamps, message previews)
   c. Keep all stable UI elements (no privacy filtering needed — data stays local)
5. Result: ~20-30 named, fixed UI components per page
```

**Important**: Components are cropped from full-screen screenshots so they match
perfectly when doing full-screen template matching later. This is why `capture_window`
uses screencapture (full screen) + crop, NOT `screencapture -l <windowID>`.

`_find_nearest_text` is a hint, not truth — always verify by viewing the cropped image.

## Component Filtering

Only save **stable UI elements** — things that look the same next session:

**SAVE** (stable):
- Sidebar elements (left ~15% of window)
- Toolbar elements (top ~12%)
- Footer elements (bottom ~12%)
- Any element with OCR text label

**SKIP** (dynamic):
- Tiny elements (< 25×25 pixels)
- Content area icons without labels
- Temporary content that changes every session

**Naming**:
- Has OCR label → label as filename (`Search.png`, `Settings.png`)
- No label + stable region → `unlabeled_<region>_<x>_<y>.png`
- No label + content area → SKIP

## What to KEEP vs REMOVE

**Golden rule**: only save things that look the same next time you open the app.

**KEEP**: sidebar nav icons, toolbar buttons, input controls, window controls, tab headers, fixed logos

**REMOVE**: chat messages, timestamps, user avatars in lists, notification badges, contact names, web content, text >15 chars in content area, profile pictures

**Quick test**: "Same place, same appearance tomorrow?" → KEEP. Otherwise → REMOVE.

## Post-Learn Checklist

- [ ] No `unlabeled_` files remain
- [ ] No timestamps, message previews, or chat content
- [ ] Each filename describes what it IS
- [ ] No duplicates
- [ ] ~20-30 components per page

## Ensure App Ready (Eval Logic)

```
Task arrives → ensure_app_ready(app, workflow)
  │
  ├── Never learned? → full learn
  ├── Known app, new page? → learn --page <name>
  └── Known app, known page → template match:
        ├── ≥ 80% → proceed
        └── < 80% → incremental learn
```

For memory rules, naming, dedup, privacy, and browser per-site memory → see `skills/gui-memory/SKILL.md`.
