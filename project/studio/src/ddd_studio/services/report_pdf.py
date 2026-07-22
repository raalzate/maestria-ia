"""Deterministic PDF report builder for a DomainAnalysis.

Compiles the analysis JSON + PlantUML diagrams (rendered via Kroki) into a
single downloadable PDF. No AI calls — purely a transformation pipeline.

Uses PyMuPDF's Story/DocumentWriter for paginated HTML/CSS layout and
Archive for embedding diagram PNGs.
"""

from __future__ import annotations

import base64
import io
import logging
import zlib
from html import escape

import pymupdf
import requests
from models.domain_analysis import (
    BigPicture,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
    ReadModel,
)
from services.report_ai_enhancer import ReportAIEnhancement

logger = logging.getLogger(__name__)

_KROKI_PDF_URL = "https://kroki.io/plantuml/pdf/{}"
_KROKI_TIMEOUT_SECONDS = 30

# PDF-only display labels: in the report we use business-friendly terms instead
# of the canonical DDD vocabulary. The data model and the interactive UI keep
# saying Comando/Evento; only PDF output substitutes these.
PDF_DISPLAY_TYPE = {
    "Comando": "Acción",
    "Evento": "Consecuencia",
}


def display_type(tipo: str) -> str:
    return PDF_DISPLAY_TYPE.get(tipo, tipo)


def build_analysis_pdf(
    analysis: DomainAnalysis,
    ai_enhancement: ReportAIEnhancement | None = None,
) -> bytes:
    """Build a PDF report for the given DomainAnalysis. Returns the raw bytes.

    When ``ai_enhancement`` is provided, an "Síntesis Ejecutiva" section is
    placed right after the cover/metrics and before the detailed sections.
    """
    # Phase 1 — text-only content rendered via Story (HTML/CSS, paginated).
    html = _render_text_html(analysis, ai_enhancement)
    story = pymupdf.Story(html=html, user_css=_CSS)
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    mediabox = pymupdf.paper_rect("a4")
    where = mediabox + (40, 50, -40, -50)
    more = 1
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev, None)
        writer.end_page()
    writer.close()

    # Phase 2 — open and append vector diagram pages so they stay sharp when zoomed.
    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    text_pages_until = doc.page_count  # last page index of Story-rendered text content
    _append_graphviz_diagram_pages(doc, analysis, ai_enhancement)
    _append_plantuml_diagram_pages(doc, analysis, ai_enhancement)

    # Phase 3 — editorial polish: stamp headers/footers + build TOC.
    _stamp_headers_and_footers(doc, analysis)
    _build_toc(doc, analysis, ai_enhancement, text_pages_until)
    return doc.tobytes()


def _render_text_html(
    analysis: DomainAnalysis,
    ai_enhancement: ReportAIEnhancement | None = None,
) -> str:
    """Build the text-only HTML. Diagrams are appended later as vector pages."""
    parts: list[str] = ["<html><body>"]

    parts.append(_cover_section(analysis))
    parts.append(_summary_metrics_section(analysis))
    if ai_enhancement is not None:
        parts.append(_ai_enhancement_section(ai_enhancement))
    parts.append(_big_picture_section(analysis.big_picture))

    for agg in analysis.agregados:
        parts.append(_aggregate_section(agg))

    if analysis.read_models:
        parts.append(_read_models_section(analysis.read_models))

    parts.append(_meta_section(analysis))

    parts.append("</body></html>")
    return "".join(parts)


