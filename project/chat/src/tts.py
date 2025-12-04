import os
import re
import json
import uuid
import base64
import edge_tts
from .utils import load_html_template

async def create_simple_audio(text):
    """
    Genera solo un archivo de audio MP3 usando EdgeTTS.
    Retorna la URL relativa del archivo generado.
    """
    # Limpiar texto de markdown básico
    clean_text = re.sub(r"[*_`]", "", text).strip()
    if not clean_text: 
        return None

    # Usamos una voz de alta calidad en inglés
    communicate = edge_tts.Communicate(clean_text, "en-US-EmmaNeural")
    audio_data = b""
    
    # Obtener solo el audio
    async for message in communicate.stream():
        if message["type"] == "audio":
            audio_data += message["data"]

    if not audio_data: 
        return None

    # Guardar archivo de audio
    filename = f"audio_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join("public", filename)
    
    if not os.path.exists("public"):
        os.makedirs("public")
        
    with open(filepath, "wb") as f:
        f.write(audio_data)
    
    return f"/public/{filename}"

async def create_interpreter_page(text):
    """
    Genera un archivo HTML con audio sincronizado (intérprete) usando EdgeTTS.
    Retorna la URL relativa del archivo generado.
    """
    # Limpiar texto de markdown básico para que el TTS no lea asteriscos
    clean_text = re.sub(r"[*_`]", "", text).strip()
    if not clean_text: 
        return None

    # Usamos una voz de alta calidad en inglés
    communicate = edge_tts.Communicate(clean_text, "en-US-EmmaNeural")
    audio_data = b""
    word_map = []
    
    # Procesar stream de TTS para obtener audio y tiempos de palabras
    async for message in communicate.stream():
        if message["type"] == "audio":
            audio_data += message["data"]
        elif message["type"] == "SentenceBoundary":
            # EdgeTTS devuelve offset y duration en ticks (1 tick = 100ns)
            # Dividimos por 10,000,000 para obtener segundos
            start = message["offset"] / 10_000_000
            dur = message["duration"] / 10_000_000
            word_map.append({
                "word": message["text"], 
                "start": start, 
                "end": start + dur
            })

    if not audio_data: 
        return None

    # Codificar audio en Base64 para incrustarlo directamente en el HTML
    b64_audio = base64.b64encode(audio_data).decode()
    json_map = json.dumps(word_map)
    
    # Cargar template y reemplazar placeholders
    html_content = load_html_template()
    final_html = html_content.replace("__B64_AUDIO__", b64_audio).replace("__WORD_MAP__", json_map)

    # Guardar archivo único
    filename = f"interpreter_{uuid.uuid4().hex[:8]}.html"
    filepath = os.path.join("public", filename)
    
    # Asegurar que public existe
    if not os.path.exists("public"):
        os.makedirs("public")
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    return f"/public/{filename}"
