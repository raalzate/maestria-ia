from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper

def curriculum_node(state: AgentState):
    """
    Generates new topics or learning paths based on user level.
    """
    level = state.get('user_level', 'Intermediate')
    llm = Llama3Wrapper()
    
    prompt = (
        f"Generate 3 practical English learning topics for a student at {level} level.\n"
        "Topics should be engaging and useful for daily life or work.\n"
        "Return ONLY a comma-separated list of topics."
    )
    
    topics = llm.invoke(prompt).strip()
    
    # Select the first one as the new current topic for simplicity, or just return suggestions
    # For now, we'll just update the current topic to the first suggestion
    new_topic = topics.split(',')[0].strip()
    
    return {"current_topic": new_topic}
