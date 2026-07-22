# 03 — Resultados y Análisis

Análisis completo de los **5 puntos** del quiz sobre las obras de Shakespeare. Los valores aquí mostrados se reproducen exactamente al ejecutar `act6-semantica.ipynb` (no hay aleatoriedad).

## 1. Datos de entrada

Matriz término–documento `X ∈ ℝ^{4×4}` (filas: términos, columnas: obras):

|       | As You Like It | Twelfth Night | Julius Caesar | Henry V |
|-------|---------------:|--------------:|--------------:|--------:|
| battle | 1   | 0  |  7 | 13 |
| good   | 114 | 80 | 62 | 89 |
| fool   | 36  | 58 |  1 |  4 |
| wit    | 20  | 15 |  2 |  3 |

> Fuente: Jurafsky & Martin, *Speech and Language Processing* 3rd ed., Fig. 6.2.

## 2. Punto 1 — Matriz TF-IDF con normalización L2

### 2.1 Document frequency e IDF

| Término | df | idf clásica `log₁₀(N/df)` | idf suavizada `ln((1+N)/(1+df))+1` |
|---------|---:|--------------------------:|-----------------------------------:|
| battle | 3 | 0.1249 | **1.2231** |
| good   | 4 | 0      | **1.0000** |
| fool   | 4 | 0      | **1.0000** |
| wit    | 4 | 0      | **1.0000** |

> Adoptamos la **idf suavizada** (sklearn). La clásica produce vectores degenerados (sólo sobrevive la fila `battle`), lo que ilustra una limitación del corpus mínimo (4 documentos): cuando un término aparece en *todos*, la idf clásica lo anula.

### 2.2 Matriz TF·IDF (antes de L2)

|       | AYLI | TN | JC | HV |
|-------|-----:|---:|---:|---:|
| battle |  1.2231 |  0.0000 |  8.5620 | 15.9009 |
| good   | 114.000 | 80.000  | 62.000  | 89.000  |
| fool   |  36.000 | 58.000  |  1.000  |  4.000  |
| wit    |  20.000 | 15.000  |  2.000  |  3.000  |

### 2.3 Norma L2 por documento y matriz L2-normalizada

| Documento | ‖d‖₂ |
|-----------|------:|
| As You Like It | 121.2167 |
| Twelfth Night  |  99.9450 |
| Julius Caesar  |  62.6283 |
| Henry V        |  90.5475 |

**Matriz TF-IDF normalizada (cada columna unitaria):**

|       | AYLI    | TN      | JC      | HV      |
|-------|--------:|--------:|--------:|--------:|
| battle | 0.0101 | 0.0000 | 0.1367 | 0.1756 |
| good   | 0.9405 | 0.8004 | 0.9900 | 0.9829 |
| fool   | 0.2970 | 0.5803 | 0.0160 | 0.0442 |
| wit    | 0.1650 | 0.1501 | 0.0319 | 0.0331 |

## 3. Punto 2 — Similitud coseno con TF-IDF

|         | AYLI   | TN     | JC     | HV     |
|---------|-------:|-------:|-------:|-------:|
| AYLI    | 1.0000 | 0.9499 | 0.9424 | 0.9448 |
| TN      | 0.9499 | 1.0000 | 0.8065 | 0.8174 |
| JC      | 0.9424 | 0.8065 | 1.0000 | **0.9988** |
| HV      | 0.9448 | 0.8174 | **0.9988** | 1.0000 |

> **Novela más similar a `Henry V` (TF-IDF):** `Julius Caesar` con **0.9988**.

## 4. Punto 3 — Similitud coseno con frecuencias crudas

L2-norms crudas:

| Documento | ‖d‖₂ |
|-----------|------:|
| AYLI | 121.2147 |
| TN   |  99.9450 |
| JC   |  62.4340 |
| HV   |  90.0833 |

Matriz de similitud:

