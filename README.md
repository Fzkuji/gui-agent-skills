# 🖥️ GUI Agent — AI-Powered Desktop Automation for macOS

> Let your AI assistant see, click, type, and navigate any macOS app — no dedicated GUI model needed.

GUI Agent turns any LLM with tool-calling into a desktop automation agent. It uses **OCR + template matching + AppleScript** for fast, local element detection, with vision model as a fallback for complex cases. No extra model deployment required.

## ✨ Features

- **🚀 Works with any LLM** — Claude, GPT-4, Gemini, local models. Just needs tool-calling.
- **📱 App-agnostic** — Works with any macOS app out of the box. App profiles for precision.
- **⚡ Fast verification** — 4-level hierarchy from 0.1s (AppleScript) to 5s (vision model). Most actions never need a screenshot.
- **🧩 10 built-in tasks** — Send messages, read screens, click elements, use menus, scroll, and more.
- **🔧 Self-improving** — Template matching learns from first interaction, subsequent uses are instant.
- **🔒 Privacy-first** — Everything runs locally. No screenshots sent to cloud unless you use vision model fallback.

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  Your LLM (Claude, GPT, etc.)  │  Decides what to do next
├─────────────────────────────────┤
│  gui_agent.py                   │  Tasks + atomic actions + observation
├──────────┬──────────┬───────────┤
│ AppleScript │  OCR    │ Template  │  Fast, local, free
│  (0.1s)     │ (1.6s)  │  (1.3s)   │
├──────────┴──────────┴───────────┤
│  Vision Model (fallback, 5-10s) │  Only when needed
└─────────────────────────────────┘
```

**Verification hierarchy** — always use the lightest method that works:

| Level | Method | Speed | Use case |
|-------|--------|-------|----------|
| 1 | AppleScript | ~0.1s | App focused? Window title? |
| 2 | Template match | ~1.3s | Known element appeared? |
| 3 | OCR | ~1.6s | Text visible/gone? |
| 4 | Vision model | ~5-10s | Complex layout judgment |

## 📦 Installation

### Prerequisites

```bash
# macOS only — uses Vision framework, AppleScript, screencapture
# Install cliclick (mouse/keyboard simulation)
brew install cliclick

# Python dependencies
pip install opencv-python-headless numpy
```

### Install as OpenClaw Skill

```bash
# Clone to your skills directory
git clone https://github.com/Fzkuji/gui-agent-skill.git \
  ~/.openclaw/workspace/skills/gui-agent
```

Or manually download and place in any `skills/` directory your agent can access.

### Permissions

On first run, macOS will ask for **Accessibility permissions** for `cliclick` and your terminal app. Click "Allow" once — it persists after that.

## 🚀 Quick Start

### High-level tasks (one command)

```bash
cd path/to/gui-agent

# Send a WeChat message
python3 scripts/gui_agent.py task send_message --app WeChat \
  --param contact="John" --param message="Hey!"

# Read messages from a chat
python3 scripts/gui_agent.py task read_messages --app WeChat \
  --param contact="John"

# Scroll through chat history
python3 scripts/gui_agent.py task scroll_history --app WeChat \
  --param contact="John" --param pages="5"

# Click any element on screen by its text
python3 scripts/gui_agent.py task click_element --app Safari \
  --param text="Downloads"

# Type in a field
python3 scripts/gui_agent.py task type_in_field --app Safari \
  --param field="Search" --param text="hello world" --param submit="true"

# Use menu bar
python3 scripts/gui_agent.py task menu_action --app Safari \
  --param menu="File" --param item="New Tab"

# Discover available menus
python3 scripts/gui_agent.py task list_menus --app Safari
python3 scripts/gui_agent.py task list_menus --app Safari --param menu="File"
```

### Mid-level: Atomic actions (LLM decides)

```bash
# Observe screen state (structured text, not a screenshot)
python3 scripts/gui_agent.py observe --app WeChat

# Execute a single action
python3 scripts/gui_agent.py exec '{"action": "click_ocr", "text": "Settings"}'
python3 scripts/gui_agent.py exec '{"action": "focus_app", "app": "WeChat"}'
python3 scripts/gui_agent.py exec '{"action": "type", "text": "hello"}'
python3 scripts/gui_agent.py exec '{"action": "key", "key": "return"}'

