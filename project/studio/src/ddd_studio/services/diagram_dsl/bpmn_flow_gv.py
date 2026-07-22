"""BPMN-style swim-lanes via Graphviz subgraphs (`cluster_*`).

Each Actor / External System / Aggregate becomes a horizontal lane. Commands
and Events land in the lane of the aggregate / actor they touch. Policies get
their own lane. Rules and Hotspots are excluded from this BPMN view (they
belong on the per-aggregate detail diagram).
"""

from __future__ import annotations

import graphviz
from models.domain_analysis import DomainAnalysis, NodoGrafo

# DDD palette: (fillcolor, strokecolor, fontcolor, shape, style)
_STYLE: dict[str, tuple[str, str, str, str, str]] = {
    "Actor": ("#FFF9C4", "#F9A825", "#5D4037", "box", "filled,rounded,bold"),
    "Sistema Externo": ("#ECEFF1", "#78909C", "#37474F", "component", "filled"),
    "Comando": ("#BBDEFB", "#42A5F5", "#0D47A1", "box", "filled,rounded"),
    "Agregado": ("#FFF3E0", "#FB8C00", "#E65100", "box3d", "filled,bold"),
    "Entidad Raíz": ("#FFF3E0", "#FB8C00", "#E65100", "box", "filled"),
    "Evento": ("#FFE0B2", "#FB8C00", "#BF360C", "box", "filled,rounded,bold"),
    "Política": ("#E8EAF6", "#7C4DFF", "#283593", "parallelogram", "filled"),
}

_FLOW_TYPES = {"Actor", "Sistema Externo", "Comando", "Evento", "Política", "Agregado", "Entidad Raíz"}

# BPMN pools: high-level boundaries that group lanes by DDD category. Visual
# style (bg, border, accent) hints at the kind of work each pool performs.
_POOLS: list[tuple[str, str, str, str]] = [
    # (pool_key, label, bgcolor, bordercolor)
    ("roles", "ROLES Y OPERACIÓN", "#FFFDF0", "#E6B800"),
    ("sistemas", "SISTEMAS EXTERNOS", "#EFF3F7", "#607D8B"),
    ("dominio", "DOMINIO · AGREGADOS", "#FFF8EC", "#E65100"),
    ("politicas", "POLÍTICAS / REACCIONES", "#F2EDFF", "#5E35B1"),
    ("otros", "OTROS", "#F5F5F5", "#9E9E9E"),
]

# Edge descriptions whose meaning is already obvious from the arrow direction
# and the source/destination node types. Suppressing them dramatically reduces
# label noise on dense BPMN diagrams.
_TRIVIAL_EDGE_VERBS = {
    "se dirige a",
    "se dirige",
    "produce",
    "dispara",
    "ejecuta",
    "emite",
    "se ejecuta",
    "se emite",
    "consume",
    "consumido por",
    "es consumido por",
}


