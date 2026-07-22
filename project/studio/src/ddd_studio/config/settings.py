import os
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

# Load environment variables. In the packaged desktop app secrets are not
# bundled; users drop a `.env` into the writable data dir (DDD_STUDIO_DATA_DIR).
# Prefer that file when present, otherwise fall back to CWD discovery (dev mode).
_DATA_DIR = os.environ.get("DDD_STUDIO_DATA_DIR")
if _DATA_DIR and os.path.exists(os.path.join(_DATA_DIR, ".env")):
    load_dotenv(os.path.join(_DATA_DIR, ".env"))
else:
    load_dotenv()

# Provider selection: "claude" (default) or "gemini" (legacy, kept during migration window)
LLM_PROVIDER: Literal["claude", "gemini"] = os.getenv("LLM_PROVIDER", "claude").lower()  # type: ignore[assignment]

# Gemini (legacy)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("LLM_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Anthropic / Claude (current)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


# Claude Code CLI (subscription-based, headless): when enabled, inference and
# chat are routed through `claude -p --output-format json` instead of the API.
USE_CLAUDE_CODE_CLI = _env_flag("USE_CLAUDE_CODE_CLI")

TRANSCRIPTION_MAX_BYTES = int(os.getenv("TRANSCRIPTION_MAX_BYTES", str(10 * 1024 * 1024)))

# Legacy aliases for backward compatibility with existing UI/services code
LLM_MODEL = CLAUDE_MODEL if LLM_PROVIDER == "claude" else GEMINI_MODEL
LLM_API_KEY = ANTHROPIC_API_KEY if LLM_PROVIDER == "claude" else GOOGLE_API_KEY
LOCAL_MODEL_PATH = None  # Removed — remote-only inference
LLM_MODEL_PATH = None  # Removed — remote-only inference
WHISPER_MODEL = os.getenv("WHISPER_MODEL") or None

RESPONSE_LANGUAGE = os.getenv("RESPONSE_LANGUAGE", "es")

# Pricing (Claude Sonnet 4.6 default: $3/$15 per MTok)
if LLM_PROVIDER == "claude":
    PRICE_PER_1K_INPUT_TOKENS = 0.003
    PRICE_PER_1K_OUTPUT_TOKENS = 0.015
else:
    PRICE_PER_1K_INPUT_TOKENS = 0.0035
    PRICE_PER_1K_OUTPUT_TOKENS = 0.0105


def load_api_key():
    """Validate that API key and model are available (env or persisted config)."""
    # Persisted config can override env. Subscription CLI mode skips the API-key check.
    try:
        from ui.utils.storage import load_llm_config

        saved = load_llm_config() or {}
    except Exception:
        saved = {}

    if USE_CLAUDE_CODE_CLI or saved.get("use_claude_code_cli"):
        return

    if LLM_PROVIDER == "claude":
        if ANTHROPIC_API_KEY and CLAUDE_MODEL:
            return
        err_msg = "ANTHROPIC_API_KEY or CLAUDE_MODEL not set in env"
    else:
        if GOOGLE_API_KEY and GEMINI_MODEL:
            return
        err_msg = "GOOGLE_API_KEY or GEMINI_MODEL not set in env"
    if saved.get("api_key") and saved.get("model_name"):
        return
    raise ValueError(err_msg)


class TokenUsageCallback(BaseCallbackHandler):
    """Callback to capture input and output token usage."""

    def __init__(self):
        super().__init__()
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_msg = ""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when the LLM finishes execution."""
        usage = response.llm_output.get("token_usage", {})

        if usage:
            self.input_tokens = usage.get("input_tokens", 0)
            self.output_tokens = usage.get("output_tokens", 0)

            if self.input_tokens == 0:
                self.input_tokens = usage.get("prompt_token_count", 0)
            if self.output_tokens == 0:
                self.output_tokens = usage.get("candidates_token_count", 0)

        input_cost = (self.input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        output_cost = (self.output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        total_cost = input_cost + output_cost

        self.cost_msg = (
            f"Input: {self.input_tokens} tk (${input_cost:.6f}) | "
            f"Output: {self.output_tokens} tk (${output_cost:.6f}) | "
            f"Total: ${total_cost:.6f} (Model: {LLM_MODEL})"
        )
