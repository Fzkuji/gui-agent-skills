# Scenes — Hierarchical Action Modeling

## Core Concepts

```
Scene (场景)
├── Meta Action (子场景/组合动作)
│   ├── Meta Action (更小的子场景)
│   │   ├── Action (原子操作: click, type, screenshot...)
│   │   └── Action
│   └── Action
└── Meta Action
    └── ...
```

- **Scene**: 一个有明确目标的上下文（如 "VPN 重连"、"1Password 取密码"）
- **Meta Action**: 由多个子步骤组成的组合动作，本身也可以被更大的 scene 引用
- **Action**: 不可再分的原子操作（click, type, keystroke, screenshot, AX query...）

## Cross-reference（交叉引用）

一个 scene 可以引用另一个 scene 作为子步骤：
```yaml
- step: Get CityU password
  ref: scenes/1password.yaml#get_password
  params:
    entry: "CityU"
    verify: { username: "zichuanfu2", strength: "Fair" }
```

这样 "VPN 重连" 不需要重复写 "1Password 取密码" 的细节，直接引用即可。

## File Format

每个 scene 是一个 YAML 文件：
```
scenes/
├── README.md          # This file
├── _actions.yaml      # Atomic action catalog
├── vpn-reconnect.yaml # VPN reconnect scene
├── 1password.yaml     # 1Password operations
├── messaging.yaml     # Chat app messaging
└── app-explore.yaml   # New app exploration
```

## Loading Strategy

Agent 处理任务时：
1. 读 SKILL.md 索引 → 确定需要哪个 scene
2. 读对应 scene YAML → 了解整体步骤
3. 遇到 `ref:` 引用 → 按需读子 scene
4. 最底层是 `_actions.yaml` 里的原子操作

不需要一次加载所有 scene。
