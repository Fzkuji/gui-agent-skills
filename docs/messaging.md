# App Messaging (WeChat, Discord, Telegram)

## When to use
Send or read messages in desktop chat apps.

## High-level tasks
```bash
cd /path/to/gui-agent

# Send message
python3 scripts/gui_agent.py task send_message --app WeChat --param contact="John" --param message="hi"

# Read messages
python3 scripts/gui_agent.py task read_messages --app WeChat --param contact="John"

# Scroll history
python3 scripts/gui_agent.py task scroll_history --app WeChat --param pages="5"

# List all tasks
python3 scripts/gui_agent.py tasks
```

## App-specific notes

### WeChat
- **AX is useless** (5 elements). Use OCR + templates
- **Input field**: OCR can't see placeholder. Use `window_calc`
- **Send**: Enter (not Cmd+Enter)
- **Search**: Use template `search_bar`. Don't use Cmd+F (opens web search)
- **Re-clicking highlighted chat** doesn't reopen it — click away first, then click back

### Discord
- **AX is excellent** (1362 elements)
- **Search**: Cmd+K opens quick switcher
- **Input**: OCR finds "Message #channel-name" placeholder
- **Send**: Enter

### Telegram
- **Search**: Cmd+F
- **Input**: OCR finds "Write a message" placeholder
- **Send**: Enter

## Manual approach (when tasks don't work)

```bash
# 1. Focus app
osascript -e 'tell application "WeChat" to activate'

# 2. Hide other apps
osascript -e 'tell application "System Events" to set visible of every process whose name is not "WeChat" to false'

# 3. Find and click contact (OCR)
python3 scripts/gui_agent.py find "ContactName"
/opt/homebrew/bin/cliclick c:{x},{y}

# 4. Click input area
/opt/homebrew/bin/cliclick c:{input_x},{input_y}

# 5. Type message
/opt/homebrew/bin/cliclick t:"hello"

# 6. Send
/opt/homebrew/bin/cliclick kp:return
```

## App profiles
Configs in `apps/*.json`. Create new ones by copying existing profiles.
