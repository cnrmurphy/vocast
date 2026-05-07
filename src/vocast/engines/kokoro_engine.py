import numpy as np

from .engine import AudioChunk, TTSEngine


class KokoroEngine(TTSEngine):
    SAMPLE_RATE = 24000
    DEFAULT_VOICE = "af_heart"
    # Kokoro caps at ~510 phoneme tokens per inference. ~4 chars/token -> ~2000;
    # stay conservative to leave room for phonemizer expansion.
    MAX_CHARS = 1800

    def __init__(self, lang_code: str = "a"):
        from kokoro import KPipeline

        self._pipeline = KPipeline(lang_code=lang_code)

    @property
    def sample_rate(self) -> int:
        return self.SAMPLE_RATE

    @property
    def max_chars(self) -> int:
        return self.MAX_CHARS

    @property
    def default_voice(self) -> str:
        return self.DEFAULT_VOICE

    def synthesize(self, text: str, voice: str | None = None) -> AudioChunk:
        voice = voice or self.DEFAULT_VOICE
        parts: list[np.ndarray] = []
        for _gs, _ps, audio in self._pipeline(text, voice=voice):
            arr = audio.cpu().numpy() if hasattr(audio, "cpu") else np.asarray(audio)
            parts.append(arr.astype(np.float32))
        if not parts:
            return AudioChunk(np.zeros(0, dtype=np.float32), self.SAMPLE_RATE)
        return AudioChunk(np.concatenate(parts), self.SAMPLE_RATE)
