"""
Figura 1 — Mapa mental: Recomendaciones para entrevistas de usuarios.
Diagram as Code (mingrammer/diagrams) — paleta Univalle.
"""
from diagrams import Diagram, Cluster, Edge
from _helpers import text_node

GRAPH_ATTR = {
    "bgcolor": "white",
    "fontname": "Helvetica",
    "fontsize": "14",
    "pad": "0.4",
    "splines": "curved",
    "rankdir": "TB",
    "nodesep": "0.35",
    "ranksep": "0.7",
}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "11"}
EDGE_ATTR = {"color": "#7A0E1F", "penwidth": "1.6"}

LEAF = dict(fillcolor="white", color="#D4A24C", fontsize="9", margin="0.16,0.10")
HEAD = dict(fillcolor="#7A0E1F", fontcolor="white", fontsize="11", color="#7A0E1F", margin="0.20,0.14")

with Diagram(
    "Entrevista Efectiva — Recomendaciones",
    filename="../../../deliverables/diagrams_output/01_recomendaciones_entrevista",
    outformat="png",
    show=False,
    direction="TB",
    graph_attr=GRAPH_ATTR,
    node_attr=NODE_ATTR,
    edge_attr=EDGE_ATTR,
):
    centro = text_node(
        "Entrevista\nEfectiva",
        shape="circle",
        fillcolor="#C8102E",
        color="#C8102E",
        fontcolor="white",
        fontsize="13",
        width="1.5",
        height="1.5",
        fixedsize="true",
    )

    with Cluster("1. Preparación", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#C8102E", "fontcolor": "#C8102E"}):
        h1 = text_node("Preparación", **HEAD)
        p1 = text_node("Investigar contexto\ndel entrevistado", **LEAF)
        p2 = text_node("Guía con preguntas\nabiertas + sondeos", **LEAF)
        p3 = text_node("Pilotaje previo", **LEAF)
        h1 >> Edge(style="dotted", color="#7A0E1F") >> p1
        h1 >> Edge(style="dotted", color="#7A0E1F") >> p2
        h1 >> Edge(style="dotted", color="#7A0E1F") >> p3

    with Cluster("2. Rapport", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#C8102E", "fontcolor": "#C8102E"}):
        h2 = text_node("Rapport", **HEAD)
        r1 = text_node("Tono cálido,\nlenguaje del usuario", **LEAF)
        r2 = text_node("Pregunta de\ncalentamiento", **LEAF)
        r3 = text_node("Empatía sin\ncondescendencia", **LEAF)
        h2 >> Edge(style="dotted", color="#7A0E1F") >> r1
        h2 >> Edge(style="dotted", color="#7A0E1F") >> r2
        h2 >> Edge(style="dotted", color="#7A0E1F") >> r3

    with Cluster("3. Escucha activa", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#C8102E", "fontcolor": "#C8102E"}):
        h3 = text_node("Escucha activa", **HEAD)
        e1 = text_node("Silencios\nproductivos", **LEAF)
        e2 = text_node("Parafrasear\npara validar", **LEAF)
        e3 = text_node("Observar\nno verbal", **LEAF)
        h3 >> Edge(style="dotted", color="#7A0E1F") >> e1
        h3 >> Edge(style="dotted", color="#7A0E1F") >> e2
        h3 >> Edge(style="dotted", color="#7A0E1F") >> e3

    with Cluster("4. Sondeos", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#C8102E", "fontcolor": "#C8102E"}):
        h4 = text_node("Sondeos", **HEAD)
        s1 = text_node('"Cuéntame más\nsobre eso"', **LEAF)
        s2 = text_node("5 Whys ante\nrespuestas vagas", **LEAF)
        s3 = text_node("Pedir incidente\ncrítico reciente", **LEAF)
        h4 >> Edge(style="dotted", color="#7A0E1F") >> s1
        h4 >> Edge(style="dotted", color="#7A0E1F") >> s2
        h4 >> Edge(style="dotted", color="#7A0E1F") >> s3

    with Cluster("5. Cierre y registro", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#C8102E", "fontcolor": "#C8102E"}):
        h5 = text_node("Cierre y registro", **HEAD)
        c1 = text_node("Síntesis del\nentrevistado", **LEAF)
        c2 = text_node("Notas inmediatas\n+ grabación", **LEAF)
        h5 >> Edge(style="dotted", color="#7A0E1F") >> c1
        h5 >> Edge(style="dotted", color="#7A0E1F") >> c2

    centro >> Edge(color="#C8102E", penwidth="2") >> h1
    centro >> Edge(color="#C8102E", penwidth="2") >> h2
    centro >> Edge(color="#C8102E", penwidth="2") >> h3
    centro >> Edge(color="#C8102E", penwidth="2") >> h4
    centro >> Edge(color="#C8102E", penwidth="2") >> h5
