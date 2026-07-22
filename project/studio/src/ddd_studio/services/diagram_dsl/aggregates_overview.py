"""Aggregates Overview — Mermaid LR flowchart showing each aggregate as a
compact subgraph with its commands and events, plus inter-aggregate policies
as dashed arrows between subgraphs.

Replaces the saturated "Process Level - Todos los Agregados" view.
"""

from __future__ import annotations

from models.domain_analysis import DomainAnalysis

from ._common import INIT_DIRECTIVE, classdefs, label, sanitize_id


def build(analysis: DomainAnalysis) -> str:
    lines: list[str] = [INIT_DIRECTIVE, "flowchart LR", classdefs().rstrip()]

    if not analysis.agregados:
        lines.append('    empty["No hay agregados modelados"]')
        return "\n".join(lines)

    # Track each aggregate's command and event IDs so we can connect inter-agg policies.
    agg_node_ids: dict[str, set[str]] = {}

    for agg in analysis.agregados:
        sub_id = sanitize_id(f"AGG_{agg.nombre_agregado}")
        title = f"{agg.nombre_agregado} · raíz: {agg.entidad_raiz}"
        lines.append(f"    subgraph {sub_id}[{label(title, max_chars=80)}]")
        lines.append("        direction TB")

        ids: set[str] = set()
        cmds = [n for n in agg.nodos if n.tipo_elemento == "Comando"]
        evts = [n for n in agg.nodos if n.tipo_elemento == "Evento"]

        if cmds:
            cmd_list = ", ".join(n.nombre for n in cmds)
            cmd_id = sub_id + "_cmds"
            lines.append(f"        {cmd_id}[{label('Comandos: ' + cmd_list, max_chars=110)}]:::cmd")
        if evts:
            evt_list = ", ".join(n.nombre for n in evts)
            evt_id = sub_id + "_evts"
            lines.append(f"        {evt_id}(({label('Eventos: ' + evt_list, max_chars=110)})):::evt")
        if cmds and evts:
            lines.append(f"        {sub_id}_cmds --> {sub_id}_evts")
        for n in agg.nodos:
            ids.add(n.id)
        agg_node_ids[sub_id] = ids
        lines.append("    end")

    # Inter-aggregate policies → dashed arrows between subgraphs (label = description).
    for edge in analysis.politicas_inter_agregados:
        src_sub = _find_aggregate(edge.fuente, agg_node_ids)
        dst_sub = _find_aggregate(edge.destino, agg_node_ids)
        if not src_sub or not dst_sub or src_sub == dst_sub:
            continue
        desc = _short_label(edge.descripcion)
        if desc:
            lines.append(f"    {src_sub} -. {desc} .-> {dst_sub}")
        else:
            lines.append(f"    {src_sub} -.-> {dst_sub}")

    return "\n".join(lines)


def _find_aggregate(node_id: str, agg_node_ids: dict[str, set[str]]) -> str | None:
    for sub_id, ids in agg_node_ids.items():
        if node_id in ids:
            return sub_id
    return None


def _short_label(text: str) -> str:
    raw = (text or "").strip()
    for ch in '"|()[]{};\n\r':
        raw = raw.replace(ch, " ")
    raw = " ".join(raw.split())
    # Avoid trailing "..." — it collides with Mermaid's `-. label .->` dashed-arrow tokens.
    if len(raw) > 36:
        raw = raw[:36].rstrip()
    return raw
