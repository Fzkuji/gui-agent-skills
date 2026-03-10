# VPN Reconnect (GlobalProtect + CityU SSO)

## When to use
SSH to AML server fails (timeout/refused) → VPN likely disconnected.

## Check VPN status
```javascript
// osascript -l JavaScript
var se = Application("System Events");
var gp = se.processes.byName("GlobalProtect");
gp.menuBars[1].menuBarItems[0].click();
delay(2);
var w = gp.windows[0];
var texts = w.staticTexts();
for (var i = 0; i < texts.length; i++) {
    // Look for "Connected" or "Disconnected"
    texts[i].value();
}
```
- Has "Disconnect" button → already connected
- Has "Connect" button → disconnected, proceed below

## Reconnect Flow

```
1. Quit GP → Reopen → Open panel → Click Connect
2. Wait ~7s for SSO window
3. AX: find "Next" button → click
4. Wait ~4s for password page
5. AX: confirm AXTextField exists → record position
6. 1Password: copy CityU password (see docs/1password.md)
7. cliclick c:{field_x},{field_y} (integers!)
8. Cmd+V paste password
9. cliclick c:{verify_x},{verify_y}
10. Wait ~8s → test SSH
```

### Step-by-step commands

```bash
# Step 1: Restart GP
osascript -e 'tell application "GlobalProtect" to quit'
sleep 3
open -a GlobalProtect
sleep 5

# Step 2: Open panel and Connect
osascript -l JavaScript -e '
var se = Application("System Events");
var gp = se.processes.byName("GlobalProtect");
gp.menuBars[1].menuBarItems[0].click();
delay(2);
gp.windows[0].buttons.byName("Connect").click();
'
sleep 7  # Wait for SSO window

# Step 3: Click Next
osascript -l JavaScript -e '
var se = Application("System Events");
var gp = se.processes.byName("GlobalProtect");
var contents = gp.windows.byName("GlobalProtect Login").entireContents();
for (var i = 0; i < contents.length; i++) {
    try {
        if (contents[i].role() === "AXButton" && contents[i].title() === "Next")
            contents[i].click();
    } catch(e) {}
}
'
sleep 4  # Wait for password page

# Step 4: Get field and button positions
osascript -l JavaScript -e '
var se = Application("System Events");
var contents = se.processes.byName("GlobalProtect").windows.byName("GlobalProtect Login").entireContents();
var result = [];
for (var i = 0; i < contents.length; i++) {
    try {
        var r = contents[i].role();
        if (r === "AXTextField") {
            var p = contents[i].position(), s = contents[i].size();
            result.push("FIELD " + Math.round(p[0]+s[0]/2) + "," + Math.round(p[1]+s[1]/2));
        }
        if (r === "AXButton" && contents[i].title() === "Verify") {
            var p = contents[i].position(), s = contents[i].size();
            result.push("VERIFY " + Math.round(p[0]+s[0]/2) + "," + Math.round(p[1]+s[1]/2));
        }
    } catch(e) {}
}
result.join("\n");
'
# → e.g. "FIELD 961,494" and "VERIFY 961,567"

# Step 5: Copy password from 1Password (see docs/1password.md)
# Step 6: Click field → paste → click Verify
/opt/homebrew/bin/cliclick c:961,494
osascript -e 'tell application "System Events" to keystroke "v" using command down'
sleep 0.3
/opt/homebrew/bin/cliclick c:961,567

# Step 7: Verify
sleep 8
sshpass -p 'PASSWORD' ssh -o ConnectTimeout=5 user@host 'echo OK'
```

## Key gotchas
- **Coordinates change if GP window was moved** — always re-query AX positions
- **SSO page has timeout** — if you're slow, it expires and you get "Unable to sign in"
- **Copy password LAST** (1Password clipboard clears after 90s)
- **Use Cmd+V to paste**, not `cliclick t:` (special chars get truncated)
- **"Back to sign in" is a link, not a button** — find via `AXLink` role
- **If login fails**: click "Back to sign in" → Next → re-enter password (max 3 retries)

## Environment-specific values
These live in TOOLS.md (not here — no credentials in skill files):
- Portal URL, EID
- SSH credentials  
- 1Password item details
- GP menu bar icon position
