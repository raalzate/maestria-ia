# 02 — Guía Práctica

Manual de ejecución del notebook `act6-semantica.ipynb`.

## 1. Requisitos

- **Python ≥ 3.10**
- **RAM**: < 100 MB (dataset trivial, 4×4).
- **Disco libre**: < 5 MB para figuras PCA.
- Sin conexión a Internet requerida (todos los datos están hard-coded en el notebook).

## 2. Entorno recomendado

### 2.1 Local

```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .venv\Scripts\activate            # Windows

pip install -q numpy pandas scikit-learn matplotlib jupyter
jupyter lab
```

### 2.2 Google Colab

Subir el notebook tal cual. Las dependencias (`numpy`, `pandas`, `sklearn`, `matplotlib`) ya están preinstaladas en Colab; ninguna instalación adicional es necesaria.

## 3. Orden de ejecución

Las celdas están secuenciadas; ejecutar **de arriba hacia abajo** (`Run All` también funciona). Tiempo total: **< 5 segundos** en CPU.

| Sección | Operación | Tiempo aprox. |
|---------|-----------|---------------|
| §1 | Imports + dataset (matriz término–documento) | < 1 s |
| §2 | TF-IDF manual + L2 (Punto 1) | < 1 s |
| §3 | Similitud coseno con TF-IDF (Punto 2) | < 1 s |
| §4 | Similitud coseno con frecuencias crudas (Punto 3) | < 1 s |
| §5 | Comparativa + respuestas (Punto 4) | < 1 s |
| §6 | PCA 2D + figuras (Punto 5) | 1–2 s |
| **Total** | | **~5 s** |

## 4. Parámetros configurables

```python
TERMS     = ['battle', 'good', 'fool', 'wit']
DOCS      = ['As You Like It', 'Twelfth Night', 'Julius Caesar', 'Henry V']

RAW = np.array([
    [ 1,   0,  7, 13],   # battle
    [114, 80, 62, 89],   # good
    [ 36, 58,  1,  4],   # fool
    [ 20, 15,  2,  3],   # wit
])

USE_SMOOTH_IDF = True     # True → sklearn-style; False → SLP clásica log10(N/df)
USE_LOG_TF     = False    # True → 1+log10(count); False → raw count
N_COMPONENTS   = 2        # PCA target dims
```

## 5. Implementación TF-IDF

El notebook calcula TF-IDF **a mano** (NumPy) y verifica contra `sklearn.feature_extraction.text.TfidfVectorizer`. La fórmula adoptada por defecto es la *suavizada* (sklearn):

$$ \text{idf}(t) = \ln\!\left(\frac{1+N}{1+df(t)}\right) + 1 $$

Con el dataset:

| Término | df | idf suavizada |
|---------|---:|--------------:|
| battle | 3 | ln(5/4)+1 ≈ **1.2231** |
| good   | 4 | ln(5/5)+1 = **1.0000** |
| fool   | 4 | 1.0000 |
| wit    | 4 | 1.0000 |

Solo `battle` recibe un *boost*; los demás términos pasan idénticos a su TF.

## 6. Implementación coseno

```python
from sklearn.metrics.pairwise import cosine_similarity

S = cosine_similarity(X.T)        # X.T = vectores documento (filas)
```

Equivalente manual:

```python
Xn = X / np.linalg.norm(X, axis=0, keepdims=True)   # L2 por columna (doc)
S  = Xn.T @ Xn                                       # producto punto = coseno
```

## 7. PCA y visualización

```python
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
Y = pca.fit_transform(X.T)         # filas = documentos

plt.scatter(Y[:, 0], Y[:, 1])
for i, lbl in enumerate(DOCS):
    plt.annotate(lbl, Y[i])
```

Se generan **dos figuras**: `pca_tfidf.png` y `pca_raw.png`, una por cada espacio vectorial.

## 8. Troubleshooting

### 8.1 `ZeroDivisionError` en cosine

**Síntoma**: el coseno explota si un documento es vector cero (e.g. `Twelfth Night` tiene `battle=0`; pero el vector global no es cero).
**Solución**: protegido con `np.clip(norm, 1e-12, None)` antes de dividir.

### 8.2 IDF clásica produce vectores degenerados

Con `log₁₀(N/df)`, los términos en *todos* los documentos (`good`, `fool`, `wit`) reciben `idf = 0` y la matriz TF-IDF queda solo con la columna `battle`. El notebook lo expone como caso de estudio en §5.

### 8.3 PCA con menos puntos que features

Con `n=4` documentos y `m=4` features, PCA tiene como máximo `min(n, m) − 1 = 3` componentes útiles si los datos están centrados. Se piden 2 → suficiente.

### 8.4 Etiquetas se solapan en la figura

Con `n=4` puntos rara vez, pero si ocurre, ajustar `xytext=(5, 5), textcoords='offset points'`.

## 9. Reproducibilidad

- No hay aleatoriedad (PCA es determinista para una semilla `svd_solver` fija; sklearn usa `auto` y los datos son pequeños → siempre la misma factorización).
- Para fijar explícitamente: `PCA(n_components=2, random_state=42)`.

## 10. Limpieza

```bash
rm -f pca_tfidf.png pca_raw.png
```

No quedan otros artefactos persistentes.
