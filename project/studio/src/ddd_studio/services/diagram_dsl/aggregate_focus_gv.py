"""Focused BPMN for a single aggregate, with commands and events grouped.

To kill visual noise, all commands targeting the aggregate are collapsed into
one box and all events emitted by the aggregate into another. Each appears
as a bulleted list. This turns 20+ edges into 2 (one in, one out), which
is the BPMN-friendly "many commands, many events" canonical view.
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import (
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
)

from .bpmn_flow_gv import _STYLE, _short_edge_label

_POOLS: list[tuple[str, str, str, str]] = [
    ("roles", "ACTORES", "#FFFDF0", "#E6B800"),
    ("dominio", "AGREGADO", "#FFF8EC", "#E65100"),
    ("reglas", "REGLAS · HOTSPOTS", "#F8F0FF", "#9C27B0"),
    ("sistemas", "SISTEMAS EXTERNOS", "#EFF3F7", "#607D8B"),
]

_CMDS_GROUP_ID = "__CMDS_GROUP__"
_EVTS_GROUP_ID = "__EVTS_GROUP__"


def build(agg: GrafoPorAgregado, analysis: DomainAnalysis) -> graphviz.Digraph:
    g = graphviz.Digraph(engine="dot", format="pdf")
    g.attr(
        rankdir="LR",
        compound="true",
        bgcolor="transparent",
        fontname="Helvetica",
        pad="0.6",
        nodesep="0.35",
        ranksep="0.85",
        splines="true",
        newrank="true",
    )
    g.attr("node", fontname="Helvetica", fontsize="10", margin="0.18,0.10", penwidth="1.4")
    g.attr("edge", fontname="Helvetica", fontsize="8", color="#90A4AE", arrowsize="0.7", penwidth="0.9")

    cmds = [n for n in agg.nodos if n.tipo_elemento == "Comando"]
    evts = [n for n in agg.nodos if n.tipo_elemento == "Evento"]
    root_agg = next((n for n in agg.nodos if n.tipo_elemento in {"Agregado", "Entidad Raíz"}), None)
    rules = [n for n in agg.nodos if n.tipo_elemento == "Regla de Negocio"]
    hotspots = [n for n in agg.nodos if n.tipo_elemento == "Hotspot"]
    sistemas = [n for n in agg.nodos if n.tipo_elemento == "Sistema Externo"]
    actores = [n for n in agg.nodos if n.tipo_elemento == "Actor"]

    grouped_cmd_ids = {n.id for n in cmds}
    grouped_evt_ids = {n.id for n in evts}

    # === Pool: ACTORES ===
    if actores:
        with g.subgraph(name="cluster_pool_roles") as pool:
            _pool_attrs(pool, "ACTORES", "#FFFDF0", "#E6B800")
            for n in actores:
                _add_node(pool, n)

    # === Pool: AGREGADO with grouped commands + agg + grouped events ===
    with g.subgraph(name="cluster_pool_dominio") as pool:
        _pool_attrs(pool, "AGREGADO", "#FFF8EC", "#E65100")
        if cmds:
            pool.node(
                _CMDS_GROUP_ID,
                _group_label("Acciones", cmds),
                shape="box",
                style="filled,rounded",
                fillcolor="#BBDEFB",
                color="#42A5F5",
                fontcolor="#0D47A1",
            )
        if root_agg:
            _add_node(pool, root_agg)
        if evts:
            pool.node(
                _EVTS_GROUP_ID,
                _group_label("Consecuencias", evts),
                shape="box",
                style="filled,rounded,bold",
                fillcolor="#FFE0B2",
                color="#FB8C00",
                fontcolor="#BF360C",
            )

    # === Pool: REGLAS · HOTSPOTS ===
    if rules or hotspots:
        with g.subgraph(name="cluster_pool_reglas") as pool:
            _pool_attrs(pool, "REGLAS · HOTSPOTS", "#F8F0FF", "#9C27B0")
            for n in rules:
                _add_node(pool, n)
            for n in hotspots:
                _add_node(pool, n)

    # === Pool: SISTEMAS EXTERNOS ===
    if sistemas:
        with g.subgraph(name="cluster_pool_sistemas") as pool:
            _pool_attrs(pool, "SISTEMAS EXTERNOS", "#EFF3F7", "#607D8B")
            for n in sistemas:
                _add_node(pool, n)

    # Synthetic edges around the grouped nodes.
    if cmds and root_agg:
        g.edge(_CMDS_GROUP_ID, root_agg.id, label="  actúa sobre  ")
    if evts and root_agg:
        g.edge(root_agg.id, _EVTS_GROUP_ID, label="  produce  ")

    # Remaining edges: route grouped node IDs to the synthetic group IDs and dedupe.
    seen: set[tuple[str, str]] = set()
    # Pre-register the synthetic edges so we don't emit them twice.
    if cmds and root_agg:
        seen.add((_CMDS_GROUP_ID, root_agg.id))
    if evts and root_agg:
        seen.add((root_agg.id, _EVTS_GROUP_ID))

    for e in agg.aristas:
        src = _remap(e.fuente, grouped_cmd_ids, grouped_evt_ids)
        dst = _remap(e.destino, grouped_cmd_ids, grouped_evt_ids)
        if src == dst:
            continue
        key = (src, dst)
        if key in seen:
            continue
        seen.add(key)
        label = _short_edge_label(e.descripcion)
        g.edge(src, dst, label=f"  {label}  " if label else "")

    return g


def _pool_attrs(pool, label: str, bg: str, border: str) -> None:
    pool.attr(
        label=label,
        labeljust="l",
        labelloc="t",
        fontname="Helvetica",
        fontsize="12",
        fontcolor=border,
        style="rounded",
        color=border,
        bgcolor=bg,
        fillcolor=bg,
        penwidth="1.6",
        margin="18",
    )


def _add_node(g: graphviz.Digraph, n: NodoGrafo) -> None:
    fill, stroke, fc, shape, style = _STYLE.get(
        n.tipo_elemento,
        ("#F5F5F5", "#BDBDBD", "#333", "box", "filled"),
    )
    if n.tipo_elemento == "Regla de Negocio":
        shape, fill, stroke, fc = "box", "#EDE7F6", "#9C27B0", "#4A148C"
        style = "filled,rounded"
    elif n.tipo_elemento == "Hotspot":
        shape, fill, stroke, fc = "octagon", "#FFEBEE", "#EF5350", "#B71C1C"
        style = "filled,bold"
    g.node(n.id, n.nombre, shape=shape, style=style, fillcolor=fill, color=stroke, fontcolor=fc)


def _group_label(heading: str, items: list[NodoGrafo]) -> str:
    """Build a left-aligned multi-line label for a grouped box."""
    lines = [f"{heading} ({len(items)})"]
    for n in items:
        name = n.nombre.replace('"', "'")
        lines.append(f"• {name}")
    # `\l` left-aligns each line within the node; `\n` would centre them.
    return "\\l".join(lines) + "\\l"


def _remap(node_id: str, cmds: set[str], evts: set[str]) -> str:
    if node_id in cmds:
        return _CMDS_GROUP_ID
    if node_id in evts:
        return _EVTS_GROUP_ID
    return node_id


def _trivial_label_filter(text: str) -> str:
    """Re-export for tests."""
    return _short_edge_label(text)
