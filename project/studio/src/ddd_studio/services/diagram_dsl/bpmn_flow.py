"""BPMN-style swim-lane flow — Mermaid flowchart with one subgraph per role.

Replaces the saturated "Event Storming - Mapa Completo" Graphviz dump with a
process-oriented visual closer to BPMN: each Actor / External System / Aggregate
becomes a horizontal lane, and the cross-lane arrows show the business flow.
"""

from __future__ import annotations

from models.domain_analysis import DomainAnalysis, NodoGrafo

from ._common import INIT_DIRECTIVE, class_for, classdefs, label, sanitize_id, shape_for

_BPMN_FLOW_TYPES = {"Actor", "Sistema Externo", "Comando", "Evento", "Política", "Agregado", "Entidad Raíz"}


def build(analysis: DomainAnalysis) -> str:
    bp = analysis.big_picture

    # Filter aggressively: BPMN view only shows flow-relevant element types. Rules
    # and Hotspots live on the per-aggregate diagrams; on a >50-node Big Picture
    # they push Mermaid/Kroki past Puppeteer's screenshot limit.
    flow_nodes = [n for n in bp.nodos if n.tipo_elemento in _BPMN_FLOW_TYPES]
    flow_ids = {n.id for n in flow_nodes}
    flow_edges = [e for e in bp.aristas if e.fuente in flow_ids and e.destino in flow_ids]
    nodes_by_id = {n.id: n for n in flow_nodes}

    # 1) Assign every node to a lane.
    lane_of: dict[str, str] = {}
    lanes: dict[str, dict] = {}  # lane_id -> {"title": str, "nodes": [NodoGrafo]}

    def ensure_lane(lane_id: str, title: str) -> None:
        if lane_id not in lanes:
            lanes[lane_id] = {"title": title, "nodes": []}

    # Each Actor / External System / Aggregate is its own lane (preserves DDD intent).
    for n in flow_nodes:
        if n.tipo_elemento in {"Actor", "Sistema Externo", "Agregado", "Entidad Raíz"}:
            lane_id = sanitize_id(n.id) + "_lane"
            ensure_lane(lane_id, f"{n.tipo_elemento}: {n.nombre}")
            lane_of[n.id] = lane_id

    out_edges: dict[str, list[str]] = {}
    in_edges: dict[str, list[str]] = {}
    for e in flow_edges:
        out_edges.setdefault(e.fuente, []).append(e.destino)
        in_edges.setdefault(e.destino, []).append(e.fuente)

    # Commands → lane of the aggregate they target, else of the actor that triggers them.
    for n in flow_nodes:
        if n.tipo_elemento != "Comando":
            continue
        target_lane = _find_lane_via(n.id, out_edges, nodes_by_id, lane_of, prefer={"Agregado", "Entidad Raíz"})
        if target_lane is None:
            target_lane = _find_lane_via(n.id, in_edges, nodes_by_id, lane_of, prefer={"Actor", "Sistema Externo"})
        if target_lane is None:
            ensure_lane("lane_cmd", "Comandos")
            target_lane = "lane_cmd"
        lane_of[n.id] = target_lane

    # Events → lane of the aggregate that produces them.
    for n in flow_nodes:
        if n.tipo_elemento != "Evento":
            continue
        producer_lane = _find_lane_via(n.id, in_edges, nodes_by_id, lane_of, prefer={"Agregado", "Entidad Raíz"})
        if producer_lane is None:
            ensure_lane("lane_evt", "Eventos")
            producer_lane = "lane_evt"
        lane_of[n.id] = producer_lane

    # Policies go in their own lane.
    if any(n.tipo_elemento == "Política" for n in flow_nodes):
        ensure_lane("lane_pol", "Políticas")
    for n in flow_nodes:
        if n.tipo_elemento == "Política":
            lane_of[n.id] = "lane_pol"

    # 2) Place each node inside its lane.
    for n in flow_nodes:
        lane_id = lane_of.get(n.id)
        if lane_id is None:
            ensure_lane("lane_otros", "Otros")
            lane_id = "lane_otros"
            lane_of[n.id] = lane_id
        lanes[lane_id]["nodes"].append(n)

    # 3) Drop empty lanes and lanes that have no edges touching them — keeps
    # the diagram focused on the actual flow.
    referenced_ids = {e.fuente for e in flow_edges} | {e.destino for e in flow_edges}
    for lane in lanes.values():
        lane["nodes"] = [n for n in lane["nodes"] if n.id in referenced_ids]
    lanes = {lid: lane for lid, lane in lanes.items() if lane["nodes"]}

    # 4) Emit Mermaid source.
    lines: list[str] = [INIT_DIRECTIVE, "flowchart LR", classdefs().rstrip()]
    for lane_id, lane in lanes.items():
        lines.append(f"    subgraph {lane_id}[{label(lane['title'])}]")
        lines.append("        direction LR")
        for n in lane["nodes"]:
            lines.append(
                f"        {sanitize_id(n.id)}{shape_for(n.tipo_elemento, n.nombre)}:::{class_for(n.tipo_elemento)}"
            )
        lines.append("    end")

    # 5) Edges only between nodes that survived filtering.
    placed_ids = {n.id for lane in lanes.values() for n in lane["nodes"]}
    for e in flow_edges:
        if e.fuente not in placed_ids or e.destino not in placed_ids:
            continue
        src = sanitize_id(e.fuente)
        dst = sanitize_id(e.destino)
        desc = _short_label(e.descripcion)
        if desc:
            lines.append(f"    {src} -->|{desc}| {dst}")
        else:
            lines.append(f"    {src} --> {dst}")

    return "\n".join(lines)


def _find_lane_via(
    node_id: str,
    edges_map: dict[str, list[str]],
    nodes_by_id: dict[str, NodoGrafo],
    lane_of: dict[str, str],
    *,
    prefer: set[str],
) -> str | None:
    """Walk one hop through `edges_map` and return the first lane whose target node
    type matches `prefer`."""
    for neighbour_id in edges_map.get(node_id, []):
        neighbour = nodes_by_id.get(neighbour_id)
        if neighbour is None:
            continue
        if neighbour.tipo_elemento in prefer and neighbour_id in lane_of:
            return lane_of[neighbour_id]
    return None


def _short_label(desc: str) -> str:
    """Edge-label sanitiser.

    Mermaid's `|label|` syntax breaks if the label contains `|`, parens, brackets,
    or trailing ellipsis — those tokens collide with node-shape parsing. We strip
    them out and cap length.
    """
    raw = (desc or "").strip()
    for ch in '"|()[]{};\n\r':
        raw = raw.replace(ch, " ")
    raw = " ".join(raw.split())
    if len(raw) > 28:
        raw = raw[:25] + "..."
    return raw
