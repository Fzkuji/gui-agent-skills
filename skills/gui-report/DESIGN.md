# gui-report 设计文档

> 最后更新：2026-03-24

## 设计原则

**数据收集全自动，报告生成一个命令。**

## 架构

```
detect_all()  ──→ auto-start tracker（首次调用时）
                  auto-tick detector_calls, ocr_calls
                  
learn_from_screenshot() ──→ auto-tick screenshots, learns
                            update task name（app/domain）

record_page_transition() ──→ auto-tick clicks, transitions

quick_template_check() ──→ auto-tick workflow_level0

execute_workflow() ──→ auto-tick workflow_level1/2, auto/explore_steps

tracker.py report ──→ 读取 token delta + memory snapshot delta
                      输出格式化报告
                      保存到 logs/task_history.jsonl
                      清理 .tracker_state.json
```

## 为什么 detect_all 是 auto-start 的入口

detect_all() 是所有 GUI 操作的统一检测入口。任何 GUI 任务必然调用 detect_all，所以在这里 auto-start 保证 tracker 一定会启动。

## 为什么 image_calls 不能自动

image tool 在 LLM 层面调用（LLM 决定发截图给视觉模型分析），Python 代码层感知不到。所以是唯一需要手动 tick 的计数器。实际上即使不 tick 也不影响其他数据的准确性。

## Report 输出维度

按用户关心的维度组织：

1. **⏱ 耗时** — 从 tracker start 到 report 的时间
2. **💰 Token 消耗** — 从 sessions.json 读取 start/end token 差值，拆分 input/output/cache
3. **🔍 检测** — detect_all 调用次数 + 组件总量变化
4. **🖱 操作** — 点击/转移/学习次数
5. **🗺 导航效率** — 自动 vs 探索步数，自动率反映 memory 的价值
6. **📝 记忆变化** — 组件/状态/转移的增减量（start 时快照 vs report 时快照）

## 兜底机制

如果 LLM 忘了调 report：
- `.tracker_state.json` 保留，数据不丢
- 下次 detect_all 触发 auto-start 时，检测到旧 state 文件
- 自动保存旧 session 数据到 log，再开始新 session

## 被废弃的方案

### OpenClaw Plugin（agent_end hook）

尝试过写 OpenClaw plugin 监听 `agent_end` 生命周期事件自动 report。技术上可行（`agent_end` hook 存在），但：
- plugin 重载依赖 gateway 重启
- 调试过程中多次重启导致 gateway 不稳定
- `api.runtime.channel` 没有直接发消息给用户的简单方法
- 最终决定：不值得为一个 `tracker.py report` 命令引入 plugin 复杂度

### 相关发现

OpenClaw 内部有丰富的生命周期 hook（文档未全列出）：
- `agent_end` — turn 结束
- `message_sending` — 可修改 LLM 回复内容
- `api.runtime.channel` — 有 text/reply/routing/discord/telegram 等子对象
- `api.runtime.system.enqueueSystemEvent` — 可注入系统事件

这些 API 未来如果文档更完善，plugin 方案可以重新考虑。
