"""Mapa de Agregados via Graphviz — each aggregate is a cluster with a compact
summary of its commands and events. Inter-aggregate policies surface as dashed
arrows between clusters.
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import DomainAnalysis


def build(analysis: DomainAnalysis) -> graphviz.Digraph:
    g = graphviz.Digraph(engine="dot", format="pdf")
    g.attr(
        rankdir="TB",
        bgcolor="transparent",
        fontname="Helvetica",
        pad="0.6",
        nodesep="0.5",
        ranksep="0.9",
        splines="spline",
        compound="true",
    )
    g.attr("node", fontname="Helvetica", fontsize="10", margin="0.18,0.10", penwidth="1.4")
    g.attr("edge", fontname="Helvetica", fontsize="9", color="#90A4AE", arrowsize="0.7")

    if not analysis.agregados:
        g.node(
            "empty", "Sin agregados modelados", shape="note", style="filled", fillcolor="#FFF8E1", fontcolor="#666666"
        )
        return g

    agg_to_cluster: dict[str, str] = {}
    agg_to_anchor: dict[str, str] = {}

    for agg in analysis.agregados:
        cluster_name = f"cluster_AGG_{_sanitize(agg.nombre_agregado)}"
        with g.subgraph(name=cluster_name) as sub:
            sub.attr(
                label=f"{agg.nombre_agregado}  ·  raíz: {agg.entidad_raiz}",
                labeljust="l",
                fontname="Helvetica",
                fontsize="12",
                style="rounded,filled",
                bgcolor="#FFFBF2",
                color="#FB8C00",
                penwidth="1.4",
                margin="16",
            )
            cmds = [n for n in agg.nodos if n.tipo_elemento == "Comando"]
            evts = [n for n in agg.nodos if n.tipo_elemento == "Evento"]

            cmd_id = f"{cluster_name}_cmds"
            evt_id = f"{cluster_name}_evts"
            anchor = cmd_id if cmds else (evt_id if evts else cluster_name)

            if cmds:
                cmd_lines = "Acciones:\n• " + "\n• ".join(n.nombre for n in cmds)
                sub.node(
                    cmd_id,
                    cmd_lines,
                    shape="box",
                    style="filled,rounded",
                    fillcolor="#BBDEFB",
                    color="#42A5F5",
                    fontcolor="#0D47A1",
                )
            if evts:
                evt_lines = "Consecuencias:\n• " + "\n• ".join(n.nombre for n in evts)
                sub.node(
                    evt_id,
                    evt_lines,
                    shape="box",
                    style="filled,rounded,bold",
                    fillcolor="#FFE0B2",
                    color="#FB8C00",
                    fontcolor="#BF360C",
                )
            if cmds and evts:
                sub.edge(cmd_id, evt_id, color="#FB8C00", penwidth="1.2")
            agg_to_cluster[agg.nombre_agregado] = cluster_name
            agg_to_anchor[agg.nombre_agregado] = anchor

    # Build a lookup from any node id -> aggregate cluster.
    node_to_agg: dict[str, str] = {}
    for agg in analysis.agregados:
        for n in agg.nodos:
            node_to_agg[n.id] = agg.nombre_agregado

    drawn: set[tuple[str, str]] = set()
    for edge in analysis.politicas_inter_agregados:
        src_agg = node_to_agg.get(edge.fuente)
        dst_agg = node_to_agg.get(edge.destino)
        if not src_agg or not dst_agg or src_agg == dst_agg:
            continue
        key = (src_agg, dst_agg, edge.descripcion or "")
        if key in drawn:
            continue
        drawn.add(key)
        desc = (edge.descripcion or "").strip().replace('"', "")
        if len(desc) > 30:
            desc = desc[:30]
        g.edge(
            agg_to_anchor[src_agg],
            agg_to_anchor[dst_agg],
            label=f"  {desc}  " if desc else "",
            ltail=agg_to_cluster[src_agg],
            lhead=agg_to_cluster[dst_agg],
            style="dashed",
            color="#7C4DFF",
            fontcolor="#5E35B1",
            penwidth="1.4",
        )
    return g


def _sanitize(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)
