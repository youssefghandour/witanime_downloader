"""
witanime-dl — Double-click entry point.

This is the file users run (or the EXE built from this file).
It starts the Flask server and opens the browser automatically.
"""

import sys
import os

# When bundled as EXE by PyInstaller, add the bundle dir to path
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)

from witanime_dl.web.app import run

if __name__ == "__main__":
    run(port=5000, open_browser=True)
