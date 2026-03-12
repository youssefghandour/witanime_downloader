"""
Output writers — saves collected links to files importable by download managers.
"""

from witanime_dl.config import cfg
from witanime_dl.utils import format_size


def save_txt(entries: list):
    """
    Save plain URL list — works with FDM, IDM, and most download managers.
    Import: File -> Import -> From Text File
    """
    with open(cfg.output_file, "w", encoding="utf-8") as f:
        f.write("# Direct Download Links\n")
        f.write("# Import into FDM: File -> Import -> From Text File\n\n")
        for e in entries:
            size_str = f"  ({format_size(e.get('size'))})" if e.get("size") else ""
            f.write(f"# {e['title']}{size_str}\n{e['url']}\n\n")


def save_aria2(entries: list):
    """
    Save aria2c input file with proper headers for direct downloading.
    Usage: aria2c --input-file=episodes.aria2 --max-concurrent-downloads=2 --continue=true
    """
    with open(cfg.aria2_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(f"# {e['title']}\n")
            f.write(f"{e['url']}\n")
            f.write(f"  out={e['title']}.mp4\n")
            f.write(f"  referer=https://www.mediafire.com/\n\n")


def save_all(entries: list):
    """Save both output formats."""
    save_txt(entries)
    save_aria2(entries)
