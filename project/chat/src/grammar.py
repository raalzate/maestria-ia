from transformers import pipeline
import asyncio

# Cache del pipeline
_grammar_pipeline = None

def get_grammar_checker():
    global _grammar_pipeline
    if _grammar_pipeline is None:
        print("⏳ Loading Grammar Correction Pipeline (T5)...")
        try:
            # device=-1 fuerza el uso de CPU y evita problemas de MPS/Meta
            _grammar_pipeline = pipeline(
                "text2text-generation",
                model="vennify/t5-base-grammar-correction",
                device=-1 
            )
        except Exception as e:
            print(f"❌ Error loading T5 pipeline: {e}")
            return None
            
    return _grammar_pipeline

def _check_grammar_sync(text):
    """Synchronous version of grammar check using pipeline."""
    pipe = get_grammar_checker()
    
    if not pipe:
        return text, False, []
    
    # Generar corrección
    input_text = f"grammar: {text}"
    try:
        results = pipe(input_text, max_length=512, num_beams=4, early_stopping=True)
        corrected_text = results[0]['generated_text']
    except Exception as e:
        print(f"❌ Error during grammar check: {e}")
        return text, False, []
    
    # Detectar si hay cambios
    has_errors = text.strip().lower() != corrected_text.strip().lower()
    
    corrections = []
    if has_errors:
        corrections.append({
            "original": text,
            "corrected": corrected_text
        })
    
    return corrected_text, has_errors, corrections

async def check_grammar(text):
    """
    Check and correct grammar using T5 pipeline (Async wrapper).
    Returns (corrected_text, has_errors, corrections_list)
    """
    return await asyncio.to_thread(_check_grammar_sync, text)
