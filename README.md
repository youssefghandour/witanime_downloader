# witanime-dl

> Collect permanent direct download links for anime episodes and import them into any download manager — with a modern browser-based UI, no command line needed.

---

## For Regular Users — No Python Required

**Download the latest release → double-click `witanime-dl.exe` → done.**

Your browser opens automatically with a clean interface. No installation, no terminal, no setup.

→ **[Download latest release](https://github.com/youssefghandour/witanime_downloader/releases/latest)**

---

## What It Does

witanime-dl scans your download folder, figures out which episodes you're missing, and collects **permanent MediaFire direct download links** for only those episodes. You then import the link file into your download manager and download at your own pace.

Most anime tools either give you expiring links (stop working in 2 hours), require a premium account, or force you to download through their own slow servers. witanime-dl gives you the raw direct link — download with FDM, IDM, aria2c, or anything else, whenever you want.

---

## Features

- **Browser UI** — no command line, works like a website
- **Folder picker** — browse for your download folder with a native dialog
- **Smart skip** — scans your folder and only collects links for missing episodes
- **Episode range** — pick exactly which episodes to collect (e.g. 61 to 500)
- **Live progress log** — see every step in real time with color-coded output
- **Pause / Resume / Stop** — full control during a run
- **Size tracking** — shows file size per episode and running total
- **Permanent links** — MediaFire URLs never expire, work in any downloader
- **Refresh mode** — paste expired links and get fresh ones instantly
- **Resume** — safely interrupt and continue from where you left off
- **Plugin architecture** — add new anime sites with one small file
- **EXE build** — package as a single `.exe` for users with no Python

---

## Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| witanime.life | ✅ Full support | Primary, all features |
| animeslayer.eu | 🔌 Plugin included | Ready to use |
| Any site | 🔧 Extensible | See [Adding a New Site](#adding-a-new-site) |

---

## Supported Download Providers

| Provider | Direct URL | Permanent | Notes |
|----------|-----------|-----------|-------|
| MediaFire | ✅ | ✅ | **Recommended** — no auth, works everywhere |
| mp4upload | ✅ | ✅ | Good fallback |
| Google Drive | ⚠️ | ❌ | Session-based, expires — avoid for FDM |

---

## Using the GUI (Recommended)

### Option A — Run directly with Python

```bash
git clone https://github.com/yourusername/witanime-dl.git
cd witanime-dl
pip install -r requirements.txt
python main.py
```

Your browser opens at `http://localhost:5000` automatically.

### Option B — Build a standalone EXE (share with anyone)

```bash
pip install pyinstaller
python build_exe.py
```

Output: `dist/witanime-dl.exe` — one file, ~70 MB, no Python needed.

> **Build tip — PermissionError on the EXE:**
> Delete the `dist\`, `build\` folders and `witanime-dl.spec` file, then run again.
> Windows Defender sometimes locks newly written EXEs while scanning them.
> Temporarily disabling real-time protection during the build fixes it.

### Option C — Run PyInstaller directly (avoids stale .spec issues)

```bash
pyinstaller --onefile --noconsole --name witanime-dl ^
  --add-data "witanime_dl/web/templates;witanime_dl/web/templates" ^
  --add-data "witanime_dl/web/static;witanime_dl/web/static" ^
  --add-data "config.yaml;." ^
  --hidden-import flask ^
  --hidden-import jinja2 ^
  --hidden-import werkzeug ^
  --hidden-import selenium ^
  --hidden-import bs4 ^
  --hidden-import yaml ^
  --hidden-import tkinter ^
  main.py
```

---

## Using the GUI — Step by Step

1. Open the app (double-click the EXE or run `python main.py`)
2. Your browser opens at `http://localhost:5000`
3. Click **📂 Browse** to select your anime download folder
4. Set the episode range (default 61–500 covers all of Naruto Shippuden)
5. Click **🚀 Start**
6. Watch the live log — episodes are collected one by one
7. When done, click **⬇ Download episodes.txt**
8. In FDM: `File → Import → From Text File → episodes.txt`

**Refresh mode:** If your old links expired, switch to the Refresh tab, paste the expired URLs, and click Start to get fresh permanent links.

---

## CLI Usage (for developers)

```bash
# Normal mode — collect missing episodes
python -m witanime_dl

# Custom folder
python -m witanime_dl --folder "C:/Videos/Naruto"

# Different anime
python -m witanime_dl --url "https://witanime.life/episode/one-piece-الحلقة-1/"

# Refresh expired links
python -m witanime_dl --refresh expired_links.txt

# Start fresh (ignore saved progress)
python -m witanime_dl --clear-progress

# Download with aria2c after collecting
aria2c --input-file=episodes.aria2 --max-concurrent-downloads=2 --continue=true
```

---

## Output Files

| File | Description |
|------|-------------|
| `episodes.txt` | Plain URL list — import into FDM / IDM |
| `episodes.aria2` | aria2c input file with proper headers |
| `progress.json` | Resume state (auto-managed, don't edit) |
| `debug_epXXX.txt` | Created on failure — shows page structure for diagnosis |

---

## Project Structure

```
witanime-dl/
├── main.py                        ← double-click / EXE entry point
├── build_exe.py                   ← builds witanime-dl.exe
├── config.yaml                    ← user settings (no code editing needed)
├── requirements.txt
└── witanime_dl/
    ├── cli.py                     ← command-line interface
    ├── browser.py                 ← Brave / Chrome setup
    ├── scraper.py                 ← clicks buttons, captures URLs
    ├── config.py                  ← loads config.yaml with safe defaults
    ├── output.py                  ← saves episodes.txt + episodes.aria2
    ├── state.py                   ← resume support (progress.json)
    ├── utils.py                   ← shared helpers
    ├── web/
    │   ├── app.py                 ← Flask server + all API routes
    │   └── templates/index.html   ← full UI (single HTML file)
    ├── providers/
    │   ├── mediafire.py           ← permanent URL extractor
    │   └── mp4upload.py           ← fallback provider
    └── sites/
        ├── base.py                ← plugin interface (well documented)
        ├── witanime.py            ← witanime plugin (reference implementation)
        └── animeslayer.py         ← animeslayer plugin example
```

---

## Configuration

Edit `config.yaml` to change defaults without touching any code:

```yaml
# Browser — Brave is strongly recommended (built-in ad blocker)
browser: brave
brave_path: "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

# Provider — MediaFire gives permanent direct links
preferred_provider: mediafire

# Timing — increase js_wait if you get "button not found" errors
js_wait: 6
request_delay: 2
page_timeout: 25
```

---

## Adding a New Site

Create one file in `witanime_dl/sites/` implementing three methods:

```python
# witanime_dl/sites/mysite.py
from witanime_dl.sites.base import BaseSite

class MySite(BaseSite):
    NAME    = "My Site"
    DOMAINS = ["mysite.com", "mysite.tv"]

    def episode_url(self, ep_num: int) -> str:
        return f"https://mysite.com/episode/anime-{ep_num}/"

    def find_provider_button(self, driver, provider: str):
        return self._find_by_keywords(driver, [provider, "تحميل"])

    def ep_num_from_url(self, url: str) -> int | None:
        import re
        m = re.search(r"-(\d+)/?$", url)
        return int(m.group(1)) if m else None
```

Then register it in `witanime_dl/sites/__init__.py`:

```python
from witanime_dl.sites.mysite import MySite
SITE_REGISTRY["mysite"] = MySite
```

Everything else — clicking, URL extraction, size tracking, saving, resume — is handled automatically.

---

## Troubleshooting

**"MediaFire button not found"**
A `debug_epXXX.txt` file is saved automatically. Open it and look at the links section to see what buttons are actually on the page. The script retries 3 times automatically. Try increasing `js_wait` to `8` or `10` in `config.yaml`.

**"Redirected away from witanime"**
Witanime uses aggressive ad networks that hijack navigation. Using **Brave** instead of Chrome helps significantly since Brave blocks ads natively. Increase `js_wait` if it keeps happening.

**FDM says "server returned a web page"**
You have a Google Drive link — it requires browser session cookies and doesn't work in download managers. Set `preferred_provider: mediafire` in `config.yaml`.

**Build error: PermissionError on witanime-dl.exe**
Delete `dist\`, `build\`, and `witanime-dl.spec` then rebuild. If it still fails, temporarily disable Windows Defender real-time protection during the build.

**ChromeDriver version mismatch**
Do not install `webdriver-manager` — Selenium 4.6+ handles this automatically. If you have it: `pip uninstall webdriver-manager` then `pip install --upgrade selenium`.

**Wrong episode numbers detected**
Your filenames need a recognizable episode number pattern. Supported formats: `EP61`, `NS EP 61`, `NS+EP+61`, `Episode 61`, `S01E061`, `[61]`.

---

## Why Not yt-dlp?

yt-dlp downloads files directly to disk. witanime-dl collects links so you queue them in your download manager — giving you speed control, scheduling, pause/resume across sessions, and full control over where files go. yt-dlp also struggles with Google Drive quota limits and has no concept of tracking which episodes you already have.

---

## Requirements

- Windows 10/11 (Linux and Mac supported for CLI mode)
- Brave or Google Chrome installed
- Python 3.10+ *(only needed if running from source — EXE users need nothing)*

---

## Contributing

Pull requests welcome. Most useful contributions:
- New site plugins (`witanime_dl/sites/`) — use `animeslayer.py` as a template
- New provider plugins (`witanime_dl/providers/`) — use `mediafire.py` as a template
- Bug reports with a `debug_epXXX.txt` file attached

---

## License

MIT — free to use, modify, and distribute.
