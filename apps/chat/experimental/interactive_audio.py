import yt_dlp
import os
import json
import time
import sys
from faster_whisper import WhisperModel

class KaraokeFasterWhisper:
    def __init__(self, model_size="base", device="cuda", compute_type="float16"):   
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        

    def descargar_audio(self, url, velocidad=0.82):
        """Descarga y procesa el audio."""
        output_name = f"audio_{int(time.time())}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': ['-af', f'atempo={velocidad}'],
            'outtmpl': f'{output_name}.%(ext)s',
            'quiet': True
        }

        print(f"--- Descargando audio (Velocidad: {velocidad}) ---")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return f"{output_name}.mp3"

    def transcribir_palabras(self, audio_path, idioma='en', task='transcribe'):
        """Usa faster-whisper para obtener timestamps por palabra."""
        print(f"--- Transcribiendo con faster-whisper (Tarea: {task}) ---")
        
        # word_timestamps=True es esencial aquí
        segments, info = self.model.transcribe(
            audio_path, 
            language=idioma, 
            task=task,
            word_timestamps=True
        )

        word_data = []
        for segment in segments:
            for word in segment.words:
                word_data.append({
                    'w': word.word.strip(),
                    's': round(word.start, 3),
                    'e': round(word.end, 3)
                })
        
        return word_data

    def generar_html_web(self, audio_file, word_data, output_name="index.html"):
        """Genera el archivo HTML estático para exportar."""
        words_json = json.dumps(word_data)
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Karaoke con IA</title>
            <style>
                body {{ background: #0a0a0a; color: #eee; font-family: 'Segoe UI', Arial; display: flex; justify-content: center; padding: 50px; }}
                .container {{ background: #111; padding: 30px; border-radius: 15px; max-width: 800px; border: 1px solid #333; }}
                h2 {{ color: #4CAF50; text-align: center; font-weight: 300; }}
                audio {{ width: 100%; margin: 20px 0; border-radius: 8px; }}
                #transcript-box {{ background: #050505; padding: 25px; border-radius: 10px; height: 300px; overflow-y: auto; line-height: 1.8; font-size: 1.4rem; border: 1px solid #222; scroll-behavior: smooth; }}
                .word {{ display: inline-block; margin-right: 8px; color: #444; transition: all 0.2s ease; cursor: pointer; }}
                .highlight {{ color: #4CAF50 !important; transform: scale(1.15); font-weight: bold; text-shadow: 0 0 12px rgba(76,175,80,0.4); }}
                .past {{ color: #fff; }}
                #transcript-box::-webkit-scrollbar {{ width: 6px; }}
                #transcript-box::-webkit-scrollbar-thumb {{ background: #333; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Reproductor Sincronizado</h2>
                <audio id="player" controls src="{audio_file}"></audio>
                <div id="transcript-box"><div id="content"></div></div>
            </div>

            <script>
                const data = {words_json};
                const content = document.getElementById('content');
                const player = document.getElementById('player');
                const box = document.getElementById('transcript-box');

                const spans = data.map((d, i) => {{
                    const s = document.createElement('span');
                    s.className = 'word';
                    s.innerText = d.w;
                    s.onclick = () => player.currentTime = d.s;
                    content.appendChild(s);
                    return {{ el: s, s: d.s, e: d.e }};
                }});

                player.ontimeupdate = () => {{
                    const now = player.currentTime;
                    spans.forEach((item, i) => {{
                        if (now >= item.s && now <= item.e) {{
                            item.el.className = 'word highlight';
                            if (i % 4 === 0) item.el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        }} else if (now > item.e) {{
                            item.el.className = 'word past';
                        }} else {{
                            item.el.className = 'word';
                        }}
                    }});
                }};
            </script>
        </body>
        </html>
        """
        with open(output_name, "w", encoding="utf-8") as f:
            f.write(html_template)
        print(f"🚀 HTML listo en: {output_name}")

    def ejecutar_todo(self, url, idioma='en', velocidad=0.85):
        audio = self.descargar_audio(url, velocidad)
        datos = self.transcribir_palabras(audio, idioma=idioma)
        self.generar_html_web(audio, datos)
        print("\n✅ Proceso completado con faster-whisper.")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    app = KaraokeFasterWhisper(model_size="base", device="cpu", compute_type="int8")
    
    video_url = "https://www.youtube.com/watch?v=w4rG5GY9IlA" 
    app.ejecutar_todo(video_url, idioma="en", velocidad=0.85)