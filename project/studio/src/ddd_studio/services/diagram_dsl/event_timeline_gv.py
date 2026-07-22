"""Event Timeline rendered with Graphviz `dot` — native vector PDF.

Replaces the Kroki/Mermaid PNG path with a local Graphviz Digraph so the
diagram embeds as true vector inside the report. No external service, no
foreignObject quirks, infinite zoom.
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import DomainAnalysis

_EVT_FILL = "#FFE0B2"
_EVT_STROKE = "#FB8C00"
_EVT_TEXT = "#BF360C"
_POL_FILL = "#E8EAF6"
_POL_STROKE = "#7C4DFF"
_POL_TEXT = "#283593"


def build(analysis: DomainAnalysis) -> graphviz.Digraph:
    """Return a graphviz.Digraph with only Events and Policies, in temporal order."""
    g = graphviz.Digraph(engine="dot", format="pdf")
    g.attr(
        rankdir="TB",  # vertical timeline scales gracefully for long event sequences
        bgcolor="transparent",
        fontname="Helvetica",
        pad="0.6",
        nodesep="0.25",
        ranksep="0.32",
        splines="spline",
    )
    g.attr(
        "node",
        fontname="Helvetica",
        fontsize="12",
        margin="0.22,0.14",
        penwidth="1.4",
    )
    g.attr("edge", fontname="Helvetica", fontsize="9", color="#cfd8dc", arrowsize="0.7", penwidth="1.1")

    bp = analysis.big_picture
    timeline_types = {"Evento", "Política"}
    sequence = [n for n in bp.nodos if n.tipo_elemento in timeline_types]

    if not sequence:
        g.node(
            "empty",
            "Sin eventos en el Big Picture",
            shape="note",
            fillcolor="#FFF8E1",
            style="filled",
            fontcolor="#666666",
        )
        return g

    for n in sequence:
        if n.tipo_elemento == "Evento":
            g.node(
                n.id,
                n.nombre,
                shape="box",
                style="filled,rounded,bold",
                fillcolor=_EVT_FILL,
                color=_EVT_STROKE,
                fontcolor=_EVT_TEXT,
            )
        else:  # Política
            g.node(
                n.id,
                n.nombre,
                shape="parallelogram",
                style="filled",
                fillcolor=_POL_FILL,
                color=_POL_STROKE,
                fontcolor=_POL_TEXT,
            )

    # Sequential edges in appearance order.
    for src, dst in zip(sequence, sequence[1:]):
        g.edge(src.id, dst.id, color="#cfd8dc")

    # Overlay explicit transitions captured by the analyser (preserves model fidelity).
    seen: set[tuple[str, str]] = set()
    ids_in_timeline = {n.id for n in sequence}
    for e in bp.aristas:
        if e.fuente not in ids_in_timeline or e.destino not in ids_in_timeline:
            continue
        key = (e.fuente, e.destino)
        if key in seen:
            continue
        seen.add(key)
        desc = (e.descripcion or "").strip().replace('"', "")
        if len(desc) > 24:
            desc = desc[:24]
        g.edge(
            e.fuente,
            e.destino,
            label=f"  {desc}  " if desc else "",
            style="dashed",
            color="#7C4DFF",
            fontcolor="#5E35B1",
        )
    return g
