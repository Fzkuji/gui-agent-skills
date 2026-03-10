---
name: gui-agent
description: "Control desktop GUI applications (WeChat, browsers, any macOS app) efficiently using batch action planning. Use when asked to operate, click, type, send messages, or interact with any desktop application on the host machine. NOT for web-only tasks that the browser tool handles natively, or simple file operations."
---

# GUI Agent — Adaptive Desktop Automation

## Architecture

Two-layer system: **fast atomic tools** at the bottom, **LLM decision-making** on top.

```
┌─────────────────────────────┐
│   LLM (you, the assistant)  │  Observe → Decide → Act → Verify
│   Natural language goals     │  Adapts to unexpected states
├─────────────────────────────┤
│   gui_agent.py              │  Structured observation + execution
│   template_match.py         │  Fast element location (~1.3s)
├─────────────────────────────┤
│   AppleScript │ OCR │ cliclick │ Vision model
│   (~0.1s)     │(~1.6s)│ (instant)│ (~5-10s)
└─────────────────────────────┘
```

**You ARE the agent loop.** Don't follow rigid scripts. Look at the screen, decide what to do, do it, verify with the lightest method possible.

---

## Quick Start: How to Use

### 1. Observe the screen state
```bash
source ~/scrapling-env/bin/activate
python3 scripts/gui_agent.py observe --app WeChat
```
Returns: frontmost app, window bounds, sidebar/main text content.

### 2. Execute an action
```bash
python3 scripts/gui_agent.py exec '{"action": "click_ocr", "text": "宋文涛", "region": {"x_max": 430}}'
```

### 3. Verify (choose the lightest method)
```bash
# Level 1 (~0.1s): AppleScript check
python3 scripts/gui_agent.py exec '{"action": "focus_app", "app": "WeChat", "verify": {"method": "app_focused", "app": "WeChat"}}'

# Level 2 (~1.3s): Template check
python3 scripts/gui_agent.py exec '{"action": "click_template", "app": "WeChat", "name": "search_bar"}'

# Level 3 (~1.6s): OCR spot check
python3 scripts/gui_agent.py find "宋文涛"

# Level 4 (~5-10s): Screenshot + vision model (LAST RESORT)
# Only when above methods can't determine success
```

### 4. Run a task (highest level — app-agnostic)
```bash
# Send message — same command, any app
gui_agent.py task send_message --app WeChat   --param contact="宋文涛" --param message="hi"
gui_agent.py task send_message --app Discord  --param contact="general" --param message="hi"
gui_agent.py task send_message --app Telegram --param contact="John"    --param message="hi"

# Read current/specified chat
gui_agent.py task read_messages --app WeChat --param contact="宋文涛"

# Scroll up to read older messages (default 3 pages)
gui_agent.py task scroll_history --app WeChat --param contact="宋文涛" --param pages="5"

# List all tasks
gui_agent.py tasks
```

### 5. Available atomic actions (mid level — LLM decides)
```json
{"action": "focus_app", "app": "WeChat"}
{"action": "hide_others", "keep": "WeChat"}
{"action": "click_ocr", "text": "keyword", "region": {"x_max": 430}}
{"action": "click_template", "app": "WeChat", "name": "search_bar"}
{"action": "click_pos", "x": 728, "y": 711}
{"action": "click_window", "app": "WeChat", "sidebar_width": 250, "bottom_offset": 80}
{"action": "type", "text": "hello"}
{"action": "key", "key": "return"}
{"action": "shortcut", "key": "a", "modifiers": ["command"]}
{"action": "delay", "seconds": 0.5}
```

---

## Verification Hierarchy (IMPORTANT)

**Always verify with the lightest method that works. Only escalate when needed.**

| Level | Method | Speed | When to use |
|-------|--------|-------|-------------|
| 1 | AppleScript | ~0.1s | App focused? Window title changed? |
| 2 | Template match | ~1.3s | Known element appeared/disappeared? |
| 3 | OCR spot check | ~1.6s | Specific text visible? Text gone (input cleared)? |
| 4 | Screenshot + vision | ~5-10s | Complex layout, nothing else works |

**Examples:**
- After `focus_app` → Level 1: check frontmost app (0.1s)
- After clicking contact → Level 3: OCR check for chat messages (1.6s)
- After pressing Enter to send → Level 3: check input field empty (1.6s)
- After complex navigation → Level 4: screenshot to understand layout (5-10s)

---

## Core Principles

### 1. You ARE the decision maker
Don't blindly follow workflows. If a step fails or the screen looks wrong, adapt:
- Try an alternative approach
- Skip unnecessary steps (e.g., chat already open)
- Add recovery steps (e.g., press Escape, click elsewhere first)

### 2. Observe less, act more
```
BAD:  Screenshot → 1 action → Screenshot → 1 action → Screenshot ...
GOOD: Screenshot → Plan 3-5 actions → Execute all → Verify once
```

