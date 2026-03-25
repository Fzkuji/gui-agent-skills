<div align="center">
  <img src="../assets/banner.png" alt="GUIClaw" width="100%" />

  <h1>🦞 GUIClaw</h1>

  <p>
    <strong>看见屏幕。学会按钮。精准点击。</strong>
    <br />
    基于视觉的桌面自动化技能，构建于 <a href="https://github.com/openclaw/openclaw">OpenClaw</a> 之上。
    <br />
    <em>需要 OpenClaw 作为运行时 — 不是独立的 API 或库。</em>
  </p>

  <p>
    <a href="#-快速开始"><img src="https://img.shields.io/badge/快速开始-blue?style=for-the-badge" /></a>
    <a href="https://github.com/openclaw/openclaw"><img src="https://img.shields.io/badge/🦞_OpenClaw-red?style=for-the-badge" /></a>
    <a href="https://discord.gg/BQbUmVuD"><img src="https://img.shields.io/badge/Discord-7289da?style=for-the-badge&logo=discord&logoColor=white" /></a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/平台-macOS_Apple_Silicon-black?logo=apple" />
    <img src="https://img.shields.io/badge/检测-GPA_GUI_Detector-green" />
    <img src="https://img.shields.io/badge/OCR-Apple_Vision-blue" />
    <img src="https://img.shields.io/badge/License-MIT-yellow" />
  </p>
</div>

---

<p align="center">
  <a href="../README.md">🇺🇸 English</a> ·
  <b>🇨🇳 中文</b>
</p>

---

## 🔥 更新日志

- **[2026-03-24]** 📐 **坐标系统重构** — 双空间模型（检测空间 vs 点击空间），每次 `detect_all()` 调用时通过 `refresh_screen_info()` 动态计算 scale。不再硬编码 Retina ÷2。
- **[2026-03-24]** 🧠 **智能工作流导航** — 目标状态分层验证（template match → 全量检测 → LLM 回退）。通过 `detect_all` 自动跟踪性能。
- **[2026-03-23]** 🏆 **OSWorld 基准测试：93.5%** — 46 个 Chrome 任务通过 45.0 个。[查看结果 →](../benchmarks/osworld/)
- **[2026-03-23]** 🔄 **记忆系统重构** — 拆分存储、组件自动遗忘（连续 15 次未命中 → 删除）、基于 Jaccard 相似度的状态合并。
- **[2026-03-22]** 🔍 **统一检测管线** — `detect_all()` 作为单一入口；原子化的 检测 → 匹配 → 执行 → 验证 循环。
- **[2026-03-21]** 🌐 **跨平台支持** — GPA-GUI-Detector 可处理任意 OS 截图（Linux VM、远程服务器等）。
- **[2026-03-10]** 🚀 **初始发布** — GPA-GUI-Detector + Apple Vision OCR + 模板匹配 + 应用视觉记忆。

## 💬 使用效果

> **你**："用微信给小明发消息说明天见"

```
OBSERVE  → 截屏，识别当前状态
           ├── 当前应用：访达（不是微信）
           └── 需要切换到微信

STATE    → 检查微信记忆
           ├── 之前学过？是（24 个组件）
           ├── OCR 可见文字：["聊天", "通讯录", "收藏", "搜索", ...]
           ├── 状态识别："initial"（89% 匹配）
           └── 当前状态可用组件：18 个 → 用这些做匹配

NAVIGATE → 查找联系人"小明"
           ├── 模板匹配 search_bar → 找到（conf=0.96）→ 点击
           ├── 粘贴"小明"（剪贴板 → Cmd+V）
           ├── OCR 搜索结果 → 找到 → 点击
           └── 新状态："click:小明"（聊天窗口打开）

VERIFY   → 确认打开了正确的聊天
           ├── OCR 聊天标题 → "小明" ✅
           └── 不对？→ 中止

ACT      → 发送消息
           ├── 点击输入框（模板匹配）
           ├── 粘贴"明天见"（剪贴板 → Cmd+V）
           └── 按回车

CONFIRM  → 验证消息已发送
           ├── OCR 聊天区域 → "明天见" 可见 ✅
           └── 完成
```

