"""Query resolution priority: exact id/short_id first, then substring title."""

from vocast.library import LibraryEntry, match_entries


def _entry(entry_id: str, title: str) -> LibraryEntry:
    return LibraryEntry(
        id=entry_id,
        title=title,
        source=None,
        synthesized_at="2026-06-04T12:00:00+00:00",
        duration_seconds=60.0,
        voice="af_heart",
        engine="kokoro",
    )


ENTRIES = [
    _entry("20260604T120000Z_the_bitter_lesson_a8f31c", "The Bitter Lesson"),
    _entry("20260605T120000Z_why_rss_b91d22", "Why RSS Still Matters"),
    _entry(
        "20260606T120000Z_bitter_lessons_ai_f812aa", "Bitter Lessons from AI History"
    ),
]


def test_no_matches():
    assert match_entries(ENTRIES, "sqlite") == []


def test_exact_short_id():
    assert [e.title for e in match_entries(ENTRIES, "a8f31c")] == ["The Bitter Lesson"]


def test_exact_short_id_is_case_insensitive():
    assert [e.title for e in match_entries(ENTRIES, "A8F31C")] == ["The Bitter Lesson"]


def test_exact_full_id():
    result = match_entries(ENTRIES, "20260605T120000Z_why_rss_b91d22")
    assert [e.title for e in result] == ["Why RSS Still Matters"]


def test_exact_id_wins_over_title():
    # An exact id resolves outright and never falls through to title matching.
    assert len(match_entries(ENTRIES, "a8f31c")) == 1


def test_partial_title_single():
    assert [e.title for e in match_entries(ENTRIES, "rss")] == ["Why RSS Still Matters"]


def test_partial_title_is_case_insensitive():
    titles = {e.title for e in match_entries(ENTRIES, "BITTER")}
    assert titles == {"The Bitter Lesson", "Bitter Lessons from AI History"}


def test_multiple_matches():
    assert len(match_entries(ENTRIES, "bitter")) == 2


def test_short_id_derivation():
    [entry] = match_entries(ENTRIES, "rss")
    assert entry.short_id == "b91d22"
