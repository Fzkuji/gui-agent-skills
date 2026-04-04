"""
gui_harness.functions.navigate — navigate through an app's state graph.

navigate() is an @agentic_function(compress=True) that:
  1. Identifies the current app state
  2. Finds a BFS path to the target state
  3. Internally calls act() + verify() for each step
  4. compress=True hides internal steps from summarize()
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from agentic import agentic_function

_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        from gui_harness.runtime import GUIRuntime
        _runtime = GUIRuntime()
    return _runtime


@agentic_function(compress=True)
def navigate(target_state: str, app_name: str,
             runtime=None, max_steps: int = 10) -> dict:
    """Navigate to a target state in an app's UI state graph.

    Uses BFS over the known state graph (from app_memory) to find the shortest
    path, then executes each step via act() + verify().

    compress=True: callers see only this function's result, not the internal
    act()/verify() calls.

    Args:
        target_state: The state name to navigate to.
        app_name:     App to navigate in.
        runtime:      Optional: Runtime instance.
        max_steps:    Maximum actions to take (default: 10).

    Returns:
        dict with keys:
            start_state, target_state, path, steps_taken,
            reached_target, current_state
    """
    from gui_harness.functions.act import act
    from gui_harness.functions.verify import verify

    rt = runtime or _get_runtime()

    # Load state graph
    states, transitions, start_state = {}, {}, "unknown"
    try:
        _SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
        if _SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, _SCRIPTS_DIR)
        from app_memory import (
            get_app_dir, load_states, load_transitions,
            identify_state_by_components, load_components, quick_template_check
        )
        app_dir = get_app_dir(app_name)
        if app_dir:
            states = load_states(app_dir) or {}
            try:
                transitions = load_transitions(app_dir) or {}
            except Exception:
                pass
            components = load_components(app_dir)
            comp_names = [c["name"] for c in components if "name" in c]
            matched_names, _, _ = quick_template_check(app_dir, comp_names)
            state_name, _ = identify_state_by_components(app_name, list(matched_names))
            start_state = state_name or "unknown"
    except Exception:
        pass

    # Already there?
    if start_state == target_state:
        return {
            "start_state": start_state, "target_state": target_state,
            "path": [start_state], "steps_taken": 0,
            "reached_target": True, "current_state": start_state,
        }

    # BFS path
    path = _bfs_path(states, transitions, start_state, target_state)

    if not path or len(path) < 2:
        # No known path — try one LLM-guided attempt
        act(action="click", target=f"element that leads to {target_state}",
            app_name=app_name, runtime=rt)
        vr = verify(expected=f"App is now in state: {target_state}", runtime=rt)
        return {
            "start_state": start_state, "target_state": target_state,
            "path": [start_state], "steps_taken": 1,
            "reached_target": vr.get("verified", False),
            "current_state": target_state if vr.get("verified") else start_state,
        }

    # Follow path
    current_state = start_state
    traversed = [start_state]
    steps = 0

    for next_state in path[1:]:
        if steps >= max_steps:
            break

        trans_key = f"{current_state}→{next_state}"
        action_info = transitions.get(trans_key, {})
        click_target = action_info.get("click_component", next_state)

        act(action="click", target=click_target, app_name=app_name, runtime=rt)
        steps += 1

        vr = verify(expected=f"Navigated to: {next_state}", runtime=rt)
        if vr.get("verified"):
            current_state = next_state
        traversed.append(current_state)

        if current_state == target_state:
            break

    return {
        "start_state": start_state, "target_state": target_state,
        "path": traversed, "steps_taken": steps,
        "reached_target": current_state == target_state,
        "current_state": current_state,
    }


def _bfs_path(states: dict, transitions: dict, start: str, target: str) -> list[str]:
    if start == target:
        return [start]

    adj: dict[str, list[str]] = {}
    for key in transitions:
        if "→" in key:
            src, dst = key.split("→", 1)
            adj.setdefault(src, []).append(dst)

    queue: deque = deque([(start, [start])])
    visited = {start}

    while queue:
        current, path = queue.popleft()
        for neighbor in adj.get(current, []):
            if neighbor == target:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []
