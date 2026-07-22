"""Unit tests for ClaudeCodeCliInferenceAdapter."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from domain.exceptions import ConfigurationError, ServiceUnavailableError
from infra.adapters.claude_code_cli_inference import ClaudeCodeCliInferenceAdapter
from pydantic import BaseModel


class MockModel(BaseModel):
    name: str
    count: int


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    completed = MagicMock()
    completed.stdout = stdout.encode("utf-8")
    completed.stderr = stderr.encode("utf-8")
    completed.returncode = returncode
    return completed


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_structured_parses_json_from_result(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter(model="claude-sonnet-4-6")
    inner = json.dumps({"name": "wf", "count": 3})
    envelope = json.dumps({"type": "result", "is_error": False, "result": inner})
    mock_run.return_value = _completed(stdout=envelope)

    result = adapter.invoke("prompt", MockModel)

    assert result == MockModel(name="wf", count=3)
    args, kwargs = mock_run.call_args
    assert args[0][:3] == ["claude", "-p", "--output-format"]
    assert "--model" in args[0]


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_structured_strips_code_fences(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    fenced = "```json\n" + json.dumps({"name": "x", "count": 1}) + "\n```"
    envelope = json.dumps({"is_error": False, "result": fenced})
    mock_run.return_value = _completed(stdout=envelope)

    result = adapter.invoke("p", MockModel)

    assert result == MockModel(name="x", count=1)


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_structured_unwraps_placeholder_wrapper(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    inner = json.dumps({"$PARAMETER_NAME": {"name": "w", "count": 9}})
    envelope = json.dumps({"is_error": False, "result": inner})
    mock_run.return_value = _completed(stdout=envelope)

    result = adapter.invoke("p", MockModel)

    assert result == MockModel(name="w", count=9)


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_text_returns_result_field(mock_run, _mock_which, capsys):
    adapter = ClaudeCodeCliInferenceAdapter()
    envelope = json.dumps({"is_error": False, "result": "Conexión Exitosa"})
    mock_run.return_value = _completed(stdout=envelope)

    assert adapter.invoke_text("ping") == "Conexión Exitosa"
    out = capsys.readouterr().out
    assert "[CLI] → claude -p" in out
    assert "[CLI] invoke_text finalizado" in out


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value=None)
def test_invoke_raises_configuration_error_when_cli_missing(_mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    with pytest.raises(ConfigurationError):
        adapter.invoke_text("hi")


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_raises_service_unavailable_on_non_zero_exit(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    mock_run.return_value = _completed(stdout="", stderr="auth failed", returncode=1)

    with pytest.raises(ServiceUnavailableError, match=r"exit=1.*auth failed"):
        adapter.invoke_text("hi")


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_raises_when_result_is_not_json(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    envelope = json.dumps({"is_error": False, "result": "not json at all"})
    mock_run.return_value = _completed(stdout=envelope)

    with pytest.raises(ServiceUnavailableError, match="did not return valid JSON"):
        adapter.invoke("p", MockModel)


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_subprocess_env_strips_api_key_vars(mock_run, _mock_which, monkeypatch):
    """The CLI subprocess must not inherit ANTHROPIC_API_KEY so it falls back to subscription auth."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "stale-key")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "stale-token")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    adapter = ClaudeCodeCliInferenceAdapter()
    envelope = json.dumps({"is_error": False, "result": "ok"})
    mock_run.return_value = _completed(stdout=envelope)

    adapter.invoke_text("hello")

    _, kwargs = mock_run.call_args
    env = kwargs["env"]
    assert "ANTHROPIC_API_KEY" not in env
    assert "ANTHROPIC_AUTH_TOKEN" not in env
    assert env.get("PATH") == "/usr/bin:/bin"


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_surfaces_envelope_error_on_nonzero_exit(mock_run, _mock_which):
    """When the CLI exits non-zero but emits a structured error envelope, surface it."""
    envelope = json.dumps({"is_error": True, "result": "Invalid API key", "api_error_status": 401})
    mock_run.return_value = _completed(stdout=envelope, returncode=1)

    adapter = ClaudeCodeCliInferenceAdapter()
    with pytest.raises(ServiceUnavailableError, match="Invalid API key"):
        adapter.invoke_text("hi")


@patch("infra.adapters.claude_code_cli_inference.shutil.which", return_value="/usr/local/bin/claude")
@patch("infra.adapters.claude_code_cli_inference.subprocess.run")
def test_invoke_list_wraps_in_items(mock_run, _mock_which):
    adapter = ClaudeCodeCliInferenceAdapter()
    inner = json.dumps({"items": [{"name": "a", "count": 1}]})
    envelope = json.dumps({"is_error": False, "result": inner})
    mock_run.return_value = _completed(stdout=envelope)

    result = adapter.invoke("p", list[MockModel])
    assert len(result) == 1
    assert result[0].name == "a"
