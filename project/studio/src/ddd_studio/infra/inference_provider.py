"""Provider for dynamic LLM inference injection.

Checks streamlit session state for overrides, falls back to env vars.
Branches on settings.LLM_PROVIDER to select Claude or Gemini adapters.
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from config import settings
from domain.ports import ChatAgentPort, InferencePort


def _is_claude_model(model_name: str | None) -> bool:
    return bool(model_name) and model_name.lower().startswith("claude")


class InferenceProvider:
    """Manages the lifecycle and configuration of LLM clients."""

    @staticmethod
    def _default_model() -> str:
        if settings.LLM_PROVIDER == "claude":
            return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
        return os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    @staticmethod
    def _default_api_key() -> str:
        if settings.LLM_PROVIDER == "claude":
            return os.getenv("ANTHROPIC_API_KEY", "")
        return os.getenv("GOOGLE_API_KEY", "")

    @staticmethod
    def get_config() -> dict[str, Any]:
        """Get current active configuration from session state, persisted file, or env."""
        if "llm_config" not in st.session_state:
            from ui.utils.storage import load_llm_config

            saved = load_llm_config()
            st.session_state["llm_config"] = saved or {
                "model_name": InferenceProvider._default_model(),
                "api_key": InferenceProvider._default_api_key(),
                "use_claude_code_cli": settings.USE_CLAUDE_CODE_CLI,
            }
        cfg = st.session_state["llm_config"]
        cfg.pop("temperature", None)
        # Env var acts as a default; persisted value overrides per session.
        cfg.setdefault("use_claude_code_cli", settings.USE_CLAUDE_CODE_CLI)
        return cfg

    @staticmethod
    def _resolve_provider(model_name: str | None) -> str:
        """Pick provider based on the selected model name; fallback to settings.LLM_PROVIDER."""
        if _is_claude_model(model_name):
            return "claude"
        if model_name and model_name.lower().startswith("gemini"):
            return "gemini"
        return settings.LLM_PROVIDER

    @staticmethod
    def get_inference_port() -> InferencePort:
        """Create an InferencePort with current config."""
        config = InferenceProvider.get_config()
        model_name = config.get("model_name")
        if config.get("use_claude_code_cli"):
            from infra.adapters.claude_code_cli_inference import ClaudeCodeCliInferenceAdapter

            print(f"      [InferenceProvider] backend=ClaudeCodeCLI model={model_name}")
            return ClaudeCodeCliInferenceAdapter(model=model_name)
        provider = InferenceProvider._resolve_provider(model_name)
        print(f"      [InferenceProvider] backend=API/{provider} model={model_name}")
        if provider == "claude":
            from infra.adapters.claude_inference import ClaudeInferenceAdapter

            return ClaudeInferenceAdapter(
                model=config["model_name"],
                api_key=config["api_key"],
            )
        from infra.adapters.gemini_inference import GeminiInferenceAdapter

        return GeminiInferenceAdapter(
            model=config["model_name"],
            api_key=config["api_key"],
        )

    @staticmethod
    def get_chat_agent_port() -> ChatAgentPort:
        """Create a ChatAgentPort with current config.

        Note: the Claude Code CLI flag only affects analysis/inference. The chat
        agent always uses an API-backed adapter so tool calls keep working.
        """
        config = InferenceProvider.get_config()
        provider = InferenceProvider._resolve_provider(config.get("model_name"))
        if provider == "claude":
            from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter

            return ClaudeChatAgentAdapter(
                model=config["model_name"],
                api_key=config["api_key"],
            )
        from infra.adapters.gemini_chat_agent import GeminiChatAgentAdapter

        return GeminiChatAgentAdapter(
            model=config["model_name"],
            api_key=config["api_key"],
        )


def get_inference_client() -> InferencePort:
    """Helper for functional injection."""
    return InferenceProvider.get_inference_port()


def get_chat_agent() -> ChatAgentPort:
    """Helper for functional injection."""
    return InferenceProvider.get_chat_agent_port()
