"""Extra coverage for the report builders' pure helpers and the ModelAccessor
draft-sync branch. These exercise code paths the smoke tests don't reach."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from models.domain_analysis import (
    AristaGrafo,
    BigPicture,
    DomainAnalysis,
    NodoGrafo,
)


def _min_analysis(ddd_specs: dict | None = None) -> DomainAnalysis:
    bp = BigPicture(
        descripcion="d",
        nodos=[NodoGrafo(id="BP-CMD-A", tipo_elemento="Comando", nombre="A", descripcion="", nivel="big_picture")],
        aristas=[],
    )
    return DomainAnalysis(
        nombre_proyecto="P",
        version="1.0.0",
        fecha_analisis="2026-05-14",
        big_picture=bp,
        agregados=[],
        read_models=[],
        politicas_inter_agregados=[],
        ddd_specs=ddd_specs or {},
    )


# ── report_pdf pure helpers ──────────────────────────────────────────────────


def test_report_pdf_display_type_known_and_unknown():
    from services.report_pdf import display_type

    assert display_type("Comando")  # mapped value is non-empty
    assert display_type("TipoDesconocido") == "TipoDesconocido"


def test_report_pdf_clean_puml_strips_fences_and_prefix():
    from services.report_pdf import _clean_puml

    out = _clean_puml("```plantuml\nbla\n@startuml\nA->B\n@enduml\n```")
    assert out.startswith("@startuml")
    assert "```" not in out


def test_report_pdf_sanitize_for_helv():
    from services.report_pdf import _sanitize_for_helv

    assert _sanitize_for_helv("") == ""
    # Unicode arrows/dashes get replaced with ASCII-safe equivalents.
    sanitized = _sanitize_for_helv("A → B — C")
    assert "→" not in sanitized


def test_report_pdf_nodes_table_empty_and_populated():
    from services.report_pdf import _nodes_table

    assert "sin nodos" in _nodes_table([])

    node = NodoGrafo(
        id="BP-CMD-X",
        tipo_elemento="Comando",
        nombre="Crear",
        descripcion="hace algo",
        nivel="big_picture",
        estado_comparativo="nuevo",
        tags_tecnologia=["API"],
    )
    html = _nodes_table([node])
    assert "Crear" in html
    assert "API" in html
    assert "nuevo" in html  # state badge rendered for non-"existente"


def test_report_pdf_graphviz_pdf_from_digraph():
    import graphviz
    from services.report_pdf import _graphviz_pdf_from_digraph

    g = graphviz.Digraph()
    g.node("a")
    g.node("b")
    g.edge("a", "b")
    out = _graphviz_pdf_from_digraph(g)
    assert out is None or (isinstance(out, bytes) and out[:4] == b"%PDF")

    # A broken object whose .pipe raises must degrade to None, not crash.
    broken = MagicMock()
    broken.pipe.side_effect = RuntimeError("no dot")
    assert _graphviz_pdf_from_digraph(broken) is None


# ── report_html pure helpers ─────────────────────────────────────────────────


def test_report_html_clean_puml():
    from services.report_html import _clean_puml

    assert _clean_puml("```\n@startuml\nx\n@enduml\n```").startswith("@startuml")


def test_report_html_kroki_puml_svg_success_and_failure():
    from services import report_html

    ok = MagicMock(status_code=200, content=b"<svg>ok</svg>")
    with patch.object(report_html.requests, "get", return_value=ok):
        assert report_html._kroki_puml_svg("@startuml\nA\n@enduml") == "<svg>ok</svg>"

    with patch.object(report_html.requests, "get", side_effect=RuntimeError("boom")):
        assert report_html._kroki_puml_svg("@startuml\nA\n@enduml") is None


def test_report_html_build_with_ddd_specs_runs_puml_path():
    from services import report_html

    analysis = _min_analysis(ddd_specs={"context_map": "@startuml\nA->B\n@enduml"})
    with patch.object(report_html, "_kroki_puml_svg", return_value="<svg>diagram</svg>"):
        html_bytes = report_html.build_analysis_html(analysis)
    assert isinstance(html_bytes, (bytes, bytearray))
    assert b"<svg" in bytes(html_bytes) or b"diagram" in bytes(html_bytes)


# ── ModelAccessor draft-sync branch ──────────────────────────────────────────


def test_model_accessor_set_model_syncs_linked_draft():
    from services.model_accessor import ModelAccessor

    draft_service = MagicMock()
    model = _min_analysis()
    state = {
        "analysis_result": {"analysis": model},
        "current_generation_id": "gen-123",
        "_draft_service": draft_service,
    }
    accessor = ModelAccessor(state)

    new_model = _min_analysis()
    new_model.big_picture.aristas.append(AristaGrafo(fuente="BP-CMD-A", destino="BP-CMD-A", descripcion="self"))
    accessor.set_model(new_model)

    draft_service.update_draft_snapshot.assert_called_once_with("gen-123", new_model)


def test_model_accessor_set_model_survives_draft_failure():
    from services.model_accessor import ModelAccessor

    draft_service = MagicMock()
    draft_service.update_draft_snapshot.side_effect = RuntimeError("disk full")
    model = _min_analysis()
    state = {
        "analysis_result": {"analysis": model},
        "current_generation_id": "gen-1",
        "_draft_service": draft_service,
    }
    accessor = ModelAccessor(state)
    # Must not raise even when the draft update fails.
    accessor.set_model(_min_analysis())