<details>
<summary>📖 更多示例</summary>

### "帮我扫描一下电脑有没有恶意软件"

```
OBSERVE  → 截屏 → CleanMyMac X 不在前台 → 激活
           ├── 获取主窗口边界（选最大窗口，跳过状态栏面板）
           └── OCR 识别当前状态

STATE    → 检查 CleanMyMac X 记忆
           ├── OCR 可见文字：["Smart Scan", "Malware Removal", "Privacy", ...]
           ├── 状态识别："initial"（92% 匹配）
           └── 可匹配组件：21 个

NAVIGATE → 点击侧边栏 "Malware Removal"
           ├── 在窗口内查找元素（精确匹配，窗口边界过滤）
           ├── 点击 → 新状态："click:Malware_Removal"
           └── OCR 确认新状态（87% 匹配）

ACT      → 点击 "Scan" 按钮
           ├── 查找 "Scan"（精确匹配，选底部位置 — 避免匹配到 "Deep Scan"）
           └── 点击 → 扫描开始

POLL     → 等待完成（事件驱动，无固定休眠）
           ├── 每 2 秒：截屏 → OCR 检查 "No threats"
           └── 找到目标 → 立即继续

CONFIRM  → "No threats found" ✅
```

### "看看我的 GPU 训练还在跑吗"

```
OBSERVE  → 截屏 → Chrome 已打开
           └── 识别目标：JupyterLab 标签页

NAVIGATE → 找到 JupyterLab 标签
           ├── OCR 标签栏或使用书签
           └── 点击切换

EXPLORE  → 多个终端标签可见
           ├── 截屏终端区域
           ├── LLM 视觉分析 → 识别 nvitop 所在标签
           └── 点击正确的标签

READ     → 截屏终端内容
           ├── LLM 读取 GPU 使用率表格
           └── 报告："8 块 GPU，7 块 100% — 实验正在运行" ✅
```

### "用活动监视器杀掉 GlobalProtect"

```
OBSERVE  → 截屏当前状态
           └── GlobalProtect 和活动监视器都不在前台

ACT      → 启动两个应用
           ├── open -a "GlobalProtect"
           └── open -a "Activity Monitor"

EXPLORE  → 截屏活动监视器窗口
           ├── LLM 视觉 → "网络标签页活跃，右上角搜索框为空"
           └── 决定：先点击搜索框

ACT      → 搜索进程
           ├── 点击搜索框（根据探索结果定位）
           ├── 粘贴 "GlobalProtect"（剪贴板 → Cmd+V，绝不用 cliclick 输入）
           └── 等待过滤结果

VERIFY   → 进程列表中找到目标 → 选中

ACT      → 结束进程
           ├── 点击工具栏的停止按钮 (X)
           └── 确认对话框弹出

VERIFY   → 点击 "Force Quit"

CONFIRM  → 截屏 → 进程列表为空 → 已终止 ✅
```

</details>

## ⚠️ 前置要求

