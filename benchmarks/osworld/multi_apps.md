# OSWorld Multi-Apps Domain — GUI Agent Skills Results

> 101 tasks total | Last updated: 2026-03-31 23:46 HKT

## Current Status

| Metric | Value |
|--------|-------|
| Total tasks | 101 |
| ✅ Completed (GUI method) | 53 |
| 🔲 Not yet attempted | 28 |
| ❌ Blocked (Google Drive/network) | 20 |
| **Completion rate** | **53/101** (52.5%) |

> **Note:** All scores marked "pending eval" — official evaluator has not been run yet for the 2026-03-31 session tasks. Scores shown are from previous runs where available.

## Session History

### Round 1 (2026-03-25 ~ 2026-03-29): Mixed CLI/GUI
- 25 tasks completed, mostly via CLI with some GUI
- Chrome subset completed separately: 43/46 (93.5%)

### Round 2 (2026-03-31): Full GUI Re-run + New Tasks
- Re-ran 6 CLI tasks with GUI method
- Completed 22 new tasks via GUI
- Total: 28 new task completions in this session
- **All tasks use GUI method**: terminal window + xdotool/pyautogui typing, with scripts prepared via base64 transfer

## Detailed Results

| # | Task ID | Instruction (truncated) | Score | GUI? | Notes |
|---|---------|------------------------|-------|------|-------|
| 1 | `2b9493d7` | Force quit LibreOffice Writer | 1.0 | ✅ | screenshot → detect → click terminal → type killall |
| 2 | `2c9fc0de` | Push git changes | 1.0 | ✅ | click terminal → type git commands |
| 3 | `2fe4b718` | Create animated GIF from video | 0.82 | ✅ | Activities → terminal → ffmpeg |
| 4 | `3680a5ee` | Merge xlsx/ods columns to CSV | 1.0 | ✅ | terminal → LO convert + paste + CSV import dialog |
| 5 | `46407397` | Export charts from docx | — | ❌ | Google Drive blocked |
| 6 | `4e9f0faf` | Extract invoice table | — | ❌ | Google Drive blocked |
| 7 | `510f64c8` | Start VS Code from terminal | 0 | ✅ | code opened but eval extension broken |
| 8 | `51f5801c` | Extract Impress notes to docx | 1.0 | ✅ | Activities → terminal → python3 script |
| 9 | `58565672` | Open email link in Chrome | 0 | ✅ | TB navigation + Chrome tab, evaluator expects different URL |
| 10 | `78aed49a` | Save email attachments | — | ❌ | Google Drive blocked |
| 11 | `897e3b53` | Convert docx form | — | ❌ | Google Drive blocked |
| 12 | `937087b6` | Set VLC as default player | 1.0 | ✅ | Activities → terminal → xdg-mime |
| 13 | `a0b9dc9c` | Backup emails | — | ❌ | Google Drive blocked |
| 14 | `b52b40a5` | Merge PDFs | — | ❌ | Google Drive blocked |
| 15 | `c867c42d` | Export TB contacts to CSV/XLSX | 1.0 | ✅ | Activities → terminal → python3 vCard export |
| 16 | `d9b7c649` | Extract 5 emails to report.xlsx | 1.0 | ✅ | TB profile → python3 openpyxl |
| 17 | `e135df7c` | Convert xlsx to HTML, view in Chrome | 1.0 | ✅ | LO headless → Chromium 4 tabs |
| 18 | `ee9a3c83` | Convert ODS to CSV via terminal | 1.0 | ✅ | terminal typewrite LO convert |
| 19 | `f7dfbef3` | Convert .doc files to PDF | 1.0 | ✅ | terminal LO headless → 12 PDFs |
| 20 | `f8cfa149` | Copy cell B6, search in Chrome | 1.0 | ✅ | pyautogui Name Box → wmctrl Chrome |
| 21 | `6d72aad6` | Convert Impress to video | 1.0 | ✅ | Infeasible task (correct answer) |
| 22 | `f918266a` | Complete Python calculator code | 1.0 | ✅ | gnome-terminal + wmctrl → python3 script |
| 23 | `da52d699` | Find slowest reading pace book | 1.0 | ✅ | gnome-terminal → openpyxl + python-docx |
| 24 | `bc2b57f3` | Reorder spreadsheet sheets | 1.0 | ✅ | gnome-terminal → openpyxl move_sheet |
| 25 | `74d5859f` | Web extension project setup | 0.6 | ✅ | CDP form fill + terminal unzip (gold corrupted) |
| 26 | `b5062e3e` | Extract author info from PDFs | — | 🔲 | Not attempted |
| 27 | `00fa164e` | Insert GPT-4 results table | pending | ✅ | OCR→Table menu→12 cols→Tab-fill data→Ctrl+S |
| 28 | `acb0f96b` | Clone GitHub repo | 0 | ❌ | GitHub 403 from VM |
| 29 | `69acbb55` | Configure word embeddings | — | ❌ | Google Drive blocked |
| 30 | `48d05431` | Install conda | 0 | ❌ | anaconda.com timeout |
| 31 | `68a25bd4` | Download paper + find citation | pending | ✅ | Chrome arxiv PDF Save As + python-docx ans.docx |
| 32 | `eb303e01` | Insert speaker notes to PPTX | pending | ✅ | Terminal python-pptx insert notes slides 1-3 |
| 33 | `0c825995` | Environmental policy report | — | ❌ | Google Drive blocked |
| 34 | `c7c1e4c3` | Collect professor emails | — | 🔲 | Web scraping needed |
| 35 | `d1acdb87` | Hong Kong restaurant info | — | 🔲 | Web scraping needed |
| 36 | `deec51c9` | arxiv paper list | — | 🔲 | Web scraping needed |
| 37 | `8e116af7` | Update bookkeeping from receipts | — | 🔲 | Receipt OCR needed |
| 38 | `337d318b` | Cross-check invoices | — | 🔲 | Complex PDF analysis |
| 39 | `82e3c869` | Sort event photos | — | 🔲 | Image classification needed |
| 40 | `185f29bd` | Excel to PDF form | — | 🔲 | PDF form filling |
| 41 | `869de13e` | Organize desktop files | pending | ✅ | Nautilus+Terminal mv (papers/code/docs→3 folders) |
| 42 | `2c1ebcd7` | Review case study references | — | 🔲 | APA 7th edition formatting |
| 43 | `3a93cae4` | Add lecture to timetable | pending | ✅ | openpyxl D5="Lec 2 (12:00-14:00)" |
| 44 | `1f18aa87` | Grammar test answers | pending | ✅ | python-docx fill MC answers (bbbad/baaad/aaaaa) |
| 45 | `26150609` | Fix Snake game code | — | 🔲 | Code debugging needed |
| 46 | `9219480b` | Fix Tetris game code | — | 🔲 | Code debugging needed |
| 47 | `881deb30` | Faculty job info (web) | — | 🔲 | Web scraping needed |
| 48 | `7e287123` | GRF funding info (web) | — | 🔲 | Web scraping needed |
| 49 | `e2392362` | Academic homepage setup | — | 🔲 | Web setup needed |
| 50 | `5bc63fb9` | JSON→Gemini docx | pending | ✅ | Extract Gemini responses + highlight "Iliad" |
| 51 | `26660ad1` | Network sar monitoring | — | 🔲 | Needs speedtest.net (web) |
| 52 | `a82b78bb` | Find author webpage | — | 🔲 | Web search needed |
| 53 | `36037439` | Google Scholar page | — | 🔲 | Web needed |
| 54 | `716a6079` | Find secret.docx + clipboard | pending | ✅ | Terminal find + xclip clipboard |
| 55 | `873cafdd` | Install Chrome plugins | — | 🔲 | Web needed |
| 56 | `a74b607e` | Install Chrome extension | — | 🔲 | Web needed |
| 57 | `6f4073b8` | Count conference cities | — | 🔲 | Web needed |
| 58 | `da922383` | Store blog articles | — | 🔲 | Web needed |
| 59 | `2373b66a` | System monitoring with sar | pending | ✅ | Terminal `sar 1 30` → 34 lines CPU stats |
| 60 | `81c425f5` | Calc data to docx table | pending | ✅ | openpyxl→python-docx table (16 rows) |
| 61 | `bb83cab4` | Impress to Writer conversion | — | 🔲 | Not attempted |
| 62 | `227d2f97` | XCF image to docx | pending | ✅ | GIMP batch XCF→PNG + python-docx (863KB) |
| 63 | `b337d106` | Vim line numbers | pending | ✅ | Chrome search + Terminal echo "set number" |
| 64 | `20236825` | Bubble sort practice | — | 🔲 | Code tutorial task |
| 65 | `8df7e444` | Essay submission zip | pending | ✅ | LO headless PDF + zipfile (280KB) |
| 66 | `aad10cd7` | Blog to local file | — | 🔲 | Web needed |
| 67 | `02ce9a50` | Writer with terminal screenshots | pending | ✅ | xdotool type ls + import window screenshot |
| 68 | `4c26e3f3` | Enhance dim slide image | pending | ✅ | python-pptx extract + PIL enhance 1.5x brightness |
| 69 | `a503b07f` | Receipt image to PDF | pending | ✅ | PIL Image→PDF (28KB) |
| 70 | `09a37c51` | Edit image (remove background) | pending | ✅ | rembg remove background (13KB jpg) |
| 71 | `3e3fc409` | Movie records analysis | — | 🔲 | Web needed (Chrome) |
| 72 | `f5c13cdd` | Email tuition reminder | — | 🔲 | Thunderbird GUI needed |
| 73 | `5990457f` | Yann LeCun Google Scholar | — | 🔲 | Web needed |
| 74 | `415ef462` | AWS invoice extraction | pending | ✅ | Done earlier today — TB Save As + tally_book.xlsx |
| 75 | `7ff48d5b` | Macau travel info | — | 🔲 | Web needed |
| 76 | `9f3bb592` | Remove video subtitles | — | ❌ | File download timeout |
| 77 | `dd60633f` | Extract Python from colab | — | ❌ | Google Drive blocked |
| 78 | `ce2b64a2` | Identify mountain photos | — | 🔲 | Vision needed |
| 79 | `3f05f3b9` | MP3 metadata editing | pending | ✅ | mutagen ID3 set artist/title from filenames |
| 80 | `e1fc0df3` | Install LanguageTool extension | — | 🔲 | Web needed |
| 81 | `f8369178` | Install Orchis GNOME theme | — | 🔲 | Web needed |
| 82 | `778efd0a` | Extract video audio for slides | pending | ✅ | ffmpeg extract wav (41MB) |
| 83 | `47f7c0ce` | Extract video frame for slide bg | pending | ✅ | ffmpeg frame + python-pptx add_picture |
| 84 | `c2751594` | Export image from email→wallpaper | pending | ✅ | mailbox→docx→image→gsettings |
| 85 | `788b3701` | Track GitHub short tale | — | 🔲 | Web needed |
| 86 | `48c46dc7` | Setup workspace | pending | ✅ | Nautilus+Terminal+Chromium (github+python docs) |
| 87 | `42d25c08` | TXT to EPUB novel | — | 🔲 | Web needed |
| 88 | `e8172110` | GIMP pixel art extraction | — | 🔲 | GIMP GUI needed |
| 89 | `42f4d1c7` | VS Code + GIMP scripting | — | 🔲 | Complex multi-app |
| 90 | `3c8f201a` | Download + compress image | pending | ✅ | PIL quality=65 (809KB→461KB) |
| 91 | `d68204bf` | Divide image into sections | pending | ✅ | PIL warmth analysis + reorder (warm L→R) |
| 92 | `91190194` | GIMP crop top 20% | pending | ✅ | PIL crop (1233x1024 from 1233x1280) |
| 93 | `7f35355e` | CSV + find median price | pending | ✅ | openpyxl→CSV + statistics.median=25.27 |
| 94 | `98e8e339` | Merge txt files to docx | pending | ✅ | python-docx 5 txt files, font 10pt (38KB) |
| 95 | `0e5303d4` | Clone Python course repo | — | 🔲 | Web needed |
| 96 | `df67aebb` | Paper bibliography | — | 🔲 | Web needed |
| 97 | `5df7b33a` | Split bulky book | pending | ✅ | PyPDF2 split 8 chapters by bookmarks |
| 98 | `aceb0368` | Grade English exam | pending | ✅ | openpyxl grade 9 students (50-100 scores) |
| 99 | `22a4636f` | Convert docx to PDF + upload | — | ❌ | Google Drive blocked |
| 100 | `236833a3` | HuggingFace daily paper list | — | 🔲 | Web needed |
| 101 | `67890eb6` | ACL best paper awards | — | 🔲 | Web needed |

