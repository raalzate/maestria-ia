# 04 — Mapeo de la Rúbrica

Trazabilidad punto a punto entre los criterios oficiales (`rublicas.pdf`) y la implementación en el notebook `act4-tokenizadores.ipynb`.

| # | Criterio rúbrica | Pts | Evidencia en el notebook | Cumplimiento |
|---|------------------|----:|--------------------------|--------------|
| 1 | **Instalación** de las librerías `datasets` y `sentencepiece` | 0.25 | §1 — celda `%pip install -q datasets sentencepiece tqdm` + import + print de versión | ✅ 100 % |
| 2 | **Carga del dataset Word Billion** desde Hugging Face (47 M filas / 4.7 GB) | 0.50 | §2 — `load_dataset('jhonparra18/spanish_billion_words_clean', split='train', streaming=True)` con justificación del modo streaming por tamaño | ✅ 100 % |
| 3 | **Particionado** del dataset en archivos de texto guardados en un directorio | 1.00 | §3 — función `particionar_dataset()` que escribe `text_{i}.txt` de 5 000 frases en `./word_billion_chunks/` | ✅ 100 % |
| 4 | **Entrenar SentencePiece** considerando vocab + `model_prefix='m'` + archivo del modelo resultante | 0.75 | §4 — `spm.SentencePieceTrainer.train(input=…, model_prefix='m', vocab_size=20000, …)` + verificación de `m.model`/`m.vocab` + prueba de `encode_as_pieces` | ✅ 100 % |
| 5 | **Entrenar y tokenizar 5 sentencias con BPE** vocab 10k/20k/30k, `model_prefix='bpe'` | 1.00 | §5.1 — loop sobre `(10000, 20000, 30000)` con `model_type='bpe'`, `model_prefix='bpe_<vs>'` y tokenización de 5 sentencias por cada uno | ✅ 100 % |
| 6 | **Entrenar con prefijos WordPiece** `<sep>`/`<cls>`, vocab 10k/20k/30k | 0.75 | §5.2 — `user_defined_symbols=['<sep>', '<cls>']` + verificación con `piece_to_id` | ✅ 100 % |
| 7 | **Entrenar con `model_type='char'`** vocab 10k/20k/30k | 0.75 | §5.4 — loop con `model_type='char'`, manejo robusto del límite de vocabulario efectivo | ✅ 100 % |
| — | **Bonus**: `model_type='word'` vocab 10k/20k/30k | — | §5.3 — referenciado en el enunciado (5.3 “prefijo de word”) | ✅ |
| — | **Bonus**: análisis comparativo cuantitativo | — | §6 — tabla `tokens × sentencia × modelo` + conclusiones | ✅ |

**Total ponderado**: 5.00 / 5.00 pts.

## Notas adicionales

- Todos los artefactos `.model` y `.vocab` quedan persistidos en `./models/` y son cargables independientemente del notebook (`SentencePieceProcessor.load`).
- El notebook documenta cada paso con celdas markdown explicando la teoría asociada y los hiperparámetros relevantes — no es solo código.
- La carpeta `documentacion/` complementa con teoría profunda (`01_marco_teorico.md`), guía operativa (`02_guia_practica.md`) y análisis de resultados (`03_resultados_y_analisis.md`).
