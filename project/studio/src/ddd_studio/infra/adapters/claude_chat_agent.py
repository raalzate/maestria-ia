"""ClaudeChatAgentAdapter implementing ChatAgentPort.

Uses the Anthropic Messages API with tool_use / tool_result loop.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic
from domain.models.tool_schemas import AgentResponse, ToolExecution
from services.model_accessor import ModelAccessor
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

MAX_ITERATIONS = 5
_MAX_TOKENS = 4096

logger = logging.getLogger(__name__)


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


def _langchain_tool_to_anthropic_schema(tool: Any) -> dict[str, Any]:
    """Convert a LangChain @tool-decorated function to an Anthropic tool schema."""
    args_schema = getattr(tool, "args_schema", None)
    if args_schema is not None and hasattr(args_schema, "model_json_schema"):
        input_schema = args_schema.model_json_schema()
    else:
        # Fallback for tools without a pydantic args_schema.
        input_schema = {"type": "object", "properties": {}, "required": []}
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": input_schema,
    }


def _log_cache_usage(response: Any, context: str) -> None:
    """Log prompt-cache hit/create tokens if the response reports them."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    created = getattr(usage, "cache_creation_input_tokens", 0) or 0
    if read or created:
        logger.info("[cache:%s] read=%d created=%d", context, read, created)


class ClaudeChatAgentAdapter:
    """ChatAgentPort implementation using Claude with tool calling."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._model_name = model
        self._api_key = api_key
        self._client_instance: anthropic.Anthropic | None = None

    @property
    def _client(self) -> anthropic.Anthropic:
        """Lazy-loaded Anthropic client."""
        if self._client_instance is None:
            from domain.exceptions import ConfigurationError

            if not self._api_key:
                raise ConfigurationError(
                    "Anthropic API Key is missing. Please configure it in the sidebar to use the Chat Agent."
                )
            self._client_instance = anthropic.Anthropic(api_key=self._api_key)
        return self._client_instance

    @staticmethod
    @_llm_retry
    def _create_with_retry(client: anthropic.Anthropic, **kwargs: Any) -> Any:
        """Call messages.create with retry on transient errors."""
        return client.messages.create(**kwargs)

    def run(
        self,
        user_message: str,
        history: list[dict[str, str]],
        system_prompt: str,
        model_accessor: ModelAccessor,
    ) -> AgentResponse:
        """Execute one agent turn with a tool_use / tool_result loop."""
        from services.agent_tools import create_tools

        tools = create_tools(model_accessor)
        tool_map = {t.name: t for t in tools}
        anthropic_tools = [_langchain_tool_to_anthropic_schema(t) for t in tools]
        # Cache the tool definitions: last tool carries the breakpoint; all prior
        # `tools` + `system` content gets cached for 5 min and reused on each loop iter.
        if anthropic_tools:
            anthropic_tools[-1] = {
                **anthropic_tools[-1],
                "cache_control": {"type": "ephemeral"},
            }
        cached_system = [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        messages: list[dict[str, Any]] = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        tool_executions: list[ToolExecution] = []
        iterations = 0
        response: Any = None
        final_text = ""

        while iterations < MAX_ITERATIONS:
            response = self._create_with_retry(
                self._client,
                model=self._model_name,
                max_tokens=_MAX_TOKENS,
                system=cached_system,
                tools=anthropic_tools,
                messages=messages,
            )
            _log_cache_usage(response, context=f"chat_agent:iter={iterations}")

            # Preserve the full assistant message verbatim (text + tool_use blocks)
            # so the next turn accepts the tool_result messages.
            assistant_blocks = [self._block_to_dict(b) for b in response.content]
            messages.append({"role": "assistant", "content": assistant_blocks})

            tool_use_blocks = [b for b in response.content if getattr(b, "type", None) == "tool_use"]

            if not tool_use_blocks:
                final_text = self._extract_text(response.content)
                break

            tool_results: list[dict[str, Any]] = []
            for tu in tool_use_blocks:
                tool_name = tu.name
                tool_args = tu.input if isinstance(tu.input, dict) else {}
                tool_id = tu.id

                tool_fn = tool_map.get(tool_name)
                if tool_fn:
                    try:
                        result_str = tool_fn.invoke(tool_args)
                        success = True
                        try:
                            parsed = json.loads(result_str)
                            success = parsed.get("success", True)
                        except (json.JSONDecodeError, AttributeError):
                            pass
                    except Exception as e:
                        result_str = json.dumps(
                            {
                                "success": False,
                                "message": str(e),
                                "affected_elements": [],
                            }
                        )
                        success = False
                else:
                    result_str = json.dumps(
                        {
                            "success": False,
                            "message": f"Unknown tool: {tool_name}",
                            "affected_elements": [],
                        }
                    )
                    success = False

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_str,
                    }
                )
                tool_executions.append(
                    ToolExecution(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=result_str,
                        success=success,
                    )
                )

            messages.append({"role": "user", "content": tool_results})
            iterations += 1

        if iterations >= MAX_ITERATIONS and response is not None:
            still_calling = any(getattr(b, "type", None) == "tool_use" for b in response.content)
            if still_calling:
                final_text = "I reached the maximum number of tool calls. Here's what I found so far."

        if not final_text.strip() and tool_executions:
            summary_parts = []
            for te in tool_executions:
                try:
                    parsed = json.loads(te.result)
                    msg = parsed.get("message", "")
                    icon = "✅" if te.success else "❌"
                    summary_parts.append(f"{icon} **{te.tool_name}**: {msg}")
                except (json.JSONDecodeError, AttributeError):
                    summary_parts.append(f"🔧 **{te.tool_name}**: ejecutado")
            final_text = "### Operaciones realizadas\n\n" + "\n".join(summary_parts)

        return AgentResponse(
            content=final_text,
            tool_executions=tool_executions,
        )

    @staticmethod
    def _extract_text(content_blocks: list[Any]) -> str:
        return "".join(b.text for b in content_blocks if getattr(b, "type", None) == "text")

    @staticmethod
    def _block_to_dict(block: Any) -> dict[str, Any]:
        """Serialize a content block back into the raw dict form the API expects."""
        btype = getattr(block, "type", None)
        if btype == "text":
            return {"type": "text", "text": block.text}
        if btype == "tool_use":
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            }
        # Unknown block type — fall back to model_dump if available.
        if hasattr(block, "model_dump"):
            return block.model_dump()
        return {"type": btype or "unknown"}
