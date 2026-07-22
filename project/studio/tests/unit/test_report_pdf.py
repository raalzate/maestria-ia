"""Unit tests for the deterministic PDF report builder."""

from __future__ import annotations

from unittest.mock import patch

import pymupdf
from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.report_pdf import _kroki_pdf, build_analysis_pdf


def _make_node(nid: str, tipo: str = "Comando") -> NodoGrafo:
    return NodoGrafo(
        id=nid,
        tipo_elemento=tipo,
        nombre=nid.split("-")[-1],
        descripcion="desc",
        nivel="big_picture",
    )


def _make_analysis(*, with_diagrams: bool = False) -> DomainAnalysis:
    n1 = _make_node("BP-CMD-Open", "Comando")
    n2 = _make_node("BP-AGG-Order", "Agregado")
    n3 = _make_node("BP-EVT-Opened", "Evento")
    bp = BigPicture(
        descripcion="Flujo principal",
        nodos=[n1, n2, n3],
        aristas=[
            AristaGrafo(fuente="BP-CMD-Open", destino="BP-AGG-Order", descripcion="dispara"),
            AristaGrafo(fuente="BP-AGG-Order", destino="BP-EVT-Opened", descripcion="produce"),
        ],
    )
    agg_node = NodoGrafo(
        id="AGG-AGG-Order", tipo_elemento="Agregado", nombre="Order", descripcion="raíz", nivel="process_level"
    )
    agg_evt = NodoGrafo(
        id="AGG-EVT-Opened", tipo_elemento="Evento", nombre="Opened", descripcion="ev", nivel="process_level"
    )
    agg = GrafoPorAgregado(
        nombre_agregado="Order",
        entidad_raiz="Order",
        descripcion="agg desc",
        nodos=[agg_node, agg_evt],
        aristas=[AristaGrafo(fuente="AGG-AGG-Order", destino="AGG-EVT-Opened", descripcion="produce")],
    )
    rm = ReadModel(nombre="OrderSummary", descripcion="vista", proyecta=["BP-EVT-Opened"])
    specs = {"context_map": "@startuml\nA -> B\n@enduml"} if with_diagrams else {}
    return DomainAnalysis(
        nombre_proyecto="Test Project",
        version="1.0.0",
        fecha_analisis="2026-05-13",
        big_picture=bp,
        agregados=[agg],
        read_models=[rm],
        politicas_inter_agregados=[AristaGrafo(fuente="BP-EVT-Opened", destino="BP-CMD-Open", descripcion="reactiva")],
        responsables=["Ada", "Linus"],
        notas="Análisis de prueba",
        ddd_specs=specs,
    )


def _tiny_pdf_bytes() -> bytes:
    """Make a 1-page PDF programmatically so tests don't need a network or graphviz."""
    doc = pymupdf.open()
    p = doc.new_page(width=400, height=300)
    p.insert_text((50, 50), "fake-diagram", fontsize=12)
    out = doc.tobytes()
    doc.close()
    return out


def test_build_analysis_pdf_returns_valid_pdf_bytes():
    """The builder must return bytes that start with the PDF signature."""
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=None),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis())

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000


def test_build_analysis_pdf_with_ai_enhancement_injects_section():
    """When an AI enhancement is provided, the synthesis section appears in the PDF text."""
    from services.report_ai_enhancer import ReportAIEnhancement

    enh = ReportAIEnhancement(
        executive_summary="Síntesis ejecutiva del dominio.",
        key_insights=["Insight uno"],
        risk_areas=["Riesgo uno"],
        recommendations=["Recomendación uno"],
    )
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=None),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis(), ai_enhancement=enh)

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc).lower()
    assert "síntesis ejecutiva" in full_text
    assert "insight uno" in full_text
    assert "riesgo uno" in full_text
    assert "recomendación uno" in full_text


