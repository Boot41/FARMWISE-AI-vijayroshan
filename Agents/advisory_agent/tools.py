from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(__file__).parent.parent / "docs"
INDEX_PATH = DOCS_DIR / "index.json"


def search_docs(query: str) -> str:
    """
    Searches FarmWise advisory documents for fertilizer recommendations,
    government schemes, subsidies, organic farming guidance, seasonal
    outlooks, and general crop management information.

    Use this tool when you need to:
    - Find NPK or fertilizer schedules for a crop
    - Look up government scheme names, benefits, and how to apply
    - Find subsidy percentages for irrigation or inputs
    - Get the seasonal advisory outlook for Kharif or Rabi
    - Answer general crop overview questions (water requirements,
      intercropping, organic practices)

    Pass a natural language query such as:
      "wheat fertilizer NPK"
      "drip irrigation subsidy"
      "PM-KISAN scheme"
      "mustard organic farming"
      "Kharif 2026 water conservation"

    Returns the text of the top matching document chunks (up to 5 chunks).
    If no relevant chunks are found, returns an empty string.
    """
    if not INDEX_PATH.exists():
        return ""

    with INDEX_PATH.open(encoding="utf-8") as f:
        index = json.load(f)

    query_words = set(query.lower().split())

    # Score each chunk by keyword overlap with query
    scored: list[tuple[int, dict]] = []
    for chunk in index.get("chunks", []):
        chunk_keywords = set(chunk.get("keywords", []))
        # Also match against title and heading path words
        title_words = set(chunk.get("title", "").lower().split())
        heading_words = set(
            word
            for h in chunk.get("heading_path", [])
            for word in h.lower().split()
        )
        all_words = chunk_keywords | title_words | heading_words
        score = len(query_words & all_words)
        if score > 0:
            scored.append((score, chunk))

    if not scored:
        return ""

    # Sort by score descending, take top 5
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for _, chunk in scored[:5]]

    # Load unique source files and return matched chunk text
    results: list[str] = []
    for chunk in top_chunks:
        chunk_text = chunk.get("text", "").strip()
        if chunk_text and chunk_text != "---":
            heading = " > ".join(chunk.get("heading_path", []))
            results.append(f"### {heading}\n\n{chunk_text}")

    return "\n\n---\n\n".join(results) if results else ""


def get_advisory(season: str, year: int) -> str:
    """
    Reads the full seasonal crop advisory for a given season and year.

    Use this tool when the farmer asks about:
    - The seasonal outlook for Kharif or Rabi
    - Which crops are recommended this season in their region
    - Government schemes active for the current season
    - Fertilizer subsidy or input recommendations for the season
    - Water conservation advisory

    Valid seasons: kharif, rabi.
    Valid years: 2026.
    Normalise season to lowercase.
    Returns the full markdown content of the advisory.
    Returns an empty string if no advisory exists for that season and year.
    """
    season_key = season.strip().lower()
    advisory_path = DOCS_DIR / "advisories" / f"{season_key}_{year}.md"
    if not advisory_path.exists():
        return ""
    return advisory_path.read_text(encoding="utf-8")
