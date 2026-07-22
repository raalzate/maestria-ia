"""Unit tests for Dynamic LLM Configuration."""

from __future__ import annotations

import os
from unittest.mock import patch

from infra.inference_provider import InferenceProvider


def test_inference_provider_default_config(monkeypatch):
    """Verify provider loads defaults from environment variables.

    With LLM_PROVIDER=claude, defaults come from CLAUDE_MODEL / ANTHROPIC_API_KEY.
    """
    from config import settings

    monkeypatch.setattr(settings, "LLM_PROVIDER", "claude")
    with (
        patch.dict(os.environ, {"CLAUDE_MODEL": "claude-env-model", "ANTHROPIC_API_KEY": "env-key"}),
        patch("streamlit.session_state", {}) as mock_state,
        patch("ui.utils.storage.load_llm_config", return_value=None),
    ):
        config = InferenceProvider.get_config()

        assert config["model_name"] == "claude-env-model"
        assert config["api_key"] == "env-key"
        assert "llm_config" in mock_state


def test_inference_provider_default_config_gemini(monkeypatch):
    """Legacy path: when LLM_PROVIDER=gemini, defaults come from GEMINI_MODEL / GOOGLE_API_KEY."""
    from config import settings

    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    with (
        patch.dict(os.environ, {"GEMINI_MODEL": "env-model", "GOOGLE_API_KEY": "env-key"}),
        patch("streamlit.session_state", {}) as mock_state,
        patch("ui.utils.storage.load_llm_config", return_value=None),
    ):
        config = InferenceProvider.get_config()

        assert config["model_name"] == "env-model"
        assert config["api_key"] == "env-key"
        assert "llm_config" in mock_state


def test_inference_provider_override():
    """Verify session state overrides environment variables."""
    mock_state = {
        "llm_config": {
            "model_name": "override-model",
            "api_key": "override-key",
        }
    }

    with (
        patch.dict(os.environ, {"GEMINI_MODEL": "env-model", "GOOGLE_API_KEY": "env-key"}),
        patch("streamlit.session_state", mock_state),
    ):
        config = InferenceProvider.get_config()

        assert config["model_name"] == "override-model"
        assert config["api_key"] == "override-key"
        assert "temperature" not in config


def test_inference_provider_strips_legacy_temperature():
    """Legacy persisted configs with `temperature` must be ignored silently."""
    mock_state = {
        "llm_config": {
            "model_name": "legacy-model",
            "api_key": "legacy-key",
            "temperature": 0.7,
        }
    }

    with patch("streamlit.session_state", mock_state):
        config = InferenceProvider.get_config()
        assert "temperature" not in config


@patch("infra.adapters.claude_inference.ClaudeInferenceAdapter")
def test_get_inference_port_uses_config(mock_adapter):
    """Verify that get_inference_port initializes the Claude adapter with correct settings."""
    mock_state = {
        "llm_config": {
            "model_name": "claude-sonnet-4-6",
            "api_key": "test-key",
        }
    }

    with patch("streamlit.session_state", mock_state):
        InferenceProvider.get_inference_port()

        mock_adapter.assert_called_once_with(model="claude-sonnet-4-6", api_key="test-key")


@patch("infra.adapters.claude_chat_agent.ClaudeChatAgentAdapter")
def test_get_chat_agent_port_uses_config(mock_agent):
    """Verify that get_chat_agent_port initializes the Claude agent with correct configuration."""
    mock_state = {
        "llm_config": {
            "model_name": "claude-opus-4-7",
            "api_key": "agent-key",
        }
    }

    with patch("streamlit.session_state", mock_state):
        InferenceProvider.get_chat_agent_port()

        mock_agent.assert_called_once_with(model="claude-opus-4-7", api_key="agent-key")


@patch("infra.adapters.claude_code_cli_inference.ClaudeCodeCliInferenceAdapter")
def test_get_inference_port_uses_claude_code_cli_when_flag_set(mock_adapter):
    """When use_claude_code_cli=True, factory bypasses API adapters and uses CLI."""
    mock_state = {
        "llm_config": {
            "model_name": "claude-sonnet-4-6",
            "api_key": "ignored-in-cli-mode",
            "use_claude_code_cli": True,
        }
    }

    with patch("streamlit.session_state", mock_state):
        InferenceProvider.get_inference_port()
        mock_adapter.assert_called_once_with(model="claude-sonnet-4-6")


@patch("infra.adapters.claude_chat_agent.ClaudeChatAgentAdapter")
def test_get_chat_agent_port_ignores_claude_code_cli_flag(mock_agent):
    """Chat agent always uses the API-backed adapter, even when CLI flag is on."""
    mock_state = {
        "llm_config": {
            "model_name": "claude-opus-4-7",
            "api_key": "agent-key",
            "use_claude_code_cli": True,
        }
    }

    with patch("streamlit.session_state", mock_state):
        InferenceProvider.get_chat_agent_port()
        mock_agent.assert_called_once_with(model="claude-opus-4-7", api_key="agent-key")


@patch("infra.adapters.gemini_inference.GeminiInferenceAdapter")
def test_get_inference_port_gemini_when_model_name_is_gemini(mock_adapter):
    """Provider is inferred from the model name: gemini-* routes to Gemini adapter."""
    mock_state = {
        "llm_config": {
            "model_name": "gemini-2.5-flash",
            "api_key": "test-key",
        }
    }

    with patch("streamlit.session_state", mock_state):
        InferenceProvider.get_inference_port()

        mock_adapter.assert_called_once_with(model="gemini-2.5-flash", api_key="test-key")
