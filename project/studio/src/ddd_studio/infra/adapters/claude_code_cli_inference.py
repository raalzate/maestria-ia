"""ClaudeCodeCliInferenceAdapter — InferencePort backed by the Claude Code CLI.

Runs `claude -p --output-format json` as a subprocess to leverage the user's
Claude subscription instead of metered API calls.

Structured output is achieved by injecting the target JSON Schema into the
prompt and parsing the resulting JSON from the `result` field of the CLI
envelope. The CLI must be installed and authenticated on the local machine.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
import types
from pathlib import Path
from typing import TypeVar, get_args, get_origin

from domain.exceptions import ConfigurationError, ServiceUnavailableError
from pydantic import BaseModel, create_model

T = TypeVar("T")

logger = logging.getLogger(__name__)

CLAUDE_CLI_BINARY = "claude"
_DEFAULT_TIMEOUT_SECONDS = 600
# Env vars that force the CLI to use an external API key instead of the
# subscription session managed by `claude login`. We strip them per-call.
_STRIP_ENV_KEYS = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_API_KEY",
        "CLAUDE_CODE_API_KEY",
    }
)
_FENCE_PREFIX = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_SUFFIX = re.compile(r"\s*```$")


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    s = _FENCE_PREFIX.sub("", s, count=1)
    s = _FENCE_SUFFIX.sub("", s, count=1)
    return s.strip()


def _ensure_cli_available() -> None:
    if shutil.which(CLAUDE_CLI_BINARY) is None:
        raise ConfigurationError(
            f"'{CLAUDE_CLI_BINARY}' CLI not found on PATH. "
            "Install Claude Code (https://docs.claude.com/claude-code) "
            "and authenticate with `claude login`."
        )


class ClaudeCodeCliInferenceAdapter:
    """InferencePort implementation that shells out to the Claude Code CLI."""

    def __init__(
        self,
        model: str | None = None,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        import os

        self._model_name = model or os.getenv("CLAUDE_MODEL", "claude-opus-4-8")
        self._timeout = timeout_seconds

    def invoke(self, prompt: str, output_schema: type[T]) -> T:
        _ensure_cli_available()
        start = time.time()
        schema_name = getattr(output_schema, "__name__", str(output_schema))

        if isinstance(output_schema, types.GenericAlias) and get_origin(output_schema) is list:
            item_type = get_args(output_schema)[0]
            wrapper = create_model("_ListWrapper", items=(list[item_type], ...))
            parsed = self._invoke_json(prompt, wrapper)
            duration = time.time() - start
            print(f"      [CLI] Extracción finalizada ({schema_name}) en {duration:.1f}s")
            return parsed.items  # type: ignore[return-value]

        parsed = self._invoke_json(prompt, output_schema)
        duration = time.time() - start
        print(f"      [CLI] Extracción finalizada ({schema_name}) en {duration:.1f}s")
        return parsed

    def invoke_text(self, prompt: str) -> str:
        _ensure_cli_available()
        start = time.time()
        envelope = self._run_cli(prompt)
        duration = time.time() - start
        text = str(envelope.get("result", ""))
        cost = envelope.get("total_cost_usd")
        cost_tag = f" cost=${cost:.6f}" if isinstance(cost, (int, float)) else ""
        print(
            f"      [CLI] invoke_text finalizado en {duration:.1f}s "
            f"(model={self._model_name} out={len(text)}c{cost_tag})"
        )
        return text

    def invoke_vision(self, prompt: str, images: list[bytes]) -> str:
        """Send prompt plus JPEG images via the CLI.

        The CLI cannot take inline image bytes, so frames are written to a temp
        directory and referenced by absolute path — Claude Code reads image
        files natively with its Read tool.
        """
        import shutil as _shutil
        import tempfile

        _ensure_cli_available()
        start = time.time()
        tmp_dir = Path(tempfile.mkdtemp(prefix="ddd_vision_"))
        try:
            paths = []
            for i, img in enumerate(images):
                p = tmp_dir / f"frame_{i:03d}.jpg"
                p.write_bytes(img)
                paths.append(str(p))
            listing = "\n".join(f"- {p}" for p in paths)
            instructed = (
                f"{prompt}\n\n"
                "=== IMAGE FRAMES ===\n"
                "Read and analyze the following image files (chronologically ordered "
                "keyframes of a screen recording) before answering:\n"
                f"{listing}"
            )
            envelope = self._run_cli(instructed)
        finally:
            _shutil.rmtree(tmp_dir, ignore_errors=True)
        duration = time.time() - start
        text = str(envelope.get("result", ""))
        print(f"      [CLI] Análisis de visión finalizado ({len(images)} imágenes) en {duration:.1f}s")
        return text

    def _invoke_json(self, prompt: str, schema: type[T]) -> T:
        if not issubclass(schema, BaseModel):  # type: ignore[arg-type]
            raise TypeError(f"output_schema must be a pydantic BaseModel, got {schema}")

        json_schema = schema.model_json_schema()  # type: ignore[attr-defined]
        instructed = (
            f"{prompt}\n\n"
            "=== STRICT OUTPUT FORMAT ===\n"
            "Return EXACTLY ONE valid JSON object conforming to this JSON Schema. "
            "No markdown fences. No preamble. No commentary. JSON only.\n\n"
            f"SCHEMA:\n{json.dumps(json_schema, ensure_ascii=False)}"
        )
        envelope = self._run_cli(instructed)
        raw = str(envelope.get("result", ""))
        cleaned = _strip_code_fences(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ServiceUnavailableError(
                f"Claude Code CLI did not return valid JSON for {schema.__name__}: {e}. "
                f"Raw (first 500 chars): {raw[:500]}"
            ) from e

        # Defensive unwrap: if Claude wraps the object under a single placeholder key
        # that doesn't belong to the schema, peel it off.
        if isinstance(data, dict):
            expected_keys = set(schema.model_fields.keys())  # type: ignore[attr-defined]
            if set(data.keys()).isdisjoint(expected_keys) and len(data) == 1:
                inner = next(iter(data.values()))
                if isinstance(inner, dict):
                    logger.warning(
                        "Claude Code CLI wrapped JSON under '%s' — unwrapping.",
                        next(iter(data.keys())),
                    )
                    data = inner

        return schema.model_validate(data)  # type: ignore[attr-defined,return-value]

    def _run_cli(self, prompt: str) -> dict:
        cmd = [
            CLAUDE_CLI_BINARY,
            "-p",
            "--output-format",
            "json",
            "--model",
            self._model_name,
        ]
        print(f"      [CLI] → claude -p --model {self._model_name} (prompt={len(prompt)}c, timeout={self._timeout}s)")
        logger.info(
            "claude-code-cli invocation model=%s prompt_chars=%d timeout=%ds",
            self._model_name,
            len(prompt),
            self._timeout,
        )
        # Strip external API-key vars so the CLI authenticates with the user's
        # `claude login` subscription session instead of a (possibly stale or
        # revoked) ANTHROPIC_API_KEY in the parent env.
        env = {k: v for k, v in os.environ.items() if k not in _STRIP_ENV_KEYS}
        try:
            completed = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=self._timeout,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as e:
            raise ServiceUnavailableError(f"Claude Code CLI timed out after {self._timeout}s") from e
        except FileNotFoundError as e:
            raise ConfigurationError(f"Could not execute '{CLAUDE_CLI_BINARY}'. Is Claude Code installed?") from e

        stdout_text = completed.stdout.decode("utf-8", errors="replace")
        stderr_text = completed.stderr.decode("utf-8", errors="replace").strip()

        # Try to parse stdout as JSON regardless of returncode — the CLI emits
        # structured errors there when --output-format json is used.
        envelope: dict | None = None
        if stdout_text.strip():
            try:
                parsed = json.loads(stdout_text)
                if isinstance(parsed, dict):
                    envelope = parsed
            except json.JSONDecodeError:
                envelope = None

        if completed.returncode != 0:
            detail_parts = [f"exit={completed.returncode}"]
            if envelope:
                detail_parts.append(f"envelope={json.dumps(envelope, ensure_ascii=False)[:400]}")
            if stderr_text:
                detail_parts.append(f"stderr={stderr_text[:300]}")
            if not envelope and stdout_text:
                detail_parts.append(f"stdout={stdout_text.strip()[:300]}")
            raise ServiceUnavailableError("Claude Code CLI failed: " + " | ".join(detail_parts))

        if envelope is None:
            raise ServiceUnavailableError(
                f"Claude Code CLI returned non-JSON stdout. Raw (first 500 chars): {stdout_text[:500]}"
            )

        if envelope.get("is_error"):
            raise ServiceUnavailableError(f"Claude Code CLI reported error: {envelope.get('result', envelope)}")
        return envelope
