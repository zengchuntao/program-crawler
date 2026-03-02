"""Evidence capture — screenshot generation and management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from contracts.models import (
    Document,
    EvidenceItem,
    Finding,
    ScreenshotType,
    generate_evidence_id,
)


def capture_full_page(
    document: Document,
    field: str = "_full_page",
) -> Optional[EvidenceItem]:
    """
    Create an EvidenceItem from the document's existing full-page screenshot.
    The screenshot must already be saved to disk (by browser_fetcher).
    """
    if not document.screenshot_path:
        return None

    return EvidenceItem(
        evidence_id=generate_evidence_id(),
        program_id=document.program_id,
        field=field,
        source_url=document.final_url,
        captured_at=document.fetched_at,
        screenshot_files=[document.screenshot_path],
        screenshot_type=ScreenshotType.FULL_PAGE,
    )


def capture_for_finding(
    finding: Finding,
    screenshot_path: str,
) -> EvidenceItem:
    """
    Create an EvidenceItem linked to a specific Finding.
    Used by the research agent when it confirms a finding and takes a screenshot.
    """
    eid = generate_evidence_id()
    return EvidenceItem(
        evidence_id=eid,
        program_id="agent",
        field=finding.field_name,
        source_url=finding.source_url,
        screenshot_files=[screenshot_path],
        screenshot_type=ScreenshotType.FULL_PAGE,
    )


async def screenshot_url(
    url: str,
    save_path: str | Path,
    timeout_ms: int = 30000,
) -> Optional[str]:
    """
    Take a full-page screenshot of a URL and save to disk.
    Returns the path string on success, None on failure.
    Used by the agent to capture evidence for findings.
    """
    from playwright.async_api import async_playwright

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(save_path), full_page=True)
            await browser.close()
            return str(save_path)
    except Exception:
        return None


async def capture_cropped(
    page,  # playwright Page object
    selector: str,
    program_id: str,
    field: str,
    source_url: str,
    save_dir: str | Path,
) -> Optional[EvidenceItem]:
    """
    Crop a specific element for field-level evidence.
    Placeholder for v1 — not required for MVP.
    """
    # TODO: Implement element-level screenshot cropping
    raise NotImplementedError("Cropped evidence capture is planned for v1")
