"""Streamlit wrapper that embeds the React Flow viewer with a given payload."""

from __future__ import annotations

import json
from typing import Any

import streamlit.components.v1 as components

from .react_flow_template import TEMPLATE


def render_react_flow(payload: dict[str, Any], *, height: int = 720) -> None:
    """Inject the React Flow payload into the HTML viewer and embed it."""
    safe_json = json.dumps(payload, ensure_ascii=False, default=_json_default)
    # The template uses str.format with {payload_json} as the only single-brace
    # placeholder; every CSS/JS literal brace is escaped with {{ / }} already.
    html = TEMPLATE.format(payload_json=safe_json)
    components.html(html, height=height + 20, scrolling=False)


def _json_default(obj):
    # Defensive fallback for unusual values; the payload should already be primitives.
    try:
        return str(obj)
    except Exception:
        return None