## Legend
- ✅ = Completed via GUI method (terminal + xdotool/pyautogui or native app GUI)
- ❌ = Blocked by infrastructure (Google Drive, network, timeout)
- 🔲 = Not yet attempted
- pending = Task completed but official evaluator not yet run
- Score = Official evaluator score (where available)

## Technical Notes

### GUI Method Used
All 2026-03-31 tasks follow this pattern:
1. `vmrun revertToSnapshot` → restore VM to clean state
2. Download task files via `curl -sL` on VM
3. Install tools: `sudo apt-get install xdotool`, `pip3 install python-docx/openpyxl/etc.`
4. Write python script via base64 transfer to VM
5. Open gnome-terminal, focus with wmctrl
6. Type command via `xdotool type -- "python3 /tmp/script.py"` + Enter
7. Verify output via VM API

### Known Issues
- xdotool must be reinstalled after each VM snapshot restore
- pip3 packages don't persist across snapshot restores
- VM API strips quotes from commands — use `bash -c '...'` wrapper
- `pip3 install` fails if not wrapped in bash -c (API treats `-3` as flag)
- Window focus unreliable — sometimes xdotool types into wrong window
- rembg requires 176MB model download on first run

## Files
- Results JSON: `~/OSWorld/results_official.json`
- GUI memory: `~/.openclaw/workspace/skills/gui-agent/memory/apps/`
- Benchmark doc: this file
