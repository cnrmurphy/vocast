from .engine import AudioChunk, TTSEngine


def get_engine(name: str) -> TTSEngine:
    if name == "kokoro":
        from .kokoro_engine import KokoroEngine
        return KokoroEngine()
    raise ValueError(f"unknown engine: {name!r}")


__all__ = ["AudioChunk", "TTSEngine", "get_engine"]
