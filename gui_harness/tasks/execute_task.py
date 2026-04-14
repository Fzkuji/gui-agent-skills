"""
GUI step — observe → verify → plan → action.

Design principle:
  The LLM is the decision maker — it decides WHAT to do freely.
  We only enforce HOW for things the LLM can't do well (GUI clicking).

Architecture:
  gui_step(task, feedback)        ← @agentic_function, one step (orchestration)
    1. Observe: screenshot + detect + match + state identification  (Python)
    2. Verify: check previous step result, judge task completion    (LLM leaf)
    3. Plan: decide next action based on verification + state       (LLM leaf)
    4. Action: execute the planned action                           (Python)

  gui_agent(task) in main.py      ← @agentic_function, drives the loop
"""

from __future__ import annotations

import inspect
import json
import sys
import time
from typing import Optional

from agentic import agentic_function

from gui_harness.utils import parse_json
from gui_harness.perception import screenshot as _screenshot
from gui_harness.action import input as _input
from gui_harness.action.general_action import general_action
from gui_harness.planning.component_memory import (
    locate_target,
    detect_components,
    match_memory_components,
    identify_state,
    record_transition,
    get_available_transitions,
)
from agentic.functions.build_catalog import build_catalog


# ═══════════════════════════════════════════
# Action wrappers (callable from dispatch)
# ═══════════════════════════════════════════

def _action_click(target: str, task: str, img_path: str, app_name: str, runtime) -> dict:
    location = locate_target(task=task, target=target, img_path=img_path, app_name=app_name, runtime=runtime)
    if not location:
        return {"success": False, "error": f"Target not found: {target}"}
    _input.mouse_click(location["cx"], location["cy"])
    return {"success": True, "location": location}


def _action_double_click(target: str, task: str, img_path: str, app_name: str, runtime) -> dict:
    location = locate_target(task=task, target=target, img_path=img_path, app_name=app_name, runtime=runtime)
    if not location:
        return {"success": False, "error": f"Target not found: {target}"}
    _input.mouse_double_click(location["cx"], location["cy"])
    return {"success": True, "location": location}


def _action_right_click(target: str, task: str, img_path: str, app_name: str, runtime) -> dict:
    location = locate_target(task=task, target=target, img_path=img_path, app_name=app_name, runtime=runtime)
    if not location:
        return {"success": False, "error": f"Target not found: {target}"}
    _input.mouse_right_click(location["cx"], location["cy"])
    return {"success": True, "location": location}


def _action_drag(target: str, target_end: str, task: str, img_path: str, app_name: str, runtime) -> dict:
    start = locate_target(task=task, target=f"Find START: {target}", img_path=img_path, app_name=app_name, runtime=runtime)
    if not start:
        return {"success": False, "error": f"Start not found: {target}"}
    end = locate_target(task=task, target=f"Find END: {target_end}", img_path=img_path, app_name=app_name, runtime=runtime)
    if not end:
        return {"success": False, "error": f"End not found: {target_end}"}
    _input.mouse_drag(start["cx"], start["cy"], end["cx"], end["cy"])
    return {"success": True}


def _action_type(text: str) -> dict:
    _input.type_text(text)
    return {"success": True}


def _action_press(key: str) -> dict:
    _input.key_press(key)
    return {"success": True}


def _action_hotkey(keys: str) -> dict:
    key_list = [k.strip() for k in keys.split("+")]
    _input.key_combo(*key_list)
    return {"success": True}


def _action_scroll(direction: str) -> dict:
    _input.key_press("pageup" if direction.lower() == "up" else "pagedown")
    return {"success": True}


def _action_done(reasoning: str = "") -> dict:
    return {"success": True, "done": True, "reasoning": reasoning}


