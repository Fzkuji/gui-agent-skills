---
name: gui-agent
description: "Visually operate any application on macOS — native apps, browsers, or anything with a GUI window. Open apps, click buttons, type text, send messages, fill forms, navigate menus, all driven by visual UI detection. Use when the task requires interacting with what's on screen."
---

# GUI Agent Skill

You ARE the agent loop. Every GUI task follows this flow, in order:

```
INTENT MATCH → OBSERVE → ENSURE APP READY → ACT → VERIFY → SAVE WORKFLOW → REPORT
```

## Sub-Skills

Each step has detailed instructions in its own skill file:

| Step | Skill | When to read |
|------|-------|-------------|
| **Observe** | `skills/gui-observe/SKILL.md` | Before any action — screenshot, OCR, identify state |
| **Learn** | `skills/gui-learn/SKILL.md` | App not in memory, or match rate < 80% |
| **Act** | `skills/gui-act/SKILL.md` | Clicking, typing, sending messages, waiting for UI |
| **Memory** | `skills/gui-memory/SKILL.md` | Visual memory — profiles, components, pages, CRUD, cleanup |
| **Workflow** | `skills/gui-workflow/SKILL.md` | Intent matching, saving/replaying workflows, meta-workflows |
| **Setup** | `skills/gui-setup/SKILL.md` | First-time setup on a new machine |

Read the relevant sub-skill when you reach that step. You don't need to read all of them upfront.

## agent.py — Unified Entry Point

**All GUI operations go through `scripts/agent.py`.** Do not call `app_memory.py` or `gui_agent.py` directly.

```bash
source ~/gui-agent-env/bin/activate

# Core operations
python3 scripts/agent.py open --app AppName
python3 scripts/agent.py learn --app AppName
python3 scripts/agent.py detect --app AppName
python3 scripts/agent.py click --app AppName --component ButtonName
python3 scripts/agent.py list --app AppName
python3 scripts/agent.py read_screen --app AppName
python3 scripts/agent.py wait_for --app AppName --component X
python3 scripts/agent.py cleanup --app AppName
python3 scripts/agent.py navigate --url "https://example.com"
python3 scripts/agent.py workflows --app AppName
python3 scripts/agent.py all_workflows

# Messaging
python3 scripts/agent.py send_message --app WeChat --contact "小明" --message "明天见"
python3 scripts/agent.py read_messages --app WeChat --contact "小明"
```

agent.py automatically handles:
- New app → learn → plan
- Known app → eval (template match; ≥80% proceed, <80% re-learn)
- Error → re-learn + new plan
- Chinese aliases: 微信→WeChat, 浏览器→Chrome

## Execution Flow

### STEP -1: INTENT MATCHING
→ Details: `skills/gui-workflow/SKILL.md`

Match user request to saved workflows before doing anything. If matched, use workflow steps as plan. If not, proceed and save after success.

### STEP 0: OBSERVE
→ Details: `skills/gui-observe/SKILL.md`

Screenshot, identify current state. Record `session_status` for token reporting.

### STEP 1: ENSURE APP READY
→ Details: `skills/gui-learn/SKILL.md`

Check if app is in memory. If not → learn. If match rate < 80% → re-learn. This is YOUR responsibility — do not wait for the user.

### STEP 2: LEARN (when needed)
→ Details: `skills/gui-learn/SKILL.md`

Detect all components (YOLO + OCR), identify them, filter, save to memory. Privacy check: delete personal info.

### STEP 3: ACT
→ Details: `skills/gui-act/SKILL.md`

Execute clicks, typing, sending. Pre-verify before every click. Pre-verify contact before every message send.

### STEP 4: POST-ACTION VERIFY
→ Details: `skills/gui-act/SKILL.md`

Screenshot after every action. Did the expected change happen? If not → re-observe.

### STEP 5: SAVE WORKFLOW
→ Details: `skills/gui-workflow/SKILL.md`

Save successful multi-step sequences for future replay.

### STEP 6: REPORT

Every GUI task ends with a report:
```
⏱ 45.2s | 📊 +10k tokens (85k→95k) | 🔧 3 screenshots, 2 clicks, 1 learn
```
Compare `session_status` from STEP 0 vs now.

---

## Key Principles

1. **Vision-driven, no shortcuts** — every GUI interaction goes through the visual pipeline (screenshot → detect → match → click). Do not use system commands (`open <url>`, `osascript tell app to set URL`, CLI tools) to manipulate app state. Only allowed: `activate` (bring window to front), `screencapture` (take screenshot), `platform_input.py` (click/type via pynput after visual detection provides coordinates). **Screenshot before AND after every click.**
2. **Template match is the ONLY way to get click coordinates** — use `click_component` or `match_on_fullscreen` from `app_memory.py`. These match saved component images on full-screen screenshots and return precise screen coordinates.
3. **NEVER use `image` tool to estimate coordinates** — the `image` tool (vision model) analyzes screenshots for understanding (what's on screen, what state, what happened). It does NOT provide reliable pixel coordinates. If you need to click something, it MUST have a saved template. If no template exists → learn the app first.
4. **For dynamic content (search results, lists, popups)**: take screenshot → use `image` tool to UNDERSTAND what's there → crop the relevant region → use `image` tool on crop to identify exact position within crop → calculate screen coordinates from crop bounds. Or better: learn the dynamic state to save templates.
5. **Paste > Type** for CJK text and special chars
6. **Learn incrementally** — save new components after each interaction
7. **Integer coordinates only** — pynput uses logical screen coordinates (integers)
8. **Learn once, match forever** — UI positions are stable unless app updates

## Safety Rules

These exist because of real bugs:

1. **Verify before sending** — screenshot chat header, use `image` tool to confirm correct contact name
2. **Every click gets before/after screenshots** — `click_component` does this automatically; manual clicks must do it explicitly
3. **No wrong-app learning** — validate frontmost app before learn
4. **Reject tiny templates** — <30×30 pixels produce false matches
5. **Vision model never provides click coordinates** — only template matching provides coordinates. Vision model provides understanding.
6. **Never send screenshots to conversation** — internal detection only
7. **If click has no effect** — screenshot, analyze what happened, don't repeat blindly. Possible causes: wrong app in front, window moved, click outside window, element not interactive.

## Memory System
→ Details: `skills/gui-memory/SKILL.md`

Visual memory stores app profiles, components, page fingerprints, workflows. See gui-memory for directory structure, profile schema, CRUD operations, and cleanup rules.

## File Structure

```
gui-agent/
├── SKILL.md              # This file (main orchestrator)
├── skills/               # Sub-skills (read on demand)
│   ├── gui-observe/SKILL.md
│   ├── gui-learn/SKILL.md
│   ├── gui-act/SKILL.md
│   ├── gui-memory/SKILL.md
│   ├── gui-workflow/SKILL.md
│   └── gui-setup/SKILL.md
├── scripts/              # Core scripts
│   ├── agent.py, ui_detector.py, app_memory.py, gui_agent.py, template_match.py
├── memory/               # Visual memory (gitignored)
│   ├── apps/<appname>/
│   └── meta_workflows/
├── actions/              # Atomic operations
├── docs/
└── README.md
```