def _ai_enhancement_section(ai: ReportAIEnhancement) -> str:
    """Render the AI synthesis (executive summary + insights + risks + recommendations)."""
    paragraphs = "".join(f"<p>{escape(p.strip())}</p>" for p in ai.executive_summary.split("\n\n") if p.strip())
    insights = "".join(f"<li>{escape(item)}</li>" for item in ai.key_insights)
    risks = "".join(f"<li>{escape(item)}</li>" for item in ai.risk_areas)
    recs = "".join(f"<li>{escape(item)}</li>" for item in ai.recommendations)
    return (
        '<section class="ai">'
        "<h2>Síntesis Ejecutiva (IA)</h2>"
        '<p class="ai-disclaimer">Generado automáticamente a partir del análisis. Verificar fidelidad.</p>'
        + paragraphs
        + ("<h3>Insights Clave</h3><ul>" + insights + "</ul>" if insights else "")
        + ("<h3>Riesgos y Hotspots</h3><ul>" + risks + "</ul>" if risks else "")
        + ("<h3>Recomendaciones</h3><ul>" + recs + "</ul>" if recs else "")
        + "</section>"
    )


def _cover_section(a: DomainAnalysis) -> str:
    return (
        '<section class="cover">'
        '<div class="cover-rule-top"></div>'
        '<p class="eyebrow">REPORTE DE ANÁLISIS DE DOMINIO</p>'
        f'<h1 class="cover-title">{escape(a.nombre_proyecto)}</h1>'
        '<p class="cover-subtitle">Event Storming · Domain-Driven Design</p>'
        '<div class="cover-divider"></div>'
        '<div class="cover-meta">'
        f'<p class="cover-meta-row"><span class="cover-meta-label">VERSIÓN</span> <span class="cover-meta-val">{escape(a.version)}</span></p>'
        f'<p class="cover-meta-row"><span class="cover-meta-label">FECHA</span> <span class="cover-meta-val">{escape(a.fecha_analisis)}</span></p>'
        "</div>"
        '</section><div class="page-break"></div>'
    )


def _summary_metrics_section(a: DomainAnalysis) -> str:
    total_nodes_bp = len(a.big_picture.nodos)
    total_aggs = len(a.agregados)
    total_rms = len(a.read_models)
    total_policies = len(a.politicas_inter_agregados)
    return (
        "<section><h2>Resumen del Modelo</h2>"
        '<table class="metrics">'
        "<tr>"
        f'<td><div class="num">{total_aggs}</div><div class="label">Módulos (Agregados)</div></td>'
        f'<td><div class="num">{total_rms}</div><div class="label">Read Models</div></td>'
        f'<td><div class="num">{total_nodes_bp}</div><div class="label">Nodos Big Picture</div></td>'
        f'<td><div class="num">{total_policies}</div><div class="label">Políticas Inter-Agg</div></td>'
        "</tr></table>"
        "</section>"
    )


def _big_picture_section(bp: BigPicture) -> str:
    return f"<section><h2>Big Picture</h2><p>{escape(bp.descripcion)}</p>" + _nodes_table(bp.nodos) + "</section>"


def _aggregate_section(agg: GrafoPorAgregado) -> str:
    desc = escape(agg.descripcion) if agg.descripcion else ""
    return (
        f"<section><h2>Agregado: {escape(agg.nombre_agregado)}</h2>"
        f"<p><strong>Entidad Raíz:</strong> {escape(agg.entidad_raiz)}</p>"
        + (f"<p>{desc}</p>" if desc else "")
        + _nodes_table(agg.nodos)
        + "</section>"
    )


def _read_models_section(rms: list[ReadModel]) -> str:
    blocks: list[str] = []
    for rm in rms:
        proyecta = ", ".join(rm.proyecta) or "—"
        policies = ", ".join(rm.ui_policies or []) or "—"
        techs = ", ".join(rm.tecnologias or []) or "—"
        desc = escape(rm.descripcion) if rm.descripcion else ""
        blocks.append(
            '<div class="row">'
            f'<p class="row-title">{escape(rm.nombre)}</p>'
            + (f'<p class="row-desc">{desc}</p>' if desc else "")
            + f'<p class="row-meta"><b>Proyecta:</b> {escape(proyecta)}</p>'
            + f'<p class="row-meta"><b>UI Policies:</b> {escape(policies)}</p>'
            + f'<p class="row-meta"><b>Tecnologías:</b> {escape(techs)}</p>'
            + "</div>"
        )
    return "<section><h2>Read Models</h2>" + "".join(blocks) + "</section>"


