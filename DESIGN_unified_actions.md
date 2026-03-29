# Unified Actions 设计方案 v2

## 概述

两个独立脚本，各司其职：

- **activate.py** — 检测本机环境，告诉模型"你在哪"
- **gui_action.py** — 统一 GUI 操作接口，模型每次调用时指定操作目标

## activate.py（精简版）

只做一件事：检测并打印 OpenClaw 运行的本机环境。

```bash
python3 activate.py
```

输出：
```
Platform: macOS (arm64)
Default target: local
Available tools: pynput, screencapture, pbcopy, osascript
```

- 不管 target 切换
- 不写状态文件
- 不复制 actions 文件
- 只是信息输出

## gui_action.py（统一操作接口）

```bash
# 本机操作（默认，不加参数）
python3 gui_action.py click 500 300
python3 gui_action.py type "hello"
python3 gui_action.py screenshot /tmp/s.png

# 远程操作（加 --remote）
python3 gui_action.py click 500 300 --remote http://172.16.105.128:5000
python3 gui_action.py type "hello" --remote http://172.16.105.128:5000
python3 gui_action.py screenshot /tmp/s.png --remote http://172.16.105.128:5000

# 未来可扩展
python3 gui_action.py click 500 300 --remote ssh://user@host
```

### 可用操作

| 操作 | 参数 | 说明 |
|------|------|------|
| click | x y | 左键点击 |
| double_click | x y | 双击 |
| right_click | x y | 右键 |
| type | "text" | 输入文本 |
| key | name | 按键（enter/tab/escape...） |
| shortcut | keys | 组合键（ctrl+s/cmd+w...） |
| screenshot | [path] | 截图，返回保存路径 |
| focus | "title" | 激活窗口 |
| close | "title" | 关闭窗口 |
| list_windows | | 列出窗口 |

### 内部实现

```python
def execute(action, args, remote=None):
    if remote is None:
        # 本机：检测 OS，选择工具
        if sys.platform == "darwin":
            return execute_mac(action, args)      # pynput
        else:
            return execute_linux(action, args)     # pyautogui/xdotool
    
    elif remote.startswith("http"):
        # HTTP API（如 OSWorld VM）
        return execute_http(action, args, remote)  # requests.post
    
    elif remote.startswith("ssh"):
        # SSH（通用远程）
        return execute_ssh(action, args, remote)   # subprocess ssh
```

### 内部映射

| 操作 | macOS 本机 (mac_local.py) | HTTP 远程 (http_remote.py) |
|------|--------------------------|--------------------------|
| click | cliclick c:X,Y | POST→pyautogui.click(X,Y) |
| type | cliclick kp:text | POST→pyautogui.typewrite(text) |
| screenshot | screencapture | GET /screenshot |
| focus | osascript activate | POST→wmctrl -a |
| shortcut | cliclick kd/ku | POST→pyautogui.hotkey() |
| key | cliclick kp | POST→pyautogui.press() |

## 模型的视角

模型只需要知道：

1. **gui_action.py 能做什么**（click/type/screenshot 等）
2. **不加 --remote = 本机操作**
3. **加 --remote URL = 远程操作**

不需要知道：pynput、pyautogui、xdotool、HTTP API、SSH 细节

## 文件结构

```
scripts/
├── activate.py            # 检测本机环境
├── gui_action.py          # 统一操作入口
├── backends/
│   ├── __init__.py
│   ├── mac_local.py       # macOS 本机实现
│   ├── linux_local.py     # Linux 本机实现
│   ├── http_remote.py     # HTTP API 远程（OSWorld）
│   └── ssh_remote.py      # SSH 远程（通用，未来）
```

## 示例流程

```
用户："帮我在 VM 的 LibreOffice 里填表格"

模型：
1. 知道要操作 VM → 后续 action 加 --remote
2. gui_action.py screenshot /tmp/s.png --remote http://172.16.105.128:5000
3. （下载截图到本地，跑 OCR）
4. gui_action.py click 91 184 --remote http://172.16.105.128:5000
5. gui_action.py type "A2" --remote http://172.16.105.128:5000
6. gui_action.py key enter --remote http://172.16.105.128:5000
7. gui_action.py type "Ming Pavilion" --remote http://172.16.105.128:5000
8. gui_action.py shortcut ctrl+s --remote http://172.16.105.128:5000
```