|         | AYLI   | TN     | JC     | HV     |
|---------|-------:|-------:|-------:|-------:|
| AYLI    | 1.0000 | 0.9499 | 0.9449 | 0.9490 |
| TN      | 0.9499 | 1.0000 | 0.8090 | 0.8216 |
| JC      | 0.9449 | 0.8090 | 1.0000 | **0.9991** |
| HV      | 0.9490 | 0.8216 | **0.9991** | 1.0000 |

> **Novela más similar a `Henry V` (raw):** `Julius Caesar` con **0.9991** (≈ 0.999, valor citado en el enunciado).

## 5. Punto 4 — Comparativa y respuestas

### 5.1 Tabla comparada `Henry V` vs resto

| Otra obra | cos (raw) | cos (TF-IDF) | Δ = tfidf − raw |
|-----------|----------:|-------------:|----------------:|
| As You Like It | 0.9490 | 0.9448 | −0.0042 |
| Twelfth Night  | 0.8216 | 0.8174 | −0.0042 |
| Julius Caesar  | 0.9991 | 0.9988 | −0.0003 |

El **orden** no cambia (`JC > AYLI > TN`), pero los valores absolutos bajan ligeramente con TF-IDF. La diferencia es minúscula porque tres de cuatro términos están en **todos** los documentos ⇒ su idf suavizada es 1 ⇒ no son penalizados realmente.

### 5.2 ¿Qué corrige TF-IDF? ¿Qué penaliza?

TF-IDF **multiplica** la frecuencia local de un término por el logaritmo del recíproco de su frecuencia documental:

$$ w_{t,d} = \text{tf}(t,d) \cdot \log\frac{N}{df(t)} $$

- **Corrige** el sesgo de las frecuencias crudas a favor de palabras **muy comunes** que aparecen en casi todos los documentos. Sin IDF, una palabra como `good`, presente en cualquier texto en inglés, distorsiona la geometría del espacio porque su magnitud bruta es enorme y arrastra el coseno hacia 1.
- **Penaliza** los términos con **alto `df`** (cercano a `N`): pierden peso relativo al cocientar entre el número de documentos donde aparecen. En el extremo, un término en todos los documentos recibe `idf = 0` (clásica) o `idf = 1` (suavizada) — el menor refuerzo posible.
- **Premia** los términos con **bajo `df`** (idealmente, presentes solo en 1 documento): obtienen idf alta y se vuelven *firmas* del documento. En nuestro corpus, `battle` (df=3) es el único término con idf > 1 y, en consecuencia, el único cuyo peso cambia entre `raw` y `tf-idf`.

### 5.3 ¿Por qué `Henry V ≈ Julius Caesar = 0.999` con frecuencias crudas?

Tres factores se combinan:

1. **Dominancia de `good`** en la norma L2. Ambas obras tienen `good` como su componente máxima (89 y 62), seguidas a gran distancia por el resto. La proporción `good/‖d‖` es ≈ 0.988 (HV) y ≈ 0.993 (JC). Los vectores quedan prácticamente paralelos al eje `good`.

2. **Misma "forma" del perfil**. Tras `good`, ambas obras siguen la jerarquía `battle > fool > wit`, mientras que `AYLI` y `TN` siguen `good > fool > wit > battle` (con `fool` mucho mayor que `battle`). El patrón de dominancia es el mismo en HV y JC.

3. **`battle` aporta poco al coseno crudo**. Aunque `battle` distingue cualitativamente las obras históricas/romanas (HV=13, JC=7) de las comedias (AYLI=1, TN=0), su magnitud bruta es marginal frente al `good`. Sin la ponderación IDF que **eleva** la contribución de `battle`, el coseno colapsa a la similitud impuesta por `good`.

Formalmente, con vectores `a = (a₁,…)` y `b = (b₁,…)` donde `a₂, b₂` dominan:

$$ \cos(a,b) \approx \frac{a_2 b_2}{\sqrt{a_2^2}\sqrt{b_2^2}} = 1 $$

— el coseno se vuelve insensible al resto de dimensiones.

### 5.4 ¿Por qué TF-IDF **no logra** invertir el ranking aquí?

