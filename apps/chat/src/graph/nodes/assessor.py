from langchain_core.messages import SystemMessage, HumanMessage, AIMessage # Importamos AIMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
import logging
import json

logger = logging.getLogger(__name__)

def _get_intent(response_raw: str, default: str = "CHAT") -> str:
    intent = default
    try:
        json_start = response_raw.find('{')
        json_end = response_raw.rfind('}') + 1
        if json_start != -1 and json_end != -1:
            data = json.loads(response_raw[json_start:json_end])
            intent = data.get("intent", default).upper()
        else:
            if "STOP" in response_raw.upper(): intent = "STOP"
            elif "DISCOVERY" in response_raw.upper(): intent = "DISCOVERY_RESPONSE"
            elif "REQUEST" in response_raw.upper(): intent = "REQUEST_LESSON"
    except Exception:
        logger.warning(f"Assessor parsing failed: {response_raw}")
    
    return intent

def assessor_node(state: AgentState):
    """
    Analyzes the user's input considering the context (Last AI Message + User Input).
    """
    try:
        llm = Llama3Wrapper()
        messages = state.get('messages', [])
        current_mode = state.get('current_mode', 'chat')
        
        # --- 1. Extracción de Contexto (Último Humano y Última AI) ---
        user_input = messages[-1].content if messages else ""
        last_ai_content = "No prior context (Conversation Start)."
        
        # Buscamos hacia atrás
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
        
        # Creamos un bloque de texto formateado para el prompt
        conversation_context = (
            f"Last AI Question/Statement: \"{last_ai_content}\"\n"
            f"User Response: \"{user_input}\""
        )

        # --- 2. Construcción de Prompts ---
        if current_mode == 'teach':
            system_instruction = (
                "### SYSTEM ###\n"
                "Context: The user is in an ACTIVE LESSON loop.\n"
                "Task: Classify intent based on the interaction between the AI's question and User's answer.\n\n"
                "### INTENT CLASSES ###\n"
                "1. STOP_TEACH: User wants to quit, change topic, or explicitly says stop.\n"
                "2. REQUEST_RESTART: User asks to start over, reset, OR explicitly asks for the next topic/lesson.\n"
                "3. CONTINUE_TEACH: User is answering the exercise, asking for help, or providing input related to the current task.\n\n"
                "### OUTPUT FORMAT ###\n"
                "Return valid JSON only: {\"intent\": \"...\"}"
            )
            # Inyectamos el contexto aquí
            prompt = f"{system_instruction}\n\n### CONVERSATION CONTEXT ###\n{conversation_context}"
            
            response_raw = llm.invoke(prompt).strip()
            intent = _get_intent(response_raw, "CONTINUE_TEACH")
            
        else:
            system_instruction = (
                "### SYSTEM ###\n"
                "Context: General Conversation.\n"
                "Task: Classify intent based on the conversation flow.\n\n"
                "### INTENT CLASSES ###\n"
                "1. REQUEST_LESSON: User explicitly asks to start a lesson, learn a specific topic, or asks for exercises.\n"
                "2. TOPIC_CHANGE: User changes the subject drastically unrelated to previous context, or suggest a new topic for us based on level.\n"
                "3. CHAT: Casual conversation, answering questions, or stating opinions.\n\n"
                "### OUTPUT FORMAT ###\n"
                "Return valid JSON only: {\"intent\": \"...\"}"
            )
            # Inyectamos el contexto aquí
            prompt = f"{system_instruction}\n\n### CONVERSATION CONTEXT ###\n{conversation_context}"
            
            response_raw = llm.invoke(prompt).strip()
            intent = _get_intent(response_raw, "CHAT")
        
        logger.info(f"Assessor Intent: {intent} (Mode: {current_mode}) User input: {user_input}")

        # --- 3. ROUTING (Mapeo de Intención a Acción) ---
        # (Esta parte permanece igual que tu código original)
        next_step = "chat"
        next_mode = current_mode
        is_lesson = False
                
        if current_mode == 'teach':
            if intent == "STOP_TEACH":
                next_step = "chat"
                next_mode = "chat"
            elif intent == "REQUEST_RESTART":
                next_step = "teach"
                is_lesson = True
            else: # CONTINUE_TEACH
                next_step = "evaluate_lesson"
                is_lesson = True
                
        else:
            if intent == "REQUEST_LESSON":
                next_step = "teach"
                next_mode = "teach"
                is_lesson = True
            elif intent == "TOPIC_CHANGE":
                next_step = "new_topic"
                next_mode = "chat"
            else:
                next_step = "chat"
                next_mode = "chat"

        return {
            "next_step": next_step,
            "is_lesson": is_lesson,
            "current_mode": next_mode,
            "grammar_error": False
        }

    except Exception as e:
        logger.error(f"Error in assessor: {e}", exc_info=True)
        return {**state, "next_step": "chat"}