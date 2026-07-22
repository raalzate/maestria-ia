# 05 — Embeddings densos y semántica vectorial escalada

Complemento del [01_marco_teorico.md](01_marco_teorico.md). Cubre los temas del blog del curso que **no** son evaluados por el quiz Act 6 pero forman parte del marco conceptual: regresión logística en PLN, Word2Vec (algoritmo + Gensim), GloVe, fastText y embeddings profundos / de sentencias.

## 1. Regresión logística en PLN

### 1.1 Por qué importa

La regresión logística es el **clasificador discriminativo de referencia** en PLN clásico. Aparece como bloque base en:

- Clasificación de texto (spam, sentimiento, intención).
- Identificación de idioma.
- Etiquetado de relevancia en IR.
- Capas de salida de modelos neuronales (softmax = generalización multiclase).

### 1.2 Modelo

Dado un vector de features `x ∈ ℝⁿ` (típicamente TF-IDF o un embedding promedio):

$$ P(y=1 \mid x) = \sigma(w^\top x + b), \quad \sigma(z) = \frac{1}{1 + e^{-z}} $$

- `w ∈ ℝⁿ`: pesos aprendidos por término/dimensión.
- `b ∈ ℝ`: sesgo.
- `σ`: función logística (squash a [0,1]).

### 1.3 Entrenamiento

Maximización de la **log-verosimilitud condicional** (equivalente a minimizar *cross-entropy*):

$$ \mathcal{L}(w) = -\frac{1}{N} \sum_{i=1}^{N} \big[ y_i \log \hat{y}_i + (1-y_i) \log(1-\hat{y}_i) \big] + \lambda \lVert w \rVert_2^2 $$

Optimización: SGD, L-BFGS o liblinear. La regularización L2 (`λ`) evita overfitting cuando `n ≫ N`.

### 1.4 Multiclase: softmax

Para `K` clases:

$$ P(y=k \mid x) = \frac{e^{w_k^\top x}}{\sum_{j=1}^{K} e^{w_j^\top x}} $$

Esta es la capa terminal de Word2Vec (CBOW/Skip-gram con softmax completo) y de prácticamente todo clasificador neuronal.

### 1.5 Conexión con la semántica vectorial

Si `x = TF-IDF(d)`, la regresión logística aprende qué términos correlacionan con cada clase — los pesos `w_k[i]` son interpretables como "evidencia del término `i` a favor de la clase `k`". Para problemas con vocabulario alto-dimensional y poca data, suele superar a redes profundas por su sesgo inductivo lineal y su regularización fuerte.

## 2. Word2Vec — el cambio de paradigma

Mikolov *et al.* (2013) — *"Efficient Estimation of Word Representations in Vector Space"* (Google). Reemplazó la matriz dispersa de TF-IDF por **vectores densos** (~100–300 dim) aprendidos por una red shallow que predice contextos.

### 2.1 Dos arquitecturas

| Variante | Predice | Mejor para |
|----------|---------|------------|
| **CBOW** (Continuous Bag-of-Words) | la palabra dado su contexto | corpora pequeños, palabras frecuentes |
| **Skip-gram** | el contexto dado la palabra | corpora grandes, palabras raras |

### 2.2 Skip-gram en detalle

Dado un par `(w_t, w_{t+j})` con `j ∈ [-c, c] \ {0}` (ventana de contexto `c`):

$$ J(\theta) = -\frac{1}{T} \sum_{t=1}^{T} \sum_{-c \le j \le c, j \ne 0} \log P(w_{t+j} \mid w_t) $$

Con softmax pleno:

$$ P(w_O \mid w_I) = \frac{\exp(v'_{w_O}{}^\top v_{w_I})}{\sum_{w=1}^{|V|} \exp(v'_w{}^\top v_{w_I})} $$

Cada palabra tiene **dos** vectores: `v_w` (input) y `v'_w` (output). Tras entrenar se usa solo `v_w` o la suma.

