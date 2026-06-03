import logging
from typing import AsyncGenerator, Dict, List, Optional

import anthropic

from app.config import get_settings


logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the LLM API call fails."""


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._async_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model
        logger.info("LLMService initialised with model %s", self._model)

    def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> str:
        try:
            kwargs: Dict = {
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = self._client.messages.create(**kwargs)
            content = response.content[0].text
            logger.debug("LLM complete: input_tokens=%d output_tokens=%d", response.usage.input_tokens, response.usage.output_tokens)
            return content
        except anthropic.APIError as exc:
            logger.error("Anthropic API error in complete: %s", exc)
            raise LLMError(f"LLM API error: {exc}") from exc

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        try:
            kwargs: Dict = {
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with self._async_client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

            logger.debug("LLM stream completed")
        except anthropic.APIError as exc:
            logger.error("Anthropic API error in stream: %s", exc)
            raise LLMError(f"LLM API stream error: {exc}") from exc


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
