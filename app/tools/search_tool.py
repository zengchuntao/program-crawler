"""GoogleSearchTool — web search via DuckDuckGo (no captcha) + SerpAPI."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import quote_plus

import httpx

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger("crawler.tools.search")


class GoogleSearchTool(BaseTool):
    """Web search — returns a list of result URLs."""

    name = "google_search"
    description = (
        "Search the web and return result URLs with titles. "
        "Uses DuckDuckGo (no captcha) or SerpAPI (set SERPAPI_KEY). "
        "Parameters: query (required), num_results (optional, default 8)."
    )

    async def execute(self, **kwargs) -> ToolResult:
        query: str = kwargs.get("query", "")
        num_results: int = kwargs.get("num_results", 8)

        if not query:
            return ToolResult(success=False, error="query is required")

        serpapi_key = os.environ.get("SERPAPI_KEY")
        if serpapi_key:
            return await self._serpapi(query, num_results, serpapi_key)
        return await self._duckduckgo(query, num_results)

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
        """Use DuckDuckGo HTML search (no captcha issues)."""
        search_url = (
            f"https://html.duckduckgo.com/html/"
            f"?q={quote_plus(query)}"
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        try:
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=15
            ) as client:
                resp = await client.get(
                    search_url, headers=headers
                )
                resp.raise_for_status()
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

    def _parse_ddg(self, html: str, num: int) -> list[dict]:
        """Parse DuckDuckGo HTML search results."""
        results = []
        # DDG result links have class "result__a"
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"'
            r'[^>]*>(.*?)</a>',
            re.DOTALL,
        )
        for match in pattern.finditer(html):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            # DDG wraps URLs through a redirect
            if "duckduckgo.com" in url:
                # Extract actual URL from redirect
                actual = re.search(r'uddg=([^&]+)', url)
                if actual:
                    from urllib.parse import unquote
                    url = unquote(actual.group(1))
            if url.startswith("http"):
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": "",
                })
            if len(results) >= num:
                break

        # Fallback: just find all external links
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