Porque la idf de `battle` (1.22) es solo modestamente mayor que la de `good` (1.00). Con un corpus más grande y un vocabulario más diverso, donde términos discriminativos tendrían `df` mucho menor que `N`, la ponderación TF-IDF sí cambia el ranking. **Lección**: TF-IDF es una herramienta de *re-pesado*, no una bala de plata; su poder corrector escala con la dispersión del vocabulario en el corpus.

## 6. Punto 5 — PCA 2D

PCA centrado sobre las **columnas** (documentos) de `X` ∈ ℝ^{4×4}.

### 6.1 Espacio TF-IDF + L2

Varianza explicada: **PC1 ≈ 96.4 %**, **PC2 ≈ 3.4 %** (acumulado ≈ 99.8 %).

| Doc | PC1 | PC2 |
|-----|----:|----:|
| AYLI | +0.087 | −0.080 |
| TN   | +0.379 | +0.041 |
| JC   | −0.241 | +0.003 |
| HV   | −0.225 | +0.035 |

> `HV` y `JC` quedan **a la izquierda** (PC1 negativo) y muy cerca entre sí; `TN` queda al extremo derecho (alto `fool`, sin `battle`); `AYLI` queda en posición intermedia. La separación PC1 codifica el eje `battle/good ↔ fool`. Ver `pca_tfidf.png`.

### 6.2 Espacio crudo (raw) + L2

Varianza explicada: **PC1 ≈ 96.8 %**, **PC2 ≈ 3.0 %** (acumulado ≈ 99.8 %).

| Doc | PC1 | PC2 |
|-----|----:|----:|
| AYLI | +0.082 | +0.075 |
| TN   | +0.378 | −0.038 |
| JC   | −0.240 | −0.006 |
| HV   | −0.220 | −0.030 |

> Topología cualitativa idéntica al caso TF-IDF: `HV ≈ JC` cerca, `AYLI` intermedia, `TN` lejos. La diferencia entre los dos PCAs es marginal porque la matriz `idf` solo modificó la fila `battle`. Ver `pca_raw.png`.

## 7. Conclusiones globales

1. **TF-IDF re-pesa, no re-ordena en corpora pequeños**. Si todos los términos están en casi todos los documentos, IDF ≈ constante y la geometría apenas cambia. El método se vuelve potente con vocabularios grandes y dispersos.
2. **La normalización L2 es no negociable**. Sin ella, los documentos largos dominan por magnitud; el coseno deja de medir solo dirección.
3. **`Henry V` y `Julius Caesar` son las obras más similares** bajo ambos esquemas, lo cual es **lingüísticamente correcto**: las dos son obras históricas/de guerra romana, con `battle` y `good` como términos relevantes. La similitud no es un artefacto del método sino una propiedad del corpus.
4. **PCA confirma la similitud** geométricamente: `HV` y `JC` se proyectan al mismo cuadrante; `TN` queda separada por su carga inusual de `fool`.
5. **La ley de cosenos es el primer paso**, no el último. Modelos posteriores (LSA, word2vec, BERT) profundizan esta misma idea con vectores aprendidos y contextuales.

## 8. Limitaciones del experimento

- **Corpus minúsculo**: 4 documentos × 4 términos no representa ningún corpus realista; los resultados deben leerse como demostración pedagógica del cálculo, no como conclusión literaria.
- **Sin pre-procesamiento**: no se aplica stemming, stop-words ni lematización (irrelevante con vocabulario tan reducido).
- **IDF clásica degenerada**: con `df = N` para 3 de 4 términos, `log₁₀(N/df) = 0` anula esas dimensiones. Usar suavizada es decisión justificada.

## 9. Trabajo futuro

- Repetir con el **texto completo** de las cuatro obras y un vocabulario de ~1 000 términos para ver cómo TF-IDF sí altera el ranking.
- Añadir **PPMI** (Pointwise Mutual Information positiva) como peso alternativo a TF-IDF.
- Comparar con embeddings **densos** (word2vec / sentence-BERT) sobre las mismas obras.
- Extender PCA a 3D y agregar **t-SNE** con más documentos para apreciar la diferencia entre proyecciones lineales y no lineales.
