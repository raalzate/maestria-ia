"""Unit tests for the React Flow payload serializer."""

from __future__ import annotations

from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.diagram_dsl import react_flow_payload as rfp


def _node(nid: str, tipo: str = "Comando", nombre: str | None = None, nivel: str = "big_picture") -> NodoGrafo:
    return NodoGrafo(
        id=nid,
        tipo_elemento=tipo,
        nombre=nombre or nid.split("-")[-1],
        descripcion="desc",
        nivel=nivel,
    )


def _analysis() -> DomainAnalysis:
    bp = BigPicture(
        descripcion="x",
        nodos=[
            _node("BP-ACT-Cliente", "Actor"),
            _node("BP-CMD-Confirmar", "Comando"),
            _node("BP-AGG-Pedido", "Agregado"),
            _node("BP-EVT-Confirmado", "Evento"),
            _node("BP-POL-Reactiva", "Política"),
            _node("BP-HOT-RiesgoFraude", "Hotspot"),
            _node("BP-SYS-Stripe", "Sistema Externo"),
        ],
        aristas=[
            AristaGrafo(fuente="BP-ACT-Cliente", destino="BP-CMD-Confirmar", descripcion="dispara"),
            AristaGrafo(fuente="BP-CMD-Confirmar", destino="BP-AGG-Pedido", descripcion="se dirige a"),
            AristaGrafo(fuente="BP-AGG-Pedido", destino="BP-EVT-Confirmado", descripcion="produce"),
            AristaGrafo(fuente="BP-EVT-Confirmado", destino="BP-POL-Reactiva", descripcion="activa"),
            AristaGrafo(fuente="BP-AGG-Pedido", destino="BP-HOT-RiesgoFraude", descripcion="riesgo"),
            AristaGrafo(fuente="BP-EVT-Confirmado", destino="BP-SYS-Stripe", descripcion="notifica"),
            AristaGrafo(fuente="BP-POL-Reactiva", destino="ORPHAN-NODE", descripcion="dispara"),
        ],
    )
    agg = GrafoPorAgregado(
        nombre_agregado="Pedido",
        entidad_raiz="Pedido",
        descripcion="d",
        nodos=[
            _node("AGG-AGG-Pedido", "Agregado", nivel="process_level"),
            _node("AGG-CMD-Confirmar", "Comando", nivel="process_level"),
            _node("AGG-EVT-Confirmado", "Evento", nivel="process_level"),
        ],
        aristas=[AristaGrafo(fuente="AGG-CMD-Confirmar", destino="AGG-AGG-Pedido", descripcion="dispara")],
    )
    rm = ReadModel(nombre="OrderView", descripcion="vista", proyecta=["BP-EVT-Confirmado"])
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=[agg],
        read_models=[rm],
        politicas_inter_agregados=[
            AristaGrafo(fuente="BP-EVT-Confirmado", destino="AGG-CMD-Confirmar", descripcion="reactiva"),
        ],
    )


# ── Element type mapping ────────────────────────────────────────────────


def test_element_type_to_rf_type_covers_all_known_element_types():
    expected = {
        "Actor",
        "Sistema Externo",
        "Comando",
        "Agregado",
        "Entidad Raíz",
        "Evento",
        "Política",
        "Política de UI",
        "Regla de Negocio",
        "Read Model",
        "Vista",
        "Proyección",
        "Hotspot",
    }
    assert expected.issubset(set(rfp.ELEMENT_TYPE_TO_RF_TYPE.keys()))


# ── Selectors ───────────────────────────────────────────────────────────


def test_select_big_picture_returns_bp_nodes_and_edges():
    a = _analysis()
    nodes, edges = rfp.select_big_picture(a)
    assert {n.id for n in nodes} == {n.id for n in a.big_picture.nodos}
    assert len(edges) == len(a.big_picture.aristas)


