"""Text utilities — HTML to plain text, text truncation, SPA detection."""

from __future__ import annotations

import re
from html.parser import HTMLParser


class _HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter — strips tags, keeps text content."""

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript", "svg", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True
        if tag in ("br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self._pieces.append("\n")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse whitespace but preserve paragraph breaks
        lines = raw.split("\n")
        cleaned = []
        for line in lines:
            stripped = " ".join(line.split())
            if stripped:
                cleaned.append(stripped)
        return "\n".join(cleaned)


def html_to_text(html: str) -> str:
    """Convert HTML to plain text by stripping tags."""
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def truncate_text(text: str, max_chars: int = 15000) -> str:
    """Truncate text to max_chars, appending a notice if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... text truncated ...]"


# SPA detection markers
_SPA_MARKERS = [
    'id="__next"',
    'id="root"',
    'id="app"',
    'id="__nuxt"',
    "data-reactroot",
    "data-server-rendered",
    'ng-version="',
    "<noscript>",
]


def looks_like_spa(html: str) -> bool:
    """Heuristic check: does the HTML look like a client-side rendered SPA?"""
    html_lower = html.lower()
    # Check for SPA markers
    for marker in _SPA_MARKERS:
        if marker.lower() in html_lower:
            # SPA marker found — but is there actual content?
            text = html_to_text(html)
            # If text body is very short despite SPA markers, probably needs JS
            if len(text.strip()) < 200:
                return True
    return False


def extract_links(html: str, base_url: str = "") -> list[str]:
    """Extract all href links from HTML."""
    pattern = r'href=["\']([^"\']+)["\']'
    raw_links = re.findall(pattern, html)
    links = []
    for link in raw_links:
        if link.startswith("http"):
            links.append(link)
        elif link.startswith("/") and base_url:
            # Resolve relative URLs
            from urllib.parse import urljoin
            links.append(urljoin(base_url, link))
    return list(dict.fromkeys(links))  # dedupe preserving order
