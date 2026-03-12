"""
CLI entry point — handles argument parsing and orchestrates all modes.

Modes:
  Normal  : scan folder, collect missing episodes
  Refresh : re-collect expired links from a file
"""

import sys
import time
import argparse

from witanime_dl.config import cfg
from witanime_dl.browser import make_driver
from witanime_dl.scraper import process_episode
from witanime_dl.sites import detect_site
from witanime_dl.output import save_all
from witanime_dl.utils import (
    get_downloaded_episodes,
    parse_expired_file,
    format_size,
    format_episodes,
)
from witanime_dl import state


def run_normal(driver, site, download_dir: str):
    """Collect links for all missing episodes."""
    downloaded = get_downloaded_episodes(download_dir)

    print(f"\n  Download folder  : {download_dir}")
    print(f"  Already have     : {len(downloaded)} episodes ({format_episodes(downloaded)})")
    print(f"  Output           : {cfg.output_file}  |  {cfg.aria2_file}\n")

    # Find the highest episode on site
    max_ep = site.find_max_episode(driver)

    all_eps = list(range(cfg.start_episode, max_ep + 1))
    missing = [ep for ep in all_eps if ep not in downloaded]

    print(f"\n  Episodes on site : {cfg.start_episode} to {max_ep}  ({len(all_eps)} total)")
    print(f"  Already have     : {len(downloaded)}")
    print(f"  Need to collect  : {len(missing)} episodes")
    if missing:
        print(f"  Missing          : {format_episodes(missing)}\n")

    if not missing:
        print("  Nothing to do!")
        return [], [], 0

    # Load existing progress (resume support)
    saved = state.load()
    entries = [
        {"title": k, "url": v["url"], "size": v.get("size")}
        for k, v in saved.get("collected", {}).items()
    ]
    already_collected = {e["title"] for e in entries}

    failed  = saved.get("failed", [])
    skipped = 0
    total_bytes = sum(e["size"] or 0 for e in entries)

    for ep_num in missing:
        title = f"Naruto Shippuden EP{ep_num:03d}"

        if title in already_collected:
            print(f"[Ep {ep_num:03d}] Already collected in previous run -- skipping")
            skipped += 1
            continue

        print(f"\n[Ep {ep_num:03d}] Collecting link...  ({missing.index(ep_num)+1}/{len(missing)})")

        direct_url, size_bytes = process_episode(driver, site, ep_num)

        if direct_url:
            total_bytes += (size_bytes or 0)
            entries.append({"title": title, "url": direct_url, "size": size_bytes})

            # Save progress after every episode
            saved["collected"][title] = {"url": direct_url, "size": size_bytes}
            state.save(saved)
            save_all(entries)

            # Show size stats
            collected_so_far = len(entries)
            known_sizes = [e["size"] for e in entries if e.get("size")]
            size_str = format_size(size_bytes) if size_bytes else "unknown size"
            print(f"  Size: {size_str}")
            if known_sizes:
                avg = sum(known_sizes) / len(known_sizes)
                estimated_total = avg * len(missing)
                print(
                    f"  [{collected_so_far}/{len(missing)}] "
                    f"Running total: {format_size(total_bytes)}  |  "
                    f"Est. full: {format_size(int(estimated_total))}"
                )
        else:
            failed.append(ep_num)
            saved["failed"] = failed
            state.save(saved)

        time.sleep(cfg.request_delay)

    return entries, failed, skipped