def test_select_aggregate_returns_that_aggregates_nodes():
    a = _analysis()
    nodes, edges = rfp.select_aggregate(a.agregados[0])
    ids = {n.id for n in nodes}
    assert "AGG-AGG-Pedido" in ids
    assert "AGG-CMD-Confirmar" in ids
    assert len(edges) == 1


def test_select_all_aggregates_includes_inter_aggregate_policies():
    a = _analysis()
    nodes, edges = rfp.select_all_aggregates(a)
    ids = {n.id for n in nodes}
    assert "AGG-AGG-Pedido" in ids
    # Inter-aggregate policies surface even if their endpoints belong to BP.
    assert any(e.descripcion == "reactiva" for e in edges)


def test_select_read_models_emits_synthetic_rm_node_and_projection_edge():
    a = _analysis()
    nodes, edges = rfp.select_read_models(a)
    ids = {n.id for n in nodes}
    assert "rm_OrderView" in ids
    assert "BP-EVT-Confirmado" in ids  # the projected event is pulled in
    assert any(
        e.fuente == "BP-EVT-Confirmado" and e.destino == "rm_OrderView" and e.descripcion == "proyecta" for e in edges
    )


def test_select_event_storming_full_includes_bp_aggregates_and_read_models():
    a = _analysis()
    nodes, edges = rfp.select_event_storming_full(a)
    ids = {n.id for n in nodes}
    assert "BP-ACT-Cliente" in ids
    assert "AGG-AGG-Pedido" in ids
    assert "rm_OrderView" in ids


# ── Serializer ──────────────────────────────────────────────────────────


def test_to_react_flow_maps_node_types_and_strips_orphan_edges():
    a = _analysis()
    nodes, edges = rfp.select_big_picture(a)
    payload = rfp.to_react_flow(nodes, edges)

    # Node type mapping.
    by_id = {n["id"]: n for n in payload["nodes"]}
    assert by_id["BP-ACT-Cliente"]["type"] == "actor"
    assert by_id["BP-CMD-Confirmar"]["type"] == "comando"
    assert by_id["BP-AGG-Pedido"]["type"] == "agregado"
    assert by_id["BP-EVT-Confirmado"]["type"] == "evento"
    assert by_id["BP-POL-Reactiva"]["type"] == "politica"
    assert by_id["BP-HOT-RiesgoFraude"]["type"] == "hotspot"
    assert by_id["BP-SYS-Stripe"]["type"] == "sistema_externo"

    # Every node has data.label + data.subtitle + data.id.
    for n in payload["nodes"]:
        assert "label" in n["data"]
        assert "subtitle" in n["data"]
        assert "id" in n["data"]

    # Orphan edges (destination not in node set) are stripped.
    targets = {e["target"] for e in payload["edges"]}
    assert "ORPHAN-NODE" not in targets


def test_to_react_flow_dedupes_identical_edges():
    a = _analysis()
    extra = AristaGrafo(fuente="BP-ACT-Cliente", destino="BP-CMD-Confirmar", descripcion="dispara")
    a.big_picture.aristas.append(extra)  # exact duplicate
    nodes, edges = rfp.select_big_picture(a)
    payload = rfp.to_react_flow(nodes, edges)
    pairs = [(e["source"], e["target"], e["label"]) for e in payload["edges"]]
    assert pairs.count(("BP-ACT-Cliente", "BP-CMD-Confirmar", "dispara")) == 1


def test_to_react_flow_preserves_state_and_tags_in_data():
    nodes = [
        NodoGrafo(
            id="N1",
            tipo_elemento="Comando",
            nombre="Pagar",
            descripcion="d",
            nivel="big_picture",
            estado_comparativo="nuevo",
            tags_tecnologia=["fastapi", "stripe"],
        )
    ]
    payload = rfp.to_react_flow(nodes, [])
    n = payload["nodes"][0]
    assert n["data"]["state"] == "nuevo"
    assert n["data"]["tags"] == ["fastapi", "stripe"]
