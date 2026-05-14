"""Fetch and extract article text from URLs using trafilatura."""

from __future__ import annotations

import gzip
import json
import urllib.error
import urllib.request
import zlib

import trafilatura

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _fetch_html(url: str, timeout: float = 30.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = resp.headers.get("Content-Encoding", "").lower()
            if encoding == "gzip":
                raw = gzip.decompress(raw)
            elif encoding == "deflate":
                raw = zlib.decompress(raw)
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP {e.code} {e.reason} from {url}") from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", str(e))
        raise ValueError(f"network error fetching {url}: {reason}") from e
    except TimeoutError:
        raise ValueError(f"timed out fetching {url}") from None


def fetch_article(url: str) -> tuple[str | None, str]:
    """Fetch a URL and return (title, body_text).

    Raises ValueError if the URL can't be fetched or has no extractable content.
    """
    html = _fetch_html(url)

    result = trafilatura.extract(
        html,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
        prune_xpath=["//pre"],
    )
    if result is None:
        raise ValueError(f"could not extract content from {url}")

    data = json.loads(result)
    title = data.get("title")
    text = (data.get("text") or "").strip()

    if not text:
        raise ValueError(f"extracted empty content from {url}")

    return title, text
