"""
Flask web UI for witanime-dl.

Features:
  - Live progress log via Server-Sent Events (SSE)
  - Folder picker (native OS dialog via tkinter)
  - Episode range picker
  - Pause / Resume / Stop controls
  - Download episodes.txt when done
"""

import os
import sys
import json
import queue
import threading
import time
import webbrowser

from flask import Flask, render_template, request, jsonify, Response, send_file

# Allow running as bundled EXE (PyInstaller) or from source
ROOT = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(ROOT, "templates"),
            static_folder=os.path.join(ROOT, "static"))

# ── Global job state ──────────────────────────────────────────────────────────

class Job:
    def __init__(self):
        self.running   = False
        self.paused    = False
        self.stopped   = False
        self.thread    = None
        self.log_q     = queue.Queue()   # SSE log messages
        self.entries   = []              # collected links
        self.failed    = []
        self.total_eps = 0
        self.done_eps  = 0
        self.total_bytes = 0

    def reset(self):
        self.__init__()

    def log(self, msg: str, level: str = "info"):
        self.log_q.put({"msg": msg, "level": level})

    def wait_if_paused(self):
        """Call this inside the worker loop to honor pause/resume."""
        while self.paused and not self.stopped:
            time.sleep(0.5)


job = Job()

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    # Auto-detect the user's Downloads folder
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    return render_template("index.html", default_folder=downloads)


