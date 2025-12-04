import os
from llama_cpp import Llama

# Configuración del modelo
MODEL_PATH = "/Users/raul.alzate/.lmstudio/models/NikolayKozloff/Meta-Llama-3-8B-Instruct-bf16-correct-pre-tokenizer-and-EOS-token-Q8_0-Q6_k-Q4_K_M-GGUF/Meta-Llama-3-8B-Instruct-bf16-correct-pre-tokenizer-and-EOS-token-Q4_K_M.gguf"

_llm_cache = None

def get_llm():
    global _llm_cache
    if _llm_cache is None:
        if not os.path.exists(MODEL_PATH):
            print(f"❌ Error: Modelo no encontrado en {MODEL_PATH}")
            return None
        print("⏳ Loading Llama-3...")
        # n_gpu_layers=-1 usa toda la GPU disponible (si aplica)
        # n_ctx=4096 es el contexto estándar de Llama 3
        _llm_cache = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=4096, verbose=False)
    return _llm_cache

async def generate_response(user_input, system_prompt="You are a helpful assistant.", is_sync=False):
    """
    Genera una respuesta usando el modelo Llama.
    Retorna un generador asíncrono para streaming.
    Si is_sync=True, funciona de forma síncrona (para corrección gramatical).
    """
    llm = get_llm()
    if not llm:
        yield "Error: Modelo no cargado."
        return

    stream = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=500,
        stream=True,
        stop=["<|eot_id|>"]
    )
    
    for chunk in stream:
        if "choices" in chunk:
            token = chunk["choices"][0]["delta"].get("content", "")
            if token:
                yield token
