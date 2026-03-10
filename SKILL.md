---
name: gui-agent
description: "Control desktop GUI applications on macOS using Accessibility API, OCR, and cliclick. Use when asked to operate, click, type, or interact with any desktop application. NOT for web-only tasks (use browser tool) or simple file operations."
---

# GUI Agent Skill

You ARE the agent loop: Observe → Decide → Act → Verify.

## When to use this skill

- Operating any macOS desktop app (click, type, navigate)
- Automating multi-step GUI workflows (VPN login, messaging, form filling)
- Reading screen content when browser tool can't access it

## Available Workflows

Read the specific workflow doc you need — don't load all of them.

| Workflow | File | Use when |
|----------|------|----------|
| **Core Principles** | `docs/core.md` | First time using GUI agent, or need a refresher on tools/techniques |
| **VPN Reconnect** | `docs/vpn-reconnect.md` | GlobalProtect VPN disconnected, need to re-authenticate via SSO |
| **App Messaging** | `docs/messaging.md` | Send/read messages in WeChat, Discord, Telegram |
| **App Exploration** | `docs/app-explore.md` | Encountering a new app for the first time |
| **1Password** | `docs/1password.md` | Need to retrieve credentials from 1Password GUI |

## Quick Decision Tree

```
Need to click/type in a desktop app?
  → Read docs/core.md for tools & principles

VPN down?
  → Read docs/vpn-reconnect.md

Send/read messages in chat app?
  → Read docs/messaging.md

New app, don't know the UI?
  → Read docs/app-explore.md

Need a password from 1Password?
  → Read docs/1password.md
```

## File Structure
```
gui-agent/
├── SKILL.md              # This index (load first)
├── docs/                 # Workflow docs (load on demand)
│   ├── core.md           # Core principles, tools, lessons learned
│   ├── vpn-reconnect.md  # GlobalProtect VPN reconnect
│   ├── messaging.md      # Chat app messaging
│   ├── app-explore.md    # Exploring new apps
│   └── 1password.md      # 1Password credential retrieval
├── apps/                 # App profiles (JSON)
├── scripts/              # Automation scripts
└── README.md             # Human documentation
```
