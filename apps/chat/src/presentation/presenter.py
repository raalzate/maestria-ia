import random
from typing import Dict, Any, List, AsyncGenerator
from langchain_core.messages import HumanMessage
from src.config import STATE_DEFAULT, HUMAN_STATUS, logger
from src.utils import SessionManager
from src.graph.onboarding_graph import create_onboarding_graph
from src.graph.workflow import create_main_graph
from src.presentation.view_models import MessageViewModel, ActionViewModel

class ChatPresenter:
    def __init__(self):
        pass

    async def initialize_session(self):
        """Inicializa la sesión verificando el progreso del usuario."""
        # Cargar progreso si es necesario (el SessionManager ya lo hace en parte, 
        # pero aquí aseguramos la lógica de inicio).
        discovery_completed = SessionManager.get("discovery_completed", False)
        
        if not discovery_completed:
            SessionManager.set("graph", create_onboarding_graph())
        else:
            SessionManager.set("graph", create_main_graph())

    def get_welcome_message(self) -> MessageViewModel:
        """Genera el mensaje de bienvenida basado en el estado."""
        name = SessionManager.get("student_name")
        discovery_completed = SessionManager.get("discovery_completed", False)
        
        greeting = f"👋 **Hello{', ' + name if name else ''}! I am Emma.** How can I help you today?.\n\n"
        
        actions = []
        if not discovery_completed:
            body = "🧩 **Let's get to know each other!** I'd love to learn about you.\n\n"
        else:
            body = ""
            actions = [
                ActionViewModel(name="check_progress", value="progress", label="📊 Check Progress", description="Show current level and topic")
            ]
            if SessionManager.get("completed_topics"):
                actions.extend([
                    ActionViewModel(name="suggest_topic", value="suggest", label="💡 New Topic", description="Suggest a new topic"),
                    ActionViewModel(name="review_topic", value="review", label="🔄 Review Topic", description="Review current topic")
                ])

        return MessageViewModel(content=greeting + body, actions=actions, last_message=greeting + body)

    async def handle_message(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        Procesa el mensaje del usuario y devuelve tokens para streaming.
        El estado final se guarda en SessionManager y se puede consultar después.
        """
        # 1. Preproceso
        user_input = user_input.strip()
        if user_input:
            user_input = user_input[0].upper() + user_input[1:]
        if not user_input.endswith(('.', '?', '!')):
            user_input += "."

        # 2. Actualizar historial
        history = SessionManager.get("conversation_history", [])
        history.append(HumanMessage(content=user_input))
        SessionManager.set("conversation_history", history) # Asegurar persistencia si es necesario
        
        # 3. Preparar inputs del grafo
        graph = SessionManager.get("graph")
        inputs = self._build_graph_inputs(history)
        
        final_state = {}
        
        # 4. Ejecutar grafo con streaming de eventos
        try:
            async for event in graph.astream_events(inputs, version="v1"):
                kind = event["event"]
                name = event["name"]
                
                # Streaming de "Thinking..." updates
                if kind == "on_chain_start" and name in HUMAN_STATUS:
                    phrase = random.choice(HUMAN_STATUS[name])
                    yield f"__THINKING__:{phrase}" 
                
                # Streaming de Tokens del LLM
                elif kind == "on_chat_model_stream" or kind == "on_llm_new_token":
                    content = event["data"].get("chunk", "")
                    if hasattr(content, "content"):
                         content = content.content
                    elif hasattr(content, "text"): 
                         content = content.text
                    
                    if content:
                        yield content

                elif kind == "on_chain_end" and name == "LangGraph":
                    final_state = event["data"]["output"]
        except Exception as e:
            logger.error(f"Graph execution error: {e}", exc_info=True)
            yield "__ERROR__:Internal error."
            return

        # 5. Guardar estado final para que la UI lo consuma
        SessionManager.set("last_final_state", final_state)
        # También actualizamos SessionManager con datos críticos
        self._update_session_from_state(final_state)

    def _build_graph_inputs(self, history) -> Dict[str, Any]:
        return {
            "messages": history,
            "current_level": SessionManager.get("current_level"),
            "current_topic": SessionManager.get("current_topic"),
            "user_memory": SessionManager.get("user_memory"),
            "current_mode": SessionManager.get("current_mode", "chat"),
            "student_name": SessionManager.get("student_name"),
            "student_interests": SessionManager.get("student_interests"),
            "student_goals": SessionManager.get("student_goals"),
            "discovery_completed": SessionManager.get("discovery_completed"),
            "networking_memory": SessionManager.get("networking_memory", []),
            "learning_progress": SessionManager.get("learning_progress", {})
        }

    def _update_session_from_state(self, final_state: dict):
        """Actualiza el SessionManager con los resultados del grafo."""
        # Lógica trasladada de chat (SessionManager.update)
        # Pero aquí podemos ser más específicos si es necesario.
        SessionManager.update() # El helper existente ya hace el trabajo pesado
        
        if final_state.get('tutor'):
            tutor_state = final_state['tutor']
            if not tutor_state.get('grammar_error', False):
                SessionManager.update_history(tutor_state)

        # Check critical transitions
        if final_state.get('onboarding') and final_state['onboarding'].get('discovery_completed'):
             SessionManager.set("graph", create_main_graph())


    def get_final_response_view_model(self) -> MessageViewModel:
        """Construye el ViewModel final basado en el estado guardado."""
        final_state = SessionManager.get("last_final_state", {})
                
        # 1. Onboarding / Grammar / Networking
        for key in ['onboarding', 'grammar', 'networking']:
            if final_state.get(key):
                state_data = final_state[key]
                if state_data.get('messages'):
                    res_text = state_data['messages'][-1].content
                    
                    actions = [
                        ActionViewModel(name="translates", value="translates", label="🇪🇸 Translate", description=""),
                        ActionViewModel(name="select_lesson_mode", value= "lesson", label="📚 Lesson Mode", description="Structured learning"),                     
                    ]
                    return MessageViewModel(content=res_text, actions=actions,last_message=res_text)

        # 2. Tutor
        if final_state.get('tutor'):
            tutor_state = final_state['tutor']
            last_bot_message = tutor_state["messages"][-1].content if tutor_state.get("messages") else ""
            mode = tutor_state.get("current_mode", "chat")
            audio_content = tutor_state.get("audio_content", "") # Usamos esto si existe, o el texto

            actions = [
                ActionViewModel(name="translates", value="translates", label="🇪🇸 Translate", description=""),
                ActionViewModel(name="check_progress", value="progress", label="📊 Check Progress", description="Show current level and topic")
            ]
            
            final_content = last_bot_message
            if audio_content:
                final_content = f"{audio_content}\n\n{last_bot_message}"

            logger.info(f"Mode: {mode}")
            if mode in ["chat", "roleplay", "new_topic"]:
                actions.insert(0, ActionViewModel(name="suggestions", value="suggestions", label="💡 Help Me Answer", description=""))
                actions.append(ActionViewModel(name="suggest_topic", value="suggest", label="🗣️ Topic", description=""))
                actions.append(ActionViewModel(name="start_roleplay", value="roleplay", label="🎭 Roleplay", description="Simulate a scenario"))
                
            elif mode in ["teach", "evaluate_lesson"]:
                if audio_content:
                    final_content = f"{audio_content}"
                actions.insert(0, ActionViewModel(name="suggestions", value="suggestions", label="💡 Help Me Answer", description=""))
                actions.append(ActionViewModel(name="next_topic", value="next", label="📚 Next Topic", description=""))

            return MessageViewModel(content=final_content, last_message=last_bot_message, actions=actions)

        return MessageViewModel(content="...", last_message="...")
