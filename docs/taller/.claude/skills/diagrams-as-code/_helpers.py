"""
Helpers para crear nodos de texto puro en diagrams (sin icono fantasma).
"""
from diagrams.generic.blank import Blank


def text_node(label, **kwargs):
    """Nodo Blank con texto centrado, sin icono invisible que desplace el label."""
    defaults = dict(
        image="",
        labelloc="c",
        imagepos="",
        imagescale="false",
        shape="box",
        style="rounded,filled",
        fillcolor="white",
        color="#d1d1d1",
        fontname="Helvetica",
        fontsize="10",
        fontcolor="#1a1a1a",
        margin="0.18,0.12",
        height="0.5",
        width="1.6",
        fixedsize="false",
    )
    defaults.update(kwargs)
    return Blank(label, **defaults)