### 2.3 Negative Sampling — el truco que lo hace viable

Softmax con `|V| ≈ 10⁶` es prohibitivo. Mikolov *et al.* reemplazan el denominador por una muestra de `k` "palabras negativas" (no aparecen en el contexto real):

$$ \log \sigma(v'_{w_O}{}^\top v_{w_I}) + \sum_{i=1}^{k} \mathbb{E}_{w_i \sim P_n(w)} \big[ \log \sigma(-v'_{w_i}{}^\top v_{w_I}) \big] $$

- `P_n(w) ∝ U(w)^{3/4}`: distribución de unigramas suavizada.
- `k = 5–20` para corpora pequeños, `2–5` para grandes.
- Reduce complejidad de `O(|V|)` a `O(k)` por paso.

### 2.4 Subsampling de palabras frecuentes

Cada palabra `w` se descarta del corpus con probabilidad:

$$ P_{drop}(w) = 1 - \sqrt{\frac{t}{f(w)}} $$

con `t ≈ 10⁻⁵`. Elimina ruido de `the`, `of`, `and` — análogo al efecto de IDF en TF-IDF.

### 2.5 Propiedades emergentes

Las direcciones del espacio capturan **relaciones lineales**:

```
king - man + woman ≈ queen
Paris - France + Italy ≈ Rome
```

Este comportamiento (analogías por aritmética vectorial) fue la prueba empírica que detonó la transición de bag-of-words a embeddings densos.

## 3. Word2Vec con Gensim

### 3.1 Instalación y carga

```python
!pip install gensim
from gensim.models import Word2Vec
from gensim.utils import simple_preprocess
```

### 3.2 Entrenamiento desde cero

```python
sentences = [simple_preprocess(line) for line in corpus_lines]

model = Word2Vec(
    sentences=sentences,
    vector_size=100,    # dim del embedding
    window=5,           # ventana de contexto
    min_count=5,        # ignora palabras con freq < 5
    sg=1,               # 0=CBOW, 1=Skip-gram
    negative=10,        # k de negative sampling
    sample=1e-3,        # subsampling threshold
    epochs=10,
    workers=4,
)

model.save('w2v.model')
```

### 3.3 Consultas típicas

```python
model.wv['battle']                          # vector (100,)
model.wv.most_similar('battle', topn=5)     # vecinos por coseno
model.wv.similarity('battle', 'war')        # similitud coseno
model.wv.doesnt_match(['battle','war','peace','sword'])  # outlier
model.wv.most_similar(positive=['king','woman'], negative=['man'])  # analogía
```

### 3.4 Cargar embeddings preentrenados

```python
import gensim.downloader as api
wv = api.load('word2vec-google-news-300')   # 3.6 GB, 3M tokens
wv = api.load('glove-wiki-gigaword-100')    # 128 MB
```

### 3.5 Vector de documento

Para representar un documento, lo más simple es **promedio** de embeddings de sus palabras:

```python
import numpy as np
def doc_vec(tokens, wv):
    vs = [wv[t] for t in tokens if t in wv]
    return np.mean(vs, axis=0) if vs else np.zeros(wv.vector_size)
```

Alternativas: SIF (Arora 2017), weighted average por IDF, *doc2vec* (Le & Mikolov 2014).

## 4. GloVe — Global Vectors

Pennington, Socher, Manning (2014) — Stanford. GloVe combina lo mejor de los modelos basados en **conteo global** (LSA) y los **predictivos locales** (Word2Vec).

### 4.1 Idea central

Aprende embeddings tal que el **producto punto reproduzca el log-ratio de probabilidades de co-ocurrencia**:

$$ w_i^\top \tilde{w}_j + b_i + \tilde{b}_j = \log X_{ij} $$

donde `X_{ij}` es la frecuencia con que `i` y `j` co-ocurren dentro de una ventana en el corpus.

