from src.llm import generate_response

async def check_grammar(text):
    """
    Check and correct grammar using Llama-3 LLM.
    Returns (corrected_text, has_errors, corrections_list)
    """
    # Usar Llama-3 para corrección gramatical
    grammar_prompt = (
        f"Check this English sentence for grammar errors and provide ONLY the corrected version:\n\n"
        f"Original: {text}\n\n"
        f"Rules:\n"
        f"- If the sentence is grammatically correct, return it EXACTLY as is\n"
        f"- If there are errors, return ONLY the corrected sentence\n"
        f"- Do NOT add explanations or extra text\n"
        f"- Keep the same meaning and style\n\n"
        f"Corrected:"
    )
    
    corrected_text = ""
    
    # Generar corrección
    async for token in generate_response(grammar_prompt, "You are a grammar expert. Reply only with the corrected sentence."):
        corrected_text += token
    
    corrected_text = corrected_text.strip()
    
    # Detectar si hay cambios significativos
    has_errors = text.strip().lower() != corrected_text.strip().lower()
    
    corrections = []
    if has_errors:
        corrections.append({
            "original": text,
            "corrected": corrected_text
        })
    
    return corrected_text, has_errors, corrections
