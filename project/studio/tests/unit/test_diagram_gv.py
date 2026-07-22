"""Unit tests for the Graphviz diagram builders (``*_gv`` modules).

These ``build()`` functions take a DomainAnalysis / GrafoPorAgregado and return a
``graphviz.Digraph``. Exercising ``build()`` end-to-end covers the lane/pool
assignment, command/event grouping, label and edge-label helpers.
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.diagram_dsl import aggregate_focus_gv, bpmn_flow_gv


def _bp_nodes() -> list[NodoGrafo]:
    return [
        NodoGrafo(id="BP-ACT-Cliente", tipo_elemento="Actor", nombre="Cliente", descripcion="", nivel="big_picture"),
        NodoGrafo(
            id="BP-CMD-Confirmar", tipo_elemento="Comando", nombre="Confirmar", descripcion="", nivel="big_picture"
        ),
        NodoGrafo(id="BP-AGG-Pedido", tipo_elemento="Agregado", nombre="Pedido", descripcion="", nivel="big_picture"),
        NodoGrafo(
            id="BP-EVT-Confirmado",
            tipo_elemento="Evento",
            nombre="Pedido Confirmado",
            descripcion="",
            nivel="big_picture",
        ),
        NodoGrafo(
            id="BP-POL-Reactiva", tipo_elemento="Política", nombre="Reaccionar", descripcion="", nivel="big_picture"
        ),
        NodoGrafo(
            id="BP-EVT-Pagado",
            tipo_elemento="Evento",
            nombre='Pedido "Pagado"',
            descripcion="",
            nivel="big_picture",
        ),
        NodoGrafo(
            id="BP-SYS-Stripe", tipo_elemento="Sistema Externo", nombre="Stripe", descripcion="", nivel="big_picture"
        ),
    ]


def _analysis(*, aggregates: bool = True) -> DomainAnalysis:
    bp = BigPicture(
        descripcion="demo",
        nodos=_bp_nodes(),
        aristas=[
            AristaGrafo(fuente="BP-ACT-Cliente", destino="BP-CMD-Confirmar", descripcion="dispara el proceso"),
            AristaGrafo(fuente="BP-CMD-Confirmar", destino="BP-AGG-Pedido", descripcion="se dirige a"),
            AristaGrafo(fuente="BP-AGG-Pedido", destino="BP-EVT-Confirmado", descripcion="produce un evento"),
            AristaGrafo(fuente="BP-EVT-Confirmado", destino="BP-POL-Reactiva", descripcion="activa la política"),
            AristaGrafo(fuente="BP-POL-Reactiva", destino="BP-EVT-Pagado", descripcion="dispara"),
            AristaGrafo(fuente="BP-EVT-Pagado", destino="BP-SYS-Stripe", descripcion="notifica a un sistema externo"),
        ],
    )
    aggs: list[GrafoPorAgregado] = []
    inter: list[AristaGrafo] = []
    if aggregates:
        aggs = [
            GrafoPorAgregado(
                nombre_agregado="Pedido",
                entidad_raiz="Pedido",
                nodos=[
                    NodoGrafo(
                        id="AGG-AGG-Pedido",
                        tipo_elemento="Agregado",
                        nombre="Pedido",
                        descripcion="",
                        nivel="process_level",
                    ),
                    NodoGrafo(
                        id="AGG-CMD-Confirmar",
                        tipo_elemento="Comando",
                        nombre="Confirmar",
                        descripcion="",
                        nivel="process_level",
                    ),
                    NodoGrafo(
                        id="AGG-EVT-Confirmado",
                        tipo_elemento="Evento",
                        nombre="Confirmado",
                        descripcion="",
                        nivel="process_level",
                    ),
                ],
                aristas=[
                    AristaGrafo(fuente="AGG-CMD-Confirmar", destino="AGG-AGG-Pedido", descripcion="se dirige a"),
                    AristaGrafo(fuente="AGG-AGG-Pedido", destino="AGG-EVT-Confirmado", descripcion="produce"),
                ],
            )
        ]
        inter = [AristaGrafo(fuente="AGG-EVT-Confirmado", destino="AGG-CMD-Confirmar", descripcion="cuando confirmado")]
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=aggs,
        read_models=[ReadModel(nombre="Resumen de Pedido", descripcion="vista", proyecta=["BP-EVT-Confirmado"])],
        politicas_inter_agregados=inter,
    )


# ── bpmn_flow_gv ─────────────────────────────────────────────────────────────


def test_bpmn_flow_gv_build_returns_digraph_with_flow():
    g = bpmn_flow_gv.build(_analysis())

    assert isinstance(g, graphviz.Digraph)
    src = g.source
    assert isinstance(src, str) and src.strip()
    # Lane titles come from actor / aggregate / external-system names.
    assert "Cliente" in src
    assert "Pedido" in src
    assert "Stripe" in src


def test_bpmn_flow_gv_handles_no_aggregates():
    g = bpmn_flow_gv.build(_analysis(aggregates=False))

    assert isinstance(g, graphviz.Digraph)
    assert g.source.strip()


def test_bpmn_flow_gv_handles_empty_big_picture():
    empty = DomainAnalysis(
        nombre_proyecto="empty",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=BigPicture(descripcion="", nodos=[], aristas=[]),
        agregados=[],
        read_models=[],
        politicas_inter_agregados=[],
    )
    g = bpmn_flow_gv.build(empty)
    assert isinstance(g, graphviz.Digraph)


# ── aggregate_focus_gv ───────────────────────────────────────────────────────


def test_aggregate_focus_gv_build_renders_aggregate():
    analysis = _analysis()
    agg = analysis.agregados[0]

    g = aggregate_focus_gv.build(agg, analysis)

    assert isinstance(g, graphviz.Digraph)
    src = g.source
    assert src.strip()
    assert "Confirmar" in src or "Confirmado" in src


def test_aggregate_focus_gv_handles_minimal_aggregate():
    analysis = _analysis(aggregates=False)
    minimal = GrafoPorAgregado(
        nombre_agregado="Solo",
        entidad_raiz="Solo",
        nodos=[
            NodoGrafo(
                id="AGG-AGG-Solo", tipo_elemento="Agregado", nombre="Solo", descripcion="", nivel="process_level"
            ),
        ],
        aristas=[],
    )
    g = aggregate_focus_gv.build(minimal, analysis)
    assert isinstance(g, graphviz.Digraph)
    assert g.source.strip()
