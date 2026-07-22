import io
import wave
import numpy as np
import chainlit as cl
from src.config import CONFIG
from src.utils import SessionManager
from src.audio import transcribe_audio
# Importamos main de chat_logic para redirigir el texto transcrito
import src.chat 

@cl.on_audio_start
async def on_audio_start():
    SessionManager.set("silent_duration_ms", 0)
    SessionManager.set("is_speaking", False)
    SessionManager.set("audio_chunks", [])
    SessionManager.set("last_elapsed_time", 0.0)
    return True

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.InputAudioChunk):
    if chunk.isStart:
        SessionManager.set("last_elapsed_time", chunk.elapsedTime)
        SessionManager.set("silent_duration_ms", 0)
        SessionManager.set("is_speaking", True)
        return

    audio_data = np.frombuffer(chunk.data, dtype=np.int16)
    chunks = SessionManager.get("audio_chunks")
    if chunks is not None:
        chunks.append(audio_data)

    if audio_data.size > 0:
        audio_energy = np.sqrt(np.mean(audio_data.astype(np.float32)**2))
    else:
        audio_energy = 0

    last_time = SessionManager.get("last_elapsed_time", 0.0)
    time_diff = chunk.elapsedTime - last_time
    SessionManager.set("last_elapsed_time", chunk.elapsedTime)

    silent_dur = SessionManager.get("silent_duration_ms", 0)
    is_speaking = SessionManager.get("is_speaking")

    if audio_energy < CONFIG.SILENCE_THRESHOLD:
        silent_dur += time_diff
        SessionManager.set("silent_duration_ms", silent_dur)
        if silent_dur >= CONFIG.SILENCE_TIMEOUT and is_speaking:
            SessionManager.set("is_speaking", False)
            await process_audio()
    else:
        SessionManager.set("silent_duration_ms", 0)
        if not is_speaking:
            SessionManager.set("is_speaking", True)

@cl.on_audio_end
async def on_audio_end():
    await process_audio()

async def process_audio():
    chunks = SessionManager.get("audio_chunks")
    if not chunks:
        return
    SessionManager.set("audio_chunks", [])
    
    try:
        concatenated = np.concatenate(chunks)
    except ValueError:
        return 

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(CONFIG.CHANNELS)
        wav_file.setsampwidth(CONFIG.SAMPLE_WIDTH)
        wav_file.setframerate(CONFIG.SAMPLE_RATE)
        wav_file.writeframes(concatenated.tobytes())
        frames = wav_file.getnframes()

    duration = frames / float(CONFIG.SAMPLE_RATE)
    if duration <= CONFIG.MIN_AUDIO_DURATION:
        return

    wav_buffer.seek(0)
    text, error = await cl.make_async(transcribe_audio)(wav_buffer.getvalue())
    
    if error:
        await cl.Message(content=f"❌ Transcription Error: {error}").send()
    elif not text.strip():
        await cl.Message(content="❌ I couldn't hear you clearly. Please try again.").send()
    else:
        # Llamamos directamente a la lógica de chat
        await chat_logic.main(cl.Message(content=text, author="User"))