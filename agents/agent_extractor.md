# Agent-Extractor: LLM Extraction + Evidence Reference Strategy

You are Agent-Extractor, responsible for converting `Document` into `ProgramRecord` field values, with field→evidence mapping.

## Goal

Implement "rules-first + LLM fallback" extractor that outputs `contracts`-compliant `ProgramRecord` (including `warnings`).

## Deliverables

1. **`app/extractor/llm_extractor.py`**: `extract_with_llm(document) -> ExtractedFields` (LLM output must be strict JSON via `response_format`)
2. **`app/extractor/rule_extractors.py`**: At least 3 rule-based extractors:
   - Deadline dates (various formats)
   - IELTS/TOEFL/DET scores
   - Credits/units
3. **`app/validate/validator.py`**: Field format validation (date ranges, score ranges, empty critical fields) → returns `warnings[]`

## Evidence Strategy (MVP)

- MVP: All fields share the same `full_page` evidence — each field's `evidence_ids` points to the full-page `EvidenceItem`'s ID
- v1 upgrade: Return "field locator hints" (keywords, DOM selectors) so `evidence/capture.py` can crop per-field

## Constraints

- LLM failure MUST return `ProgramRecord(status=partial, warnings=[...])` — NEVER raise exceptions
- Rule extractors augment (not replace) LLM results — only fill in if LLM returned `null`
- Page text truncated to 15k chars for LLM to control costs
- Uses `OPENAI_API_KEY` env var, configurable model and base_url

## Acceptance Criteria

- `extract_with_llm()` returns `ExtractedFields` even on API error (empty fields + warning)
- Rule extractors pass tests in `tests/test_extractors.py`
- Validator catches: unusual GPA (>4.0 but <10), IELTS out of [0-9], TOEFL out of [40-120], missing critical fields

## Key Contracts

```python
from contracts.models import Document, ExtractedFields, EvidenceRefs, ProgramRecord, CrawlStatus
```
