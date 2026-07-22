import logging
import json
import os
import uuid
import re
import chainlit as cl
from src.llm import generate_response
from src.utils import load_html_template_suggestion, safe_extract_llm_response, SessionManager

logger = logging.getLogger(__name__)

async def generate_suggestions_html(last_message: str):
    """
    Genera sugerencias (Safe, Natural, Narrative) con traducción en lugar de fonética,
    agrupadas por frases con significado completo.
    """
    current_level = SessionManager.get("current_level", "Intermediate")
    topic = SessionManager.get("current_topic", "General Chat")
    
    # Instrucción de sistema enfocada en traducción natural
    system_instruction = (
        f"You are an English Fluency Coach. Level: {current_level}. "
        "Your goal is to provide response suggestions broken into meaningful phrases "
        "with their Spanish translations."
    )

    # Prompt ajustado para pedir TRADUCCIÓN en los corchetes
    user_prompt = (
        f"Topic: {topic}. Coach said: '{last_message}'.\n\n"
        "TASK: Generate EXACTLY 3 responses: Safe, Natural, Narrative.\n\n"
        "RULES:\n"
        "- EACH response must be ONE SINGLE LINE.\n"
        "- EACH response must contain 3–4 MEANINGFUL PHRASES (thought groups).\n"
        "- INSIDE BRACKETS: Provide the Spanish translation of that phrase (NOT phonetics).\n"
        "- FORMAT: Level | Phrase[Spanish Translation] | Phrase[Spanish Translation]\n"
        "- DO NOT add titles, explanations, or numbering.\n\n"
        "EXAMPLE:\n"
        "Safe | I agree with you[Estoy de acuerdo contigo] | that is a great point[ese es un gran punto] | for our team[para nuestro equipo].\n"
        "Natural | To be honest[Para ser honesto] | it's kind of tough[es un poco difícil] | to get it right[hacerlo bien].\n"
        "Narrative | While the idea is compelling[Aunque la idea es convincente] | it requires careful execution[requiere una ejecución cuidadosa] | to succeed[para tener éxito].\n\n"
        "OUTPUT ONLY THE 3 LINES."
    )

    try:
        response = await cl.make_async(generate_response)(
            f"{system_instruction}\n\n{user_prompt}", 
            "Thought Groups Suggestions",
            max_tokens=2000
        )
        
        raw_text = await safe_extract_llm_response(response)
        
        # Limpieza básica para evitar basura de Llama-3
        raw_text = re.sub(r'^(Output:|Response:|Here are the suggestions:)', '', raw_text, flags=re.IGNORECASE).strip()
        logger.info(f"Llama-3 Suggestion Output: {raw_text}")

        suggestions_data = []
        lines = raw_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if "|" not in line or "[" not in line:
                continue
            
            # Identificar el tipo de mensaje
            msg_type = "Suggestion"
            if "Safe" in line: msg_type = "Safe"
            elif "Natural" in line: msg_type = "Natural"
            elif "Narrative" in line: msg_type = "Narrative"

            parts = line.split("|")
            breakdown = []
            
            # El índice 0 es el Label (Safe/Natural...), los demás son las frases traducidas
            for part in parts[1:]:
                part = part.strip()
                if not part: continue
                
                # Regex para capturar Texto[Traducción]
                match = re.search(r'([^\[]+)\[([^\]]+)\]', part)
                if match:
                    phrase_text = match.group(1).strip()
                    phrase_translation = match.group(2).strip()
                    
                    breakdown.append({
                        "word": phrase_text,        # Texto en inglés
                        "phonetic": phrase_translation # Se guarda en 'phonetic' para que el HTML lo use como traducción
                    })
            
            if breakdown:
                suggestions_data.append({
                    "type": msg_type,
                    "breakdown": breakdown
                })

        if not suggestions_data:
            logger.error(f"Failed to parse suggestions. Raw: {raw_text[:200]}")
            return "⚠️ _(Could not format suggestions correctly)_"

        # Generar HTML usando el template existente
        json_data = json.dumps(suggestions_data)
        html_template = load_html_template_suggestion()
        final_html = html_template.replace("__SUGGESTIONS_JSON__", json_data)

        filename = f"suggestion_{uuid.uuid4().hex[:8]}.html"
        public_dir = "public"
        os.makedirs(public_dir, exist_ok=True)
            
        filepath = os.path.join(public_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_html)
        
        return f"""<iframe src="/public/{filename}" 
                    style="width:100%; height:450px; border:none; border-radius:15px; background: transparent;" 
                    scrolling="yes"></iframe>"""

    except Exception as e:
        logger.error(f"Error in phrase suggestions: {e}")
        return "⚠️ _Error generating phrase suggestions._"