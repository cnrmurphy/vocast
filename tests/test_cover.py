"""Cover art: og:image extraction, download filtering, and embed forwarding."""

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from vocast import audio, fetch, library
from vocast.audio import write_audio
from vocast.engines import AudioChunk
from vocast.library import LibraryEntry
from vocast.server import _build_rss, create_app


def _chunk() -> AudioChunk:
    return AudioChunk(np.zeros(2400, dtype=np.float32), 24000)


# --- fetch: og:image extraction -------------------------------------------


def test_fetch_returns_cover_image(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fetch, "_fetch_html", lambda url, timeout=30.0: "<html></html>")
    monkeypatch.setattr(
        fetch.trafilatura,
        "extract",
        lambda *a, **k: json.dumps(
            {"title": "T", "text": "body", "image": "https://ex.com/i.jpg"}
        ),
    )
    _, _, cover = fetch.fetch_article("http://x")
    assert cover == "https://ex.com/i.jpg"


def test_fetch_cover_none_when_absent(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fetch, "_fetch_html", lambda url, timeout=30.0: "<html></html>")
    monkeypatch.setattr(
        fetch.trafilatura,
        "extract",
        lambda *a, **k: json.dumps({"title": "T", "text": "body"}),
    )
    _, _, cover = fetch.fetch_article("http://x")
    assert cover is None


# --- _download_cover: accept only genuine JPEG/PNG ------------------------


class _MockHeaders:
    def __init__(self, content_type: str):
        self._content_type = content_type

    def get_content_type(self) -> str:
        return self._content_type


class _MockResponse:
    def __init__(self, content_type: str, data: bytes):
        self.headers = _MockHeaders(content_type)
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._data


def _mock_urlopen(monkeypatch, content_type: str, data: bytes):
    monkeypatch.setattr(
        library.urllib.request,
        "urlopen",
        lambda req, timeout=None: _MockResponse(content_type, data),
    )


def test_download_cover_saves_jpeg(tmp_path, monkeypatch):
    jpeg_bytes = library._JPEG_MAGIC + b"\x00" * 16
    _mock_urlopen(monkeypatch, "image/jpeg", jpeg_bytes)
    saved = library._download_cover("http://x/i.jpg", tmp_path)
    assert saved == tmp_path / "cover.jpg"
    assert saved.read_bytes() == jpeg_bytes


def test_download_cover_rejects_non_image(tmp_path, monkeypatch):
    _mock_urlopen(monkeypatch, "text/html", b"<html></html>")
    assert library._download_cover("http://x/page", tmp_path) is None


def test_download_cover_rejects_magic_mismatch(tmp_path, monkeypatch):
    _mock_urlopen(monkeypatch, "image/png", b"this is not a png")
    assert library._download_cover("http://x/fake.png", tmp_path) is None


# --- write_audio: forward the cover, never let it break the mp3 -----------


def test_write_audio_forwards_cover(tmp_path, monkeypatch):
    export_calls: list[dict] = []

    def mock_export(self, out_f, **kwargs):
        export_calls.append(kwargs)
        Path(out_f).write_bytes(b"")

    monkeypatch.setattr(audio.AudioSegment, "export", mock_export)
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"image-bytes")
    write_audio(_chunk(), tmp_path / "audio.mp3", cover_path=cover)
    assert export_calls[-1].get("cover") == str(cover)


def test_write_audio_omits_cover_when_absent(tmp_path, monkeypatch):
    export_calls: list[dict] = []

    def mock_export(self, out_f, **kwargs):
        export_calls.append(kwargs)
        Path(out_f).write_bytes(b"")

    monkeypatch.setattr(audio.AudioSegment, "export", mock_export)
    write_audio(_chunk(), tmp_path / "audio.mp3")
    assert "cover" not in export_calls[-1]


def test_write_audio_falls_back_when_embedding_fails(tmp_path, monkeypatch):
    export_calls: list[dict] = []

    def mock_export(self, out_f, **kwargs):
        export_calls.append(kwargs)
        if "cover" in kwargs:
            raise RuntimeError("encoder rejected the cover")
        Path(out_f).write_bytes(b"mp3-bytes")

    monkeypatch.setattr(audio.AudioSegment, "export", mock_export)
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"image-bytes")
    audio_output = tmp_path / "audio.mp3"
    write_audio(_chunk(), audio_output, cover_path=cover)
    assert any("cover" in call for call in export_calls)
    assert any("cover" not in call for call in export_calls)
    assert audio_output.exists()


# --- _resolve_cover: downloaded wins, else bundled default ----------------


def test_resolve_cover_uses_downloaded(tmp_path):
    downloaded = tmp_path / "cover.jpg"
    downloaded.write_bytes(b"image-bytes")
    with library._resolve_cover(downloaded) as cover_path:
        assert cover_path == downloaded


def test_resolve_cover_falls_back_to_bundled_default():
    with library._resolve_cover(None) as cover_path:
        assert cover_path is not None
        assert cover_path.name == "default_cover.jpg"
        assert cover_path.is_file()


# --- show cover: served from /cover.jpg and advertised in the feed --------


def test_cover_endpoint_serves_default_jpeg():
    resp = TestClient(create_app()).get("/cover.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content.startswith(library._JPEG_MAGIC)


def test_feed_advertises_channel_cover():
    xml = _build_rss([], "https://host")
    assert '<itunes:image href="https://host/cover.jpg" />' in xml


# --- backward compatibility ----------------------------------------------


def test_backward_compatible_entry_without_cover_field():
    data = {
        "id": "20260604T120000Z_x_a1b2c3",
        "title": "Old Entry",
        "source": None,
        "synthesized_at": "2026-06-04T12:00:00+00:00",
        "duration_seconds": 60.0,
        "voice": "af_heart",
        "engine": "kokoro",
    }
    assert LibraryEntry(**data).cover_url is None
