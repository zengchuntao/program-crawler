"""ScreenshotTool — take full-page screenshots of URLs."""

from __future__ import annotations

import logging
from pathlib import Path

from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger("crawler.tools.screenshot")


class ScreenshotTool(BaseTool):
    """Take a full-page screenshot of a URL."""

    name = "screenshot"
    description = (
        "Take a full-page screenshot of a web page and save as PNG. "
        "Uses Playwright headless browser. "
        "Parameters: url (required), save_path (required)."
    )

    async def execute(self, **kwargs) -> ToolResult:
        url: str = kwargs.get("url", "")
        save_path: str = kwargs.get("save_path", "")

        if not url or not save_path:
            return ToolResult(
                success=False,
                error="url and save_path are required",
            )

        try:
            from playwright.async_api import async_playwright

            Path(save_path).parent.mkdir(
                parents=True, exist_ok=True
            )

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page(
                    viewport={"width": 1280, "height": 900}
                )
                try:
                    await page.goto(
                        url,
                        wait_until="load",
                        timeout=15000,
                    )
                except Exception:
                    # Timeout is OK — take screenshot anyway
                    pass
                await page.wait_for_timeout(1000)
                await page.screenshot(
                    path=save_path, full_page=True
                )
                await browser.close()

            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "screenshot_path": save_path,
                },
            )
        except Exception as e:
            logger.warning(
                "Screenshot failed for %s: %s", url, e
            )
            return ToolResult(success=False, error=str(e))
