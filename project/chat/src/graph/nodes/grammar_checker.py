from src.graph.state import AgentState
from src.grammar import check_grammar
from langchain_core.messages import AIMessage 

async def grammar_node(state: AgentState):
    """
    Checks the latest user message for grammar errors.
    If found, returns the correction immediately.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    # Check grammar
    corrected_text, has_errors, corrections = await check_grammar(last_message)
    
    if has_errors:
        # Construimos la respuesta de corrección aquí mismo
        feedback_msg = f"🤓 I noticed a small mistake. Here is the corrected version:\n\n**{corrected_text}**"
        
        return {
            "grammar_error": True,
            "correction": corrected_text,
            "messages": [AIMessage(content=feedback_msg)] 
        }
    
    # Si no hay errores, seguimos normal sin añadir mensajes
    return {
        "grammar_error": False,
        "correction": ""
    }