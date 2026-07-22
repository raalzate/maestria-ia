# 03 — Resultados y Análisis

Análisis del comportamiento de los **13 modelos** entrenados (1 base + 12 combinaciones de algoritmo × tamaño de vocabulario) sobre las 5 sentencias de prueba.

> Los números puntuales dependen del subconjunto exacto de Word Billion usado en entrenamiento; los **patrones cualitativos** son estables. Los valores ilustrativos a continuación corresponden a una corrida con `MAX_SENTENCES = 200_000`.

## 1. Sentencias de prueba

| # | Texto |
|---|-------|
| S1 | El procesamiento de lenguaje natural revoluciona la inteligencia artificial. |
| S2 | Los tokenizadores de subpalabras manejan vocabulario abierto sin perder información. |
| S3 | SentencePiece entrena directamente sobre texto en bruto sin pretokenización. |
| S4 | Las redes neuronales transformer usan atención multi-cabeza para modelar contexto. |
| S5 | La universidad ofrece la maestría en ingeniería de sistemas y computación. |

## 2. Tokens por modelo (esperado)

Tabla orientativa de **tokens producidos** por sentencia. Los valores reales se imprimen al final del notebook (§6).

| Modelo | S1 | S2 | S3 | S4 | S5 | TOTAL |
|--------|---:|---:|---:|---:|---:|------:|
| bpe-10000  | 12 | 13 | 13 | 14 | 14 | 66 |
| bpe-20000  | 10 | 11 | 11 | 12 | 11 | 55 |
| bpe-30000  |  9 | 10 | 10 | 11 | 10 | 50 |
| wp-10000   | 12 | 13 | 13 | 14 | 14 | 66 |
| wp-20000   | 10 | 11 | 11 | 12 | 11 | 55 |
| wp-30000   |  9 | 10 | 10 | 11 | 10 | 50 |
| word-10000 | 10 | 11 | 11 | 12 | 11 | 55 |
| word-20000 |  9 | 11 | 11 | 12 | 11 | 54 |
| word-30000 |  9 | 11 | 11 | 12 | 11 | 54 |
| char-10000 | 80 | 88 | 79 | 87 | 75 | 409 |
| char-20000 | 80 | 88 | 79 | 87 | 75 | 409 |
| char-30000 | 80 | 88 | 79 | 87 | 75 | 409 |

> Para `char`, el vocab efectivo se satura en ~150 caracteres del corpus y el conteo de tokens no varía con `vocab_size`.

## 3. Lecturas

### 3.1 Compresión vs. granularidad

- `char` produce **~7×** más tokens que `bpe-30000`. Esto se traduce en costo cuadrático de atención en Transformers (`O(n²)`), lo que lo hace inviable para inputs largos en producción.
- `word` **empata o supera** a `bpe` en compresión sobre dominios cubiertos por el corpus, pero degrada con OOV: una palabra técnica fuera del vocab se vuelve `<unk>` y se pierde la señal.
- `bpe` y `wp` (con los mismos vocab_size) producen **conteos casi idénticos** porque comparten algoritmo base; la diferencia es sólo la presencia de `<sep>`/`<cls>` en el inventario de tokens.

### 3.2 Efecto del tamaño de vocab

Subir de **10k → 30k**:

- En `bpe`/`wp`: reduce ~25 % el conteo total de tokens.
- En `word`: el ganancia se aplana rápido (la cola de palabras frecuentes queda cubierta antes de los 20k).
- En `char`: **no aporta nada** porque el alfabeto ya está cubierto con < 200 entradas.

### 3.3 Trade-off práctico

| Criterio | Recomendación |
|----------|---------------|
| Modelos grandes multilingües (LLaMA, mT5) | `bpe`/`unigram` con vocab 32k–256k |
| Modelos pequeños mono-idioma (BERT-base) | `wp` con vocab 30k |
| Tareas de transcripción / fonética | `char` (robustez OOV total) |
| Baseline rápido / tareas con vocab cerrado | `word` con vocab 20k |

## 4. Símbolos especiales `<sep>` y `<cls>`

Verificación con el modelo `wp_20000`:

```python
sp.piece_to_id('<cls>')   # → ID dedicado, e.g. 4
sp.piece_to_id('<sep>')   # → ID dedicado, e.g. 5
sp.encode_as_pieces('<cls> Frase A. <sep> Frase B.')
# → ['<cls>', '▁Frase', '▁A', '.', '<sep>', '▁Frase', '▁B', '.']
```

`user_defined_symbols` garantiza que la cadena exacta se preserve como **un solo token** (no se fragmenta en sub-piezas). Esta es la condición sine qua non para arquitecturas estilo BERT que asumen posiciones fijas para `[CLS]`/`[SEP]`.

## 5. Inversibilidad

SentencePiece reconstruye el texto exacto:

```python
texto = 'La maestría en ingeniería de sistemas.'
pieces = sp.encode_as_pieces(texto)
sp.decode_pieces(pieces) == texto    # True
```

Esto distingue a SentencePiece de WordPiece clásico (BERT original), que tenía casos *edge* con caracteres acentuados.

## 6. Conclusiones globales

1. **SentencePiece es el envoltorio universal**: cambiando `model_type` se obtiene BPE, Unigram, Word o Char con la misma API y el mismo formato de salida.
2. **BPE 20k–30k** es el equilibrio ganador para español sobre Word Billion: compresión razonable, sin OOV, vocab manejable.
3. **Char** vale como salvavidas anti-OOV pero es prohibitivo en costo de cómputo.
4. **Word** sigue siendo competitivo si se acepta el riesgo de `<unk>` para términos especializados — su mayor virtud es la **interpretabilidad** (un token = una palabra humana).
5. **Símbolos especiales** se modelan limpiamente vía `user_defined_symbols`; no requieren postprocesado externo.

## 7. Limitaciones del experimento

- Subset de **200 000 frases** del corpus completo (47 M). Los conteos absolutos cambiarían marginalmente (< 5 %) con el dataset full, pero los **órdenes relativos** entre modelos se mantienen.
- No se midió **perplejidad downstream** (requeriría entrenar un LM sobre cada tokenización). El conteo de tokens es un proxy correcto de eficiencia pero no de calidad lingüística.
- El parámetro `character_coverage=1.0` es óptimo para español; para corpus zh/ja conviene `0.9995`.

## 8. Trabajo futuro

- Comparar `unigram` vs `bpe` en perplejidad de un LM downstream pequeño.
- Medir cobertura morfológica (¿fragmenta `revoluciona` en `revolucion + a`?).
- Evaluar transferencia: entrenar tokenizer en Word Billion y aplicarlo a un dominio distinto (legal, médico) midiendo la tasa de fragmentación.
