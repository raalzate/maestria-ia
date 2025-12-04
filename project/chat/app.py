import chainlit as cl
from chainlit.server import app
from fastapi.staticfiles import StaticFiles
import io
import asyncio
import numpy as np
import audioop
import wave

# Importar módulos propios
from src.audio import transcribe_audio, get_whisper
from src.llm import get_llm, generate_response
from src.tts import create_karaoke_page, create_simple_audio
from src.utils import ensure_directories

# =================================================================================
# 1. CONFIGURACIÓN INICIAL
# =================================================================================
SILENCE_THRESHOLD = (
    3500  # Adjust based on your audio level (e.g., lower for quieter audio)
)
SILENCE_TIMEOUT = 1300.0  # Seconds of silence to consider the turn finished

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

    loading_msg.content = "✅ **Ready!**"
    await loading_msg.update()
    await asyncio.sleep(1)
    await loading_msg.remove()
    
    # Inicializar estado de sesión
    cl.user_session.set("user_level", "Intermediate")
    cl.user_session.set("current_topic", "General Conversation")

    # Mensaje de bienvenida con Botón de Acción
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
    cl.user_session.set("silent_duration_ms", 0)
    cl.user_session.set("is_speaking", False)
    cl.user_session.set("audio_chunks", [])
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    audio_chunks = cl.user_session.get("audio_chunks")

    if audio_chunks is not None:
        audio_chunk = np.frombuffer(chunk.data, dtype=np.int16)
        audio_chunks.append(audio_chunk)

    # If this is the first chunk, initialize timers and state
    if chunk.isStart:
        cl.user_session.set("last_elapsed_time", chunk.elapsedTime)
        cl.user_session.set("is_speaking", True)
        return

    audio_chunks = cl.user_session.get("audio_chunks")
    last_elapsed_time = cl.user_session.get("last_elapsed_time")
    silent_duration_ms = cl.user_session.get("silent_duration_ms")
    is_speaking = cl.user_session.get("is_speaking")

    # Calculate the time difference between this chunk and the previous one
    time_diff_ms = chunk.elapsedTime - last_elapsed_time
    cl.user_session.set("last_elapsed_time", chunk.elapsedTime)

    # Compute the RMS (root mean square) energy of the audio chunk
    audio_energy = audioop.rms(
        chunk.data, 2
    )  # Assumes 16-bit audio (2 bytes per sample)

    if audio_energy < SILENCE_THRESHOLD:
        silent_duration_ms += time_diff_ms
        cl.user_session.set("silent_duration_ms", silent_duration_ms)
        if silent_duration_ms >= SILENCE_TIMEOUT and is_speaking:
            cl.user_session.set("is_speaking", False)
            await process_audio()
    else:
        # Audio is not silent, reset silence timer and mark as speaking
        cl.user_session.set("silent_duration_ms", 0)
        if not is_speaking:
            cl.user_session.set("is_speaking", True)

@cl.on_audio_end
async def on_audio_end():
    await process_audio()