def build(analysis: DomainAnalysis) -> graphviz.Digraph:
    bp = analysis.big_picture

    flow_nodes = [n for n in bp.nodos if n.tipo_elemento in _FLOW_TYPES]
    flow_ids = {n.id for n in flow_nodes}
    flow_edges = [e for e in bp.aristas if e.fuente in flow_ids and e.destino in flow_ids]
    nodes_by_id = {n.id: n for n in flow_nodes}

    # ── Group commands and events per aggregate ─────────────────────────
    # For each aggregate, gather (a) commands that target it and (b) events it
    # produces. They collapse into one synthetic node per group, reducing the
    # canonical "20 edges from agg to events" problem to a single arrow.
    aggregates = [n for n in flow_nodes if n.tipo_elemento in {"Agregado", "Entidad Raíz"}]
    grouped_cmds: dict[str, list[NodoGrafo]] = {a.id: [] for a in aggregates}
    grouped_evts: dict[str, list[NodoGrafo]] = {a.id: [] for a in aggregates}
    cmd_to_group: dict[str, str] = {}  # cmd id -> aggregate id (== group)
    evt_to_group: dict[str, str] = {}  # evt id -> aggregate id

    for e in flow_edges:
        src = nodes_by_id.get(e.fuente)
        dst = nodes_by_id.get(e.destino)
        if not src or not dst:
            continue
        # cmd -> agg : group the cmd under this aggregate
        if src.tipo_elemento == "Comando" and dst.tipo_elemento in {"Agregado", "Entidad Raíz"}:
            if src.id not in cmd_to_group:
                cmd_to_group[src.id] = dst.id
                grouped_cmds[dst.id].append(src)
        # agg -> evt : group the evt under this aggregate
        if src.tipo_elemento in {"Agregado", "Entidad Raíz"} and dst.tipo_elemento == "Evento":
            if dst.id not in evt_to_group:
                evt_to_group[dst.id] = src.id
                grouped_evts[src.id].append(dst)

    # Lane assignment.
    lane_of: dict[str, str] = {}
    lanes: dict[str, dict] = {}
    lane_pool: dict[str, str] = {}  # lane_id -> pool_key

    def ensure_lane(lane_id: str, title: str, pool: str) -> None:
        if lane_id not in lanes:
            lanes[lane_id] = {"title": title, "nodes": []}
        lane_pool.setdefault(lane_id, pool)

    # Each Actor / Sistema / Agregado is its own lane, routed to the matching pool.
    for n in flow_nodes:
        if n.tipo_elemento == "Actor":
            ensure_lane(f"L_{n.id}", n.nombre, "roles")
            lane_of[n.id] = f"L_{n.id}"
        elif n.tipo_elemento == "Sistema Externo":
            ensure_lane(f"L_{n.id}", n.nombre, "sistemas")
            lane_of[n.id] = f"L_{n.id}"
        elif n.tipo_elemento in {"Agregado", "Entidad Raíz"}:
            ensure_lane(f"L_{n.id}", n.nombre, "dominio")
            lane_of[n.id] = f"L_{n.id}"

    out_edges: dict[str, list[str]] = {}
    in_edges: dict[str, list[str]] = {}
    for e in flow_edges:
        out_edges.setdefault(e.fuente, []).append(e.destino)
        in_edges.setdefault(e.destino, []).append(e.fuente)

    def _lane_via(node_id: str, em: dict[str, list[str]], prefer: set[str]) -> str | None:
        for neigh in em.get(node_id, []):
            nb = nodes_by_id.get(neigh)
            if nb and nb.tipo_elemento in prefer and neigh in lane_of:
                return lane_of[neigh]
        return None

    for n in flow_nodes:
        if n.tipo_elemento != "Comando":
            continue
        lane = _lane_via(n.id, out_edges, {"Agregado", "Entidad Raíz"}) or _lane_via(
            n.id, in_edges, {"Actor", "Sistema Externo"}
        )
        if lane is None:
            ensure_lane("L_cmd", "Acciones", "roles")
            lane = "L_cmd"
        lane_of[n.id] = lane

    for n in flow_nodes:
        if n.tipo_elemento != "Evento":
            continue
        lane = _lane_via(n.id, in_edges, {"Agregado", "Entidad Raíz"})
        if lane is None:
            ensure_lane("L_evt", "Consecuencias", "dominio")
            lane = "L_evt"
        lane_of[n.id] = lane

    if any(n.tipo_elemento == "Política" for n in flow_nodes):
        ensure_lane("L_pol", "Políticas", "politicas")
    for n in flow_nodes:
        if n.tipo_elemento == "Política":
            lane_of[n.id] = "L_pol"

    for n in flow_nodes:
        lane_id = lane_of.get(n.id)
        if lane_id is None:
            ensure_lane("L_other", "Otros", "otros")
            lane_id = "L_other"
            lane_of[n.id] = lane_id
        lanes[lane_id]["nodes"].append(n)

    # Drop lanes containing only disconnected nodes.
    referenced = {e.fuente for e in flow_edges} | {e.destino for e in flow_edges}
    for lane in lanes.values():
        lane["nodes"] = [n for n in lane["nodes"] if n.id in referenced]
    lanes = {k: v for k, v in lanes.items() if v["nodes"]}

    # Build the Graphviz Digraph.
    g = graphviz.Digraph(engine="dot", format="pdf")
    g.attr(
        rankdir="LR",
        compound="true",
        bgcolor="transparent",
        fontname="Helvetica",
        pad="0.6",
        nodesep="0.4",
        ranksep="0.9",
        splines="true",
        newrank="true",
    )
    g.attr("node", fontname="Helvetica", fontsize="10", margin="0.18,0.10", penwidth="1.4")
    g.attr("edge", fontname="Helvetica", fontsize="8", color="#90A4AE", arrowsize="0.7", penwidth="0.9")

    # Group lanes by pool, emit pools in canonical order so the legend reads
    # top-to-bottom Roles → Sistemas → Dominio → Políticas → Otros.
    lanes_by_pool: dict[str, list[str]] = {pk: [] for pk, *_ in _POOLS}
    for lane_id in lanes:
        pk = lane_pool.get(lane_id, "otros")
        lanes_by_pool.setdefault(pk, []).append(lane_id)

    for pool_key, pool_label, pool_bg, pool_border in _POOLS:
        lane_ids = lanes_by_pool.get(pool_key) or []
        if not lane_ids:
            continue
        with g.subgraph(name=f"cluster_pool_{pool_key}") as pool_sub:
            pool_sub.attr(
                label=pool_label,
                labeljust="l",
                labelloc="t",
                fontname="Helvetica",
                fontsize="13",
                fontcolor=pool_border,
                style="rounded",
                color=pool_border,
                bgcolor=pool_bg,
                fillcolor=pool_bg,
                penwidth="1.8",
                margin="22",
            )
            for lane_id in lane_ids:
                lane = lanes[lane_id]
                with pool_sub.subgraph(name=f"cluster_{lane_id}") as lane_sub:
                    lane_sub.attr(
                        label=_lane_label(lane["title"]),
                        labeljust="l",
                        fontname="Helvetica",
                        fontsize="10",
                        fontcolor="#37474F",
                        style="rounded,filled",
                        bgcolor="#FFFFFF",
                        color="#D5DCE4",
                        penwidth="0.7",
                        margin="14",
                    )
                    _emit_lane_nodes(lane_sub, lane["nodes"], grouped_cmds, grouped_evts, cmd_to_group, evt_to_group)

    placed_ids = {n.id for lane in lanes.values() for n in lane["nodes"]}
    # Register the synthetic group IDs so edges to/from them aren't filtered.
    for agg_id, cmds_list in grouped_cmds.items():
        if cmds_list and agg_id in placed_ids:
            placed_ids.add(_cmds_group_id(agg_id))
    for agg_id, evts_list in grouped_evts.items():
        if evts_list and agg_id in placed_ids:
            placed_ids.add(_evts_group_id(agg_id))

    seen_edges: set[tuple[str, str]] = set()
    # Synthetic edges around groups: CMDS_GROUP -> agg, agg -> EVTS_GROUP.
    for agg_id, cmds_list in grouped_cmds.items():
        if cmds_list and agg_id in placed_ids:
            key = (_cmds_group_id(agg_id), agg_id)
            seen_edges.add(key)
            g.edge(key[0], key[1])
    for agg_id, evts_list in grouped_evts.items():
        if evts_list and agg_id in placed_ids:
            key = (agg_id, _evts_group_id(agg_id))
            seen_edges.add(key)
            g.edge(key[0], key[1])

    for e in flow_edges:
        src = _remap_to_group(e.fuente, cmd_to_group, evt_to_group)
        dst = _remap_to_group(e.destino, cmd_to_group, evt_to_group)
        if src not in placed_ids or dst not in placed_ids:
            continue
        if src == dst:
            continue
        if (src, dst) in seen_edges:
            continue
        seen_edges.add((src, dst))
        label = _short_edge_label(e.descripcion)
        g.edge(src, dst, label=f"  {label}  " if label else "")
    return g


