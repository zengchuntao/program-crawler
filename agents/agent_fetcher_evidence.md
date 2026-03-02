# Agent-Fetcher&Evidence: Fetch + Screenshot Capture

You are Agent-Fetcher&Evidence, responsible for "given URL → get Document → generate screenshot evidence".

## Goal

Implement HTTP fetch + Playwright browser fetch (at least MVP supports `browser_only`), and save screenshots organized by `program_id`.

## Deliverables

1. **`app/fetcher/http_fetcher.py`**: Returns `Document` (html/text/final_url/metadata)
2. **`app/fetcher/browser_fetcher.py`**: Playwright opens page, waits (domcontentloaded/networkidle), saves rendered HTML, returns `Document`, generates full_page screenshot
3. **`app/evidence/capture.py`**: `capture_full_page(document) -> EvidenceItem`, plus `capture_cropped(...)` interface (stub for v1)
4. **Tests**: Smoke test against a public webpage (do not depend on private network)

## Constraints

- No adversarial bypass — return `status=failed + reason` for strong anti-bot pages
- File paths MUST be configurable via `out_dir` parameter
- Screenshots saved to `out/evidence/<program_id>/full_page.png`
- Raw HTML saved to `out/raw/<program_id>/page.html`

## Acceptance Criteria

- Each URL produces at least 1 screenshot AND 1 raw HTML file (in browser mode)
- `Document` returned matches `contracts.models.Document` schema exactly
- `EvidenceItem` returned with correct `screenshot_files[]` paths

## Key Contracts (import from contracts.models)

```python
from contracts.models import Document, FetchPlan, FetchMode, EvidenceItem, ScreenshotType
```
