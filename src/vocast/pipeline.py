from pathlib import Path

from .audio import concat_with_silence, write_audio
from .chunking import chunk_text
from .engines import TTSEngine


def synthesize_article(
    text: str,
    engine: TTSEngine,
    output: Path,
    voice: str | None = None,
    progress: bool = True,
) -> None:
    chunks = chunk_text(text, engine.max_chars)
    if not chunks:
        raise ValueError("input text is empty")

    audio_chunks = []
    for i, chunk in enumerate(chunks, 1):
        if progress:
            print(f"[{i}/{len(chunks)}] synthesizing ({len(chunk)} chars)...")
        audio_chunks.append(engine.synthesize(chunk, voice=voice))

    combined = concat_with_silence(audio_chunks)
    write_audio(combined, output)
