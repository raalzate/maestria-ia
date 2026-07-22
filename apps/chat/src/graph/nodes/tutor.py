from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
from src.features.tts import create_interpreter_page, create_simple_audio
import logging
import json
from src.config import CURRICULUM

# Configurar logger
logger = logging.getLogger(__name__)

# --- 1. PROMPTS OPTIMIZED FOR LLAMA-3 ---
PROMPT_TEMPLATES = {
    "grammar_error": (
        "### SYSTEM ###\n"
        "You are Emma, a Senior Tech Lead and English Coach.\n"
        "Task: Identify the grammar error in the developer's input and help them fix it.\n"
        "Context: Technical discussion or Daily Stand-up.\n\n"
        "### USER INPUT ###\n"
        "\"{last_message}\"\n\n"
        "### INSTRUCTIONS ###\n"
        "1. Identify the grammar error.\n"
        "2. Provide the corrected sentence in **bold**.\n"
        "3. Explain the rule briefly, relating it to technical clarity if possible.\n"
        "4. Ask the user to rewrite it.\n\n"
        "### FORMAT ###\n"
        "Correction: [Corrected Sentence]\n"
        "Why: [Short Explanation]\n"
        "Try it: [Instruction]\n"
        "Limit: Under 40 words."
    ),
    "teach": (
        "### SYSTEM ###\n"
        "Role: Emma, Senior Technical Lead & English Coach.\n"
        "Student Context: Name: {student_name} | Interests: {student_interests} | Goals: {student_goals}\n"
        "Current Topic: \"{current_topic}\"\n"
        "{example_context}"
        "Last Response: \"{last_ai_content}\"\n"
        "User Input: \"{last_message}\"\n\n"
    
        "### AUDIO CONSTRAINTS ###\n"
        "1. VOICE ONL CONVERSATION.\n"
        "2. NO fill-in-the-blanks or multiple choice.\n\n"

        "### INSTRUCTIONS (SIMULATION MODE) ###\n"
        "1. **Act the Part**: You are simulating a workplace scenario related to \"{current_topic}\".\n"
        "   - E.g., if topic is 'Daily Stand-up', act as the Scrum Master.\n"
        "   - If topic is 'Code Review', act as a Reviewer.\n"
        "2. **Natural Correction**: Correct mistakes gently *inside* the roleplay. Don't break character abruptly.\n"
        "3. **Teach**: Explain the concept briefly if they are stuck.\n"
        "4. **Next Step**: Push the simulation forward. Ask a relevant technical question or for a status update.\n"
        "5. **Tag**: If the user handles the scenario well, append '[PASSED]' at the end.\n\n"

        "### FORMAT ###\n"
        "[Roleplay Response / Gentle Correction]\n"
        "[Brief Explanation (Optional)]\n"
        "[Next Simulation Step/Question]"
    ),
    "evaluate_lesson": (
        "### SYSTEM ###\n"
        "Context: Validating a developer's response for topic \"{current_topic}\".\n"
        "Last Response: \"{last_ai_content}\"\n"
        "User Input: \"{last_message}\"\n\n"
        "### LOGIC ###\n"
        "1. **Evaluate**: Is the grammar correct? Is the technical terminology used correctly?\n"
        "2. **If Correct**: 'Great update!' or 'Good explanation.'. Then move to the next edge case or scenario.\n"
        "3. **If Incorrect**: Explain the error (grammar or technical clarity). Ask to retry.\n\n"
        "Limit: Under 50 words."
    ),
    "new_topic": (
        "### SYSTEM ###\n"
        "Role: Emma, Tech Lead. Level: {current_level}. Topic: {current_topic}.\n"
        "Action: Start a new workplace simulation.\n"
        "1. Set the scene: 'Okay, let's start our {current_topic}. I'll be your [Role].'\n"
        "2. Start with a direct question or prompt suitable for that scenario."
    ),
    "roleplay": (
        "### SYSTEM ###\n"
        "You are participating in a **Roleplay Simulation** about \"{current_topic}\".\n"
        "User Context: {student_name} ({current_level})\n\n"
        "### TASK ###\n"
        "1. **Adopt a Persona**: Become a character relevant to the topic (e.g., Interviewer, Colleague, Client).\n"
        "2. **Stay in Character**: Do NOT act as a teacher. Do NOT correct grammar unless it breaks communication.\n"
        "3. **Engage**: Ask questions, challenge the user, or collaborate as the character would.\n"
        "4. **Short Responses**: Keep it conversational (under 50 words).\n\n"
        "User said: \"{last_message}\"\n\n"
        "Respond naturally as your character."
    )
}

# --- 2. HELPERS ---

def _get_profile_value(value, default="Unknown"):
    """
    Asegura que el prompt reciba un string explícito ("Unknown")
    en lugar de None o string vacío, para activar la lógica condicional del LLM.
    """
    if not value or (isinstance(value, list) and not value):
        return default
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)

def _generate_audio_html(url: str, is_iframe: bool = False) -> str:
    """Genera el HTML seguro para el frontend."""
    if not url:
        return ""
    
    if is_iframe:
        return f"""
        <iframe src="{url}" 
                style="width:100%; height:300px; border:none; border-radius:12px; overflow:hidden; background: transparent;" 
                scrolling="no">
        </iframe>
        """
    else:
        return f'<audio autoplay style="display:none;"><source src="{url}" type="audio/mp3"></audio>'

def _generate_error_html() -> str:
    return """
    <div style="padding: 12px; background: rgba(255, 0, 0, 0.1); color: #ff6b6b; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(255, 0, 0, 0.2);">
        ⚠️ <b>Audio unavailable</b>
    </div>
    """

