from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class AudioChunk:
    samples: np.ndarray  # float32, mono, in [-1, 1]
    sample_rate: int


class TTSEngine(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice: str | None = None) -> AudioChunk: ...

    @property
    @abstractmethod
    def sample_rate(self) -> int: ...

    @property
    @abstractmethod
    def max_chars(self) -> int: ...

    @property
    @abstractmethod
    def default_voice(self) -> str: ...
