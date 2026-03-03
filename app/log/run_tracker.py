"""RunTracker — collects LLM calls, agent steps, errors; writes JSON + summary."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LLMCallRecord:
    caller: str
    model: str
    duration_s: float
    prompt_preview: str = ""
    response_preview: str = ""
    timestamp: float = 0.0


@dataclass
class StepRecord:
    step: int
    action: str
    url_or_query: str
    duration_s: float
    findings_added: int = 0
    timestamp: float = 0.0


@dataclass
class ErrorRecord:
    step: int
    error_type: str
    message: str
    timestamp: float = 0.0


class RunTracker:
    """Collects runtime metrics and writes run_record.json + run_summary.txt."""

    def __init__(self) -> None:
        self.start_time: float = time.time()
        self.query: str = ""
        self.model: str = ""
        self.max_steps: int = 0

        self.llm_calls: list[LLMCallRecord] = []
        self.steps: list[StepRecord] = []
        self.errors: list[ErrorRecord] = []

    # --- recording methods ---

    def record_llm_call(
        self,
        caller: str,
        model: str,
        duration_s: float,
        prompt_preview: str = "",
        response_preview: str = "",
    ) -> None:
        self.llm_calls.append(LLMCallRecord(
            caller=caller,
            model=model,
            duration_s=round(duration_s, 3),
            prompt_preview=prompt_preview[:200],
            response_preview=response_preview[:200],
            timestamp=time.time(),
        ))

    def record_step(
        self,
        step: int,
        action: str,
        url_or_query: str,
        duration_s: float,
        findings_added: int = 0,
    ) -> None:
        self.steps.append(StepRecord(
            step=step,
            action=action,
            url_or_query=url_or_query,
            duration_s=round(duration_s, 3),
            findings_added=findings_added,
            timestamp=time.time(),
        ))

    def record_error(
        self,
        step: int,
        error: Exception,
    ) -> None:
        self.errors.append(ErrorRecord(
            step=step,
            error_type=type(error).__name__,
            message=str(error)[:500],
            timestamp=time.time(),
        ))

    # --- output ---

    def finalize(self, run_dir: str | Path) -> None:
        """Write run_record.json and run_summary.txt to *run_dir*."""
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        total_duration = time.time() - self.start_time
        total_llm_time = sum(c.duration_s for c in self.llm_calls)

        record = {
            "query": self.query,
            "model": self.model,
            "max_steps": self.max_steps,
            "total_duration_s": round(total_duration, 2),
            "total_llm_time_s": round(total_llm_time, 2),
            "llm_calls_count": len(self.llm_calls),
            "steps_count": len(self.steps),
            "errors_count": len(self.errors),
            "llm_calls": [_asdict(c) for c in self.llm_calls],
            "steps": [_asdict(s) for s in self.steps],
            "errors": [_asdict(e) for e in self.errors],
        }

        # JSON record
        json_path = run_dir / "run_record.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        # Human-readable summary
        summary_path = run_dir / "run_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(self._build_summary(total_duration, total_llm_time))

    def _build_summary(
        self, total_duration: float, total_llm_time: float,
    ) -> str:
        lines: list[str] = []
        lines.append("=" * 60)
        lines.append("RUN SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Query:    {self.query}")
        lines.append(f"Model:    {self.model}")
        lines.append(f"Duration: {total_duration:.1f}s (LLM: {total_llm_time:.1f}s)")
        lines.append(f"Steps:    {len(self.steps)}/{self.max_steps}")
        lines.append(f"LLM calls: {len(self.llm_calls)}")
        lines.append(f"Errors:   {len(self.errors)}")
        lines.append("")

        # LLM call breakdown by caller
        caller_stats: dict[str, list[float]] = {}
        for c in self.llm_calls:
            caller_stats.setdefault(c.caller, []).append(c.duration_s)
        if caller_stats:
            lines.append("--- LLM Calls by Caller ---")
            for caller, durations in sorted(caller_stats.items()):
                avg = sum(durations) / len(durations)
                lines.append(
                    f"  {caller}: {len(durations)} calls, "
                    f"avg {avg:.2f}s, total {sum(durations):.2f}s"
                )
            lines.append("")

        # Steps
        if self.steps:
            lines.append("--- Steps ---")
            for s in self.steps:
                findings_str = f" (+{s.findings_added} findings)" if s.findings_added else ""
                lines.append(
                    f"  [{s.step}] {s.action}: "
                    f"{s.url_or_query[:80]} ({s.duration_s:.1f}s){findings_str}"
                )
            lines.append("")

        # Errors
        if self.errors:
            lines.append("--- Errors ---")
            for e in self.errors:
                lines.append(f"  [Step {e.step}] {e.error_type}: {e.message[:120]}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines) + "\n"


def _asdict(obj: LLMCallRecord | StepRecord | ErrorRecord) -> dict:
    """Convert a dataclass instance to a plain dict."""
    return {k: v for k, v in obj.__dict__.items()}
