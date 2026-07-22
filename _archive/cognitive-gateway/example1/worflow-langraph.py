from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from dotenv import load_dotenv
import operator

load_dotenv()

# =========================
#  CONFIGURAR LLM
# =========================
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=20,  # 🔹 respuesta breve
)

# =========================
#  TOOLS
# =========================
@tool
def consultar_inventario(item_count: int) -> str:
    """Consulta el inventario actual."""
    print(f"🧰 Ejecutando tool: consultar_inventario({item_count})")
    return (
        "⚠️ Reabastecer pronto." if item_count >= 5 else "✅ Inventario estable."
    )

tools = [consultar_inventario]

# Crear versión del LLM con tools disponibles
llm_with_tools = llm.bind_tools(tools)

# =========================
#  ESTADO GLOBAL
# =========================
class State(TypedDict):
    messages: Annotated[list, operator.add]
    item_count: int

# =========================
#  NODOS
# =========================
def increment_node(state: State) -> dict:
    count = state.get("item_count", 0) + 1
    return {"messages": [f"🛒 {count} items procesados."], "item_count": count}

def recommendations_node(state: State) -> dict:
    """LLM decide si usar herramientas."""
    messages = [
        SystemMessage(content="Eres un asistente de inventario. Puedes usar herramientas para consultar inventario o registrar eventos. No des explicaciones, solo actúa."),
        HumanMessage(content=f"Hay {state['item_count']} items procesados. Evalúa el inventario y actúa si es necesario."),
    ]
    res = llm_with_tools.invoke(messages)
    return {"messages": [res]}

def result_node(state: State) -> dict:
    return {"messages": [f"📦 Total: {state['item_count']} items."]}

# =========================
#  GRAFO
# =========================
workflow = StateGraph(State)
workflow.add_node("increment", increment_node)
workflow.add_node("llm_analysis", recommendations_node)
workflow.add_node("check", ToolNode(tools=tools))
workflow.add_node("result", result_node)

# =========================
#  CONDICIONES
# =========================
workflow.set_entry_point("increment")
workflow.add_edge("increment", "llm_analysis")
workflow.add_edge("llm_analysis", "check")
workflow.add_conditional_edges(
    "check",
    lambda s: "result" if s["item_count"] >= 5 else "increment",
    {"result": "result", "increment": "increment"},
)
workflow.add_edge("result", END)

# =========================
#  EJECUCIÓN
# =========================
app = workflow.compile()

result = app.invoke({"messages": [], "item_count": 0})

print("\n🧾 RESULTADOS DEL FLUJO:\n")
for m in result["messages"]:
    if isinstance(m, AIMessage):
        print(f"🤖 {m.content}")
    else:
        print("-", m)
