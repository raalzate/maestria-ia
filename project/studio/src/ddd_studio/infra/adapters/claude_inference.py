"""ClaudeInferenceAdapter implementing InferencePort.

Uses the Anthropic Messages API with tool-forcing for structured output.
"""

from __future__ import annotations

import logging
import time
import types
from typing import TypeVar, get_args, get_origin

import anthropic
from domain.exceptions import ConfigurationError, ServiceUnavailableError
from pydantic import BaseModel, create_model
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)

_STRUCTURED_TOOL_NAME = "extract_structured_output"
_MAX_TOKENS = 8192


def _is_retryable_error(exc: BaseException) -> bool:
    """Return True for transient Anthropic errors worth retrying."""
    if isinstance(exc, anthropic.RateLimitError):
        return True
    if isinstance(exc, anthropic.APIConnectionError):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        status = getattr(exc, "status_code", None)
        if status in {429, 500, 502, 503, 529}:
            return True
    return False


def _log_cache_usage(response: object, context: str) -> None:
    """Log prompt-cache hit/create tokens if the response reports them."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    created = getattr(usage, "cache_creation_input_tokens", 0) or 0
    if read or created:
        logger.info("[cache:%s] read=%d created=%d", context, read, created)


_llm_retry = retry(
    retry=retry_if_exception(_is_retryable_error),
    wait=wait_exponential_jitter(initial=10, max=120, jitter=5),
    stop=stop_after_attempt(5),
    before_sleep=lambda rs: logger.warning(
        "Rate limited by Anthropic API. Retrying in %.1fs (attempt %d/5)…",
        rs.next_action.sleep,  # type: ignore[union-attr]
        rs.attempt_number,
    ),
    reraise=True,
)


class ClaudeInferenceAdapter:
    """InferencePort implementation using Anthropic Claude."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        import os

        self._model_name = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._client_instance: anthropic.Anthropic | None = None

    @property
    def _client(self) -> anthropic.Anthropic:
        """Lazy-loaded Anthropic client."""
        if self._client_instance is None:
            if not self._api_key:
                raise ConfigurationError(
                    "Anthropic API Key is missing. Please set ANTHROPIC_API_KEY environment variable."
                )
            self._client_instance = anthropic.Anthropic(api_key=self._api_key)
        return self._client_instance

    @_llm_retry
    def invoke(self, prompt: str, output_schema: type[T]) -> T:
        """Send prompt and return structured output via forced tool use."""
        time.sleep(5)

        start_time = time.time()
        schema_name = getattr(output_schema, "__name__", str(output_schema))

        try:
            # Wrap list[T] so the top-level schema is a JSON object.
            if isinstance(output_schema, types.GenericAlias) and get_origin(output_schema) is list:
                item_type = get_args(output_schema)[0]
                wrapper = create_model("_ListWrapper", items=(list[item_type], ...))
                parsed = self._invoke_structured(prompt, wrapper)
                duration = time.time() - start_time
                print(f"      [LLM] Extracción finalizada ({schema_name}) en {duration:.1f}s")
                return parsed.items  # type: ignore[return-value]

            parsed = self._invoke_structured(prompt, output_schema)
            duration = time.time() - start_time
            print(f"      [LLM] Extracción finalizada ({schema_name}) en {duration:.1f}s")
            return parsed

        except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
            raise ServiceUnavailableError(str(e)) from e

    @_llm_retry
    def invoke_text(self, prompt: str) -> str:
        """Send prompt and return raw text response."""
        time.sleep(1)

        start_time = time.time()
        try:
            response = self._client.messages.create(
                model=self._model_name,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            duration = time.time() - start_time
            print(f"      [LLM] Inferencia de texto finalizada en {duration:.1f}s")
            return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
            raise ServiceUnavailableError(str(e)) from e

    @_llm_retry
    def invoke_vision(self, prompt: str, images: list[bytes]) -> str:
        """Send prompt plus JPEG images and return the text response."""
        import base64

        time.sleep(1)

        content: list[dict] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(img).decode("ascii"),
                },
            }
            for img in images
        ]
        content.append({"type": "text", "text": prompt})

        start_time = time.time()
        try:
            response = self._client.messages.create(
                model=self._model_name,
                max_tokens=_MAX_TOKENS,
                messages=[{"role": "user", "content": content}],
            )
            duration = time.time() - start_time
            print(f"      [LLM] Análisis de visión finalizado ({len(images)} imágenes) en {duration:.1f}s")
            return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
            raise ServiceUnavailableError(str(e)) from e

    def _invoke_structured(self, prompt: str, schema: type[T]) -> T:
        """Call Messages API with a forced tool whose input_schema is `schema`."""
        if not issubclass(schema, BaseModel):  # type: ignore[arg-type]
            raise TypeError(f"output_schema must be a pydantic BaseModel, got {schema}")

        input_schema = schema.model_json_schema()  # type: ignore[attr-defined]

        response = self._client.messages.create(
            model=self._model_name,
            max_tokens=_MAX_TOKENS,
            tools=[
                {
                    "name": _STRUCTURED_TOOL_NAME,
                    "description": f"Return a structured {schema.__name__} object.",
                    "input_schema": input_schema,
                    # Cache the tool schema: repeated extractions reuse it at 10% cost.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tool_choice={"type": "tool", "name": _STRUCTURED_TOOL_NAME},
            messages=[{"role": "user", "content": prompt}],
        )
        _log_cache_usage(response, context=f"structured:{schema.__name__}")

        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == _STRUCTURED_TOOL_NAME:
                payload = block.input
                if isinstance(payload, dict):
                    expected_keys = set(schema.model_fields.keys())  # type: ignore[attr-defined]
                    top_keys = set(payload.keys())
                    # Unwrap when Claude nests the real object under a single placeholder key
                    # (e.g. "$PARAMETER_NAME", "input", "parameter") that doesn't match the schema.
                    if top_keys.isdisjoint(expected_keys) and len(payload) == 1:
                        inner = next(iter(payload.values()))
                        if isinstance(inner, dict):
                            logger.warning(
                                "Claude wrapped tool output under '%s' — unwrapping.",
                                next(iter(payload.keys())),
                            )
                            payload = inner
                return schema.model_validate(payload)  # type: ignore[attr-defined,return-value]

        raise ServiceUnavailableError(
            f"Claude did not return a tool_use block for {schema.__name__}. stop_reason={response.stop_reason}"
        )
