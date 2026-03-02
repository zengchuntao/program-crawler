# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Research Agent** — an AI-driven CLI tool that takes natural language queries about academic programs, autonomously searches the web, visits pages, extracts structured data (admission requirements, deadlines, tuition, etc.), captures screenshot evidence, and exports to Excel with full audit trail.

Also supports legacy batch crawl mode via `--input` flag.

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

# Run the research agent (NEW — natural language query)
python -m app.runner "帮我找MIT CS硕士的GPA要求和语言要求"
python -m app.runner "Stanford CS Master deadlines" --max-steps 15 --out out/

# Run legacy batch crawl mode
python -m app.runner --input tests/fixtures/inputs.csv --out out/

# Run with http-first mode (cheaper, falls back to browser)
python -m app.runner -i input.csv -o out/ --mode http_first --concurrency 5
```

## Architecture

### Two Modes

1. **Research Agent mode** (new, default): Natural language query → LLM-driven autonomous research loop → findings + evidence
2. **Legacy batch mode**: CSV/JSONL input → mechanical fetch → extract → export

### Contracts-First Design

All modules depend on `contracts/models.py` (Pydantic) and `contracts/columns.yaml` — these are **frozen interfaces**. Do not rename or remove fields; only append new optional fields.

### Agent Data Flow (new)
```
ResearchQuery → [Planner LLM] → ResearchGoal
    → Agent Loop (max 20 steps):
        [Action Picker LLM] → AgentAction (search/visit/done)
        → Google search or page visit
        → [Evaluator LLM] → Findings + useful links
        → Screenshot evidence capture
    → ResearchResult → results.xlsx (4 sheets)
```

### Legacy Data Flow (preserved)
```
ProgramInput → FetchPlan → Document → ExtractedFields → ProgramRecord + EvidenceItem[] → results.xlsx (2 sheets)
```

### Key Models

**Legacy (frozen):**
- `ProgramInput`, `FetchPlan`, `Document`, `ExtractedFields`, `EvidenceItem`, `EvidenceRefs`, `ProgramRecord`, `RunLogEntry`

**New Agent models:**
- `ResearchQuery`: Natural language input with max_steps
- `ResearchGoal`: LLM-parsed target entities, requested fields, search hints
- `AgentAction`: Single action decision (search/visit/done/give_up) with reasoning
- `Finding`: One confirmed data point with entity, field, value, confidence, source URL
- `PageVisit`: Record of visiting a page (URL, relevance, extracted links)
- `AgentMemory`: Working memory across the agent loop
- `AgentLogStep`: One step in the execution log
- `ResearchResult`: Final output with findings, evidence, agent log, status

### Module Layout

| Module | Purpose | Key function/class |
|---|---|---|
| `app/runner.py` | CLI + orchestrator (both modes) | `main()`, `run_research_mode()`, `run()` |
| **Agent Brain** | | |
| `app/agent/research_agent.py` | Core agent loop | `run_research()` |
| `app/agent/planner.py` | LLM: parse query → goals | `plan_research()` |
| `app/agent/evaluator.py` | LLM: evaluate page content | `evaluate_page()` |
| `app/agent/action_picker.py` | LLM: decide next action | `pick_action()` |
| `app/agent/memory.py` | Memory management | `create_memory()`, `add_findings()`, `prune_memory()` |
| **Fetchers** | | |
| `app/fetcher/http_fetcher.py` | Plain HTTP fetch via httpx | `fetch_http()` |
| `app/fetcher/browser_fetcher.py` | Playwright headless browser | `fetch_browser()`, `fetch_browser_with_handle()` |
| `app/fetcher/google_search.py` | Google search (direct/SerpAPI) | `google_search()` |
| `app/fetcher/fetch_router.py` | HTTP vs Playwright auto-routing | `smart_fetch()` |
| **Evidence & Export** | | |
| `app/evidence/capture.py` | Screenshot capture | `capture_full_page()`, `capture_for_finding()`, `screenshot_url()` |
| `app/export/xlsx_exporter.py` | Excel export | `ResearchExporter` (4 sheets), `XlsxExporter` (legacy 2 sheets) |
| **Utilities** | | |
| `app/util/text_utils.py` | HTML→text, truncation, SPA detection | `html_to_text()`, `looks_like_spa()` |
| `app/util/helpers.py` | Paths, logging, run_log | `evidence_dir()`, `raw_dir()`, `append_run_log()` |
| `app/extractor/llm_extractor.py` | Legacy LLM extraction | `extract_with_llm()` |
| `app/extractor/rule_extractors.py` | Regex extractors | `extract_ielts_toefl()`, `extract_deadline_dates()` |
| `app/validate/validator.py` | Field validation | `validate_fields()` |
| `app/plugins/generic.py` | Legacy batch pipeline | `process_program()` |

### Output Structure (Agent Mode)

```
out/
  results.xlsx          # 4 sheets: Findings, Summary, Evidence, Agent Log
  evidence/agent/       # Screenshot PNGs per finding
  run_log.jsonl         # Execution log
```

### 3 LLM Calls in the Agent Loop

| LLM Call | When | Input | Output |
|---------|------|-------|--------|
| **Planner** | Once at start | User's raw query | ResearchGoal (entities, fields, search hints) |
| **Action Picker** | Each loop step | AgentMemory summary | AgentAction (search/visit/done/give_up) |
| **Evaluator** | After each page visit | Page text + needed fields | Findings + useful links |

### Error Handling Contract

**No module may raise exceptions that crash the pipeline.** All LLM calls and page visits are wrapped in try/except. The agent loop always produces a ResearchResult, even on failure.

### Smart Fetch Router

```
URL → Try HTTP first (fast, ~200ms)
  → Content enough (>200 chars)? → Use HTTP result
  → Too thin / SPA detected? → Fall back to Playwright
```

SPA detection: checks for `id="__next"`, `id="root"`, `<noscript>`, `data-reactroot`, etc.

### Google Search

Uses direct HTTP scraping (free) with Playwright fallback. Set `SERPAPI_KEY` env var to use SerpAPI instead.

### Excel Output (4 Sheets)

1. **Findings**: One row per discovered fact (finding_id, entity, field, value, confidence, source, screenshot)
2. **Summary**: One row per entity with all fields aggregated + missing fields + status
3. **Evidence**: Evidence index linking screenshots to findings
4. **Agent Log**: Debug trail — every step the agent took with reasoning

## Parallel Development

This repo is designed for 5 concurrent agents. Each agent works within their designated module directory. The `contracts/` directory is the shared interface — never modify it without coordinating with Agent-Lead. See `agents/` directory for individual agent task prompts.