### 4.2 Función de pérdida

$$ J = \sum_{i,j} f(X_{ij}) \big( w_i^\top \tilde{w}_j + b_i + \tilde{b}_j - \log X_{ij} \big)^2 $$

con `f(x) = min((x/x_max)^α, 1)` (típicamente `α=0.75`, `x_max=100`) para no dejar que pares ultra-frecuentes dominen.

### 4.3 Word2Vec vs GloVe

| Aspecto | Word2Vec | GloVe |
|---------|----------|-------|
| Señal | Pares locales (ventana) | Estadística global (matriz co-oc) |
| Entrenamiento | SGD streaming | Optimización sobre matriz pre-computada |
| Memoria | Baja | Alta (matriz `|V|²` dispersa) |
| Empirícamente | Mejor en analogías sintácticas | Mejor en similitudes semánticas |

### 4.4 Uso

GloVe publica embeddings preentrenados (Wikipedia + Gigaword, Common Crawl, Twitter):

```python
import gensim.downloader as api
glove = api.load('glove-wiki-gigaword-300')
glove.most_similar('shakespeare', topn=5)
```

## 5. fastText

Bojanowski, Grave, Joulin, Mikolov (2017) — Facebook AI. Extiende Word2Vec representando cada palabra como **suma de n-gramas de caracteres**.

### 5.1 Por qué subwords

Word2Vec/GloVe asignan un vector único por palabra → no funciona con:

- **OOV** (palabras no vistas durante entrenamiento).
- **Morfología rica** (español, alemán, finés, turco): `caminar`, `caminé`, `caminaríamos` se aprenden por separado.

### 5.2 Representación

Una palabra `w` se descompone en n-gramas con `n ∈ [3, 6]`, rodeada por `<` y `>`:

```
where → <wh, whe, her, ere, re>, <where>
```

El embedding de `w` es la suma de embeddings de sus n-gramas:

$$ \mathbf{v}_w = \sum_{g \in \mathcal{G}_w} \mathbf{z}_g $$

### 5.3 Ventajas

- **OOV**: una palabra nueva se compone de sus n-gramas — siempre hay vector.
- **Morfología**: `caminar` y `caminé` comparten n-gramas → vectores cercanos sin entrenamiento explícito.
- Entrenamiento similar a Skip-gram + negative sampling.

### 5.4 fastText supervisado

Además de embeddings, fastText incluye un clasificador de texto extremadamente rápido (lineal sobre el promedio de embeddings) que en muchos benchmarks iguala a redes profundas con `1000×` menos cómputo.

### 5.5 Uso

```python
from gensim.models import FastText
ft = FastText(sentences, vector_size=100, window=5, min_count=5, sg=1)
ft.wv['caminaríamos']   # funciona aunque no esté en el vocab
```

## 6. Embeddings profundos y de sentencias

### 6.1 Limitación de embeddings estáticos

Word2Vec/GloVe/fastText asignan **un único vector por palabra** independiente del contexto. Pero `banco` ≠ `banco` (institución financiera vs. asiento). Se requieren embeddings **contextuales**.

### 6.2 ELMo (2018)

Peters *et al.* — *Deep Contextualized Word Representations*. BiLSTM bidireccional preentrenado sobre Language Modeling. Cada palabra recibe vector dependiente de la oración completa.

### 6.3 BERT (2018)

Devlin *et al.* (Google) — *Bidirectional Encoder Representations from Transformers*. Marcó la transición a la era Transformer en PLN.

| Componente | Detalle |
|------------|---------|
| Arquitectura | Stack de encoders Transformer (12 o 24 capas) |
| Pre-training | **MLM** (predecir tokens enmascarados) + **NSP** (frase siguiente) |
| Tokens especiales | `[CLS]` (clasificación), `[SEP]` (separador) |
| Tokenización | WordPiece |
| Salida | Embedding contextual por token (768 o 1024 dim) |

