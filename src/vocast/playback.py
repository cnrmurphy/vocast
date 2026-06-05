"""Local playback — hand an audio file to the operating system's default player."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def play_file(path: Path) -> None:
    """Open an audio file with the OS default player.

    Returns immediately; playback happens in whatever app the OS associates
    with the file. Raises OSError / CalledProcessError if no launcher is
    available so callers can surface a clear message.
    """
    target = str(path)
    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]  # Windows-only API
    elif sys.platform == "darwin":
        subprocess.run(["open", target], check=True)
    else:
        subprocess.run(["xdg-open", target], check=True)
