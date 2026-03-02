"""Rule-based extractors — regex patterns for common fields."""

from __future__ import annotations

import re
from typing import Optional


def extract_ielts_toefl(text: str) -> Optional[str]:
    """Extract IELTS/TOEFL/DET score requirements."""
    patterns = [
        r"IELTS[:\s]*(?:overall\s*)?(\d+(?:\.\d+)?)",
        r"TOEFL[:\s]*(?:iBT\s*)?(\d+)",
        r"Duolingo[:\s]*(?:English\s*Test\s*)?(\d+)",
        r"DET[:\s]*(\d+)",
    ]
    results = []
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            label = pat.split("[")[0]
            results.append(f"{label} {match.group(1)}")
    return "; ".join(results) if results else None


def extract_deadline_dates(text: str) -> Optional[str]:
    """Extract application deadline dates."""
    patterns = [
        # "January 15, 2025" or "Jan 15, 2025"
        r"(?:deadline|due)[:\s]*(\w+ \d{1,2},?\s*\d{4})",
        # "15 January 2025"
        r"(?:deadline|due)[:\s]*(\d{1,2}\s+\w+\s+\d{4})",
        # ISO-like "2025-01-15"
        r"(?:deadline|due)[:\s]*(\d{4}-\d{2}-\d{2})",
    ]
    results = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        results.extend(matches)
    return "; ".join(results) if results else None


def extract_credits(text: str) -> Optional[str]:
    """Extract credit/unit requirements."""
    patterns = [
        r"(\d+)\s*(?:credit|unit|cr)s?\s*(?:hour)?",
    ]
    matches = []
    for pat in patterns:
        found = re.findall(pat, text, re.IGNORECASE)
        matches.extend(found)
    if matches:
        unique = sorted(set(matches), key=int)
        return "; ".join(f"{c} credits" for c in unique)
    return None
