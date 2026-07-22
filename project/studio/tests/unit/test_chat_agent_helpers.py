"""Unit tests for the pure helper functions of the chat-agent adapters.

These cover error classification, tool-schema conversion, cache logging, and
content-block serialization without needing a live LLM client.
"""

from __future__ import annotations

from types import SimpleNamespace

import anthropic

# ── claude_chat_agent ────────────────────────────────────────────────────────


def test_claude_is_retryable_error():
    from infra.adapters.claude_chat_agent import _is_retryable_error

    # Build instances without invoking the SDK constructors (which need a
    # request/response); isinstance-based classification still applies.
    assert _is_retryable_error(anthropic.RateLimitError.__new__(anthropic.RateLimitError)) is True
    assert _is_retryable_error(anthropic.APIConnectionError.__new__(anthropic.APIConnectionError)) is True

    status_err = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
    status_err.status_code = 503
    assert _is_retryable_error(status_err) is True

    non_retryable = anthropic.APIStatusError.__new__(anthropic.APIStatusError)
    non_retryable.status_code = 400
    assert _is_retryable_error(non_retryable) is False

    assert _is_retryable_error(ValueError("nope")) is False


def test_claude_langchain_tool_to_anthropic_schema():
    from infra.adapters.claude_chat_agent import _langchain_tool_to_anthropic_schema

    class _Args:
        @staticmethod
        def model_json_schema():
            return {"type": "object", "properties": {"x": {"type": "string"}}}

    tool = SimpleNamespace(name="do_it", description="does it", args_schema=_Args)
    schema = _langchain_tool_to_anthropic_schema(tool)
    assert schema["name"] == "do_it"
    assert schema["description"] == "does it"
    assert schema["input_schema"]["properties"] == {"x": {"type": "string"}}

    # Fallback path: no args_schema.
    bare = SimpleNamespace(name="bare", description=None, args_schema=None)
    bare_schema = _langchain_tool_to_anthropic_schema(bare)
    assert bare_schema["input_schema"] == {"type": "object", "properties": {}, "required": []}
    assert bare_schema["description"] == ""


def test_claude_log_cache_usage_no_crash():
    from infra.adapters.claude_chat_agent import _log_cache_usage

    # With usage reporting cache tokens.
    resp = SimpleNamespace(usage=SimpleNamespace(cache_read_input_tokens=5, cache_creation_input_tokens=2))
    _log_cache_usage(resp, "test")
    # No usage attribute at all.
    _log_cache_usage(SimpleNamespace(usage=None), "test")


def test_claude_extract_text_and_block_to_dict():
    from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter

    text_block = SimpleNamespace(type="text", text="hola")
    tool_block = SimpleNamespace(type="tool_use", id="t1", name="add", input={"a": 1})

    assert ClaudeChatAgentAdapter._extract_text([text_block, tool_block]) == "hola"

    assert ClaudeChatAgentAdapter._block_to_dict(text_block) == {"type": "text", "text": "hola"}
    assert ClaudeChatAgentAdapter._block_to_dict(tool_block) == {
        "type": "tool_use",
        "id": "t1",
        "name": "add",
        "input": {"a": 1},
    }
    # Unknown block with model_dump fallback.
    dumpable = SimpleNamespace(type="weird", model_dump=lambda: {"type": "weird", "k": "v"})
    assert ClaudeChatAgentAdapter._block_to_dict(dumpable) == {"type": "weird", "k": "v"}


# ── gemini_chat_agent ────────────────────────────────────────────────────────


def test_gemini_is_rate_limit_error():
    from infra.adapters.gemini_chat_agent import _is_rate_limit_error

    assert _is_rate_limit_error(Exception("Error 429 Too Many Requests")) is True
    assert _is_rate_limit_error(Exception("RESOURCE_EXHAUSTED")) is True
    assert _is_rate_limit_error(Exception("rate limit reached")) is True
    assert _is_rate_limit_error(Exception("some other failure")) is False