def _build_action_registry():
    """Build the action function registry for LLM dispatch."""
    return {
        "click": {
            "function": _action_click,
            "description": "Click a UI element on screen (we locate it for you)",
            "input": {
                "target": {"source": "llm", "type": str, "description": "description of element to click"},
                "task": {"source": "context"},
                "img_path": {"source": "context"},
                "app_name": {"source": "context"},
            },
            "output": {"success": bool},
        },
        "double_click": {
            "function": _action_double_click,
            "description": "Double-click a UI element on screen",
            "input": {
                "target": {"source": "llm", "type": str, "description": "description of element to double-click"},
                "task": {"source": "context"},
                "img_path": {"source": "context"},
                "app_name": {"source": "context"},
            },
            "output": {"success": bool},
        },
        "right_click": {
            "function": _action_right_click,
            "description": "Right-click a UI element on screen",
            "input": {
                "target": {"source": "llm", "type": str, "description": "description of element to right-click"},
                "task": {"source": "context"},
                "img_path": {"source": "context"},
                "app_name": {"source": "context"},
            },
            "output": {"success": bool},
        },
        "drag": {
            "function": _action_drag,
            "description": "Drag from one element to another",
            "input": {
                "target": {"source": "llm", "type": str, "description": "description of drag start element"},
                "target_end": {"source": "llm", "type": str, "description": "description of drag end element"},
                "task": {"source": "context"},
                "img_path": {"source": "context"},
                "app_name": {"source": "context"},
            },
            "output": {"success": bool},
        },
        "type": {
            "function": _action_type,
            "description": "Type text using keyboard",
            "input": {
                "text": {"source": "llm", "type": str, "description": "text to type"},
            },
            "output": {"success": bool},
        },
        "press": {
            "function": _action_press,
            "description": "Press a keyboard key (enter, tab, escape, etc.)",
            "input": {
                "key": {"source": "llm", "type": str, "description": "key to press"},
            },
            "output": {"success": bool},
        },
        "hotkey": {
            "function": _action_hotkey,
            "description": "Press a keyboard shortcut (e.g., ctrl+s, ctrl+c)",
            "input": {
                "keys": {"source": "llm", "type": str, "description": "key combination like ctrl+s"},
            },
            "output": {"success": bool},
        },
        "scroll": {
            "function": _action_scroll,
            "description": "Scroll the page up or down",
            "input": {
                "direction": {"source": "llm", "type": str, "description": "up or down"},
            },
            "output": {"success": bool},
        },
        "general": {
            "function": general_action,
            "description": "Execute command-line operations on the VM (only for tasks that cannot be done via GUI)",
            "input": {
                "sub_task": {"source": "llm", "type": str, "description": "what to do via command line"},
                "task_context": {"source": "context"},
            },
            "output": {"success": bool, "output": str},
        },
        "done": {
            "function": _action_done,
            "description": "Mark the task as fully complete",
            "input": {
                "reasoning": {"source": "llm", "type": str, "description": "why the task is complete"},
            },
            "output": {"success": bool},
        },
    }


# ═══════════════════════════════════════════
# 1. Observe — pure Python, no LLM
# ═══════════════════════════════════════════

def _observe(app_name: str) -> dict:
    """Take screenshot, detect components, match memory, identify state.

    Pure Python — no LLM calls. Produces all observation data needed
    by verify_step and plan_next_action.
    """
    t_start = time.time()

    # Screenshot
    img_path = _screenshot.take()
    time.sleep(0.3)

    # Component detection (GPA + OCR)
    t0 = time.time()
    detection = detect_components(img_path)
    icons = detection.get("icons", []) if isinstance(detection, dict) else []
    texts = detection.get("texts", []) if isinstance(detection, dict) else []
    t_detect = round(time.time() - t0, 2)

    # Memory matching (template match against saved components)
    t0 = time.time()
    matched = match_memory_components(app_name, img_path)
    matched_names = {c["name"] for c in matched}
    t_match = round(time.time() - t0, 2)

    # State identification (Jaccard similarity against known states)
    current_state = identify_state(app_name, matched_names)

    # Known transitions from current state
    transitions = get_available_transitions(app_name, current_state) if current_state else []

    t_total = round(time.time() - t_start, 2)
    print(
        f"    [observe] {len(icons)} icons, {len(texts)} texts, "
        f"{len(matched)} matched, state={current_state}, "
        f"{len(transitions)} transitions ({t_total}s: detect={t_detect}s, match={t_match}s)",
        file=sys.stderr,
    )

    # Build component info string for LLM
    comp_lines = []
    for c in matched[:30]:
        comp_lines.append(f"  [{c['name']}] at ({c['cx']}, {c['cy']})")
    text_lines = []
    for t_item in texts[:40]:
        label = t_item.get("label", "")
        if label and len(label) > 1:
            text_lines.append(f"  '{label}' at ({t_item.get('cx', 0)}, {t_item.get('cy', 0)})")

    component_info = ""
    if comp_lines:
        component_info += "\n<known_components>\n" + "\n".join(comp_lines) + "\n</known_components>"
    if text_lines:
        component_info += "\n<screen_text>\n" + "\n".join(text_lines) + "\n</screen_text>"

    # Build transitions info string for LLM
    transitions_info = ""
    if transitions:
        trans_lines = [
            f"  {t['action']}:{t['target']} -> state {t['to_state']} (used {t['use_count']}x)"
            for t in transitions[:10]
        ]
        transitions_info = "\n<known_transitions>\n" + "\n".join(trans_lines) + "\n</known_transitions>"

    return {
        "img_path": img_path,
        "icons": icons,
        "texts": texts,
        "matched": matched,
        "matched_names": matched_names,
        "current_state": current_state,
        "transitions": transitions,
        "component_info": component_info,
        "transitions_info": transitions_info,
    }


