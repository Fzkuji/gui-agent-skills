# 1Password Credential Retrieval

## When to use
Need to copy a password/credential from 1Password GUI for use in another app.

## Fastest method: Click password dots

1. **Activate 1Password**: `osascript -e 'tell application "1Password" to activate'`
2. **Navigate to the entry** (search or scroll to it)
3. **Click the password dots (●●●●)** in the detail panel → auto-copies to clipboard
4. **Use immediately** — clipboard clears after 90 seconds

## Finding and selecting an entry

```bash
# Search for an entry
osascript -e 'tell application "System Events"
    keystroke "f" using command down
    delay 0.3
    keystroke "a" using command down
    delay 0.1
    keystroke "SearchTerm"
    delay 1.5
    key code 36  -- Enter to select first result
    delay 1
end tell'
```

⚠️ **Multiple entries with same name**: Use keyboard Down arrow to navigate the list. Verify the correct entry by checking the right panel (username, website, password strength).

## Clicking the password dots

The password dots are in the right detail panel, below the username field. Use either:

**Method A: Screenshot + estimate position**
```bash
/usr/sbin/screencapture -x /path/screenshot.png
# Use image tool to find the dots location
# Then click with cliclick
```

**Method B: Known position** (if entry layout is stable)
```bash
# After selecting the entry, the password dots are typically
# in the right panel, ~2nd row. Position varies by window size.
/opt/homebrew/bin/cliclick c:1145,325  # Example position
```

**Method C: Edit menu** (reliable fallback)
```javascript
// osascript -l JavaScript
var se = Application("System Events");
var op = se.processes.byName("1Password");
op.menuBars[0].menuBarItems.byName("Edit").menus[0].menuItems.byName("Copy Password").click();
```

## Verify clipboard
```bash
PASS=$(pbpaste)
echo "Length: ${#PASS}"
# Check it's the expected length, not some leftover content
```

## Key gotchas
- **90-second TTL**: 1Password auto-clears clipboard. Copy → paste immediately
- **Search results overlap**: "CityU" may match logins, credit cards, identities — verify the right panel
- **Focus stealing**: other apps (especially GP SSO) can grab focus while you're in 1Password. Complete 1Password operations before interacting with focus-stealing apps
- **`op` CLI needs Touch ID**: won't work on headless/remote machines. Use GUI methods above
- **Cmd+Shift+C** copies password too, but less reliable than clicking dots or Edit menu