@app.route("/api/browse-folder", methods=["GET"])
def browse_folder():
    """Open a native OS folder picker dialog and return the selected path."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        path = filedialog.askdirectory(title="Select your anime download folder")
        root.destroy()
        return jsonify({"path": path or ""})
    except Exception as e:
        return jsonify({"path": "", "error": str(e)})


@app.route("/api/start", methods=["POST"])
def start():
    global job
    if job.running:
        return jsonify({"error": "A job is already running."}), 400

    data = job_params = request.json
    job.reset()

    t = threading.Thread(target=run_job, args=(job_params,), daemon=True)
    job.thread = t
    job.running = True
    t.start()

    return jsonify({"status": "started"})


@app.route("/api/pause", methods=["POST"])
def pause():
    if not job.running:
        return jsonify({"error": "No job running."}), 400
    job.paused = not job.paused
    status = "paused" if job.paused else "resumed"
    job.log(f"{'⏸ Paused' if job.paused else '▶ Resumed'}.", "warn" if job.paused else "info")
    return jsonify({"status": status})


@app.route("/api/stop", methods=["POST"])
def stop():
    job.stopped = True
    job.paused  = False
    job.log("⛔ Stop requested — finishing current episode then stopping...", "error")
    return jsonify({"status": "stopping"})


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "running":     job.running,
        "paused":      job.paused,
        "done_eps":    job.done_eps,
        "total_eps":   job.total_eps,
        "total_bytes": job.total_bytes,
        "failed":      job.failed,
        "entries":     len(job.entries),
    })


@app.route("/api/stream")
def stream():
    """Server-Sent Events endpoint — pushes log lines to the browser in real time."""
    def event_generator():
        while True:
            try:
                item = job.log_q.get(timeout=30)
                data = json.dumps(item)
                yield f"data: {data}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"
    return Response(event_generator(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/download-txt")
def download_txt():
    from witanime_dl.config import cfg
    path = os.path.abspath(cfg.output_file)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "episodes.txt not found"}), 404


@app.route("/api/download-aria2")
def download_aria2():
    from witanime_dl.config import cfg
    path = os.path.abspath(cfg.aria2_file)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "episodes.aria2 not found"}), 404


# ── Job worker (runs in background thread) ────────────────────────────────────

def run_job(params: dict):
    """Background thread — runs the scraper and logs to job.log_q."""
    global job

    try:
        _do_run(params)
    except Exception as e:
        job.log(f"💥 Unexpected error: {e}", "error")
    finally:
        job.running = False
        job.paused  = False
        job.log("__DONE__", "done")


def _do_run(params: dict):
    from witanime_dl.config import cfg
    from witanime_dl.browser import make_driver
    from witanime_dl.scraper import process_episode
    from witanime_dl.sites import detect_site
    from witanime_dl.output import save_all
    from witanime_dl.utils import (
        get_downloaded_episodes, parse_expired_file,
        format_size, format_episodes
    )

    mode         = params.get("mode", "normal")
    download_dir = params.get("folder", cfg.download_dir)
    start_ep     = int(params.get("start_ep", cfg.start_episode))
    end_ep       = int(params.get("end_ep",   cfg.max_episode))
    refresh_urls = params.get("refresh_urls", "").strip()

    def log(msg, level="info"):
        job.log(msg, level)

    log(f"🚀 Starting {'refresh' if mode == 'refresh' else 'normal'} mode...")
    log(f"📁 Folder: {download_dir}")

    # ── Launch browser ──
    log("🌐 Launching browser (this takes a few seconds)...")
    try:
        driver = make_driver()
    except Exception as e:
        log(f"❌ Could not start browser: {e}", "error")
        log("Fix: make sure Brave or Chrome is installed.", "error")
        return

    log("✅ Browser ready.")
    site = detect_site("https://witanime.life/")
    log(f"🔍 Site: {site.NAME}")

    try:
        if mode == "refresh":
            _run_refresh(driver, site, refresh_urls, log)
        else:
            _run_normal(driver, site, download_dir, start_ep, end_ep, log)
    finally:
        driver.quit()
        log("🔒 Browser closed.")


def _run_normal(driver, site, download_dir, start_ep, end_ep, log):
    from witanime_dl.utils import get_downloaded_episodes, format_size, format_episodes
    from witanime_dl.scraper import process_episode
    from witanime_dl.output import save_all
    from witanime_dl.config import cfg

    downloaded = get_downloaded_episodes(download_dir)
    log(f"✅ Already downloaded: {len(downloaded)} episodes")

    # Find max episode
    log("🔎 Checking how many episodes are on the site...")
    max_ep = min(end_ep, site.find_max_episode(driver))
    log(f"📺 Episodes available: {start_ep} to {max_ep}")

    missing = [ep for ep in range(start_ep, max_ep + 1) if ep not in downloaded]
    job.total_eps = len(missing)

    if not missing:
        log("🎉 You already have all episodes!", "success")
        return

    log(f"📋 Need to collect: {len(missing)} episodes  ({format_episodes(missing)})", "info")

    for ep_num in missing:
        if job.stopped:
            log("⛔ Stopped by user.", "error")
            break

        job.wait_if_paused()

        log(f"━━━ Episode {ep_num:03d} ({'#'+str(job.done_eps+1)}/{job.total_eps}) ━━━")

        direct_url, size_bytes = process_episode(driver, site, ep_num)

        if direct_url:
            job.done_eps    += 1
            job.total_bytes += (size_bytes or 0)
            entry = {
                "title": f"Naruto Shippuden EP{ep_num:03d}",
                "url":   direct_url,
                "size":  size_bytes,
            }
            job.entries.append(entry)
            save_all(job.entries)

            size_str = format_size(size_bytes) if size_bytes else "size unknown"
            log(f"✅ EP{ep_num:03d} — {size_str}  |  Running total: {format_size(job.total_bytes)}", "success")
            log(f"__PROGRESS__{job.done_eps}/{job.total_eps}/{job.total_bytes}", "progress")
        else:
            job.failed.append(ep_num)
            log(f"❌ EP{ep_num:03d} failed — will retry on next run", "error")

        time.sleep(cfg.request_delay)

    if job.entries:
        from witanime_dl.utils import format_size
        log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log(f"✅ Collected: {len(job.entries)} links", "success")
        log(f"📦 Total size: {format_size(job.total_bytes)}", "success")
        if job.failed:
            log(f"⚠️ Failed: {len(job.failed)} episodes — re-run to retry", "warn")
        log(f"📄 Saved to episodes.txt — ready to import into FDM!", "success")


def _run_refresh(driver, site, refresh_urls_text, log):
    from witanime_dl.utils import parse_expired_file, format_size
    from witanime_dl.scraper import process_episode
    from witanime_dl.output import save_all
    from witanime_dl.config import cfg
    import tempfile

    # Write the pasted URLs to a temp file and parse it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                     delete=False, encoding="utf-8") as f:
        f.write(refresh_urls_text)
        tmp_path = f.name

    episode_numbers = parse_expired_file(tmp_path)
    os.unlink(tmp_path)

    if not episode_numbers:
        log("❌ Could not find any episode numbers in the pasted URLs.", "error")
        return

    job.total_eps = len(episode_numbers)
    log(f"🔄 Refreshing {len(episode_numbers)} episodes...")

    for ep_num in episode_numbers:
        if job.stopped:
            log("⛔ Stopped by user.", "error")
            break

        job.wait_if_paused()
        log(f"━━━ Refreshing EP{ep_num:03d} ({'#'+str(job.done_eps+1)}/{job.total_eps}) ━━━")

        direct_url, size_bytes = process_episode(driver, site, ep_num)

        if direct_url:
            job.done_eps    += 1
            job.total_bytes += (size_bytes or 0)
            job.entries.append({
                "title": f"Naruto Shippuden EP{ep_num:03d}",
                "url":   direct_url,
                "size":  size_bytes,
            })
            save_all(job.entries)
            log(f"✅ EP{ep_num:03d} refreshed — {format_size(size_bytes)}", "success")
            log(f"__PROGRESS__{job.done_eps}/{job.total_eps}/{job.total_bytes}", "progress")
        else:
            job.failed.append(ep_num)
            log(f"❌ EP{ep_num:03d} failed", "error")

        time.sleep(cfg.request_delay)


# ── Entry point ───────────────────────────────────────────────────────────────

def run(port: int = 5000, open_browser: bool = True):
    """Start the Flask server and optionally open the browser."""
    if open_browser:
        # Open browser after a short delay to let Flask start
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}")).start()

    print(f"\n  witanime-dl UI → http://localhost:{port}")
    print("  Close this window to exit.\n")

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