### 3. Hide before interact
**Always** hide other apps before GUI automation to prevent window overlap mis-clicks:
```json
{"action": "hide_others", "keep": "TargetApp"}
```

### 4. Restore after done
Re-show hidden apps when finished.

### 5. Pre-existing workflows are hints, not rules
JSON workflows in `workflows/` are "happy path" recipes. Use them as starting points, but override any step that doesn't match the current screen state.

---

## Prerequisites

### Tools
- `exec`, `read`, `write` tools must be available (OpenClaw `tools.profile: "full"`)
- `cliclick`: `brew install cliclick`
- Python venv: `~/scrapling-env/` (opencv-python-headless, numpy)

### Permissions
**Try first, handle denial gracefully.** Don't pre-configure.
- If cliclick/osascript fails with permission error → macOS shows a dialog
- Tell user: "Click Allow in the Accessibility dialog, then I'll retry"
- **Screen Recording** (for `screencapture`): Required by macOS. If `screencapture` returns "could not create image from display", the running process needs Screen Recording permission in **System Settings → Privacy & Security → Screen Recording**.

### PATH Issues (headless / OpenClaw environments)
macOS CLI tools like `screencapture` live in `/usr/sbin/` which may not be in PATH for background services (e.g., OpenClaw gateway, launchd agents). All scripts in this skill use the full path `/usr/sbin/screencapture` to avoid this. If you add new scripts that call `screencapture`, always use the absolute path.

### Locale (CRITICAL for CJK)
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```
Without this, Chinese text gets garbled during paste. Set in every exec call.

---

## Battle-Tested Lessons (2026-03-10)

Real failures from automating GlobalProtect VPN + 1Password. These apply to **any** multi-app GUI automation.

### 1. Focus Theft is the #1 Enemy
- **Any app can steal focus at any time.** GP SSO pops a WebView window mid-flow; macOS auth dialogs appear; apps auto-activate.
- **`osascript keystroke` goes to the focused window**, not the window you think. If GP steals focus while you're "typing" into 1Password, you just typed your search query into the GP password field.
- **Rule: Never use `keystroke` for anything important.** Use `cliclick c:x,y` to explicitly click where you need, then `cliclick t:` or Cmd+V to input.
- **Do the focus-stealing app first.** Complete all GP steps (Connect → Next → wait for password page) *before* touching 1Password.

### 2. Coordinate Discipline
- **AX is the single source of truth for coordinates.** Don't estimate from screenshots.
- **`cliclick` requires integer coordinates.** AX returns floats from `position + size/2`. Always `Math.round()`.
- **Coordinates change when windows move.** If you moved a window (intentionally or not), re-query AX before clicking.
- **Use center of element**: `x = pos[0] + size[0]/2`, `y = pos[1] + size[1]/2`.

### 3. Clipboard is Fragile
- **1Password clears clipboard after 90 seconds.** Copy password as the *last step before pasting*, not at the beginning.
- **Verify clipboard immediately**: `pbpaste | wc -c` — if 0, it's been cleared.
- **Don't assume clipboard contents.** Other apps or system events can overwrite it.

### 4. Identity Verification for Credentials
- **Search results can have multiple similar entries.** "CityU" in 1Password returned: a login (correct), a credit card (wrong), and Underline with a cityu email (wrong, 19 chars).
- **Always verify**: check the right panel for username + website + password strength before copying.
- **Password length is a good sanity check.** If you expected 11 chars and got 19, you have the wrong entry.

### 5. WebView Inputs are Special
- **`osascript keystroke` doesn't work in WebViews** (GP, Electron apps).
- **`cliclick kp:return` doesn't click buttons in WebViews.** Must use `cliclick c:x,y` on the actual button.
- **`cliclick t:` truncates on special characters.** Cmd+V paste is more reliable for passwords.
- **WebViews load slowly.** After clicking "Next", wait 3-5 seconds for the password page to render and AX elements to appear.

### 6. Debugging: Screenshot Every Step
- `/usr/sbin/screencapture -x path.png` + vision model analysis — this is your "eyes"
- **Don't retry blindly.** Screenshot first, understand current state, then decide next action.
- **AX state check is faster than screenshot** for confirming element existence: `entireContents` → find role/title.

### 7. Timeout-Sensitive Flows
- SSO pages expire. GP gives ~60-90 seconds before "Unable to sign in" appears.
- **Plan the entire flow before starting.** Know every coordinate and action sequence.
- **Single-script execution is fastest.** Avoid round-trips between shell calls when timing matters.

---

## Platform Notes (macOS)

### Coordinate System
- OCR: bottom-left origin, normalized 0-1
- Screen: top-left origin, logical pixels
- Retina: physical ÷ 2 = logical (e.g., 3024×1964 → 1512×982)
- `gui_agent.py` OCR already returns logical pixel coordinates

### Dangerous Operations
| Operation | Risk | When OK |
|-----------|------|---------|
| Cmd+A | Selects ALL | Only in confirmed input fields |
| Cmd+Delete | Deletes files | Never in Finder |
| Cmd+W | Closes window | When you're sure which window |
| Cmd+Q | Quits app | Verify app first |

---

## Exploring a New App

When you encounter an app for the first time, **explore before automating**:

### 1. Quick Recon (~30 seconds)
```bash
# What does the app look like?
gui_agent.py observe --app AppName

