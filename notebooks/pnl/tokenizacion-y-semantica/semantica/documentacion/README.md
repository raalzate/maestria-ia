# Documentación — Actividad 6: Semántica vectorial clásica

Carpeta de soporte teórico-práctico para el notebook `act6-semantica.ipynb`.

## Estructura

| Archivo | Contenido |
|---------|-----------|
| `01_marco_teorico.md` | Fundamentos: similaridad semántica, modelo VS, TF-IDF, ley de cosenos, L2, PCA. |
| `02_guia_practica.md` | Cómo ejecutar el notebook paso a paso, parámetros y troubleshooting. |
| `03_resultados_y_analisis.md` | Cálculos completos, comparativa raw vs tf-idf, visualización PCA y conclusiones. |
| `04_rubrica_mapeo.md` | Mapeo punto-a-punto entre los criterios de evaluación y las celdas del notebook. |
| `05_embeddings_densos.md` | Complemento teórico (no evaluado por el quiz): regresión logística en PLN, Word2Vec + Gensim, GloVe, fastText, BERT/SBERT. |

## Resumen de la actividad

Aplicar **semántica vectorial clásica** a cuatro obras de Shakespeare (`As You Like It`, `Twelfth Night`, `Julius Caesar`, `Henry V`) representadas como vectores de frecuencia sobre los términos `(battle, good, fool, wit)`. Se construye la matriz TF-IDF con normalización L2, se calcula la similitud coseno con frecuencias crudas y ponderadas, se analiza por qué `Henry V ≈ Julius Caesar ≈ 0.999` y se proyectan los documentos en 2D mediante PCA.

## Entregables

- `act6-semantica.ipynb` — notebook funcional con los 5 puntos resueltos.
- `documentacion/` — esta carpeta.
- Figuras PCA generadas en runtime (`pca_tfidf.png`, `pca_raw.png`).

## Dataset (term–document matrix, Jurafsky & Martin SLP §6.5)

|       | As You Like It | Twelfth Night | Julius Caesar | Henry V |
|-------|---------------:|--------------:|--------------:|--------:|
| battle | 1 | 0 | 7 | 13 |
| good   | 114 | 80 | 62 | 89 |
| fool   | 36 | 58 | 1 | 4 |
| wit    | 20 | 15 | 2 | 3 |