GUIClaw 是一个 **OpenClaw 技能** — 它运行在 [OpenClaw](https://github.com/openclaw/openclaw) 内部，利用 OpenClaw 的 LLM 编排来推理 UI 操作。它**不是**独立的 API、命令行工具或 Python 库。你需要：

1. **[OpenClaw](https://github.com/openclaw/openclaw)** 已安装并运行
2. **macOS + Apple Silicon**（用于 GPA-GUI-Detector 和 Apple Vision OCR）
3. **辅助功能权限** 已授予 OpenClaw / Terminal

LLM（Claude、GPT 等）由 OpenClaw 配置提供 — GUIClaw 本身不直接调用任何外部 API。

## 🚀 快速开始

**1. 克隆并安装**
```bash
git clone https://github.com/Fzkuji/GUIClaw.git
cd GUIClaw
bash scripts/setup.sh
```

**2. 授予辅助功能权限**

系统设置 → 隐私与安全性 → 辅助功能 → 添加 Terminal / OpenClaw

**3. 配置 OpenClaw**

在 `~/.openclaw/openclaw.json` 中添加：
```json
{
  "skills": { "entries": { "gui-agent": { "enabled": true } } },
  "tools": { "exec": { "timeoutSec": 300 } },
  "messages": { "queue": { "mode": "interrupt" } }
}
```

> ⚠️ **`timeoutSec: 300`** 很重要 — GUIClaw 的操作链（截屏 → 检测 → 点击 → 等待 → 验证）可能较长，推荐 5 分钟超时。默认超时太短会中途终止命令。

> 💡 **`queue.mode: "interrupt"`** 推荐启用 — GUI 操作耗时较长，interrupt 模式允许你发送任意消息立即中止当前智能体操作。否则消息会排队，智能体完成当前动作后才能看到。

然后直接和你的 OpenClaw 智能体对话 — 它会自动读取 `SKILL.md` 并处理一切。

## 🧠 工作原理

<p align="center">
  <img src="../assets/architecture.png" alt="GUIClaw 架构图" width="700" />
</p>

架构分为三层：

- **编排层** — `SKILL.md` 路由到子技能（`gui-observe`、`gui-act`、`gui-learn`、`gui-memory`、`gui-workflow`）。每一步都强制执行安全协议（INTENT → OBSERVE → VERIFY → ACT → CONFIRM → REPORT）。
- **核心脚本** — `agent.py` 是统一入口。`app_memory.py` 处理视觉记忆（学习、检测、匹配、验证）。`ui_detector.py` 运行 GPA-GUI-Detector (YOLO) + Apple Vision OCR。
- **记忆层** — 拆分存储：每个应用/站点维护 `components.json`、`states.json`、`transitions.json`。组件在连续未命中后自动遗忘，状态基于 Jaccard 相似度自动合并。

### 检测引擎

| 检测器 | 速度 | 检测内容 |
|--------|------|----------|
| **[GPA-GUI-Detector](https://huggingface.co/Salesforce/GPA-GUI-Detector)** | ~0.3s | 图标、按钮、输入框 |
| **Apple Vision OCR** | ~1.6s | 文字元素（中英文） |
| **模板匹配** | ~0.3s | 已知组件（首次学习后） |

## 📁 应用视觉记忆

每个应用拥有独立的视觉记忆，采用**点击图状态模型**。
浏览器比较特殊 — 它承载多个网站，因此每个网站都有独立的**嵌套记忆**，结构与普通应用完全相同。

```
memory/apps/
├── wechat/
│   ├── meta.json                 # 元数据（detect_count, forget_threshold）
│   ├── components.json           # 组件注册表 + 活跃度追踪
│   ├── states.json               # 状态（由组件集合定义）
│   ├── transitions.json          # 状态转移（字典结构，去重）
│   ├── components/               # 裁切的 UI 元素图片
│   │   ├── search_bar.png
│   │   ├── emoji_button.png
│   │   └── ...
│   ├── workflows/                # 保存的任务序列
│   │   └── send_message.json
│   └── pages/
│       └── main_annotated.jpg
├── cleanmymac_x/
│   ├── meta.json
│   ├── components.json
│   ├── states.json
│   ├── transitions.json
│   ├── components/
│   ├── workflows/
│   │   └── smart_scan_cleanup.json
│   └── pages/
├── claude/
│   ├── meta.json
│   ├── components.json
│   ├── states.json
│   ├── transitions.json
│   ├── components/
│   ├── workflows/
│   │   └── check_usage.json
│   └── pages/
└── chromium/
    ├── meta.json                 # 浏览器级元数据
    ├── components.json           # 浏览器 UI 组件（工具栏、设置）
    ├── states.json
    ├── transitions.json
    ├── components/               # 浏览器 UI 元素模板
    ├── pages/
    └── sites/                    # ⭐ 每个网站的记忆（结构与普通应用相同）
        ├── united.com/
        │   ├── meta.json
        │   ├── components.json   # 网站 UI：导航栏、表单、链接
        │   ├── states.json
        │   ├── transitions.json
        │   ├── components/       # 网站特定的裁切 UI 元素
        │   └── pages/            # 页面截图
        ├── delta.com/
        │   ├── meta.json
        │   ├── components.json
        │   ├── states.json
        │   ├── transitions.json
        │   ├── components/
        │   └── pages/
        └── amazon.com/
            ├── meta.json
            ├── components.json
            ├── states.json
            ├── transitions.json
            ├── components/
            └── pages/
```

### 点击图（Click Graph）

UI 被建模为**状态图**。每个状态由 `defining_components` 集合定义 — 即屏幕上检测到的组件集合。状态匹配使用当前屏幕组件与已保存状态定义集合之间的 **Jaccard 相似度**。

**components.json 结构：**
```json
{
  "Search": {
    "type": "icon",
    "rel_x": 115, "rel_y": 143,
    "icon_file": "components/Search.png",
    "last_seen": "2026-03-24T01:30:00",
    "seen_count": 12,
    "consecutive_misses": 0
  },
  "Settings": {
    "type": "icon",
    "rel_x": 63, "rel_y": 523,
    "icon_file": "components/Settings.png",
    "last_seen": "2026-03-24T01:30:00",
    "seen_count": 8,
    "consecutive_misses": 2
  }
}
```

**states.json 结构：**
```json
{
  "state_0": {
    "defining_components": ["Chat_tab", "Cowork_tab", "Code_tab", "Search", "Ideas"],
    "description": "Main app view when first opened"
  },
  "state_1": {
    "defining_components": ["Chat_tab", "Account", "Billing", "Usage", "General"],
    "description": "Settings page"
  },
  "state_2": {
    "defining_components": ["Chat_tab", "Account", "Billing", "Usage", "Developer"],
    "description": "Settings > Usage tab"
  }
}
```

**工作方式：**
1. **状态 = 组件集合** — 每个状态由当前可见的组件（`defining_components`）定义
2. **Jaccard 匹配** — 当前屏幕检测到的组件与各状态对比：`|A ∩ B| / |A ∪ B|`
3. **匹配阈值 > 0.7** — 识别当前状态
4. **合并阈值 > 0.85** — 新状态与已有状态过于相似时，自动合并
5. **组件属于状态** — 一个组件可以出现在多个状态中（如 `Chat_tab` 同时在 `state_0`、`state_1`、`state_2`）
6. **匹配是状态相关的** — 只匹配属于当前识别状态的组件

**组件自动遗忘：**
- 每个组件追踪 `last_seen`、`seen_count` 和 `consecutive_misses`
- 当组件连续 **15 次 detect_all 运行**未被检测到时，自动删除
- 随着应用 UI 更新，记忆自动保持精简

**为什么这样设计：**
- 无需预定义"页面"或"区域" — 状态通过交互自动发现
- 状态识别速度快（Jaccard 组件集合匹配，无需视觉模型）
- 相似状态自动合并，防止状态爆炸
- 过时组件自动遗忘，保持记忆精简
- 自然处理弹窗、覆盖层、嵌套导航
- 可扩展到具有复杂 UI 状态的应用

## 🔄 工作流记忆

完成的任务会被保存为可复用的工作流。下次收到类似请求时，智能体自动进行语义匹配。

```
memory/apps/cleanmymac_x/workflows/smart_scan_cleanup.json
memory/apps/claude/workflows/check_usage.json
```

**匹配机制：**
1. 用户说"帮我清理一下电脑" / "scan my Mac" / "run CleanMyMac"
2. 智能体列出目标应用的已保存工作流
3. **LLM 语义匹配**（不是字符串匹配）— 智能体本身就是 LLM
4. 匹配成功 → 加载工作流步骤，观察当前状态，从正确步骤恢复
5. 没有匹配 → 正常操作，成功后保存新工作流

**分层验证（Workflow v2）：**

每个工作流步骤采用分层验证 — 先执行快速检查，必要时才使用昂贵方法：

| 层级 | 方法 | 速度 | 使用场景 |
|------|------|------|----------|
| **Level 0** | `quick_template_check` — 模板匹配目标组件 | ~0.3s | 默认首选检查 |
| **Level 1** | `detect_all` + `identify_current_state` — 全量检测 | ~2s | Level 0 失败或有歧义 |
| **Level 2** | LLM 视觉回退 | ~5s+ | Level 1 无法确定状态 |

**执行模式：**
- **Auto 模式** — 按已保存的工作流步骤执行，每步使用分层验证
- **Explore 模式** — 无已保存工作流；智能体交互式发现步骤，成功后保存

**`execute_workflow()` 返回值：**
- `success` — 所有步骤完成并验证通过
- `fallback` — 工作流偏离，回退到 Explore 模式
- `error` — 不可恢复的错误

**工作流示例** (`smart_scan_cleanup.json`)：
```json
{
  "steps": [
    {"action": "open", "target": "CleanMyMac X"},
    {"action": "observe", "note": "check current state"},
    {"action": "click", "target": "Scan"},
    {"action": "wait_for", "target": "Run", "timeout": 120},
    {"action": "click", "target": "Run"},
    {"action": "wait_for", "target": "Ignore", "timeout": 30},
    {"action": "click", "target": "Ignore", "condition": "only if quit dialog appeared"}
  ]
}
```

**`wait_for` — 异步 UI 轮询：**
```bash
python3 agent.py wait_for --app "CleanMyMac X" --component Run
# ⏳ Waiting for 'Run' (timeout=120s, poll=10s)...
# ✅ Found 'Run' at (855,802) conf=0.98 after 45.2s (5 polls)
```
- 每 10 秒模板匹配（单次约 0.3 秒）
- 超时 → 保存截图供检查，**绝不盲点**

## 🔴 视觉 vs 命令

GUIClaw 用视觉检测做**决策**，用最高效的方式做**执行**：

| | 必须基于视觉 | 可以用键盘/命令 |
|---|---|---|
| **什么** | 判断状态、定位元素、验证结果 | 快捷键（Ctrl+L）、文字输入、系统命令 |
| **为什么** | Agent 必须先看到屏幕再行动 | 执行可以用最快的方式 |
| **原则** | **决策 = 视觉，执行 = 最佳工具** | |

### 三种视觉方法

| 方法 | 返回 | 用途 |
|------|------|------|
| **OCR** (`detect_text`) | 文字 + 坐标 ✅ | 找文字标签、链接、菜单项 |
| **GPA-GUI-Detector** (`detect_icons`) | 边界框 + 坐标 ✅（无标签） | 找图标、按钮、非文字元素 |
| **image 工具** (LLM 视觉) | 语义理解 ⛔ 不提供坐标 | 理解场景，决定点击什么 |

**渐进式流程**：首次访问 → 三种方法全用。熟悉的页面 → 仅 OCR + detector（跳过 image 工具，节省 token）。

## ⚠️ 安全与协议

每个操作遵循统一的 检测→匹配→执行→保存 协议：

| 步骤 | 内容 | 原因 |
|------|------|------|
| **检测** | 截屏 + OCR + GPA-GUI-Detector | 获取屏幕元素和坐标 |
| **匹配** | 对比已保存的记忆组件 | 复用已学习的元素（跳过重复检测） |
| **决策** | LLM 选择目标元素 | 视觉理解驱动决策 |
| **执行** | 点击检测坐标 / 键盘快捷键 | 用最佳工具执行 |
| **再检测** | 操作后再次截屏 + OCR + 检测 | 查看发生了什么变化 |
| **差异** | 对比操作前后（出现/消失/持续） | 理解状态转移 |
| **保存** | 更新记忆：组件、标签、转移、页面 | 为未来复用而学习 |

**代码层面强制的安全规则：**
- ✅ 发送消息前验证聊天对象（OCR 读取标题）
- ✅ 操作限制在窗口范围内（不点击目标应用外部）
- ✅ 精确文字匹配（防止 "Scan" 匹配到 "Deep Scan"）
- ✅ 最大窗口检测（多窗口应用跳过状态栏面板）
- ✅ 超时后不盲点 — 截屏 + 检查
- ✅ 每次任务后强制报告耗时和 token 增量

## 🗂️ 项目结构

```
GUIClaw/
├── SKILL.md                   # 🧠 主技能文件 — 智能体首先读取此文件
│                              #    定义：视觉 vs 命令边界、三种视觉方法、执行流程
├── skills/                    # 📖 子技能
│   ├── gui-observe/SKILL.md   #   👁️ 截屏、OCR、状态识别
│   ├── gui-learn/SKILL.md     #   🎓 检测组件、标注、过滤、保存
│   ├── gui-act/SKILL.md       #   🖱️ 统一流程：检测→匹配→执行→差异→保存
│   ├── gui-memory/SKILL.md    #   💾 记忆结构、浏览器 sites/、清理规则
│   ├── gui-workflow/SKILL.md  #   🔄 状态图导航、工作流重放
│   ├── gui-report/SKILL.md    #   📊 任务性能追踪
│   └── gui-setup/SKILL.md     #   ⚙️ 新机器首次设置
├── scripts/
│   ├── setup.sh               # 🔧 一键安装
│   ├── agent.py               # 🎯 统一入口（所有 GUI 操作经由此处）
│   ├── ui_detector.py         # 🔍 检测引擎（GPA-GUI-Detector + OCR + Swift 窗口信息）
│   ├── app_memory.py          # 🧠 视觉记忆（学习/检测/点击/验证/learn_site）
│   ├── gui_agent.py           # 🖱️ 旧版任务执行器
│   └── template_match.py      # 🎯 模板匹配工具
├── memory/                    # 🔒 视觉记忆（gitignored 但至关重要）
│   ├── apps/<appname>/        #   每个应用的记忆：
│   │   ├── meta.json          #     元数据（detect_count, forget_threshold）
│   │   ├── components.json    #     组件注册表 + 活跃度追踪
│   │   ├── states.json        #     状态（由组件集合定义）
│   │   ├── transitions.json   #     状态转移（字典结构，去重）
│   │   ├── components/        #     模板图片
│   │   ├── pages/             #     页面截图
│   │   └── sites/<domain>/    #   每个网站的记忆（浏览器专用，相同结构）
├── benchmarks/osworld/        # 📈 OSWorld 基准测试结果
├── assets/                    # 🎨 架构图、banner
├── actions/_actions.yaml      # 📋 原子操作定义
├── docs/
│   ├── core.md                # 📚 经验教训与硬规则
│   └── README_CN.md           # 🇨🇳 中文文档
├── LICENSE                    # 📄 MIT
└── requirements.txt
```

## 📦 环境要求

- **macOS** + Apple Silicon（M1/M2/M3/M4）
- **辅助功能权限**：系统设置 → 隐私与安全性 → 辅助功能
- 其余依赖由 `bash scripts/setup.sh` 自动安装

## 🤝 生态系统

| | |
|---|---|
| 🦞 **[OpenClaw](https://github.com/openclaw/openclaw)** | AI 助手框架 — 将 GUIClaw 作为技能加载 |
| 🔍 **[GPA-GUI-Detector](https://huggingface.co/Salesforce/GPA-GUI-Detector)** | Salesforce/GPA-GUI-Detector — 通用 UI 元素检测模型 |
| 💬 **[Discord 社区](https://discord.gg/BQbUmVuD)** | 获取帮助，分享反馈 |

## 📄 许可证

MIT — 详见 [LICENSE](../LICENSE)。

---

## 📌 引用

如果 GUIClaw 对你的研究有帮助，请引用：

```bibtex
@misc{fu2026guiclaw,
  author       = {Fu, Zichuan},
  title        = {GUIClaw: Visual Memory-Driven GUI Automation for macOS},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/Fzkuji/GUIClaw},
}
```

---

## ⭐ Star History

<p align="center">
  <a href="https://star-history.com/#Fzkuji/GUIClaw&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Fzkuji/GUIClaw&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Fzkuji/GUIClaw&type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Fzkuji/GUIClaw&type=Date" width="600" />
    </picture>
  </a>
</p>

<p align="center">
  <sub>由 🦞 GUIClaw 团队构建 · 基于 <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