# ═══════════════════════════════════════════
# 2. Verify — LLM leaf function (one exec)
# ═══════════════════════════════════════════

@agentic_function(
    summarize={"depth": 0, "siblings": 0},
    input={
        "task": {"description": "The overall task being performed"},
        "img_path": {"description": "Path to current screenshot (after previous action)"},
        "component_info": {"description": "Formatted string of detected UI components"},
        "feedback": {"description": "Dict from previous step: goal, action, target, success, error"},
        "runtime": {"hidden": True},
    },
)
def verify_step(
    task: str,
    img_path: str,
    component_info: str,
    feedback: dict,
    runtime=None,
) -> dict:
    """Evaluate whether the previous action achieved its goal.

    You see a screenshot taken AFTER the previous action was executed.
    Your ONLY job: compare the stated goal with what is now visible.

    Return JSON:
    {
      "step_succeeded": true/false,
      "observation": "brief factual description of current screen state"
    }

    step_succeeded = Did the action achieve its stated goal?
      true  — the expected change is visible (e.g., app opened, text appeared,
              button state changed, file listed in directory)
      false — no visible change, wrong result, or error message on screen

    IMPORTANT — Command-line ("general") actions:
      When the previous action was "general" (command-line), it runs in the
      background and does NOT change the GUI. The screenshot will look the
      same as before. This is NORMAL — do NOT mark step_succeeded=false
      just because the screen hasn't changed. Instead:
      - If Execution=succeeded → trust it, set step_succeeded=true
      - If Execution=failed or there is an error → set step_succeeded=false
      - Only set false if you see an actual error message ON SCREEN

    observation = One sentence describing what you see RIGHT NOW.
      Good: "Terminal shows 'Build complete', file explorer open in background"
      Bad:  "The task appears to be done" (vague, not factual)

    You do NOT decide whether the overall task is complete.
    That decision belongs to the planning step, not to you.
    """
    if runtime is None:
        raise ValueError("verify_step() requires a runtime argument")

    feedback_text = f"Previous step goal: {feedback.get('goal', 'unknown')}\n"
    feedback_text += f"Action taken: {feedback.get('action', 'unknown')}"
    if feedback.get("target"):
        feedback_text += f" on '{feedback['target']}'"
    feedback_text += f"\nExecution: {'succeeded' if feedback.get('success') else 'failed'}"
    if feedback.get("error"):
        feedback_text += f"\nError: {feedback['error']}"

    context = f"<task>{task}</task>\n\n<previous_step>\n{feedback_text}\n</previous_step>{component_info}"

    reply = runtime.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])

    try:
        result = parse_json(reply)
        result.pop("task_completed", None)  # verify no longer decides completion
        return result
    except Exception:
        return {
            "step_succeeded": True,
            "observation": reply[:300],
        }


# ═══════════════════════════════════════════
# 3. Plan — LLM leaf function (one exec)
# ═══════════════════════════════════════════

