"""
GUI Agent Functions — 6 core + sub-functions for desktop automation.

Architecture (two-layer Session design):

    Programmer Session (orchestrator):
      - Knows the overall task and all prior function results
      - Only sees I/O summaries — never execution details
      - Decides what to call next

    Worker Sessions (one per function call):
      - Each high-level function creates its own Session
      - Has full context: OCR data, screenshots, detection results
      - Destroyed after function returns — only the result survives

    ┌─────────────────────────────────────────────────┐
    │ Programmer Session                               │
    │ "observe returned: Discord, #常规, target found" │
    │ "act returned: clicked login, success=true"      │
    │ → grows slowly (only summaries)                  │
    └──────────┬──────────────────────┬────────────────┘
               │                      │
    ┌──────────▼──────────┐ ┌────────▼─────────────┐
    │ observe Worker      │ │ act Worker            │
    │ (own Session)       │ │ (own Session)         │
    │ Full OCR data       │ │ Full OCR + templates  │
    │ 156 elements        │ │ Coordinate matching   │
    │ Screenshot attached │ │ Click execution       │
    │ → destroyed after   │ │ → destroyed after     │
    └─────────────────────┘ └──────────────────────┘

    Low-level functions (Python deterministic):
        screenshot, ocr, detect, template_match, click, type_text, ...
        No Session needed. Pure Python.

Usage:
    # Option 1: With Programmer Session (full orchestration)
    programmer = ClaudeCodeSession(model="sonnet")
    result = observe(programmer, task="find login button")
    # programmer now knows the result summary
    # observe's worker Session is gone

    # Option 2: Without Programmer (standalone, uses its own Session)
    result = observe(None, task="find login button", worker_model="haiku")
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# Setup paths
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Framework import (bundled in-repo, no external dependency)
_harness_path = str(SKILL_DIR)
if _harness_path not in sys.path:
    sys.path.insert(0, _harness_path)
from harness import function, Session


# ═══════════════════════════════════════════
# Worker Session factory
# ═══════════════════════════════════════════

# Default worker model (can be overridden)
DEFAULT_WORKER_MODEL = "sonnet"


def _create_worker(model: str = None) -> Session:
    """Create a fresh worker Session for a single function execution.
    Destroyed after the function returns — only the result survives."""
    from harness.session import ClaudeCodeSession
    return ClaudeCodeSession(model=model or DEFAULT_WORKER_MODEL, max_turns=1)


def _report_to_programmer(programmer: Session, function_name: str, result: BaseModel):
    """Report function result summary to the Programmer Session.
    This is how the Programmer learns what happened without seeing details."""
    if programmer is not None:
        summary = f"[{function_name}] returned: {result.model_dump_json()}"
        # Don't send as a question — just inform
        programmer.send(f"Function result:\n{summary}\n\nAcknowledge with 'ok'.")


# ═══════════════════════════════════════════
# Return types
# ═══════════════════════════════════════════

class ScreenshotResult(BaseModel):
    path: str
    width: int = 0
    height: int = 0

class OCRResult(BaseModel):
    texts: list[dict]      # [{label, cx, cy, x, y, w, h}, ...]
    count: int

class DetectResult(BaseModel):
    elements: list[dict]   # [{cx, cy, x, y, w, h, confidence, label}, ...]
    count: int

class DetectAllResult(BaseModel):
    """Combined detection: OCR + GPA-GUI-Detector + (optional) Accessibility."""
    elements: list[dict]   # merged elements in click-space coordinates
    count: int
    screenshot_path: str
    screen_info: dict      # {detect_w, detect_h, click_w, click_h, scale_x, scale_y}

class TemplateMatchResult(BaseModel):
    matched: list[dict]    # [{name, cx, cy, confidence}, ...]
    count: int

class StateResult(BaseModel):
    state_name: Optional[str] = None
    confidence: float = 0.0
    visible_components: list[str] = []

class ObserveResult(BaseModel):
    app_name: str
    page_description: str
    visible_text: list[str]
    interactive_elements: list[str]
    state_name: Optional[str] = None
    state_confidence: Optional[float] = None
    target_visible: bool = False
    target_location: Optional[dict] = None
    screenshot_path: Optional[str] = None

class LearnResult(BaseModel):
    app_name: str
    components_found: int
    components_saved: int
    component_names: list[str]
    page_name: str
    already_known: bool = False

class ActResult(BaseModel):
    action: str
    target: str
    coordinates: Optional[dict] = None
    success: bool
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    screen_changed: bool = False
    error: Optional[str] = None

class RememberResult(BaseModel):
    operation: str
    app_name: str
    details: str

class NavigateResult(BaseModel):
    start_state: str
    target_state: str
    path: list[str]
    steps_taken: int
    reached_target: bool
    current_state: str

class VerifyResult(BaseModel):
    expected: str
    actual: str
    verified: bool
    evidence: str
    screenshot_path: Optional[str] = None


# ═══════════════════════════════════════════
# Low-level functions (deterministic, no LLM)
# ═══════════════════════════════════════════

def take_screenshot(app_name: str = None, fullscreen: bool = True) -> ScreenshotResult:
    """Take a screenshot. Returns path and dimensions."""
    from platform_input import screenshot as _screenshot, capture_window
    import cv2

    if app_name and not fullscreen:
        path = capture_window(app_name)
    else:
        path = _screenshot()

    if path and Path(path).exists():
        img = cv2.imread(path)
        h, w = img.shape[:2] if img is not None else (0, 0)
        return ScreenshotResult(path=path, width=w, height=h)

    return ScreenshotResult(path=path or "/tmp/gui_agent_screen.png")


def run_ocr(image_path: str) -> OCRResult:
    """Run Apple Vision OCR on an image. Returns text elements with coordinates."""
    from ui_detector import detect_text
    texts = detect_text(image_path)
    return OCRResult(texts=texts, count=len(texts))


def run_detector(image_path: str, conf: float = 0.1) -> DetectResult:
    """Run GPA-GUI-Detector on an image. Returns UI elements with bounding boxes."""
    from ui_detector import detect_icons
    # detect_icons returns (elements, img_w, img_h)
    elements, img_w, img_h = detect_icons(image_path, conf=conf)
    return DetectResult(elements=elements, count=len(elements))


def detect_all(image_path: str, conf: float = 0.1) -> DetectAllResult:
    """Run full detection pipeline: OCR + GPA-GUI-Detector + merge.
    Returns all elements in click-space coordinates.
    Gracefully degrades if detector is unavailable (OCR-only mode)."""
    try:
        from ui_detector import detect_all as _detect_all, get_screen_info
        # detect_all returns (icons, texts, merged, img_w, img_h)
        icons, texts, merged, img_w, img_h = _detect_all(image_path, conf=conf)
        info = get_screen_info()
        elements = merged  # merged list contains all elements in click-space
    except (ImportError, Exception):
        # Fallback: OCR-only
        ocr = run_ocr(image_path)
        elements = ocr.texts
        info = {}
    return DetectAllResult(
        elements=elements,
        count=len(elements),
        screenshot_path=image_path,
        screen_info=info,
    )


def template_match(app_name: str, image_path: str = None) -> TemplateMatchResult:
    """Match known components from memory against the current screen."""
    from app_memory import quick_template_check, get_app_dir, load_components
    app_dir = get_app_dir(app_name)
    if not app_dir or not Path(app_dir).exists():
        return TemplateMatchResult(matched=[], count=0)

    components = load_components(app_dir)
    comp_names = [c["name"] for c in components if "name" in c]

    # quick_template_check returns (matched_names: set, total: int, ratio: float)
    matched_names, total, ratio = quick_template_check(app_dir, comp_names, img=image_path)

    # Convert to list of dicts with component info
    matched = []
    for comp in components:
        if comp.get("name") in matched_names:
            matched.append({
                "name": comp["name"],
                "cx": comp.get("cx", 0),
                "cy": comp.get("cy", 0),
            })

    return TemplateMatchResult(matched=matched, count=len(matched))


def identify_state(app_name: str) -> StateResult:
    """Identify the current state of an app from visual memory."""
    from app_memory import (
        identify_state_by_components, get_app_dir,
        load_components, load_states, quick_template_check
    )

    app_dir = get_app_dir(app_name)
    if not app_dir or not Path(app_dir).exists():
        return StateResult()

    components = load_components(app_dir)
    comp_names = [c["name"] for c in components if "name" in c]

    # quick_template_check returns (matched_names: set, total: int, ratio: float)
    matched_names, total, ratio = quick_template_check(app_dir, comp_names)
    visible_names = list(matched_names)

    state_name, conf = identify_state_by_components(app_name, visible_names)
    return StateResult(
        state_name=state_name,
        confidence=conf,
        visible_components=visible_names,
    )


def click(x: int, y: int, button: str = "left", clicks: int = 1):
    """Click at screen coordinates."""
    from platform_input import mouse_click
    mouse_click(x, y, button=button, clicks=clicks)


def type_text(text: str):
    """Type text using keyboard."""
    from platform_input import type_text as _type
    _type(text)


def paste(text: str):
    """Paste text via clipboard."""
    from platform_input import paste_text
    paste_text(text)


def press_key(key: str):
    """Press a single key."""
    from platform_input import key_press
    key_press(key)


def key_combo(*keys: str):
    """Press a key combination (e.g., key_combo('cmd', 'c'))."""
    from platform_input import key_combo as _combo
    _combo(*keys)


def get_frontmost_app() -> str:
    """Get the name of the frontmost application."""
    from platform_input import get_frontmost_app as _get
    return _get()


def activate_app(app_name: str):
    """Bring an app to the foreground."""
    from platform_input import activate_app as _activate
    _activate(app_name)


def learn_from_screenshot(image_path: str, app_name: str,
                          page_name: str, domain: str = None) -> dict:
    """Run detection on a screenshot and save all components to memory."""
    from app_memory import learn_from_screenshot as _learn
    return _learn(
        img_path=image_path,
        domain=domain,
        app_name=app_name,
        page_name=page_name,
    )


def record_transition(before_img: str, after_img: str,
                      click_label: str, click_pos: tuple,
                      app_name: str, domain: str = None) -> dict:
    """Record a state transition (before/after a click)."""
    from app_memory import record_page_transition
    return record_page_transition(
        before_img_path=before_img,
        after_img_path=after_img,
        click_label=click_label,
        click_pos=click_pos,
        domain=domain,
        app_name=app_name,
    )


# ═══════════════════════════════════════════
# High-level functions (LLM reasoning)
# ═══════════════════════════════════════════

def observe(programmer: Session, task: str, app_name: str = None,
            worker_model: str = None) -> ObserveResult:
    """Observe the current screen.

    Args:
        programmer: Programmer Session (receives result summary). None = standalone.
        task: What to look for.
        app_name: Override frontmost app detection.
        worker_model: Override worker LLM model.

    Flow:
        1. Python: screenshot → OCR → detector → memory
        2. Worker Session (LLM): interpret all data + screenshot
        3. Report summary to Programmer Session
        4. Worker Session destroyed
    """
    # 1. Deterministic: gather data
    if not app_name:
        app_name = get_frontmost_app()

    shot = take_screenshot()
    ocr = run_ocr(shot.path)
    detection = detect_all(shot.path)
    state = identify_state(app_name)

    ocr_lines = [f"  '{t.get('label','')}' at ({t.get('cx',0)}, {t.get('cy',0)})"
                 for t in ocr.texts[:50]]
    det_lines = [f"  [{e.get('label','component')}] at ({e.get('cx',0)}, {e.get('cy',0)}) conf={e.get('confidence',0):.2f}"
                 for e in detection.elements[:40]]
    state_line = f"State: {state.state_name} (conf={state.confidence:.2f}), visible: {state.visible_components[:10]}" if state.state_name else "(unknown state)"

    # 2. Worker Session: LLM interprets
    worker = _create_worker(worker_model)

    prompt = f"""You are observing the current screen.

