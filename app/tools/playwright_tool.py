"""PlaywrightTool — full browser with JS rendering."""

from __future__ import annotations

import logging
from pathlib import Path

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger("crawler.tools.playwright")


class PlaywrightTool(BaseTool):
    """Playwright headless Chromium — renders JS, supports screenshots."""

    name = "playwright"
    description = (
        "Full headless browser (Chromium) that renders JavaScript. "
        "Can take screenshots, execute scroll/click actions, "
        "and extract rendered page text. Slower than HTTP (~3-5s) "
        "but handles SPAs and dynamic content. "
        "Parameters: url (required), screenshot_path (optional), "
        "wait_until (optional: domcontentloaded/networkidle/load)."
    )

    async def execute(self, **kwargs) -> ToolResult:
        url: str = kwargs.get("url", "")
        screenshot_path: str | None = kwargs.get("screenshot_path")
        wait_until: str = kwargs.get("wait_until", "domcontentloaded")
        timeout_ms: int = kwargs.get("timeout_ms", 30000)

        if not url:
            return ToolResult(success=False, error="url is required")

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page(
                    viewport={"width": 1280, "height": 900}
                )
                await page.goto(
                    url, wait_until=wait_until, timeout=timeout_ms
                )
                await page.wait_for_timeout(1500)

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
            logger.warning("Playwright fetch failed for %s: %s", url, e)
            return ToolResult(success=False, error=str(e))
