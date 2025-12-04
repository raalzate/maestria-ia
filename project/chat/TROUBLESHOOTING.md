# 🐛 Guía de Solución de Problemas de Audio

## Problema Identificado

El error de FFmpeg ocurre cuando el navegador envía archivos de audio corruptos (llenos de bytes nulos `0x00`) en lugar de datos de audio válidos.

## ✅ Mejoras Implementadas

### 1. **Detección Temprana de Corrupción**
- Validación automática de bytes nulos antes de procesar
- Mensajes de error claros con soluciones específicas

### 2. **Mejor Detección de Formato**
- Análisis mejorado de magic bytes (12 bytes en lugar de 4)
- Soporte para múltiples formatos: WebM, MP4, MP3, WAV, OGG

### 3. **Validación con FFprobe**
- Verificación del formato antes de intentar la conversión
- Mensajes de error descriptivos con posibles causas

### 4. **Configuración Optimizada de Chainlit**
```toml
[features.audio]
   enabled = true
   min_duration = 500        # 0.5 segundos mínimo
   max_duration = 60000      # 60 segundos máximo
   chunk_duration = 2000     # Chunks más grandes = menos fragmentación
   sample_rate = 48000       # Sample rate estándar para WebM
```

### 5. **Herramienta de Diagnóstico**
- Script Python: `diagnose_audio.py`
- Página web: `public/audio_debug.html`

## 🔧 Soluciones

### Opción 1: Usar la Herramienta de Debug Web

1. Inicia tu aplicación Chainlit:
   ```bash
   chainlit run app.py
   ```

2. Abre en tu navegador:
   ```
   http://localhost:8000/public/audio_debug.html
   ```

3. Haz clic en "Start Recording" y prueba tu micrófono
4. La herramienta te dirá si el audio es válido o corrupto

### Opción 2: Probar con Diferentes Navegadores

**Navegadores Recomendados (en orden de compatibilidad):**
1. ✅ **Google Chrome** - Mejor soporte para WebM/Opus
2. ✅ **Firefox** - Buen soporte general
3. ⚠️ **Safari** - Puede tener problemas con formatos

### Opción 3: Verificar Permisos del Sistema

#### macOS:
1. Abre `Preferencias del Sistema` → `Seguridad y Privacidad`
2. Ve a la pestaña `Privacidad`
3. Selecciona `Micrófono` en el panel izquierdo
4. Asegúrate de que tu navegador tenga permiso ✅

#### Navegador (Chrome):
1. Haz clic en el candado 🔒 en la barra de direcciones
2. Verifica que "Micrófono" esté en "Permitir"
3. Si está bloqueado, cámbialo a "Permitir" y recarga la página

### Opción 4: Diagnóstico Manual de Archivos

Si ya tienes archivos problemáticos en `debug_files/`:

```bash
cd /Users/raul.alzate/Documents/maestria/maestria/project/chat
python3 diagnose_audio.py debug_files/last_input.webm
```

Esto te mostrará:
- ✓ Tamaño del archivo
- ✓ Magic bytes (formato)
- ✓ Resultado de FFprobe
- ✓ Intento de conversión con FFmpeg

## 🎯 Próximos Pasos

### Problema Detectado: Audio Corrupto (100% bytes nulos)

Si ves que el archivo está corrupto, prueba:

1. **Recargar la página completamente** (Cmd+Shift+R / Ctrl+Shift+F5)
2. **Cerrar otras aplicaciones** que usen el micrófono (Zoom, Teams, etc.)
3. **Probar con otro navegador**
4. **Verificar que el micrófono funciona** en otra aplicación (QuickTime, etc.)

### Si el Problema Persiste

Puede ser un problema de Chainlit con el manejo de audio en tu navegador específico.

**Workaround alternativo:**
Usa el drag & drop de archivos de audio en lugar del micrófono:
1. Graba tu audio con cualquier app (Voice Memos, QuickTime, etc.)
2. Arrastra el archivo a la ventana del chat
3. Chainlit lo procesará correctamente

## 📊 Logs Útiles

El código ahora imprime información detallada en la consola:

```
🔍 MAGIC BYTES (12 bytes): 1A45DFA3...
📊 Tamaño del audio: 57344 bytes
📊 Análisis de corrupción: 2.5% bytes nulos
📂 Archivo de entrada: debug_files/last_input.webm (57344 bytes)
🔍 Verificando formato del archivo con ffprobe...
✅ Formato verificado correctamente
🛠️ Convirtiendo debug_files/last_input.webm -> debug_files/last_input.webm.converted.wav
🎯 Transcribiendo con Whisper...
✅ Transcripción completada: 145 caracteres
```

## 🔍 Entendiendo los Errores

### Error 1: "Audio corrupto detectado (90%+ bytes nulos)"
- **Causa:** El navegador no capturó audio real
- **Solución:** Verificar permisos de micrófono

### Error 2: "FFprobe Error: Invalid data found"
- **Causa:** Formato de archivo no válido
- **Solución:** El nuevo código ya detecta esto antes de llegar a FFmpeg

### Error 3: "Whisper no escuchó nada"
- **Causa:** Audio válido pero silencioso
- **Solución:** Habla más cerca del micrófono, verifica volumen

## 📝 Notas Adicionales

- Los archivos de debug se guardan en `debug_files/` para inspección manual
- El formato WebM es el más común en navegadores modernos
- El sample rate de 48kHz es el estándar para WebM
- Los chunks de 2 segundos reducen la fragmentación

## 🆘 Soporte

Si sigues teniendo problemas, revisa:
1. Los archivos en `debug_files/`
2. Los logs en la consola del navegador (F12 → Console)
3. Los logs en la terminal donde ejecutas Chainlit
