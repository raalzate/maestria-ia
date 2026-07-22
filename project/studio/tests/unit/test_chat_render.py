"""Coverage for ui.components.chat.render_chat_tab via a fully mocked Streamlit.

render_chat_tab is the largest chat.py function; driving it with a controlled
`st` double exercises the context-config, history-render and agent-write paths.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from models.domain_analysis import BigPicture, DomainAnalysis, NodoGrafo


class _SessionState(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def __setattr__(self, k, v):
        self[k] = v

    def __delattr__(self, k):
        self.pop(k, None)


def _analysis() -> DomainAnalysis:
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-14",
        big_picture=BigPicture(
            descripcion="d",
            nodos=[NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="", nivel="big_picture")],
            aristas=[],
        ),
        agregados=[],
        read_models=[],
        politicas_inter_agregados=[],
    )


def _make_st(session_state, *, chat_input=None) -> MagicMock:
    """A Streamlit double: columns yield real-bool toggles, widgets are inert."""
    st = MagicMock()
    st.session_state = session_state

    def _col():
        c = MagicMock()
        c.toggle.return_value = True
        c.checkbox.return_value = False
        c.button.return_value = False
        return c

    st.columns.side_effect = lambda spec: [_col() for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.toggle.return_value = True
    st.checkbox.return_value = False
    st.button.return_value = False
    st.chat_input.return_value = chat_input
    return st


def test_render_chat_tab_warns_without_engine():
    session = _SessionState({"_chat_agent_port": None, "_inference_port": None})
    st = _make_st(session)
    with patch("ui.components.chat.st", st):
        from ui.components.chat import render_chat_tab

        render_chat_tab(_analysis())
    st.warning.assert_called()


def test_render_chat_tab_renders_history_without_input():
    session = _SessionState(
        {
            "_chat_agent_port": MagicMock(),
            "_inference_port": None,
            "chat_messages": [
                {"role": "user", "content": "hola"},
                {
                    "role": "assistant",
                    "content": "respuesta",
                    "tool_executions": [
                        SimpleNamespace(
                            tool_name="add_node",
                            success=True,
                            arguments={"x": 1},
                            result=json.dumps({"message": "ok"}),
                        )
                    ],
                },
            ],
            "analysis_result": {"analysis": _analysis(), "transcript": "t"},
        }
    )
    st = _make_st(session, chat_input=None)
    with patch("ui.components.chat.st", st):
        from ui.components.chat import render_chat_tab

        render_chat_tab(_analysis())
    # Rendered the context-config + history without hitting the input branch.
    st.subheader.assert_called()
    st.chat_input.assert_called_once()


def test_render_chat_tab_agent_write_path_persists_and_reruns():
    agent = MagicMock()
    agent.run.return_value = SimpleNamespace(
        content="",  # empty -> forces the tool-summary synthesis branch
        tool_executions=[
            SimpleNamespace(
                tool_name="add_node",
                success=True,
                arguments={"node_name": "X"},
                result=json.dumps({"message": "added"}),
            )
        ],
    )
    session = _SessionState(
        {
            "_chat_agent_port": agent,
            "_inference_port": None,
            "chat_messages": [],
            "analysis_result": {"analysis": _analysis(), "transcript": "t"},
        }
    )
    st = _make_st(session, chat_input="agrega un nodo")
    with (
        patch("ui.components.chat.st", st),
        patch("ui.components.chat.registry") as reg,
        patch("ui.utils.storage.save_static_json") as save_json,
    ):
        reg.get.return_value.render.return_value.to_string.return_value = "system prompt"
        from ui.components.chat import render_chat_tab

        render_chat_tab(_analysis())

    agent.run.assert_called_once()
    save_json.assert_called_once()  # write tool -> persisted
    st.rerun.assert_called()


def test_render_chat_tab_fallback_inference_path():
    inference = MagicMock()
    inference.invoke_text.return_value = "respuesta libre"
    session = _SessionState(
        {
            "_chat_agent_port": None,
            "_inference_port": inference,
            "chat_messages": [],
            "analysis_result": {"analysis": _analysis(), "transcript": "t"},
        }
    )
    st = _make_st(session, chat_input="hola")
    with (
        patch("ui.components.chat.st", st),
        patch("ui.components.chat.registry") as reg,
    ):
        reg.get.return_value.render.return_value.to_string.return_value = "system prompt"
        from ui.components.chat import render_chat_tab

        render_chat_tab(_analysis())

    inference.invoke_text.assert_called_once()
