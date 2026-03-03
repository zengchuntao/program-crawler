"""LoggedLLM — transparent wrapper around BaseLLM that logs every call."""

from __future__ import annotations

import logging
import time

from app.llm.base import BaseLLM
from app.log.run_tracker import RunTracker

logger = logging.getLogger("crawler.llm.logged")

# Mapping: system-prompt substring → caller label
_CALLER_PATTERNS: list[tuple[str, str]] = [
    ("research planning", "planner"),
    ("action decision", "action_picker"),
    ("page content evaluator", "evaluator"),
]


def _detect_caller(system_prompt: str) -> str:
    """Detect the caller from the first 100 chars of the system prompt."""
    prefix = system_prompt[:100].lower()
    for pattern, label in _CALLER_PATTERNS:
        if pattern in prefix:
            return label
    return "unknown"


class LoggedLLM(BaseLLM):
    """Wrapper that delegates to an inner BaseLLM and records every call."""

    def __init__(self, inner: BaseLLM, tracker: RunTracker) -> None:
        self._inner = inner
        self._tracker = tracker

    @property
    def model_name(self) -> str:
        return self._inner.model_name

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        caller = _detect_caller(system_prompt)
        start = time.time()

        try:
            result = await self._inner.chat(system_prompt, user_message)
        except Exception:
            duration = time.time() - start
            logger.warning(
                "LLM chat failed [%s] after %.2fs", caller, duration,
            )
            raise

        duration = time.time() - start
        self._tracker.record_llm_call(
            caller=caller,
            model=self.model_name,
            duration_s=duration,
            prompt_preview=user_message[:200],
            response_preview=result[:200],
        )
        logger.debug(
            "LLM chat [%s] %.2fs (%d chars)",
            caller, duration, len(result),
        )
        return result

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict:
        caller = _detect_caller(system_prompt)
        start = time.time()

        try:
            result = await self._inner.chat_json(system_prompt, user_message)
        except Exception:
            duration = time.time() - start
            logger.warning(
                "LLM chat_json failed [%s] after %.2fs", caller, duration,
            )
            raise

        duration = time.time() - start
        response_preview = str(result)[:200]
        self._tracker.record_llm_call(
            caller=caller,
            model=self.model_name,
            duration_s=duration,
            prompt_preview=user_message[:200],
            response_preview=response_preview,
        )
        logger.debug(
            "LLM chat_json [%s] %.2fs (%d keys)",
            caller, duration, len(result),
        )
        return result
