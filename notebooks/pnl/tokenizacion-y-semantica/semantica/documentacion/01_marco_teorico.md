# 01 — Marco Teórico

## 1. Semántica distribucional

> **Hipótesis distribucional (Harris, 1954; Firth, 1957):** *"You shall know a word by the company it keeps"*. El significado de una unidad lingüística se infiere de los contextos en los que aparece.

La **semántica vectorial** operacionaliza esa hipótesis representando palabras o documentos como **vectores en un espacio ℝⁿ**, de modo que la similaridad geométrica refleje similitud semántica. Esta familia se divide en dos generaciones:

| Generación | Representante | Característica |
|------------|---------------|----------------|
| **Clásica (sparse)** | TF, TF-IDF, PPMI, LSA | Vectores largos (|V|) y mayormente nulos. Pesos basados en conteos. |
| **Escalada (dense)** | word2vec, GloVe, fastText, BERT | Vectores cortos (50–1024 dim), aprendidos por contexto. |

El presente taller cubre la generación **clásica**, fundamento conceptual del resto.

## 2. Modelo de Espacio Vectorial (Vector Space Model)

Propuesto por **Salton, Wong & Yang (1975)** en *"A Vector Space Model for Automatic Indexing"* (CACM). Tres ingredientes:

1. **Vocabulario** `V = {t₁, …, t_m}` — el conjunto de términos índice.
2. **Matriz término–documento** `X ∈ ℝ^{m×n}` donde `X[i,j] = peso del término t_i en el documento d_j`.
3. **Función de similaridad** entre columnas (documentos) o filas (términos).

En el dataset del quiz: `m = 4` (battle, good, fool, wit), `n = 4` obras → matriz 4×4.

## 3. Frecuencia de términos (TF)

`tf(t, d)` = veces que el término `t` aparece en el documento `d`.

Variantes prácticas:

| Variante | Fórmula | Notas |
|----------|---------|-------|
| **Raw** | `tf = count` | Sesgo a docs largos |
| **Booleana** | `1 si count>0, else 0` | Pierde intensidad |
| **Log** | `1 + log₁₀(count) si count>0` | Atenúa palabras hiperfrecuentes |
| **Normalizada** | `count / max_t(count)` | Compara docs de diferente longitud |

## 4. Inverse Document Frequency (IDF)

Introducido por **Karen Spärck Jones (1972)** en *"A Statistical Interpretation of Term Specificity"* (JoDoc). Castiga términos que aparecen en muchos documentos (poco discriminativos):

$$ \text{idf}(t, D) = \log\frac{N}{df(t)} $$

- `N` = número total de documentos.
- `df(t)` = número de documentos donde aparece `t` al menos una vez.

**Variantes** numéricamente estables:

| Variante | Fórmula | Uso |
|----------|---------|-----|
| Clásica | `log(N/df)` | SLP, libros clásicos |
| Suavizada (sklearn `smooth_idf=True`, default) | `ln((1+N)/(1+df)) + 1` | Evita división por cero y log(1)=0; usada en este taller |
| Probabilística | `log((N-df)/df)` | Robertson–BM25 |

### 4.1 Intuición

- Un término que está en **todos** los documentos → `idf ≈ 0` (con la fórmula clásica) o `idf = 1` (suavizada) → aporta poca información discriminativa.
- Un término que está en **un solo documento** → `idf` máxima → señal fuerte de pertenencia.

## 5. TF-IDF

Producto puntual del peso local (TF) por el peso global (IDF):

$$ w_{t,d} = \text{tf}(t, d) \cdot \text{idf}(t, D) $$

Es la representación clásica de un documento como vector en `ℝ^|V|`. Salton & Buckley (1988) demostraron empíricamente que supera a TF puro en *information retrieval*.

### 5.1 Normalización L2

Para comparar documentos de **distinta longitud**, se normaliza cada vector a magnitud unitaria:

$$ \hat{\mathbf{d}} = \frac{\mathbf{d}}{\lVert \mathbf{d} \rVert_2}, \qquad \lVert \mathbf{d} \rVert_2 = \sqrt{\sum_i w_i^2} $$

Tras L2, todos los documentos viven en la **esfera unitaria** ⇒ el producto punto coincide con la similitud coseno.

