"""
Figura 3 — Diagrama esquemático: Anatomía de una User-Persona.
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
    "rankdir": "LR",
    "nodesep": "0.35",
    "ranksep": "1.0",
}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "11"}
EDGE_ATTR = {"color": "#7A0E1F", "penwidth": "1.4"}

ATTR = dict(fillcolor="white", color="#C8102E", fontsize="10", fontcolor="#1a1a1a", margin="0.18,0.12")

with Diagram(
    "User-Persona — Anatomía",
    filename="../../../deliverables/diagrams_output/03_user_persona_anatomia",
    outformat="png",
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
    node_attr=NODE_ATTR,
    edge_attr=EDGE_ATTR,
):
    with Cluster("Atributos primarios", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        demograficos = text_node("Demográficos\n(edad, profesión,\ncontexto)", **ATTR)
        objetivos = text_node("Objetivos / Goals\n(qué quiere lograr)", **ATTR)
        pains = text_node("Pain points\n(frustraciones,\nbloqueos)", **ATTR)
        comportamiento = text_node("Comportamiento\n(hábitos, dispositivos)", **ATTR)

    persona = text_node(
        "USER-PERSONA\n(arquetipo del\nusuario)",
        shape="circle",
        fillcolor="#C8102E",
        color="#C8102E",
        fontcolor="white",
        fontsize="12",
        width="2.0",
        height="2.0",
        fixedsize="true",
    )

    with Cluster("Atributos contextuales", graph_attr={"bgcolor": "#fdf6f0", "style": "rounded", "color": "#7A0E1F", "fontcolor": "#7A0E1F"}):
        contexto = text_node("Contexto de uso\n(cuándo, dónde)", **ATTR)
        motivaciones = text_node("Motivaciones\n(control, eficiencia,\nconfianza)", **ATTR)
        cita = text_node('Cita representativa\n("verbatim")', **ATTR)
        skill = text_node("Skill / nivel\ntécnico", **ATTR)

    demograficos >> Edge(color="#C8102E", penwidth="1.6") >> persona
    objetivos >> Edge(color="#C8102E", penwidth="1.6") >> persona
    pains >> Edge(color="#C8102E", penwidth="1.6") >> persona
    comportamiento >> Edge(color="#C8102E", penwidth="1.6") >> persona

    persona >> Edge(color="#C8102E", penwidth="1.6") >> contexto
    persona >> Edge(color="#C8102E", penwidth="1.6") >> motivaciones
    persona >> Edge(color="#C8102E", penwidth="1.6") >> cita
    persona >> Edge(color="#C8102E", penwidth="1.6") >> skill
