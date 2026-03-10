# Exploring a New App

## When to use
First time automating an app. Need to understand its UI before writing actions.

## Step 1: AX Recon (~5s)

```javascript
// osascript -l JavaScript
var se = Application("System Events");
var p = se.processes["AppName"];
var w = p.windows[0];

// Count elements (indicates AX quality)
var all = w.entireContents();
"Elements: " + all.length;
// < 10 = AX useless, use OCR
// > 100 = AX excellent, prefer AX
```

## Step 2: Map key elements

```javascript
// List all buttons, fields, links with positions
var result = [];
for (var i = 0; i < all.length; i++) {
    try {
        var r = all[i].role();
        if (r === "AXButton" || r === "AXTextField" || r === "AXLink" || r === "AXStaticText") {
            var t = all[i].title() || all[i].value() || "";
            var p2 = all[i].position(), s = all[i].size();
            if (t) result.push(r + ' "' + t + '" (' + p2[0] + ',' + p2[1] + ') ' + s[0] + 'x' + s[1]);
        }
    } catch(e) {}
}
result.join("\n");
```

## Step 3: OCR scan (if AX is sparse)

```bash
python3 scripts/gui_agent.py observe --app AppName
python3 scripts/gui_agent.py find "some keyword"
```

## Step 4: Document in app profile

Create `apps/appname.json`:
```json
{
  "app": "AppName",
  "process_name": "AppName",
  "layout": {
    "sidebar_width": 250,
    "input_bottom_offset": 60
  },
  "navigation": {
    "method": "sidebar_click",
    "search_shortcut": {"key": "f", "modifiers": ["command"]}
  },
  "input": {
    "method": "ocr",
    "ocr_keyword": "Type a message"
  },
  "send": {"key": "return"},
  "quirks": ["Notes about unusual behavior"]
}
```

## What to look for
- **Window regions**: sidebar width, main area, input field location
- **AX quality**: how many elements? Are buttons/fields labeled?
- **WebView or native?**: WebViews need cliclick, native can use AX clicks
- **Keyboard shortcuts**: Cmd+F for search? Cmd+K? Enter to send?
- **Quirks**: auto-lock? focus stealing? non-standard input methods?
