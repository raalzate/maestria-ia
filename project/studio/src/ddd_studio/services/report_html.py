"""HTML single-file report — interactive, CDN-friendly, mirrors the front.

Each Event Storming view is rendered with the same React Flow + dagre stack
the Streamlit front uses, so the report looks identical to the interactive UI.
PlantUML diagrams (Context Map / Domain Model) stay as inline SVG fetched
from Kroki — they are not React Flow data.

External runtime fetches: React Flow + React + dagre come from esm.sh (same
as the front). The HTML file itself is single-file, downloadable, and works
as long as the browser has internet access on first load. Cached afterwards.
"""

from __future__ import annotations

import base64
import json
import logging
import zlib
from html import escape

import requests
from models.domain_analysis import DomainAnalysis
from services.diagram_dsl import react_flow_payload as rfp
from services.report_ai_enhancer import ReportAIEnhancement

logger = logging.getLogger(__name__)

_KROKI_SVG_URL = "https://kroki.io/plantuml/svg/{}"
_KROKI_TIMEOUT = 30


def build_analysis_html(
    analysis: DomainAnalysis,
    ai_enhancement: ReportAIEnhancement | None = None,
) -> bytes:
    """Return a portable single-file HTML report as UTF-8 bytes."""
    rf_diagrams = _build_rf_diagrams(analysis)
    puml_diagrams = _build_puml_diagrams(analysis)
    html = _render(analysis, ai_enhancement, rf_diagrams, puml_diagrams)
    return html.encode("utf-8")


# ── React Flow payloads (same as the Streamlit front) ───────────────────


def _build_rf_diagrams(a: DomainAnalysis) -> list[dict]:
    """Per-view React Flow payloads. Each dict carries the title, the JSON
    payload, and the preferred layout direction.
    """
    views: list[dict] = []

    nodes, edges = rfp.select_event_storming_full(a)
    if nodes:
        views.append(
            {
                "title": "Event Storming - Mapa Completo",
                "payload": rfp.to_react_flow(nodes, edges),
                "direction": "LR",
            }
        )

    nodes, edges = rfp.select_big_picture(a)
    if nodes:
        views.append(
            {
                "title": "Big Picture",
                "payload": rfp.to_react_flow(nodes, edges),
                "direction": "TB",
            }
        )

    nodes, edges = rfp.select_all_aggregates(a)
    if nodes:
        views.append(
            {
                "title": "Process Level - Todos los Agregados",
                "payload": rfp.to_react_flow(nodes, edges),
                "direction": "LR",
            }
        )

    for agg in a.agregados:
        nodes, edges = rfp.select_aggregate(agg)
        if not nodes:
            continue
        views.append(
            {
                "title": f"Process Level - {agg.nombre_agregado}",
                "payload": rfp.to_react_flow(nodes, edges),
                "direction": "TB",
            }
        )

    nodes, edges = rfp.select_read_models(a)
    if nodes:
        views.append(
            {
                "title": "Modelos de Lectura",
                "payload": rfp.to_react_flow(nodes, edges),
                "direction": "TB",
            }
        )
    return views


# ── PlantUML diagrams via Kroki (inline SVG) ────────────────────────────


def _build_puml_diagrams(a: DomainAnalysis) -> list[dict]:
    """Returns [{title, svg}] for ddd_specs Context Map / Domain Model."""
    if not a.ddd_specs:
        return []
    out: list[dict] = []
    for key, title in (
        ("context_map", "Context Map (Diseño Estratégico)"),
        ("domain_models", "Modelo de Dominio (Diseño Táctico)"),
    ):
        puml = a.ddd_specs.get(key)
        if not puml:
            continue
        svg = _kroki_puml_svg(_clean_puml(puml))
        out.append(
            {
                "title": title,
                "svg": _strip_xml_prolog(svg) if svg else _placeholder_svg("Kroki no devolvió el diagrama."),
            }
        )
    return out


def _strip_xml_prolog(svg: str) -> str:
    s = svg.strip()
    if s.startswith("<?xml"):
        s = s.split("?>", 1)[-1]
    s = s.strip()
    if s.lower().startswith("<!doctype"):
        s = s.split(">", 1)[-1]
    return s.strip()


def _placeholder_svg(message: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 80">'
        f'<text x="14" y="48" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="14" fill="#b84d00">{escape(message)}</text></svg>'
    )


