import os
from faster_whisper import WhisperModel

# Cache del modelo Whisper
_whisper_cache = None

def get_whisper():
    global _whisper_cache
    if _whisper_cache is None:
        print("⏳ Loading Faster-Whisper...")
        _whisper_cache = WhisperModel(
            "base", 
            device="cpu",
            compute_type="int8"
        )
    return _whisper_cache

def transcribe_audio(audio_input):
   
    model = get_whisper()
    
    # Wrap bytes in BytesIO if needed
    if isinstance(audio_input, bytes):
        import io
        audio_input = io.BytesIO(audio_input)

    try:
        print(f"🎯 Transcribing with Whisper...")
        segments, info = model.transcribe(audio_input, beam_size=5, language="en")                 
        text = " ".join([segment.text for segment in segments])
        
        print(f"✅ Transcription completed: {len(text)} characters")
            
        return text.strip(), None 

    except Exception as e:
        return None, f"Transcription Error: {str(e)}"
