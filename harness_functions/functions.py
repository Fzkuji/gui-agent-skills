"""
GUI Agent Functions — the 6 core functions for desktop automation.

Each function's docstring is the LLM prompt. Change the docstring → change the behavior.
The scripts/*.py layer handles all deterministic operations (screenshot, OCR, click, etc.).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# Add parent to path for imports
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Import from harness framework
sys.path.insert(0, str(SKILL_DIR.parent.parent.parent / "Documents" / "LLM Agent Harness" / "llm-agent-harness"))
from harness import function, Session


# ═══════════════════════════════════════════
# Return types
# ═══════════════════════════════════════════

class ObserveResult(BaseModel):
    """What the agent sees on screen right now."""
    app_name: str                          # frontmost app
    page_description: str                  # what's on screen
    visible_text: list[str]                # OCR results (key texts)
    interactive_elements: list[str]        # clickable things found
    state_name: Optional[str] = None       # known state from memory (if any)
    state_confidence: Optional[float] = None
    target_visible: bool = False           # is the user's target on screen?
    target_location: Optional[dict] = None # {x, y} if found
    screenshot_path: Optional[str] = None  # path to screenshot taken

class LearnResult(BaseModel):
    """Result of learning a new app's UI."""
    app_name: str
    components_found: int                  # total detected
    components_saved: int                  # new ones saved to memory
    component_names: list[str]             # what was identified
    page_name: str                         # human-readable page label
    already_known: bool = False            # was this app already in memory?

class ActResult(BaseModel):
    """Result of performing a GUI action."""
    action: str                            # what was done ("click", "type", "shortcut")
    target: str                            # what was targeted
    coordinates: Optional[dict] = None     # {x, y} where action happened
    success: bool                          # did it appear to work?
    before_state: Optional[str] = None     # state before action
    after_state: Optional[str] = None      # state after action
    screen_changed: bool = False           # did the screen change?
    error: Optional[str] = None            # error message if failed

class RememberResult(BaseModel):
    """Result of a memory operation."""
    operation: str                         # "save", "merge", "forget", "list"
    app_name: str
    details: str                           # human-readable summary

class NavigateResult(BaseModel):
    """Result of multi-step navigation."""
    start_state: str
    target_state: str
    path: list[str]                        # states traversed
    steps_taken: int
    reached_target: bool
    current_state: str                     # where we ended up

class VerifyResult(BaseModel):
    """Result of verification after an action."""
    expected: str                          # what we expected to see
    actual: str                            # what we actually see
    verified: bool                         # does actual match expected?
    evidence: str                          # why we think so
    screenshot_path: Optional[str] = None


# ═══════════════════════════════════════════
# Helper: run scripts
# ═══════════════════════════════════════════

def _run_script(script_name: str, *args) -> str:
    """Run a Python script from scripts/ and return stdout."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed: {result.stderr[:500]}")
    return result.stdout.strip()


def _take_screenshot() -> str:
    """Take a screenshot and return the path."""
    import tempfile
    path = Path(tempfile.mkdtemp()) / "screenshot.png"
    subprocess.run(["screencapture", "-x", str(path)], check=True, timeout=10)
    return str(path)


def _run_ocr(image_path: str) -> list[dict]:
    """Run OCR on an image, return text elements."""
    try:
        from ui_detector import detect_text
        return detect_text(image_path)
    except Exception:
        return []


def _run_detector(image_path: str) -> list[dict]:
    """Run GPA-GUI-Detector on an image, return UI elements."""
    try:
        from ui_detector import detect_icons
        return detect_icons(image_path)
    except Exception:
        return []


def _get_frontmost_app() -> str:
    """Get the name of the frontmost application."""
    try:
        r = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to name of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=5
        )
        return r.stdout.strip()
    except Exception:
        return "unknown"


# ═══════════════════════════════════════════
# Functions (docstring = LLM prompt)
# ═══════════════════════════════════════════

def observe(session: Session, task: str, screenshot_path: str = None) -> ObserveResult:
    """Observe the current screen state.

    This is a hybrid function: Python gathers data, LLM interprets it.

    1. Python: take screenshot, run OCR, run detector, check memory
    2. LLM: interpret all the data and answer the task
    3. Python: parse LLM output into ObserveResult
    """
    # Step 1: Python gathers data
    app_name = _get_frontmost_app()

    if not screenshot_path:
        screenshot_path = _take_screenshot()

    ocr_results = _run_ocr(screenshot_path)
    ocr_texts = [f"  '{r.get('label', '')}' at ({r.get('cx', 0)}, {r.get('cy', 0)})"
                 for r in ocr_results[:50]]  # limit to top 50

    detector_results = _run_detector(screenshot_path)
    detector_items = [f"  component at ({r.get('cx', 0)}, {r.get('cy', 0)}) conf={r.get('confidence', 0):.2f}"
                      for r in detector_results[:30]]

    # Check memory for known state
    state_name, state_conf = None, None
    try:
        from app_memory import identify_state_by_components, _detect_visible_components
        visible = _detect_visible_components(app_name)
        state_name, state_conf = identify_state_by_components(app_name, visible)
    except Exception:
        pass

    # Step 2: LLM interprets
    prompt = f"""You are observing the current screen to understand what's visible.

