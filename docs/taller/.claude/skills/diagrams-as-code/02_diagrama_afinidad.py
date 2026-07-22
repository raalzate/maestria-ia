"""
Figura 2 — Mapa conceptual: Elementos del Diagrama de Afinidad.
Diagram as Code (mingrammer/diagrams) — paleta Univalle.
"""
from diagrams import Diagram, Cluster, Edge
from _helpers import text_node

GRAPH_ATTR = {
    "bgcolor": "white",
    "fontname": "Helvetica",
    "fontsize": "14",
    "pad": "0.4",
    "splines": "ortho",
    "rankdir": "TB",
    "nodesep": "0.3",
    "ranksep": "0.55",
}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "10"}
EDGE_ATTR = {"color": "#7A0E1F", "penwidth": "1.4"}

LEAF = dict(fillcolor="#fef9f0", color="#D4A24C", fontsize="9", margin="0.16,0.10")
HEAD = dict(fillcolor="#C8102E", fontcolor="white", color="#C8102E", fontsize="11", margin="0.20,0.14")

with Diagram(
    "Diagrama de Afinidad — Mapa Conceptual",
    filename="../../../deliverables/diagrams_output/02_diagrama_afinidad",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=GRAPH_ATTR,
    node_attr=NODE_ATTR,
    edge_attr=EDGE_ATTR,
):
    raiz = text_node(
        "Diagrama\nde Afinidad",
        shape="ellipse",
        fillcolor="#7A0E1F",
        color="#7A0E1F",
        fontcolor="white",
        fontsize="13",
        width="2.2",
        height="0.9",
        fixedsize="true",
    )

    with Cluster("Insumos", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        ins_h = text_node("Insumos", **HEAD)
        i1 = text_node("Notas atómicas\n(1 idea = 1 sticky)", **LEAF)
        i2 = text_node("Verbatims /\nobservaciones", **LEAF)
        i3 = text_node("Codificación\ninicial", **LEAF)
        ins_h >> Edge(style="dotted") >> i1
        ins_h >> Edge(style="dotted") >> i2
        ins_h >> Edge(style="dotted") >> i3

    with Cluster("Proceso", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        proc_h = text_node("Proceso", **HEAD)
        p1 = text_node("Agrupación\nbottom-up silenciosa", **LEAF)
        p2 = text_node("Iteración hasta\nsaturación", **LEAF)
        p3 = text_node("Resolución de\nconflictos", **LEAF)
        proc_h >> Edge(style="dotted") >> p1
        proc_h >> Edge(style="dotted") >> p2
        proc_h >> Edge(style="dotted") >> p3

    with Cluster("Estructura", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        est_h = text_node("Estructura", **HEAD)
        e1 = text_node("Etiqueta\nde cluster", **LEAF)
        e2 = text_node("Subgrupos y\nmeta-grupos", **LEAF)
        e3 = text_node("Trazabilidad\nnota↔fuente", **LEAF)
        est_h >> Edge(style="dotted") >> e1
        est_h >> Edge(style="dotted") >> e2
        est_h >> Edge(style="dotted") >> e3

    with Cluster("Salida", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        sal_h = text_node("Salida", **HEAD)
        s1 = text_node("Insights\npriorizados", **LEAF)
        s2 = text_node("Hipótesis\nde diseño", **LEAF)
        s3 = text_node("Insumo para\nUser-Personas", **LEAF)
        sal_h >> Edge(style="dotted") >> s1
        sal_h >> Edge(style="dotted") >> s2
        sal_h >> Edge(style="dotted") >> s3

    raiz >> Edge(color="#C8102E", penwidth="2") >> ins_h
    raiz >> Edge(color="#C8102E", penwidth="2") >> proc_h
    raiz >> Edge(color="#C8102E", penwidth="2") >> est_h
    raiz >> Edge(color="#C8102E", penwidth="2") >> sal_h
