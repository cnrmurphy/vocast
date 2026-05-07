from .audio import concat_with_silence
from .chunking import chunk_text
from .engines import AudioChunk, TTSEngine


def synthesize_article(
    text: str,
    engine: TTSEngine,
    voice: str | None = None,
    progress: bool = True,
) -> AudioChunk:
    chunks = chunk_text(text, engine.max_chars)
    if not chunks:
        raise ValueError("input text is empty")

    audio_chunks = []
    for i, chunk in enumerate(chunks, 1):
        if progress:
            print(f"[{i}/{len(chunks)}] synthesizing ({len(chunk)} chars)...")
        audio_chunks.append(engine.synthesize(chunk, voice=voice))

    return concat_with_silence(audio_chunks)