def _stamp_headers_and_footers(doc: pymupdf.Document, analysis: DomainAnalysis) -> None:
    """Add running headers (project name + section eyebrow) and footers (page X / Y)."""
    project_name = analysis.nombre_proyecto.strip()
    total = doc.page_count
    # Page 0 is the cover — keep it pristine.
    for idx in range(1, total):
        page = doc.load_page(idx)
        pw = page.rect.width
        ph = page.rect.height

        # Top eyebrow rule (thin grey line).
        page.draw_line(
            (40, 28),
            (pw - 40, 28),
            color=(0.86, 0.88, 0.92),
            width=0.4,
        )
        page.insert_text(
            (40, 22),
            project_name,
            fontsize=8,
            fontname="helv",
            color=(0.42, 0.46, 0.54),
        )

        page_label = f"{idx + 1} / {total}"
        text_w = pymupdf.get_text_length(page_label, fontname="helv", fontsize=8)
        page.insert_text(
            (pw - 40 - text_w, 22),
            page_label,
            fontsize=8,
            fontname="helv",
            color=(0.42, 0.46, 0.54),
        )

        # Footer rule + brand tag.
        page.draw_line(
            (40, ph - 28),
            (pw - 40, ph - 28),
            color=(0.92, 0.93, 0.96),
            width=0.3,
        )
        page.insert_text(
            (40, ph - 14),
            "DDD Studio · Reporte de Análisis de Dominio",
            fontsize=7,
            fontname="heit",
            color=(0.55, 0.58, 0.64),
        )


def _build_toc(
    doc: pymupdf.Document,
    analysis: DomainAnalysis,
    ai: ReportAIEnhancement | None,
    text_pages_until: int,
) -> None:
    """Build the document outline (visible in the PDF reader sidebar)."""
    toc: list[list] = []

    def find_first(query: str, start: int = 0, end: int | None = None) -> int | None:
        end = end if end is not None else doc.page_count
        for p in range(start, end):
            if doc.load_page(p).search_for(query, quads=False):
                return p + 1
        return None

    sections: list[tuple[str, str]] = [("Resumen del Modelo", "Resumen del Modelo")]
    if ai is not None:
        sections.append(("Síntesis Ejecutiva (IA)", "Síntesis Ejecutiva"))
    sections.append(("Big Picture", "Big Picture"))
    for agg in analysis.agregados:
        sections.append((f"Agregado: {agg.nombre_agregado}", f"Agregado: {agg.nombre_agregado}"))
    if analysis.read_models:
        sections.append(("Read Models", "Read Models"))
    sections.append(("Metadatos", "Metadatos"))

    for title, needle in sections:
        page = find_first(needle, start=0, end=text_pages_until)
        if page:
            toc.append([1, title, page])

    # Annex A: first diagram page (after text content).
    annex_a_page = find_first("Anexo A", start=text_pages_until)
    if annex_a_page:
        toc.append([1, "Anexo A - Diagramas del Modelo", annex_a_page])
    # Annex B: first PlantUML page.
    annex_b_page = find_first("Anexo B", start=text_pages_until)
    if annex_b_page:
        toc.append([1, "Anexo B - DDD Specs (PlantUML)", annex_b_page])

    if toc:
        try:
            doc.set_toc(toc)
        except Exception as e:
            logger.warning("Could not set TOC: %s", e)


