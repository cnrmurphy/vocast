import argparse
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import library
from .audio import write_audio
from .engines import get_engine
from .pipeline import synthesize_article


def cmd_add(args: argparse.Namespace) -> int:
    if _is_url(args.input):
        from .fetch import fetch_article

        if not args.quiet:
            print(f"fetching {args.input}...")
        try:
            fetched_title, text = fetch_article(args.input)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        title = args.title or fetched_title or "untitled"
        source = args.source or args.input
    else:
        path = Path(args.input)
        if not path.exists():
            print(f"error: {path} not found", file=sys.stderr)
            return 1
        text = path.read_text(encoding="utf-8")
        title = args.title or path.stem
        source = args.source

    engine = get_engine(args.engine)
    voice = args.voice or engine.default_voice
    chunk = synthesize_article(text, engine, voice=voice, progress=not args.quiet)
    entry = library.add_entry(
        title=title,
        chunk=chunk,
        voice=voice,
        engine=args.engine,
        source=source,
    )
    if not args.quiet:
        print(f"added {entry.id} ({entry.duration_seconds:.1f}s)")
    return 0


def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def cmd_list(args: argparse.Namespace) -> int:
    entries = library.list_entries()
    if not entries:
        print("(no articles)")
        return 0
    for e in entries:
        print(f"{e.id}  {e.duration_seconds:>6.1f}s  {e.title}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    # Imported here so non-serve commands skip ~200ms of fastapi/uvicorn loading.
    from .server import serve

    print(f"vocast serving on http://{args.host}:{args.port}")
    print(f"podcast feed: http://{args.host}:{args.port}/feed.xml")
    serve(host=args.host, port=args.port)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    print("Checking setup for serving vocast over Tailscale...")
    print()

    if not shutil.which("tailscale"):
        print("[ ] Tailscale not installed.")
        print()
        print("Install Tailscale, then re-run 'vocast init':")
        if sys.platform == "darwin":
            print("  brew install tailscale  (or https://tailscale.com/download)")
        else:
            print("  curl -fsSL https://tailscale.com/install.sh | sh")
        return 1
    print("[x] Tailscale installed.")

    status_proc = subprocess.run(
        ["tailscale", "status", "--json"],
        capture_output=True,
        text=True,
    )
    if status_proc.returncode != 0:
        print("[ ] Tailscale daemon not reachable.")
        print()
        print("Start the daemon and sign in, then re-run 'vocast init':")
        print("  sudo systemctl enable --now tailscaled")
        print("  sudo tailscale up")
        return 1

    status = json.loads(status_proc.stdout)
    if status.get("BackendState") != "Running":
        print("[ ] Not signed in to a tailnet.")
        print()
        print("Sign in (opens a browser), then re-run 'vocast init':")
        print("  sudo tailscale up")
        return 1
    print("[x] Signed in to tailnet.")

    dns_name = (status.get("Self") or {}).get("DNSName", "").rstrip(".")
    if not dns_name or "." not in dns_name:
        print("[ ] No tailnet DNS hostname available.")
        print()
        print("Enable MagicDNS, then re-run 'vocast init':")
        print("  https://login.tailscale.com/admin/dns")
        return 1
    print(f"[x] Tailnet hostname: {dns_name}")

    expected_proxy = f"http://127.0.0.1:{args.port}"
    is_configured = False
    serve_proc = subprocess.run(
        ["tailscale", "serve", "status", "--json"],
        capture_output=True,
        text=True,
    )
    if serve_proc.returncode == 0 and serve_proc.stdout.strip():
        try:
            serve_cfg = json.loads(serve_proc.stdout)
            web = serve_cfg.get("Web") or {}
            entry = web.get(f"{dns_name}:443") or {}
            handlers = entry.get("Handlers") or {}
            root = handlers.get("/") or {}
            if root.get("Proxy") == expected_proxy:
                is_configured = True
        except json.JSONDecodeError:
            pass

    if not is_configured:
        print(f"[ ] HTTPS proxy not configured for port {args.port}.")
        print()
        print("Configure it (one-time, may prompt for sudo), then re-run 'vocast init':")
        print(f"  sudo tailscale serve --bg {args.port}")
        return 1
    print(f"[x] HTTPS proxy: https://{dns_name}/  ->  {expected_proxy}")

    feed_url = f"https://{dns_name}/feed.xml"
    print()
    print("All set.")
    print()
    print(f"  Feed URL: {feed_url}")
    print()
    print("To use it:")
    print(f"  1. Start the server:        vocast serve --port {args.port}")
    print("  2. Install Tailscale on iPhone, sign in to the same tailnet.")
    print(f"  3. Open Safari, visit:      {feed_url}")
    print(f"  4. Install a direct-download podcast app and add:  {feed_url}")
    print("     Confirmed working: Downcast ($2.99). Any app that fetches feeds")
    print("     directly on-device will work; AVOID Overcast and Pocket Casts —")
    print("     they fetch feeds via their own servers, which can't reach your tailnet.")
    return 0


def cmd_synth(args: argparse.Namespace) -> int:
    if not args.input.exists():
        print(f"error: {args.input} not found", file=sys.stderr)
        return 1
    output = args.output or args.input.with_suffix(".mp3")
    text = args.input.read_text(encoding="utf-8")
    engine = get_engine(args.engine)
    chunk = synthesize_article(text, engine, voice=args.voice, progress=not args.quiet)
    write_audio(chunk, output)
    if not args.quiet:
        print(f"wrote {output}")
    return 0


def _vocast_version() -> str:
    try:
        return version("vocast")
    except PackageNotFoundError:
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vocast",
        description="Convert text articles to audio you can stream.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_vocast_version()}",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="synthesize an article and add it to the library")
    p_add.add_argument("input", type=str, help="path to a UTF-8 text file or a URL to fetch")
    p_add.add_argument("--title", default=None, help="article title (default: extracted/filename)")
    p_add.add_argument("--source", default=None, help="source URL or attribution (default: the URL if input is one)")
    p_add.add_argument("-e", "--engine", default="kokoro", help="TTS engine (default: kokoro)")
    p_add.add_argument("--voice", default=None, help="voice id (engine-specific)")
    p_add.add_argument("--quiet", action="store_true", help="suppress progress output")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="show library entries")
    p_list.set_defaults(func=cmd_list)

    p_serve = sub.add_parser("serve", help="run the HTTP server (RSS feed + audio)")
    p_serve.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8080, help="bind port (default: 8080)")
    p_serve.set_defaults(func=cmd_serve)

    p_init = sub.add_parser(
        "init",
        help="guided setup for serving the feed externally via Tailscale HTTPS",
    )
    p_init.add_argument(
        "--port",
        type=int,
        default=8080,
        help="local port that vocast serve uses (default: 8080)",
    )
    p_init.set_defaults(func=cmd_init)

    p_synth = sub.add_parser("synth", help="synthesize directly to a file (no library)")
    p_synth.add_argument("input", type=Path, help="path to a UTF-8 text file")
    p_synth.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="output audio file (default: <input>.mp3). Format: .mp3 or .wav.",
    )
    p_synth.add_argument("-e", "--engine", default="kokoro", help="TTS engine (default: kokoro)")
    p_synth.add_argument("--voice", default=None, help="voice id (engine-specific)")
    p_synth.add_argument("--quiet", action="store_true", help="suppress progress output")
    p_synth.set_defaults(func=cmd_synth)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
