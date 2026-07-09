import sys
from pathlib import Path

# Vercel's Python runtime executes this file from inside api/, so the
# project root (where app.py, config.py, models/, db/ all live) needs to be
# added to sys.path manually - otherwise `from config import Config` etc.
# inside app.py fail with ModuleNotFoundError.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app  # noqa: E402

# Vercel's @vercel/python builder looks for a WSGI-compatible object named
# `app` in this file and calls it directly per-request - no app.run(),
# no separate server process.
