from langchain_core.messages import AIMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
from src.services.progress_service import ProgressService
import logging

logger = logging.getLogger(__name__)

ONBOARDING_PROMPTS = {
    "ask_name": (
        "### SYSTEM ###\n"
        "You are Emma, a friendly English Coach.\n"
        "Task: Ask for the user's name in a warm, welcoming way.\n\n"
        "### INSTRUCTIONS ###\n"
        "1. Greet the user warmly.\n"
        "2. Ask for their name.\n"
        "3. Keep it brief (1-2 sentences).\n\n"
        "Example: 'Hi! I'm Emma, your English coach. What's your name?'"
    ),
    "ask_goals": (
        "### SYSTEM ###\n"
        "You are Emma, a friendly English Coach.\n"
        "Student Name: {student_name}\n"
        "User said: \"{last_message}\"\n\n"
        "### TASK ###\n"
        "1. Acknowledge their name briefly (e.g., 'Nice to meet you, {student_name}!').\n"
        "2. Ask why they are learning English (their goals).\n"
        "3. Keep it conversational and brief.\n\n"
        "Example: 'Nice to meet you, {student_name}! What brings you here? Why are you learning English?'"
    ),
    "ask_interests": (
        "### SYSTEM ###\n"
        "You are Emma, a friendly English Coach.\n"
        "Student: {student_name}\n"
        "Goals: {student_goals}\n"
        "User said: \"{last_message}\"\n\n"
        "### TASK ###\n"
        "1. Acknowledge their goal briefly (e.g., 'Great goal!', 'That's wonderful!').\n"
        "2. Ask about their hobbies or interests.\n"
        "3. Keep it brief and friendly.\n\n"
        "Example: 'That's a great goal! What do you enjoy doing in your free time? Any hobbies or sports?'"
    ),
    "complete": (
        "### SYSTEM ###\n"
        "You are Emma. Be concise.\n"
        "Student: {student_name}\n"
        "Goals: {student_goals}\n"
        "Interests: {student_interests}\n"
        "User said: \"{last_message}\"\n\n"
        "### TASK ###\n"
        "1. Answer user question/request if any (concisely).\n"
        "2. State: \"We'll start in Chat Mode. Use 'Check Progress' to switch modes.\"\n"
        "3. Ask one short question to start.\n"
        "MAX LENGTH: 2 sentences total."
    )
}

def onboarding_node(state: AgentState):
    """
    Handles the onboarding/discovery flow.
    Collects: name, interests, goals.
    Transitions to flow selection when complete.
    """
    try:
        ps = ProgressService()
        llm = Llama3Wrapper()
        messages = state.get('messages', [])
        last_message = messages[-1].content if messages else ""
        dataInfo = ps.load_progress()
        # Get current profile state
        student_name = dataInfo.get('student_name', 'Unknown')
        student_interests = dataInfo.get('student_interests') or []
        student_goals = dataInfo.get('student_goals') or []
        
        # Determine onboarding stage
        has_name = len(student_name) > 0 and student_name != "Unknown"
        has_goals = len(student_goals) > 0
        has_interests = len(student_interests) > 0
        
        
        # Select appropriate prompt based on what's missing
        if not has_name:
            prompt_key = "ask_name"
            system_prompt = ONBOARDING_PROMPTS[prompt_key]
        elif not has_goals:
            prompt_key = "ask_goals"
            system_prompt = ONBOARDING_PROMPTS[prompt_key].format(
                student_name=student_name,
                last_message=last_message
            )
        elif not has_interests:
            prompt_key = "ask_interests"
            system_prompt = ONBOARDING_PROMPTS[prompt_key].format(
                student_name=student_name,
                student_goals=student_goals,
                last_message=last_message
            )
        else:
            # All info collected - complete onboarding
            prompt_key = "complete"
            system_prompt = ONBOARDING_PROMPTS[prompt_key].format(
                student_name=student_name,
                student_goals=student_goals,
                student_interests=student_interests,
                last_message=last_message
            )
        
        # Generate response
        response_text = ""
        for chunk in llm.stream(system_prompt):
            response_text += chunk
        
        # Update state
        updates = {
            "messages": [AIMessage(content=response_text)],
        }
        
        if prompt_key == "complete":
            # Dynamic prompt based on user intent (Check if they asked for a lesson)
            user_wants_lesson = any(keyword in last_message.lower() for keyword in ["lesson", "teach", "learn", "class"])
            
            if user_wants_lesson:
                instructions = (
                    "### TASK ###\n"
                    "1. Great! Confirm we will start in **Lesson Mode** immediately.\n"
                    "2. Ask what topic they want to start with (or suggest one based on interests).\n"
                    "MAX LENGTH: 2 sentences."
                )
                updates["current_mode"] = "teach" # Set initial mode to teach/lesson
            else:
                 instructions = (
                    "### TASK ###\n"
                    "1. Answer user question/request if any (concisely).\n"
                    "2. State: \"We'll start in Chat Mode. Use 'Check Progress' to switch modes.\"\n"
                    "3. Ask one short question to start.\n"
                    "MAX LENGTH: 2 sentences total."
                )
                 updates["current_mode"] = "chat"

            system_prompt = (
                "### SYSTEM ###\n"
                "You are Emma. Be concise.\n"
                "Student: {student_name}\n"
                "Goals: {student_goals}\n"
                "Interests: {student_interests}\n"
                "User said: \"{last_message}\"\n\n"
            ) + instructions
            
            system_prompt = system_prompt.format(
                student_name=student_name,
                student_goals=student_goals,
                student_interests=student_interests,
                last_message=last_message
            )

            # Re-generate response with the dynamic prompt
            response_text = ""
            for chunk in llm.stream(system_prompt):
                response_text += chunk
            
            updates["messages"] = [AIMessage(content=response_text)]
            updates["discovery_completed"] = True
            updates["next_step"] = "flow_selection"
            
            try:
                ps.current_progress['discovery_completed'] = True
                ps.save_progress()
                logger.info("Onboarding: Completed and saved to disk")
            except Exception as e:
                logger.error(f"Error saving onboarding completion: {e}")
        else:
            updates["next_step"] = "continue_onboarding"
        
        return updates
        
    except Exception as e:
        logger.error(f"Error in onboarding_node: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content="I'm having a little trouble. Can you tell me that again?")],
            "next_step": "continue_onboarding"
        }
