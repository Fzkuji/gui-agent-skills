---
name: gui-observe
description: "Observe current screen state before any GUI action. Full-screen screenshot + visual analysis to identify app, page, state, and blocking dialogs."
---

# Observe — Know Before You Act

Before ANY GUI task, observe the current state. Do not assume anything from last time.

## Steps

1. **Record baseline** — call `session_status`, note context size for later reporting
2. **Take full-screen screenshot**:
   ```python
   from platform_input import screenshot
   screenshot("/tmp/observe.png")
   ```
3. **Analyze with `image` tool** — ask:
   - What app is in the foreground? (check menu bar)
   - Is the target app visible? Where is its window?
   - What page/state is the app in?
   - Any popups, dialogs, overlays blocking?
4. **Template match known components** to confirm state:
   ```python
   from app_memory import match_on_fullscreen
   found, x, y, conf = match_on_fullscreen('AppName', 'component_name')
   ```
5. **Decide**: proceed to act, or need to dismiss/navigate first?

## Coordinate System

- **Full-screen screenshot**: physical pixels (e.g., 3024x1964 on Retina 2x)
- **Logical screen**: physical ÷ 2 (e.g., 1512x982)
- **pynput/click_at**: uses logical screen coordinates
- **Template match**: `match_on_fullscreen` returns logical coordinates directly — use as-is
- **No window offset needed**: full-screen matching eliminates offset bugs

## Window Management

```python
from platform_input import activate_app, get_window_bounds

# Activate (bring to front)
activate_app("AppName")

# Get bounds (logical coords)
x, y, w, h = get_window_bounds("AppName")
```

osascript is allowed ONLY for read-only queries (bounds, frontmost check, URLs).
Never use osascript for clicking, typing, or any input.

## State Identification

1. Screenshot full screen
2. Analyze with `image` tool (understand what's on screen)
3. Template match known components to confirm state programmatically
4. Match against known page fingerprints if available

## Detection Stack

| Detector | Purpose | Speed |
|----------|---------|-------|
| **Template Match** (full screen) | Click coordinates for known components | 0.3s, conf ≈ 1.0 |
| **`image` tool** (vision model) | Understand what's on screen, verify state | ~2s |
| **GPA-GUI-Detector (YOLO)** | Discover unknown UI elements during learn | 0.3s |

**Key rule**: Template match → click coordinates. Image tool → understanding. Never the other way around.
