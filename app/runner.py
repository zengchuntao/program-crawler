"""CLI entrypoint — supports research agent mode and legacy batch mode."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from app.export.xlsx_exporter import ResearchExporter, XlsxExporter
from app.util.helpers import append_run_log, out_dir, setup_logging
from contracts.models import (
    CrawlStatus,
    ProgramInput,
    ResearchQuery,
    RunLogEntry,
)

# -------------------------------------------------------------------
# Research Agent mode
# -------------------------------------------------------------------

async def run_research_mode(
    query: str,
    out_base: str = "out",
    max_steps: int = 20,
    api_key: str | None = None,
    model: str = "gemini-3-flash-preview",
) -> None:
    """Run the AI research agent on a natural language query."""
    from app.agent.research_agent import run_research
    from app.llm.gemini_client import GeminiClient
    from app.log import LoggedLLM, RunTracker
    from app.tools.registry import create_default_registry

    base = out_dir(out_base)
    logger = setup_logging(log_dir=base / "logs")
    run_dir = getattr(logger, "run_dir", None)

    # Init tracker
    tracker = RunTracker()
    tracker.query = query
    tracker.model = model
    tracker.max_steps = max_steps

    # Init LLM
    if not api_key:
        print("Error: GEMINI_API_KEY not set.")
        sys.exit(1)

    raw_llm = GeminiClient(api_key=api_key, model=model)
    llm = LoggedLLM(raw_llm, tracker)
    tools = create_default_registry()

    rq = ResearchQuery(raw_query=query, max_steps=max_steps)
    logger.info(
        "Research: %s (model=%s, max_steps=%d)",
        query, model, max_steps,
    )

    result = await run_research(
        rq, llm=llm, tools=tools, out_base=str(base),
        tracker=tracker,
    )

    # Finalize tracker
    if run_dir:
        tracker.finalize(run_dir)
        logger.info("Run logs saved to %s", run_dir)

    # Export
    exporter = ResearchExporter()
    exporter.load_result(result)
    xlsx_path = base / "results.xlsx"
    exporter.save(xlsx_path)
    logger.info("Results saved to %s", xlsx_path)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Research complete: {result.status.value}")
    print(
        f"Steps: {result.total_steps} | "
        f"Pages: {result.pages_visited} | "
        f"Duration: {result.duration_s}s"
    )
    print(f"Findings: {len(result.findings)}")
    for f in result.findings:
        print(
            f"  [{f.entity}] {f.field_name}: "
            f"{f.value} (confidence: {f.confidence:.0%})"
        )
    if result.missing_fields:
        print(
            "Missing fields: "
            + ", ".join(result.missing_fields)
        )
    print(f"Output: {xlsx_path}")
    print(f"{'='*60}\n")


# -------------------------------------------------------------------
# Legacy batch mode (preserved)
# -------------------------------------------------------------------

async def run(
    inputs: list[ProgramInput],
    out_base: str = "out",
    concurrency: int = 3,
    mode: str = "browser_only",
    llm_api_key: str | None = None,
    llm_model: str = "gpt-4o-mini",
    llm_base_url: str | None = None,
) -> None:
    """Process ProgramInputs in batch (legacy mode)."""
    from app.plugins.generic import process_program

    logger = setup_logging()
    base = out_dir(out_base)
    exporter = XlsxExporter()
    sem = asyncio.Semaphore(concurrency)

    async def _one(inp: ProgramInput) -> None:
        async with sem:
            started = datetime.utcnow()
            logger.info(
                "Processing: %s (%s)",
                inp.program_url, inp.program_id,
            )
            record, evidence_items = await process_program(
                inp,
                str(base),
                mode=mode,
                llm_api_key=llm_api_key,
                llm_model=llm_model,
                llm_base_url=llm_base_url,
            )
            finished = datetime.utcnow()
            exporter.add_program(record)
            exporter.add_evidence(evidence_items)
            has_err = (
                record.status == CrawlStatus.FAILED
                and record.warnings
            )
            append_run_log(
                base,
                RunLogEntry(
                    program_id=record.program_id,
                    program_url=record.program_url,
                    status=record.status,
                    started_at=started,
                    finished_at=finished,
                    duration_s=(
                        finished - started
                    ).total_seconds(),
                    warnings=record.warnings,
                    error=(
                        record.warnings[0] if has_err else None
                    ),
                ),
            )
            logger.info(
                "Done: %s -> %s",
                inp.program_url, record.status.value,
            )

    tasks = [asyncio.create_task(_one(inp)) for inp in inputs]
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
                inputs.append(
                    ProgramInput(
                        **{k: v or None for k, v in row.items()}
                    )
                )
    elif p.suffix in (".jsonl", ".json"):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    inputs.append(
                        ProgramInput(**json.loads(line))
                    )
    else:
        raise ValueError(
            f"Unsupported format: {p.suffix} (use .csv or .jsonl)"
        )
    return inputs


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Research Agent — AI-driven academic program research"
        ),
    )
    parser.add_argument(
        "query", nargs="?", default=None,
        help="Natural language research query (agent mode)",
    )
    parser.add_argument(
        "--input", "-i", default=None,
        help="CSV or JSONL input (legacy batch mode)",
    )
    parser.add_argument(
        "--out", "-o", default="out",
        help="Output directory (default: out)",
    )
    parser.add_argument(
        "--concurrency", "-c", type=int, default=3,
        help="Max concurrent fetches (batch mode)",
    )
    parser.add_argument(
        "--mode", "-m", default="browser_only",
        choices=["browser_only", "http_first"],
        help="Fetch mode (batch mode)",
    )
    parser.add_argument(
        "--max-steps", type=int, default=20,
        help="Max agent steps (default: 20)",
    )
    parser.add_argument(
        "--llm-model",
        default="gemini-3-flash-preview",
        help="LLM model (default: gemini-3-flash-preview)",
    )
    parser.add_argument(
        "--llm-base-url", default=None,
        help="LLM API base URL (legacy OpenAI mode only)",
    )

    args = parser.parse_args()

    if args.query:
        # Agent mode: use Gemini
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print(
                "Error: set GEMINI_API_KEY env var.\n"
                "  export GEMINI_API_KEY='your-key'"
            )
            sys.exit(1)

        print(f'Research Agent: "{args.query}"')
        asyncio.run(run_research_mode(
            query=args.query,
            out_base=args.out,
            max_steps=args.max_steps,
            api_key=api_key,
            model=args.llm_model,
        ))

    elif args.input:
        # Legacy batch mode
        api_key = os.environ.get("OPENAI_API_KEY")
        inputs = load_inputs(args.input)
        if not inputs:
            print("No inputs found. Exiting.")
            sys.exit(1)
        print(f"Loaded {len(inputs)} program(s). Starting...")
        asyncio.run(run(
            inputs,
            out_base=args.out,
            concurrency=args.concurrency,
            mode=args.mode,
            llm_api_key=api_key,
            llm_model=args.llm_model,
            llm_base_url=args.llm_base_url,
        ))

    else:
        parser.print_help()
        print("\nExamples:")
        print(
            '  export GEMINI_API_KEY="AIza..."\n'
            '  python -m app.runner "帮我找MIT CS硕士的GPA要求"\n'
            '  python -m app.runner "Stanford CS deadlines" '
            "--max-steps 15\n"
            "  python -m app.runner -i input.csv -o out/"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
