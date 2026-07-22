"""Unit tests for ClaudeInferenceAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from domain.exceptions import ServiceUnavailableError
from infra.adapters.claude_inference import ClaudeInferenceAdapter
from pydantic import BaseModel


class MockModel(BaseModel):
    name: str
    count: int


def _make_tool_use_response(tool_input: dict, name: str = "extract_structured_output"):
    """Build a mock Anthropic response whose content contains a single tool_use block."""
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.input = tool_input

    response = MagicMock()
    response.content = [block]
    response.stop_reason = "tool_use"
    return response


def _make_text_response(text: str):
    """Build a mock Anthropic response whose content is a single text block."""
    block = MagicMock()
    block.type = "text"
    block.text = text

    response = MagicMock()
    response.content = [block]
    response.stop_reason = "end_turn"
    return response


@patch("infra.adapters.claude_inference.time.sleep", return_value=None)
@patch("infra.adapters.claude_inference.anthropic.Anthropic")
def test_claude_invoke_structured(mock_anthropic_cls, _mock_sleep):
    """ClaudeInferenceAdapter.invoke forces a tool call and parses the tool_use input."""
    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="fake")

    client = mock_anthropic_cls.return_value
    client.messages.create.return_value = _make_tool_use_response({"name": "test", "count": 5})

    result = adapter.invoke("prompt", MockModel)

    assert result == MockModel(name="test", count=5)
    _, kwargs = client.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert "temperature" not in kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "extract_structured_output"}
    assert kwargs["tools"][0]["name"] == "extract_structured_output"
    assert kwargs["tools"][0]["input_schema"]["properties"]["name"]["type"] == "string"


@patch("infra.adapters.claude_inference.time.sleep", return_value=None)
@patch("infra.adapters.claude_inference.anthropic.Anthropic")
def test_claude_invoke_list_structured(mock_anthropic_cls, _mock_sleep):
    """ClaudeInferenceAdapter.invoke wraps list[T] in a _ListWrapper schema."""
    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="fake")

    client = mock_anthropic_cls.return_value
    client.messages.create.return_value = _make_tool_use_response({"items": [{"name": "a", "count": 1}]})

    result = adapter.invoke("prompt", list[MockModel])

    assert len(result) == 1
    assert result[0].name == "a"
    _, kwargs = client.messages.create.call_args
    assert "items" in kwargs["tools"][0]["input_schema"]["properties"]


@patch("infra.adapters.claude_inference.time.sleep", return_value=None)
@patch("infra.adapters.claude_inference.anthropic.Anthropic")
def test_claude_unwraps_placeholder_wrapper(mock_anthropic_cls, _mock_sleep):
    """If Claude nests the real object under a single placeholder key, unwrap it."""
    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="fake")

    client = mock_anthropic_cls.return_value
    wrapped = {"$PARAMETER_NAME": {"name": "wrapped", "count": 7}}
    client.messages.create.return_value = _make_tool_use_response(wrapped)

    result = adapter.invoke("prompt", MockModel)

    assert result == MockModel(name="wrapped", count=7)


@patch("infra.adapters.claude_inference.time.sleep", return_value=None)
@patch("infra.adapters.claude_inference.anthropic.Anthropic")
def test_claude_invoke_text(mock_anthropic_cls, _mock_sleep):
    """ClaudeInferenceAdapter.invoke_text returns concatenated text blocks."""
    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="fake")

    client = mock_anthropic_cls.return_value
    client.messages.create.return_value = _make_text_response("raw response")

    result = adapter.invoke_text("prompt")

    assert result == "raw response"
    _, kwargs = client.messages.create.call_args
    assert kwargs["messages"] == [{"role": "user", "content": "prompt"}]
    assert "tools" not in kwargs


@patch("infra.adapters.claude_inference.time.sleep", return_value=None)
@patch("infra.adapters.claude_inference.anthropic.Anthropic")
def test_claude_retryable_error_eventually_raises(mock_anthropic_cls, _mock_sleep):
    """A persistent retryable error is surfaced after the retry budget is exhausted.

    Tenacity's wait is patched via time.sleep mock, so this runs fast.
    """
    import anthropic

    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="fake")

    client = mock_anthropic_cls.return_value
    client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())

    with pytest.raises((ServiceUnavailableError, anthropic.APIConnectionError)):
        adapter.invoke_text("prompt")


def test_claude_missing_api_key_raises_configuration_error(monkeypatch):
    """Instantiating without an API key and lazily accessing client raises ConfigurationError."""
    from domain.exceptions import ConfigurationError

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    adapter = ClaudeInferenceAdapter(model="claude-sonnet-4-6", api_key="")
    with pytest.raises(ConfigurationError):
        _ = adapter._client
