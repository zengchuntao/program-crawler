"""Evidence capture — screenshot generation and management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from contracts.models import Document, EvidenceItem, ScreenshotType, generate_evidence_id


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
    # locator = page.locator(selector)
    # bbox = await locator.bounding_box()
    # if bbox: await page.screenshot(clip=bbox, path=...)
    raise NotImplementedError("Cropped evidence capture is planned for v1")