def _append_graphviz_diagram_pages(
    doc: pymupdf.Document,
    a: DomainAnalysis,
    ai: ReportAIEnhancement | None = None,
) -> None:
    """Append vector pages for each Event Storming view.

    All annex diagrams are rendered with local Graphviz (`dot`) so they embed
    as true vectors — infinite zoom, no external service.
    """
    from contextlib import contextmanager

    from ui.visualization import graph as gv

    def _vertical(digraph):
        digraph.attr(rankdir="TB")
        return digraph

    @contextmanager
    def _pdf_labels_active():
        """Temporarily translate Comando/Evento in node headers while the PDF
        builds. Affects ONLY this call — the front uses canonical DDD terms."""
        original = gv._html_label

        def _translated(tipo: str, nombre: str, badge: str = "", **kwargs) -> str:
            return original(display_type(tipo), nombre, badge, **kwargs)

        gv._html_label = _translated
        try:
            yield
        finally:
            gv._html_label = original

    def _build(fn):
        with _pdf_labels_active():
            return fn()

    # Wide overview diagrams stay horizontal (landscape) — they have too many
    # clusters in parallel for TB to be readable. Focused diagrams go vertical.
    diagrams: list[tuple[str, callable]] = [
        ("Event Storming - Mapa Completo", lambda: _build(lambda: gv._build_user_journey(a))),
        ("Big Picture", lambda: _vertical(_build(lambda: gv._build_big_picture(a)))),
        ("Process Level - Todos los Agregados", lambda: _build(lambda: gv._build_all_aggregates(a))),
    ]
    for agg in a.agregados:
        diagrams.append(
            (
                f"Process Level - {agg.nombre_agregado}",
                lambda agg=agg: _vertical(_build(lambda: gv._build_aggregate(agg, a))),
            )
        )
    if a.read_models:
        diagrams.append(("Modelos de Lectura", lambda: _vertical(_build(lambda: gv._build_read_models(a)))))

    if not diagrams:
        return
    for idx, (title, producer) in enumerate(diagrams):
        annex_label = "Anexo A - Diagramas del Modelo" if idx == 0 else None
        explanation = ai.explanation_for(title) if ai else None
        try:
            digraph = producer()
        except Exception as e:
            logger.warning("Diagram producer failed (%s): %s", title, e)
            _add_placeholder_page(doc, title, "No se pudo construir el diagrama.", annex_label, explanation)
            continue
        pdf_bytes = _graphviz_pdf_from_digraph(digraph)
        if pdf_bytes is None:
            _add_placeholder_page(doc, title, "No se pudo renderizar el grafo.", annex_label, explanation)
            continue
        _append_pdf_as_page(doc, pdf_bytes, title, annex_label, explanation)


def _append_plantuml_diagram_pages(
    doc: pymupdf.Document,
    a: DomainAnalysis,
    ai: ReportAIEnhancement | None = None,
) -> None:
    """Append vector pages for the PlantUML diagrams from ddd_specs."""
    if not a.ddd_specs:
        return
    items: list[tuple[str, str]] = []
    for key, title in (
        ("context_map", "Context Map (Diseño Estratégico)"),
        ("domain_models", "Modelo de Dominio (Diseño Táctico)"),
    ):
        puml = a.ddd_specs.get(key)
        if puml:
            items.append((title, _clean_puml(puml)))
    if not items:
        return

    for idx, (title, puml) in enumerate(items):
        annex_label = "Anexo B - DDD Specs (PlantUML)" if idx == 0 else None
        explanation = ai.explanation_for(title) if ai else None
        pdf_bytes = _kroki_pdf(puml)
        if pdf_bytes is None:
            _add_placeholder_page(doc, title, "Kroki no devolvió un PDF para este diagrama.", annex_label, explanation)
            continue
        _append_pdf_as_page(doc, pdf_bytes, title, annex_label, explanation)


def _graphviz_pdf(factory) -> bytes | None:
    """Render a graphviz.Digraph to vector PDF bytes."""
    try:
        g = factory()
        return g.pipe(format="pdf")
    except Exception as e:
        logger.warning("Graphviz PDF render failed: %s", e)
        return None


