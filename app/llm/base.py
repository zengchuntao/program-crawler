"""BaseLLM — abstract interface for all LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Abstract LLM interface. All providers (Gemini, OpenAI, etc.) implement this.

    Usage:
        llm = GeminiClient(api_key="...", model="gemini-3-flash-preview")
        result = await llm.chat_json(system_prompt, user_message)
    """

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Send a chat message and get a text response."""
        ...

    @abstractmethod
    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict:
        """Send a chat message and get a parsed JSON response."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""
        ...