## 6. Similitud coseno (ley de cosenos)

Del producto interno y la ley de cosenos: `a · b = |a| |b| cos θ`. Despejando:

$$ \cos(\mathbf{a}, \mathbf{b}) = \frac{\mathbf{a} \cdot \mathbf{b}}{\lVert \mathbf{a} \rVert \lVert \mathbf{b} \rVert} = \sum_i \hat{a}_i \hat{b}_i $$

| cos θ | Interpretación |
|------:|----------------|
| 1 | Vectores colineales (misma dirección) → máxima similitud |
| 0 | Vectores ortogonales → sin similitud |
| -1 | Opuestos (raro con TF-IDF, todos los pesos ≥ 0) |

### 6.1 Por qué coseno y no distancia euclidiana

La euclidiana se sesga con la **longitud** del documento (un libro vs. un párrafo). El coseno mide solo **dirección**, robusto a magnitud — propiedad clave en IR y NLP. Bajo L2-norm, ambas métricas se vuelven monotónicamente equivalentes: `‖a − b‖² = 2 − 2·cos(a,b)`.

## 7. El "problema de la palabra dominante"

Cuando un término común (e.g. `good`) tiene una frecuencia mucho mayor que el resto, **domina** la norma L2 del vector y arrastra el coseno hacia 1 para cualquier par de documentos que también lo tengan como dominante. Síntoma:

> *Con frecuencias crudas, `cos(Henry V, Julius Caesar) = 0.999` aunque temáticamente sean ambas obras de guerra romana, no por la presencia de `battle` sino por el peso bruto de `good`.*

TF-IDF mitiga (no elimina) el efecto al **multiplicar `good` por una IDF baja** y elevar el peso relativo de términos discriminativos (en este caso `battle`, ausente solo en `Twelfth Night`). El alivio es proporcional a cuán dispersa esté la distribución de un término entre los documentos.

## 8. Reducción de dimensionalidad

### 8.1 PCA (Principal Component Analysis)

Pearson (1901), Hotelling (1933). Encuentra una base ortogonal `{u₁, …, u_k}` que maximiza la **varianza explicada** de los datos centrados:

1. Centrar `X` → `X̃ = X − μ`.
2. Calcular la matriz de covarianza `C = X̃ᵀ X̃ / (n-1)`.
3. Diagonalizar `C = U Λ Uᵀ`.
4. Proyectar `Y = X̃ · U[:, :k]`.

Para visualizar `k = 2`. En este taller, `m = 4` features → PCA es exacto (no hay pérdida real, solo rotación con descarte de los 2 componentes menores).

### 8.2 t-SNE (opcional)

van der Maaten & Hinton (2008). Preserva **vecindades locales** mediante un *embedding* probabilístico no lineal. Útil con muchos puntos; con solo `n=4` documentos pierde sentido (la perplejidad mínima ya supera la cardinalidad).

## 9. Pipeline del taller (resumen)

```
   X (4×4 raw freq)
        │
        ├─► L2-norm ───► CosSim_raw ───► PCA 2D ────► plot1
        │
        └─► TF·IDF ───► L2-norm ───► CosSim_tfidf ─► PCA 2D ─► plot2
```

## 10. Referencias

1. Harris, Z. (1954). *Distributional structure*. Word 10(2–3).
2. Salton, G., Wong, A., Yang, C. S. (1975). *A Vector Space Model for Automatic Indexing*. CACM 18(11).
3. Spärck Jones, K. (1972). *A Statistical Interpretation of Term Specificity*. Journal of Documentation.
4. Salton, G., Buckley, C. (1988). *Term-weighting Approaches in Automatic Text Retrieval*. IPM 24(5).
5. Pearson, K. (1901). *On Lines and Planes of Closest Fit to Systems of Points in Space*. Phil. Mag.
6. van der Maaten, L., Hinton, G. (2008). *Visualizing Data using t-SNE*. JMLR.
7. Jurafsky, D., Martin, J. (2024). *Speech and Language Processing* (3rd ed. draft), Cap. 6 — Vector Semantics. <https://web.stanford.edu/~jurafsky/slp3/>
8. Manning, C., Raghavan, P., Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge UP — Cap. 6.