## Task
{task}

## Frontmost app
{app_name}

## OCR text (with click-space coordinates)
{chr(10).join(ocr_lines) if ocr_lines else '(none)'}

## Detected UI elements (with click-space coordinates)
{chr(10).join(det_lines) if det_lines else '(none)'}

## Visual memory
{state_line}

Based on ALL data above, report what you see.
Coordinates MUST come from the OCR/detector lists above, never estimated.

Return JSON:
{json.dumps(ObserveResult.model_json_schema(), indent=2)}"""

    reply = worker.send({"text": prompt, "images": [shot.path]})
    # Worker Session done — will be garbage collected

    # 3. Parse
    try:
        data = _parse_json(reply)
        data.setdefault("app_name", app_name)
        data.setdefault("screenshot_path", shot.path)
        data.setdefault("state_name", state.state_name)
        data.setdefault("state_confidence", state.confidence)
        result = ObserveResult(**data)
    except Exception:
        result = ObserveResult(
            app_name=app_name,
            page_description=reply[:300],
            visible_text=[t.get("label", "") for t in ocr.texts[:10]],
            interactive_elements=[],
            state_name=state.state_name,
            state_confidence=state.confidence,
            screenshot_path=shot.path,
        )

    # 4. Report summary to Programmer (only I/O, no details)
    _report_to_programmer(programmer, "observe", result)

    return result


def learn(programmer: Session, app_name: str,
          worker_model: str = None) -> LearnResult:
    """Learn a new app's UI. Worker labels components, Python saves to memory.

    Args:
        programmer: Programmer Session (receives summary). None = standalone.
        app_name: App to learn.
        worker_model: Override worker LLM model.
    """
    shot = take_screenshot()
    detection = detect_all(shot.path)
    ocr = run_ocr(shot.path)

    det_lines = [f"  Component {i}: at ({e.get('cx',0)}, {e.get('cy',0)}), size={e.get('w',0)}x{e.get('h',0)}, conf={e.get('confidence',0):.2f}"
                 for i, e in enumerate(detection.elements[:40])]
    ocr_lines = [f"  '{t.get('label','')}' at ({t.get('cx',0)}, {t.get('cy',0)})"
                 for t in ocr.texts[:50]]

    worker = _create_worker(worker_model)

    prompt = f"""You are learning the UI of "{app_name}" for the first time.

