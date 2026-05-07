"""HTTP server — exposes the library as a podcast RSS feed + audio endpoints."""

from __future__ import annotations

from datetime import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response

from .library import LibraryEntry, get_entry, list_entries


def create_app() -> FastAPI:
    app = FastAPI(title="vocast", docs_url=None, redoc_url=None)

    @app.get("/")
    def index() -> Response:
        n = len(list_entries())
        suffix = "s" if n != 1 else ""
        return PlainTextResponse(f"vocast — {n} article{suffix}\nfeed: /feed.xml\n")

    @app.get("/feed.xml")
    def feed(request: Request) -> Response:
        base = str(request.base_url).rstrip("/")
        xml = _build_rss(list_entries(), base)
        return Response(content=xml, media_type="application/rss+xml; charset=utf-8")

    @app.get("/audio/{entry_id}.mp3")
    def audio(entry_id: str) -> Response:
        entry = get_entry(entry_id)
        if entry is None:
            return PlainTextResponse("not found", status_code=404)
        path = entry.audio_path()
        if not path.exists():
            return PlainTextResponse("audio missing", status_code=404)
        return FileResponse(path, media_type="audio/mpeg")

    return app


def _build_rss(entries: list[LibraryEntry], base_url: str) -> str:
    items: list[str] = []
    for e in entries:
        try:
            pub = datetime.fromisoformat(e.synthesized_at)
        except ValueError:
            pub = datetime.now()
        size = e.audio_path().stat().st_size if e.audio_path().exists() else 0
        url = f"{base_url}/audio/{e.id}.mp3"
        items.append(
            f"""    <item>
      <title>{escape(e.title)}</title>
      <description>{escape(e.title)}</description>
      <guid isPermaLink="false">{escape(e.id)}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <enclosure url="{escape(url)}" length="{size}" type="audio/mpeg" />
      <itunes:duration>{int(e.duration_seconds)}</itunes:duration>
    </item>"""
        )
    items_xml = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>vocast</title>
    <link>{escape(base_url)}</link>
    <description>Self-hosted articles-as-podcasts</description>
    <language>en-us</language>
{items_xml}
  </channel>
</rss>
"""


def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    import uvicorn

    uvicorn.run(create_app(), host=host, port=port, log_level="info")
