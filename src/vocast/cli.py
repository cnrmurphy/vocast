import argparse
import sys
from pathlib import Path

from .engines import get_engine
from .pipeline import synthesize_article


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vocast",
        description="Convert a text article into an audio file using a local TTS model.",
    )
    parser.add_argument("input", type=Path, help="path to a UTF-8 text file")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="output audio file (default: <input>.mp3). Format inferred from extension (.mp3, .wav).",
    )
    parser.add_argument(
        "-e", "--engine", default="kokoro",
        help="TTS engine to use (default: kokoro)",
    )
    parser.add_argument("--voice", default=None, help="voice id (engine-specific)")
    parser.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: {args.input} not found", file=sys.stderr)
        return 1

    output = args.output or args.input.with_suffix(".mp3")
    text = args.input.read_text(encoding="utf-8")

    engine = get_engine(args.engine)
    synthesize_article(text, engine, output, voice=args.voice, progress=not args.quiet)

    if not args.quiet:
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
