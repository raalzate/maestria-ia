"""DomainAnalysis → React Flow JSON payload.

The browser-side viewer (`ui/visualization/react_flow_viewer.py`) consumes
this payload, runs a dagre layout, and renders custom Event Storming sticky
notes. Keeping the layout out of Python means the UI can re-arrange nodes on
the fly when the user drags or resizes the canvas.

Each view (Big Picture, Process Level, Read Models, Event Storming Full) has
its own selector that returns the nodes + edges to display. The serialiser
turns them into the shape React Flow expects.
"""

from __future__ import annotations

from typing import Any

from models.domain_analysis import (
    AristaGrafo,
    DomainAnalysis,
    GrafoPorAgregado,
    NodoGrafo,
)

# DDD element type → React Flow `type` string. The JS side registers a
# `nodeTypes` map keyed by these values.
ELEMENT_TYPE_TO_RF_TYPE = {
    "Actor": "actor",
    "Sistema Externo": "sistema_externo",
    "Comando": "comando",
    "Agregado": "agregado",
    "Entidad Raíz": "entidad_raiz",
    "Evento": "evento",
    "Política": "politica",
    "Política de UI": "politica_ui",
    "Regla de Negocio": "regla",
    "Read Model": "read_model",
    "Vista": "vista",
    "Proyección": "proyeccion",
    "Hotspot": "hotspot",
}


# ── View selectors ───────────────────────────────────────────────────────


def select_big_picture(a: DomainAnalysis) -> tuple[list[NodoGrafo], list[AristaGrafo]]:
    return list(a.big_picture.nodos), list(a.big_picture.aristas)


def select_aggregate(agg: GrafoPorAgregado) -> tuple[list[NodoGrafo], list[AristaGrafo]]:
    return list(agg.nodos), list(agg.aristas)


def select_all_aggregates(
    a: DomainAnalysis,
) -> tuple[list[NodoGrafo], list[AristaGrafo]]:
    """All aggregates' internal nodes + inter-aggregate policies."""
    nodes: list[NodoGrafo] = []
    edges: list[AristaGrafo] = []
    seen_ids: set[str] = set()
    for agg in a.agregados:
        for n in agg.nodos:
            if n.id in seen_ids:
                continue
            seen_ids.add(n.id)
            nodes.append(n)
        edges.extend(agg.aristas)
    edges.extend(a.politicas_inter_agregados)
    return nodes, edges


def select_read_models(a: DomainAnalysis) -> tuple[list[NodoGrafo], list[AristaGrafo]]:
    """Read models + the events they project, plus synthetic 'projects' edges."""
    nodes: list[NodoGrafo] = []
    edges: list[AristaGrafo] = []
    seen: set[str] = set()
    bp_ids = {n.id for n in a.big_picture.nodos}
    agg_node_ids = {n.id: n for agg in a.agregados for n in agg.nodos}
    all_node_by_id: dict[str, NodoGrafo] = {n.id: n for n in a.big_picture.nodos}
    all_node_by_id.update(agg_node_ids)

    for rm in a.read_models:
        rm_id = f"rm_{rm.nombre}"
        rm_node = NodoGrafo(
            id=rm_id,
            tipo_elemento="Read Model",
            nombre=rm.nombre,
            descripcion=rm.descripcion or "",
            nivel="read_model",
        )
        if rm_id not in seen:
            seen.add(rm_id)
            nodes.append(rm_node)
        for ev_id in rm.proyecta:
            ev = all_node_by_id.get(ev_id)
            if ev and ev_id not in seen:
                seen.add(ev_id)
                nodes.append(ev)
            if ev_id in all_node_by_id or ev_id in bp_ids:
                edges.append(AristaGrafo(fuente=ev_id, destino=rm_id, descripcion="proyecta"))
    return nodes, edges


def select_event_storming_full(
    a: DomainAnalysis,
) -> tuple[list[NodoGrafo], list[AristaGrafo]]:
    """Everything: Big Picture + each aggregate + inter-aggregate policies + read models."""
    nodes: list[NodoGrafo] = []
    edges: list[AristaGrafo] = []
    seen: set[str] = set()

    for n in a.big_picture.nodos:
        if n.id in seen:
            continue
        seen.add(n.id)
        nodes.append(n)
    edges.extend(a.big_picture.aristas)

    for agg in a.agregados:
        for n in agg.nodos:
            if n.id in seen:
                continue
            seen.add(n.id)
            nodes.append(n)
        edges.extend(agg.aristas)

    edges.extend(a.politicas_inter_agregados)

    # Read models as derived nodes connected to the events they project.
    for rm in a.read_models:
        rm_id = f"rm_{rm.nombre}"
        if rm_id in seen:
            continue
        seen.add(rm_id)
        nodes.append(
            NodoGrafo(
                id=rm_id,
                tipo_elemento="Read Model",
                nombre=rm.nombre,
                descripcion=rm.descripcion or "",
                nivel="read_model",
            )
        )
        for ev_id in rm.proyecta:
            if ev_id in seen:
                edges.append(AristaGrafo(fuente=ev_id, destino=rm_id, descripcion="proyecta"))
    return nodes, edges


# ── Serialiser ──────────────────────────────────────────────────────────


def to_react_flow(nodes: list[NodoGrafo], edges: list[AristaGrafo]) -> dict[str, Any]:
    """Return a `{nodes, edges}` dict ready to be JSON-encoded for the browser.

    Strips edges whose endpoints aren't in the node set, so React Flow never
    receives a dangling reference (it crashes silently if that happens).
    """
    node_ids = {n.id for n in nodes}

    rf_nodes = []
    for n in nodes:
        rf_nodes.append(
            {
                "id": n.id,
                "type": ELEMENT_TYPE_TO_RF_TYPE.get(n.tipo_elemento, "default"),
                "data": {
                    "label": n.nombre,
                    "subtitle": n.tipo_elemento,
                    "id": n.id,
                    "description": getattr(n, "descripcion", "") or "",
                    "state": getattr(n, "estado_comparativo", "existente") or "existente",
                    "tags": list(getattr(n, "tags_tecnologia", None) or []),
                },
            }
        )

    rf_edges = []
    seen_edge_keys: set[tuple[str, str, str]] = set()
    for idx, e in enumerate(edges):
        if e.fuente not in node_ids or e.destino not in node_ids:
            continue
        desc = (e.descripcion or "").strip()
        key = (e.fuente, e.destino, desc)
        if key in seen_edge_keys:
            continue
        seen_edge_keys.add(key)
        rf_edges.append(
            {
                "id": f"e{idx}_{e.fuente}_{e.destino}",
                "source": e.fuente,
                "target": e.destino,
                "label": desc,
                "data": {
                    "state": getattr(e, "estado_comparativo", "existente") or "existente",
                },
            }
        )
    return {"nodes": rf_nodes, "edges": rf_edges}
