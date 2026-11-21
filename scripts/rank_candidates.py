#!/usr/bin/env python3
"""Rank listening-material candidates by reliability, freshness, and fit.

The ranking is deliberately deterministic so different users and domains get
the same source-type priority. It is a shortlist aid, not a claim that a page is
the newest or that an auto transcript is correct.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

SOURCE_SCORES = {
    "official_article_audio": 100,
    "official_podcast_transcript": 90,
    "official_talk_transcript": 85,
    "conference_transcript": 75,
    "interview_transcript": 70,
    "auto_caption_video": 55,
    "text_only": 0,
}
TRANSCRIPT_SCORES = {
    "official": 20,
    "human_edited": 18,
    "auto_generated": 8,
    "none": 0,
    "unknown": 2,
}
ACCESS_SCORES = {"public": 10, "registration": 3, "paywalled": -5, "login": -5, "unknown": 0}
QUALITY_SCORES = {"high": 10, "medium": 5, "low": 0, "unknown": 0}
DURATION_BONUS = [(300, 10), (240, 5), (180, 2)]


def parse_date(value: Any) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def freshness_score(published_at: Any, as_of: dt.date) -> int:
    published = parse_date(published_at)
    if not published:
        return 0
    age = (as_of - published).days
    if age < 0:
        return 5  # future-dated metadata is suspicious and should be checked
    if age <= 180:
        return 25
    if age <= 365:
        return 20
    if age <= 730:
        return 10
    return 0


def duration_seconds(value: Any) -> int:
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value or "")
    parts = [int(part) for part in text.split(":") if part.isdigit()]
    if not parts:
        return 0
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def rank_candidate(candidate: dict[str, Any], as_of: dt.date) -> dict[str, Any]:
    source_type = str(candidate.get("source_type") or candidate.get("format") or "").lower()
    if source_type == "article_audio":
        source_type = "official_article_audio"
    transcript_type = str(candidate.get("transcript_type") or "unknown").lower()
    if transcript_type in {"official_article_text", "official_published_transcript", "published_transcript"}:
        transcript_type = "official"
    access = str(candidate.get("access") or "unknown").lower()
    quality = str(candidate.get("quality") or "unknown").lower()
    score = SOURCE_SCORES.get(source_type, 35)
    score += TRANSCRIPT_SCORES.get(transcript_type, 2)
    score += ACCESS_SCORES.get(access, 0)
    score += QUALITY_SCORES.get(quality, 0)
    score += freshness_score(candidate.get("published_at"), as_of)
    seconds = duration_seconds(candidate.get("duration") or candidate.get("audio_duration") or candidate.get("duration_seconds"))
    for minimum, bonus in DURATION_BONUS:
        if seconds >= minimum:
            score += bonus
            break
    if candidate.get("listen_to_article") is True:
        score += 10
    url_status = str(candidate.get("url_status") or "unknown").lower()
    if url_status in {"verified", "user_provided_verified"}:
        score += 10
    elif url_status == "inferred":
        score -= 15
    elif url_status == "blocked":
        score -= 5
    if candidate.get("transcript_url") and candidate.get("source_url"):
        score += 5
    ranked = dict(candidate)
    ranked["score"] = score
    ranked["eligible"] = source_type != "text_only" and transcript_type not in {"none", "unknown"} and seconds >= 180
    return ranked


def rank_candidates(candidates: list[dict[str, Any]], as_of: dt.date) -> list[dict[str, Any]]:
    ranked = [rank_candidate(candidate, as_of) for candidate in candidates]
    return sorted(ranked, key=lambda item: (not item["eligible"], -item["score"], str(item.get("published_at") or "")), reverse=False)


def to_markdown(items: list[dict[str, Any]]) -> str:
    lines = ["| Rank | Score | Source type | Published | Duration | Transcript | Access | Title |", "|---:|---:|---|---|---:|---|---|---|"]
    for index, item in enumerate(items, 1):
        lines.append(
            f"| {index} | {item['score']} | {item.get('source_type') or item.get('format') or ''} | "
            f"{item.get('published_at') or 'unknown'} | {item.get('audio_duration') or item.get('duration') or ''} | "
            f"{item.get('transcript_type') or 'unknown'} | {item.get('access') or 'unknown'} | {item.get('title') or ''} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="JSON array of candidate records")
    parser.add_argument("--as-of", default=dt.date.today().isoformat())
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(candidates, list):
        raise SystemExit("candidates JSON must be an array")
    ranked = rank_candidates(candidates, dt.date.fromisoformat(args.as_of))
    if args.format == "markdown":
        print(to_markdown(ranked))
    else:
        print(json.dumps(ranked, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
