"""Unit tests for the Mermaid diagram DSL builders used by the PDF report."""

from __future__ import annotations

from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
)
from services.diagram_dsl import aggregates_overview, bpmn_flow, event_timeline


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
            id="BP-EVT-Pagado", tipo_elemento="Evento", nombre='Pedido "Pagado"', descripcion="", nivel="big_picture"
        ),
        NodoGrafo(
            id="BP-SYS-Stripe", tipo_elemento="Sistema Externo", nombre="Stripe", descripcion="", nivel="big_picture"
        ),
    ]


def _analysis_with(*, aggregates: bool = True) -> DomainAnalysis:
    bp = BigPicture(
        descripcion="demo",
        nodos=_bp_nodes(),
        aristas=[
            AristaGrafo(fuente="BP-ACT-Cliente", destino="BP-CMD-Confirmar", descripcion="dispara"),
            AristaGrafo(fuente="BP-CMD-Confirmar", destino="BP-AGG-Pedido", descripcion="se dirige a"),
            AristaGrafo(fuente="BP-AGG-Pedido", destino="BP-EVT-Confirmado", descripcion="produce"),
            AristaGrafo(fuente="BP-EVT-Confirmado", destino="BP-POL-Reactiva", descripcion="activa"),
            AristaGrafo(fuente="BP-POL-Reactiva", destino="BP-EVT-Pagado", descripcion="dispara"),
            AristaGrafo(fuente="BP-EVT-Pagado", destino="BP-SYS-Stripe", descripcion="notifica"),
        ],
    )
    aggs: list[GrafoPorAgregado] = []
    inter: list[AristaGrafo] = []
    if aggregates:
        a1 = GrafoPorAgregado(
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
            aristas=[],
        )
        a2 = GrafoPorAgregado(
            nombre_agregado="Pago",
            entidad_raiz="Pago",
            nodos=[
                NodoGrafo(
                    id="AGG-AGG-Pago", tipo_elemento="Agregado", nombre="Pago", descripcion="", nivel="process_level"
                ),
                NodoGrafo(
                    id="AGG-CMD-Cobrar", tipo_elemento="Comando", nombre="Cobrar", descripcion="", nivel="process_level"
                ),
                NodoGrafo(
                    id="AGG-EVT-Pagado", tipo_elemento="Evento", nombre="Pagado", descripcion="", nivel="process_level"
                ),
            ],
            aristas=[],
        )
        aggs = [a1, a2]
        inter = [AristaGrafo(fuente="AGG-EVT-Confirmado", destino="AGG-CMD-Cobrar", descripcion="cuando confirmado")]
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=aggs,
        read_models=[],
        politicas_inter_agregados=inter,
    )


# ── Event Timeline ───────────────────────────────────────────────────


def test_event_timeline_emits_only_events_and_policies():
    src = event_timeline.build(_analysis_with())
    assert "flowchart LR" in src
    # Events and policies present.
    assert "Pedido Confirmado" in src
    assert "Reaccionar" in src
    # Commands, actors, aggregates, external systems are excluded.
    assert "Confirmar" not in src.split("Pedido Confirmado")[0]  # cmd doesn't appear before event
    assert "Cliente" not in src
    assert "Stripe" not in src
    assert "Pedido [Agregado" not in src  # aggregate isn't a node here


def test_event_timeline_handles_no_events():
    bp = BigPicture(
        descripcion="x",
        nodos=[NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="", nivel="big_picture")],
        aristas=[],
    )
    a = DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=[],
        read_models=[],
        politicas_inter_agregados=[],
    )
    src = event_timeline.build(a)
    assert "No hay eventos" in src


def test_event_timeline_escapes_quotes_in_names():
    src = event_timeline.build(_analysis_with())
    # The node name `Pedido "Pagado"` must be HTML-escaped, not bare-quoted.
    assert "&quot;Pagado&quot;" in src


# ── BPMN-style swim-lanes ────────────────────────────────────────────


def test_bpmn_flow_creates_one_lane_per_actor_and_aggregate():
    src = bpmn_flow.build(_analysis_with())
    assert "flowchart LR" in src
    # Each Actor, External System and Aggregate becomes a subgraph.
    assert "Actor: Cliente" in src
    assert "Sistema Externo: Stripe" in src
    assert "Agregado: Pedido" in src
    # Subgraph fences are present.
    assert "subgraph" in src
    assert src.count("end") >= 3


def test_bpmn_flow_groups_policies_in_a_dedicated_lane():
    src = bpmn_flow.build(_analysis_with())
    assert "Políticas" in src


def test_bpmn_flow_preserves_all_big_picture_edges():
    src = bpmn_flow.build(_analysis_with())
    # Edge count assertion: 6 edges in the fixture → 6 arrow lines.
    arrow_lines = [line for line in src.splitlines() if "-->" in line]
    assert len(arrow_lines) == 6


# ── Aggregates Overview ──────────────────────────────────────────────


def test_aggregates_overview_emits_one_subgraph_per_aggregate():
    src = aggregates_overview.build(_analysis_with())
    assert "flowchart LR" in src
    assert "Pedido · raíz: Pedido" in src
    assert "Pago · raíz: Pago" in src
    assert "Comandos:" in src
    assert "Eventos:" in src


def test_aggregates_overview_renders_inter_aggregate_policy_as_dashed_edge():
    src = aggregates_overview.build(_analysis_with())
    # Inter-agg dashed arrow: `... -. <desc> .-> ...`
    assert "-. cuando confirmado .->" in src


def test_aggregates_overview_handles_empty_aggregates():
    src = aggregates_overview.build(_analysis_with(aggregates=False))
    assert "No hay agregados" in src