def _kroki_puml_svg(puml: str) -> str | None:
    try:
        compressed = zlib.compress(puml.encode("utf-8"), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
        resp = requests.get(_KROKI_SVG_URL.format(encoded), timeout=_KROKI_TIMEOUT)
        if resp.status_code == 200 and resp.content:
            return resp.content.decode("utf-8", errors="replace")
        logger.warning("Kroki PUML SVG returned status=%s", resp.status_code)
    except Exception as e:
        logger.warning("Kroki PUML SVG fetch failed: %s", e)
    return None


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


# ── Renderer ────────────────────────────────────────────────────────────


def _render(
    a: DomainAnalysis,
    ai: ReportAIEnhancement | None,
    rf_diagrams: list[dict],
    puml_diagrams: list[dict],
) -> str:
    cover = _render_cover(a)
    metrics = _render_metrics(a)
    ai_section = _render_ai(ai) if ai else ""
    bp_section = _render_big_picture(a)
    agg_section = _render_aggregates(a)
    rm_section = _render_read_models(a)
    meta_section = _render_meta(a)
    diagrams_html = _render_diagrams(rf_diagrams, puml_diagrams, ai)
    raw_section = _render_raw(a)

    return _HTML_SHELL.format(
        title=escape(a.nombre_proyecto),
        css=_CSS,
        js=_JS,
        rf_module=_REACT_FLOW_MODULE,
        cover=cover,
        metrics=metrics,
        ai_section=ai_section,
        bp_section=bp_section,
        agg_section=agg_section,
        rm_section=rm_section,
        meta_section=meta_section,
        diagrams_section=diagrams_html,
        raw_section=raw_section,
    )


def _render_cover(a: DomainAnalysis) -> str:
    return f"""<section class="cover">
  <div class="cover-rule"></div>
  <p class="eyebrow">REPORTE DE ANÁLISIS DE DOMINIO</p>
  <h1 class="cover-title">{escape(a.nombre_proyecto)}</h1>
  <p class="cover-subtitle">Event Storming · Domain-Driven Design</p>
  <div class="cover-meta">
    <p><span class="cover-meta-label">VERSIÓN</span> <span class="cover-meta-val">{escape(a.version)}</span></p>
    <p><span class="cover-meta-label">FECHA</span> <span class="cover-meta-val">{escape(a.fecha_analisis)}</span></p>
  </div>
</section>"""


def _render_metrics(a: DomainAnalysis) -> str:
    cards = [
        ("Módulos (Agregados)", len(a.agregados)),
        ("Read Models", len(a.read_models)),
        ("Nodos Big Picture", len(a.big_picture.nodos)),
        ("Políticas Inter-Agg", len(a.politicas_inter_agregados)),
    ]
    cells = "".join(
        f'<div class="metric"><div class="num">{val}</div><div class="label">{escape(label)}</div></div>'
        for label, val in cards
    )
    return f'<section class="metrics"><h2>Resumen del Modelo</h2><div class="metrics-grid">{cells}</div></section>'


def _render_ai(ai: ReportAIEnhancement) -> str:
    paragraphs = "".join(f"<p>{escape(p.strip())}</p>" for p in ai.executive_summary.split("\n\n") if p.strip())
    insights = "".join(f"<li>{escape(t)}</li>" for t in ai.key_insights)
    risks = "".join(f"<li>{escape(t)}</li>" for t in ai.risk_areas)
    recs = "".join(f"<li>{escape(t)}</li>" for t in ai.recommendations)
    blocks = [paragraphs]
    if insights:
        blocks.append(f"<h3>Insights Clave</h3><ul>{insights}</ul>")
    if risks:
        blocks.append(f"<h3>Riesgos y Hotspots</h3><ul>{risks}</ul>")
    if recs:
        blocks.append(f"<h3>Recomendaciones</h3><ul>{recs}</ul>")
    return (
        '<section class="ai">'
        "<h2>Síntesis Ejecutiva (IA)</h2>"
        '<p class="ai-disclaimer">Generado automáticamente a partir del análisis. Verificar fidelidad.</p>'
        + "".join(blocks)
        + "</section>"
    )


def _render_type_filter(nodes, scope: str) -> str:
    """Chip row that filters node `.row` elements by `tipo_elemento` within the
    matching `[data-filter-container]`. Hidden when there's 0/1 distinct type."""
    types: list[str] = []
    for n in nodes:
        if n.tipo_elemento not in types:
            types.append(n.tipo_elemento)
    if len(types) <= 1:
        return ""
    btns = [f'<button class="filter-btn active" data-ftype="__all__" data-filter-scope="{scope}">Todos</button>']
    for t in types:
        btns.append(
            f'<button class="filter-btn" data-ftype="{escape(t)}" data-filter-scope="{scope}">{escape(t)}</button>'
        )
    return f'<div class="filter-bar">{"".join(btns)}</div>'


def _render_big_picture(a: DomainAnalysis) -> str:
    body = f"<p>{escape(a.big_picture.descripcion)}</p>" if a.big_picture.descripcion else ""
    filt = _render_type_filter(a.big_picture.nodos, "bp")
    return (
        f'<section class="block"><h2>Big Picture</h2>{body}{filt}'
        f'<div data-filter-container="bp">{_render_nodes(a.big_picture.nodos)}</div></section>'
    )


def _render_aggregates(a: DomainAnalysis) -> str:
    if not a.agregados:
        return ""
    all_nodes = [n for agg in a.agregados for n in agg.nodos]
    filt = _render_type_filter(all_nodes, "agg")
    parts = [f'<section class="block"><h2>Agregados</h2>{filt}<div data-filter-container="agg">']
    for agg in a.agregados:
        desc = f"<p>{escape(agg.descripcion)}</p>" if agg.descripcion else ""
        parts.append(
            f'<details class="agg-card" open><summary>'
            f'<span class="agg-name">{escape(agg.nombre_agregado)}</span>'
            f'<span class="agg-raiz">raíz: {escape(agg.entidad_raiz)}</span>'
            f"</summary>"
            f"{desc}{_render_nodes(agg.nodos)}"
            f"</details>"
        )
    parts.append("</div></section>")
    return "".join(parts)


def _render_nodes(nodes) -> str:
    if not nodes:
        return '<p class="empty">— sin nodos —</p>'
    rows = []
    for n in nodes:
        tags = ", ".join(n.tags_tecnologia or []) or "—"
        state = n.estado_comparativo or "existente"
        badge = f' <span class="state state-{state}">{escape(state)}</span>' if state != "existente" else ""
        rows.append(
            f'<div class="row" data-tipo="{escape(n.tipo_elemento)}">'
            f'<p class="row-title">{escape(n.nombre)} '
            f'<span class="row-type">[{escape(n.tipo_elemento)}]</span>{badge}</p>'
            f'<p class="row-id">{escape(n.id)}</p>'
            f'<p class="row-desc">{escape(n.descripcion or "")}</p>'
            + (f'<p class="row-meta"><b>Tags:</b> {escape(tags)}</p>' if tags != "—" else "")
            + "</div>"
        )
    return "".join(rows)


def _render_read_models(a: DomainAnalysis) -> str:
    if not a.read_models:
        return ""
    cards = []
    for rm in a.read_models:
        proyecta = ", ".join(rm.proyecta) or "—"
        ui_pol = ", ".join(rm.ui_policies or []) or "—"
        techs = ", ".join(rm.tecnologias or []) or "—"
        desc = f'<p class="row-desc">{escape(rm.descripcion)}</p>' if rm.descripcion else ""
        cards.append(
            '<div class="row">'
            f'<p class="row-title">{escape(rm.nombre)}</p>'
            f"{desc}"
            f'<p class="row-meta"><b>Proyecta:</b> {escape(proyecta)}</p>'
            f'<p class="row-meta"><b>UI Policies:</b> {escape(ui_pol)}</p>'
            f'<p class="row-meta"><b>Tecnologías:</b> {escape(techs)}</p>'
            "</div>"
        )
    return f'<section class="block"><h2>Read Models</h2>{"".join(cards)}</section>'


def _render_meta(a: DomainAnalysis) -> str:
    parts = ['<section class="block"><h2>Metadatos</h2>']
    if a.responsables:
        parts.append(f"<p><strong>Responsables:</strong> {escape(', '.join(a.responsables))}</p>")
    if a.notas:
        parts.append(f"<p><strong>Notas:</strong> {escape(a.notas)}</p>")
    parts.append("</section>")
    return "".join(parts)


def _render_diagrams(
    rf_diagrams: list[dict],
    puml_diagrams: list[dict],
    ai: ReportAIEnhancement | None,
) -> str:
    if not rf_diagrams and not puml_diagrams:
        return '<p class="empty">— sin diagramas —</p>'
    sections = []
    for idx, d in enumerate(rf_diagrams):
        title = d["title"]
        explanation = ai.explanation_for(title) if ai else None
        ai_box = f'<div class="diag-explain"><p>{escape(explanation)}</p></div>' if explanation else ""
        payload_id = f"rfp_{idx}"
        # JSON gets escaped so a stray </script> can't break out.
        payload_text = json.dumps(d["payload"], ensure_ascii=False).replace("</", "<\\/")
        sections.append(
            '<article class="diagram">'
            f"<h3>{escape(title)}</h3>"
            f"{ai_box}"
            f'<div class="rf-container" data-rf-container '
            f'data-rf-payload-id="{payload_id}" '
            f'data-rf-direction="{escape(d.get("direction", "LR"))}"></div>'
            f'<script type="application/json" id="{payload_id}">{payload_text}</script>'
            "</article>"
        )
    for d in puml_diagrams:
        sections.append(
            f'<article class="diagram"><h3>{escape(d["title"])}</h3><div class="puml-stage">{d["svg"]}</div></article>'
        )
    return "".join(sections)


def _render_raw(a: DomainAnalysis) -> str:
    data = a.model_dump()
    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    return (
        '<section class="block">'
        "<h2>JSON del Análisis</h2>"
        '<p class="muted">Estructura completa del modelo. Ctrl+F busca por nombre o ID.</p>'
        f'<pre class="raw-json">{escape(pretty)}</pre>'
        "</section>"
    )


# ── Inline assets ───────────────────────────────────────────────────────


_CSS = """
:root {
  --primary: #0a2540; --muted: #4b5563; --accent: #d97757;
  --bg: #fafbfd; --panel: #ffffff; --border: #d2dae6;
  --ai-bg: #f3f6fb;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg);
             color: #1a1f29; font-family: -apple-system, BlinkMacSystemFont,
             'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.55;
             font-size: 14.5px; }
.container { max-width: 1180px; margin: 0 auto; padding: 28px 36px 64px; }

/* Cover */
.cover { padding: 48px 0 36px; }
.cover-rule { width: 60px; height: 5px; background: var(--primary);
              margin-bottom: 22px; }
.eyebrow { font-size: 11px; letter-spacing: 0.22em; color: var(--muted);
           margin: 0 0 8px; }
.cover-title { font-size: 42px; margin: 0 0 8px; color: var(--primary);
               letter-spacing: -0.025em; line-height: 1.05; }
.cover-subtitle { font-size: 16px; color: var(--muted); margin: 0;
                  font-style: italic; }
.cover-meta { display: flex; gap: 28px; margin-top: 24px; font-size: 13px; }
.cover-meta p { margin: 0; }
.cover-meta-label { font-size: 10px; letter-spacing: 0.2em; color: var(--muted);
                    margin-right: 6px; }
.cover-meta-val { font-weight: 700; color: var(--primary); }

/* Tabs */
.tabs { display: flex; gap: 0; border-bottom: 1.5px solid var(--border);
        margin: 24px 0 20px; position: sticky; top: 0; background: var(--bg);
        z-index: 5; }
.tab-btn { background: transparent; border: 0; padding: 12px 18px;
           font: inherit; font-size: 13px; cursor: pointer; color: var(--muted);
           letter-spacing: 0.04em; border-bottom: 2.5px solid transparent;
           margin-bottom: -1.5px; transition: color 0.15s, border-color 0.15s; }
.tab-btn:hover { color: var(--primary); }
.tab-btn.active { color: var(--primary); border-color: var(--primary);
                  font-weight: 600; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* Sub-tabs (within Resumen) */
.subtabs { display: flex; gap: 6px; margin: 18px 0 14px; flex-wrap: wrap; }
.subtab-btn { background: var(--panel); border: 0.5px solid var(--border);
              padding: 7px 16px; font: inherit; font-size: 12.5px; cursor: pointer;
              color: var(--muted); border-radius: 6px; letter-spacing: 0.02em;
              transition: all 0.15s; }
.subtab-btn:hover { color: var(--primary); border-color: #b9c4d6; }
.subtab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary);
                     font-weight: 600; }
.subtab-panel { display: none; }
.subtab-panel.active { display: block; }

/* Type filter chips */
.filter-bar { display: flex; gap: 6px; flex-wrap: wrap; margin: 4px 0 12px; }
.filter-btn { background: var(--panel); border: 0.5px solid var(--border);
              padding: 3px 10px; font: inherit; font-size: 11px; cursor: pointer;
              color: var(--muted); border-radius: 999px; transition: all 0.15s; }
.filter-btn:hover { color: var(--primary); border-color: #b9c4d6; }
.filter-btn.active { background: var(--primary); color: #fff; border-color: var(--primary);
                     font-weight: 600; }

/* Metric cards */
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr);
                gap: 12px; }
.metric { background: var(--panel); border: 0.5px solid var(--border);
          border-radius: 6px; padding: 16px 8px; text-align: center; }
.metric .num { font-size: 28px; font-weight: 800; color: var(--primary);
               letter-spacing: -0.02em; }
.metric .label { font-size: 10px; color: var(--muted);
                 letter-spacing: 0.14em; margin-top: 4px;
                 text-transform: uppercase; }

/* Sections */
h2 { font-size: 20px; color: var(--primary); margin: 26px 0 12px;
     border-bottom: 0.5px solid var(--border); padding-bottom: 6px;
     letter-spacing: -0.01em; }
h3 { font-size: 14px; color: var(--primary); margin: 14px 0 6px;
     letter-spacing: 0.02em; }
.block p { margin: 6px 0; }
.muted { color: var(--muted); font-size: 12px; }

/* Cards (rows) */
.row { border-left: 3px solid var(--border); padding: 4px 0 4px 12px;
       margin: 8px 0; }
.row-title { font-size: 13px; font-weight: 700; margin: 0 0 1px;
             color: var(--primary); }
.row-type { font-size: 10px; color: var(--muted); font-weight: 400; }
.row-id { font-size: 10px; color: var(--muted); margin: 0 0 3px;
          font-family: ui-monospace, Menlo, monospace; }
.row-desc { font-size: 12.5px; color: #2a2f3a; margin: 2px 0; }
.row-meta { font-size: 11.5px; color: #4b5563; margin: 2px 0; }
.state { font-size: 9px; padding: 1px 6px; border-radius: 2px;
         background: #eceff4; color: #4b5563; letter-spacing: 0.08em;
         text-transform: uppercase; font-weight: 700; }
.state-nuevo      { background: #d1fae5; color: #065f46; }
.state-modificado { background: #fef3c7; color: #92400e; }
.state-eliminado  { background: #fee2e2; color: #991b1b; }

.empty { color: var(--muted); font-style: italic; }

/* Aggregate accordion */
.agg-card { background: var(--panel); border: 0.5px solid var(--border);
            border-radius: 6px; padding: 4px 16px 14px; margin: 10px 0; }
.agg-card summary { cursor: pointer; padding: 12px 0; outline: none;
                    list-style: none; }
.agg-card summary::-webkit-details-marker { display: none; }
.agg-name { font-weight: 700; color: var(--primary); font-size: 15px; }
.agg-raiz { font-size: 11px; color: var(--muted); margin-left: 12px;
            letter-spacing: 0.06em; text-transform: uppercase; }

/* AI block */
.ai { background: var(--ai-bg); padding: 18px 22px; border-radius: 6px;
      border-left: 4px solid var(--accent); margin: 16px 0; }
.ai h2 { border-bottom: none; margin-top: 0; }
.ai .ai-disclaimer { font-size: 11px; color: var(--muted); font-style: italic;
                     margin-bottom: 8px; }
.ai ul { margin: 4px 0 10px 18px; padding: 0; }
.ai li { margin: 4px 0; font-size: 13px; }

/* Diagrams */
.diagram { background: var(--panel); border: 0.5px solid var(--border);
           border-radius: 8px; padding: 14px 16px; margin: 16px 0; }
.diagram h3 { margin-top: 0; }
.diag-explain { background: #fafbfd; border-left: 3px solid var(--accent);
                padding: 8px 12px; margin: 6px 0 12px; font-size: 12.5px;
                color: #2a2f3a; }
.diag-explain p { margin: 0; }
.rf-container { width: 100%; height: 620px; background: var(--bg);
                border: 0.5px solid var(--border); border-radius: 6px;
                position: relative; }
.puml-stage { width: 100%; max-height: 700px; overflow: auto;
              background: var(--bg); border: 0.5px solid var(--border);
              border-radius: 6px; padding: 14px;
              display: flex; align-items: center; justify-content: center; }
.puml-stage svg { max-width: 100%; height: auto; }

/* Sticky-note styling for React Flow custom nodes */
.sticky-rf {
  min-width: 150px; max-width: 230px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1.5px solid;
  font-size: 11px;
  background: var(--panel);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  position: relative;
}
.sticky-rf .subtitle {
  font-size: 8px; letter-spacing: 0.12em; text-transform: uppercase;
  opacity: 0.7; margin-bottom: 3px;
}
.sticky-rf .label { font-weight: 600; line-height: 1.25; margin-bottom: 4px;
                    word-break: break-word; }
.sticky-rf .id { font-family: ui-monospace, Menlo, monospace; font-size: 8.5px;
                 opacity: 0.55; word-break: break-all; }
.sticky-rf .state-badge { position: absolute; top: 4px; right: 6px;
                          font-size: 7.5px; padding: 1px 5px; border-radius: 2px;
                          text-transform: uppercase; letter-spacing: 0.1em;
                          font-weight: 700; }
.sticky-rf { cursor: grab; }
.sticky-rf:active { cursor: grabbing; }
.node-tooltip {
  position: absolute; bottom: 100%; left: 0; margin-bottom: 8px;
  width: 240px; z-index: 1000;
  background: #0a2540; color: #fff; padding: 8px 10px; border-radius: 6px;
  font-size: 10px; line-height: 1.4; box-shadow: 0 4px 14px rgba(0,0,0,0.28);
  pointer-events: none; white-space: normal; text-align: left;
}
.node-tooltip::after { content: ''; position: absolute; top: 100%; left: 16px;
  border: 5px solid transparent; border-top-color: #0a2540; }
.node-tooltip .tt-type { text-transform: uppercase; letter-spacing: 0.08em;
  opacity: 0.65; font-size: 8px; margin-bottom: 2px; }
.node-tooltip .tt-name { font-weight: 700; margin-bottom: 4px; font-size: 11px; }
.node-tooltip .tt-desc { opacity: 0.92; }
.node-tooltip .tt-id { font-family: ui-monospace, Menlo, monospace; font-size: 8px;
  opacity: 0.55; margin-top: 5px; word-break: break-all; }
.node-tooltip .tt-tags { margin-top: 6px; display: flex; flex-wrap: wrap; gap: 3px; }
.node-tooltip .tt-tag { background: rgba(255,255,255,0.16); padding: 1px 5px;
  border-radius: 3px; font-size: 8px; }

/* Raw JSON */
.raw-json { background: #0f172a; color: #cbd5f5; padding: 18px;
            border-radius: 6px; font-size: 11.5px;
            font-family: ui-monospace, Menlo, monospace;
            overflow: auto; max-height: 720px; }

@media print {
  .tabs, .subtabs, .filter-bar { display: none; }
  .tab-panel, .subtab-panel { display: block !important; page-break-after: always; }
  .rf-container, .puml-stage { height: auto; overflow: visible; }
}
"""

# Plain (non-module) JS for tabs; React Flow is loaded as a separate ES module
# block defined in _HTML_SHELL.
_JS = r"""
(function () {
  var btns = document.querySelectorAll('[data-tab]');
  function activate(name) {
    btns.forEach(function (b) { b.classList.toggle('active', b.dataset.tab === name); });
    document.querySelectorAll('[data-panel]').forEach(function (p) {
      p.classList.toggle('active', p.dataset.panel === name);
    });
  }
  btns.forEach(function (b) {
    b.addEventListener('click', function () { activate(b.dataset.tab); });
  });
  if (btns.length) activate(btns[0].dataset.tab);

  // Sub-tabs inside the Resumen panel (Big Picture / Agregados / Read Models).
  var subBtns = document.querySelectorAll('[data-subtab]');
  function activateSub(name) {
    subBtns.forEach(function (b) { b.classList.toggle('active', b.dataset.subtab === name); });
    document.querySelectorAll('[data-subpanel]').forEach(function (p) {
      p.classList.toggle('active', p.dataset.subpanel === name);
    });
  }
  subBtns.forEach(function (b) {
    b.addEventListener('click', function () { activateSub(b.dataset.subtab); });
  });
  if (subBtns.length) activateSub(subBtns[0].dataset.subtab);

  // Type filter chips: hide node rows whose data-tipo doesn't match the choice.
  document.querySelectorAll('.filter-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var scope = btn.dataset.filterScope;
      var container = document.querySelector('[data-filter-container="' + scope + '"]');
      if (!container) return;
      document.querySelectorAll('.filter-btn[data-filter-scope="' + scope + '"]')
        .forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var ft = btn.dataset.ftype;
      container.querySelectorAll('.row[data-tipo]').forEach(function (row) {
        var show = (ft === '__all__' || row.getAttribute('data-tipo') === ft);
        row.style.display = show ? '' : 'none';
      });
    });
  });
})();
"""


# React Flow viewer (multi-instance) — same engine as the Streamlit front.
# Each `[data-rf-container]` div has a sibling `<script type="application/json">`
# carrying the payload; we mount one ReactFlow per container.
_REACT_FLOW_MODULE = r"""
import React from 'https://esm.sh/react@18.3.1';
import { createRoot } from 'https://esm.sh/react-dom@18.3.1/client';
import RF, {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
} from 'https://esm.sh/reactflow@11.11.4?deps=react@18.3.1,react-dom@18.3.1';
import dagre from 'https://esm.sh/dagre@0.8.5';

const TYPE_STYLES = {
  actor:           { bg: '#FFF9C4', fg: '#5D4037', border: '#F9A825' },
  sistema_externo: { bg: '#ECEFF1', fg: '#37474F', border: '#78909C' },
  comando:         { bg: '#BBDEFB', fg: '#0D47A1', border: '#42A5F5' },
  agregado:        { bg: '#FFF3E0', fg: '#E65100', border: '#FB8C00' },
  entidad_raiz:    { bg: '#FFF3E0', fg: '#E65100', border: '#FB8C00' },
  evento:          { bg: '#FFE0B2', fg: '#BF360C', border: '#FB8C00' },
  politica:        { bg: '#E8EAF6', fg: '#283593', border: '#7C4DFF' },
  politica_ui:     { bg: '#F3E5F5', fg: '#6A1B9A', border: '#AB47BC' },
  regla:           { bg: '#EDE7F6', fg: '#4A148C', border: '#9C27B0' },
  read_model:      { bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' },
  vista:           { bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' },
  proyeccion:      { bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' },
  hotspot:         { bg: '#FFEBEE', fg: '#B71C1C', border: '#EF5350' },
  default:         { bg: '#F5F5F5', fg: '#333',   border: '#BDBDBD' },
};

function StickyNode(props) {
  const t = TYPE_STYLES[props.type] || TYPE_STYLES.default;
  const data = props.data || {};
  const state = data.state || 'existente';
  const tags = data.tags || [];
  const [hover, setHover] = React.useState(false);
  const badgeBg = { nuevo: '#c8e6c9', modificado: '#fff3e0', eliminado: '#ffcdd2' }[state];
  const badgeFg = { nuevo: '#1b5e20', modificado: '#e65100', eliminado: '#b71c1c' }[state];
  const badge = state !== 'existente'
    ? React.createElement('span', {
        className: 'state-badge',
        style: { background: badgeBg, color: badgeFg },
      }, state)
    : null;

  const tooltip = hover
    ? React.createElement(
        'div',
        { className: 'node-tooltip' },
        React.createElement('div', { className: 'tt-type' }, data.subtitle || ''),
        React.createElement('div', { className: 'tt-name' }, data.label || ''),
        data.description
          ? React.createElement('div', { className: 'tt-desc' }, data.description)
          : React.createElement('div', { className: 'tt-desc', style: { opacity: 0.5 } }, 'Sin descripción.'),
        tags.length
          ? React.createElement('div', { className: 'tt-tags' },
              tags.map(function (tag, i) {
                return React.createElement('span', { className: 'tt-tag', key: i }, tag);
              }))
          : null,
        React.createElement('div', { className: 'tt-id' }, data.id || ''),
      )
    : null;

  return React.createElement(
    'div',
    {
      className: 'sticky-rf',
      style: { background: t.bg, color: t.fg, borderColor: t.border },
      onMouseEnter: function () { setHover(true); },
      onMouseLeave: function () { setHover(false); },
    },
    React.createElement(Handle, { type: 'target', position: Position.Left,
                                  style: { background: t.border } }),
    badge,
    tooltip,
    React.createElement('div', { className: 'subtitle' }, data.subtitle || ''),
    React.createElement('div', { className: 'label' }, data.label),
    React.createElement('div', { className: 'id' }, data.id),
    React.createElement(Handle, { type: 'source', position: Position.Right,
                                  style: { background: t.border } }),
  );
}

const nodeTypes = {};
['actor','sistema_externo','comando','agregado','entidad_raiz','evento',
 'politica','politica_ui','regla','read_model','vista','proyeccion','hotspot']
 .forEach(function (k) { nodeTypes[k] = StickyNode; });

function layoutWithDagre(nodes, edges, direction) {
  const g = new dagre.graphlib.Graph();
  g.setGraph({ rankdir: direction || 'LR', nodesep: 32, ranksep: 56,
               marginx: 18, marginy: 18 });
  g.setDefaultEdgeLabel(function () { return {}; });
  const W = 200, H = 92;
  nodes.forEach(function (n) { g.setNode(n.id, { width: W, height: H }); });
  edges.forEach(function (e) { g.setEdge(e.source, e.target); });
  dagre.layout(g);
  return nodes.map(function (n) {
    const p = g.node(n.id);
    return Object.assign({}, n, {
      position: { x: p.x - W / 2, y: p.y - H / 2 },
      sourcePosition: (direction === 'TB') ? Position.Bottom : Position.Right,
      targetPosition: (direction === 'TB') ? Position.Top : Position.Left,
    });
  });
}

// Build an ordered list of walkthrough steps: a DFS from each actor (or, if
// there are none, from indegree-0 roots) that grows a flow-tree. Each step
// snapshots the nodes/edges visited so far for the current root, so advancing
// reveals the tree branch by branch; a final sweep covers unreachable nodes.
function buildTourSteps(nodes, edges) {
  const adj = {};
  edges.forEach(function (e) { (adj[e.source] = adj[e.source] || []).push(e); });
  const indeg = {};
  nodes.forEach(function (n) { indeg[n.id] = 0; });
  edges.forEach(function (e) { if (indeg[e.target] != null) indeg[e.target] += 1; });

  const actors = nodes.filter(function (n) { return n.type === 'actor'; }).map(function (n) { return n.id; });
  const roots = actors.length
    ? actors.slice()
    : nodes.filter(function (n) { return (indeg[n.id] || 0) === 0; }).map(function (n) { return n.id; });

  const steps = [];
  const covered = new Set();

  function traverse(rootId) {
    const visN = new Set();
    const visE = new Set();
    const seen = new Set();
    function dfs(nodeId, viaEdge) {
      visN.add(nodeId);
      if (viaEdge) visE.add(viaEdge.id);
      covered.add(nodeId);
      steps.push({
        actorId: rootId,
        focusNode: nodeId,
        focusEdge: viaEdge ? viaEdge.id : null,
        parentNode: viaEdge ? viaEdge.source : null,
        visibleNodes: new Set(visN),
        visibleEdges: new Set(visE),
      });
      if (seen.has(nodeId)) return;
      seen.add(nodeId);
      (adj[nodeId] || []).forEach(function (e) {
        if (!seen.has(e.target)) dfs(e.target, e);
      });
    }
    dfs(rootId, null);
  }

  roots.forEach(function (r) { traverse(r); });
  nodes.forEach(function (n) { if (!covered.has(n.id)) traverse(n.id); });
  return steps;
}

function Diagram(props) {
  const [direction, setDirection] = React.useState(props.direction || 'LR');
  const styledEdges = React.useMemo(function () {
    return props.payload.edges.map(function (e) {
      return Object.assign({}, e, {
        type: 'smoothstep',
        style: { stroke: '#94a3b8', strokeWidth: 1.4 },
        labelStyle: { fontSize: 10, fill: '#475569' },
        labelBgStyle: { fill: 'rgba(255,255,255,0.9)' },
        labelBgPadding: [4, 2],
        markerEnd: { type: 'arrowclosed', color: '#94a3b8' },
      });
    });
  }, [props.payload]);

  // Controlled state so dragging a node persists; edges re-route to follow it.
  const [nodes, setNodes, onNodesChange] = useNodesState(
    layoutWithDagre(props.payload.nodes, styledEdges, props.direction || 'LR')
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(styledEdges);

  React.useEffect(function () {
    setNodes(layoutWithDagre(props.payload.nodes, styledEdges, direction));
  }, [direction]);

  // Clicking an edge focuses it: the edge + its two endpoints stay solid, the
  // rest of the graph dims so you can follow the direction at a glance.
  const [focusEdge, setFocusEdge] = React.useState(null);

  // ── Guided walkthrough (assistant) ──────────────────────────────────────
  const nodeById = React.useMemo(function () {
    const m = {};
    props.payload.nodes.forEach(function (n) { m[n.id] = n; });
    return m;
  }, [props.payload]);
  const steps = React.useMemo(function () {
    return buildTourSteps(props.payload.nodes, props.payload.edges);
  }, [props.payload]);
  const [tour, setTour] = React.useState(false);
  const [stepIdx, setStepIdx] = React.useState(0);
  const rfInstance = React.useRef(null);
  const tourStep = (tour && steps.length) ? steps[Math.min(stepIdx, steps.length - 1)] : null;

  function startTour() { setFocusEdge(null); setStepIdx(0); setTour(true); }
  function exitTour() {
    setTour(false);
    if (rfInstance.current) rfInstance.current.fitView({ padding: 0.2, duration: 400 });
  }
  function nextStep() { setStepIdx(function (i) { return Math.min(i + 1, steps.length - 1); }); }
  function prevStep() { setStepIdx(function (i) { return Math.max(i - 1, 0); }); }

  React.useEffect(function () {
    if (!tourStep || !rfInstance.current) return;
    const ids = tourStep.parentNode
      ? [{ id: tourStep.parentNode }, { id: tourStep.focusNode }]
      : [{ id: tourStep.focusNode }];
    rfInstance.current.fitView({ nodes: ids, duration: 450, padding: 0.5, maxZoom: 1.4 });
  }, [tourStep]);

  const displayNodes = React.useMemo(function () {
    if (tourStep) {
      return nodes.map(function (n) {
        const visible = tourStep.visibleNodes.has(n.id);
        const isFocus = n.id === tourStep.focusNode;
        return Object.assign({}, n, {
          style: Object.assign({}, n.style, {
            opacity: visible ? (isFocus ? 1 : 0.5) : 0.04,
            transition: 'opacity 0.25s',
          }),
        });
      });
    }
    if (!focusEdge) {
      return nodes.map(function (n) {
        return Object.assign({}, n, { style: Object.assign({}, n.style, { opacity: 1, transition: 'opacity 0.2s' }) });
      });
    }
    const fe = edges.find(function (x) { return x.id === focusEdge; });
    const keep = fe ? new Set([fe.source, fe.target]) : new Set();
    return nodes.map(function (n) {
      const on = keep.has(n.id);
      return Object.assign({}, n, {
        style: Object.assign({}, n.style, { opacity: on ? 1 : 0.12, transition: 'opacity 0.2s' }),
      });
    });
  }, [nodes, edges, focusEdge, tourStep]);

  const displayEdges = React.useMemo(function () {
    return edges.map(function (ed) {
      if (tourStep) {
        const visible = tourStep.visibleEdges.has(ed.id);
        const isFocus = ed.id === tourStep.focusEdge;
        const stroke = isFocus ? '#0a2540' : '#94a3b8';
        return Object.assign({}, ed, {
          animated: !!isFocus,
          style: Object.assign({}, ed.style, {
            stroke: stroke,
            strokeWidth: isFocus ? 2.8 : 1.4,
            opacity: visible ? (isFocus ? 1 : 0.45) : 0.03,
            transition: 'opacity 0.25s',
          }),
          labelStyle: Object.assign({}, ed.labelStyle, { opacity: visible ? 1 : 0.03 }),
          labelBgStyle: Object.assign({}, ed.labelBgStyle, { opacity: visible ? 1 : 0.03 }),
          markerEnd: { type: 'arrowclosed', color: stroke },
        });
      }
      const sel = focusEdge && ed.id === focusEdge;
      const on = !focusEdge || sel;
      const stroke = sel ? '#0a2540' : '#94a3b8';
      return Object.assign({}, ed, {
        animated: !!sel,
        style: Object.assign({}, ed.style, {
          stroke: stroke,
          strokeWidth: sel ? 2.6 : 1.4,
          opacity: on ? 1 : 0.07,
          transition: 'opacity 0.2s',
        }),
        labelStyle: Object.assign({}, ed.labelStyle, { opacity: on ? 1 : 0.07 }),
        labelBgStyle: Object.assign({}, ed.labelBgStyle, { opacity: on ? 1 : 0.07 }),
        markerEnd: { type: 'arrowclosed', color: stroke },
      });
    });
  }, [edges, focusEdge, tourStep]);

  const toolbar = React.createElement(
    'div',
    { style: {
        position: 'absolute', top: 10, right: 10, zIndex: 5,
        background: '#fff', border: '1px solid #d2dae6', borderRadius: 6,
        padding: '4px 6px', fontSize: 11 } },
    React.createElement('span', { style: { marginRight: 8, color: '#475569' } }, 'Flujo:'),
    React.createElement('button', {
      onClick: function () { setDirection('LR'); },
      title: 'Las flechas avanzan hacia la derecha',
      style: { marginRight: 4, padding: '3px 10px',
               background: direction === 'LR' ? '#0a2540' : '#fff',
               color: direction === 'LR' ? '#fff' : '#0a2540',
               border: '1px solid #0a2540', borderRadius: 4,
               cursor: 'pointer', fontFamily: 'inherit' },
    }, '→ horizontal'),
    React.createElement('button', {
      onClick: function () { setDirection('TB'); },
      title: 'Las flechas avanzan hacia abajo',
      style: { padding: '3px 10px',
               background: direction === 'TB' ? '#0a2540' : '#fff',
               color: direction === 'TB' ? '#fff' : '#0a2540',
               border: '1px solid #0a2540', borderRadius: 4,
               cursor: 'pointer', fontFamily: 'inherit' },
    }, '↓ vertical'),
    React.createElement('button', {
      onClick: startTour,
      disabled: !steps.length,
      title: 'Recorrido guiado del flujo, paso a paso desde cada actor',
      style: { marginLeft: 10, padding: '3px 10px',
               background: tour ? '#0a2540' : '#fff',
               color: tour ? '#fff' : '#0a2540',
               border: '1px solid #0a2540', borderRadius: 4,
               cursor: steps.length ? 'pointer' : 'not-allowed',
               opacity: steps.length ? 1 : 0.4, fontFamily: 'inherit' },
    }, '▶ Asistente'),
  );

  // Step-by-step assistant panel (only while the walkthrough is active).
  const focusData = tourStep ? ((nodeById[tourStep.focusNode] || {}).data || {}) : {};
  let connText = 'Inicio del flujo';
  if (tourStep && tourStep.focusEdge) {
    const fe = props.payload.edges.find(function (x) { return x.id === tourStep.focusEdge; });
    const parent = nodeById[tourStep.parentNode];
    const parentName = parent ? (parent.data.label || tourStep.parentNode) : tourStep.parentNode;
    const rel = fe && fe.label ? fe.label : 'conecta';
    connText = parentName + '  —[' + rel + ']→  ' + (focusData.label || '');
  }
  const tourPanel = tourStep
    ? React.createElement(
        'div',
        { style: {
            position: 'absolute', top: 10, left: 10, zIndex: 6, width: 290,
            background: '#fff', border: '1px solid #d2dae6', borderRadius: 8,
            padding: '12px 14px', fontSize: 11,
            boxShadow: '0 4px 16px rgba(0,0,0,0.14)', fontFamily: 'inherit' } },
        React.createElement('div',
          { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 } },
          React.createElement('span', { style: { fontSize: 10, fontWeight: 700, letterSpacing: '0.04em', color: '#0a2540' } },
            'ASISTENTE · Paso ' + (stepIdx + 1) + ' / ' + steps.length),
          React.createElement('button', {
            onClick: exitTour, title: 'Salir del asistente',
            style: { border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 14, color: '#64748b', lineHeight: 1 },
          }, '✕'),
        ),
        React.createElement('div', { style: { fontSize: 8, letterSpacing: '0.1em', textTransform: 'uppercase', opacity: 0.6 } },
          focusData.subtitle || ''),
        React.createElement('div', { style: { fontSize: 14, fontWeight: 700, color: '#0a2540', margin: '2px 0 5px' } },
          focusData.label || ''),
        React.createElement('div', { style: { fontSize: 11, color: '#374151', lineHeight: 1.45 } },
          focusData.description || 'Sin descripción.'),
        React.createElement('div',
          { style: { fontSize: 10, color: '#475569', marginTop: 7, borderTop: '1px solid #e2e8f0', paddingTop: 7, lineHeight: 1.4 } },
          '\u{1F517} ' + connText),
        React.createElement('div',
          { style: { display: 'flex', gap: 6, marginTop: 11 } },
          React.createElement('button', {
            onClick: prevStep, disabled: stepIdx <= 0,
            style: { flex: 1, padding: '5px 8px', border: '1px solid #0a2540', borderRadius: 5,
                     background: '#fff', color: '#0a2540', fontFamily: 'inherit',
                     cursor: stepIdx <= 0 ? 'not-allowed' : 'pointer', opacity: stepIdx <= 0 ? 0.4 : 1 },
          }, '◀ Anterior'),
          React.createElement('button', {
            onClick: nextStep, disabled: stepIdx >= steps.length - 1,
            style: { flex: 1, padding: '5px 8px', border: '1px solid #0a2540', borderRadius: 5,
                     background: '#0a2540', color: '#fff', fontFamily: 'inherit',
                     cursor: stepIdx >= steps.length - 1 ? 'not-allowed' : 'pointer',
                     opacity: stepIdx >= steps.length - 1 ? 0.4 : 1 },
          }, 'Siguiente ▶'),
        ),
      )
    : null;

  return React.createElement(
    'div',
    { style: { width: '100%', height: '100%', position: 'relative' } },
    toolbar,
    tourPanel,
    React.createElement(ReactFlow || RF, {
      nodes: displayNodes,
      edges: displayEdges,
      onInit: function (inst) { rfInstance.current = inst; },
      onNodesChange: onNodesChange,
      onEdgesChange: onEdgesChange,
      onEdgeClick: function (evt, edge) { if (!tour) setFocusEdge(edge.id); },
      onPaneClick: function () { if (!tour) setFocusEdge(null); },
      nodeTypes: nodeTypes,
      nodesDraggable: true,
      fitView: true,
      fitViewOptions: { padding: 0.2 },
      minZoom: 0.05,
      maxZoom: 2.5,
      proOptions: { hideAttribution: true },
    },
      React.createElement(Background, { gap: 24, size: 1, color: '#e2e8f0' }),
      React.createElement(Controls, { position: 'bottom-right' }),
      React.createElement(MiniMap, {
        position: 'bottom-left', zoomable: true, pannable: true,
        nodeColor: function (n) { return (TYPE_STYLES[n.type] || TYPE_STYLES.default).border; },
      }),
    ),
  );
}

document.querySelectorAll('[data-rf-container]').forEach(function (container) {
  const id = container.getAttribute('data-rf-payload-id');
  const direction = container.getAttribute('data-rf-direction') || 'LR';
  const script = document.getElementById(id);
  if (!script) return;
  try {
    const payload = JSON.parse(script.textContent);
    createRoot(container).render(
      React.createElement(Diagram, { payload: payload, direction: direction })
    );
  } catch (e) {
    container.innerHTML = '<p style="padding:14px;color:#b84d00">' +
      'No se pudo cargar el diagrama: ' + e.message + '</p>';
  }
});
"""


_HTML_SHELL = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{title} · Reporte de Análisis de Dominio</title>
<link rel="stylesheet" href="https://esm.sh/reactflow@11.11.4/dist/style.css" />
<style>{css}</style>
</head>
<body>
<div class="container">

{cover}

{metrics}

<nav class="tabs">
  <button class="tab-btn" data-tab="resumen">Resumen</button>
  <button class="tab-btn" data-tab="diagramas">Diagramas</button>
  <button class="tab-btn" data-tab="datos">Datos</button>
</nav>

<div class="tab-panel" data-panel="resumen">
  {ai_section}
  <nav class="subtabs">
    <button class="subtab-btn" data-subtab="bp">Big Picture</button>
    <button class="subtab-btn" data-subtab="agg">Agregados</button>
    <button class="subtab-btn" data-subtab="rm">Read Models</button>
  </nav>
  <div class="subtab-panel" data-subpanel="bp">{bp_section}</div>
  <div class="subtab-panel" data-subpanel="agg">{agg_section}</div>
  <div class="subtab-panel" data-subpanel="rm">{rm_section}</div>
  {meta_section}
</div>

<div class="tab-panel" data-panel="diagramas">
  {diagrams_section}
</div>

<div class="tab-panel" data-panel="datos">
  {raw_section}
</div>

</div>
<script>{js}</script>
<script type="module">{rf_module}</script>
</body>
</html>
"""
