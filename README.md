# Vocast

Convert articles to audio using local TTS models.

## Status

Early. The CLI works end-to-end. No server, URL fetching, streaming, or UI yet — plain text in, audio file out.

## Requirements

- Python 3.10–3.12 (Kokoro does not yet support 3.13)
- `ffmpeg` on PATH (used for MP3 encoding)
- `espeak-ng` on PATH (used by Kokoro as a fallback phonemizer)

On Fedora:

```
sudo dnf install ffmpeg espeak-ng
```

## Install

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The first run downloads the Kokoro weights (~300 MB) and a small spaCy model into the cache. Subsequent runs are immediate.

## Usage

```
vocast article.txt                   # writes article.mp3
vocast article.txt -o out.wav        # WAV output
vocast article.txt --voice af_bella  # different Kokoro voice
vocast article.txt --quiet           # suppress per-chunk progress
```

Long articles are split on sentence boundaries (Kokoro has a per-call token limit), each piece is synthesized separately, and the results are concatenated with a short silence between chunks.

## Project layout

```
src/vocast/
  cli.py             CLI entry point
  pipeline.py        text -> chunks -> audio -> file
  chunking.py        sentence-aware splitting
  audio.py           concat + WAV/MP3 encoding
  engines/
    engine.py        TTSEngine ABC + AudioChunk
    kokoro_engine.py
    __init__.py      get_engine(name) factory
```

## Adding a TTS engine

Implement `TTSEngine` in `src/vocast/engines/` and add a branch to `get_engine` in `engines/__init__.py`. The pipeline only sees the abstract interface, so no other code changes.

```python
from .engine import AudioChunk, TTSEngine

class MyEngine(TTSEngine):
    @property
    def sample_rate(self) -> int: ...
    @property
    def max_chars(self) -> int: ...
    @property
    def default_voice(self) -> str: ...
    def synthesize(self, text: str, voice: str | None = None) -> AudioChunk: ...
```
