# Notebooks

Notebooks de curso de la maestría, agrupados **por materia**. Cada carpeta de
ejercicio conserva sus datos (`data/`, `img/`, `utils.py`) **al lado del `.ipynb`**
que los consume — los notebooks leen rutas relativas, así que no muevas los datos
fuera de su carpeta.

## Estructura

| Carpeta | Materia | Contenido |
|---|---|---|
| [`fundamentos-python/`](fundamentos-python/) | Fundamentos de Python | Bases del lenguaje y comparación de modelos lineales vs no lineales. |
| [`machine-learning/`](machine-learning/) | Machine Learning | Redes neuronales, aprendizaje supervisado y talleres prácticos. |
| [`data-science/`](data-science/) | Ciencia de Datos | Laboratorios de ML y talleres de calidad del aire (ETL + modelado). |
| [`pnl/`](pnl/) | Procesamiento de Lenguaje Natural | Fine-tuning de T5, cadenas de Markov, tokenización y semántica vectorial. |
| [`taller-agentes/`](taller-agentes/) | Agentes | Notebooks del Agent SDK (tools, señales deterministas). |

## Convenciones

- Los talleres llevan prefijo numérico (`01-`, `02-`, …) para preservar el orden del curso.
- Nombres en kebab-case que describen el tema, no el número de taller.
- Datasets grandes (`*.csv`, `*.sql`, `*.zip`) y artefactos pueden estar excluidos por `.gitignore`.

## Cómo ejecutar

```bash
python -m venv .venv && source .venv/bin/activate
pip install jupyterlab pandas numpy scikit-learn matplotlib seaborn
jupyter lab
```

Abre el `.ipynb` desde su propia carpeta para que las rutas relativas a `data/` e `img/` resuelvan.
