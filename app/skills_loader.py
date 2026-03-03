"""Skill loader — loads agent knowledge from skills/ directory."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger("crawler.skills")

_SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def load_skill_md() -> str:
    """Load skills/skill.md as text for LLM context."""
    path = _SKILLS_DIR / "skill.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning("skill.md not found at %s", path)
    return ""


def load_soul_md() -> str:
    """Load skills/soul.md as text for LLM context."""
    path = _SKILLS_DIR / "soul.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning("soul.md not found at %s", path)
    return ""


def load_university_registry() -> dict:
    """Load skills/university_registry.yaml as a dict."""
    path = _SKILLS_DIR / "university_registry.yaml"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    logger.warning("university_registry.yaml not found at %s", path)
    return {}


def match_university(
    query_text: str, registry: dict | None = None,
) -> list[dict]:
    """Match a query against the university registry.

    Returns a list of matched university entries with their
    entry_points and notes.

    Uses longest-match-first to avoid false positives
    (e.g. "City University of Hong Kong" should not match
    "University of Hong Kong").
    """
    if registry is None:
        registry = load_university_registry()

    query_lower = query_text.lower()

    # Collect all (alias, uni_data) pairs, sort by alias length desc
    # so longer/more specific aliases match first
    candidates = []
    for region, universities in registry.items():
        if not isinstance(universities, dict):
            continue
        for uni_key, uni_data in universities.items():
            if not isinstance(uni_data, dict):
                continue
            aliases = uni_data.get("aliases", [])
            for alias in aliases:
                candidates.append((
                    alias.lower(), uni_key, region, uni_data,
                ))

    # Sort by alias length descending (longest first)
    candidates.sort(key=lambda x: len(x[0]), reverse=True)

    matches = []
    matched_keys: set[str] = set()
    matched_spans: list[tuple[int, int]] = []

    for alias, uni_key, region, uni_data in candidates:
        if uni_key in matched_keys:
            continue
        idx = query_lower.find(alias)
        if idx < 0:
            continue
        # Check no longer match already covers this span
        span = (idx, idx + len(alias))
        if any(s <= span[0] and e >= span[1] for s, e in matched_spans):
            continue

        matched_keys.add(uni_key)
        matched_spans.append(span)
        matches.append({
            "key": uni_key,
            "region": region,
            "aliases": uni_data.get("aliases", []),
            "entry_points": uni_data.get("entry_points", []),
            "notes": uni_data.get("notes", ""),
        })

    return matches


def get_entry_urls(query_text: str) -> list[str]:
    """Get known entry-point URLs for universities mentioned in query."""
    matches = match_university(query_text)
    urls = []
    for m in matches:
        for ep in m["entry_points"]:
            urls.append(ep["url"])
    return urls


def get_skill_context_for_planner(query: str) -> str:
    """Build a concise skill context string for the planner LLM.

    Includes matched university info and relevant strategy hints.
    """
    matches = match_university(query)
    if not matches:
        return ""

    parts = ["[University Knowledge]"]
    for m in matches:
        parts.append(
            f"University: {m['aliases'][0]} ({m['region']})"
        )
        if m["notes"]:
            parts.append(f"  Notes: {m['notes']}")
        parts.append("  Known pages:")
        for ep in m["entry_points"]:
            parts.append(f"    - {ep['url']} ({ep['label']})")

    return "\n".join(parts)
