"""Browser fetcher — Playwright-based with screenshot support."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from contracts.models import Document, FetchMode, FetchPlan


async def fetch_browser(
    plan: FetchPlan,
    program_id: str,
    screenshot_path: Optional[str | Path] = None,
    raw_html_path: Optional[str | Path] = None,
) -> Document:
    """
    Fetch a URL via Playwright headless browser.
    Optionally saves a full-page screenshot and raw HTML to disk.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})

        await page.goto(plan.url, wait_until=plan.wait_until, timeout=plan.timeout_ms)

        # Execute extra actions (scroll, click, etc.)
        for action in plan.extra_actions:
            action_type = action.get("type")
            if action_type == "scroll":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            elif action_type == "click":
                selector = action.get("selector", "")
                if selector:
                    await page.click(selector, timeout=5000)
            elif action_type == "wait":
                await page.wait_for_timeout(action.get("ms", 1000))

        html = await page.content()
        text = await page.evaluate("() => document.body.innerText")
        final_url = page.url

        # Save full-page screenshot
        if screenshot_path:
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path), full_page=True)

        # Save raw HTML
        if raw_html_path:
            Path(raw_html_path).parent.mkdir(parents=True, exist_ok=True)
            Path(raw_html_path).write_text(html, encoding="utf-8")

        await browser.close()

        return Document(
            program_id=program_id,
            source_url=plan.url,
            final_url=final_url,
            fetch_mode=FetchMode.BROWSER,
            html=html,
            text=text,
            raw_path=str(raw_html_path) if raw_html_path else None,
            screenshot_path=str(screenshot_path) if screenshot_path else None,
        )
