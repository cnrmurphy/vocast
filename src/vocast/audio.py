import warnings
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import soundfile as sf

from .engines import AudioChunk

# pydub probes PATH for ffmpeg/avconv when it is imported and warns if neither is
# found. We supply ffmpeg via imageio-ffmpeg (set as the converter below), so on
# machines without a system ffmpeg (e.g. Windows) that probe is a false alarm —
# silence just that one warning during the import.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning
    )
    from pydub import AudioSegment  # noqa: E402

# Use the ffmpeg binary bundled with imageio-ffmpeg so users don't need a
# system ffmpeg install. pydub shells out to this for MP3 encoding.
AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()


def concat_with_silence(chunks: list[AudioChunk], gap_ms: int = 120) -> AudioChunk:
    if not chunks:
        raise ValueError("no audio chunks to concatenate")
    sr = chunks[0].sample_rate
    if any(c.sample_rate != sr for c in chunks):
        raise ValueError("sample rates differ across chunks")
    samples_per_ms = sr / 1000
    gap = np.zeros(int(samples_per_ms * gap_ms), dtype=np.float32)
    parts: list[np.ndarray] = []
    for i, c in enumerate(chunks):
        if i:
            parts.append(gap)
        parts.append(c.samples)
    return AudioChunk(np.concatenate(parts), sr)


def write_audio(chunk: AudioChunk, path: Path, mp3_bitrate: str = "96k") -> None:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".wav":
        sf.write(path, chunk.samples, chunk.sample_rate)
        return
    if suffix == ".mp3":
        pcm = np.clip(chunk.samples, -1.0, 1.0)
        pcm = (pcm * 32767).astype(np.int16)
        seg = AudioSegment(
            pcm.tobytes(),
            frame_rate=chunk.sample_rate,
            sample_width=2,
            channels=1,
        )
        seg.export(path, format="mp3", bitrate=mp3_bitrate)
        return
    raise ValueError(f"unsupported output format: {suffix!r} (use .mp3 or .wav)")