## Detected UI components (need labels)
{chr(10).join(det_lines) if det_lines else '(none)'}

## OCR text on screen
{chr(10).join(ocr_lines) if ocr_lines else '(none)'}

## Screenshot
(attached)

For each component, give it a descriptive snake_case name.
Filter out decorative/non-interactive elements.
Identify the current page name.

Return JSON:
{json.dumps(LearnResult.model_json_schema(), indent=2)}"""

    reply = worker.send({"text": prompt, "images": [shot.path]})

    try:
        data = _parse_json(reply)
        data.setdefault("app_name", app_name)
        saved = learn_from_screenshot(shot.path, app_name, data.get("page_name", "unknown"))
        data.setdefault("components_found", saved.get("saved", 0) + saved.get("existing", 0))
        data.setdefault("components_saved", saved.get("saved", 0))
        result = LearnResult(**data)
    except Exception:
        result = LearnResult(
            app_name=app_name, components_found=detection.count,
            components_saved=0, component_names=[], page_name="unknown",
        )

    _report_to_programmer(programmer, "learn", result)
    return result


def act(programmer: Session, action: str, target: str,
        text: str = None, app_name: str = None,
        worker_model: str = None) -> ActResult:
    """Perform a GUI action. Worker finds target, Python executes.

    Args:
        programmer: Programmer Session (receives result summary). None = standalone.
        action: "click", "double_click", "right_click", "type", "shortcut"
        target: What to click/interact with.
        text: Text to type (for "type" action).
        worker_model: Override worker LLM model.

    Flow:
        1. Python: screenshot → OCR → template match
        2. Worker Session: find target in detection results
        3. Python: execute click/type, screenshot diff
        4. Report summary to Programmer
        5. Worker Session destroyed
    """
    if not app_name:
        app_name = get_frontmost_app()

    # 1. Gather data
    before_shot = take_screenshot()
    ocr = run_ocr(before_shot.path)
    tmatch = template_match(app_name, before_shot.path)

    ocr_lines = [f"  '{t.get('label','')}' at ({t.get('cx',0)}, {t.get('cy',0)})"
                 for t in ocr.texts[:50]]
    match_lines = [f"  '{m.get('name','')}' at ({m.get('cx',0)}, {m.get('cy',0)})"
                   for m in tmatch.matched[:20]]

    before_state = identify_state(app_name)

    # 2. Worker Session: find target
    worker = _create_worker(worker_model)

    prompt = f"""You are performing a GUI action.

