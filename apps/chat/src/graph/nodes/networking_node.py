from langchain_core.messages import AIMessage, HumanMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
from src.features.tts import create_simple_audio
import logging
import json

logger = logging.getLogger(__name__)

NETWORKING_PROMPT = (
    "### SYSTEM ###\n"
    "Role: Emma, a Senior Software Engineer networking at a Tech Conference.\n"
    "Student: {student_name} | Interests: {student_interests}\n"
    "Recent topics: {networking_memory}\n"
    "User said: \"{last_message}\"\n\n"
    "### INSTRUCTIONS ###\n"
    "1. Chat expertly about software, AI, or tech.\n"
    "2. Connect non-tech topics back to tech/lifestyle briefly.\n"
    "3. Use industry slang correctly (PRs, deployment, latency, stack).\n"
    "4. Always end with a short relevant question.\n"
    "5. **CRITICAL**: Be extremely concise. Max 1-2 short sentences.\n\n"
    "### CONTEXT ###\n"
    "Simulate a quick hallway chat. Friendly but direct."
)

def _get_profile_value(value, default="Unknown"):
    """Helper to safely get profile values"""
    if not value or (isinstance(value, list) and not value):
        return default
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)

def _generate_audio_html(url: str) -> str:
    """Generate HTML for audio playback"""
    if not url:
        return ""
    return f'<audio autoplay style="display:none;"><source src="{url}" type="audio/mp3"></audio>'

def _generate_error_html() -> str:
    return """
    <div style="padding: 12px; background: rgba(255, 0, 0, 0.1); color: #ff6b6b; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(255, 0, 0, 0.2);">
        ⚠️ <b>Audio unavailable</b>
    </div>
    """

def networking_node(state: AgentState):
    """
    Networking/Chat mode.
    - Friendly, casual conversation
    - Memorizes interests/hobbies to networking_memory
    - Does NOT affect lesson progress
    """
    try:
        messages = state.get('messages', [])
        if not messages:
            return {"messages": [AIMessage(content="Let's chat! What's on your mind?")]}
        
        last_message = messages[-1].content
        
        # Get profile and networking context
        student_name = _get_profile_value(state.get('student_name'), "friend")
        student_interests = _get_profile_value(state.get('student_interests'), "various topics")
        networking_memory = state.get('networking_memory') or []
        
        # Format networking memory for context
        memory_context = ", ".join(networking_memory[-5:]) if networking_memory else "No previous topics"
        
        # Build prompt
        system_prompt = NETWORKING_PROMPT.format(
            student_name=student_name,
            student_interests=student_interests,
            networking_memory=memory_context,
            last_message=last_message
        )
        
        # Build conversation history for context
        chat_history = [{"role": "system", "content": system_prompt}]
        for msg in messages[-6:]:  # Last 6 messages for context
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            chat_history.append({"role": role, "content": msg.content})
        
        prompt_json = json.dumps(chat_history)
        
        # Generate response
        llm = Llama3Wrapper()
        response_text = ""
        for chunk in llm.stream(prompt_json):
            response_text += chunk
        
        # Note: Audio generation removed to keep it sync
        # Audio will be handled by the UI layer if needed
        
        # Return updates
        return {
            "messages": [AIMessage(content=response_text)],
            "current_mode": "networking",
            "next_step": "networking"
        }
        
    except Exception as e:
        logger.error(f"Error in networking_node: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="Sorry, I lost my train of thought. What were we talking about?")],
        }
