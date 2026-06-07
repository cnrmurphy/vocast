"""Library — synthesized articles stored as <id>/{audio.mp3, meta.json}."""

from __future__ import annotations

import json
import re
import secrets
import shutil
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path

from .audio import write_audio
from .engines import AudioChunk

LIBRARY_PATH = Path.home() / ".vocast" / "library"

_COVER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# File signatures, to confirm a downloaded cover really is the image its
# content-type claims (and not, say, an HTML error page served as image/*).
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@dataclass
class LibraryEntry:
    id: str
    title: str
    source: str | None
    synthesized_at: str
    duration_seconds: float
    voice: str
    engine: str
    cover_url: str | None = None

    def dir(self) -> Path:
        return LIBRARY_PATH / self.id

    def audio_path(self) -> Path:
        return self.dir() / "audio.mp3"

    def meta_path(self) -> Path:
        return self.dir() / "meta.json"

    @property
    def short_id(self) -> str:
        """Trailing hex token of the id — a stable, human-friendly handle."""
        return self.id.rsplit("_", 1)[-1]


def _make_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40] or "untitled"
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = secrets.token_hex(3)
    return f"{ts}_{slug}_{short}"


def _download_cover(url: str, dest_dir: Path) -> Path | None:
    """Download a JPEG/PNG cover into dest_dir; return its path, or None.

    Returns None on any failure (bad URL, non-image content, timeout) so a
    missing or unusable cover never blocks adding the article.
    """
    ext_by_type = {"image/jpeg": ".jpg", "image/png": ".png"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _COVER_USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            ext = ext_by_type.get(resp.headers.get_content_type())
            if ext is None:
                return None
            data = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    if not (data.startswith(_JPEG_MAGIC) or data.startswith(_PNG_MAGIC)):
        return None
    dest = dest_dir / f"cover{ext}"
    dest.write_bytes(data)
    return dest


@contextmanager
def _resolve_cover(downloaded: Path | None):
    """Yield a cover image path: the downloaded one, else the bundled default.

    Yields None only if the bundled default is somehow missing, so callers
    still produce audio without art rather than failing.
    """
    if downloaded is not None:
        yield downloaded
        return
    default = files("vocast").joinpath("assets/default_cover.jpg")
    if not default.is_file():
        yield None
        return
    with as_file(default) as path:
        yield path


def add_entry(
    *,
    title: str,
    chunk: AudioChunk,
    voice: str,
    engine: str,
    source: str | None = None,
    cover_url: str | None = None,
    mp3_bitrate: str = "96k",
) -> LibraryEntry:
    entry_id = _make_id(title)
    entry_dir = LIBRARY_PATH / entry_id
    entry_dir.mkdir(parents=True, exist_ok=False)

    downloaded_cover = _download_cover(cover_url, entry_dir) if cover_url else None
    audio_path = entry_dir / "audio.mp3"
    with _resolve_cover(downloaded_cover) as cover_path:
        write_audio(chunk, audio_path, mp3_bitrate=mp3_bitrate, cover_path=cover_path)

    duration = float(len(chunk.samples)) / chunk.sample_rate
    entry = LibraryEntry(
        id=entry_id,
        title=title,
        source=source,
        synthesized_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=duration,
        voice=voice,
        engine=engine,
        cover_url=cover_url,
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


def match_entries(entries: list[LibraryEntry], query: str) -> list[LibraryEntry]:
    """Resolve a query against entries.

    Priority: an exact id / short_id match (case-insensitive) wins outright;
    otherwise a case-insensitive substring match on the title.
    """
    q = query.strip()
    lowered = q.lower()
    exact = [e for e in entries if e.id == q or e.short_id.lower() == lowered]
    if exact:
        return exact
    return [e for e in entries if lowered in e.title.lower()]


def resolve(query: str) -> list[LibraryEntry]:
    """Scan the library and resolve a query to zero, one, or many entries."""
    return match_entries(list_entries(), query)


def delete_entry(entry: LibraryEntry) -> None:
    shutil.rmtree(entry.dir())
