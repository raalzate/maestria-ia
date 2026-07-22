# Documentación — Actividad 4: Tokenizador SentencePiece

Carpeta de soporte teórico-práctico para el notebook `act4-tokenizadores.ipynb`.

## Estructura

| Archivo | Contenido |
|---------|-----------|
| `01_marco_teorico.md` | Fundamentos: tokenización, BPE, WordPiece, Unigram, SentencePiece. |
| `02_guia_practica.md` | Cómo ejecutar el notebook paso a paso, parámetros y troubleshooting. |
| `03_resultados_y_analisis.md` | Análisis comparativo de los modelos entrenados y conclusiones. |
| `04_rubrica_mapeo.md` | Mapeo punto-a-punto entre los criterios de evaluación y las celdas del notebook. |

## Resumen de la actividad

Entrenar y comparar tokenizadores **SentencePiece** sobre el corpus `spanish_billion_words_clean` (Hugging Face), evaluando cuatro variantes del algoritmo (`bpe`, modelo con símbolos `<sep>`/`<cls>` estilo WordPiece, `word`, `char`) bajo tres tamaños de vocabulario (10 000, 20 000, 30 000) y midiendo la tokenización resultante sobre 5 oraciones de prueba.

## Entregables

- `act4-tokenizadores.ipynb` — notebook funcional.
- `documentacion/` — esta carpeta.
- `models/` (generado al ejecutar) — artefactos `.model` y `.vocab` de los 12+1 entrenamientos.
- `word_billion_chunks/` (generado al ejecutar) — corpus particionado en archivos de 5 000 frases.
