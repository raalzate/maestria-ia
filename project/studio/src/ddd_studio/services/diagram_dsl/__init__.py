"""Builders that translate a DomainAnalysis into vector-friendly diagram DSLs.

Each module exposes a `build(analysis: DomainAnalysis) -> str` returning Mermaid
source ready to be rendered to PDF via Kroki. The DSL approach removes the
saturation problem of dumping the full graph into one Graphviz canvas.
"""
