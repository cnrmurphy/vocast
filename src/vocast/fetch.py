"""Fetch and extract article text from URLs using trafilatura."""

from __future__ import annotations

import trafilatura


def fetch_article(url: str) -> tuple[str | None, str]:
    """Fetch a URL and return (title, body_text).

    Raises ValueError if the URL can't be fetched or has no extractable content.
    """
    html = trafilatura.fetch_url(url)
    if html is None:
        raise ValueError(f"could not fetch {url}")

    result = trafilatura.bare_extraction(html, include_comments=False)
    if not result:
        raise ValueError(f"could not extract content from {url}")

    title = result.get("title") if isinstance(result, dict) else getattr(result, "title", None)
    text = result.get("text") if isinstance(result, dict) else getattr(result, "text", None)
    text = (text or "").strip()

    if not text:
        raise ValueError(f"extracted empty content from {url}")

    return title, text
