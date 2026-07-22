"""Unit tests for the AI enhancement helper."""

from __future__ import annotations

from models.domain_analysis import BigPicture, DomainAnalysis, NodoGrafo
from services.report_ai_enhancer import (
    DiagramExplanation,
    ReportAIEnhancement,
    generate_enhancement,
    list_diagram_titles,
)


class _FakeInference:
    """Captures the prompt and returns a fixed ReportAIEnhancement."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, type]] = []

    def invoke(self, prompt, schema):
        self.calls.append((prompt, schema))
        return ReportAIEnhancement(
            executive_summary="Resumen.\n\nMás contexto.",
            key_insights=["a", "b"],
            risk_areas=["r1"],
            recommendations=["rec1", "rec2"],
        )

    def invoke_text(self, prompt):  # pragma: no cover — unused here
        return ""


def _trivial_analysis() -> DomainAnalysis:
    bp = BigPicture(
        descripcion="x",
        nodos=[NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="d", nivel="big_picture")],
        aristas=[],
    )
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=[],
        read_models=[],
        politicas_inter_agregados=[],
    )


def test_generate_enhancement_uses_inference_port_and_returns_model():
    fake = _FakeInference()
    result = generate_enhancement(_trivial_analysis(), fake)

    assert isinstance(result, ReportAIEnhancement)
    assert result.executive_summary.startswith("Resumen")
    assert result.key_insights == ["a", "b"]
    assert len(fake.calls) == 1

    prompt, schema = fake.calls[0]
    assert schema is ReportAIEnhancement
    # Prompt must embed the analysis JSON so the model has the source of truth.
    assert "DOMAIN ANALYSIS JSON" in prompt
    assert "nombre_proyecto" in prompt
    # Prompt must list the diagram titles so the AI can produce per-diagram explanations.
    assert "DIAGRAMS IN THE REPORT" in prompt
    assert "Event Storming - Mapa Completo" in prompt
    assert "Big Picture" in prompt
    assert "Process Level - Todos los Agregados" in prompt


def test_list_diagram_titles_includes_per_aggregate_and_specs():
    from models.domain_analysis import GrafoPorAgregado

    bp = BigPicture(
        descripcion="x",
        nodos=[NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="d", nivel="big_picture")],
        aristas=[],
    )
    agg = GrafoPorAgregado(
        nombre_agregado="Order",
        entidad_raiz="Order",
        nodos=[
            NodoGrafo(
                id="AGG-AGG-Order", tipo_elemento="Agregado", nombre="Order", descripcion="d", nivel="process_level"
            )
        ],
        aristas=[],
    )
    a = DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=[agg],
        read_models=[],
        ddd_specs={"context_map": "@startuml\nA->B\n@enduml"},
    )

    titles = list_diagram_titles(a)
    assert "Process Level - Order" in titles
    assert "Context Map (Diseño Estratégico)" in titles
    # No read_models in this fixture, so the read-model diagram must NOT appear.
    assert "Modelos de Lectura" not in titles


def test_explanation_for_is_case_insensitive_lookup():
    enh = ReportAIEnhancement(
        executive_summary="x",
        diagram_explanations=[
            DiagramExplanation(diagram_name="Big Picture", explanation="Explica el flujo."),
        ],
    )
    assert enh.explanation_for("Big Picture") == "Explica el flujo."
    assert enh.explanation_for("  big picture  ") == "Explica el flujo."
    assert enh.explanation_for("Unknown") is None