## Action: {action}
## Target: {target}
{f'## Text to type: {text}' if text else ''}

## App: {app_name}

## OCR text (with coordinates)
{chr(10).join(ocr_lines) if ocr_lines else '(none)'}

## Known components from memory (template matched)
{chr(10).join(match_lines) if match_lines else '(none)'}

Find the target "{target}" in the lists above.
Report EXACT coordinates from the list. Do NOT estimate from image.
If not found, set success=false.

Return JSON:
{json.dumps(ActResult.model_json_schema(), indent=2)}"""

    reply = worker.send({"text": prompt, "images": [before_shot.path]})
    # Worker done

    # 3. Parse and execute
    try:
        data = _parse_json(reply)
        result = ActResult(**{**data, "action": action, "target": target})

        if result.success and result.coordinates:
            cx, cy = result.coordinates.get("x", 0), result.coordinates.get("y", 0)

            if action.lower() in ("click", "single_click"):
                click(cx, cy)
            elif action.lower() == "double_click":
                click(cx, cy, clicks=2)
            elif action.lower() == "right_click":
                click(cx, cy, button="right")
            elif action.lower() == "type" and text:
                click(cx, cy)
                time.sleep(0.3)
                paste(text)

            # Diff
            time.sleep(0.5)
            after_shot = take_screenshot()
            after_ocr = run_ocr(after_shot.path)
            before_texts = {t.get("label", "") for t in ocr.texts}
            after_texts = {t.get("label", "") for t in after_ocr.texts}
            result.screen_changed = before_texts != after_texts

            after_state = identify_state(app_name)
            result.before_state = before_state.state_name
            result.after_state = after_state.state_name

            if result.screen_changed:
                try:
                    record_transition(
                        before_shot.path, after_shot.path,
                        target, (cx, cy), app_name,
                    )
                except Exception:
                    pass

    except Exception as e:
        result = ActResult(
            action=action, target=target, success=False,
            error=f"Failed: {e}",
        )

    # 4. Report to Programmer
    _report_to_programmer(programmer, "act", result)

    return result


def remember(programmer: Session, operation: str, app_name: str,
             details: str = None) -> RememberResult:
    """Manage visual memory. LLM decides what to save/merge/forget.

    Flow: load memory → LLM reviews → execute operation
    """
    from app_memory import (
        get_app_dir, load_components, load_states,
        save_components, save_states, forget_stale_components,
        merge_similar_states, load_meta, save_meta
    )

    app_dir = get_app_dir(app_name)

    result = None

    if operation == "list":
        components = load_components(app_dir) if app_dir else []
        states = load_states(app_dir) if app_dir else {}
        result = RememberResult(
            operation="list", app_name=app_name,
            details=f"{len(components)} components, {len(states)} states",
        )

    elif operation == "forget":
        if not app_dir:
            result = RememberResult(operation="forget", app_name=app_name, details="No memory found")
        else:
            components = load_components(app_dir)
            meta = load_meta(app_dir)
            states = load_states(app_dir)
            transitions = {}
            try:
                from app_memory import load_transitions
                transitions = load_transitions(app_dir)
            except Exception:
                pass
            removed = forget_stale_components(app_dir, components, meta, states, transitions)
            result = RememberResult(
                operation="forget", app_name=app_name,
                details=f"Removed {removed} stale components",
            )

    elif operation == "merge":
        if not app_dir:
            result = RememberResult(operation="merge", app_name=app_name, details="No memory found")
        else:
            states = load_states(app_dir)
            transitions = {}
            try:
                from app_memory import load_transitions
                transitions = load_transitions(app_dir)
            except Exception:
                pass
            merged = merge_similar_states(states, transitions)
            save_states(app_dir, states)
            result = RememberResult(
                operation="merge", app_name=app_name,
                details=f"Merged {merged} similar states",
            )

    else:
        result = RememberResult(
            operation=operation, app_name=app_name,
            details=f"Unknown operation: {operation}",
        )

    _report_to_programmer(programmer, "remember", result)
    return result


def navigate(programmer: Session, target_state: str, app_name: str,
             worker_model: str = None) -> NavigateResult:
    """Navigate through an app's state graph to reach a target state.

    Args:
        programmer: Programmer Session (receives summary). None = standalone.
        target_state: The state we want to reach.
        app_name: App to navigate in.
        worker_model: Override worker LLM model.

    Flow: identify state → BFS path → act() each step → verify transitions
    Note: act() creates its own worker Sessions for each step.
    """
    from app_memory import get_app_dir, load_states, load_transitions

    current = identify_state(app_name)
    start = current.state_name or "unknown"

    app_dir = get_app_dir(app_name)
    if not app_dir:
        result = NavigateResult(
            start_state=start, target_state=target_state,
            path=[], steps_taken=0, reached_target=False, current_state=start,
        )
        _report_to_programmer(programmer, "navigate", result)
        return result

    states = load_states(app_dir)
    transitions = {}
    try:
        transitions = load_transitions(app_dir)
    except Exception:
        pass

    path = _bfs_path(states, transitions, start, target_state)

    if not path:
        # No known path — use a worker to suggest exploration
        worker = _create_worker(worker_model)
        worker.send(
            f"Navigate from '{start}' to '{target_state}' in {app_name}. "
            f"No known path. States: {list(states.keys())[:20]}. "
            f"Suggest an element to click."
        )
        result = NavigateResult(
            start_state=start, target_state=target_state,
            path=[], steps_taken=0, reached_target=False, current_state=start,
        )
        _report_to_programmer(programmer, "navigate", result)
        return result

    # Follow the path — each step creates its own worker via act()
    steps = 0
    current_state = start
    traversed = [start]

    for next_state in path[1:]:
        trans_key = f"{current_state}→{next_state}"
        action_info = transitions.get(trans_key, {})
        click_target = action_info.get("click_component", next_state)

        # act() creates its own worker Session
        # Pass None as programmer — navigate handles its own reporting
        act_result = act(None, "click", click_target, app_name=app_name,
                         worker_model=worker_model)
        steps += 1

        new_state = identify_state(app_name)
        current_state = new_state.state_name or "unknown"
        traversed.append(current_state)

        if current_state == target_state:
            break

    result = NavigateResult(
        start_state=start,
        target_state=target_state,
        path=traversed,
        steps_taken=steps,
        reached_target=current_state == target_state,
        current_state=current_state,
    )

    _report_to_programmer(programmer, "navigate", result)
    return result


def verify(programmer: Session, expected: str,
           worker_model: str = None) -> VerifyResult:
    """Verify whether a previous action succeeded.

    Args:
        programmer: Programmer Session (receives summary). None = standalone.
        expected: What we expect to see.
        worker_model: Override worker LLM model.
    """
    shot = take_screenshot()
    ocr = run_ocr(shot.path)
    ocr_lines = [f"  '{t.get('label', '')}'" for t in ocr.texts[:30]]

    worker = _create_worker(worker_model)

    prompt = f"""Verify whether the expected outcome was achieved.

