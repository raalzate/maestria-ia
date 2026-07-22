import os
import uuid
import json
import re
import logging
import chainlit as cl
from src.llm import generate_response
from src.utils import safe_extract_llm_response, load_html_template_suggestion

logger = logging.getLogger(__name__)

async def generate_translation_html(english_text: str):
    """
    Genera un HTML interactivo con la traducción segmentada por frases lógicas.
    Optimizado para Llama-3-8B-Instruct.
    """
    
    # System instruction más directa para Llama 3
    system_instruction = (
        "You are a professional Spanish translator specialized in creating natural phrase groupings. "
        "You MUST group words into meaningful thought units, NOT translate word-by-word."
    )

    # User prompt con énfasis en frases completas
    user_prompt = (
        "TASK: Translate the following text into Spanish, keeping the meaning intact.\n"
        "RULES:\n"
        "1. Break the text into logical phrases (3-7 words).\n"
        "2. Format EXACTLY as: English Phrase[Spanish Translation]\n"
        "3. Do NOT include any introduction or explanation.\n"
        "4. Do NOT output the examples below, only translate the text.\n\n"
        f"### TEXT TO TRANSLATE\n{english_text}\n"
    )

    try:
        # Llamada al LLM
        response = await cl.make_async(generate_response)(
            f"{system_instruction}\n\n{user_prompt}",
            "Translation",
            max_tokens=2000  
        )
        
        raw_text = await safe_extract_llm_response(response)
        raw_text = re.sub(r'^(Output:|Response:|Here is the translation:|Here is the output:)', '', raw_text, flags=re.IGNORECASE).strip()        
        raw_text = raw_text.strip()
        logger.info(f"Translation Raw Output (cleaned): {english_text[:50]}... ==> {raw_text[:100]}...")

        # Parseo para formato: English|Spanish|
        breakdown = []
        
        # Dividimos por saltos de línea primero
        lines = raw_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Usar finditer para capturar todos los pares Texto[Traducción] en la línea
            # Relaxed regex: allows any char (likes spaces or |) before the bracket
            matches = re.finditer(r'(.+?)\[([^\]]+)\]', line)
            for match in matches:
                english_phrase = match.group(1).strip().strip('|').strip()
                spanish_translation = match.group(2).strip()
                
                if english_phrase and spanish_translation:
                    breakdown.append({
                        "word": english_phrase,
                        "phonetic": spanish_translation 
                    })
        
        if not breakdown:
            logger.error(f"Failed to parse translation output.")
            return "⚠️ _(Could not format translation)_"
        
        logger.info(f"Successfully parsed {len(breakdown)} translation segments")

        # Estructura de datos para el template
        translations_data = [{
            "type": "Traducción",
            "breakdown": breakdown
        }]

        # Generación de archivo HTML
        json_data = json.dumps(translations_data)
        html_template = load_html_template_suggestion()
        final_html = html_template.replace("__SUGGESTIONS_JSON__", json_data)

        filename = f"translation_{uuid.uuid4().hex[:8]}.html"
        public_dir = "public/generated/translations"
        os.makedirs(public_dir, exist_ok=True)
        
        filepath = os.path.join(public_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_html)
        
        return f"""<iframe src="/public/generated/translations/{filename}" 
                    style="width:100%; height:350px; border:none; border-radius:15px; background: transparent;" 
                    scrolling="yes"></iframe>"""

    except Exception as e:
        logger.error(f"Error in translation HTML generation: {e}")
        return "⚠️ _Error generating translation._"