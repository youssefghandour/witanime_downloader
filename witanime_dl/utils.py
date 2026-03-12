"""Shared utility functions."""

import os
import re
from selenium.webdriver.common.by import By


def format_size(size_bytes: int | None) -> str:
    """Human-readable file size string."""
    if size_bytes is None or size_bytes == 0:
        return "unknown size"
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / 1024**3:.2f} GB"
    elif size_bytes >= 1024 ** 2:
        return f"{size_bytes / 1024**2:.1f} MB"
    else:
        return f"{size_bytes / 1024:.1f} KB"


def format_episodes(eps) -> str:
    """Format a list/set of episode numbers as compact ranges: '61-123, 191, 402-403'"""
    if not eps:
        return "none"
    sorted_eps = sorted(eps)
    ranges = []
    start = end = sorted_eps[0]
    for ep in sorted_eps[1:]:
        if ep == end + 1:
            end = ep
        else:
            ranges.append(f"{start}-{end}" if start != end else str(start))
            start = end = ep
    ranges.append(f"{start}-{end}" if start != end else str(start))
    return ", ".join(ranges)


def get_downloaded_episodes(folder: str) -> set:
    """
    Scan a download folder and return a set of episode numbers found in filenames.

    Handles patterns like:
      NS EP 93, NS+EP+93, EP093, EP93, Episode 93, S01E093, [93], _93_
    """
    if not os.path.isdir(folder):
        return set()

    patterns = [
        r"NS[\s+_-]*EP[\s+_-]*(\d+)",        # NS EP 93, NS+EP+93
        r"\bEP[\s+_-]*(\d{2,4})\b",           # EP93, EP093
        r"[Ee]pisode[\s_-]*(\d+)",             # Episode 93
        r"[Ss]\d+[Ee](\d+)",                  # S01E093
        r"[\[_\-\s](\d{2,4})[\]_\-\s\.]",    # [93], _93_
    ]

    downloaded = set()
    for fname in os.listdir(folder):
        if not fname.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
            continue
        for pat in patterns:
            m = re.search(pat, fname, re.IGNORECASE)
            if m:
                downloaded.add(int(m.group(1)))
                break
    return downloaded


def parse_expired_file(filepath: str) -> list:
    """
    Extract episode numbers from a file of expired URLs or comment lines.
    Returns sorted list of episode numbers.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return []

    def try_extract(text, strict=False):
        patterns = [
            r"NS[\s+_-]*EP[\s+_-]*(\d+)",
            r"\bEP[\s+_-]*(\d{2,4})\b",
            r"[Ee]pisode[\s_-]*(\d+)",
            r"[Ss]\d+[Ee](\d+)",
        ]
        if not strict:
            patterns += [r"[\[_\-\s+](\d{2,4})[\]_\-\s+\.]"]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                num = int(m.group(1))
                if 1 <= num <= 9999:
                    return num
        return None

    episode_numbers = []
    seen = set()

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            num = None
            if line.startswith("http"):
                from urllib.parse import unquote, urlparse
                filename = unquote(urlparse(line).path.split("/")[-1])
                num = try_extract(filename, strict=True)
                if num is None:
                    num = try_extract(unquote(line), strict=True)
            elif line.startswith("#"):
                num = try_extract(line[1:], strict=False)
            else:
                num = try_extract(line, strict=False)

            if num is not None and num not in seen:
                seen.add(num)
                episode_numbers.append(num)

    return sorted(episode_numbers)


def dump_debug(driver, ep_num: int):
    """Save page content to a debug file when a button isn't found."""
    debug_file = f"debug_ep{ep_num:03d}.txt"
    with open(debug_file, "w", encoding="utf-8") as f:
        f.write(f"URL   : {driver.current_url}\n")
        f.write(f"Title : {driver.title}\n\n")
        f.write("=== ALL LINKS ===\n")
        for el in driver.find_elements(By.TAG_NAME, "a"):
            text = el.text.strip()
            href = el.get_attribute("href") or ""
            cls  = el.get_attribute("class") or ""
            durl = el.get_attribute("data-url") or ""
            if text or href:
                f.write(f"  text='{text[:60]}' href='{href[:100]}'\n")
                f.write(f"  class='{cls}' data-url='{durl}'\n\n")
        f.write("=== BUTTONS ===\n")
        for el in driver.find_elements(By.TAG_NAME, "button"):
            f.write(f"  text='{el.text.strip()[:60]}' class='{el.get_attribute('class')}'\n")
        f.write("\n=== PAGE SOURCE (first 6000 chars) ===\n")
        f.write(driver.page_source[:6000])
    print(f"  [debug] Saved -> {debug_file}")
