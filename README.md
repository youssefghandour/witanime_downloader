# witanime-dl

> Automatically collect permanent direct download links for anime episodes and import them into any download manager (FDM, IDM, aria2c).

---

## Why witanime-dl?

Most anime download tools either:
- Require a premium account
- Give you expiring links that stop working in 2 hours
- Only work with one specific download manager

**witanime-dl gives you permanent MediaFire direct links** — save them once, download whenever you want, with any tool.

---

## Features

- Scans your download folder and **only collects links for episodes you're missing**
- **Permanent direct download URLs** (MediaFire) — never expire
- **Refresh mode** — regenerate expired links from a list
- **Multi-provider** — MediaFire (primary), Google Drive, mp4upload fallback
- **Plugin architecture** — add support for new anime sites with one file
- **Smart retry** — handles ad redirects, page timeouts, JS loading delays
- **Size tracking** — shows file size and running total after each episode
- **Resume** — saves progress after every episode, safe to interrupt
- Works with **FDM, IDM, aria2c, wget, curl** — any downloader

---

## Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| witanime.life | ✅ Full support | Primary site, all features |
| animeslayer.eu | 🔌 Plugin ready | Add `sites/animeslayer.py` |
| animeiat.com | 🔌 Plugin ready | Add `sites/animeiat.py` |
| Any site | 🔧 Extensible | See [Adding a New Site](#adding-a-new-site) |

---

## Supported Providers

| Provider | Direct URL | Permanent | Notes |
|----------|-----------|-----------|-------|
| MediaFire | ✅ | ✅ | Best — no auth needed |
| mp4upload | ✅ | ✅ | Good fallback |
| Google Drive | ⚠️ | ❌ | Session-based, expires |
| Mega | ✅ | ✅ | Needs megatools |

---

## Installation

```bash
git clone https://github.com/yourusername/witanime-dl.git
cd witanime-dl
pip install -r requirements.txt
```

You also need **Google Chrome** or **Brave** installed.

---

## Quick Start

```bash
# Collect missing episodes (scans your download folder automatically)
python -m witanime_dl

# Specify your download folder
python -m witanime_dl --folder "C:/Videos/Naruto"

# Collect for a different anime
python -m witanime_dl --url "https://witanime.life/episode/one-piece-الحلقة-1/"

# Refresh expired links
python -m witanime_dl --refresh expired_links.txt

# Use aria2c to download everything after collecting
aria2c --input-file=episodes.aria2 --max-concurrent-downloads=2 --continue=true
```

---

## Output Files

| File | Description |
|------|-------------|
| `episodes.txt` | Plain URL list — import into FDM/IDM |
| `episodes.aria2` | aria2c input file with headers |
| `progress.json` | Resume state (auto-managed) |
| `debug_epXXX.txt` | Created when a button isn't found — helps diagnose issues |

### Import into FDM
`File → Import → From Text File → episodes.txt`

### Download with aria2c
```bash
aria2c --input-file=episodes.aria2 --max-concurrent-downloads=2 --continue=true
```

---

## Configuration

Edit `config.yaml` to set your defaults:

```yaml
# Your anime download folder
download_dir: "C:/Users/YourName/Downloads/naruto shippuden"

# Which provider to prefer
preferred_provider: mediafire   # mediafire | googledrive | mp4upload | mega

# Browser (brave recommended — better ad blocking)
browser: brave   # brave | chrome

# Delays (seconds) — increase if getting blocked
js_wait: 6
request_delay: 2
page_timeout: 25

# Output files
output_file: episodes.txt
aria2_file: episodes.aria2
```

---

## Adding a New Site

Create a file in `witanime_dl/sites/` that implements the `BaseSite` interface:

```python
# witanime_dl/sites/mysite.py
from witanime_dl.sites.base import BaseSite

class MySite(BaseSite):
    # Domain this plugin handles
    DOMAINS = ["mysite.com", "mysite.tv"]

    # URL template to build episode URLs by number
    def episode_url(self, ep_num: int) -> str:
        return f"https://mysite.com/episode/anime-name-{ep_num}/"

    # Find the download provider button (return its element)
    def find_provider_button(self, driver, provider: str):
        # Your site-specific logic here
        ...

    # Extract episode number from URL
    def ep_num_from_url(self, url: str) -> int | None:
        ...
```

That's it. The rest (clicking, extracting URLs, size tracking, saving) is handled automatically.

---

## Why Not Just Use yt-dlp?

yt-dlp is great but:
- It downloads directly — you can't queue into FDM/IDM
- Google Drive files frequently fail with yt-dlp due to quota limits
- It doesn't track which episodes you already have
- No resume state across multiple runs

witanime-dl is designed specifically for **collecting links to import into your download manager**, giving you full control over when and how files download.

---

## Troubleshooting

**"MediaFire button not found"**
A `debug_epXXX.txt` file is created — open it to see what's on the page.
Common cause: ad redirect (wps.com etc). The script retries 3x automatically.

**"Redirected away from witanime"**
Witanime uses ad networks that sometimes hijack navigation.
Try increasing `js_wait` in `config.yaml` to `8` or `10`.

**FDM says "server returned a web page"**
You're using a Google Drive link — switch to MediaFire provider.
MediaFire links work directly in FDM with no issues.

**Script finds wrong episode numbers**
Open `debug_epXXX.txt` and check what filenames are in your download folder.
The filename must contain a recognizable episode number pattern (EP61, NS EP 61, etc.)

---

## Contributing

Pull requests welcome! Most useful contributions:
- New site plugins (`witanime_dl/sites/`)
- New provider plugins (`witanime_dl/providers/`)
- Bug fixes with a `debug_epXXX.txt` example

---

## License

MIT — free to use, modify, and distribute.