def run_refresh(driver, site, expired_file: str):
    """Re-collect links for a list of expired URLs."""
    episode_numbers = parse_expired_file(expired_file)

    if not episode_numbers:
        print("[ERROR] No episode numbers found in file.")
        sys.exit(1)

    print(f"\n  Refreshing       : {len(episode_numbers)} episodes")
    print(f"  Episodes         : {format_episodes(episode_numbers)}")
    print(f"  Output           : {cfg.output_file}  |  {cfg.aria2_file}\n")

    entries = []
    failed  = []
    total_bytes = 0

    for i, ep_num in enumerate(episode_numbers, 1):
        print(f"\n[Ep {ep_num:03d}] Refreshing...  ({i}/{len(episode_numbers)})")

        direct_url, size_bytes = process_episode(driver, site, ep_num)

        if direct_url:
            total_bytes += (size_bytes or 0)
            entries.append({
                "title": f"Naruto Shippuden EP{ep_num:03d}",
                "url":   direct_url,
                "size":  size_bytes,
            })
            save_all(entries)
            size_str = format_size(size_bytes) if size_bytes else "unknown size"
            print(f"  Size: {size_str}")
            print(f"  [{i}/{len(episode_numbers)}] Running total: {format_size(total_bytes)}")
        else:
            failed.append(ep_num)

        time.sleep(cfg.request_delay)

    return entries, failed


def print_summary(entries, failed, skipped=0, mode="normal"):
    out_file = cfg.output_file
    print("\n" + "=" * 60)
    print("SUMMARY")
    if mode == "normal":
        print(f"  Skipped (resume / already have) : {skipped}")
    print(f"  Links collected                 : {len(entries)}")
    print(f"  Failed                          : {len(failed)}")

    if entries:
        total = sum(e["size"] or 0 for e in entries)
        known = sum(1 for e in entries if e.get("size"))
        size_note = f" ({known}/{len(entries)} sizes known)" if known < len(entries) else ""
        print(f"  Total download size             : {format_size(total)}{size_note}")
        print(f"\n  Saved to : {out_file}")
        print(f"             {cfg.aria2_file}")
        print(f"\n  FDM      : File -> Import -> From Text File -> {out_file}")
        print(f"  aria2c   : aria2c --input-file={cfg.aria2_file} --max-concurrent-downloads=2 --continue=true")

    if failed:
        print(f"\n  Failed episodes : {format_episodes(failed)}")
        print("  Tip: re-run the script to retry failed episodes.")
        print("  Check debug_epXXX.txt files for details on why they failed.")

    if not entries and not failed:
        print("\n  Nothing to download!")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="witanime-dl — Collect permanent MediaFire download links for anime episodes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m witanime_dl
  python -m witanime_dl --folder "C:/Videos/Naruto"
  python -m witanime_dl --url "https://witanime.life/episode/one-piece-الحلقة-1/"
  python -m witanime_dl --refresh expired.txt
  python -m witanime_dl --clear-progress
        """,
    )
    parser.add_argument("--folder",  metavar="PATH", default=cfg.download_dir,
                        help=f"Download folder to scan (default: {cfg.download_dir})")
    parser.add_argument("--url",     metavar="URL",
                        help="Custom episode URL (auto-detects site)")
    parser.add_argument("--refresh", metavar="FILE",
                        help="File with expired URLs to regenerate")
    parser.add_argument("--clear-progress", action="store_true",
                        help="Delete progress.json and start fresh")
    args = parser.parse_args()

    print("=" * 60)
    if args.refresh:
        print("witanime-dl  [REFRESH MODE]")
    else:
        print("witanime-dl  [NORMAL MODE]")
    print("=" * 60)

    if args.clear_progress:
        state.clear()

    # Auto-detect site from URL (or use default witanime)
    base_url = args.url or "https://witanime.life/"
    site = detect_site(base_url)
    print(f"\n  Site     : {site.NAME}")
    print(f"  Provider : {cfg.preferred_provider}")

    print("\n  Launching browser...")
    try:
        driver = make_driver()
    except Exception as e:
        print(f"\n[FATAL] Could not start browser: {e}")
        print("Fix: install Brave/Chrome + pip install webdriver-manager")
        sys.exit(1)

    try:
        if args.refresh:
            entries, failed = run_refresh(driver, site, args.refresh)
            print_summary(entries, failed, mode="refresh")
        else:
            entries, failed, skipped = run_normal(driver, site, args.folder)
            print_summary(entries, failed, skipped, mode="normal")
    finally:
        driver.quit()
