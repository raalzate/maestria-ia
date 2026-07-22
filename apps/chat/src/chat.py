import asyncio
import chainlit as cl
from src.config import logger
from src.audio.transcription import get_whisper
from src.llm import get_llm
from src.features.grammar import get_grammar_checker
from src.utils import SessionManager, cleanup_previous_ui_elements, cleanup_generated_files
from src.presentation.presenter import ChatPresenter

# Instance for the session (or we can instantiate inside handlers)
presenter = ChatPresenter()

@cl.on_chat_start
async def start():
    # 1. Initialization and Cleanup
    cleanup_generated_files()
    
    loading_msg = cl.Message(content="🚀 **Starting English Tutor...**", author="System")
    await loading_msg.send()

    try:
        loading_msg.content = "🧠 Loading AI Models..."
        await loading_msg.update()
        await asyncio.gather(
            cl.make_async(get_llm)(),
            cl.make_async(get_whisper)(),
            cl.make_async(get_grammar_checker)()
        )
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        loading_msg.content = "❌ Error loading resources. Please restart."
        await loading_msg.update()
        return

    await presenter.initialize_session()
    
    
    # Restoring original progress loading logic here for safety, though it could be in Presenter
    from src.services.progress_service import ProgressService
    from src.config import STATE_DEFAULT
    ps = ProgressService()
    user_progress = ps.load_progress()
    for key, default in STATE_DEFAULT.items():
        val = user_progress.get(key, default)
        SessionManager.set(key, val)

    await loading_msg.remove()

    welcome_vm = presenter.get_welcome_message()
    
    cl_actions = [
        cl.Action(name=a.name, payload={"value": a.value}, label=a.label) 
        for a in welcome_vm.actions
    ]
    
    await cl.Message(content=welcome_vm.content, actions=cl_actions).send()

@cl.on_message
async def main(message: cl.Message):
    # --- RESET PoC ---
    if message.content.strip().lower() == "/reset":
        res = await cl.AskUserMessage(
            content="⚠️ **Are you sure you want to reset all your progress?** This cannot be undone.",
            author="System"
        ).send()
        
        if res and "yes" in res.get("output", res.get("content", "")).lower():
            from src.services.progress_service import ProgressService
            ps = ProgressService()
            ps.reset_progress()
            await cl.Message(content="✅ **Progress reset successful!** Please restart the chat or just continue from scratch.", author="System").send()
            await presenter.initialize_session() # Re-init graph state
            return
        else:
            await cl.Message(content="❌ **Reset cancelled.**", author="System").send()
            return
    # -----------------

    await cleanup_previous_ui_elements()
    
    msg = cl.Message(content="", author="Emma")
    await msg.send()
    
    # Delegate to Presenter
    async for token in presenter.handle_message(message.content):
        if token.startswith("__THINKING__:"):
            phrase = token.replace("__THINKING__:", "")
            if msg.content != phrase:
                msg.content = phrase
                await msg.update()
        elif token.startswith("__ERROR__:"):
            msg.content = token.replace("__ERROR__:", "")
            await msg.update()
            return
        else:
            # Stream actual text content
            await msg.stream_token(token)

    # Final rendering based on Presenter's end state
    response_vm = presenter.get_final_response_view_model()
    
    if response_vm.content:
        msg.content = response_vm.content
        msg.actions = [
            cl.Action(name=a.name, payload={"value": a.value, "last_message": response_vm.last_message}, label=a.label)
            for a in response_vm.actions
        ]
        await msg.update()
    
    # (Optional) If streaming was separate, we'd handle it. 
    # The original code streamed the Tutor response token by token in a special way.
    # For MVP simplicity, we are bulk updating. 
    # If we want to restore token streaming, Presenter.handle_message needs to yield tokens from LLM.
    # Currently `graph.astream_events` is used, and it creates events.
    # We will assume bulk update for now as a valid MVP step, can refine later.