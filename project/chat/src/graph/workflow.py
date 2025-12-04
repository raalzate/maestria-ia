from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes.assessor import assessor_node
from src.graph.nodes.memory import memory_node
from src.graph.nodes.curriculum import curriculum_node
from src.graph.nodes.tutor import tutor_node

from src.graph.nodes.grammar_checker import grammar_node

def create_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("assessor", assessor_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("curriculum", curriculum_node)
    workflow.add_node("tutor", tutor_node)
    
    # Define edges
    workflow.set_entry_point("grammar")
    
    # Grammar check routing
    def route_grammar(state):
        if state.get("grammar_error"):
            return "tutor" # Go directly to tutor for correction
        return "assessor" # Continue normal flow
        
    workflow.add_conditional_edges(
        "grammar",
        route_grammar,
        {
            "tutor": "tutor",
            "assessor": "assessor"
        }
    )
    
    workflow.add_edge("assessor", "memory")
    
    # Conditional edge logic for topic
    def route_step(state):
        if state.get("next_step") == "new_topic":
            return "curriculum"
        return "tutor"
        
    workflow.add_conditional_edges(
        "memory",
        route_step,
        {
            "curriculum": "curriculum",
            "tutor": "tutor"
        }
    )
    
    workflow.add_edge("curriculum", "tutor")
    workflow.add_edge("tutor", END)
    
    return workflow.compile()
