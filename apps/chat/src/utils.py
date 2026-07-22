import os
import json
import glob
import chainlit as cl
from typing import Any
from src.services.progress_service import ProgressService
import logging
logger = logging.getLogger(__name__)

def load_html_template():
    template_path = os.path.join("public", "templates", "template.html")
    if not os.path.exists(template_path):
        # Fallback simple si no existe el archivo
        return """
        <div style="padding: 20px; text-align: center; color: red;">
            <h3>Error: Template not found</h3>
            <p>Please ensure public/template.html exists.</p>
        </div>
        """
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def load_html_template_suggestion():
    template_path = os.path.join("public", "templates", "template-suggestion.html")
    if not os.path.exists(template_path):
        # Fallback simple si no existe el archivo
        return """
        <div style="padding: 20px; text-align: center; color: red;">
            <h3>Error: Template not found</h3>
            <p>Please ensure public/template-suggestion.html exists.</p>
        </div>
        """
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def ensure_directories():
    """Asegura que existan los directorios necesarios."""
    dirs = [
        "public/templates", 
        "public/generated/audio", 
        "public/generated/suggestions", 
        "public/generated/translations",
        "data/user_progress",
        "debug_files"
    ]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"📁 Directorio creado: {d}")




async def safe_extract_llm_response(generator) -> str:
    content = ""
    try:
        # Maneja tanto generadores async como respuestas directas
        if hasattr(generator, '__aiter__'):
            async for response in generator:
                if isinstance(response, dict) and "choices" in response:
                    content += response["choices"][0]["message"]["content"]
                elif isinstance(response, str):
                    content += response
        else:
            return str(generator)
    except Exception as e:
        logger.error(f"Error extracting LLM response: {e}")
        return "Error."
    return content



class SessionManager:
    """Helper para manejar el estado de la sesión de forma segura y tipada."""
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        return cl.user_session.get(key, default)

    @staticmethod
    def set(key: str, value: Any):
        cl.user_session.set(key, value)

    @classmethod
    def update_history(cls, state: dict):    
        history = cls.get("conversation_history", [])
        new_messages = state.get("messages") or []
        history.extend(new_messages)
        history = history[-10:]

        cls.set("conversation_history", history)
        cls.set("current_mode", state.get("current_mode", "chat"))
   

    @classmethod
    def update(cls):
        """Actualiza variables críticas desde el estado final del grafo."""
        ps = ProgressService()
        user_progress =  ps.load_progress() or {}

        keys_to_sync = [
            "student_name", 
            "student_interests", 
            "student_goals", 
            "discovery_completed", 
            "user_memory"
        ]
        
        for key in keys_to_sync:
            cls.set(key, user_progress.get(key))

def build_progress_bar_string(level: str, topic: Any) -> str:
    """Genera el string visual de la barra de progreso."""
    
    # Extract topic string if it's a dict
    display_topic = topic
    if isinstance(topic, dict):
        display_topic = topic.get("topic", "Unknown Topic")
        
    try:
        progress_service = ProgressService()
        progress_info = progress_service.get_current_state()
        level_progress = progress_info.get('level_progress', {})
        
        level_pct = level_progress.get('percentage', 0)
        completed = level_progress.get('completed', 0)
        total = level_progress.get('total', 0)
        
        filled = int(level_pct / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        
        return (
            f"**📊 Current Level:** {level}\n"
            f"**Progress:** {bar} {level_pct}% ({completed}/{total} topics)\n"
            f"**📚 Topic:** {display_topic}"
        )
    except Exception as e:
        logger.error(f"Error building progress bar: {e}")
        return f"**📊 Level:** {level} | **Topic:** {display_topic}"

async def cleanup_previous_ui_elements():
    """Elimina sugerencias o traducciones antiguas para limpiar el chat."""
    keys = [
        "last_suggestion_id", 
        "last_translation_id", 
        "last_progress_id", 
        "last_saved_phrases_id",
        "last_review_topics_id",
        "last_topic_selection_id"
    ]
    for key in keys:
        msg_id = SessionManager.get(key)
        if msg_id:
            try:
                await cl.Message(content="", id=msg_id).remove()
            except Exception:
                pass # El mensaje ya no existe
            SessionManager.set(key, None)

def cleanup_generated_files():
    """Limpia archivos HTML generados (suggestions/translations) al iniciar nueva sesión."""
    try:
        # Patrones de archivos a eliminar
        patterns = [
            'public/suggestion_*.html',
            'public/translation_*.html',
            'public/audio_*.mp3'

        ]
        
        deleted_count = 0
        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                try:
                    os.remove(file)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} generated HTML files")
    except Exception as e:
        logger.error(f"Error during file cleanup: {e}")