## Task
{task}

## Current app
{app_name}

## OCR text detected (with coordinates)
{chr(10).join(ocr_texts) if ocr_texts else '(no text detected)'}

## UI components detected (with coordinates)
{chr(10).join(detector_items) if detector_items else '(no components detected)'}

## Known state from memory
{f'State: {state_name} (confidence: {state_conf:.2f})' if state_name else '(unknown state)'}

## Screenshot
(attached as image)

Based on ALL of this information, determine:
- What app is open and what page/state it's in
- What interactive elements are available
- Whether the target described in the task is visible
- If visible, where exactly it is (x, y coordinates from OCR or detector, NOT from your visual estimate)

IMPORTANT: Coordinates must come from OCR or detector results listed above.

Respond with ONLY a JSON object matching this schema:
{json.dumps(ObserveResult.model_json_schema(), indent=2)}"""

    # Send with screenshot if session supports images
    message = {"text": prompt, "images": [screenshot_path]}
    reply = session.send(message)

    # Step 3: Parse
    try:
        result = _parse_observe_result(reply, app_name, screenshot_path, state_name, state_conf)
    except Exception:
        # Fallback: construct from raw data
        result = ObserveResult(
            app_name=app_name,
            page_description=reply[:200],
            visible_text=[r.get("label", "") for r in ocr_results[:10]],
            interactive_elements=[],
            state_name=state_name,
            state_confidence=state_conf,
            target_visible=False,
            screenshot_path=screenshot_path,
        )

    return result


def _parse_observe_result(reply: str, app_name: str, screenshot_path: str,
                          state_name: str = None, state_conf: float = None) -> ObserveResult:
    """Parse LLM reply into ObserveResult."""
    text = reply.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    data = json.loads(text)
    # Ensure required fields
    data.setdefault("app_name", app_name)
    data.setdefault("screenshot_path", screenshot_path)
    if state_name and not data.get("state_name"):
        data["state_name"] = state_name
        data["state_confidence"] = state_conf
    return ObserveResult(**data)


@function(return_type=LearnResult)
def learn(session: Session, app_name: str, screenshot_path: str = None) -> LearnResult:
    """You are learning a new app's UI for the first time.

App to learn: {app_name}

You will receive:
1. A screenshot of the app
2. All UI components detected by GPA-GUI-Detector (bounding boxes, no labels)
3. OCR text detected on screen

Your job:
- Look at each detected component in the screenshot
- Give each component a descriptive name based on what it is (e.g., "send_button", "search_bar", "contact_list")
- Filter out duplicates and non-interactive decorative elements
- Group related components if they belong together
- Identify the current page/state name (e.g., "chat_main", "settings", "login")

Name components clearly and consistently. Use snake_case. Be specific: "send_message_button" not just "button"."""


def act(session: Session, action: str, target: str,
        text: str = None, screenshot_path: str = None) -> ActResult:
    """Perform a GUI action: click, type, shortcut, or scroll.

    Hybrid function:
    1. Python: screenshot, OCR, detector, template match
    2. LLM: find target element, decide exact coordinates
    3. Python: execute click/type, take after-screenshot, diff
    """
    # Step 1: Gather data
    app_name = _get_frontmost_app()

    if not screenshot_path:
        screenshot_path = _take_screenshot()

    ocr_results = _run_ocr(screenshot_path)
    ocr_texts = [f"  '{r.get('label', '')}' at ({r.get('cx', 0)}, {r.get('cy', 0)})"
                 for r in ocr_results[:50]]

    # Check template matches from memory
    memory_matches = []
    try:
        from app_memory import _detect_visible_components
        visible = _detect_visible_components(app_name)
        memory_matches = [f"  '{c['name']}' at ({c.get('cx', 0)}, {c.get('cy', 0)}) conf={c.get('confidence', 0):.2f}"
                         for c in visible[:20]]
    except Exception:
        pass

    # Step 2: LLM decides coordinates
    prompt = f"""You are performing a GUI action on the screen.

## Action
{action}: {target}
{f'Text to type: {text}' if text else ''}

## Current app
{app_name}

