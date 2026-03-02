"""Google search — direct scraping with Playwright fallback, SerpAPI optional."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger("crawler.fetcher.google_search")


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str


async def google_search(query: str, num_results: int = 8) -> list[SearchResult]:
    """
    Search Google for a query. Tries strategies in order:
    1. SerpAPI (if SERPAPI_KEY is set)
    2. Direct HTTP scrape of Google
    3. Playwright render of Google (if HTTP is blocked)
    """
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if serpapi_key:
        return await _serpapi_search(query, num_results, serpapi_key)
    return await _direct_search(query, num_results)


async def _serpapi_search(query: str, num_results: int, api_key: str) -> list[SearchResult]:
    """Use SerpAPI for reliable search results."""
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "engine": "google",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("organic_results", [])[:num_results]:
        results.append(SearchResult(
            title=item.get("title", ""),
            url=item.get("link", ""),
            snippet=item.get("snippet", ""),
        ))
    return results


async def _direct_search(query: str, num_results: int) -> list[SearchResult]:
    """Direct HTTP scrape of Google search results page."""
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(search_url, headers=headers)
            resp.raise_for_status()
            return _parse_google_html(resp.text, num_results)
    except Exception as e:
        logger.warning("Direct Google search failed (%s), trying Playwright", e)
        return await _playwright_search(search_url, num_results)


async def _playwright_search(search_url: str, num_results: int) -> list[SearchResult]:
    """Fallback: render Google search page with Playwright."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            html = await page.content()
            await browser.close()
            return _parse_google_html(html, num_results)
    except Exception as e:
        logger.error("Playwright Google search also failed: %s", e)
        return []


def _parse_google_html(html: str, num_results: int) -> list[SearchResult]:
    """Parse Google search HTML to extract results."""
    results = []

    # Pattern: look for links with /url?q= or direct links in search results
    # Google wraps results in <a> tags — we look for the main result links
    # and their surrounding text
    url_pattern = re.compile(r'/url\?q=([^&"]+)')
    urls_found = url_pattern.findall(html)

    # Also try direct href patterns for newer Google HTML
    direct_pattern = re.compile(r'<a[^>]+href="(https?://[^"]+)"[^>]*>')
    direct_urls = direct_pattern.findall(html)

    # Combine and dedupe, filtering out google.com internal links
    all_urls = []
    seen = set()
    for url in urls_found + direct_urls:
        url = url.split("&")[0]  # Remove tracking params from /url?q= results
        if (
            url not in seen
            and "google.com" not in url
            and "googleapis.com" not in url
            and "gstatic.com" not in url
            and url.startswith("http")
        ):
            seen.add(url)
            all_urls.append(url)

    for url in all_urls[:num_results]:
        results.append(SearchResult(
            title="",  # Title extraction from raw HTML is unreliable
            url=url,
            snippet="",
        ))

    return results
