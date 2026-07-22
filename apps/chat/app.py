import os
import tempfile
import hashlib
import chainlit as cl
from fastapi.staticfiles import StaticFiles
from chainlit.server import app
from src.config import logger
from src.features.tts import generate_audio_bytes
from src.utils import ensure_directories

# 1. Directorios y Rutas Estáticas
ensure_directories()
AUDIO_TEMP_DIR = os.path.join(tempfile.gettempdir(), "maestria_audio")
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

app.mount("/public", StaticFiles(directory="public"), name="public")
app.mount("/public_audio", StaticFiles(directory=AUDIO_TEMP_DIR), name="public_audio")

# 2. API de TTS (Text-to-Speech)
@app.get("/api/tts")
async def api_tts(text: str):
    try:
        text_clean = text.strip()
        filename_hash = hashlib.md5(text_clean.encode('utf-8')).hexdigest()
        filename = f"audio_{filename_hash}.mp3"
        filepath = os.path.join(AUDIO_TEMP_DIR, filename)
        
        if os.path.exists(filepath):
            return {"url": f"/public_audio/{filename}"}

        audio_bytes = await generate_audio_bytes(text)
        if not audio_bytes:
            return {"error": "Failed to generate audio"}
            
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
            
        return {"url": f"/public_audio/{filename}"}
    except Exception as e:
        logger.error(f"TTS API Error: {e}")
        return {"error": str(e)}

@app.post("/api/save_phrase")
async def api_save_phrase(payload: dict):
    try:
        text = payload.get("text")
        if not text:
            return {"error": "No text provided"}
        
        from src.services.progress_service import ProgressService
        ps = ProgressService()
        added = ps.add_saved_phrase(text)
        return {"success": True, "added": added}
    except Exception as e:
        logger.error(f"Save Phrase Error: {e}")
        return {"error": str(e)}

@app.get("/api/get_saved_phrases")
async def api_get_saved_phrases():
    try:
        from src.services.progress_service import ProgressService
        ps = ProgressService()
        phrases = ps.get_saved_phrases()
        return {"phrases": phrases}
    except Exception as e:
        logger.error(f"Get Phrases Error: {e}")
        return {"error": str(e)}

def prioritize_route(path: str):
    target_route = None
    for r in app.router.routes:
        if getattr(r, "path", "") == path:
            target_route = r
            break
    if target_route:
        app.router.routes.remove(target_route)
        app.router.routes.insert(0, target_route)

prioritize_route("/api/tts")
prioritize_route("/public_audio")

# 3. Importación de Handlers (Se deben importar al final para registrar los eventos)
import src.audio.handlers
import src.chat
import src.actions