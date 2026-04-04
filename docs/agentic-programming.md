# Agentic Programming Layer

> `gui_harness/` — programmatic interface for GUI automation, powered by [Agentic Programming](https://github.com/Fzkuji/Agentic-Programming).

## Quick Start

### 1. Install

```bash
git clone --recurse-submodules https://github.com/Fzkuji/GUI-Agent-Harness.git
cd GUI-Agent-Harness
pip install -e ./agentic   # install Agentic Programming (submodule)
pip install -e .           # install GUI Agent Harness
```

That's it. If OpenClaw is installed, everything works out of the box.

> **Already cloned without submodules?** Run: `git submodule update --init --recursive`

### 2. Use

```python
from gui_harness import observe, act, verify
from gui_harness.runtime import GUIRuntime

runtime = GUIRuntime()  # auto-detects OpenClaw

# Observe the screen
result = observe(task="find the login button", runtime=runtime)
# → {app_name, page_description, visible_text, target_visible, target_location, ...}

# Click something
result = act(action="click", target="login button", runtime=runtime)
# → {action, target, coordinates, success, screen_changed, ...}

# Verify the result
result = verify(expected="dashboard is visible", runtime=runtime)
# → {expected, actual, verified, evidence, ...}
```

### 3. For VMs (OSWorld)

```python
from gui_harness.primitives.vm_adapter import patch_for_vm
patch_for_vm("http://172.16.105.128:5000")
# Now all primitives route to the VM. Functions work the same.
```

---

## How It Works

```
You (or OpenClaw) call a function
        │
        ▼
  @agentic_function          ← decorator records the call to Context tree
  observe(task="...")
        │
        ├─ screenshot.take()        ← primitive (pure Python)
        ├─ ocr.detect_text()        ← primitive (Apple Vision / EasyOCR)
        ├─ detector.detect_all()    ← primitive (GPA-GUI-Detector)
        │
        └─ runtime.exec(content=[   ← sends data to LLM
             screenshot + OCR data
           ])
        │
        ▼
  LLM analyzes and returns structured JSON
        │
        ▼
  Result stored in Context tree + returned to caller
```

**Key:** Python handles the deterministic parts (screenshot, OCR, detection). The LLM only does reasoning (analyzing what's on screen, deciding where to click).

---

## LLM Provider

`GUIRuntime()` auto-detects the best available provider:

| Priority | Provider | Cost | How |
|----------|----------|------|-----|
| 1 | **OpenClaw** | Free* | `openclaw agent` CLI |
| 2 | **Claude Code** | Subscription | `claude -p` CLI |
| 3 | **Anthropic API** | Per token | `ANTHROPIC_API_KEY` env var |
| 4 | **OpenAI API** | Per token | `OPENAI_API_KEY` env var |

\* Uses your existing OpenClaw configuration.

```python
runtime = GUIRuntime()                        # auto-detect (recommended)
runtime = GUIRuntime(provider="openclaw")     # force OpenClaw
runtime = GUIRuntime(provider="claude-code")  # force Claude Code CLI
runtime = GUIRuntime(provider="anthropic")    # force Anthropic API
runtime = GUIRuntime(provider="openai")       # force OpenAI API
```

**OpenClaw users:** OpenClaw is detected automatically. Each `GUIRuntime()` creates a new OpenClaw session (`--session-id`). The session accumulates context across function calls, so each function only sends its own data.

---

## Context Management

Agentic Programming has two context modes. GUI Harness uses **Session Mode** by default:

### Session Mode (default for OpenClaw)

```python
@agentic_function(summarize={"depth": 0, "siblings": 0})
def observe(task, runtime=None):
    # Only sends THIS call's data to the LLM.
    # OpenClaw session remembers everything from prior calls.
    return runtime.exec(content=[...])
```

- `summarize={"depth": 0, "siblings": 0}` → skip Context tree injection
- The LLM session (OpenClaw/Claude Code) keeps its own conversation history
- No redundant context duplication

### API Mode (for stateless API calls)

```python
@agentic_function  # summarize=None → full context injection
def observe(task, runtime=None):
    # Injects all prior calls' results into the LLM prompt.
    # Needed for stateless API calls (Anthropic/OpenAI).
    return runtime.exec(content=[...])
```

To switch to API mode, remove `summarize={"depth": 0, "siblings": 0}` from the decorators in `gui_harness/functions/`.

---

## All Functions

| Function | LLM? | Decorator | Description |
|----------|-------|-----------|-------------|
| `observe()` | Yes | `summarize={d:0,s:0}` | Screenshot + OCR + detection + LLM analysis |
| `act()` | Yes | `summarize={d:0,s:0}` | Find target + execute click/type |
| `verify()` | Yes | `summarize={d:0,s:0}` | Check if action succeeded |
| `learn()` | Yes | `summarize={d:0,s:0}` | Label UI components |
| `navigate()` | No* | `compress=True` | BFS state graph navigation |
| `remember()` | No | — | Manage visual memory |
| `send_message()` | No* | `compress=True` | observe → navigate → type → verify |
| `read_messages()` | No* | `compress=True` | navigate → observe |

\* Calls other functions internally which call the LLM.

`compress=True` hides internal sub-steps from `summarize()` — callers only see the final result.

---

## File Structure

```
gui_harness/
├── __init__.py              # from gui_harness import observe, act, ...
├── runtime.py               # GUIRuntime (auto-detect provider)
│
├── functions/               # @agentic_function decorated
│   ├── observe.py           # screenshot + OCR + LLM analysis
│   ├── act.py               # find target + execute action
│   ├── verify.py            # verify action result
│   ├── learn.py             # learn app UI components
│   ├── navigate.py          # BFS state graph (compress=True)
│   └── remember.py          # memory management
│
├── tasks/                   # High-level composite tasks
│   ├── send_message.py      # observe → navigate → type → verify
│   └── read_messages.py     # navigate → observe
│
├── primitives/              # Pure Python (no LLM, no decorator)
│   ├── screenshot.py        # → scripts/platform_input
│   ├── ocr.py               # → scripts/ui_detector
│   ├── detector.py          # → scripts/ui_detector
│   ├── input.py             # → scripts/platform_input
│   ├── template_match.py    # → scripts/template_match
│   └── vm_adapter.py        # VM monkey-patch for OSWorld
│
agentic/                     # Bundled Agentic Programming library
```
