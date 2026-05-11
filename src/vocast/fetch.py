"""Fetch and extract article text from URLs using trafilatura."""

from __future__ import annotations

import json

import trafilatura


def fetch_article(url: str) -> tuple[str | None, str]:
    """Fetch a URL and return (title, body_text).

    Raises ValueError if the URL can't be fetched or has no extractable content.
    """
    html = trafilatura.fetch_url(url)
    if html is None:
        raise ValueError(f"could not fetch {url}")

    result = trafilatura.extract(
        html,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
    )
    if result is None:
        raise ValueError(f"could not extract content from {url}")

    data = json.loads(result)
    title = data.get("title")
    text = (data.get("text") or "").strip()

    if not text:
        raise ValueError(f"extracted empty content from {url}")

    return title, text
