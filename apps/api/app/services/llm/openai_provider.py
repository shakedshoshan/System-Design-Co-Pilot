from __future__ import annotations

import logging

from openai import APIError, AsyncOpenAI, RateLimitError

logger = logging.getLogger("app.llm.openai")


class OpenAILLMProvider:
    """OpenAI Chat Completions via the async client (see /openai/openai-python Context7 docs)."""

    def __init__(self, client: AsyncOpenAI, default_model: str) -> None:
        self._client = client
        self._default_model = default_model

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        use_model = model or self._default_model
        try:
            completion = await self._client.chat.completions.create(
                model=use_model,
                messages=messages,
            )
        except RateLimitError:
            logger.warning("openai_rate_limited", extra={"model": use_model})
            raise
        except APIError as e:
            logger.warning(
                "openai_api_error",
                extra={"model": use_model, "type": type(e).__name__},
            )
            raise
        choice = completion.choices[0]
        msg = choice.message
        text = msg.content
        if text is None:
            return ""
        return text
