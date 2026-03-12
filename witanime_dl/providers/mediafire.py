"""
MediaFire provider — extracts permanent direct download URLs.

MediaFire embeds the direct download URL in the page HTML as:
    <a id="downloadButton" href="https://download1078.mediafire.com/...">

This URL is permanent — it never expires and works in any downloader.
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
}
session = requests.Session()
session.headers.update(HEADERS)


def get_direct_url(share_url: str) -> tuple[str | None, int | None]:
    """
    Given a MediaFire share URL (e.g. https://www.mediafire.com/file/abc123/...),
    return (direct_download_url, file_size_in_bytes).

    Returns (None, None) on failure.
    """
    try:
        r = session.get(share_url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"  [mediafire] Page load failed: {e}")
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")
    direct_url = _extract_url(soup, r.text)
    file_size  = _extract_size(soup, direct_url)

    if not direct_url:
        print("  [mediafire] Could not find download URL on page")

    return direct_url, file_size


def _extract_url(soup: BeautifulSoup, raw_html: str) -> str | None:
    # Strategy 1: standard download button
    btn = soup.find("a", id="downloadButton")
    if btn and btn.get("href", "").startswith("http"):
        return btn["href"]

    # Strategy 2: aria-label
    btn = soup.find("a", attrs={"aria-label": re.compile("download", re.I)})
    if btn and btn.get("href") and "mediafire.com" in btn["href"]:
        return btn["href"]

    # Strategy 3: any link to download subdomain
    for a in soup.find_all("a", href=True):
        if re.match(r"https?://download\d*\.mediafire\.com/", a["href"]):
            return a["href"]

    # Strategy 4: regex on raw HTML
    m = re.search(r"https?://download\d*\.mediafire\.com/[^\s'\"\\)>]+", raw_html)
    if m:
        return m.group(0)

    # Strategy 5: JSON-embedded URL
    m = re.search(r'"(https://download[^"]*mediafire[^"]*)"', raw_html)
    if m:
        return m.group(1)

    return None


def _extract_size(soup: BeautifulSoup, direct_url: str | None) -> int | None:
    # Try to find size text on the page (e.g. "369.4 MB")
    for tag in soup.find_all(string=re.compile(r"\d+(\.\d+)?\s*(MB|GB|KB)", re.I)):
        m = re.search(r"([\d.]+)\s*(KB|MB|GB)", tag, re.I)
        if m:
            val  = float(m.group(1))
            unit = m.group(2).upper()
            multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
            return int(val * multipliers[unit])

    # Fallback: HEAD request on the direct URL
    if direct_url:
        try:
            head = session.head(direct_url, timeout=10, allow_redirects=True)
            cl = head.headers.get("Content-Length")
            if cl:
                return int(cl)
        except Exception:
            pass

    return None
