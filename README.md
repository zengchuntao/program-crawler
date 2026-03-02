# Program Crawler

CLI tool that crawls academic program pages, extracts structured admission data, captures screenshot evidence, and exports to auditable Excel.

## Quick Start

```bash
# Requirements: Python 3.11+
pip install -e ".[dev]"

# Install Playwright browsers (first time only)
playwright install chromium

# Set LLM API key
export OPENAI_API_KEY="sk-..."

# Run
python -m app.runner --input programs.csv --out out/
```

## Input Format

CSV with at least `program_url` column:

```csv
program_url,school_name,program_name,degree_level
https://example.edu/ms-cs,Example University,Computer Science,Master
```

Or JSONL:
```json
{"program_url": "https://example.edu/ms-cs", "school_name": "Example University"}
```

## Output

```
out/
├── results.xlsx          # Programs + Evidence sheets
├── evidence/
│   └── <program_id>/
│       └── full_page.png
├── raw/
│   └── <program_id>/
│       └── page.html
└── run_log.jsonl
```

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `--input, -i` | required | Path to CSV or JSONL |
| `--out, -o` | `out` | Output directory |
| `--concurrency, -c` | `3` | Max parallel fetches |
| `--mode, -m` | `browser_only` | `browser_only` or `http_first` |
| `--llm-model` | `gpt-4o-mini` | LLM model for extraction |
| `--llm-base-url` | None | Custom LLM API endpoint |

## Extracted Fields

| Field | Description |
|---|---|
| `gpa_requirement` | Minimum GPA |
| `language_requirement` | IELTS/TOEFL/DET scores |
| `gre_gmat_requirement` | Standardized test scores |
| `prerequisites` | Required courses/background |
| `deadlines` | Application deadlines |
| `tuition_fees` | Tuition and fee information |
| `materials` | Required application materials |
| `curriculum_summary` | Program curriculum overview |
| `curriculum_links` | Links to curriculum pages |

## Development

```bash
# Run tests
pytest -v

# Lint
ruff check .

# Single test
pytest tests/test_contracts.py::TestProgramInput -v
```

## Architecture

See [CLAUDE.md](./CLAUDE.md) for detailed architecture documentation.
