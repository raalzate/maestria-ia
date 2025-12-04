import chainlit as cl
# Importamos engineio para aplicar el parche
import engineio

# =================================================================================
# PARCHE CRÍTICO PARA EL ERROR "Too many packets in payload"
# =================================================================================
# Esto permite que el servidor acepte ráfagas grandes de datos de audio
# si la red se retrasa o el servidor está ocupado procesando.
engineio.payload.Payload.max_decode_packets = 2000
# =================================================================================

from chainlit.server import app
from fastapi.staticfiles import StaticFiles
import io
import asyncio
import numpy as np
import audioop
import wave

# Importar módulos propios
from src.audio import transcribe_audio, get_whisper
from src.llm import get_llm
from src.utils import ensure_directories
from src.grammar import get_grammar_checker
from langchain_core.messages import HumanMessage
from src.graph.workflow import create_graph

# Inicializar grafo
graph = create_graph()

# =================================================================================
# 1. CONFIGURACIÓN INICIAL
# =================================================================================
SILENCE_THRESHOLD = 3500  # Ajustar según tu micrófono
SILENCE_TIMEOUT = 1300.0  # Milisegundos de silencio para cortar

# Asegurar directorios
ensure_directories()

# Montar carpeta estática
app.mount("/public", StaticFiles(directory="public"), name="public")

# =================================================================================
# 2. EVENTOS DE CHAINLIT
# =================================================================================

@cl.on_chat_start
async def start():
    loading_msg = cl.Message(content="🚀 **Starting English Tutor...**", author="System")
    await loading_msg.send()

    # Precargar modelos en segundo plano
    if not get_llm():
        loading_msg.content = "🧠 Loading Llama-3..."
        await loading_msg.update()
        await cl.make_async(get_llm)()

    if not get_whisper():
        loading_msg.content = "👂 Loading Whisper..."
        await loading_msg.update()
        await cl.make_async(get_whisper)()

    # Pre-cargar modelo de corrección gramatical (T5)
    loading_msg.content = "⏳ Loading Grammar Checker (T5)..."
    await loading_msg.update()
    await cl.make_async(get_grammar_checker)()

    loading_msg.content = "✅ **Ready!**"
    await loading_msg.update()
    await asyncio.sleep(1)
    await loading_msg.remove()
    
    # Inicializar estado de sesión
    cl.user_session.set("user_level", "Intermediate")
    cl.user_session.set("current_topic", "General Conversation")

    # Mensaje de bienvenida
    welcome_msg = (
        "👋 **Hello! I am Emma, your English Tutor.**\n\n"
        "🎙️ **Practice Speaking:** Click the microphone to start talking.\n"
        "📝 **Feedback:** I will correct your grammar and help you improve.\n\n"
        "**Current Level:** Intermediate | **Topic:** General Conversation"
    )
    
    actions = [
        cl.Action(name="change_level", value="beginner", label="👶 Beginner", payload={}),
        cl.Action(name="change_level", value="intermediate", label="🧑 Intermediate", payload={}),
        cl.Action(name="change_level", value="advanced", label="🎓 Advanced", payload={}),
        cl.Action(name="suggest_topic", value="suggest", label="💡 New Topic", payload={})
    ]
    
    await cl.Message(content=welcome_msg, actions=actions).send()


@cl.action_callback("change_level")
async def on_level_change(action):
    level = action.value.capitalize()
    cl.user_session.set("user_level", level)
    await cl.Message(content=f"✅ **Level changed to:** {level}").send()

@cl.action_callback("suggest_topic")
async def on_suggest_topic(action):
    await main(cl.Message(content="Suggest a new topic for us to discuss based on my level.", author="User"))


@cl.on_audio_start
async def on_audio_start():
    # Inicialización segura de variables
    cl.user_session.set("silent_duration_ms", 0)
    cl.user_session.set("is_speaking", False)
    cl.user_session.set("audio_chunks", [])
    cl.user_session.set("last_elapsed_time", 0.0) 
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks")

    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)

    if chunk.isStart:
        cl.user_session.set("last_elapsed_time", chunk.elapsedTime)
        cl.user_session.set("silent_duration_ms", 0)
        cl.user_session.set("is_speaking", True)
        return

    # Recuperación segura con valores por defecto
    last_elapsed_time = cl.user_session.get("last_elapsed_time") or 0.0
    silent_duration_ms = cl.user_session.get("silent_duration_ms") or 0
    is_speaking = cl.user_session.get("is_speaking")

    time_diff_ms = chunk.elapsedTime - last_elapsed_time
    cl.user_session.set("last_elapsed_time", chunk.elapsedTime)

    audio_energy = audioop.rms(chunk.data, 2)

    if audio_energy < SILENCE_THRESHOLD:
        silent_duration_ms += time_diff_ms
        cl.user_session.set("silent_duration_ms", silent_duration_ms)
        if silent_duration_ms >= SILENCE_TIMEOUT and is_speaking:
            cl.user_session.set("is_speaking", False)
            await process_audio()
    else:
        cl.user_session.set("silent_duration_ms", 0)
        if not is_speaking:
            cl.user_session.set("is_speaking", True)

@cl.on_audio_end
async def on_audio_end():
    await process_audio()

async def process_audio():
    audio_chunks = cl.user_session.get("audio_chunks")
    
    if not audio_chunks:
        return

    concatenated = np.concatenate(list(audio_chunks))
    wav_buffer = io.BytesIO()

    frames = 0
    rate = 0

    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(concatenated.tobytes())
        # Leer propiedades ANTES de cerrar el archivo
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()

    wav_buffer.seek(0)
    cl.user_session.set("audio_chunks", [])

    if rate > 0:
        duration = frames / float(rate)
    else:
        duration = 0

    if duration <= 1.0:
        print(f"Audio too short ({duration:.2f}s), ignoring.")
        return

    audio_buffer = wav_buffer.getvalue()
    
    text, error = await cl.make_async(transcribe_audio)(audio_buffer)
    
    if error:
        await cl.Message(content=f"❌ Error: {error}").send()
        return

    if not text:
        await cl.Message(content="❌ I heard silence. Please try speaking louder.").send()
        return

    await main(cl.Message(content=text, author="User"))


@cl.on_message
async def main(message: cl.Message):
    user_input = message.content
    
    level = cl.user_session.get("user_level", "Intermediate")
    topic = cl.user_session.get("current_topic", "General Conversation")
    user_memory = cl.user_session.get("user_memory", [])
    
    msg = cl.Message(content="🧠 _Thinking..._", author="Emma")
    await msg.send()
    
    inputs = {
        "messages": [HumanMessage(content=user_input)],
        "user_level": level,
        "current_topic": topic,
        "user_memory": user_memory
    }
    
    final_state = await graph.ainvoke(inputs)
    
    cl.user_session.set("user_level", final_state.get("user_level", level))
    cl.user_session.set("current_topic", final_state.get("current_topic", topic))
    cl.user_session.set("user_memory", final_state.get("user_memory", user_memory))
    
    response_message = final_state["messages"][-1].content
    audio_content = final_state.get("audio_content", "")
    
    msg.content = response_message
    if audio_content:
        msg.content += "\n\n" + audio_content
    await msg.update()