## OCR text detected (with coordinates)
{chr(10).join(ocr_texts) if ocr_texts else '(no text detected)'}

## Known components from memory (template matched)
{chr(10).join(memory_matches) if memory_matches else '(no known components matched)'}

## Screenshot
(attached as image)

Your job:
1. Find the target "{target}" in the OCR results or memory matches above
2. Report the EXACT coordinates from the list above (not estimated from image)
3. If you can't find it, set success=false

Respond with ONLY a JSON object matching this schema:
{json.dumps(ActResult.model_json_schema(), indent=2)}"""

    message = {"text": prompt, "images": [screenshot_path]}
    reply = session.send(message)

    # Step 3: Parse and execute
    try:
        text_clean = reply.strip()
        if text_clean.startswith("```"):
            lines = text_clean.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text_clean = "\n".join(lines).strip()
        data = json.loads(text_clean)
        result = ActResult(**data)

        # If LLM found coordinates and action is click, execute it
        if result.success and result.coordinates and action.lower() in ("click", "single_click"):
            try:
                from platform_input import click_at
                click_at(result.coordinates["x"], result.coordinates["y"])

                # Take after-screenshot and check diff
                import time
                time.sleep(0.5)
                after_path = _take_screenshot()
                after_ocr = _run_ocr(after_path)
                before_texts = {r.get("label", "") for r in ocr_results}
                after_texts = {r.get("label", "") for r in after_ocr}
                result.screen_changed = before_texts != after_texts
            except Exception as e:
                result.success = False
                result.error = str(e)

        return result

    except Exception as e:
        return ActResult(
            action=action,
            target=target,
            success=False,
            error=f"Failed to parse LLM response: {e}",
        )


@function(return_type=RememberResult)
def remember(session: Session, operation: str, app_name: str,
             details: str = None) -> RememberResult:
    """You are managing the visual memory for an app.

Operation: {operation}
App: {app_name}
Details: {details}

Available operations:
- "save": Save new components detected on the current screen
- "merge": Merge duplicate states that look the same
- "forget": Remove components that haven't been matched in 15+ attempts
- "list": List all known components and states for the app
- "rename": Rename a component to a better name

For "save": You'll receive detected components. Decide which are worth saving.
For "merge": You'll see similar states. Decide if they should be combined.
For "forget": You'll see components with low match rates. Decide what to remove.

Be conservative with forgetting — only remove things that are clearly obsolete."""


@function(return_type=NavigateResult)
def navigate(session: Session, target_state: str, app_name: str) -> NavigateResult:
    """You are navigating through an app to reach a target state.

Target state: {target_state}
App: {app_name}

You will receive:
1. Current state (from visual memory)
2. The state graph (known states and transitions between them)
3. BFS shortest path from current state to target (if one exists)

Your job:
1. If a known path exists, follow it step by step
2. At each step, verify you reached the expected state (template match or OCR)
3. If verification fails, re-observe and try an alternative path
4. If no known path exists, explore: try clicking likely elements and observe results

Verification tiers (try in order):
1. Template match against known components → fast, reliable
2. Full detection (OCR + GPA) → slower but comprehensive
3. LLM visual check → last resort, send screenshot to image tool

Report each state transition as you go."""


def verify(session: Session, expected: str,
           screenshot_path: str = None) -> VerifyResult:
    """Verify whether a previous action succeeded.

    Hybrid function: Python takes screenshot + OCR, LLM judges.
    """
    if not screenshot_path:
        screenshot_path = _take_screenshot()

    ocr_results = _run_ocr(screenshot_path)
    ocr_texts = [f"  '{r.get('label', '')}'" for r in ocr_results[:30]]

    prompt = f"""You are verifying whether a previous action succeeded.

## Expected outcome
{expected}

## OCR text currently visible on screen
{chr(10).join(ocr_texts) if ocr_texts else '(no text detected)'}

## Screenshot
(attached as image)

Determine if the expected outcome is achieved.
Provide specific evidence (what text you see, what's present/absent).
Be honest: if it didn't work, say so clearly.

Respond with ONLY a JSON object matching this schema:
{json.dumps(VerifyResult.model_json_schema(), indent=2)}"""

    message = {"text": prompt, "images": [screenshot_path]}
    reply = session.send(message)

    try:
        text_clean = reply.strip()
        if text_clean.startswith("```"):
            lines = text_clean.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text_clean = "\n".join(lines).strip()
        data = json.loads(text_clean)
        data.setdefault("screenshot_path", screenshot_path)
        return VerifyResult(**data)
    except Exception:
        return VerifyResult(
            expected=expected,
            actual=reply[:200],
            verified=False,
            evidence="Failed to parse LLM response",
            screenshot_path=screenshot_path,
        )