@agentic_function(
    summarize={"depth": 0, "siblings": 0},
    input={
        "task": {"description": "The overall task being performed"},
        "img_path": {"description": "Path to current screenshot"},
        "component_info": {"description": "Formatted string of detected UI components"},
        "verification_summary": {"description": "What happened in the previous step (or empty)"},
        "transitions_info": {"description": "Known transitions from current UI state (or empty)"},
        "action_catalog": {"description": "Available actions and their parameter schemas"},
        "runtime": {"hidden": True},
    },
)
def plan_next_action(
    task: str,
    img_path: str,
    component_info: str,
    verification_summary: str,
    transitions_info: str,
    action_catalog: str,
    runtime=None,
) -> dict:
    """Decide the next action to take toward completing the task.

    You are a GUI automation agent. You see a screenshot of the current
    screen, along with detected UI components, previous step results,
    and a list of actions you can perform.

    Return JSON for exactly ONE action from the available list.
    You MUST include these fields:
    {
      "call": "<action_name>",
      "args": { ... },
      "goal": "what this action should achieve (one sentence)",
      "reasoning": "why this is the right next step"
    }

    The "goal" field is critical — it will be used to verify this action
    in the next step. Be specific:
      Good goal: "Type 'Calculator' into the Spotlight search field"
      Bad goal:  "Continue the task"

    Decision guidelines:
    - Prefer GUI interaction (click, type, hotkey) over command-line ("general")
    - If <known_transitions> lists a relevant action, prefer it — it worked before
    - Do NOT generate or paraphrase content from your own knowledge.
      All data must come from what is visible on screen or from actual files.
    - Choose "done" ONLY when you have strong evidence the task is fully
      complete. If a command ran but you haven't verified the output, do NOT
      choose "done" — choose an action to verify the result first.
    - If the previous step failed, plan a recovery (retry or alternative approach).

    Work habits — follow these to avoid common mistakes:
    - EXPLORE FIRST: Before starting work, check what files and scripts
      already exist in the working directory (ls ~/Desktop, ls .). There may
      be pre-written scripts or templates you can reuse instead of writing
      from scratch.
    - VERIFY OUTPUTS: After creating a file, verify it meets requirements.
      For images: check dimensions, format, file size (e.g., identify file.png
      or python3 -c "from PIL import Image; im=Image.open('f.png'); print(im.size, im.mode)").
      Compare against any reference or expected values.
    - DON'T REPEAT YOURSELF: If you've already done the same "general" action
      in a previous step and it succeeded, do NOT repeat it. Move on to the
      next sub-task or verify the output instead.
    - PRESERVE FORMAT: When working with files, only make the changes
      explicitly requested. Do not add extra transformations (resizing,
      cropping, reformatting, restructuring) that the task didn't ask for.
      Keep the original attributes (dimensions, format, structure) intact
      unless the task specifically says otherwise.
    """
    if runtime is None:
        raise ValueError("plan_next_action() requires a runtime argument")

    parts = [f"<task>{task}</task>"]
    if verification_summary:
        parts.append(f"\n<previous_result>\n{verification_summary}\n</previous_result>")
    parts.append(component_info)
    if transitions_info:
        parts.append(transitions_info)
    parts.append(f"\n== Available Actions ==\n{action_catalog}")

    context = "\n".join(parts)

    reply = runtime.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])

    try:
        return parse_json(reply)
    except Exception:
        reply_lower = reply.lower()
        if '"done"' in reply_lower or "task is complete" in reply_lower:
            return {"action": "done", "goal": "task complete", "reasoning": reply[:200]}
        return {"action": "general", "sub_task": reply[:200], "goal": reply[:100]}


# ═══════════════════════════════════════════
# 4. Dispatch — pure Python, execute planned action
# ═══════════════════════════════════════════

def _dispatch(plan: dict, img_path: str, app_name: str, task: str, runtime) -> dict:
    """Execute the planned action. Pure Python dispatch (no LLM except via locate_target)."""
    action_name = plan.get("call", plan.get("action", "general"))
    registry = _build_action_registry()

    dispatch_context = {
        "task": task,
        "img_path": img_path,
        "app_name": app_name,
        "task_context": f"<task>{task}</task>",
    }

    try:
        if action_name in registry:
            spec = registry[action_name]
            func = spec["function"]
            args = dict(plan.get("args", {}))
            # Accept flat plan keys for backward compatibility
            for key in spec.get("input", {}):
                if key not in args and key in plan:
                    args[key] = plan[key]
            # Fill context params
            for key, info in spec.get("input", {}).items():
                if info.get("source") == "context" and key not in args:
                    if key in dispatch_context:
                        args[key] = dispatch_context[key]
            # Inject runtime if needed
            sig = inspect.signature(func)
            if "runtime" in sig.parameters and "runtime" not in args:
                args["runtime"] = runtime
            valid_params = set(sig.parameters.keys())
            args = {k: v for k, v in args.items() if k in valid_params}
            result = func(**args)
        else:
            sub_task = plan.get("sub_task", plan.get("task", plan.get("target", str(plan)[:200])))
            result = general_action(sub_task=sub_task, task_context=f"<task>{task}</task>", runtime=runtime)
    except Exception as e:
        result = {"success": False, "error": str(e)}

    return result


# ═══════════════════════════════════════════
# gui_step — orchestration function (no exec)
# ═══════════════════════════════════════════

