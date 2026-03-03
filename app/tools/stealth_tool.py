"""StealthBrowserTool — anti-detection browser using playwright-stealth."""

from __future__ import annotations

import logging
from pathlib import Path

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger("crawler.tools.stealth")


class StealthBrowserTool(BaseTool):
    """Stealth browser — Playwright + anti-detection patches."""

    name = "stealth_browser"
    description = (
        "Headless browser with stealth anti-detection (hides "
        "automation fingerprints). Use when a site blocks normal "
        "Playwright or returns CAPTCHAs. Slower than regular "
        "Playwright but bypasses bot detection. "
        "Parameters: url (required), screenshot_path (optional)."
    )

    async def execute(self, **kwargs) -> ToolResult:
        url: str = kwargs.get("url", "")
        screenshot_path: str | None = kwargs.get("screenshot_path")
        timeout_ms: int = kwargs.get("timeout_ms", 30000)

        if not url:
            return ToolResult(success=False, error="url is required")

        try:
            from playwright.async_api import async_playwright
            from playwright_stealth import Stealth

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features="
                        "AutomationControlled",
                    ],
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X "
                        "10_15_7) AppleWebKit/537.36 (KHTML, like "
                        "Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                )
                page = await context.new_page()
                async with Stealth(page):
                    await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )
                    await page.wait_for_timeout(2000)

                    html = await page.content()
                    text = await page.evaluate(
                        "() => document.body.innerText"
                    )
                    title = await page.title()
                    final_url = page.url

                    if screenshot_path:
                        Path(screenshot_path).parent.mkdir(
                            parents=True, exist_ok=True
                        )
                        await page.screenshot(
                            path=screenshot_path, full_page=True
                        )

                await browser.close()

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "final_url": final_url,
                    "title": title,
                    "html": html,
                    "text": text,
                    "text_length": len(text),
                    "screenshot_path": screenshot_path,
                },
            )
        except Exception as e:
            logger.warning(
                "Stealth browser failed for %s: %s", url, e
            )
            return ToolResult(success=False, error=str(e))
