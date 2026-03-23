---
name: gui-report
description: "Track and report GUI agent task performance — fully automatic via detect_all auto-start + agent_end hook."
---

# GUI Task Report

Fully automatic performance tracking for GUI tasks.

## How It Works

```
detect_all() called     → tracker auto-starts (if not running)
各函数内部              → counters auto-tick
agent turn ends         → agent_end hook auto-saves report to log
```

**No manual start/report needed.** Everything is automatic.

## What's Tracked

| Counter | Auto-ticked by | Category |
|---------|---------------|----------|
| detector_calls | `detect_all()` | 检测 |
| ocr_calls | `detect_all()` | 检测 |
| screenshots | `learn_from_screenshot()` | 检测 |
| learns | `learn_from_screenshot()` | 记忆 |
| clicks | `record_page_transition()` | 操作 |
| transitions | `record_page_transition()` | 操作 |
| workflow_level0 | `quick_template_check()` | 导航 |
| workflow_level1 | `execute_workflow()` Level 1 | 导航 |
| workflow_level2 | `execute_workflow()` Level 2 | 导航 |
| workflow_auto_steps | `execute_workflow()` auto mode | 导航 |
| workflow_explore_steps | `execute_workflow()` explore mode | 导航 |
| **image_calls** | — | **唯一需手动 tick** |

## Report Output

```
📊 任务报告：chromium/united_com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱ 耗时：2min 35s

💰 Token 消耗：
   总计 +26.8k tokens
   input +3.2k | output +1.8k | cache +21.8k

🔍 检测：
   detect_all 8 次 | OCR 8 次 | LLM 视觉 1 次
   组件总量：96（+12）

🖱 操作：
   点击 5 次 | 状态转移 3 个 | 学习 3 次

🗺 导航效率：
   自动模式 3 步 | 探索模式 2 步
   自动率 60%
   验证分布：L0(模板) 3 | L1(检测) 1 | L2(LLM) 0

📝 记忆变化：
   组件 +12（84 → 96）
   状态 +1（5 → 6）
   转移 +2（3 → 5）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Manual Commands

Usually not needed (everything is automatic), but available:

```bash
TRACKER="python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py"

# View current session stats (without saving)
$TRACKER report

# View history
$TRACKER history

# Manual tick for image_calls
$TRACKER tick image_calls

# Add a note
$TRACKER note "something worth recording"
```

## Log Storage

`skills/gui-report/logs/task_history.jsonl` — one JSON per completed task.

## Plugin: gui-report-hook

The `agent_end` hook lives in `plugins/gui-report-hook/`. It's an OpenClaw plugin that:
1. Listens for `agent_end` lifecycle event
2. Checks if tracker has active data
3. Auto-saves report to log
4. Cleans up tracker state

Installed automatically by `setup.sh` (symlinked to `~/.openclaw/plugins/`).
