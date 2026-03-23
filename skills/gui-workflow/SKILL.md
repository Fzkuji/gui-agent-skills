---
name: gui-workflow
description: "State graph navigation, workflow recording and replay with tiered verification."
---

# Workflow — Target State Verification Mode

## Core Concept

Workflows navigate to a **target state** using the app's state graph.
Verification uses **tiered cost escalation**: cheapest check first, only escalate if needed.

```
Level 0: Template Match (~0.3s, 0 tokens)
  → Check target state's defining_components on screen
  → matched_ratio > 0.7 → confirmed ✅

Level 1: detect_all (~2s, 0 tokens)
  → Full component detection + identify_current_state
  → matches expected → continue
  → different known state → re-route via find_path
  → unknown state → escalate to Level 2

Level 2: LLM Fallback
  → Return ("fallback", state, step, reason) for LLM to decide
```

## Workflow Lifecycle

### 1. Exploring (First Time)

The agent doesn't know the path. Every click is trial and error:

```python
# Each click records a PENDING transition
click_and_record(app, "Scan", x, y)      # pending: unknown → click:Scan
click_and_record(app, "Run", x, y)        # pending: click:Scan → click:Run

# Workflow succeeded! Commit all transitions
confirm_transitions(app)                   # → saved to transitions.json

# OR workflow failed — discard everything
discard_transitions(app)                   # → nothing saved, graph stays clean
```

### 2. Save Workflow

After full end-to-end success:

```python
save_workflow(app, "smart_cleanup", target_state="s_c8e5f3",
             description="Navigate to cleanup complete page")
```

### 3. Auto Mode (Known Path)

```python
# By name
run_workflow(app, "smart_cleanup")

# By target state directly
execute_workflow(app, "s_c8e5f3")
```

`execute_workflow` flow:
1. **Level 1** detect_all → identify current state
2. `find_path(current, target)` → BFS shortest path
3. For each step:
   - Click component
   - **Level 0**: quick_template_check target defining_components
     - ratio > 0.7 → done ✅
   - **Level 1**: detect_all + identify_current_state
     - matches expected → continue
     - different known state → re-route
   - **Level 2**: return fallback for LLM

## Storage Format

Workflows are stored in `workflows.json` per app (same directory as meta.json):

```json
{
  "check_baggage_fee": {
    "target_state": "s_c8e5f3",
    "description": "Navigate to baggage fee calculator",
    "created_at": "2026-03-23 15:30:00",
    "last_run": "2026-03-23 16:00:00",
    "run_count": 3,
    "success_count": 2,
    "notes": []
  }
}
```

## State Identification

States are matched using **Jaccard similarity** against `defining_components`.

- `identify_current_state()` — pure identification, never creates new states
- `identify_or_create_state()` — identifies OR creates (for exploration mode)
- Filters to **stable components** (seen_count >= 2) to avoid noise

```python
from app_memory import identify_current_state, load_states, load_components

states = load_states(app_dir)
components = load_components(app_dir)
state_id, jaccard = identify_current_state(states, detected_set, components)
```

## Quick Template Check

Fast verification without full detection:

```python
from app_memory import quick_template_check

matched, total, ratio = quick_template_check(app_dir, ["btn_submit", "nav_bar", "logo"], img=screenshot)
if ratio > 0.7:
    print("Target state confirmed")
```

## CLI Commands

```bash
# Run a workflow
python3 scripts/agent.py run_workflow --app "CleanMyMac X" --workflow smart_cleanup

# View workflows
python3 scripts/agent.py workflows --app "CleanMyMac X"

# View all workflows across all apps
python3 scripts/agent.py all_workflows

# View committed transitions (state graph)
python3 scripts/app_memory.py transitions --app "CleanMyMac X"

# View pending (uncommitted) transitions
python3 scripts/app_memory.py pending --app "CleanMyMac X"

# Commit after success
python3 scripts/app_memory.py commit --app "CleanMyMac X"

# Discard after failure
python3 scripts/app_memory.py discard --app "CleanMyMac X"

# Find path between states
python3 scripts/app_memory.py path --app "CleanMyMac X" --component from_state --contact to_state
```

## Return Values

`execute_workflow()` returns one of:

| Result | Meaning |
|---|---|
| `("success", state_id)` | Reached target state |
| `("fallback", state_id, step_idx, reason)` | Need LLM intervention |
| `("error", message)` | Cannot execute (no path, missing state, etc.) |

## Rules

1. **Never save transitions from failed/aborted workflows** — use `discard_transitions()`
2. **Only `confirm_transitions()` after full end-to-end success**
3. **Workflow = target state** — the path is computed at runtime from the graph
4. **Tiered verification** — Level 0 first, only escalate when needed
5. **Re-routing** — if Level 1 finds a different known state, BFS finds a new path
