from langchain_core.messages import AIMessage
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
from src.tts import create_interpreter_page, create_simple_audio
import asyncio

async def tutor_node(state: AgentState):
    """
    Generates the final response based on the determined intent and context.
    Also generates the appropriate audio/interpreter content.
    """
    messages = state['messages']
    last_message = messages[-1].content
    user_level = state.get('user_level', 'Intermediate')
    current_topic = state.get('current_topic', 'General Conversation')
    next_step = state.get('next_step', 'chat')
    user_memory = state.get('user_memory', [])
    grammar_error = state.get('grammar_error', False)
    correction = state.get('correction', '')
    is_lesson = state.get('is_lesson', False)
    
    llm = Llama3Wrapper()
    
    memory_context = f"User Memory: {', '.join(user_memory)}" if user_memory else ""
    
    if grammar_error:
        system_prompt = (
            f"You are Emma, a helpful English Tutor.\n"
            f"The user made a grammar mistake. Original: '{last_message}'. Corrected: '{correction}'.\n"
            "Politely explain the correction and ask them to try again.\n"
            "Keep it encouraging and short."
        )
    elif next_step == "teach":
        system_prompt = (
            f"You are Emma, a professional English Tutor. Level: {user_level}. Topic: {current_topic}.\n"
            f"{memory_context}\n"
            "The user requested learning content. Provide a detailed, educational response with examples."
        )
    elif next_step == "new_topic":
        system_prompt = (
            f"You are Emma. Level: {user_level}.\n"
            f"The user wants a new topic. The suggested topic is: {current_topic}.\n"
            "Introduce this topic and ask a starting question."
        )
    else: # chat
        system_prompt = (
            f"You are Emma, a friendly conversation partner. Level: {user_level}.\n"
            f"{memory_context}\n"
            "Keep response short (1-2 sentences) and natural."
        )
        
    response = llm.invoke(f"System: {system_prompt}\nUser: {last_message}")
    
    # Generar contenido de audio según el modo
    audio_content = ""
    
    if is_lesson:
        # Modo lección: Intérprete completo
        interpreter_url = await create_interpreter_page(response)
        if interpreter_url:
            audio_content = f"""
            <iframe src="{interpreter_url}" 
                    style="width:100%; height:300px; border:none; border-radius:12px; overflow:hidden; background: transparent;" 
                    scrolling="no">
            </iframe>
            """
    else:
        # Modo conversación: Audio simple
        audio_url = await create_simple_audio(response)
        if audio_url:
            audio_content = f'<audio autoplay style="display:none;"><source src="{audio_url}" type="audio/mp3"></audio>'
    
    return {
        "messages": [AIMessage(content=response)],
        "audio_content": audio_content
    }
