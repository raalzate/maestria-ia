"""Branch coverage for agent_tools query/error paths and chat._render_tool_executions."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.model_accessor import ModelAccessor


def _model() -> DomainAnalysis:
    bp = BigPicture(
        descripcion="d",
        nodos=[
            NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="", nivel="big_picture"),
            NodoGrafo(id="BP-AGG-Ped", tipo_elemento="Agregado", nombre="Pedido", descripcion="", nivel="big_picture"),
        ],
        aristas=[AristaGrafo(fuente="BP-CMD-A", destino="BP-AGG-Ped", descripcion="va")],
    )
    agg = GrafoPorAgregado(
        nombre_agregado="Pedido",
        entidad_raiz="Pedido",
        nodos=[
            NodoGrafo(
                id="AGG-AGG-Ped", tipo_elemento="Agregado", nombre="Pedido", descripcion="", nivel="process_level"
            )
        ],
        aristas=[],
    )
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-14",
        big_picture=bp,
        agregados=[agg],
        read_models=[ReadModel(nombre="Vista", descripcion="v", proyecta=["BP-CMD-A"])],
        politicas_inter_agregados=[],
    )


def _tools():
    from services.agent_tools import create_tools

    accessor = ModelAccessor({"analysis_result": {"analysis": _model()}})
    return {t.name: t for t in create_tools(accessor)}, accessor


# ── query_model sections ─────────────────────────────────────────────────────


def test_query_model_sections():
    tools, _ = _tools()
    q = tools["query_model"]

    assert "nodos" in q.invoke({"section": "big_picture"})
    # read_models / policies / summary return JSON without raising.
    json.loads(q.invoke({"section": "read_models"}))
    json.loads(q.invoke({"section": "policies"}))
    summary = json.loads(q.invoke({"section": "summary"}))
    assert summary["nombre_proyecto"] == "P"

    # aggregate section with a valid name.
    agg = json.loads(q.invoke({"section": "aggregate", "aggregate_name": "Pedido"}))
    assert agg["nombre_agregado"] == "Pedido"


def test_query_model_aggregate_errors():
    tools, _ = _tools()
    q = tools["query_model"]

    missing_name = json.loads(q.invoke({"section": "aggregate"}))
    assert missing_name["success"] is False

    not_found = json.loads(q.invoke({"section": "aggregate", "aggregate_name": "NoExiste"}))
    assert not_found["success"] is False


def test_add_node_invalid_scope_combinations():
    tools, _ = _tools()
    add = tools["add_node"]

    # scope=aggregate but no aggregate_name -> container resolution error.
    res = json.loads(add.invoke({"scope": "aggregate", "node_name": "X", "node_type": "Comando", "description": "d"}))
    assert res["success"] is False


def test_undo_with_no_history():
    tools, _ = _tools()
    res = json.loads(tools["undo_last_change"].invoke({}))
    assert res["success"] is False
    assert "No previous changes" in res["message"]


# ── chat._render_tool_executions ─────────────────────────────────────────────


@patch("ui.components.chat.st")
def test_render_tool_executions_empty_is_noop(mock_st):
    from ui.components.chat import _render_tool_executions

    _render_tool_executions([])
    mock_st.expander.assert_not_called()


@patch("ui.components.chat.st")
def test_render_tool_executions_writes_and_reads(mock_st):
    from ui.components.chat import _render_tool_executions

    mock_st.expander.return_value = MagicMock()  # context manager via MagicMock
    execs = [
        SimpleNamespace(
            tool_name="add_node",
            success=True,
            arguments={"node_name": "X"},
            result=json.dumps({"success": True, "message": "Added X"}),
        ),
        SimpleNamespace(
            tool_name="query_model",
            success=False,
            arguments={"section": "summary"},
            result="not-json",
        ),
    ]
    _render_tool_executions(execs)
    mock_st.expander.assert_called_once()
    # Label reflects 1 write + 1 read.
    label = mock_st.expander.call_args[0][0]
    assert "escritura" in label and "consulta" in label
