"""Fetch router — automatically picks HTTP or Playwright based on content."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.util.text_utils import html_to_text, looks_like_spa
from contracts.models import Document, FetchMode, FetchPlan

logger = logging.getLogger("crawler.fetcher.router")


async def smart_fetch(
    url: str,
    screenshot_dir: Optional[str | Path] = None,
    raw_dir: Optional[str | Path] = None,
    timeout_ms: int = 30000,
) -> Document:
    """
    Intelligently fetch a URL:
    1. Try HTTP first (fast, ~200ms)
    2. If content is too thin or looks like SPA → fall back to Playwright
    3. Playwright keeps page alive for potential screenshots

    Returns a Document with text content populated.
    """
    from app.fetcher.browser_fetcher import fetch_browser_with_handle
    from app.fetcher.http_fetcher import fetch_http

    plan = FetchPlan(url=url, timeout_ms=timeout_ms)

    # Step 1: Try lightweight HTTP fetch
    try:
        http_plan = FetchPlan(url=url, mode=FetchMode.HTTP, timeout_ms=timeout_ms)
        doc = await fetch_http(http_plan, program_id="agent")
        html = doc.html or ""
        text = html_to_text(html)

        # Is the content sufficient?
        if len(text.strip()) > 200 and not looks_like_spa(html):
            # HTTP result is good enough
            doc.text = text
            logger.debug("HTTP fetch sufficient for %s (%d chars)", url, len(text))
            return doc
        else:
            logger.debug(
                "HTTP content too thin (%d chars) or SPA for %s, falling back to browser",
                len(text), url,
            )
    except Exception as e:
        logger.debug("HTTP fetch failed for %s: %s, trying browser", url, e)

    # Step 2: Fall back to Playwright
    screenshot_path = None
    raw_html_path = None
    if screenshot_dir:
        screenshot_path = str(Path(screenshot_dir) / "page.png")
    if raw_dir:
        raw_html_path = str(Path(raw_dir) / "page.html")

    plan = FetchPlan(url=url, mode=FetchMode.BROWSER, timeout_ms=timeout_ms)
    doc = await fetch_browser_with_handle(
        plan,
        program_id="agent",
        screenshot_path=screenshot_path,
        raw_html_path=raw_html_path,
    )
    return doc