# --- 3. NODO PRINCIPAL ---
async def tutor_node(state: AgentState):
    try:
        llm = Llama3Wrapper()
        # --- A. Extracción de Estado ---
        messages = state.get('messages', [])
        last_message = messages[-1].content
        last_ai_content = ""
        if len(messages) > 1:
            for msg in reversed(messages[:-1]):
                if isinstance(msg, AIMessage):
                    content = msg.content.strip()
                    
                    # --- FILTRO DE CORRECCIÓN ---
                    # Si el mensaje empieza con "Correction:", lo ignoramos y seguimos buscando atrás
                    if content.startswith("Correction:"):
                        continue 
                    last_ai_content = content
                    break

        # Flags de flujo
        grammar_error = state.get('grammar_error', False)
        is_lesson = state.get('is_lesson', False)
        next_step = state.get('next_step', 'chat')
        
        # Datos del perfil (Normalizados para el Prompt)
        student_name = _get_profile_value(state.get('student_name'), "Unknown")
        student_interests = _get_profile_value(state.get('student_interests'), "Unknown")
        student_goals = _get_profile_value(state.get('student_goals'), "Unknown")
        
        # Contexto educativo
        current_level = state.get('current_level', 'Intermediate')
        raw_topic = state.get('current_topic', 'General Conversation')
        
        # 1. Try to find the full topic object in the CURRICULUM based on the name from state
        # The state might store just the string name (from ProgressService)
        # We need to find the dict in CURRICULUM that matches this name to get the example.
        
        current_topic_name = raw_topic
        example_context = ""

        if current_level in CURRICULUM:
             level_items = CURRICULUM[current_level]
             for item in level_items:
                 if isinstance(item, dict):
                     if item.get("topic") == raw_topic:
                         # Found the dict for this topic
                         example_text = item.get("example", "")
                         example_context = f"Example Scenario to Follow: {example_text}\n" if example_text else ""
                         break
                 elif item == raw_topic:
                     # It's a string, acts as normal
                     break
        
        current_topic = current_topic_name
        user_memory = state.get('user_memory', [])
        memory_context = f"User Memory: {', '.join(user_memory)}" if user_memory else ""
        correction = state.get('correction', '')
        current_mode = state.get('current_mode', 'chat')

        # --- B. Selección de Prompt ---
        # Prioritize explicit modes (Roleplay) over inferred next_steps if applicable
        if grammar_error:
            prompt_key = "grammar_error"
        elif current_mode == "roleplay":
            prompt_key = "roleplay"
        elif next_step == "teach" or is_lesson:
            prompt_key = "teach"
            current_mode = "teach"
        elif next_step == "evaluate_lesson":
            prompt_key = "evaluate_lesson"
            current_mode = "evaluate_lesson"
        elif next_step == "new_topic":
            prompt_key = "new_topic"
            current_mode = "new_topic"
        else:
            prompt_key = "new_topic"

        # Formateo del System Prompt
        try:
            system_prompt_content = PROMPT_TEMPLATES[prompt_key].format(
                last_ai_content=last_ai_content,
                current_level=current_level,
                current_topic=current_topic,
                memory_context=memory_context,
                last_message=last_message,
                correction=correction,
                student_name=student_name,
                student_interests=student_interests,
                student_goals=student_goals,
                example_context=example_context
            )
        except Exception as fe:
            logger.error(f"Error formatting prompt '{prompt_key}': {fe}")
            # Fallback to a simple prompt to avoid hanging
            system_prompt_content = f"You are Emma. Continue the conversation about {current_topic}."

        logger.info(f"Prompt Key: {prompt_key} | Mode: {current_mode} | Topic: {current_topic}")
        
        # --- C. Construcción del Historial para Llama-3 ---
        chat_history = []
        chat_history.append({"role": "system", "content": system_prompt_content})
        
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            if role == "assistant" and msg.content.startswith("Correction:"):
                continue
            chat_history.append({"role": role, "content": msg.content})
            
        prompt_json = json.dumps(chat_history)
        logger.info(f"LLM Request ({len(chat_history)} messages)...")

        # --- D. Inferencia (Streaming) ---
        response_text = ""
        audio_content = ""
        try:
            for chunk in llm.stream(prompt_json):
                response_text += chunk
        except Exception as le:
            logger.error(f"LLM Inference Error: {le}")
            response_text = "I'm sorry, I'm having trouble with my language model right now."

        if not response_text:
            logger.warning("LLM returned empty response!")
            response_text = "I'm listening. Tell me more!"

        logger.info(f"LLM Response received ({len(response_text)} chars)")
        if grammar_error:
            logger.info("Generating grammar error...")
            return {
                "grammar_error": grammar_error,
                "current_mode": current_mode,
                "messages": [AIMessage(content=response_text)],
                "audio_content": audio_content
            }

        try:
            if is_lesson:
                logger.info("Generating interpreter audio (TTS)...")
                interpreter_url = await create_interpreter_page(response_text)
                audio_content = _generate_audio_html(interpreter_url, is_iframe=True)
            else:   
                logger.info("Generating simple audio (TTS)...")
                audio_url = await create_simple_audio(response_text)
                audio_content = _generate_audio_html(audio_url, is_iframe=False)
            logger.info("TTS Generation completed.")
        except Exception as e:
            logger.error(f"TTS Error: {e}")
            audio_content = _generate_error_html()

        # --- F. Retorno de Estado ---
        return {
            "grammar_error": grammar_error,
            "current_mode": current_mode,
            "messages": [AIMessage(content=response_text)],
            "audio_content": audio_content
        }

    except Exception as e:
        logger.critical(f"Critical error in tutor_node: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I'm having a little trouble right now. Can we try again in a moment?")],
            "audio_content": ""
        }