"""
Build script — creates a single witanime-dl.exe using PyInstaller.

Usage:
    pip install pyinstaller
    python build_exe.py

Output: dist/witanime-dl.exe   (~60-80 MB, no Python needed)

Users just download this one file, double-click, done.
"""

import os
import sys
import shutil
import subprocess

ROOT      = os.path.dirname(os.path.abspath(__file__))
DIST_DIR  = os.path.join(ROOT, "dist")
BUILD_DIR = os.path.join(ROOT, "build")
ICON_PATH = os.path.join(ROOT, "witanime_dl", "web", "static", "icon.ico")

# Files and folders PyInstaller must include inside the bundle
DATAS = [
    # (source_path, dest_folder_inside_exe)
    ("witanime_dl/web/templates", "witanime_dl/web/templates"),
    ("witanime_dl/web/static",    "witanime_dl/web/static"),
    ("config.yaml",               "."),
]


def build():
    print("=" * 55)
    print("  witanime-dl — EXE Builder")
    print("=" * 55)

    # Check PyInstaller is installed
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("\n  PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Delete old EXE if it exists (avoids PermissionError if it was running)
    old_exe = os.path.join(DIST_DIR, "witanime-dl.exe")
    if os.path.exists(old_exe):
        try:
            os.remove(old_exe)
            print(f"  Removed old EXE.")
        except PermissionError:
            print()
            print("  ❌ Cannot delete the old witanime-dl.exe — it is still running or locked.")
            print("  Fix:")
            print("    1. Close witanime-dl.exe if it is open")
            print("    2. Disable Windows Defender real-time protection temporarily")
            print("    3. Run this script again")
            sys.exit(1)

    # Build --add-data arguments
    # Windows uses ; as separator, Linux/Mac uses :
    sep = ";" if sys.platform == "win32" else ":"
    add_data_args = []
    for src, dst in DATAS:
        if os.path.exists(os.path.join(ROOT, src)):
            add_data_args += ["--add-data", f"{src}{sep}{dst}"]

    icon_args = ["--icon", ICON_PATH] if os.path.exists(ICON_PATH) else []

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # single EXE
        "--noconsole",                        # no black CMD window (GUI app)
        "--name", "witanime-dl",
        "--distpath", DIST_DIR,
        "--workpath", BUILD_DIR,
        "--clean",
        *icon_args,
        *add_data_args,
        # Hidden imports Flask needs
        "--hidden-import", "flask",
        "--hidden-import", "jinja2",
        "--hidden-import", "werkzeug",
        "--hidden-import", "selenium",
        "--hidden-import", "bs4",
        "--hidden-import", "requests",
        "--hidden-import", "yaml",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "main.py",
    ]

    print(f"\n  Running PyInstaller...\n")
    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode == 0:
        exe_path = os.path.join(DIST_DIR, "witanime-dl.exe")
        size_mb  = os.path.getsize(exe_path) / 1024 / 1024
        print(f"\n{'=' * 55}")
        print(f"  ✅ Build successful!")
        print(f"  📦 {exe_path}")
        print(f"  📏 Size: {size_mb:.1f} MB")
        print(f"\n  Share this single file — users just double-click it.")
        print(f"{'=' * 55}\n")
    else:
        print(f"\n  ❌ Build failed (exit code {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    build()