def _graphviz_pdf_from_digraph(digraph) -> bytes | None:
    """Same as _graphviz_pdf but takes the already-built Digraph (matches the
    `renderer(payload)` interface used by `_append_graphviz_diagram_pages`)."""
    try:
        return digraph.pipe(format="pdf")
    except Exception as e:
        logger.warning("Graphviz PDF render failed: %s", e)
        return None


def _append_pdf_as_page(
    doc: pymupdf.Document,
    pdf_bytes: bytes,
    title: str,
    annex_label: str | None = None,
    explanation: str | None = None,
) -> None:
    """Insert each page of `pdf_bytes` into `doc` with a heading and centred scaling."""
    try:
        src = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.warning("Could not open diagram PDF (%s): %s", title, e)
        _add_placeholder_page(doc, title, "PDF del diagrama inválido.", annex_label, explanation)
        return

    for page_idx in range(src.page_count):
        src_page = src.load_page(page_idx)
        sw, sh = src_page.rect.width, src_page.rect.height
        landscape = sw > sh
        page_w, page_h = (842.0, 595.0) if landscape else (595.0, 842.0)
        page = doc.new_page(width=page_w, height=page_h)

        y = _draw_diagram_header(
            page,
            title,
            annex_label if page_idx == 0 else None,
            explanation if page_idx == 0 else None,
        )
        if src.page_count > 1:
            page.insert_text(
                (40, y + 14),
                f"Página {page_idx + 1} de {src.page_count}",
                fontsize=8,
                fontname="helv",
                color=(0.5, 0.5, 0.5),
            )
            y += 12

        target = pymupdf.Rect(40, y + 10, page_w - 40, page_h - 40)
        page.show_pdf_page(target, src, page_idx, keep_proportion=True)
    src.close()


def _draw_diagram_header(
    page,
    title: str,
    annex_label: str | None,
    explanation: str | None = None,
) -> float:
    """Render annex label, title, and optional AI explanation. Returns y baseline."""
    y = 50
    if annex_label:
        page.insert_text((40, y), annex_label, fontsize=9, fontname="helv", color=(0.45, 0.45, 0.45))
        y += 16
    page.insert_text((40, y), title, fontsize=14, fontname="hebo", color=(0.04, 0.23, 0.43))
    y += 6
    page.draw_line(
        (40, y),
        (page.rect.width - 40, y),
        color=(0.85, 0.85, 0.85),
        width=0.5,
    )
    y += 8
    if explanation:
        max_h = 110
        text_rect = pymupdf.Rect(40, y, page.rect.width - 40, y + max_h)
        rc = page.insert_textbox(
            text_rect,
            _sanitize_for_helv(explanation),
            fontsize=9,
            fontname="helv",
            color=(0.2, 0.25, 0.35),
            align=0,
        )
        used = max_h if rc < 0 else max(40, max_h - rc)
        y += used + 8
    return y


# ────────────────────────────────────────────────────────────────────────
# Unicode → ASCII sanitizer for PyMuPDF's built-in Helvetica font, which
# lacks glyphs for arrows, em-dashes, smart quotes, ellipsis, bullets…
# Any unsupported codepoint would render as '?'. We rewrite the common
# offenders so AI-written explanations don't get mangled in the PDF.
# ────────────────────────────────────────────────────────────────────────
_ASCII_REPLACEMENTS = {
    "→": "->",
    "⇒": "=>",
    "⟶": "->",
    "➜": "->",
    "➔": "->",
    "►": ">",
    "←": "<-",
    "⇐": "<=",
    "⟵": "<-",
    "↔": "<->",
    "⇔": "<=>",
    "—": "-",
    "–": "-",
    "−": "-",
    "“": '"',
    "”": '"',
    "„": '"',
    "«": '"',
    "»": '"',
    "‘": "'",
    "’": "'",
    "‚": "'",
    "…": "...",
    "•": "*",
    "·": "-",
    "◦": "*",
    "▪": "*",
    "▫": "*",
    "✓": "[v]",
    "✔": "[v]",
    "✗": "[x]",
    "✘": "[x]",
    "©": "(c)",
    "®": "(R)",
    "™": "(TM)",
    " ": " ",  # nbsp
}


