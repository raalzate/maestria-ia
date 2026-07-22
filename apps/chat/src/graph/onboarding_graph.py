from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes.grammar_checker import grammar_node
from src.graph.nodes.memory import memory_node
from src.graph.nodes.onboarding_node import onboarding_node

def create_onboarding_graph():
    """
    Dedicated graph for onboarding flow.
    Purpose: Collect user profile (name, interests, goals)
    Used: Only when discovery_completed = False
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("onboarding", onboarding_node)
    
    # Define entry point
    workflow.set_entry_point("grammar")
    
    # --- CONDITIONAL LOGIC ---
    def route_grammar(state):
        """
        Si grammar detecta error -> Termina (devuelve corrección).
        Si no -> Pasa a memoria y sigue el onboarding.
        """
        if state.get("grammar_error"):
            return END
        return "memory"

    # Reemplazamos workflow.add_edge("grammar", "memory") por:
    workflow.add_conditional_edges(
        "grammar",
        route_grammar,
        {
            END: END,           # Finaliza el turno si hay error
            "memory": "memory"  # Continúa flujo normal
        }
    )
    
    # --- STANDARD EDGES ---
    # El resto del flujo sigue lineal si pasó la gramática
    workflow.add_edge("memory", "onboarding")
    workflow.add_edge("onboarding", END)
    
    return workflow.compile()