def _cmds_group_id(agg_id: str) -> str:
    return f"__CMDS__{agg_id}"


def _evts_group_id(agg_id: str) -> str:
    return f"__EVTS__{agg_id}"


def _remap_to_group(node_id: str, cmd_to_group: dict[str, str], evt_to_group: dict[str, str]) -> str:
    if node_id in cmd_to_group:
        return _cmds_group_id(cmd_to_group[node_id])
    if node_id in evt_to_group:
        return _evts_group_id(evt_to_group[node_id])
    return node_id


def _emit_lane_nodes(
    lane,
    nodes: list[NodoGrafo],
    grouped_cmds: dict[str, list[NodoGrafo]],
    grouped_evts: dict[str, list[NodoGrafo]],
    cmd_to_group: dict[str, str],
    evt_to_group: dict[str, str],
) -> None:
    """Emit a lane's nodes, replacing individual cmds/evts by a single grouped
    box per aggregate. Commands/events grouped under an aggregate elsewhere are
    skipped here so they don't render twice."""
    emitted_groups: set[str] = set()
    for n in nodes:
        if n.tipo_elemento in {"Agregado", "Entidad Raíz"}:
            _add_node(lane, n)
            if grouped_cmds.get(n.id):
                gid = _cmds_group_id(n.id)
                if gid not in emitted_groups:
                    emitted_groups.add(gid)
                    lane.node(
                        gid,
                        _group_box_label("Acciones", grouped_cmds[n.id]),
                        shape="box",
                        style="filled,rounded",
                        fillcolor="#BBDEFB",
                        color="#42A5F5",
                        fontcolor="#0D47A1",
                    )
            if grouped_evts.get(n.id):
                gid = _evts_group_id(n.id)
                if gid not in emitted_groups:
                    emitted_groups.add(gid)
                    lane.node(
                        gid,
                        _group_box_label("Consecuencias", grouped_evts[n.id]),
                        shape="box",
                        style="filled,rounded,bold",
                        fillcolor="#FFE0B2",
                        color="#FB8C00",
                        fontcolor="#BF360C",
                    )
        elif n.tipo_elemento == "Comando" and n.id in cmd_to_group:
            continue  # collapsed into the aggregate's grouped Comandos box
        elif n.tipo_elemento == "Evento" and n.id in evt_to_group:
            continue  # collapsed into the aggregate's grouped Eventos box
        else:
            _add_node(lane, n)


def _group_box_label(heading: str, items: list[NodoGrafo]) -> str:
    lines = [f"{heading} ({len(items)})"]
    for n in items:
        lines.append(f"• {n.nombre.replace(chr(34), chr(39))}")
    return "\\l".join(lines) + "\\l"


def _add_node(g: graphviz.Digraph, n: NodoGrafo) -> None:
    fill, stroke, fc, shape, style = _STYLE.get(n.tipo_elemento, ("#F5F5F5", "#BDBDBD", "#333", "box", "filled"))
    g.node(n.id, n.nombre, shape=shape, style=style, fillcolor=fill, color=stroke, fontcolor=fc)


def _lane_label(title: str) -> str:
    raw = (title or "").strip()
    if len(raw) > 60:
        raw = raw[:60]
    return raw


def _short_edge_label(text: str) -> str:
    raw = (text or "").strip().replace('"', "")
    if raw.lower() in _TRIVIAL_EDGE_VERBS:
        return ""
    if len(raw) > 22:
        raw = raw[:22]
    return raw
