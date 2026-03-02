"""HttpTool — lightweight HTTP fetch using httpx."""

from __future__ import annotations

import logging
import re

import httpx

from app.tools.base import BaseTool, ToolResult
from app.util.text_utils import html_to_text

logger = logging.getLogger("crawler.tools.http")


def _extract_title(html: str) -> str:
    """Extract <title> from HTML."""
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


class HttpTool(BaseTool):
    """Plain HTTP GET — fast (~200ms), no JS rendering."""

    name = "http_fetch"
    description = (
        "Fast HTTP GET request. Returns page HTML and extracted text. "
        "Cannot render JavaScript. Best for static pages and APIs. "
        "Parameters: url (required), timeout_s (optional, default 10)."
    )

    async def execute(self, **kwargs) -> ToolResult:
        url: str = kwargs.get("url", "")
        timeout_s: float = kwargs.get("timeout_s", 10)

        if not url:
            return ToolResult(success=False, error="url is required")

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            }
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=timeout_s
            ) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()

            html = resp.text
            text = html_to_text(html)
            title = _extract_title(html)

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "final_url": str(resp.url),
                    "status_code": resp.status_code,
                    "title": title,
                    "html": html,
                    "text": text,
                    "text_length": len(text),
                },
            )
        except Exception as e:
            logger.warning("HTTP fetch failed for %s: %s", url, e)
            return ToolResult(success=False, error=str(e))