# Find text on screen with coordinates
python3 scripts/gui_agent.py find "Settings"
python3 scripts/gui_agent.py find "Send" --region '{"x_min": 400}'
```

### Template matching (self-improving)

```bash
# Learn a UI element (first time: uses OCR to find coordinates)
python3 scripts/template_match.py save --app WeChat --name search_bar \
  --region 235,187,150,25

# Find it later (instant, ~1.3s)
python3 scripts/template_match.py find --app WeChat --name search_bar

# Click it
python3 scripts/template_match.py click --app WeChat --name search_bar
```

## 📂 All Tasks

```bash
python3 scripts/gui_agent.py tasks
```

| Task | Description | Requires Profile |
|------|-------------|:---:|
| `send_message` | Send a message to a contact/channel | Recommended |
| `read_messages` | Read visible messages in a chat | Recommended |
| `scroll_history` | Scroll up to read older messages | Recommended |
| `open_app` | Open and focus any app | No |
| `read_screen` | OCR all visible text with coordinates | No |
| `click_element` | Find and click by text or template | No |
| `type_in_field` | Click field + type + optional submit | No |
| `menu_action` | Execute menu bar action via AppleScript | No |
| `list_menus` | Discover available menu items | No |
| `scroll` | Scroll in any direction | No |

## 🎯 App Profiles

App profiles in `apps/*.json` define app-specific layout and behavior:

```bash
python3 scripts/gui_agent.py apps
```

**Included profiles:** WeChat, Discord, Telegram

**Apps without profiles work too** — they get sensible defaults (sidebar width 250px, Enter to send, etc.). Profiles just make things more precise.

### Create a new profile

```json
{
  "app": "Slack",
  "process_name": "Slack",
  "layout": {
    "sidebar_width": 260,
    "input_bottom_offset": 60,
    "sidebar_x_max": 360
  },
  "navigation": {
    "method": "sidebar_click",
    "fallback": "search",
    "search_shortcut": {"key": "k", "modifiers": ["command"]}
  },
  "input": {
    "method": "ocr",
    "ocr_keyword": "Message #",
    "fallback": "window_calc"
  },
  "send": {"key": "return"},
  "verify": {"method": "ocr", "region": "main_area"},
  "quirks": ["Cmd+K opens channel switcher"]
}
```

Save as `apps/slack.json` and all tasks work immediately.

## 🤖 Integration with AI Agents

### OpenClaw

This skill is designed for [OpenClaw](https://github.com/openclaw/openclaw). Place it in your skills directory and the agent will automatically use it when asked to interact with desktop apps.

### Other LLM agents

The scripts work standalone. Your agent just needs to:

1. Call `gui_agent.py observe --app X` to see the screen
2. Decide what to do based on the text output
3. Call `gui_agent.py exec '{...}'` or `gui_agent.py task ...` to act
4. Verify with the lightest method available

No vision model needed for most operations — OCR output is structured text with coordinates.

## 📁 Project Structure

```
gui-agent/
├── README.md                # You're reading this
├── SKILL.md                 # Agent instructions (loaded by OpenClaw)
├── apps/                    # App profiles
│   ├── wechat.json
│   ├── discord.json
│   └── telegram.json
├── scripts/
│   ├── gui_agent.py         # Main agent engine
│   ├── template_match.py    # Template learning & matching
│   ├── workflow_runner.py   # Legacy JSON workflow executor
│   ├── ocr_screen.sh        # OCR shell wrapper
│   └── ocr_screen.swift     # macOS Vision OCR
├── templates/               # Auto-generated (gitignored)
│   └── {AppName}/           # Learned UI element templates
└── workflows/               # Legacy declarative workflows
    └── wechat_send_message.json
```

## ⚠️ Limitations

- **macOS only** — Uses Vision framework, AppleScript, screencapture, cliclick
- **Accessibility permissions required** — Prompted on first use
- **OCR can't see everything** — Very faint placeholder text, icons without labels need vision model fallback
- **Retina displays** — Coordinates are in logical pixels (physical ÷ 2). Handled automatically.
- **Some apps have poor Accessibility API** — WeChat exposes only 5 elements. OCR + templates are the workaround.

## 📄 License

MIT

## 🙏 Credits

Built with:
- [cliclick](https://github.com/BlueM/cliclick) — macOS mouse/keyboard automation
- [OpenCV](https://opencv.org/) — Template matching
- Apple Vision Framework — On-device OCR
- [OpenClaw](https://github.com/openclaw/openclaw) — AI agent platform
