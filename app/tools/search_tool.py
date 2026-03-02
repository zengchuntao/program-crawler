"""SearchTool — web search via DuckDuckGo, Brave, or SerpAPI."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from urllib.parse import quote_plus, unquote

import httpx

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger("crawler.tools.search")

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


class GoogleSearchTool(BaseTool):
    """Web search — returns a list of result URLs."""

    name = "google_search"
    description = (
        "Search the web and return result URLs with titles. "
        "Tries DuckDuckGo first, falls back to Brave Search. "
        "Set SERPAPI_KEY env var to use SerpAPI instead. "
        "Parameters: query (required), num_results (optional, default 8)."
    )

    def __init__(self):
        self._ddg_blocked = False  # Track DDG captcha state

    async def execute(self, **kwargs) -> ToolResult:
        query: str = kwargs.get("query", "")
        num_results: int = kwargs.get("num_results", 8)

        if not query:
            return ToolResult(success=False, error="query is required")

        serpapi_key = os.environ.get("SERPAPI_KEY")
        if serpapi_key:
            return await self._serpapi(query, num_results, serpapi_key)

        # Try DDG first (if not previously blocked by captcha)
        if not self._ddg_blocked:
            result = await self._duckduckgo(query, num_results)
            if result.success and result.data.get("count", 0) > 0:
                return result
            # If DDG returned 0, it might be captcha — try Brave

        # Fallback to Brave Search
        result = await self._brave(query, num_results)
        if result.success and result.data.get("count", 0) > 0:
            return result

        # Last resort: retry DDG with a short delay
        if self._ddg_blocked:
            await asyncio.sleep(2)
            self._ddg_blocked = False
            return await self._duckduckgo(query, num_results)

        return ToolResult(
            success=False,
            error="All search engines returned 0 results",
        )

    async def _serpapi(
        self, query: str, num: int, api_key: str
    ) -> ToolResult:
        url = "https://serpapi.com/search.json"
        params = {
            "q": query, "api_key": api_key,
            "num": num, "engine": "google",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            results = []
            for item in data.get("organic_results", [])[:num]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return ToolResult(
                success=True,
                data={"results": results, "count": len(results)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _duckduckgo(
        self, query: str, num: int
    ) -> ToolResult:
        """Use DuckDuckGo HTML search."""
        search_url = (
            f"https://html.duckduckgo.com/html/"
            f"?q={quote_plus(query)}"
        )
        headers = {"User-Agent": _BROWSER_UA}
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15
            ) as client:
                resp = await client.get(
                    search_url, headers=headers
                )
                resp.raise_for_status()

                # Detect CAPTCHA
                if self._is_ddg_captcha(resp.text):
                    self._ddg_blocked = True
                    logger.warning(
                        "DuckDuckGo CAPTCHA detected, "
                        "switching to Brave"
                    )
                    return ToolResult(
                        success=True,
                        data={"results": [], "count": 0},
                    )

                results = self._parse_ddg(resp.text, num)

            logger.info(
                "DuckDuckGo: %d results for '%s'",
                len(results), query,
            )
            return ToolResult(
                success=True,
                data={"results": results, "count": len(results)},
            )
        except Exception as e:
            logger.warning("DuckDuckGo failed: %s", e)
            return ToolResult(success=False, error=str(e))

    async def _brave(
        self, query: str, num: int
    ) -> ToolResult:
        """Use Brave Search as fallback (no CAPTCHA issues)."""
        search_url = (
            f"https://search.brave.com/search"
            f"?q={quote_plus(query)}"
        )
        headers = {
            "User-Agent": _BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15
            ) as client:
                resp = await client.get(
                    search_url, headers=headers
                )
                resp.raise_for_status()
                results = self._parse_brave(resp.text, num)

            logger.info(
                "Brave: %d results for '%s'",
                len(results), query,
            )
            return ToolResult(
                success=True,
                data={"results": results, "count": len(results)},
            )
        except Exception as e:
            logger.warning("Brave search failed: %s", e)
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def _is_ddg_captcha(html: str) -> bool:
        """Detect DuckDuckGo CAPTCHA/bot-check page."""
        markers = [
            "Please complete the following challenge",
            "squares containing a duck",
            "confirm this search was made by a human",
            "error-lite@duckduckgo.com",
        ]
        return any(m in html for m in markers)

    @staticmethod
    def _parse_ddg(html: str, num: int) -> list[dict]:
        """Parse DuckDuckGo HTML search results."""
        results = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"'
            r'[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            url = match.group(1)
            title = re.sub(
                r'<[^>]+>', '', match.group(2)
            ).strip()
            # DDG wraps URLs through a redirect
            if "duckduckgo.com" in url:
                actual = re.search(r'uddg=([^&]+)', url)
                if actual:
                    url = unquote(actual.group(1))
            # Handle protocol-relative URLs
            if url.startswith("//"):
                url = "https:" + url
            if url.startswith("http"):
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": "",
                })
            if len(results) >= num:
                break

        # Fallback: find all external links
        if not results:
            link_pattern = re.compile(
                r'href="(https?://[^"]+)"'
            )
            seen: set[str] = set()
            skip = {"duckduckgo.com", "duck.com", "bing.com"}
            for m in link_pattern.finditer(html):
                url = m.group(1)
                if url in seen:
                    continue
                if any(d in url for d in skip):
                    continue
                seen.add(url)
                results.append({
                    "title": "", "url": url, "snippet": ""
                })
                if len(results) >= num:
                    break

        return results

    @staticmethod
    def _parse_brave(html: str, num: int) -> list[dict]:
        """Parse Brave Search HTML results."""
        results = []
        seen: set[str] = set()
        skip_domains = {
            "brave.com", "bing.com", "google.com",
            "bravesoftware.com",
        }

        # Primary: <a> tags with result-header class
        for m in re.finditer(
            r'<a[^>]+href="(https?://[^"]+)"[^>]*>'
            r'(.*?)</a>',
            html, re.DOTALL,
        ):
            url = m.group(1)
            if url in seen:
                continue
            if any(d in url for d in skip_domains):
                continue
            # Skip internal anchors and fragments
            if "#" in url and url.index("#") < len(url) - 1:
                base = url[:url.index("#")]
                if base in seen:
                    continue
                url = base
            seen.add(url)
            title = re.sub(
                r'<[^>]+>', '', m.group(2)
            ).strip()
            if title and len(title) > 5:
                results.append({
                    "title": title[:200],
                    "url": url,
                    "snippet": "",
                })
            if len(results) >= num:
                break

        return results