def _sanitize_for_helv(text: str) -> str:
    if not text:
        return text
    return text.translate({ord(k): v for k, v in _ASCII_REPLACEMENTS.items()})


def _add_placeholder_page(
    doc: pymupdf.Document,
    title: str,
    message: str,
    annex_label: str | None = None,
    explanation: str | None = None,
) -> None:
    page = doc.new_page(width=595, height=842)
    y = _draw_diagram_header(page, title, annex_label, explanation)
    page.insert_text((40, y + 30), message, fontsize=10, fontname="helv", color=(0.7, 0.3, 0.0))


def _meta_section(a: DomainAnalysis) -> str:
    parts: list[str] = ["<section><h2>Metadatos</h2>"]
    if a.responsables:
        parts.append("<p><strong>Responsables:</strong> " + escape(", ".join(a.responsables)) + "</p>")
    if a.notas:
        parts.append(f"<p><strong>Notas:</strong> {escape(a.notas)}</p>")
    parts.append("</section>")
    return "".join(parts)


def _nodes_table(nodes: list[NodoGrafo]) -> str:
    if not nodes:
        return '<p class="empty">— sin nodos —</p>'
    blocks: list[str] = []
    for n in nodes:
        tags = ", ".join(n.tags_tecnologia) if n.tags_tecnologia else "—"
        state_badge = (
            f' <span class="state state-{n.estado_comparativo}">{escape(n.estado_comparativo)}</span>'
            if n.estado_comparativo and n.estado_comparativo != "existente"
            else ""
        )
        blocks.append(
            '<div class="row">'
            f'<p class="row-title">{escape(n.nombre)} '
            f'<span class="row-type">[{escape(display_type(n.tipo_elemento))}]</span>{state_badge}</p>'
            f'<p class="row-id">{escape(n.id)}</p>'
            f'<p class="row-desc">{escape(n.descripcion)}</p>'
            + (f'<p class="row-meta"><b>Tags:</b> {escape(tags)}</p>' if tags != "—" else "")
            + "</div>"
        )
    return "".join(blocks)


