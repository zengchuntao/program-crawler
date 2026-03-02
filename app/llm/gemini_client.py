"""Gemini LLM client — Google Generative AI implementation."""

from __future__ import annotations

import asyncio
import json
import logging

from app.llm.base import BaseLLM

logger = logging.getLogger("crawler.llm.gemini")


class GeminiClient(BaseLLM):
    """
    Google Gemini LLM client using the google-genai SDK.

    Supports structured JSON output via response_mime_type.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3-flash-preview",
    ):
        self._api_key = api_key
        self._model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Send a chat message and get a text response."""
        from google.genai import types

        client = self._get_client()

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                ),
            )
            result = response.text or ""
            logger.debug("Gemini chat response (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("Gemini chat failed: %s", e)
            raise

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict:
        """Send a chat message and get a parsed JSON response."""
        from google.genai import types

        client = self._get_client()

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
            raw = response.text or "{}"
            logger.debug("Gemini JSON response (%d chars)", len(raw))
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Gemini returned invalid JSON: %s", e)
            return {}
        except Exception as e:
            logger.error("Gemini chat_json failed: %s", e)
            raise
