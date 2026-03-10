# 🖥️ GUI Agent Skills

> Hierarchical desktop automation for macOS — let any LLM see, click, type, and navigate any app.

A skill pack that models GUI automation as **composable scenes**. Big tasks decompose into sub-scenes, sub-scenes into atomic actions. The LLM agent loads only what it needs, progressively.

## Architecture

```
SKILL.md (index)          ← Agent reads this first (~80 lines)
    │
    ├── scenes/*.yaml     ← Load on demand per task
    │   ├── vpn-reconnect.yaml    (depends on → 1password.yaml)
    │   ├── 1password.yaml
    │   ├── messaging.yaml
    │   ├── app-explore.yaml
    │   └── _actions.yaml         (shared atomic operations)
    │
    ├── docs/core.md      ← General principles & lessons learned
    ├── apps/*.json        ← App-specific UI profiles
    └── scripts/           ← Execution tools
```

### Progressive Disclosure

Each layer only exposes the next layer's **interface**, not its implementation:

```
Level 0: SKILL.md
    "VPN down" → read scenes/vpn-reconnect.yaml

Level 1: vpn-reconnect.yaml
    exports: full_reconnect() → VPN connected
    internally: sso_login → ref: 1password.yaml#get_password

Level 2: 1password.yaml (loaded because referenced)
    exports: get_password(entry, verify) → clipboard
    internally: select_entry → verify_entry → copy_password (click dots)

Level 3: _actions.yaml (loaded when executing)
    click(x, y), paste(), ax_scan(app), screenshot(path)...
```

### Scene Composition

Scenes reference each other via `ref:`:

```yaml
# In vpn-reconnect.yaml
- ref: "scenes/1password.yaml#get_password"
  params:
    entry: "CityU"
    verify: { username: "zichuanfu2", strength: "Fair" }
```

This means "VPN reconnect" doesn't duplicate "get password" logic — it just calls it.

## Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Scene** | A goal-oriented context with clear entry/exit | "Reconnect VPN", "Send WeChat message" |
| **Meta Action** | A composed step within a scene; can reference sub-scenes | "SSO Login" = Next + get_password + enter_password |
| **Action** | Atomic, indivisible operation | click(x,y), type("hello"), ax_scan("App") |
| **Export** | A scene's public interface (params → output) | get_password(entry, verify) → clipboard |
| **Ref** | Cross-scene reference | `ref: scenes/1password.yaml#get_password` |

## Quick Start

### For LLM agents (OpenClaw)

The agent reads `SKILL.md` to find the right scene, then follows it:

```
1. Read SKILL.md → identify scene
2. Read the scene YAML → understand steps
3. Follow refs to sub-scenes as needed
4. Execute atomic actions via scripts/tools
```

### For direct CLI use

```bash
# High-level tasks
python3 scripts/gui_agent.py task send_message --app WeChat \
  --param contact="John" --param message="hi"

# Observe
python3 scripts/gui_agent.py observe --app WeChat
python3 scripts/gui_agent.py find "keyword"

# Atomic actions
python3 scripts/gui_agent.py exec '{"action": "click_ocr", "text": "Settings"}'

# List all tasks
python3 scripts/gui_agent.py tasks
```

## Scenes

| Scene | File | Goal | Dependencies |
|-------|------|------|-------------|
| **Atomic Actions** | `scenes/_actions.yaml` | Shared primitives (click, type, AX, OCR...) | None |
| **1Password** | `scenes/1password.yaml` | Copy credentials to clipboard | _actions |
| **VPN Reconnect** | `scenes/vpn-reconnect.yaml` | Restore GlobalProtect VPN | 1password |
| **Messaging** | `scenes/messaging.yaml` | Send/read in chat apps | _actions |
| **App Exploration** | `scenes/app-explore.yaml` | Map unfamiliar app UI | _actions |

### Adding a new scene

1. Create `scenes/your-scene.yaml`
2. Define `exports:` (public interface)
3. Define `meta_actions:` (internal steps)
4. Reference `_actions.yaml` for atomic ops, or other scenes via `ref:`
5. Add entry to SKILL.md index table

## App Profiles

App-specific configs in `apps/*.json`:

| App | AX Quality | Navigation | Notes |
|-----|-----------|------------|-------|
| WeChat | Poor (5) | Sidebar OCR | No Cmd+F, faint placeholder |
| Discord | Excellent (1362) | Cmd+K switcher | AX-first strategy |
| Telegram | Good | Cmd+F search | Standard |
| GlobalProtect | WebView | AX + cliclick | osascript doesn't work in WebView |

## Prerequisites

- **macOS** with Accessibility permissions
- `brew install cliclick`
- `pip install opencv-python-headless numpy`
- Python venv recommended: `~/scrapling-env/`

## File Structure

```
gui-agent/
├── SKILL.md              # Agent index (~80 lines)
├── README.md             # This file
├── scenes/               # Hierarchical scene definitions
│   ├── README.md         # Scene system documentation
│   ├── _actions.yaml     # Atomic action catalog (shared)
│   ├── 1password.yaml    # Credential retrieval
│   ├── vpn-reconnect.yaml
│   ├── messaging.yaml
│   └── app-explore.yaml
├── docs/
│   └── core.md           # Core principles & hard-won lessons
├── apps/                 # App UI profiles (JSON)
│   ├── wechat.json
│   ├── discord.json
│   ├── telegram.json
│   └── globalprotect.json
├── scripts/              # Execution tools
│   ├── gui_agent.py      # Main engine (observe/exec/task/find)
│   ├── template_match.py # Template learning & matching
│   ├── ocr_screen.sh     # OCR shell wrapper
│   └── ocr_screen.swift  # macOS Vision OCR
└── _legacy/              # Archived old implementations
```

## License

MIT