El embedding del token `[CLS]` se usa como representación de la oración completa para clasificación.

### 6.4 Sentence-BERT (SBERT, 2019)

Reimers & Gurevych — siamese network sobre BERT entrenado con triplet loss / contrastive loss sobre pares de oraciones. Produce embeddings de **oración** comparables por coseno sin necesidad de pasar pares por el modelo (104× más rápido que BERT crudo en STS).

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embs = model.encode(['Henry V is about war', 'Twelfth Night is a comedy'])
from sklearn.metrics.pairwise import cosine_similarity
cosine_similarity([embs[0]], [embs[1]])
```

### 6.5 Familia post-BERT relevante

| Modelo | Año | Aporte |
|--------|-----|--------|
| RoBERTa | 2019 | BERT mejor entrenado, sin NSP |
| ALBERT | 2019 | Parámetros compartidos, menor footprint |
| DistilBERT | 2019 | Destilación, 40% más chico y 60% más rápido |
| GPT-3 / 4 | 2020+ | LM autoregresivos a escala; embeddings vía API |
| E5, BGE, MPNet | 2022+ | SBERT-style optimizados para recuperación |

### 6.6 Cuándo usar qué

| Caso | Recomendación |
|------|---------------|
| Pocas oraciones, vocabulario fijo, baseline | **TF-IDF + coseno** (este taller) |
| Similitud de palabras, idioma morfológico | **fastText** |
| Similitud semántica, recursos limitados | **GloVe / Word2Vec preentrenado** |
| Clasificación sentence-level con poca data | **SBERT + logistic regression** |
| Búsqueda semántica, RAG | **SBERT / E5 / BGE** + índice FAISS |
| Clasificación SOTA, recursos abundantes | **Fine-tune BERT/RoBERTa** |

## 7. Continuum conceptual

```
Conteo →   TF        TF-IDF       PPMI/LSA
          (raw)    (este taller)  (matriz)
                                       │
                                       ▼
              Predictivos  Word2Vec  GloVe   fastText
              (estáticos)  (locales) (global) (subword)
                                       │
                                       ▼
              Contextuales        ELMo  BERT  SBERT  GPT
              (dependen del input)
```

Cada salto resuelve una limitación del anterior:

1. **Raw → TF-IDF**: corregir el sesgo de palabras frecuentes (este taller).
2. **TF-IDF → Word2Vec**: pasar de vectores dispersos `|V|`-dim a densos `100`-dim, capturar relaciones semánticas.
3. **Word2Vec → fastText**: manejar OOV y morfología.
4. **Estático → BERT**: capturar polisemia y contexto.
5. **BERT → SBERT**: producir embeddings de oración comparables eficientemente.

## 8. Referencias

1. Mikolov, T., Chen, K., Corrado, G., Dean, J. (2013). *Efficient Estimation of Word Representations in Vector Space*. ICLR Workshop.
2. Mikolov, T., Sutskever, I., Chen, K., Corrado, G., Dean, J. (2013). *Distributed Representations of Words and Phrases and their Compositionality*. NeurIPS.
3. Pennington, J., Socher, R., Manning, C. (2014). *GloVe: Global Vectors for Word Representation*. EMNLP.
4. Bojanowski, P., Grave, E., Joulin, A., Mikolov, T. (2017). *Enriching Word Vectors with Subword Information*. TACL.
5. Peters, M. *et al.* (2018). *Deep Contextualized Word Representations*. NAACL.
6. Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. (2018). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. NAACL.
7. Reimers, N., Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP.
8. Jurafsky, D., Martin, J. (2024). *Speech and Language Processing*, Cap. 5 (Logistic Regression), Cap. 6 (Vector Semantics), Cap. 11 (BERT). <https://web.stanford.edu/~jurafsky/slp3/>
9. Řehůřek, R. (2010). *Software Framework for Topic Modelling with Large Corpora* — Gensim. LREC Workshop.
