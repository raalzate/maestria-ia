from src.graph.state import AgentState
from src.grammar import check_grammar

async def grammar_node(state: AgentState):
    """
    Checks the latest user message for grammar errors.
    """
    messages = state['messages']
    last_message = messages[-1].content
    
    # Check grammar
    corrected_text, has_errors, corrections = await check_grammar(last_message)
    print("Corrected Text:", corrected_text)
    print("Has Errors:", has_errors)
    print("Corrections:", corrections)
    return {
        "grammar_error": has_errors,
        "correction": corrected_text if has_errors else "",
        "is_lesson": False if has_errors else state.get("is_lesson", False)
    }
