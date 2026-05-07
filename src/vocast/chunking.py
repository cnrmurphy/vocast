import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")
_CLAUSE_END = re.compile(r"(?<=[,;:])\s+")


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [p.strip() for p in _SENTENCE_END.split(text) if p.strip()]


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Group sentences into chunks no larger than max_chars, preserving boundaries."""
    sentences = split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for s in sentences:
        if len(s) > max_chars:
            if current:
                chunks.append(" ".join(current))
                current, current_len = [], 0
            chunks.extend(_split_long(s, max_chars))
            continue
        added = len(s) + (1 if current else 0)
        if current_len + added > max_chars:
            chunks.append(" ".join(current))
            current, current_len = [s], len(s)
        else:
            current.append(s)
            current_len += added

    if current:
        chunks.append(" ".join(current))
    return chunks


def _split_long(sentence: str, max_chars: int) -> list[str]:
    pieces = _CLAUSE_END.split(sentence)
    out: list[str] = []
    current: list[str] = []
    current_len = 0
    for p in pieces:
        if len(p) > max_chars:
            if current:
                out.append(" ".join(current))
                current, current_len = [], 0
            out.extend(_hard_wrap(p, max_chars))
            continue
        added = len(p) + (1 if current else 0)
        if current_len + added > max_chars:
            out.append(" ".join(current))
            current, current_len = [p], len(p)
        else:
            current.append(p)
            current_len += added
    if current:
        out.append(" ".join(current))
    return out


def _hard_wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    out: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for w in words:
        added = len(w) + (1 if buf else 0)
        if buf_len + added > max_chars and buf:
            out.append(" ".join(buf))
            buf, buf_len = [w], len(w)
        else:
            buf.append(w)
            buf_len += added
    if buf:
        out.append(" ".join(buf))
    return out
