# OSWorld Benchmark Results — GUIClaw

> Last updated: 2026-03-23

## Overview

**GUIClaw** is evaluated on [OSWorld](https://github.com/xlang-ai/OSWorld), a real-computer benchmark for multimodal agents with 356 tasks across 10 domains.

## Results Summary

| Domain | Score | Total | Rate | Status |
|--------|-------|-------|------|--------|
| **Chrome** | 43 | 46 | **93.5%** | ✅ Complete |
| GIMP | — | 26 | — | Not tested |
| LibreOffice Calc | — | 47 | — | Not tested |
| LibreOffice Impress | — | 47 | — | Not tested |
| LibreOffice Writer | — | 23 | — | Not tested |
| Multi-app | — | 93 | — | Not tested |
| OS | — | 24 | — | Not tested |
| Thunderbird | — | 15 | — | Not tested |
| VLC | — | 17 | — | Not tested |
| VS Code | — | 22 | — | Not tested |
| **Total** | **43** | **356** | — | 1/10 domains |

> Scoring: ✅ = 1.0, ⚠️ env-change = 1.0, ⚠️ retry = 0.5, ❌ = 0

### Comparison with Leaderboard

Reference scores from the [OSWorld leaderboard](https://os-world.github.io/):

| Rank | Agent | Chrome | Overall | Type |
|------|-------|--------|---------|------|
| 1 | HIPPO Agent w/Opus 4.5 (Lenovo) | 60.4% | 74.5% | Agentic framework |
| 2 | Claude Sonnet 4.6 (Anthropic) | 78.5% | 72.1% | General model |
| — | **GUIClaw** | **93.5%** | TBD | OpenClaw + Claude Opus 4.6 |

## Framework & Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  Mac Host (Apple Silicon)                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  OpenClaw (runtime framework)                   │    │
│  │  └─ Claude Opus 4.6 (LLM reasoning & planning)  │    │
│  │     └─ GUIClaw Skill                            │    │
│  │        ├─ Salesforce/GPA-GUI-Detector (UI det.) │    │
│  │        ├─ Apple Vision OCR (text recognition)   │    │
│  │        └─ pyautogui (action execution)          │    │
│  └─────────────────────────────────────────────────┘    │
│                   HTTP API ↓                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Ubuntu ARM VM (VMware Fusion)                  │    │
│  │  └─ Target apps + OSWorld tasks                 │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

| Component | Role |
|-----------|------|
| **[OpenClaw](https://github.com/openclaw/openclaw)** | Runtime framework — orchestrates the agent, manages tools, routes LLM calls |
| **Claude Opus 4.6** (Anthropic) | LLM backbone — all reasoning, planning, and decision-making |
| **[Salesforce/GPA-GUI-Detector](https://huggingface.co/Salesforce/GPA-GUI-Detector)** | UI element detection (required, cross-platform) |
| **Apple Vision OCR** | Text recognition (optional, Mac-only, graceful degradation) |
| **pyautogui** | Action execution — clicks, types, hotkeys sent to VM via HTTP API |

### Per-Task Workflow

1. **Snapshot restore** → Clean VM state
2. **Config setup** → Launch target app, run task-specific setup
3. **Screenshot** → Download VM screen as PNG to Mac
4. **detect_all()** → GPA-GUI-Detector (required) + OCR (optional) → element positions
5. **LLM reasoning** → Claude decides action based on detection results + visual understanding
6. **Action execution** → pyautogui click/type/hotkey to VM via HTTP API
7. **Repeat 3–6** until task complete
8. **Evaluation** → Run official OSWorld evaluator

## Domain Results

- [Chrome](chrome.md) — 43/46 (93.5%) ✅

## Environment

- **Host**: Mac (Apple Silicon)
- **VM**: Ubuntu ARM (aarch64), VMware Fusion 13.6.4
- **Resolution**: 1920×1080
- **VM API**: HTTP server on port 5000 (screenshot, execute, setup)
