from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper

def memory_node(state: AgentState):
    """
    Extracts relevant information (vocabulary, user details) to update long-term memory.
    """
    messages = state['messages']
    last_message = messages[-1].content
    current_memory = state.get('user_memory', [])
    
    llm = Llama3Wrapper()
    
    # Prompt to extract memory items
    prompt = (
        f"Analyze this message: '{last_message}'\n"
        "Identify if there are any NEW English words the user is trying to learn or specific personal details mentioned.\n"
        "Return a comma-separated list of items to remember (e.g., 'vocabulary: apple', 'user_fact: likes cats').\n"
        "If nothing worth remembering, return 'NONE'."
    )
    
    result = llm.invoke(prompt).strip()
    
    new_memories = []
    if result != "NONE":
        items = [item.strip() for item in result.split(',')]
        new_memories = items
        
    # Update state
    return {"user_memory": new_memories}
