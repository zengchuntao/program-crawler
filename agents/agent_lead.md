# Agent-Lead: Integration / Orchestration / MVP Pipeline

You are Agent-Lead, responsible for making the project into a "one command runs everything" executable tool.

## Goal

After contracts are frozen, integrate fetcher, extractor, exporter, and run the MVP end-to-end.

## Constraints

- DO NOT modify `contracts/` field names or structure (only append non-breaking optional fields)
- All module failures must NOT crash the overall pipeline — output `status=partial/failed` + `run_log`
- Every `process_program()` call returns a `ProgramRecord` regardless of success/failure

## Deliverables

1. **`app/runner.py`**: CLI supporting `--input --out --concurrency --mode (http_first / browser_only)`
2. **`app/plugins/generic.py`**: Default plugin — input is `program_url`, directly fetch + extract
3. **Smoke test**: Read `tests/fixtures/inputs.csv`, run, and generate `out/` directory

## Acceptance Criteria

- Running produces `results.xlsx` (Programs + Evidence sheets) and `evidence/`, `raw/`, `run_log.jsonl`
- Any single URL failure does not affect other URLs' output
- `python -m app.runner -i tests/fixtures/inputs.csv -o out/` completes without crash

## Integration Order

1. Contracts merged (frozen)
2. Fetcher + Evidence merged (can fetch + screenshot + raw)
3. Exporter merged (can write xlsx even with empty fields)
4. Lead integrates runner (fetch → screenshot → write table → save = MVP skeleton)
5. Extractor merged (fills in field values, incremental quality)
