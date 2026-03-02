# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Program Crawler** — a CLI tool that crawls academic program pages, extracts structured data (admission requirements, deadlines, tuition, etc.), captures screenshot evidence, and exports to Excel with full audit trail.

## Commands

```bash
# Install (Python 3.11+)
pip install -e ".[dev]"

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_contracts.py -v

# Run a single test
pytest tests/test_contracts.py::TestProgramInput::test_auto_id_generation -v

# Lint
ruff check .

# Fix lint issues
ruff check --fix .

# Run the crawler
python -m app.runner --input tests/fixtures/inputs.csv --out out/

# Run with http-first mode (cheaper, falls back to browser)
python -m app.runner -i input.csv -o out/ --mode http_first --concurrency 5
```

## Architecture

### Contracts-First Design

All modules depend on `contracts/models.py` (Pydantic) and `contracts/columns.yaml` — these are **frozen interfaces**. Do not rename or remove fields; only append new optional fields.

**Core data flow:**
```
ProgramInput → FetchPlan → Document → ExtractedFields → ProgramRecord + EvidenceItem[] → results.xlsx
```

**Key models:**
- `ProgramInput`: One row from input CSV/JSONL (required: `program_url`)
- `FetchPlan`: How to fetch a URL (mode, wait strategy, timeout, extra actions)
- `Document`: Unified post-fetch representation (html, text, screenshot path, raw path)
- `ExtractedFields`: The 9 data fields we extract (GPA, language, deadlines, etc.)
- `EvidenceItem`: One evidence record with `screenshot_files[]` (supports multiple screenshots)
- `EvidenceRefs`: Maps each extracted field to its supporting evidence IDs
- `ProgramRecord`: Final output row = metadata + ExtractedFields + EvidenceRefs + status/warnings
- `RunLogEntry`: One line in `run_log.jsonl`

### Module Layout

| Module | Purpose | Key function/class |
|---|---|---|
| `app/runner.py` | CLI + async orchestrator | `main()`, `run()`, `load_inputs()` |
| `app/plugins/generic.py` | Default pipeline: fetch→extract→export | `process_program()` |
| `app/fetcher/http_fetcher.py` | Plain HTTP fetch via httpx | `fetch_http(plan, pid)` |
| `app/fetcher/browser_fetcher.py` | Playwright headless browser | `fetch_browser(plan, pid, screenshot_path, raw_path)` |
| `app/evidence/capture.py` | Screenshot evidence creation | `capture_full_page(doc, field)` |
| `app/extractor/llm_extractor.py` | LLM-based field extraction | `extract_with_llm(doc, api_key, model)` |
| `app/extractor/rule_extractors.py` | Regex-based extractors | `extract_ielts_toefl()`, `extract_deadline_dates()`, `extract_credits()` |
| `app/validate/validator.py` | Field validation + warnings | `validate_fields(fields)` |
| `app/export/xlsx_exporter.py` | Excel export (2 sheets) | `XlsxExporter.add_program()`, `.add_evidence()`, `.save()` |
| `app/util/helpers.py` | Paths, logging, run_log append | `evidence_dir()`, `raw_dir()`, `append_run_log()` |

### Output Structure

```
out/
  results.xlsx          # Programs sheet + Evidence sheet
  evidence/<pid>/       # Screenshot PNGs per program
  raw/<pid>/page.html   # Raw HTML per program
  run_log.jsonl         # One JSON line per program processed
```

### Error Handling Contract

**No module may raise exceptions that crash the pipeline.** Every `process_program()` call must return a `ProgramRecord` with `status=failed` + `warnings` on error. The runner uses `asyncio.gather(*tasks, return_exceptions=True)`.

### Evidence Strategy

- MVP: All fields share the same `full_page` screenshot; each field's `*_evidence_ids` points to the same `EvidenceItem`
- v1 target: Per-field cropped screenshots using Playwright element locators

### LLM Extraction

- Uses OpenAI-compatible API (configurable via `--llm-model` and `--llm-base-url`)
- Requires `OPENAI_API_KEY` env var
- Always requests `response_format={"type": "json_object"}` with `temperature=0`
- Truncates page text to 15k chars to control costs
- Rule-based extractors (`rule_extractors.py`) augment LLM results for IELTS/TOEFL scores and deadline dates

## Parallel Development

This repo is designed for 5 concurrent agents. Each agent works within their designated module directory. The `contracts/` directory is the shared interface — never modify it without coordinating with Agent-Lead. See `agents/` directory for individual agent task prompts.
