import chainlit as cl
import logging
from src.utils import SessionManager, safe_extract_llm_response, build_progress_bar_string, cleanup_previous_ui_elements

logger = logging.getLogger(__name__)
from src.llm import generate_response
from src.features.suggestions import generate_suggestions_html
from src.features.translations import generate_translation_html
import src.chat # Para disparar flujos desde acciones

@cl.action_callback("translates")
async def on_translates(action):
    await cleanup_previous_ui_elements()
    last_message = action.payload.get("last_message")
    if not last_message: return
    try:
        iframe = await generate_translation_html(last_message)
        msg = await cl.Message(content=iframe).send()
        # Guardar ID para limpieza posterior
        SessionManager.set("last_translation_id", msg.id)
    except Exception as e:
        await cl.Message(content="❌ Translation error.").send()

@cl.action_callback("suggestions")
async def on_suggestions(action):
    await cleanup_previous_ui_elements()
    last_message = action.payload.get("last_message")
    if not last_message: return
    try:
        iframe = await generate_suggestions_html(last_message)
        msg = await cl.Message(content=iframe).send()
        # Guardar ID para limpieza posterior
        SessionManager.set("last_suggestion_id", msg.id)
    except Exception as e:
        await cl.Message(content="❌ Error generating suggestions.").send()

@cl.action_callback("review_topic")
async def on_review_topic(action):
    await cleanup_previous_ui_elements()
    completed = SessionManager.get("completed_topics", [])
    if not completed:
        await cl.Message(content="❌ You haven't completed any topics yet.").send()
        return
    actions = [cl.Action(name="select_topic", payload={"value": t}, label=f"📚 {t}") for t in completed]
    msg = await cl.Message(content="**Select a topic to review:**", actions=actions).send()
    SessionManager.set("last_review_topics_id", msg.id)

@cl.action_callback("select_topic")
async def on_select_topic(action):
    await cleanup_previous_ui_elements()
    topic = action.payload["value"]
    SessionManager.set("current_topic", topic)
    msg = await cl.Message(content=f"✅ **Topic changed to:** {topic}").send()
    SessionManager.set("last_topic_selection_id", msg.id)

@cl.action_callback("suggest_topic")
async def on_suggest_topic(action):
    await cleanup_previous_ui_elements()
    await src.chat.main(cl.Message(content="Suggest a new topic for us based on my level.", author="User"))

@cl.action_callback("next_topic")
async def on_next_topic(action):
    await cleanup_previous_ui_elements()
    await src.chat.main(cl.Message(content="Let's continue with the next topic.", author="User"))

@cl.action_callback("check_progress")
async def on_check_progress(action):
    await cleanup_previous_ui_elements()
    try:
        logger.info("👉 Action triggered: check_progress")
        level = SessionManager.get("current_level")
        topic = SessionManager.get("current_topic")
        
        progress_ui = build_progress_bar_string(level, topic)
        
        actions = [
            cl.Action(name="select_chat_mode", payload={"value": "chat"}, label="💬 Chat Mode", description="Casual conversation"),
            cl.Action(name="select_lesson_mode", payload={"value": "lesson"}, label="📚 Lesson Mode", description="Structured learning"),
            cl.Action(name="review_saved_phrases", payload={"value": "saved"}, label="🔖 Saved Phrases", description="Review saved items")
        ]
        
        msg = await cl.Message(content=progress_ui, actions=actions).send()
        SessionManager.set("last_progress_id", msg.id)
    except Exception as e:
        logger.error(f"Error in check_progress: {e}", exc_info=True)
        await cl.Message(content="❌ Error.").send()

@cl.action_callback("review_saved_phrases")
async def on_review_saved_phrases(action):
    await cleanup_previous_ui_elements()
    from src.services.progress_service import ProgressService
    ps = ProgressService()
    phrases = ps.get_saved_phrases()
    
    if not phrases:
        await cl.Message(content="📂 Your saved phrases list is empty.").send()
    else:
        content = "### 🔖 Saved Phrases\n\n" + "\n".join([f"- {p}" for p in phrases])
        msg = await cl.Message(content=content).send()
        SessionManager.set("last_saved_phrases_id", msg.id)

@cl.action_callback("select_chat_mode")
async def on_select_chat_mode(action):
    await cleanup_previous_ui_elements()
    SessionManager.set("current_mode", "chat")
    await src.chat.main(cl.Message(content="I want to start with Chat Mode (practice).", author="User"))

@cl.action_callback("select_lesson_mode")
async def on_select_lesson_mode(action):
    await cleanup_previous_ui_elements()
    SessionManager.set("current_mode", "teach")
    await src.chat.main(cl.Message(content="I want to start with Lesson Mode (practice).", author="User"))

@cl.action_callback("start_roleplay")
async def on_start_roleplay(action):
    await cleanup_previous_ui_elements()
    SessionManager.set("current_mode", "roleplay")
    await src.chat.main(cl.Message(content="Let's start a roleplay simulation about this topic.", author="User"))