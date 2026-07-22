from langgraph.graph import StateGraph, END
from src.graph.state import AgentState

from src.graph.nodes.assessor import assessor_node
from src.graph.nodes.memory import memory_node
from src.graph.nodes.curriculum import curriculum_node
from src.graph.nodes.tutor import tutor_node
from src.graph.nodes.grammar_checker import grammar_node
from src.graph.nodes.networking_node import networking_node

# --- CONDITIONAL LOGIC FUNCTIONS ---

def route_after_memory(state):
    """
    Decide a dónde ir después de la memoria:
    1. Si hay error gramatical grave -> Tutor (Corrección inmediata)
    2. Si el usuario quiere charlar -> Networking
    3. Si es algo educativo o ambiguo -> Assessor (Análisis profundo)
    """
    if state.get("grammar_error"):
        return "tutor"
    
    # Direct routing for Roleplay Mode
    if state.get("current_mode") == "roleplay":
        return "tutor"
    
    messages = state.get('messages', [])
    if messages:
        last_message = messages[-1].content.lower()
        
        # Keywords básicas para desvío rápido
        chat_keywords = ['chat', 'talk', 'conversation', 'discuss', 'speak']
        lesson_keywords = ['lesson', 'teach', 'learn', 'practice', 'exercise', 'english']

        if any(keyword in last_message for keyword in lesson_keywords):
            return "assessor"  
        elif any(keyword in last_message for keyword in chat_keywords):
            return "networking"
            
    # Por defecto, dejamos que el Assessor decida la intención fina
    return "assessor"

def route_learning_flow(state):
    """
    Ruta después del Assessor.
    Basa la decisión en 'next_step' o keywords de cambio de tema.
    """
    # Prioridad 1: Si el Assessor ya determinó un cambio de tema explícito
    if state.get("next_step") == "new_topic":
        return "curriculum"
        
    # Prioridad 2: Análisis de fallback (por si el assessor no devolvió next_step claro)
    messages = state.get('messages', [])
    if not messages:
        return "tutor"
        
    last_message = messages[-1].content.lower().strip()
    trigger_phrases = [
        "next topic", 
        "change topic", 
        "new topic", 
        "let's continue",
        "skip this"
    ]

    if any(phrase in last_message for phrase in trigger_phrases):
        return "curriculum"
        
    # Por defecto, seguimos con la lección actual
    return "tutor" 

def route_after_tutor(state):
    """
    Revisa la salida del Tutor.
    - Si contiene [PASSED] -> El usuario aprobó -> Ir a Curriculum (Siguiente tema).
    - Si no -> Fin del turno (Esperar respuesta del usuario).
    """
    messages = state.get('messages', [])
    if not messages:
        return END
        
    # Verificamos el último mensaje generado por la IA (Tutor)
    last_ai_message = messages[-1].content
    
    if "[PASSED]" in last_ai_message:
        return "curriculum"
        
    return END

# --- MAIN GRAPH ---

def create_main_graph():
    """
    Main graph for post-onboarding flows.
    Handles: Networking (chat) and Learning (lessons)
    Used: Only when discovery_completed = True
    """
    workflow = StateGraph(AgentState)
    
    # --- 1. ADD NODES ---
    workflow.add_node("grammar", grammar_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("networking", networking_node)
    workflow.add_node("assessor", assessor_node)
    workflow.add_node("curriculum", curriculum_node)
    workflow.add_node("tutor", tutor_node)
    
    # --- 2. DEFINE ENTRY POINT ---
    workflow.set_entry_point("grammar")
    
    # --- 3. STANDARD EDGES ---
    # Grammar siempre pasa a Memory para guardar/procesar contexto
    workflow.add_edge("grammar", "memory")

    # Curriculum siempre pasa a Tutor (para enseñar el nuevo tema)
    workflow.add_edge("curriculum", "tutor")
    
    # Networking es un nodo terminal en este turno (espera input usuario)
    workflow.add_edge("networking", END)

    # --- 5. CONDITIONAL EDGES ---

    # Salida de Memory
    workflow.add_conditional_edges(
        "memory",
        route_after_memory,
        {
            "tutor": "tutor",
            "networking": "networking",
            "assessor": "assessor"
        }
    )
    
    # Salida de Assessor (Learning Flow)
    workflow.add_conditional_edges(
        "assessor",
        route_learning_flow,
        {
            "curriculum": "curriculum",
            "tutor": "tutor"
        }
    )

    # Salida de Tutor (CICLO DE APROBACIÓN)
    workflow.add_conditional_edges(
        "tutor",
        route_after_tutor,
        {
            "curriculum": "curriculum", # Loop automático si aprobó
            END: END                    # Esperar input si sigue enseñando
        }
    )
    
    return workflow.compile()