---
name: gui-report
description: "Track and report GUI agent task performance — automatic data collection, manual report command."
---

# GUI Task Report

Automatic performance tracking for GUI tasks. Data collection is fully automatic, report generation is one command.

## How It Works

```
detect_all() called     → tracker auto-starts (records token baseline)
GUI functions called     → counters auto-tick (screenshots, clicks, OCR, etc.)
task finished           → run: tracker.py report (saves to log, prints summary)
```

Data collection needs zero manual effort. Only the final `report` command needs to be called.

## Quick Start

```bash
# After a GUI task finishes, generate report:
source ~/gui-actor-env/bin/activate
python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py report

# View history:
python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py history
```

## What's Tracked (all automatic)

| Counter | Auto-ticked by |
|---------|---------------|
| detector_calls | `detect_all()` |
| ocr_calls | `detect_all()` |
| screenshots | `learn_from_screenshot()` |
| learns | `learn_from_screenshot()` |
| clicks | `record_page_transition()` |
| transitions | `record_page_transition()` |
| workflow_level0 | `quick_template_check()` |
| workflow_level1 | `execute_workflow()` Level 1 |
| workflow_level2 | `execute_workflow()` Level 2 |
| workflow_auto_steps | `execute_workflow()` auto mode |
| workflow_explore_steps | `execute_workflow()` explore mode |
| **image_calls** | **manual: `tracker.py tick image_calls`** |

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

📝 记忆变化：
   组件 +12（84 → 96）
   状态 +1（5 → 6）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Failsafe

If `report` is not called, data stays in `.tracker_state.json`. Next time tracker starts (next `detect_all` call), it auto-saves the previous session's data to the log before starting fresh. **Data never lost.**

## Log Storage

`skills/gui-report/logs/task_history.jsonl` — one JSON per completed task.
