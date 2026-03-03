"""Tests for LoggedLLM and caller detection."""

from __future__ import annotations

import pytest

from app.llm.base import BaseLLM
from app.log.llm_logger import LoggedLLM, _detect_caller
from app.log.run_tracker import RunTracker


# ------------------------------------------------------------------
# Caller detection
# ------------------------------------------------------------------

class TestDetectCaller:
    def test_planner(self):
        assert _detect_caller("You are a research planning assistant.") == "planner"

    def test_action_picker(self):
        assert _detect_caller("You are an action decision maker.") == "action_picker"

    def test_evaluator(self):
        assert _detect_caller("You are a page content evaluator for...") == "evaluator"

    def test_unknown(self):
        assert _detect_caller("Hello world") == "unknown"

    def test_case_insensitive(self):
        assert _detect_caller("RESEARCH PLANNING system") == "planner"

    def test_only_first_100_chars(self):
        # Pattern beyond 100 chars should not match
        prompt = "x" * 100 + "research planning"
        assert _detect_caller(prompt) == "unknown"


# ------------------------------------------------------------------
# Fake LLM for testing
# ------------------------------------------------------------------

class FakeLLM(BaseLLM):
    """Deterministic LLM for testing."""

    def __init__(self, chat_response: str = "ok", json_response: dict | None = None):
        self._chat_response = chat_response
        self._json_response = json_response or {"status": "ok"}

    @property
    def model_name(self) -> str:
        return "fake-model"

    async def chat(self, system_prompt: str, user_message: str) -> str:
        return self._chat_response

    async def chat_json(self, system_prompt: str, user_message: str) -> dict:
        return self._json_response


class FailingLLM(BaseLLM):
    """LLM that always raises."""

    @property
    def model_name(self) -> str:
        return "failing-model"

    async def chat(self, system_prompt: str, user_message: str) -> str:
        raise RuntimeError("LLM down")

    async def chat_json(self, system_prompt: str, user_message: str) -> dict:
        raise RuntimeError("LLM down")


# ------------------------------------------------------------------
# LoggedLLM
# ------------------------------------------------------------------

class TestLoggedLLM:
    @pytest.mark.asyncio
    async def test_chat_delegates_and_records(self):
        tracker = RunTracker()
        inner = FakeLLM(chat_response="hello")
        logged = LoggedLLM(inner, tracker)

        result = await logged.chat("research planning sys", "user msg")

        assert result == "hello"
        assert len(tracker.llm_calls) == 1
        assert tracker.llm_calls[0].caller == "planner"
        assert tracker.llm_calls[0].model == "fake-model"
        assert tracker.llm_calls[0].duration_s >= 0

    @pytest.mark.asyncio
    async def test_chat_json_delegates_and_records(self):
        tracker = RunTracker()
        inner = FakeLLM(json_response={"key": "val"})
        logged = LoggedLLM(inner, tracker)

        result = await logged.chat_json("action decision sys", "user msg")

        assert result == {"key": "val"}
        assert len(tracker.llm_calls) == 1
        assert tracker.llm_calls[0].caller == "action_picker"

    @pytest.mark.asyncio
    async def test_model_name_delegated(self):
        tracker = RunTracker()
        inner = FakeLLM()
        logged = LoggedLLM(inner, tracker)
        assert logged.model_name == "fake-model"

    @pytest.mark.asyncio
    async def test_exception_propagated(self):
        tracker = RunTracker()
        logged = LoggedLLM(FailingLLM(), tracker)

        with pytest.raises(RuntimeError, match="LLM down"):
            await logged.chat("sys", "msg")

        # Should NOT record a successful call
        assert len(tracker.llm_calls) == 0

    @pytest.mark.asyncio
    async def test_chat_json_exception_propagated(self):
        tracker = RunTracker()
        logged = LoggedLLM(FailingLLM(), tracker)

        with pytest.raises(RuntimeError, match="LLM down"):
            await logged.chat_json("sys", "msg")

        assert len(tracker.llm_calls) == 0

    @pytest.mark.asyncio
    async def test_multiple_calls_accumulated(self):
        tracker = RunTracker()
        inner = FakeLLM()
        logged = LoggedLLM(inner, tracker)

        await logged.chat("research planning", "q1")
        await logged.chat("action decision", "q2")
        await logged.chat_json("page content evaluator", "q3")

        assert len(tracker.llm_calls) == 3
        callers = [c.caller for c in tracker.llm_calls]
        assert callers == ["planner", "action_picker", "evaluator"]
