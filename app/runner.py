"""CLI entrypoint and orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from contracts.models import CrawlStatus, ProgramInput, RunLogEntry
from app.export.xlsx_exporter import XlsxExporter
from app.plugins.generic import process_program
from app.util.helpers import append_run_log, out_dir, setup_logging


async def run(
    inputs: list[ProgramInput],
    out_base: str = "out",
    concurrency: int = 3,
    mode: str = "browser_only",
    llm_api_key: str | None = None,
    llm_model: str = "gpt-4o-mini",
    llm_base_url: str | None = None,
) -> None:
    """Process a list of ProgramInputs and write all outputs."""
    logger = setup_logging()
    base = out_dir(out_base)
    exporter = XlsxExporter()

    sem = asyncio.Semaphore(concurrency)

    async def _process_one(inp: ProgramInput) -> None:
        async with sem:
            started = datetime.utcnow()
            logger.info("Processing: %s (%s)", inp.program_url, inp.program_id)
            record, evidence_items = await process_program(
                inp, str(base), mode=mode,
                llm_api_key=llm_api_key, llm_model=llm_model, llm_base_url=llm_base_url,
            )
            finished = datetime.utcnow()

            exporter.add_program(record)
            exporter.add_evidence(evidence_items)

            append_run_log(base, RunLogEntry(
                program_id=record.program_id,
                program_url=record.program_url,
                status=record.status,
                started_at=started,
                finished_at=finished,
                duration_s=(finished - started).total_seconds(),
                warnings=record.warnings,
                error=record.warnings[0] if record.status == CrawlStatus.FAILED and record.warnings else None,
            ))
            logger.info("Done: %s -> %s", inp.program_url, record.status.value)

    tasks = [asyncio.create_task(_process_one(inp)) for inp in inputs]
    await asyncio.gather(*tasks, return_exceptions=True)

    xlsx_path = base / "results.xlsx"
    exporter.save(xlsx_path)
    logger.info("Results saved to %s", xlsx_path)


def load_inputs(path: str) -> list[ProgramInput]:
    """Load ProgramInputs from CSV or JSONL."""
    p = Path(path)
    inputs = []

    if p.suffix == ".csv":
        with open(p, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                inputs.append(ProgramInput(**{k: v or None for k, v in row.items()}))
    elif p.suffix in (".jsonl", ".json"):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    inputs.append(ProgramInput(**json.loads(line)))
    else:
        raise ValueError(f"Unsupported input format: {p.suffix} (use .csv or .jsonl)")

    return inputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Program Crawler — fetch, extract, export")
    parser.add_argument("--input", "-i", required=True, help="Path to input CSV or JSONL")
    parser.add_argument("--out", "-o", default="out", help="Output directory (default: out)")
    parser.add_argument("--concurrency", "-c", type=int, default=3, help="Max concurrent fetches")
    parser.add_argument("--mode", "-m", default="browser_only",
                        choices=["browser_only", "http_first"],
                        help="Fetch mode strategy")
    parser.add_argument("--llm-model", default="gpt-4o-mini", help="LLM model name")
    parser.add_argument("--llm-base-url", default=None, help="LLM API base URL (optional)")

    args = parser.parse_args()
    api_key = os.environ.get("OPENAI_API_KEY")

    inputs = load_inputs(args.input)
    if not inputs:
        print("No inputs found. Exiting.")
        sys.exit(1)

    print(f"Loaded {len(inputs)} program(s). Starting crawl...")
    asyncio.run(run(
        inputs,
        out_base=args.out,
        concurrency=args.concurrency,
        mode=args.mode,
        llm_api_key=api_key,
        llm_model=args.llm_model,
        llm_base_url=args.llm_base_url,
    ))


if __name__ == "__main__":
    main()