## Expected
{expected}

## OCR text on screen
{chr(10).join(ocr_lines) if ocr_lines else '(none)'}

## Screenshot
(attached)

Was the expected outcome achieved? Provide evidence.

Return JSON:
{json.dumps(VerifyResult.model_json_schema(), indent=2)}"""

    reply = worker.send({"text": prompt, "images": [shot.path]})

    try:
        data = _parse_json(reply)
        data.setdefault("screenshot_path", shot.path)
        result = VerifyResult(**data)
    except Exception:
        result = VerifyResult(
            expected=expected, actual=reply[:200],
            verified=False, evidence="Failed to parse LLM response",
            screenshot_path=shot.path,
        )

    _report_to_programmer(programmer, "verify", result)
    return result


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def _parse_json(reply: str) -> dict:
    """Parse JSON from LLM reply, handling markdown code blocks."""
    text = reply.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)


def _bfs_path(states: dict, transitions: dict, start: str, target: str) -> list[str]:
    """BFS shortest path through the state graph."""
    if start == target:
        return [start]

    from collections import deque
    queue = deque([(start, [start])])
    visited = {start}

    # Build adjacency from transitions
    adj = {}
    for key in transitions:
        if "→" in key:
            src, dst = key.split("→", 1)
            adj.setdefault(src, []).append(dst)

    while queue:
        current, path = queue.popleft()
        for neighbor in adj.get(current, []):
            if neighbor == target:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []  # no path found