def _clean_puml(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if not text.startswith("@startuml") and "@startuml" in text:
        text = text[text.index("@startuml") :]
    return text.strip()


def _kroki_pdf(puml_text: str) -> bytes | None:
    """Fetch a vector PDF render of a PlantUML diagram from Kroki."""
    try:
        compressed = zlib.compress(puml_text.encode("utf-8"), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        url = _KROKI_PDF_URL.format(encoded)
        resp = requests.get(url, timeout=_KROKI_TIMEOUT_SECONDS)
        if resp.status_code == 200 and resp.content.startswith(b"%PDF-"):
            return resp.content
        logger.warning("Kroki PDF endpoint returned status=%s", resp.status_code)
    except Exception as e:
        logger.warning("Kroki PDF render failed: %s", e)
    return None


_CSS = """
/* Palette: primary navy + warm accent + tight neutrals. */
body { font-family: sans-serif; color: #1a1f29; line-height: 1.5;
       font-size: 10pt; letter-spacing: 0.01em; }
h1 { font-size: 28pt; margin: 0 0 4pt 0; color: #0a2540;
     letter-spacing: -0.02em; font-weight: bold; }
h2 { font-size: 17pt; margin: 22pt 0 8pt 0; color: #0a2540;
     letter-spacing: -0.01em; font-weight: bold;
     border-bottom: 0.6pt solid #d2dae6; padding-bottom: 4pt; }
h3 { font-size: 11.5pt; margin: 14pt 0 5pt 0; color: #2c3e57;
     letter-spacing: 0.02em; font-weight: bold; }
p  { font-size: 10pt; margin: 4pt 0; color: #2a2f3a; }
strong { color: #0a2540; }
section { margin-bottom: 14pt; }

/* === Cover === */
.cover { padding-top: 110pt; }
.cover-rule-top { background: #0a2540; height: 5pt; width: 64pt;
                  margin: 0 0 28pt 0; }
.eyebrow { font-size: 9pt; color: #6b7280; letter-spacing: 0.22em;
           margin: 0 0 14pt 0; }
.cover-title { font-size: 40pt; line-height: 1.05; color: #0a2540;
               margin: 0 0 14pt 0; letter-spacing: -0.03em; }
.cover-subtitle { font-size: 13pt; color: #4b5563; margin: 0 0 64pt 0;
                  font-style: italic; }
.cover-divider { background: #0a2540; height: 0.8pt; width: 100%;
                 margin: 18pt 0 26pt 0; }
.cover-meta { font-size: 11pt; }
.cover-meta-row { margin: 6pt 0; }
.cover-meta-label { font-size: 8pt; letter-spacing: 0.2em; color: #6b7280;
                    margin-right: 8pt; }
.cover-meta-val { color: #0a2540; font-weight: bold; }
.page-break { page-break-before: always; }

/* === Metrics === */
.metrics { width: 100%; border-collapse: collapse; margin: 4pt 0 12pt 0;
           page-break-inside: avoid; }
.metrics td { width: 25%; border: 0.6pt solid #d2dae6; padding: 12pt 4pt;
              text-align: center; background: #fafbfd; }
.metrics .num { font-size: 22pt; font-weight: bold; color: #0a2540;
                letter-spacing: -0.02em; }
.metrics .label { font-size: 7.5pt; color: #6b7280;
                  letter-spacing: 0.12em; margin-top: 4pt; }

/* === Element cards === */
.row { border-left: 2.5pt solid #d2dae6; padding: 4pt 0 4pt 10pt;
       margin: 6pt 0; }
.row.edge { border-left-color: #94a3b8; }
.row-title { font-size: 11pt; font-weight: bold; margin: 0 0 1pt 0;
             color: #0a2540; letter-spacing: -0.01em; }
.row-id { font-size: 8pt; color: #6b7280; margin: 0 0 3pt 0;
          font-family: monospace; letter-spacing: 0; }
.row-desc { font-size: 9.5pt; color: #2a2f3a; margin: 2pt 0; }
.row-meta { font-size: 8.5pt; color: #4b5563; margin: 2pt 0; }
.row-type { font-size: 8pt; color: #6b7280; font-weight: normal; }
.state { font-size: 7pt; padding: 1pt 5pt; border-radius: 2pt;
         background: #eceff4; color: #4b5563; letter-spacing: 0.08em; }
.state-nuevo      { background: #d1fae5; color: #065f46; }
.state-modificado { background: #fef3c7; color: #92400e; }
.state-eliminado  { background: #fee2e2; color: #991b1b; }
.empty { font-size: 9pt; color: #6b7280; font-style: italic; }
.warn  { font-size: 9pt; color: #b45309; font-style: italic; }
img { display: block; margin: 6pt auto; }

/* === AI synthesis callout === */
.ai { background: #f3f6fb; padding: 14pt 18pt 12pt 18pt;
      margin: 10pt 0 14pt 0; border-left: 4pt solid #d97757; }
.ai h2 { color: #0a2540; border-bottom: none; margin: 0 0 4pt 0; }
.ai .ai-disclaimer { font-size: 8pt; color: #6b7280; font-style: italic;
                     margin: 0 0 10pt 0; letter-spacing: 0.04em; }
.ai p { color: #1a1f29; }
.ai h3 { font-size: 11pt; color: #0a2540;
         margin: 12pt 0 4pt 0; letter-spacing: 0.04em; }
.ai ul { font-size: 9.5pt; margin: 2pt 0 6pt 14pt; padding: 0;
         color: #2a2f3a; }
.ai li { margin: 3pt 0; }
"""
