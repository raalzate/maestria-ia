"""Layered flow diagram for the Big Picture.

Replaces the BPMN swim-lane view with a strictly-aligned layer cake:

    ╔════ ACTORES ═════════════════════════════════════════╗
    ║  [Actor 1]  [Actor 2]  [Actor 3] ...                 ║
    ╠════ ACCIONES (Comandos) ══════════════════════════════╣
    ║  [Cmd 1]  [Cmd 2]  [Cmd 3] ...                       ║
    ╠════ AGREGADOS ═══════════════════════════════════════╣
    ║  [Agg 1]  [Agg 2] ...                                ║
    ╠════ CONSECUENCIAS (Eventos) ═════════════════════════╣
    ║  [Evt 1]  [Evt 2]  [Evt 3] ...                       ║
    ╠════ REACCIONES (Políticas) ══════════════════════════╣
    ║  [Pol 1]  [Pol 2] ...                                ║
    ╠════ SISTEMAS EXTERNOS ═══════════════════════════════╣
    ║  [Sys 1]  [Sys 2] ...                                ║
    ╚══════════════════════════════════════════════════════╝

Inside each layer every node is placed at the same Graphviz rank, so the
band stays horizontally aligned regardless of edge density.
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import DomainAnalysis, NodoGrafo

from .bpmn_flow_gv import _STYLE, _short_edge_label

# (layer_key, label, [element types], bg, border, font)
_LAYERS: list[tuple[str, str, list[str], str, str, str]] = [
    ("actores", "ACTORES", ["Actor"], "#FFFDF0", "#E6B800", "#5D4037"),
    ("acciones", "ACCIONES", ["Comando"], "#EFF6FF", "#42A5F5", "#0D47A1"),
    ("agregados", "AGREGADOS", ["Agregado", "Entidad Raíz"], "#FFF8EC", "#E65100", "#E65100"),
    ("consecuencias", "CONSECUENCIAS", ["Evento"], "#FFF4E6", "#FB8C00", "#BF360C"),
    ("reacciones", "REACCIONES", ["Política", "Política de UI"], "#F2EDFF", "#7C4DFF", "#283593"),
    ("sistemas", "SISTEMAS EXTERNOS", ["Sistema Externo"], "#EFF3F7", "#607D8B", "#37474F"),
]


def build(analysis: DomainAnalysis) -> graphviz.Digraph:
    bp = analysis.big_picture

    # Filter to flow-relevant element types only (drop Rules/Hotspots — those
    # live on the per-aggregate diagram).
    flow_types: set[str] = {t for _, _, types, *_ in _LAYERS for t in types}
    nodes = [n for n in bp.nodos if n.tipo_elemento in flow_types]
    node_ids = {n.id for n in nodes}
    edges = [e for e in bp.aristas if e.fuente in node_ids and e.destino in node_ids]
    referenced = {e.fuente for e in edges} | {e.destino for e in edges}

    # Drop disconnected nodes — keeps each layer clean.
    nodes = [n for n in nodes if n.id in referenced]

    g = graphviz.Digraph(engine="dot", format="pdf")
    g.attr(
        rankdir="TB",
        bgcolor="transparent",
        fontname="Helvetica",
        pad="0.6",
        nodesep="0.35",
        ranksep="0.6",
        splines="spline",
        newrank="true",
        compound="true",
    )
    g.attr("node", fontname="Helvetica", fontsize="10", margin="0.18,0.10", penwidth="1.4")
    g.attr("edge", fontname="Helvetica", fontsize="8", color="#90A4AE", arrowsize="0.7", penwidth="0.9")

    # Group nodes by layer in declared order.
    by_layer: dict[str, list[NodoGrafo]] = {key: [] for key, *_ in _LAYERS}
    for n in nodes:
        for key, _, types, *_ in _LAYERS:
            if n.tipo_elemento in types:
                by_layer[key].append(n)
                break

    # Emit one cluster per non-empty layer. Inside each cluster force rank=same
    # so the band stays horizontally aligned.
    layer_anchors: dict[str, str] = {}  # layer_key -> first node id (for invisible chain)
    for key, label, _types, bg, border, fontcolor in _LAYERS:
        layer_nodes = by_layer[key]
        if not layer_nodes:
            continue
        with g.subgraph(name=f"cluster_layer_{key}") as layer:
            layer.attr(
                label=label,
                labeljust="l",
                labelloc="t",
                fontname="Helvetica",
                fontsize="12",
                fontcolor=fontcolor,
                style="rounded,filled",
                color=border,
                bgcolor=bg,
                fillcolor=bg,
                penwidth="1.4",
                margin="14",
            )
            layer.attr(rank="same")
            for n in layer_nodes:
                _add_node(layer, n)
            layer_anchors[key] = layer_nodes[0].id

    # Force the vertical order of layers via invisible edges between anchors of
    # consecutive non-empty layers. Without this Graphviz may shuffle the bands
    # when many cross-layer edges fight for vertical space.
    ordered_keys = [k for k, *_ in _LAYERS if k in layer_anchors]
    for prev, nxt in zip(ordered_keys, ordered_keys[1:]):
        g.edge(layer_anchors[prev], layer_anchors[nxt], style="invis", weight="20", minlen="2")

    for e in edges:
        label = _short_edge_label(e.descripcion)
        g.edge(e.fuente, e.destino, label=f"  {label}  " if label else "")

    return g


def _add_node(g: graphviz.Digraph, n: NodoGrafo) -> None:
    fill, stroke, fc, shape, style = _STYLE.get(n.tipo_elemento, ("#F5F5F5", "#BDBDBD", "#333", "box", "filled"))
    g.node(n.id, n.nombre, shape=shape, style=style, fillcolor=fill, color=stroke, fontcolor=fc)
