# 01 — Marco Teórico

## 1. Tokenización en PLN

La **tokenización** es el primer eslabón de cualquier pipeline de Procesamiento de Lenguaje Natural: convierte una secuencia continua de caracteres en una lista discreta de unidades (tokens) que el modelo manipula como vectores. La elección del esquema de tokenización condiciona:

- **Tamaño de la matriz de embeddings** (vocab × dim).
- **Longitud media de la secuencia** que verá el modelo (afecta atención cuadrática).
- **Capacidad de manejar palabras desconocidas** (OOV) y morfología.
- **Transferencia entre idiomas** (cobertura unicode, scripts no latinos).

### 1.1 Familia de algoritmos

| Estrategia | Unidad | Ventaja | Desventaja |
|------------|--------|---------|------------|
| Carácter | 1 char | Sin OOV, vocab mínimo (~100) | Secuencias muy largas, pierde semántica de palabra |
| Palabra | palabra completa | Semántica directa | Vocab enorme, OOV severo, mal con flexión |
| Subpalabra | morfemas / fragmentos | Balance: poco OOV + secuencias razonables | Requiere entrenamiento, no siempre lingüísticamente coherente |
| Byte | 1 byte UTF-8 | Universal multi-idioma | Secuencias todavía más largas que char |

Los modelos *state-of-the-art* (BERT, GPT, T5, LLaMA) usan **subpalabra**.

## 2. Byte-Pair Encoding (BPE)

Algoritmo de compresión re-purposed para PLN por **Sennrich, Haddow & Birch (2016)** en *"Neural Machine Translation of Rare Words with Subword Units"* (ACL 2016).

### 2.1 Algoritmo

```
1. Inicializa vocab = {todos los caracteres del corpus}
2. Cuenta frecuencia de pares adyacentes en el corpus tokenizado por carácter
3. Fusiona el par más frecuente en un nuevo símbolo
4. Repite 2–3 hasta alcanzar |vocab| objetivo
```

### 2.2 Propiedades

- **Determinista**: el mismo corpus + tamaño objetivo → mismas fusiones.
- **Greedy**: nunca revisita decisiones previas.
- **Vocab abierto**: cualquier palabra es representable como secuencia de subpiezas (en último caso, caracteres).

### 2.3 Ejemplo

Corpus pequeño: `low low lowest newer wider`. Tras varias fusiones BPE puede producir:
`low`, `er`, `est`, `new`, `wid`, etc. La palabra OOV `lowering` se segmenta como `low + er + ing` si esos morfemas existen.

Modelos que lo usan: **GPT-2/3/4, RoBERTa, LLaMA**.

## 3. WordPiece

Variante de BPE introducida por **Schuster & Nakajima (2012)** y popularizada por **BERT (Devlin et al., 2018)**.

### 3.1 Diferencia clave con BPE

En vez de fusionar el par **más frecuente**, fusiona el par que **maximiza la verosimilitud** del corpus bajo un modelo de lenguaje unigrama:

$$\text{score}(A, B) = \frac{P(AB)}{P(A) \cdot P(B)}$$

Esto privilegia fusiones que reducen perplejidad, no solo frecuencia bruta.

### 3.2 Notación distintiva

WordPiece marca subpalabras internas con `##`:

- `tokenization` → `token`, `##ization`
- `playing` → `play`, `##ing`

### 3.3 Tokens especiales

BERT introduce símbolos de control que el preprocesamiento añade al input:

| Token | Función |
|-------|---------|
| `[CLS]` | Marca inicio; embedding agregado para clasificación de secuencia |
| `[SEP]` | Separador de segmentos (par de oraciones, pregunta/contexto) |
| `[PAD]` | Relleno hasta longitud fija |
| `[MASK]` | Posición enmascarada para MLM |
| `[UNK]` | Caracter / palabra fuera del vocab |

En el taller se replican `<sep>` y `<cls>` con `user_defined_symbols` de SentencePiece.

## 4. Modelo Unigram

Propuesto por **Taku Kudo (2018)** en *"Subword Regularization"* (ACL 2018). Es la base por defecto de SentencePiece.

### 4.1 Idea

Asume un **modelo de lenguaje de unigramas** sobre subpalabras y entrena las probabilidades con **EM (Expectation-Maximization)**:

