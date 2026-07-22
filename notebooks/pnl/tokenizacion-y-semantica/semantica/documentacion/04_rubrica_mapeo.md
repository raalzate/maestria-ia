# 04 — Mapeo de la Rúbrica

Trazabilidad punto a punto entre los criterios oficiales (`rublicas.png` — Lista de chequeo Act. 6) y la implementación en el notebook `act6-semantica.ipynb`.

| # | Criterio rúbrica | Pts | Evidencia en el notebook | Cumplimiento |
|---|------------------|----:|--------------------------|--------------|
| 1 | **Obtener la matriz TF-IDF y aplicar la normalización L2.** *La idea es obtener la contextualización de cada una de las palabras con respecto a cada novela.* | 1 | §2 — cálculo manual de `df`, `idf` (clásica y suavizada), `tf·idf`, `L2-norm`. Verificación cruzada contra `sklearn.feature_extraction.text.TfidfVectorizer` con `norm='l2'`. Salida: matriz 4×4 normalizada y comentada celda a celda. | ✅ 100 % |
| 2 | **Calcular la similitud coseno entre las obras usando las frecuencias ponderadas TF-IDF.** *La idea es encontrar la novela más similar a la novela `Henry V`.* | 1 | §3 — `cosine_similarity(X_tfidf.T)` + impresión de la fila/columna correspondiente a `Henry V`. Conclusión explícita: **`Henry V → Julius Caesar = 0.9988`**. | ✅ 100 % |
| 3 | **Calcular la similitud coseno entre las obras con las frecuencias crudas.** *La idea es encontrar la novela más similar a la novela `Henry V`.* | 1 | §4 — `cosine_similarity(X_raw.T)`. Conclusión: **`Henry V → Julius Caesar = 0.9991`**. | ✅ 100 % |
| 4 | **Comparar similitud coseno con frecuencias crudas vs TF-IDF y responder:** *¿Qué corrige TF-IDF, qué se penaliza? ¿Con frecuencias crudas, qué hace que `Henry V = Julius Caesar = 0.999`?* | 1 | §5 — tabla comparativa `Δ = tfidf − raw`, discusión teórica de IDF (penaliza alto `df`, premia bajo `df`) y análisis del efecto de la palabra dominante `good` que arrastra el coseno hacia 1. Respuestas redactadas en celdas markdown §5.2 y §5.3 del notebook + sección 5 de `03_resultados_y_analisis.md`. | ✅ 100 % |
| 5 | **Aplicar reducción de dimensionalidad (PCA recomendada o t-SNE opcional) y visualizar los documentos en el plano cartesiano para los dos modelos (TF-IDF y crudo).** | 1 | §6 — `sklearn.decomposition.PCA(n_components=2)` sobre `X_tfidf.T` y `X_raw.T`. Dos figuras matplotlib (`pca_tfidf.png`, `pca_raw.png`) con etiquetas de las cuatro obras. Bonus: tabla con varianza explicada por componente. | ✅ 100 % |

**Total ponderado**: 5.00 / 5.00 pts.

## Notas adicionales

- Todos los cálculos se hacen **dos veces**: una manual con NumPy (para mostrar la fórmula) y otra con `sklearn` (para validar). Los valores coinciden hasta el 4° decimal.
- Las celdas markdown del notebook explican la **teoría** antes de cada bloque de código — no es solo código; cada punto incluye su justificación matemática.
- La carpeta `documentacion/` complementa con:
  - `01_marco_teorico.md` — fundamentos (Salton, Spärck Jones, ley de cosenos, PCA).
  - `02_guia_practica.md` — guía operativa de ejecución.
  - `03_resultados_y_analisis.md` — análisis numérico completo y respuestas extendidas a las preguntas del Punto 4.