@agentic_function(
    compress=True,
    summarize={"siblings": -1},
    input={
        "task": {"description": "The overall task being performed"},
        "feedback": {"description": "Structured result from previous step (None for first step)"},
        "app_name": {"description": "App name for component memory lookup"},
        "runtime": {"hidden": True},
    },
)
def gui_step(
    task: str,
    feedback: Optional[dict],
    app_name: str,
    runtime=None,
) -> dict:
    """Execute one step of a GUI task: observe -> verify -> plan -> action.

    Orchestration function — coordinates four phases without calling
    runtime.exec() directly. Each LLM-calling child is a separate
    @agentic_function (verify_step, plan_next_action).

    Flow:
      1. Observe  (Python): screenshot + detect + match + identify_state
      2. Verify   (LLM):    check previous step result + task completion
      3. Plan     (LLM):    decide next action
      4. Action   (Python): dispatch and execute the planned action

    Args:
        task: The overall task description.
        feedback: Result summary from the previous step (None for first step).
        app_name: App name for component memory.
        runtime: LLM runtime instance.

    Returns:
        dict with keys:
          - done (bool): Whether the task is complete (decided by plan, not verify).
          - plan (dict): The planned action {action, args, goal, reasoning}.
          - exec_result (dict): Dispatch result {success, error, ...}.
          - verification (dict|None): Verify result {step_succeeded, observation}.
          - state (str|None): Current UI state ID.
    """
    if runtime is None:
        raise ValueError("gui_step() requires a runtime argument")

    # ── 1. Observe (pure Python) ──
    obs = _observe(app_name)

    # ── 2. Verify previous step (LLM, only if feedback exists) ──
    verification = None
    if feedback:
        verification = verify_step(
            task=task,
            img_path=obs["img_path"],
            component_info=obs["component_info"],
            feedback=feedback,
            runtime=runtime,
        )

        # Record state transition: previous state → current state
        prev_state = feedback.get("prev_state")
        if prev_state and obs["current_state"]:
            record_transition(
                app_name=app_name,
                from_state=prev_state,
                action=feedback.get("action", ""),
                action_target=feedback.get("target", ""),
                to_state=obs["current_state"],
            )

        # NOTE: verify does NOT decide task completion.
        # Plan always runs and makes the final "done" decision.

    # ── 3. Plan next action (LLM) ──
    registry = _build_action_registry()
    catalog = build_catalog(registry)

    verification_summary = ""
    if verification:
        succeeded = "succeeded" if verification.get("step_succeeded") else "failed"
        verification_summary = (
            f"Previous step {succeeded}. "
            f"Observation: {verification.get('observation', '')}"
        )

    plan = plan_next_action(
        task=task,
        img_path=obs["img_path"],
        component_info=obs["component_info"],
        verification_summary=verification_summary,
        transitions_info=obs["transitions_info"],
        action_catalog=catalog,
        runtime=runtime,
    )

    action_name = plan.get("call", plan.get("action", "general"))

    # Plan says done?
    if action_name == "done":
        return {
            "done": True,
            "plan": plan,
            "state": obs["current_state"],
        }

    # ── 4. Action (pure Python dispatch) ──
    exec_result = _dispatch(plan, obs["img_path"], app_name, task, runtime)

    return {
        "done": False,
        "plan": plan,
        "exec_result": exec_result,
        "verification": verification,
        "state": obs["current_state"],
    }


# ═══════════════════════════════════════════
# build_step_feedback — pure Python
# ═══════════════════════════════════════════

def build_step_feedback(result: dict) -> dict:
    """Extract key information from a step result for the next iteration.

    Pure Python — no LLM. Produces a structured feedback dict that
    verify_step will receive to evaluate the previous action.
    """
    plan = result.get("plan", {})
    exec_result = result.get("exec_result", {})
    verification = result.get("verification")

    feedback = {
        "goal": plan.get("goal", ""),
        "action": plan.get("call", plan.get("action", "")),
        "target": plan.get("args", {}).get("target", plan.get("target", "")),
        "success": exec_result.get("success", False),
        "error": exec_result.get("error", ""),
        "prev_state": result.get("state"),
    }

    if verification:
        feedback["prev_observation"] = verification.get("observation", "")

    return feedback


# ═══════════════════════════════════════════
# Workflow recording
# ═══════════════════════════════════════════

def save_workflow_record(result: dict, app_name: str):
    """Save the workflow record for future reference."""
    from gui_harness.memory import app_memory
    try:
        app_dir = app_memory.get_app_dir(app_name)
        workflows_dir = app_dir / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        ts = time.strftime("%Y%m%d_%H%M%S")
        record_path = workflows_dir / f"workflow_{ts}.json"
        with open(record_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
    except Exception as e:
        print(f"  [workflow] save error: {e}", file=sys.stderr)


# ═══════════════════════════════════════════
# Backward-compatible wrapper (for benchmarks)
# ═══════════════════════════════════════════

def execute_task(task: str, runtime=None, max_steps: int = 30, app_name: str = "desktop") -> dict:
    """Execute a GUI task. Thin wrapper around gui_agent for backward compatibility.

    Prefer using gui_agent() directly for new code.
    """
    from gui_harness.main import gui_agent
    return gui_agent(task=task, max_steps=max_steps, app_name=app_name, runtime=runtime)
