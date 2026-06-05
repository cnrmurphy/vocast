"""Scanner + play/delete command flows against a temporary library."""

import argparse
import json
from pathlib import Path

import pytest

from vocast import cli, library


@pytest.fixture
def lib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(library, "LIBRARY_PATH", tmp_path)
    return tmp_path


def _make_library_entry(lib_path: Path, entry_id: str, title: str) -> Path:
    entry_dir = lib_path / entry_id
    entry_dir.mkdir(parents=True)
    (entry_dir / "audio.mp3").write_bytes(b"fake-mp3")
    (entry_dir / "meta.json").write_text(
        json.dumps(
            {
                "id": entry_id,
                "title": title,
                "source": None,
                "synthesized_at": "2026-06-04T12:00:00+00:00",
                "duration_seconds": 60.0,
                "voice": "af_heart",
                "engine": "kokoro",
            }
        )
    )
    return entry_dir


def test_scanner_loads_entries(lib: Path):
    _make_library_entry(lib, "20260604T120000Z_a_aaa111", "Alpha")
    _make_library_entry(lib, "20260605T120000Z_b_bbb222", "Beta")
    assert {e.title for e in library.list_entries()} == {"Alpha", "Beta"}


def test_delete_entry_removes_directory(lib: Path):
    entry_dir = _make_library_entry(lib, "20260604T120000Z_a_aaa111", "Alpha")
    [entry] = library.list_entries()
    library.delete_entry(entry)
    assert not entry_dir.exists()


def test_delete_confirmed(lib: Path, monkeypatch: pytest.MonkeyPatch):
    entry_dir = _make_library_entry(
        lib, "20260604T120000Z_bitter_a8f31c", "The Bitter Lesson"
    )
    monkeypatch.setattr("builtins.input", lambda *a, **k: "y")
    rc = cli.cmd_delete(argparse.Namespace(query="bitter", yes=False))
    assert rc == 0
    assert not entry_dir.exists()


def test_delete_declined_keeps_directory(lib: Path, monkeypatch: pytest.MonkeyPatch):
    entry_dir = _make_library_entry(
        lib, "20260604T120000Z_bitter_a8f31c", "The Bitter Lesson"
    )
    monkeypatch.setattr("builtins.input", lambda *a, **k: "n")
    rc = cli.cmd_delete(argparse.Namespace(query="bitter", yes=False))
    assert rc == 0
    assert entry_dir.exists()


def test_delete_yes_flag_skips_prompt(lib: Path):
    entry_dir = _make_library_entry(
        lib, "20260604T120000Z_bitter_a8f31c", "The Bitter Lesson"
    )
    rc = cli.cmd_delete(argparse.Namespace(query="a8f31c", yes=True))
    assert rc == 0
    assert not entry_dir.exists()


def test_delete_no_match(lib: Path, capsys: pytest.CaptureFixture[str]):
    rc = cli.cmd_delete(argparse.Namespace(query="nope", yes=False))
    assert rc == 1
    assert "No matching article found" in capsys.readouterr().err


def test_play_resolves_and_invokes_player(lib: Path, monkeypatch: pytest.MonkeyPatch):
    _make_library_entry(lib, "20260604T120000Z_bitter_a8f31c", "The Bitter Lesson")
    played: dict[str, Path] = {}
    monkeypatch.setattr(cli, "play_file", lambda p: played.update(path=p))
    rc = cli.cmd_play(argparse.Namespace(query="bitter"))
    assert rc == 0
    assert played["path"].name == "audio.mp3"


def test_multiple_match_selection(lib: Path, monkeypatch: pytest.MonkeyPatch):
    _make_library_entry(lib, "20260604T120000Z_bitter_a8f31c", "The Bitter Lesson")
    _make_library_entry(
        lib, "20260606T120000Z_bitter2_f812aa", "Bitter Lessons from AI History"
    )
    # newest-first ordering -> f812aa is #1, a8f31c is #2; pick #2.
    monkeypatch.setattr("builtins.input", lambda *a, **k: "2")
    played: dict[str, Path] = {}
    monkeypatch.setattr(cli, "play_file", lambda p: played.update(path=p))
    rc = cli.cmd_play(argparse.Namespace(query="bitter"))
    assert rc == 0
    assert "a8f31c" in str(played["path"])