# What's the AX tree? (accessibility elements)
osascript -l JavaScript -e '
var se = Application("System Events");
var p = se.processes["AppName"];
var w = p.windows[0];
// List top-level children with class, name, position
var result = [];
function scan(elem, depth) {
    if (depth > 3) return;
    try {
        var cls = elem.class();
        var nm = elem.name();
        var pos = elem.position();
        var sz = elem.size();
        result.push("  ".repeat(depth) + cls + ": " + nm + " @" + pos[0]+","+pos[1] + " " + sz[0]+"x"+sz[1]);
    } catch(e) {}
    try {
        var ch = elem.uiElements();
        for (var i=0; i<ch.length; i++) scan(ch[i], depth+1);
    } catch(e) {}
}
scan(w, 0);
result.join("\n");
'

# What text is visible? (OCR scan)
gui_agent.py find "some keyword"
```

### 2. Document What You Find
Create `apps/appname.json` with:
- Window position & size
- Key UI regions (sidebar, main area, input fields)
- Which approach works: AX (buttons/fields), OCR (text), or coordinates
- Quirks (WebView inputs, non-standard panels, auto-lock behavior)

### 3. Build a Minimal Workflow
Start with the simplest flow. Test each step individually:
```
Observe → single action → verify → next action
```
Once stable, batch actions for speed.

### 4. Coordinate Gotchas
- **OCR coordinates** may differ from **AX/cliclick logical coordinates** depending on display scaling
- Always verify by: AX `position()` → cliclick click → screenshot → confirm
- On Retina displays: check if OCR returns physical/2 or logical pixels
- When in doubt, use AX `position()` + `size()` to get the center point of elements

### 5. Privacy
- **Never commit passwords, tokens, or personal data** to app profiles or skill files
- Reference TOOLS.md or environment variables for sensitive values
- App profiles should describe *how* to get credentials, not *what* they are

---

## App Profiles

App-specific configs live in `apps/*.json`. List them:
```bash
gui_agent.py apps
```

Each profile defines: layout (sidebar width, input position), navigation (sidebar click vs search), input method (OCR vs window_calc), send key, and quirks.

**Adding a new app**: Create `apps/appname.json` with the same structure. The generic tasks work automatically — no code changes needed.

### WeChat (`apps/wechat.json`)
- **Accessibility API**: Useless (5 elements). Use OCR + templates.
- **Input field**: OCR can't see placeholder (too faint). Uses `window_calc`.
- **Send**: Enter (not Cmd+Enter).
- **Search**: Template `search_bar` available. Search results need filtering (skip Q-prefix suggestions, skip y<220 search box text).
- **Chat already selected bug**: Re-clicking highlighted chat doesn't reopen. Tasks handle this with click-away-and-back retry.
- **Don't use Cmd+F**: Opens web search ("搜一搜"), not contact search.
- **Scrolling history**: Page Up works in chat area. End key returns to bottom.

### Discord (`apps/discord.json`)
- **Accessibility API**: Excellent (1362 elements).
- **Search**: Cmd+K opens quick switcher.
- **Input**: OCR can find "Message #channel-name" placeholder.
- **Send**: Enter.

### Telegram (`apps/telegram.json`)
- **Search**: Cmd+F works well.
- **Input**: OCR can find "Write a message" placeholder.
- **Send**: Enter (configurable).

### GlobalProtect (`apps/globalprotect.json`)
- **Type**: System tray app (menu bar, not standard window).
- **AX**: Panel from menu bar click often has no children. Quit+reopen to get real window.
- **Password input**: WebView — must use `cliclick`, not `osascript keystroke`.
- **States**: Disconnected → Connect → SSO Sign In → Password → Connected.
- **Key quirk**: If "Disconnect" button exists, VPN is connected even if login window is still open.

---

## File Structure
```
skills/gui-agent/
├── SKILL.md                          # This file
├── apps/                             # App profiles (layout, nav, input, send)
│   ├── wechat.json
│   ├── discord.json
│   └── telegram.json
├── scripts/
│   ├── gui_agent.py                  # Main agent (observe/exec/task/find)
│   ├── template_match.py             # Template matching (save/find/click)
│   └── workflow_runner.py            # JSON workflow executor (legacy)
├── templates/
│   └── WeChat/                       # Saved templates + index.json
└── workflows/                        # Legacy JSON workflows
    └── wechat_send_message.json
```

---

*Last updated: 2026-03-10*
