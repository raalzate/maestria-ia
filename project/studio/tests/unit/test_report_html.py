"""Unit tests for the HTML single-file report builder."""

from __future__ import annotations

from unittest.mock import patch

from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.report_html import (
    _placeholder_svg,
    _strip_xml_prolog,
    build_analysis_html,
)

# React Flow ships from this CDN — same as the Streamlit front. We accept it
# as an external runtime dependency (the HTML file itself stays single-file).
_ALLOWED_EXTERNAL_PREFIXES = (
    "https://esm.sh/",
    "http://www.w3.org/",
    "https://www.w3.org/",
)


def _make_node(nid: str, tipo: str = "Comando") -> NodoGrafo:
    return NodoGrafo(
        id=nid,
        tipo_elemento=tipo,
        nombre=nid.split("-")[-1],
        descripcion="desc",
        nivel="big_picture",
    )


def _make_analysis() -> DomainAnalysis:
    bp = BigPicture(
        descripcion="Flujo principal",
        nodos=[
            _make_node("BP-CMD-Open", "Comando"),
            _make_node("BP-AGG-Order", "Agregado"),
            _make_node("BP-EVT-Opened", "Evento"),
        ],
        aristas=[
            AristaGrafo(fuente="BP-CMD-Open", destino="BP-AGG-Order", descripcion="dispara"),
            AristaGrafo(fuente="BP-AGG-Order", destino="BP-EVT-Opened", descripcion="produce"),
        ],
    )
    agg = GrafoPorAgregado(
        nombre_agregado="Order",
        entidad_raiz="Order",
        descripcion="agg desc",
        nodos=[
            NodoGrafo(
                id="AGG-AGG-Order", tipo_elemento="Agregado", nombre="Order", descripcion="raíz", nivel="process_level"
            ),
            NodoGrafo(
                id="AGG-EVT-Opened", tipo_elemento="Evento", nombre="Opened", descripcion="ev", nivel="process_level"
            ),
        ],
        aristas=[AristaGrafo(fuente="AGG-AGG-Order", destino="AGG-EVT-Opened", descripcion="produce")],
    )
    rm = ReadModel(nombre="OrderView", descripcion="vista", proyecta=["BP-EVT-Opened"])
    return DomainAnalysis(
        nombre_proyecto="Test Project",
        version="1.0.0",
        fecha_analisis="2026-05-14",
        big_picture=bp,
        agregados=[agg],
        read_models=[rm],
        politicas_inter_agregados=[],
        responsables=["Ada"],
        notas="Smoke",
    )


def test_strip_xml_prolog_removes_xml_declaration_and_doctype():
    raw = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE svg PUBLIC ".."><svg></svg>'
    out = _strip_xml_prolog(raw)
    assert out == "<svg></svg>"


def test_placeholder_svg_renders_message():
    svg = _placeholder_svg("Error de prueba")
    assert svg.startswith("<svg")
    assert "Error de prueba" in svg


def test_build_analysis_html_produces_valid_single_file_html():
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html_bytes = build_analysis_html(_make_analysis())

    assert isinstance(html_bytes, bytes)
    html = html_bytes.decode("utf-8")
    assert html.startswith("<!DOCTYPE html>")
    assert "<html" in html
    assert "</html>" in html.lower()
    # Allowed external refs: esm.sh (React Flow + deps, same as the front) and
    # w3.org (SVG namespace literal). Any other host would break offline use.
    import re

    urls = re.findall(r'https?://[^\s\'"<>]+', html)
    forbidden = [u for u in urls if not u.startswith(_ALLOWED_EXTERNAL_PREFIXES)]
    assert forbidden == [], f"Found unexpected external refs: {forbidden[:3]}"


def test_build_analysis_html_includes_project_name_and_metrics():
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html = build_analysis_html(_make_analysis()).decode("utf-8")
    assert "Test Project" in html
    assert "Módulos (Agregados)" in html
    assert "Read Models" in html
    # Three tabs.
    assert 'data-tab="resumen"' in html
    assert 'data-tab="diagramas"' in html
    assert 'data-tab="datos"' in html


def test_build_analysis_html_embeds_react_flow_payloads():
    """Event Storming views are embedded as React Flow JSON payloads — same
    engine as the Streamlit front, so visuals match."""
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html = build_analysis_html(_make_analysis()).decode("utf-8")
    # ReactFlow CDN is loaded.
    assert "reactflow@11" in html
    assert "dagre" in html
    # Per-diagram payload containers + JSON scripts.
    assert "data-rf-container" in html
    assert 'data-rf-payload-id="rfp_0"' in html
    assert 'type="application/json"' in html


def test_build_analysis_html_uses_canonical_labels_like_front():
    """HTML report mirrors the React Flow front: canonical Comando/Evento, NOT
    the PDF's Acción/Consecuencia translation."""
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html = build_analysis_html(_make_analysis()).decode("utf-8")
    assert "[Comando]" in html
    assert "[Evento]" in html
    # PDF-only translations should NOT appear in the HTML report.
    assert "[Acción]" not in html
    assert "[Consecuencia]" not in html


def test_build_analysis_html_includes_ai_synthesis_when_provided():
    from services.report_ai_enhancer import ReportAIEnhancement

    enh = ReportAIEnhancement(
        executive_summary="Resumen de prueba.",
        key_insights=["Insight A"],
        risk_areas=["Riesgo A"],
        recommendations=["Recomendación A"],
    )
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html = build_analysis_html(_make_analysis(), ai_enhancement=enh).decode("utf-8")
    assert "Síntesis Ejecutiva (IA)" in html
    assert "Resumen de prueba." in html
    assert "Insight A" in html
    assert "Riesgo A" in html
    assert "Recomendación A" in html


def test_build_analysis_html_omits_ai_section_when_not_provided():
    with patch("services.report_html._kroki_puml_svg", return_value=None):
        html = build_analysis_html(_make_analysis()).decode("utf-8")
    assert "Síntesis Ejecutiva (IA)" not in html
