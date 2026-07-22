"""Event Timeline — Mermaid LR flowchart with only Events and Policies.

Replaces the saturated "Big Picture" Graphviz view with a canonical Event
Storming timeline: the temporal sequence of Domain Events. Policies that
react to an event and trigger the next are placed inline between events.

Excludes commands, actors, external systems, aggregates, read models, rules
and hotspots — those live on the other (per-aggregate) diagrams.
"""

from __future__ import annotations

from models.domain_analysis import DomainAnalysis

from ._common import INIT_DIRECTIVE, class_for, classdefs, sanitize_id, shape_for


def build(analysis: DomainAnalysis) -> str:
    bp = analysis.big_picture
    nodes_by_id = {n.id: n for n in bp.nodos}
    timeline_types = {"Evento", "Política"}

    # Preserve Pass-1 (order-of-appearance) ordering.
    sequence = [n for n in bp.nodos if n.tipo_elemento in timeline_types]

    lines: list[str] = [INIT_DIRECTIVE, "flowchart LR", classdefs().rstrip()]

    if not sequence:
        lines.append('    empty["No hay eventos en el Big Picture"]')
        return "\n".join(lines)

    # Declare nodes.
    declared: set[str] = set()
    for n in sequence:
        nid = sanitize_id(n.id)
        if nid in declared:
            continue
        declared.add(nid)
        lines.append(f"    {nid}{shape_for(n.tipo_elemento, n.nombre)}:::{class_for(n.tipo_elemento)}")

    # Draw the timeline: events in appearance order, policies as bridges.
    edges: list[str] = []
    for src, dst in zip(sequence, sequence[1:]):
        edges.append(f"    {sanitize_id(src.id)} --> {sanitize_id(dst.id)}")

    # Overlay any explicit edges (events triggering policies, policies triggering events)
    # that the analyser captured, to keep faithfulness with the model.
    explicit_pairs = set()
    for e in bp.aristas:
        src = nodes_by_id.get(e.fuente)
        dst = nodes_by_id.get(e.destino)
        if not src or not dst:
            continue
        if src.tipo_elemento not in timeline_types or dst.tipo_elemento not in timeline_types:
            continue
        key = (e.fuente, e.destino)
        if key in explicit_pairs:
            continue
        explicit_pairs.add(key)
        edges.append(f"    {sanitize_id(e.fuente)} -. {label_short(e.descripcion)} .-> {sanitize_id(e.destino)}")

    lines.extend(edges)
    return "\n".join(lines)


def label_short(text: str) -> str:
    raw = (text or "").strip()
    for ch in '"|()[]{};\n\r':
        raw = raw.replace(ch, " ")
    raw = " ".join(raw.split())
    # Avoid trailing "..." — it collides with Mermaid's `-. label .->` dashed-arrow tokens.
    if len(raw) > 24:
        raw = raw[:24].rstrip()
    return raw
