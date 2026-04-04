"""
gui_harness.functions.remember — manage visual memory for apps.

Wraps app_memory operations with @agentic_function for Context tree integration.
"""

from __future__ import annotations

import sys
from pathlib import Path

from agentic import agentic_function

_SCRIPTS_DIR = str(Path(__file__).parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


@agentic_function
def remember(operation: str, app_name: str, details: str = None) -> dict:
    """Manage visual memory for an app.

    Operations:
        "list"   — list all known components and states
        "forget" — remove stale/outdated components
        "merge"  — merge similar states in the state graph

    Args:
        operation: One of "list", "forget", "merge".
        app_name:  App whose memory to manage.
        details:   Optional extra info.

    Returns:
        dict with keys: operation, app_name, details
    """
    try:
        from app_memory import (
            get_app_dir, load_components, load_states,
            forget_stale_components, merge_similar_states,
            save_states, load_meta
        )

        app_dir = get_app_dir(app_name)

        if operation == "list":
            if not app_dir:
                return {"operation": "list", "app_name": app_name,
                        "details": "No memory found"}
            components = load_components(app_dir)
            states = load_states(app_dir) or {}
            return {
                "operation": "list", "app_name": app_name,
                "details": f"{len(components)} components, {len(states)} states",
            }

        elif operation == "forget":
            if not app_dir:
                return {"operation": "forget", "app_name": app_name,
                        "details": "No memory found"}
            components = load_components(app_dir)
            meta = load_meta(app_dir)
            states = load_states(app_dir) or {}
            transitions = {}
            try:
                from app_memory import load_transitions
                transitions = load_transitions(app_dir)
            except Exception:
                pass
            removed = forget_stale_components(app_dir, components, meta, states, transitions)
            return {
                "operation": "forget", "app_name": app_name,
                "details": f"Removed {removed} stale components",
            }

        elif operation == "merge":
            if not app_dir:
                return {"operation": "merge", "app_name": app_name,
                        "details": "No memory found"}
            states = load_states(app_dir) or {}
            transitions = {}
            try:
                from app_memory import load_transitions
                transitions = load_transitions(app_dir)
            except Exception:
                pass
            merged = merge_similar_states(states, transitions)
            save_states(app_dir, states)
            return {
                "operation": "merge", "app_name": app_name,
                "details": f"Merged {merged} similar states",
            }

        else:
            return {
                "operation": operation, "app_name": app_name,
                "details": f"Unknown operation: {operation}",
            }

    except ImportError:
        return {
            "operation": operation, "app_name": app_name,
            "details": "app_memory module not available",
        }
