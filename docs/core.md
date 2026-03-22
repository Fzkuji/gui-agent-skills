# Core Principles & Lessons Learned

## 🔴 Vision vs Command — The #1 Rule

**Decision = Visual, Execution = Best Tool.**

Every action must be justified by what you observed on screen. Keyboard shortcuts are fine for execution, but the DECISION to act must come from visual observation (OCR, GPA-GUI-Detector, or image tool).

### Three Visual Methods

| Method | Returns | Coordinates? | Use for |
|--------|---------|-------------|---------|
| **OCR** (`detect_text`) | Text + bounding box | ✅ YES | Text elements (labels, links, menu items) |
| **GPA-GUI-Detector** (`detect_icons`) | Bounding box (no labels) | ✅ YES | Non-text elements (icons, buttons) |
| **image tool** (LLM vision) | Semantic understanding | ⛔ NEVER | Understanding the scene, deciding WHAT to click |

**Phase 1** (unfamiliar page): OCR + image tool + GPA-GUI-Detector → all three together
**Phase 2** (familiar page): OCR + GPA-GUI-Detector only → skip image tool, save tokens

## Tool Priority (fastest → slowest)

| Tool | Speed | Use for |
|------|-------|---------|
| **Template match** | ~0.3s | Known UI elements from memory (conf=1.0) |
| **pynput** | instant | Mouse clicks, keys, keyboard shortcuts |
| **Apple Vision OCR** | ~1.6s | Find text on screen (Chinese + English) |
| **GPA-GUI-Detector** | ~0.3s | General-purpose UI element detection (40MB) |
| **Screenshot + Vision** | ~5-10s | Last resort, send to LLM for analysis |

**Rule**: Always try cheaper methods first. Template match > OCR > GPA-GUI-Detector > image tool.

## Coordinate System

```
Screen (0,0) ──────────────────────────► x
│
│    Window (win_x, win_y)
│    ┌──────────────────┐
│    │  Component at     │
│    │  relative (rx,ry) │
│    │                   │
│    │  screen_x = win_x + rx
│    │  screen_y = win_y + ry
│    └──────────────────┘
│
▼ y
```

- **All memory stores relative coordinates** (relative to window top-left)
- **Convert to screen coords only at click time**
- **Retina**: screenshots are 2x physical pixels, divide by 2 for logical
- **cliclick uses logical screen pixels**, always integers

## Hard-Won Lessons

### Window Management
- **Don't hide other apps by default** — only hide if click fails (retry strategy)
- **Read-only operations don't need hide** — read_messages, scroll_history just activate
- **Activate app before any operation** — never assume focus
- **Window might have moved** — always get fresh bounds before converting coords
- **CRITICAL: OCR/click must be within target window bounds** — NEVER click coordinates outside the target app's window. OCR results from other visible windows will cause mis-clicks (e.g., sending message to Discord instead of WeChat). Always filter OCR results by window bounds.
- **Known bug**: searching for a contact name may match text in OTHER apps' windows if they're visible behind the target app. FIX: capture ONLY the target window screenshot (screencapture -l), not fullscreen

### Input
- **NEVER type directly through IME** — always use clipboard paste (pbcopy + Cmd+V or paste_text()). Direct typing through system IME produces garbled text when Chinese input method is active. Paste bypasses IME completely.
- **Set LANG=en_US.UTF-8** before paste — CJK garbles without it
- **Click input field before typing** — never assume cursor is in the right place
- **Enter sends in WeChat** — NOT Cmd+Enter

### WeChat Specific
- **Cmd+F opens web search (搜一搜)** — NOT contact search. Use sidebar click or search bar template
- **Re-clicking selected chat does nothing** — click away first, then back
- **Input field placeholder invisible to OCR** — use window_calc positioning
- **Only 4 AX elements** — must use GPA-GUI-Detector+OCR for everything
- **Left sidebar icons are gray-on-gray** — only GPA-GUI-Detector can detect them (OmniParser fails)

### Detection
- **Salesforce/GPA-GUI-Detector > OmniParser** for desktop apps (40MB vs 41MB, same architecture, better training data)
- **Apple Vision OCR > EasyOCR** for Chinese (EasyOCR produces garbled output for Chinese)
- **AX is perfect for Dock/menubar** — don't waste time on CV for those
- **Electron apps (Discord, Cursor) have huge AX trees** — filter by region, don't scan everything

### Window Capture & Coordinate Conversion
- **Window crop from fullscreen**: retina fullscreen crop → coordinates are retina pixels (2x)
- **OCR on cropped window**: returns retina pixel coords within the crop
- **Convert to screen**: screen_x = win_x + retina_x ÷ 2, screen_y = win_y + retina_y ÷ 2
- **BUT**: OCR on the non-resized fullscreen returns screen logical coords directly — simpler!
- **Best approach**: activate window → fullscreen screenshot → OCR → filter results by window bounds
- **DO NOT** hardcode button positions (y>700) — use window-relative percentages (cy > win_h * 0.7)
- **EXPLORE before acting**: when unsure of state, crop window screenshot and use vision model to look at it

### Status Bar / Menu Bar / Floating Windows
- **Status bar icons**: Use AppleScript `click menu bar item 1 of menu bar 2 of process "AppName"` — NOT screenshot+GPA-GUI-Detector
- **Menu items**: Navigate by name: `click menu item "Switch Profile" of menu 1 of ...`
- **Sub-menus**: `click menu item "MESL" of menu 1 of menu item "Switch Profile" of ...`
- **Check active item**: `value of attribute "AXMenuItemMarkChar"` returns checkmark
- **Floating windows/popups**: Appear temporarily — screenshot fast before they disappear, or use AppleScript if available

### Remote Server Management (JupyterLab)
- **nvitop** is usually already running in one of the terminal tabs — don't create new notebooks/terminals unnecessarily, look for existing ones first
- JupyterLab has multiple terminal tabs — check ALL tabs before creating new ones
- To run shell commands in Jupyter Notebook: prefix with `!` (e.g., `!nvidia-smi`)
- IME interferes with `!` prefix — use pbcopy paste instead of typing

### Browser / Web Forms
- **Autocomplete inputs (12306, Google, etc.)**: MUST click dropdown suggestion, typing text alone doesn't count
- **Chinese in browser forms**: System IME interferes. Switch to English input, type pinyin abbreviation, let WEBSITE autocomplete handle it
- **Cmd+V in web forms**: May produce garbled text. Use `cliclick t:pinyin` + website autocomplete instead
- **Date pickers**: Click the calendar UI, don't just type date strings
- **URL parameters**: May fill text visually but NOT trigger selection events. Still need to click dropdown items

### Safety
- **Always verify contact before sending** — OCR the chat header
- **Check click target is within window bounds** — prevents clicking wrong app
- **Confidence threshold 0.7** — don't click if template match is too low
- **Don't impersonate user in private chats** — act as AI, not as the user

### Memory Management
- **NEVER auto-learn from wrong-app clicks** — if OCR matched text in Discord but you were supposed to be in WeChat, that learned template is WRONG. Validate the match is in the correct app window before auto-learning.
- **Minimum template size** — templates smaller than 30×30 pixels are too small and will produce false matches everywhere. Don't save them.
- **Icon filename = content description** — `search_bar.png`, NOT `icon_0_170.png`
- **Dedup before saving** — similarity > 0.92 = duplicate, skip it
- **Auto-cleanup dynamic content** — timestamps, message previews, stickers
- **~20-30 components per page** — if you have 60+, you saved too much junk
- **Memory is per-machine** — gitignored, each machine learns its own UI
- **NEVER commit memory/, detected/, templates/ to git** — contains personal screenshots, chat content, contact names. If accidentally committed, use `git filter-branch` to purge from ALL history, then force push


| App | AX Elements | Framework | Notes |
|-----|-------------|-----------|-------|
| Discord | ~1900 | Electron/Chromium | Full AX, sidebar servers have names |
| Chrome | ~1400 | Chromium | Full AX |
| System Settings | ~500 | SwiftUI/AppKit | Full AX, native best |
| Outlook | Very many | Electron | Full AX but slow to scan |
| Cursor | Very many | Electron (VS Code) | Full AX but slow to scan |
| **WeChat** | **4** | Custom engine | Only window buttons, need GPA-GUI-Detector+OCR |
| Telegram | Unknown | Custom | Needs testing |
| Dock | Full | System | Always has names + positions |
| Menu bar | Full | System | Always has names + positions |
| Status bar | Full | System | Each app's tray icon accessible |

### LLM Role: Decision Only, Never Coordinates
- **LLM decides WHAT to click** (which component/button name) — never WHERE (coordinates)
- **Coordinates ALWAYS come from detection tools**: OCR, GPA-GUI-Detector, template match
- **LLM never writes coordinates directly** — not in code, not in commands, not anywhere
- **Correct**: LLM → "click Force Quit" → OCR/GPA-GUI-Detector/template finds coordinates → click
- **Wrong**: LLM → "click at (719, 534)" → miss

### OCR Text Matching Pitfalls
- **Substring matching is dangerous**: searching "Scan" also matches "Deep Scan", "Smart Scan", "Scanner"
- **Always use exact or contextual matching**: check if matched text IS the button, not just contains the keyword
- **Position filtering alone is not enough**: "Deep Scan" label and "Scan" button may both be in the bottom 40% of the window
- **Solution**: match exact text first, filter by position second. Or use template match for known buttons.

### Coordinate Conversion (VERIFIED CORRECT)
- **Window crop OCR**: retina coords → ÷2 = logical window-relative → + window position = screen coords
  - Example: retina(1289,1229) → logical(644,614) → screen(855,802) ✅
- **Resized fullscreen OCR** (sips -z 982 1512): output coords ARE screen logical coords directly
  - Example: (855,801) ✅
- **Both methods give same result** (±1px)
- The previous "coordinate bug" was actually an **OCR text matching bug** (matched "Deep Scan" instead of "Scan" button)

### Memory Saving (CRITICAL — most commonly skipped step)
- **Save after EVERY action** — not as a separate step, but as part of the action itself
- **ACT = detect → match → execute → detect again → diff → save** — all 7 sub-steps, every time
- **Browser websites need per-site memory**: `memory/apps/chromium/sites/united.com/` with the same structure as any app (profile.json + components/ + pages/)
- **Label components when saving** — OCR text → use as label; unlabeled → use image tool to identify
- **The payoff**: first visit needs GPA + image tool (slow, expensive). Second visit uses template match only (fast, free)
- **If you skip saving, every visit starts from scratch** — this defeats the entire purpose of the memory system
- **"I'll save it later" = never** — memory saving was a separate STEP 3 and it was ALWAYS skipped. Now it's built into ACT.

### Skill Reading vs Skill Following
- **Reading SKILL.md ≠ following SKILL.md** — LLM reads rules then ignores them during execution
- **Writing ABSOLUTE RULES doesn't help** — the same mistakes recur across sessions
- **Merging steps helps** — separate "save memory" step was always skipped; merging it into "act" makes it harder to skip
- **Specific > vague** — "save to memory" is vague; "crop component, save template, update profile.json, record transition" is actionable
