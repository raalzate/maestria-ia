"""Unit tests for ClaudeChatAgentAdapter (Messages API tool_use loop)."""

from __future__ import annotations

from unittest.mock import MagicMock

from models.domain_analysis import (
    BigPicture,
    DomainAnalysis,
    NodoGrafo,
)


def _make_model() -> DomainAnalysis:
    return DomainAnalysis(
        nombre_proyecto="TestProject",
        version="1.0.0",
        fecha_analisis="2026-03-19",
        big_picture=BigPicture(
            descripcion="Test",
            nodos=[
                NodoGrafo(
                    id="cmd_test",
                    tipo_elemento="Comando",
                    nombre="Test",
                    descripcion="Test node",
                    nivel="big_picture",
                ),
            ],
            aristas=[],
        ),
        agregados=[],
    )


def _make_session_state(model: DomainAnalysis) -> dict:
    return {
        "analysis_result": {"analysis": model},
        "model_history": [],
    }


def _text_block(text: str):
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def _tool_use_block(tool_id: str, name: str, tool_input: dict):
    b = MagicMock()
    b.type = "tool_use"
    b.id = tool_id
    b.name = name
    b.input = tool_input
    return b


def _response(blocks: list, stop_reason: str = "end_turn"):
    r = MagicMock()
    r.content = blocks
    r.stop_reason = stop_reason
    return r


class TestClaudeChatAgentAdapter:
    """Tests for the Claude tool_use loop with mocked client."""

    def test_text_only_response_returns_agent_response(self):
        """When Claude returns only a text block, return AgentResponse with no tool executions."""
        from domain.models.tool_schemas import AgentResponse
        from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter
        from services.model_accessor import ModelAccessor

        model = _make_model()
        accessor = ModelAccessor(_make_session_state(model))

        mock_client = MagicMock()
        mock_client.messages.create.return_value = _response([_text_block("The model looks good.")])

        adapter = ClaudeChatAgentAdapter(model="claude-sonnet-4-6", api_key="fake-key")
        adapter._client_instance = mock_client
        result = adapter.run(
            user_message="How does the model look?",
            history=[],
            system_prompt="You are an architect.",
            model_accessor=accessor,
        )

        assert isinstance(result, AgentResponse)
        assert result.content == "The model looks good."
        assert result.tool_executions == []
        # system prompt must be forwarded as the top-level `system` kwarg.
        # It's sent as a list of text blocks with cache_control for prompt caching.
        _, kwargs = mock_client.messages.create.call_args
        assert isinstance(kwargs["system"], list)
        assert kwargs["system"][0]["type"] == "text"
        assert kwargs["system"][0]["text"] == "You are an architect."
        assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
        assert kwargs["model"] == "claude-sonnet-4-6"
        assert "temperature" not in kwargs

    def test_tool_call_executes_and_returns_result(self):
        """When Claude emits tool_use, execute the tool and feed tool_result back."""
        from domain.models.tool_schemas import AgentResponse
        from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter
        from services.model_accessor import ModelAccessor

        model = _make_model()
        accessor = ModelAccessor(_make_session_state(model))

        first = _response(
            [_tool_use_block("call_1", "query_model", {"section": "summary"})],
            stop_reason="tool_use",
        )
        second = _response([_text_block("The model has 1 node.")])

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [first, second]

        adapter = ClaudeChatAgentAdapter(model="claude-sonnet-4-6", api_key="fake-key")
        adapter._client_instance = mock_client
        result = adapter.run(
            user_message="How many nodes?",
            history=[],
            system_prompt="You are an architect.",
            model_accessor=accessor,
        )

        assert isinstance(result, AgentResponse)
        assert result.content == "The model has 1 node."
        assert len(result.tool_executions) == 1
        assert result.tool_executions[0].tool_name == "query_model"

        # Verify a tool_result block was appended to the conversation.
        # (messages is mutated after the second call, so scan rather than index.)
        second_kwargs = mock_client.messages.create.call_args_list[1].kwargs
        tool_result_found = False
        for m in second_kwargs["messages"]:
            if m["role"] == "user" and isinstance(m["content"], list):
                for block in m["content"]:
                    if block.get("type") == "tool_result" and block.get("tool_use_id") == "call_1":
                        tool_result_found = True
        assert tool_result_found

    def test_max_iterations_prevents_infinite_loop(self):
        """The loop stops after MAX_ITERATIONS even if Claude keeps calling tools."""
        from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter
        from services.model_accessor import ModelAccessor

        model = _make_model()
        accessor = ModelAccessor(_make_session_state(model))

        looping = _response(
            [_tool_use_block("call_loop", "query_model", {"section": "summary"})],
            stop_reason="tool_use",
        )

        mock_client = MagicMock()
        mock_client.messages.create.return_value = looping

        adapter = ClaudeChatAgentAdapter(model="claude-sonnet-4-6", api_key="fake-key")
        adapter._client_instance = mock_client
        result = adapter.run(
            user_message="Loop forever",
            history=[],
            system_prompt="You are an architect.",
            model_accessor=accessor,
        )

        # Should stop after MAX_ITERATIONS=5 calls.
        assert mock_client.messages.create.call_count == 5
        # Synthesized content must be present when max iterations is hit.
        assert result.content

    def test_agent_response_includes_operation_details(self):
        """After a successful add_node tool call the final response mentions the new element."""
        from infra.adapters.claude_chat_agent import ClaudeChatAgentAdapter
        from services.model_accessor import ModelAccessor

        model = _make_model()
        accessor = ModelAccessor(_make_session_state(model))

        add_node_call = _response(
            [
                _tool_use_block(
                    "call_add",
                    "add_node",
                    {
                        "scope": "big_picture",
                        "node_name": "NuevoEvento",
                        "node_type": "Evento",
                        "description": "A new event",
                        "nivel": "big_picture",
                    },
                )
            ],
            stop_reason="tool_use",
        )
        final = _response([_text_block("I've added NuevoEvento to the big picture.")])

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [add_node_call, final]

        adapter = ClaudeChatAgentAdapter(model="claude-sonnet-4-6", api_key="fake-key")
        adapter._client_instance = mock_client
        result = adapter.run(
            user_message="Add NuevoEvento",
            history=[],
            system_prompt="You are an architect.",
            model_accessor=accessor,
        )

        assert len(result.tool_executions) == 1
        assert result.tool_executions[0].tool_name == "add_node"
        assert "NuevoEvento" in result.content
