#!/bin/bash

echo "🧹 Limpiando archivos temporales..."
rm -f debug_files/last_input.*
rm -rf src/__pycache__

echo "🔄 Reiniciando Chainlit (English Tutor)..."
echo "   (Presiona Ctrl+C en la terminal donde está corriendo Chainlit y ejecuta este script)"
echo ""
echo "📝 Para iniciar la aplicación:"
echo "   chainlit run app.py"
echo ""
echo "✅ Mejoras activas:"
echo "   ✓ Arquitectura Modular (src/)"
echo "   ✓ Tutor de Inglés 'Emma' activado"
echo "   ✓ Fallback de subida de archivos"
echo "   ✓ Configuración de audio optimizada (44.1kHz)"
