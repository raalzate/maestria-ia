#!/usr/bin/env python3
"""
Script de diagnóstico para verificar archivos de audio problemáticos.
Uso: python diagnose_audio.py <ruta_al_archivo>
"""

import sys
import os
import subprocess

def diagnose_audio_file(file_path):
    """Diagnostica un archivo de audio para entender por qué falla FFmpeg."""
    
    print("="*80)
    print("🔍 DIAGNÓSTICO DE ARCHIVO DE AUDIO")
    print("="*80)
    
    # 1. Verificar existencia
    if not os.path.exists(file_path):
        print(f"❌ El archivo no existe: {file_path}")
        return
    
    # 2. Tamaño del archivo
    file_size = os.path.getsize(file_path)
    print(f"\n📊 Tamaño del archivo: {file_size:,} bytes")
    
    if file_size < 100:
        print(f"⚠️ ADVERTENCIA: Archivo muy pequeño, probablemente corrupto")
        return
    
    # 3. Magic Bytes
    with open(file_path, 'rb') as f:
        magic_bytes = f.read(16)
    
    print(f"\n🔮 Magic Bytes (primeros 16 bytes):")
    print(f"   HEX: {magic_bytes.hex().upper()}")
    print(f"   ASCII: {repr(magic_bytes)}")
    
    # Detectar formato
    header = magic_bytes.hex().upper()
    if header.startswith("1A45DFA3"):
        detected_format = "WebM/Matroska"
    elif b'ftyp' in magic_bytes:
        detected_format = "MP4"
    elif header.startswith("494433"):
        detected_format = "MP3 (con ID3)"
    elif header.startswith("FFFB") or header.startswith("FFF3"):
        detected_format = "MP3 (sin ID3)"
    elif header.startswith("52494646"):
        detected_format = "WAV (RIFF)"
    elif header.startswith("4F676753"):
        detected_format = "OGG"
    else:
        detected_format = "DESCONOCIDO"
    
    print(f"   Formato detectado: {detected_format}")
    
    # 4. FFprobe
    print(f"\n🔍 Ejecutando FFprobe...")
    probe_command = [
        "ffprobe",
        "-v", "error",
        "-show_format",
        "-show_streams",
        file_path
    ]
    
    probe_result = subprocess.run(probe_command, capture_output=True, text=True)
    
    if probe_result.returncode != 0:
        print(f"❌ FFprobe falló:")
        print(probe_result.stderr)
    else:
        print(f"✅ FFprobe exitoso:")
        print(probe_result.stdout[:500])  # Primeros 500 caracteres
    
    # 5. Intentar conversión con FFmpeg
    print(f"\n🛠️ Intentando conversión con FFmpeg...")
    temp_wav = file_path + ".test.wav"
    
    ffmpeg_command = [
        "ffmpeg", "-y",
        "-i", file_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-t", "5",  # Solo 5 segundos para test rápido
        temp_wav
    ]
    
    ffmpeg_result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
    
    if ffmpeg_result.returncode != 0:
        print(f"❌ FFmpeg falló:")
        print(ffmpeg_result.stderr)
    else:
        print(f"✅ FFmpeg exitoso!")
        if os.path.exists(temp_wav):
            wav_size = os.path.getsize(temp_wav)
            print(f"   WAV generado: {wav_size:,} bytes")
            os.remove(temp_wav)
    
    print("\n" + "="*80)
    print("🏁 DIAGNÓSTICO COMPLETADO")
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python diagnose_audio.py <ruta_al_archivo>")
        print("\nEjemplo:")
        print("  python diagnose_audio.py debug_files/last_input.mp4")
        sys.exit(1)
    
    file_path = sys.argv[1]
    diagnose_audio_file(file_path)