def test_diagram_explanation_unicode_arrows_become_ascii_in_pdf():
    """Arrows like '→' and em-dashes get rewritten so they don't render as '?'."""
    from services.report_ai_enhancer import DiagramExplanation, ReportAIEnhancement

    enh = ReportAIEnhancement(
        executive_summary="resumen.",
        diagram_explanations=[
            DiagramExplanation(
                diagram_name="Big Picture",
                explanation="Comando → Agregado — produce evento. Final…",
            ),
        ],
    )
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=_tiny_pdf_bytes()),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis(), ai_enhancement=enh)

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc)
    # Unicode arrows / em-dashes / ellipsis are rewritten before drawing.
    assert "Comando -> Agregado - produce evento. Final..." in full_text
    # No lingering '?' from missing glyphs in the sanitised explanation.
    assert "Comando ?" not in full_text


def test_diagram_explanations_appear_above_each_diagram():
    """AI explanations matching a diagram title are rendered above the diagram page."""
    from services.report_ai_enhancer import DiagramExplanation, ReportAIEnhancement

    enh = ReportAIEnhancement(
        executive_summary="resumen.",
        diagram_explanations=[
            DiagramExplanation(diagram_name="Big Picture", explanation="Aquí explico el Big Picture del dominio."),
        ],
    )
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=_tiny_pdf_bytes()),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis(), ai_enhancement=enh)

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc).lower()
    assert "aquí explico el big picture del dominio" in full_text


def test_build_analysis_pdf_appends_vector_pages_for_diagrams():
    """Mermaid (Kroki) and Graphviz vector PDF pages are inserted at the end of the document."""
    fake = _tiny_pdf_bytes()
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=fake),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis())

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc).lower()
    assert "anexo a - diagramas del modelo" in full_text
    assert "event storming - mapa completo" in full_text
    assert "big picture" in full_text
    assert "process level - todos los agregados" in full_text
    # The fake diagram payload should appear because show_pdf_page embeds it.
    assert "fake-diagram" in full_text


def test_build_analysis_pdf_appends_plantuml_vector_pages():
    """Kroki PDF pages are appended under the PlantUML annex."""
    fake = _tiny_pdf_bytes()
    with (
        patch("services.report_pdf._kroki_pdf", return_value=fake),
        patch("services.report_pdf._graphviz_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=None),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis(with_diagrams=True))

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc).lower()
    assert "anexo b - ddd specs" in full_text
    assert "context map" in full_text


def test_build_analysis_pdf_survives_diagram_failures():
    """If neither graphviz nor Kroki return a PDF, placeholder pages keep the build alive."""
    with (
        patch("services.report_pdf._kroki_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf", return_value=None),
        patch("services.report_pdf._graphviz_pdf_from_digraph", return_value=None),
    ):
        pdf_bytes = build_analysis_pdf(_make_analysis(with_diagrams=True))

    assert pdf_bytes.startswith(b"%PDF-")
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(p.get_text() for p in doc).lower()
    assert "no se pudo renderizar el grafo" in full_text


@patch("services.report_pdf.requests.get")
def test_kroki_pdf_returns_none_on_non_pdf_response(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"<html>not a pdf</html>"
    assert _kroki_pdf("@startuml\nA->B\n@enduml") is None


@patch("services.report_pdf.requests.get")
def test_kroki_pdf_returns_bytes_when_pdf_signature_present(mock_get):
    payload = b"%PDF-1.4\nfake pdf body"
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = payload
    assert _kroki_pdf("@startuml\nA->B\n@enduml") == payload


def test_build_analysis_pdf_appends_real_diagram_pages():
    """Exercise the diagram-append pipeline: graphviz pages (real dot) + a
    PlantUML page from real PDF bytes, plus TOC and header/footer stamping."""
    from unittest.mock import patch

    with patch("services.report_pdf._kroki_pdf", return_value=_tiny_pdf_bytes()):
        pdf_bytes = build_analysis_pdf(_make_analysis(with_diagrams=True))

    assert pdf_bytes[:4] == b"%PDF"
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    # Text pages + at least one appended diagram page.
    assert doc.page_count >= 2
    doc.close()
