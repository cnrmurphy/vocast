import argparse
import sys
from pathlib import Path

from . import library
from .audio import write_audio
from .engines import get_engine
from .pipeline import synthesize_article
from .server import serve


def cmd_add(args: argparse.Namespace) -> int:
    if not args.input.exists():
        print(f"error: {args.input} not found", file=sys.stderr)
        return 1
    text = args.input.read_text(encoding="utf-8")
    title = args.title or args.input.stem
    engine = get_engine(args.engine)
    voice = args.voice or engine.default_voice
    chunk = synthesize_article(text, engine, voice=voice, progress=not args.quiet)
    entry = library.add_entry(
        title=title,
        chunk=chunk,
        voice=voice,
        engine=args.engine,
        source=args.source,
    )
    if not args.quiet:
        print(f"added {entry.id} ({entry.duration_seconds:.1f}s)")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = library.list_entries()
    if not entries:
        print("(no articles)")
        return 0
    for e in entries:
        print(f"{e.id}  {e.duration_seconds:>6.1f}s  {e.title}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    print(f"vocast serving on http://{args.host}:{args.port}")
    print(f"podcast feed: http://{args.host}:{args.port}/feed.xml")
    serve(host=args.host, port=args.port)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vocast",
        description="Convert text articles to audio you can stream.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="synthesize an article and add it to the library")
    p_add.add_argument("input", type=Path, help="path to a UTF-8 text file")
    p_add.add_argument("--title", default=None, help="article title (default: filename)")
    p_add.add_argument("--source", default=None, help="source URL or attribution")
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