async def process_audio():
    # Get the audio buffer from the session
    if audio_chunks := cl.user_session.get("audio_chunks"):
        # Concatenate all chunks
        concatenated = np.concatenate(list(audio_chunks))

        # Create an in-memory binary stream
        wav_buffer = io.BytesIO()

        # Create WAV file with proper parameters
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(24000)  # sample rate (24kHz PCM)
            wav_file.writeframes(concatenated.tobytes())

        # Reset buffer position
        wav_buffer.seek(0)

        cl.user_session.set("audio_chunks", [])

    frames = wav_file.getnframes()
    rate = wav_file.getframerate()

    duration = frames / float(rate)
    if duration <= 1.71:
        print("The audio is too short, please try again.")
        return

    audio_buffer = wav_buffer.getvalue()
    
    # Transcribir directamente desde el buffer
    text, error = await cl.make_async(transcribe_audio)(audio_buffer)
    
    if error:
        await cl.Message(content=f"❌ Error: {error}").send()
        return

    if not text:
        await cl.Message(content="❌ I heard silence. Please try speaking louder.").send()
        return

    # Procesar como mensaje de usuario (sin mostrar "You said" para experiencia más limpia)
    await main(cl.Message(content=text, author="User"))

    

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content
    
    # Manejo de archivos de audio subidos (Drag & Drop)
    audio_file = next((el for el in message.elements if "audio" in el.mime), None)
    if audio_file:
        load = cl.Message(content="👂 Processing uploaded file...", author="System")
        await load.send()
        transcribed_text, error = await cl.make_async(transcribe_audio)(audio_file.path)
        await load.remove()
        
        if error:
            await cl.Message(f"❌ Error processing file: {error}").send()
            return
            
        user_input = transcribed_text
        await cl.Message(f"🗣️ **Transcribed:** {user_input}").send()

    # Recuperar estado
    level = cl.user_session.get("user_level", "Intermediate")
    topic = cl.user_session.get("current_topic", "General Conversation")

    # Detectar si el usuario está haciendo una petición de aprendizaje
    request_check_prompt = (
        f"User said: '{user_input}'. "
        "Is this a REQUEST for learning content, explanations, or lists? "
        "Examples of requests: 'teach me...', 'give me...', 'what are...', 'explain...', 'show me...', 'list...' "
        "Reply 'YES' only for direct learning requests. "
        "Reply 'NO' for casual conversation, greetings, or personal questions."
    )
    
    request_decision = ""
    async for token in generate_response(request_check_prompt, "You are a helpful assistant."):
        request_decision += token
    
    is_request = "YES" in request_decision.upper()
    
    # Ajustar el prompt según si es petición o conversación
    if is_request:
        # Modo completo para peticiones educativas
        system_prompt = (
            f"You are Emma, a professional English Tutor. Current Level: {level}. Current Topic: {topic}.\n"
            "The user is requesting learning content. Provide a complete, detailed response.\n"
            "1. Always answer in English.\n"
            "2. Be thorough and educational.\n"
            f"3. Adapt your vocabulary to the {level} level.\n"
            "4. Provide examples and explanations."
        )
    else:
        # Modo conciso para conversación
        system_prompt = (
            f"You are Emma, a friendly English conversation partner. Current Level: {level}.\n"
            "Keep your responses SHORT and NATURAL (1-2 sentences maximum).\n"
            "1. Always answer in English.\n"
            "2. Be conversational and warm, not formal.\n"
            f"3. Use {level} level vocabulary.\n"
            "4. If you notice a grammar mistake, mention it briefly at the end."
        )
    
    # Mostrar indicador de escritura
    msg = cl.Message(content="✍️ _Emma is writing..._", author="Emma")
    await msg.send()
    
    # Generar respuesta SIN streaming (silenciosamente)
    full_resp = ""
    async for token in generate_response(user_input, system_prompt):
        full_resp += token

    # Solo hacer lección completa si es una petición de aprendizaje
    if is_request:
        # MODO LECCIÓN: Karaoke completo con todos los extras
        karaoke_url = await create_karaoke_page(full_resp)
        if karaoke_url:
            iframe = f'<iframe src="{karaoke_url}" style="width:100%; height:200px; border:none;" scrolling="no"></iframe>'
            
            # Generar traducción
            translation_prompt = f"Translate the following English text to Spanish: '{full_resp}'"
            translation = ""
            async for token in generate_response(translation_prompt, "You are a translator. Reply ONLY with the translation, no explanations."):
                translation += token
            
            translation_html = """
<details style="margin-top: 15px; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; background: #24283b;">
    <summary style="cursor: pointer; font-weight: 600; color: #bb9af7; user-select: none; outline: none;">
        🌐 Show translation (Spanish)
    </summary>
    <div style="margin-top: 10px; padding: 10px; background: #1a1b26; border-radius: 4px; color: #a9b1d6; line-height: 1.6;">
        <em>{}</em>
    </div>
</details>""".format(translation.strip())
            
            # Generar sugerencias
            suggestions_prompt = (
                f"The user said: '{user_input}' and Emma (the tutor) responded: '{full_resp[:200]}...'. "
                f"Generate EXACTLY 3 possible response options that the user could say next as a {level} English learner. "
                "These should be natural conversational replies or follow-up statements. "
                "Keep each option under 12 words. Reply ONLY with the 3 options, one per line, numbered 1., 2., 3."
            )
            
            suggestions_text = ""
            async for token in generate_response(suggestions_prompt, "You are a helpful assistant."):
                suggestions_text += token
            
            suggestions = []
            for line in suggestions_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    clean_line = line.lstrip('0123456789.-•) ').strip()
                    if clean_line:
                        suggestions.append(clean_line)
            
            accordion_html = """
<details style="margin-top: 15px; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; background: #24283b;">
    <summary style="cursor: pointer; font-weight: 600; color: #7aa2f7; user-select: none; outline: none;">
        💡 Show response suggestions
    </summary>
    <div style="margin-top: 10px; padding-left: 10px;">
"""
            for i, suggestion in enumerate(suggestions[:3], 1):
                accordion_html += f'        <div style="margin: 5px 0; padding: 8px; background: #1a1b26; border-radius: 4px; border-left: 3px solid #7aa2f7; color: #a9b1d6;"><em>"{suggestion}"</em></div>\n'
            
            accordion_html += """    </div>
</details>"""
            
            msg.content = iframe + translation_html + accordion_html
            msg.disable_feedback = True
            await msg.update()
        else:
            msg.content = full_resp
            await msg.update()
    else:
        # MODO CONVERSACIÓN: Solo audio simple y rápido
        msg.content = full_resp
        await msg.update()
        
        # Generar solo audio simple (sin karaoke)
        audio_url = await create_simple_audio(full_resp)
        if audio_url:
            # Agregar solo el reproductor de audio simple
            audio_html = f'<audio controls autoplay style="width:100%; margin-top:10px;"><source src="{audio_url}" type="audio/mp3"></audio>'
            msg.content = full_resp + "\n\n" + audio_html
            await msg.update()