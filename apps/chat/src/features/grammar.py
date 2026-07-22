from transformers import pipeline
import asyncio

# Cache global del pipeline para no cargarlo en cada mensaje
_grammar_pipeline = None

def get_grammar_checker():
    """
    Carga el modelo T5 de corrección gramatical.
    Usa device=-1 para forzar CPU y evitar errores de 'Meta Tensors'.
    """
    global _grammar_pipeline
    if _grammar_pipeline is None:
        print("⏳ Loading Grammar Correction Pipeline (T5)...")
        try:
            # device=-1 es CRÍTICO aquí para evitar el error de tensores
            _grammar_pipeline = pipeline(
                "text2text-generation",
                model="vennify/t5-base-grammar-correction",
                device=-1 
            )
            print("✅ Grammar Pipeline Loaded on CPU")
        except Exception as e:
            print(f"❌ Error loading T5 pipeline: {e}")
            return None
            
    return _grammar_pipeline

def _check_grammar_sync(text):
    """
    Versión síncrona que ejecuta el pipeline.
    """
    pipe = get_grammar_checker()
    
    if not pipe:
        # Si falla la carga, devolvemos que no hubo errores para no romper el chat
        return text, False, []
    
    # El prefijo 'grammar: ' es necesario para este modelo específico
    input_text = f"grammar: {text}"
    
    try:
        # Ejecución del modelo
        results = pipe(
            input_text, 
            max_new_tokens=512, 
            num_beams=4,      # Mayor calidad en la corrección
            early_stopping=True
        )
        corrected_text = results[0]['generated_text']
    except Exception as e:
        print(f"❌ Error during grammar check execution: {e}")
        return text, False, []
    
    # Limpieza básica para comparación
    original_clean = text.strip()
    corrected_clean = corrected_text.strip()
    
    # Detectar si hay cambios (ignorando mayúsculas/minúsculas para la detección de error)
    # Nota: Comparamos lower() para detectar si hay error, pero devolvemos el texto corregido con su case real.
    has_errors = original_clean.lower() != corrected_clean.lower()
    
    corrections = []
    if has_errors:
        corrections.append({
            "original": original_clean,
            "corrected": corrected_clean
        })
    
    return corrected_clean, has_errors, corrections

async def check_grammar(text):
    """
    Wrapper asíncrono para no bloquear el bucle de eventos de Chainlit.
    """
    return await asyncio.to_thread(_check_grammar_sync, text)