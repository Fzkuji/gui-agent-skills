# gui-report 设计文档

> 最后更新：2026-03-24

## 核心设计

**全自动，不依赖 LLM 记得调用任何命令。**

### 三层自动化

1. **auto-start**：`detect_all()` 是所有 GUI 操作的统一入口，首次调用时自动启动 tracker
2. **auto-tick**：各函数内部自动增加对应计数器，LLM 不需要手动 tick（除了 image_calls）
3. **auto-save**：OpenClaw plugin 监听 `agent_end` hook，turn 结束时自动保存 report

### 为什么 image_calls 不能自动 tick

image tool 的调用发生在 LLM 层面（LLM 决定调用 image tool 分析截图），不在 GUIClaw 的 Python 代码层面。代码感知不到 LLM 用了 image tool。所以这是唯一需要手动 tick 的计数器。

### 为什么用 plugin 而不是 skill

Skill 只是 SKILL.md + 脚本，不能注入 OpenClaw 的运行时生命周期。要监听 `agent_end` 事件必须用 plugin，因为 plugin 通过 `api.on("agent_end", ...)` 注册回调。

### agent_end hook 的发现

OpenClaw 文档只列出了 `before_` 系列 hook，但源码中存在完整的生命周期事件：
- `before_model_resolve`, `before_prompt_build`, `before_agent_start`
- **`agent_end`** — agent turn 结束（void, fire-and-forget）
- `llm_input`, `llm_output`
- `before_tool_call`, `after_tool_call`
- `message_received`, `message_sending`, `message_sent`
- `session_start`, `session_end`
- `before_compaction`, `after_compaction`

### Plugin 安装方式

Plugin 源码在 GUIClaw 仓库的 `plugins/gui-report-hook/` 目录。`setup.sh` 自动创建 symlink：

```
~/.openclaw/plugins/gui-report-hook → <GUIClaw>/plugins/gui-report-hook
```

然后在 `openclaw.json` 里启用：

```json
{
  "plugins": {
    "load": { "paths": ["~/.openclaw/plugins/gui-report-hook"] },
    "entries": { "gui-report-hook": { "enabled": true } }
  }
}
```

### 兜底机制

如果 plugin 没装或 hook 没触发：
- tracker 数据保存在 `.tracker_state.json` 里，不会丢
- 下次 `start()` 被调用时（新的 detect_all），自动保存上一轮数据再清理

### Report 输出维度

按用户关心的维度组织，不是原始计数器列表：

1. **⏱ 耗时** — 任务总时间
2. **💰 Token 消耗** — 总量 + input/output/cache 拆分（反映真实成本）
3. **🔍 检测** — detect_all/OCR/LLM 调用次数 + 组件总量变化
4. **🖱 操作** — 点击/转移/学习次数
5. **🗺 导航效率** — 自动 vs 探索步数、自动率（反映 memory 的价值）
6. **📝 记忆变化** — 组件/状态/转移的增减量

### memory snapshot 对比

report 在 start 时记录所有 app/site 的组件/状态/转移数量快照，report 时再读一次，算差值。这样能准确反映"这个任务让 memory 增长了多少"。
