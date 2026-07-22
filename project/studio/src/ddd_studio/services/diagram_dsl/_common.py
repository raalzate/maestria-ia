"""Shared helpers for the diagram_dsl builders."""

from __future__ import annotations

import re

_ID_PATTERN = re.compile(r"[^A-Za-z0-9_]")
_MERMAID_CLASSDEFS = """    classDef cmd fill:#BBDEFB,stroke:#42A5F5,color:#0D47A1
    classDef evt fill:#FFE0B2,stroke:#FF8C00,color:#BF360C
    classDef pol fill:#E8EAF6,stroke:#7C4DFF,color:#283593
    classDef act fill:#FFF9C4,stroke:#F9A825,color:#5D4037
    classDef sys fill:#ECEFF1,stroke:#78909C,color:#37474F
    classDef agg fill:#FFF3E0,stroke:#FB8C00,color:#E65100
    classDef rule fill:#EDE7F6,stroke:#9C27B0,color:#4A148C
    classDef rm fill:#E8F5E9,stroke:#43A047,color:#1B5E20
    classDef hot fill:#FFEBEE,stroke:#EF5350,color:#B71C1C
"""

_TYPE_TO_CLASS = {
    "Actor": "act",
    "Sistema Externo": "sys",
    "Comando": "cmd",
    "Evento": "evt",
    "Política": "pol",
    "Política de UI": "pol",
    "Agregado": "agg",
    "Entidad Raíz": "agg",
    "Regla de Negocio": "rule",
    "Read Model": "rm",
    "Vista": "rm",
    "Proyección": "rm",
    "Hotspot": "hot",
}


def sanitize_id(node_id: str) -> str:
    """Mermaid node IDs only accept [A-Za-z0-9_], rewrite others to '_'."""
    cleaned = _ID_PATTERN.sub("_", node_id or "")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "n_" + cleaned
    return cleaned


def label(text: str, *, max_chars: int = 60) -> str:
    """Build a Mermaid label expression. Escapes quotes, trims long labels."""
    raw = (text or "").strip()
    if len(raw) > max_chars:
        raw = raw[: max_chars - 1] + "…"
    raw = raw.replace('"', "&quot;")
    return f'"{raw}"'


def classdefs() -> str:
    """Return the shared Mermaid `classDef` block (DDD palette)."""
    return _MERMAID_CLASSDEFS


# Kroki/Mermaid ignores `htmlLabels: false`, and CairoSVG cannot render the
# resulting <foreignObject> HTML labels. We deliberately ship Mermaid without
# init overrides and let Kroki rasterise to a high-resolution PNG instead.
# Keeping the init directive empty means the source stays small (lower chance
# of Puppeteer crashes on big graphs) and PNG output remains predictable.
INIT_DIRECTIVE = ""


# PDF-only display labels for DDD elements. Business stakeholders read the
# report; the canonical DDD terms (Comando/Evento) live on the data model and
# the interactive UI, but the PDF substitutes friendlier wording.
PDF_DISPLAY_TYPE = {
    "Comando": "Acción",
    "Evento": "Consecuencia",
}
PDF_DISPLAY_PLURAL = {
    "Comando": "Acciones",
    "Evento": "Consecuencias",
}


def display_type(tipo: str) -> str:
    return PDF_DISPLAY_TYPE.get(tipo, tipo)


def display_plural(tipo: str) -> str:
    return PDF_DISPLAY_PLURAL.get(tipo, tipo + "s")


def class_for(tipo: str) -> str:
    return _TYPE_TO_CLASS.get(tipo, "")


def shape_for(tipo: str, text: str) -> str:
    """Return the Mermaid shape syntax for a node based on its DDD element type."""
    expr = label(text)
    if tipo in {"Evento"}:
        return f"(({expr}))"  # rounded — events
    if tipo in {"Política", "Política de UI"}:
        return f"[/{expr}/]"  # parallelogram — policies
    if tipo in {"Regla de Negocio"}:
        return f"[[{expr}]]"  # subroutine — rules
    if tipo in {"Hotspot"}:
        return f"{{{{{expr}}}}}"  # hexagon — hotspots
    if tipo in {"Actor"}:
        return f"([{expr}])"  # stadium — actors
    if tipo in {"Sistema Externo"}:
        return f"[({expr})]"  # cylinder — external systems
    if tipo in {"Agregado", "Entidad Raíz"}:
        return f"[{expr}]"  # rectangle — aggregates (highlighted via class)
    return f"[{expr}]"  # default rectangle (commands and others)
