"""
mp4upload provider — extracts direct stream/download URLs.

mp4upload embeds the video source in a <script> tag.
Note: these URLs may have shorter TTLs than MediaFire — use MediaFire first.
"""

import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.mp4upload.com/",
}
session = requests.Session()
session.headers.update(HEADERS)


def get_direct_url(share_url: str) -> tuple[str | None, int | None]:
    """
    Given an mp4upload share URL, return (direct_url, file_size_bytes).
    Returns (None, None) on failure.
    """
    try:
        r = session.get(share_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"  [mp4upload] Page load failed: {e}")
        return None, None

    # mp4upload puts the file URL in a player config script
    m = re.search(r'"file"\s*:\s*"(https?://[^"]+\.mp4[^"]*)"', r.text)
    if m:
        return m.group(1), None

    m = re.search(r'src:\s*"(https?://[^"]+\.mp4[^"]*)"', r.text)
    if m:
        return m.group(1), None

    print("  [mp4upload] Could not find video URL in page source")
    return None, None