1. Empieza con un vocabulario grande (semilla de subpalabras candidatas).
2. EM ajusta las probabilidades $p(x_i)$.
3. Poda iterativamente las subpalabras de menor utilidad (las que menos bajan la log-likelihood al eliminarlas) hasta llegar al `vocab_size` objetivo.

### 4.2 Ventaja: regularización por sub-palabra

A diferencia de BPE (segmentación única), Unigram puede **muestrear** segmentaciones alternativas en entrenamiento → actúa como *data augmentation*. Útil en NMT y modelos pequeños.

Modelos que lo usan: **ALBERT, T5, XLNet, mBART, mT5**.

## 5. SentencePiece

Implementación de Google (Kudo & Richardson, EMNLP 2018) que **unifica** BPE, Unigram, Word y Char bajo una misma API y resuelve dos problemas prácticos:

### 5.1 Procesa texto en bruto (sin pretokenizar)

BPE/WordPiece tradicionales asumen que el texto ya está dividido por espacios → fallan en idiomas sin separadores explícitos (japonés, chino, tailandés). SentencePiece **trata el espacio como un símbolo más** (`▁`, U+2581) e incluye sus propios algoritmos de segmentación.

### 5.2 Tokenización + destokenización determinista

La operación inversa siempre reconstruye el texto exacto (espacios incluidos):

```
encode("Hola mundo")  →  ["▁Hola", "▁mundo"]
decode(["▁Hola", "▁mundo"])  →  "Hola mundo"
```

Esto era un problema histórico en BERT (tokenizer no era inverso al detokenizer para algunas variantes Unicode).

### 5.3 Parámetros clave

| Parámetro | Significado |
|-----------|-------------|
| `model_type` | `unigram` (default), `bpe`, `word`, `char` |
| `vocab_size` | Tamaño del vocabulario (incluye special tokens) |
| `character_coverage` | Fracción de caracteres del corpus a cubrir; `1.0` para idiomas con alfabeto pequeño (es, en); `0.9995` recomendado para zh/ja |
| `model_prefix` | Nombre base de los artefactos de salida (`<prefix>.model`, `<prefix>.vocab`) |
| `user_defined_symbols` | Tokens preservados como unidad cuando aparecen en el texto (e.g. `<sep>`, `<cls>`) |
| `control_symbols` | Tokens reservados que **nunca** aparecen en input pero tienen ID dedicado (los inserta el código del usuario) |
| `input_sentence_size` | Frases máximas a usar para entrenamiento (subsampling) |
| `shuffle_input_sentence` | Mezclar antes de subsamplear |

### 5.4 Modelos que lo usan

ALBERT, XLNet, MarianMT, T5, mT5, NLLB, LLaMA-2 multilingüe, Whisper.

## 6. Comparación conceptual rápida

```
Texto: "tokenización"

CHAR     : t o k e n i z a c i ó n             (12 tokens)
WORD     : tokenización                         (1 token, OOV si no estaba)
BPE      : token ización                        (2 tokens, fusiones por frecuencia)
WordPiece: token ##ización                      (2 tokens, fusiones por verosimilitud)
Unigram  : tokeni zación   /   token ización    (varias segmentaciones probabilísticas)
```

## 7. Dataset Word Billion (Spanish Billion Words)

- Corpus de ~**1 800 millones** de tokens en español, derivado de Wikipedia y otras fuentes web.
- Variante limpia en HF: `jhonparra18/spanish_billion_words_clean` — ~47 M oraciones, ~4.7 GB.
- Es un *standard* en NLP en español (similar al rol de WikiText-103 en inglés).
- Por su tamaño, es práctica obligada **trocearlo en archivos** y usar `streaming=True` + `input_sentence_size` al entrenar.

## 8. Referencias

1. Sennrich, R., Haddow, B., Birch, A. (2016). *Neural Machine Translation of Rare Words with Subword Units*. ACL.
2. Schuster, M., Nakajima, K. (2012). *Japanese and Korean voice search*. ICASSP.
3. Kudo, T. (2018). *Subword Regularization: Improving Neural Network Translation Models with Multiple Subword Candidates*. ACL.
4. Kudo, T., Richardson, J. (2018). *SentencePiece: A simple and language independent subword tokenizer*. EMNLP demo.
5. Devlin, J. et al. (2018). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*.
6. HuggingFace Tokenizers docs — <https://huggingface.co/docs/tokenizers>.
7. SentencePiece repo — <https://github.com/google/sentencepiece>.
