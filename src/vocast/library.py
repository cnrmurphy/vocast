"""Library — synthesized articles stored as <id>/{audio.mp3, meta.json}."""

from __future__ import annotations

import json
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .audio import write_audio
from .engines import AudioChunk

LIBRARY_PATH = Path.home() / ".vocast" / "library"


@dataclass
class LibraryEntry:
    id: str
    title: str
    source: str | None
    synthesized_at: str
    duration_seconds: float
    voice: str
    engine: str

    def dir(self) -> Path:
        return LIBRARY_PATH / self.id

    def audio_path(self) -> Path:
        return self.dir() / "audio.mp3"

    def meta_path(self) -> Path:
        return self.dir() / "meta.json"


def _make_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "untitled"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = secrets.token_hex(3)
    return f"{ts}_{slug}_{short}"


def add_entry(
    *,
    title: str,
    chunk: AudioChunk,
    voice: str,
    engine: str,
    source: str | None = None,
    mp3_bitrate: str = "96k",
) -> LibraryEntry:
    entry_id = _make_id(title)
    entry_dir = LIBRARY_PATH / entry_id
    entry_dir.mkdir(parents=True, exist_ok=False)

    audio_path = entry_dir / "audio.mp3"
    write_audio(chunk, audio_path, mp3_bitrate=mp3_bitrate)

    duration = float(len(chunk.samples)) / chunk.sample_rate
    entry = LibraryEntry(
        id=entry_id,
        title=title,
        source=source,
        synthesized_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration,
        voice=voice,
        engine=engine,
    )
    (entry_dir / "meta.json").write_text(json.dumps(asdict(entry), indent=2))
    return entry


def list_entries() -> list[LibraryEntry]:
    if not LIBRARY_PATH.exists():
        return []
    entries: list[LibraryEntry] = []
    for child in sorted(LIBRARY_PATH.iterdir(), reverse=True):
        meta = child / "meta.json"
        if meta.exists():
            entries.append(LibraryEntry(**json.loads(meta.read_text())))
    return entries


def get_entry(entry_id: str) -> LibraryEntry | None:
    meta = LIBRARY_PATH / entry_id / "meta.json"
    if not meta.exists():
        return None
    return LibraryEntry(**json.loads(meta.read_text()))
