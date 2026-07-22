# 02 — Guía Práctica

Manual de ejecución del notebook `act4-tokenizadores.ipynb`.

## 1. Requisitos

- **Python ≥ 3.10**
- **RAM**: ≥ 4 GB (con `MAX_SENTENCES = 200_000`); ≥ 32 GB para correr con el dataset completo.
- **Disco libre**: ~500 MB con el subset; ~6 GB con el dataset full.
- **Conexión a Internet** para la primera ejecución (descarga del dataset desde HF Hub).

## 2. Entorno recomendado

### 2.1 Local

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate            # Windows

pip install -q datasets sentencepiece tqdm jupyter
jupyter lab
```

### 2.2 Google Colab

Subir el notebook tal cual; las instalaciones son idempotentes (`%pip install -q ...`). Si se requiere persistencia de los modelos:

```python
from google.colab import drive
drive.mount('/content/drive')
MODELS_DIR = pathlib.Path('/content/drive/MyDrive/act4_models')
```

## 3. Orden de ejecución

Las celdas están secuenciadas; ejecutar **de arriba hacia abajo** (`Run All` también funciona). Tiempos aproximados con `MAX_SENTENCES = 200_000` en CPU moderna:

| Sección | Operación | Tiempo aprox. |
|---------|-----------|---------------|
| §1 | `pip install` | 30 s |
| §2 | Carga streaming HF | < 5 s |
| §3 | Particionado 200k frases | 1–3 min |
| §4 | Entrenamiento base (vocab 20k) | 2–4 min |
| §5.1 | 3 modelos BPE | 6–10 min |
| §5.2 | 3 modelos WP-style | 6–10 min |
| §5.3 | 3 modelos word | 4–6 min |
| §5.4 | 3 modelos char | 1–2 min |
| §6 | Tabla resumen | < 1 s |
| **Total** | | **~25–40 min** |

## 4. Parámetros configurables

Editar las constantes al inicio de cada sección:

```python
DATASET_NAME   = 'jhonparra18/spanish_billion_words_clean'
MAX_SENTENCES  = 200_000   # None ⇒ dataset completo
CHUNK_SIZE     = 5_000     # frases por archivo de texto
```

Para subir vocab o cambiar tipo de modelo, modificar la celda correspondiente:

```python
spm.SentencePieceTrainer.train(
    input=input_files,
    model_prefix='mi_modelo',
    vocab_size=32000,
    model_type='unigram',           # bpe | unigram | word | char
    character_coverage=1.0,
    input_sentence_size=200_000,
    shuffle_input_sentence=True,
)
```

## 5. Estructura de salida

Tras ejecutar el notebook se generan dos directorios:

```
taller/
├── word_billion_chunks/
│   ├── text_0.txt        # 5 000 frases
│   ├── text_1.txt
│   └── ...
└── models/
    ├── m.model           ├── m.vocab
    ├── bpe_10000.model   ├── bpe_10000.vocab
    ├── bpe_20000.model   ├── bpe_20000.vocab
    ├── bpe_30000.model   ├── bpe_30000.vocab
    ├── wp_10000.model    ├── wp_10000.vocab
    ├── wp_20000.model    ├── wp_20000.vocab
    ├── wp_30000.model    ├── wp_30000.vocab
    ├── word_10000.model  ├── word_10000.vocab
    ├── word_20000.model  ├── word_20000.vocab
    ├── word_30000.model  ├── word_30000.vocab
    ├── char_10000.model  ├── char_10000.vocab
    ├── char_20000.model  ├── char_20000.vocab
    └── char_30000.model  └── char_30000.vocab
```

`.model` = blob binario que carga `SentencePieceProcessor`.  
`.vocab` = TSV `token<TAB>log_prob` legible para inspección.

## 6. Cargar un modelo entrenado

```python
import sentencepiece as spm

sp = spm.SentencePieceProcessor()
sp.load('models/bpe_20000.model')

print(sp.encode_as_pieces('Hola mundo'))
print(sp.encode_as_ids('Hola mundo'))
print(sp.decode_pieces(['▁Hola', '▁mundo']))
print('Vocab size:', sp.get_piece_size())
```

## 7. Troubleshooting

### 7.1 `RuntimeError: Vocabulary size too small`
**Síntoma**: aparece en `model_type='char'` o `'word'` cuando se pide un `vocab_size` superior al número real de unidades distintas en el corpus.  
**Solución**: el notebook captura la excepción y reentrenar con un tamaño efectivo. Para `char` típico es ~150–500 caracteres únicos.

### 7.2 OOM al particionar
**Síntoma**: el kernel muere en §3.  
**Solución**: bajar `MAX_SENTENCES` o `CHUNK_SIZE` (e.g. 2 000 frases por archivo). El streaming evita cargar el dataset entero en RAM, pero `text_data.append` sí acumula en memoria entre dumps.

### 7.3 Descarga lenta del dataset
**Síntoma**: `load_dataset` se demora.  
**Solución**: usar caché local de HF (`HF_HOME=/path/to/cache`) y ejecutar una sola vez; `streaming=True` evita la materialización completa pero el iterador igual lee del Hub.

### 7.4 `_sentencepiece.Decode()` returns extra spaces
SentencePiece reemplaza los espacios por `▁` y los reconstruye al decodificar. Si en una versión vieja se observa pérdida de espacios, actualizar:

```bash
pip install --upgrade sentencepiece
```

### 7.5 GPU no se usa
SentencePiece **es CPU-only por diseño** (entrenamiento basado en estadísticas, no en gradiente). No hace falta GPU; en Colab basta el runtime estándar.

## 8. Reproducibilidad

SentencePiece es **determinista** dado:

1. Mismo corpus de entrada (mismo orden de archivos).
2. Misma configuración de hiperparámetros.
3. Misma versión de la librería.

Pero `streaming=True` desde HF puede entregar muestras en orden distinto si el dataset cambia. Para reproducibilidad estricta, fijar la semilla del shuffle:

```python
spm.SentencePieceTrainer.train(
    ...,
    seed_sentencepiece_size=1_000_000,
    random_seed=42,
)
```

## 9. Limpieza

Para liberar disco tras la entrega:

```bash
rm -rf word_billion_chunks/ models/
```

Los `.model` ocupan entre 200 KB (`char`) y 2 MB (`bpe_30000`); los chunks de texto pueden sumar varios cientos de MB según `MAX_SENTENCES`.
