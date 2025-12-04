from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper

def assessor_node(state: AgentState):
    """
    Analyzes the user's input to determine the intent and potential level changes.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    llm = Llama3Wrapper()
    
    # Prompt to assess intent
    prompt = (
        f"Analyze this user message: '{last_message}'\n"
        "Determine the intent:\n"
        "1. REQUEST: User is asking for specific learning content (e.g., 'teach me', 'explain', 'list').\n"
        "2. CHAT: User is just chatting or greeting.\n"
        "3. TOPIC_CHANGE: User wants to change the topic.\n"
        "\n"
        "Reply ONLY with one word: REQUEST, CHAT, or TOPIC_CHANGE."
    )
    
    intent = llm.invoke(prompt).strip().upper()
    print(intent)
    # Determinar si es lección
    is_lesson = "REQUEST" in intent
    
    # Map intent to next step
    if "REQUEST" in intent:
        next_step = "teach"
    elif "TOPIC_CHANGE" in intent:
        next_step = "new_topic"
    else:
        next_step = "chat"
        
    return {
        "next_step": next_step,
        "is_lesson": is_lesson
    }
