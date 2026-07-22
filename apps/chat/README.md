# Emma AI - Proyecto de Maestría

Este proyecto es un asistente de aprendizaje de inglés basado en IA (Emma) que utiliza LangGraph para la gestión de flujos conversacionales, Faster-Whisper para reconocimiento de voz y Edge-TTS para síntesis de voz.

## Estructura del Proyecto

```
chat/
├── app.py                  # Punto de entrada de la aplicación Chainlit
├── chainlit.md             # Configuración de la interfaz de Chainlit
├── requirements.txt        # Dependencias del proyecto
├── scripts/                # Scripts de utilidad
│   ├── create_env.sh       # Script para crear el entorno virtual
│   └── restart.sh          # Script para reiniciar la aplicación
├── src/                    # Código fuente principal
│   ├── audio/              # Transcripción y manejo de eventos de audio
│   ├── llm/                # Manejo del modelo Llama-3 (base y wrappers)
│   ├── features/           # Funcionalidades (grammar, suggestions, translations, tts)
│   ├── graph/              # Definición de grafos y nodos de LangGraph
│   ├── services/           # Servicios (progreso, etc.)
│   ├── config.py           # Configuraciones globales
│   └── utils.py            # Utilidades generales
├── data/                   # Almacenamiento de datos persistentes
│   └── user_progress/      # Progreso de los usuarios
├── public/                 # Archivos estáticos y generados
│   ├── templates/          # Plantillas HTML/JS
│   └── generated/          # Archivos dinámicos (audio, sugerencias, etc.)
├── tests/                  # Suite de pruebas unitarias y de integración
└── docs/                   # Documentación adicional
```

## Instalación y Uso

1. **Crear entorno**: `bash scripts/create_env.sh`
2. **Ejecutar**: `chainlit run app.py`

## Pruebas

Para ejecutar las pruebas:
```bash
./chat-env/bin/pytest tests/ -v
```
