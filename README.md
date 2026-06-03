# Vocast

Convert articles to audio using local TTS models.

## Why

I wanted a way to convert articles into audio that I could stream to my mobile device while on the go. This seemed straightforward enough to build myself
and I didn't want to pay for an app. 

## How

Vocast uses Kokoro for TTS. It can fetch articles from a given URL or local text file. Audio files are saved to `~/.vocast/library`. It provides an HTTP server
that exposes an RSS feed allowing for podcast apps to discover the converted audio files. You can use Tailscale to allow connections between the server and client devices
like your mobile phone. You will need to use a podcast app that does not proxy requests through their own servers as that will prevent the app from connecting to your Vocast server.

## Requirements

- Python 3.10–3.12 (Kokoro does not yet support 3.13). Installing with `uv` provisions a compatible Python for you.
- `espeak-ng` on PATH (used by Kokoro as a fallback phonemizer)

ffmpeg is bundled (via `imageio-ffmpeg`), so the only system dependency is `espeak-ng`:

```
sudo dnf install espeak-ng     # Fedora
sudo apt install espeak-ng     # Debian/Ubuntu
brew install espeak-ng         # macOS
```

## Install

The recommended way is an isolated tool install, which also provisions a compatible Python for you and puts a `vocast` command on your PATH:

```
uv tool install vocast
# or, with pipx:
pipx install vocast
```

The first run downloads the Kokoro weights (~300 MB) and a small spaCy model into the cache. Subsequent runs are immediate.

### From source (development)

```
uv venv && source .venv/bin/activate
uv pip install -e .
```

## Usage

Vocast has subcommands; run `vocast --help` to see them all.

### Add an article to the library

```
vocast add https://example.com/article    # fetch and synthesize a URL
vocast add notes.txt                      # synthesize a local text file
vocast add ... --title "Custom title"     # override the title
vocast add ... --voice af_bella           # use a different Kokoro voice
vocast add ... --quiet                    # suppress per-chunk progress
```

URLs are fetched and cleaned with `trafilatura`. Code blocks (`<pre>` elements) are stripped before synthesis since they don't translate well to audio. Each entry is stored under `~/.vocast/library/<id>/` as `audio.mp3` plus `meta.json` with title, source URL, duration, and voice.

### List the library

```
vocast list
```

### Serve the library as a podcast feed

```
vocast serve                                # 127.0.0.1:8080 by default
vocast serve --host 0.0.0.0 --port 8000     # custom host/port
```

Exposes `GET /feed.xml` (podcast RSS) and `GET /audio/<id>.mp3` (audio enclosures). Long articles are split on sentence boundaries during synthesis and concatenated with short silence between chunks.

### Expose the feed to your phone over Tailscale

```
vocast init
```

A guided checklist that walks you through installing Tailscale, signing into your tailnet, and proxying `vocast serve` over HTTPS via `tailscale serve`. Re-run after each step until it prints your feed URL, then add that URL to a direct-download podcast app (Downcast is confirmed working).

### Synthesize directly to a file (skip the library)

```
vocast synth article.txt              # writes article.mp3
vocast synth article.txt -o out.wav   # WAV output
```

