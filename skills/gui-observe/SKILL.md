---
name: gui-observe
description: "Observe current screen state before any GUI action."
---

# Observe — Know Before You Act

## Three Visual Methods (see main SKILL.md for full details)

| Method | Returns | Coordinates? |
|--------|---------|-------------|
| **OCR** (`detect_text`) | Text + bounding box | ✅ YES |
| **GPA-GUI-Detector** (`detect_icons`) | UI components + bounding box | ✅ YES (no labels) |
| **image tool** | Semantic understanding | ⛔ NEVER |

## Phase 1: First encounter / unfamiliar page (DEFAULT)

1. Take screenshot
2. Run OCR (`detect_text`) → read all text + get coordinates
3. Send screenshot to image tool → understand layout and semantics (⛔ no coordinates from this)
4. Run GPA-GUI-Detector (`detect_icons`) → detect all UI components + coordinates
5. Combine all three to understand current state

## Phase 2: Familiar page (OPTIMIZATION)

1. Take screenshot (but don't send to image tool)
2. Run OCR + GPA-GUI-Detector → get text + coordinates as structured text
3. LLM reads text output directly → decide without visual analysis
4. If uncertain → fall back to Phase 1

## For known apps with saved memory

Use template matching instead of full detection:

1. `_detect_visible_components()` → which saved components are on screen
2. `identify_state_by_components()` → which known state matches
3. If state is known → proceed with `click_component` (no GPA-GUI-Detector needed)
4. If state is unknown → Phase 1 (full observation)

## Coordinate System

- **Screen**: 1512×982 logical pixels (Retina 2x → 3024×1964 physical)
- **Templates**: saved in physical pixels (from full-screen screenshot)
- **Matching**: full-screen template match → physical center ÷ 2 = logical coords
- **Clicking**: logical coordinates via `platform_input.click_at(x, y)`
- **Window validation**: match position checked against `get_window_bounds()` to reject other apps
- **Remote VMs (OSWorld)**: 1920×1080 (no Retina), coordinates are 1:1

## State Detection

States are identified by which components are visible (F1 score matching):
```python
from app_memory import identify_state_by_components, _detect_visible_components
visible = _detect_visible_components(app_name)
state, f1 = identify_state_by_components(app_name, visible)
```
