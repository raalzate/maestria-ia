import os
import subprocess
from faster_whisper import WhisperModel

_whisper_cache = None

def get_whisper():
    global _whisper_cache
    if _whisper_cache is None:
        print("⏳ Loading Faster-Whisper...")
        # Usamos 'base' o 'small' para buen balance velocidad/precisión
        _whisper_cache = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_cache

def validate_audio_file(file_path):
    """
    Valida si un archivo de audio es válido usando ffprobe.
    Retorna (True, None) si es válido, o (False, error_message) si no lo es.
    """
    if not os.path.exists(file_path):
        return False, f"El archivo no existe: {file_path}"
    
    file_size = os.path.getsize(file_path)
    if file_size < 100:
        return False, f"El archivo es demasiado pequeño ({file_size} bytes). Probablemente esté corrupto."
    
    # Verificar bytes nulos (corrupción común en navegadores)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(1024)
            null_count = header.count(b'\x00')
            if len(header) > 0 and (null_count / len(header)) > 0.9:
                return False, "El archivo contiene principalmente bytes vacíos (corrupción de grabación)."
    except Exception as e:
        return False, f"Error leyendo archivo: {str(e)}"

    # Validación con FFprobe
    probe_command = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    try:
        probe_result = subprocess.run(probe_command, capture_output=True, text=True)
        if probe_result.returncode != 0:
            return False, f"FFprobe no reconoce el formato: {probe_result.stderr}"
    except FileNotFoundError:
        return False, "FFprobe no está instalado o no se encuentra en el PATH."
        
    return True, None

def transcribe_audio(audio_input):
    """
    Recibe la ruta del archivo de audio (str) o un objeto file-like/bytes.
    Si es ruta: valida y convierte con FFmpeg.
    Si es bytes/buffer: transcribe directamente.
    """
    model = get_whisper()
    
    # Caso 1: Entrada es ruta de archivo (str)
    if isinstance(audio_input, str):
        file_path = audio_input
        # 1. Validación previa
        is_valid, error_msg = validate_audio_file(file_path)
        if not is_valid:
            return None, error_msg

        # Generamos el nombre del WAV de salida
        wav_path = file_path + ".converted.wav"
        
        try:
            print(f"🛠️ Convirtiendo {file_path} -> {wav_path}")

            # Convertir a WAV 16kHz mono (formato ideal para Whisper)
            command = [
                "ffmpeg", "-y",
                "-i", file_path,
                "-ar", "16000",
                "-ac", "1",
                "-c:a", "pcm_s16le",
                wav_path
            ]
            
            subprocess.run(command, check=True, capture_output=True, text=True)
            
            if not os.path.exists(wav_path):
                return None, "FFmpeg no generó el archivo WAV de salida."
            
            transcription_source = wav_path
            
        except subprocess.CalledProcessError as e:
            return None, f"FFmpeg Error:\n{e.stderr}"
        except Exception as e:
            return None, f"Error General en Conversión: {str(e)}"
            
    # Caso 2: Entrada es bytes o file-like object (In-memory)
    else:
        print("🧠 Procesando audio en memoria...")
        if isinstance(audio_input, bytes):
            import io
            transcription_source = io.BytesIO(audio_input)
        else:
            transcription_source = audio_input

    try:
        # Transcribir
        print(f"🎯 Transcribiendo con Whisper...")
        segments, info = model.transcribe(transcription_source, beam_size=5, language="en")                 
        text = " ".join([segment.text for segment in segments])
        
        print(f"✅ Transcripción completada: {len(text)} caracteres")
        
        # Limpieza solo si creamos un archivo temporal
        if isinstance(audio_input, str) and 'wav_path' in locals() and os.path.exists(wav_path):
             os.remove(wav_path)
            
        return text.strip(), None 

    except Exception as e:
        return None, f"Error General en Transcripción: {str(e)}"
