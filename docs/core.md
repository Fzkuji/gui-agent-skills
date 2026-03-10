# Core Principles & Tools

## Tools (fastest → slowest)

| Tool | Speed | Use for |
|------|-------|---------|
| AppleScript/JXA | ~0.1s | App focus, window info, menu clicks, AX element discovery |
| cliclick | instant | Mouse clicks (`c:x,y`), keyboard input (`t:text`), keys (`kp:return`) |
| OCR (`gui_agent.py find`) | ~1.6s | Find text on screen with coordinates |
| Template match | ~1.3s | Find known UI elements (learned from prior use) |
| Screenshot + vision model | ~5-10s | Complex layout understanding (last resort) |

## Principles

### 1. AX first, OCR second, screenshot last
- **AX (`entireContents`)**: Precise positions, roles, titles. Best for buttons, fields, links
- **OCR**: When AX can't see content (WebViews, custom renders)
- **Screenshot + vision**: Only when you can't determine state otherwise

### 2. Observe less, act more
```
BAD:  Screenshot → 1 action → Screenshot → 1 action
GOOD: AX scan → Plan 3-5 actions → Execute all → Verify once
```

### 3. Hide before interact
Prevents mis-clicks on overlapping windows:
```bash
osascript -e 'tell application "System Events" to set visible of every process whose name is not "TargetApp" to false'
```

## Hard-Won Lessons

### Focus Management (最重要)
- **Any app can steal focus at any time** — especially auth/SSO pop-ups
- `osascript keystroke` sends to **current focus**, not the app you intended
- **Never assume focus** — use `cliclick c:x,y` to click the target directly
- **Multi-app interaction**: finish the focus-stealing app first, then operate the passive one

### Coordinates
- **AX is the most reliable source**: `entireContents()` → find by role + title → position + size
- **Window moves invalidate coordinates** — always re-query AX before acting
- **cliclick only accepts integers**: use `Math.round(pos + size/2)`
- **Retina**: OCR pixels ÷ 2 = logical coords. AX already returns logical coords

### Text Input
- **Cmd+V paste > cliclick t:** — `cliclick t:` truncates on special characters (`!@#`)
- **For sensitive input**: copy to clipboard first, then Cmd+V into the field

### WebView Quirks
- `osascript keystroke` doesn't work inside WebViews
- `cliclick kp:return` may not trigger WebView buttons
- **Must use `cliclick c:x,y`** to click WebView buttons directly
- WebViews need load time — wait after navigation before interacting

### Debugging
- **Screenshot every step** when things go wrong: `/usr/sbin/screencapture -x path.png`
- **AX dump**: JXA `entireContents()` lists all elements with role/title/position
- **Never retry blindly** — observe current state first, then decide

## Common Code Snippets

### AX scan all elements
```javascript
// osascript -l JavaScript
var se = Application("System Events");
var w = se.processes["AppName"].windows[0];
var all = w.entireContents();
var result = [];
for (var i = 0; i < all.length; i++) {
    try {
        var r = all[i].role(), t = all[i].title() || "";
        var p = all[i].position(), s = all[i].size();
        result.push(r + ' "' + t + '" (' + p[0] + ',' + p[1] + ') ' + s[0] + 'x' + s[1]);
    } catch(e) {}
}
result.join("\n");
```

### Click AX button by name
```javascript
se.processes["AppName"].windows[0].buttons.byName("OK").click();
```

### Menu bar action
```javascript
var p = se.processes["AppName"];
p.menuBars[0].menuBarItems.byName("Edit").menus[0].menuItems.byName("Copy").click();
```

### Prerequisites
- macOS with Accessibility permissions
- `brew install cliclick`
- `pip install opencv-python-headless numpy`
- `/usr/sbin/screencapture` (full path required in headless environments)
