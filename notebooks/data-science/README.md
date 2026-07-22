# Ciencia de Datos

Laboratorios de ML y talleres sobre monitoreo de calidad del aire en Bogotá.

## Carpetas

| Carpeta | Tema |
|---|---|
| `laboratorio/` | Laboratorios 3.2 – 3.7 de machine learning (datasets `student`, `imports-85`, etc.). |
| `talleres/` | Pipeline de calidad del aire (ver abajo). |

## Talleres

| Carpeta | Notebook(s) | Tema |
|---|---|---|
| `01-calidad-aire-ingesta-bd/` | `calidad_aire_bogota.ipynb`, `visualization.ipynb` | Ingesta y limpieza; incluye `docker-compose.yml`, `conexion.py` y dump SQL de PostgreSQL. |
| `02-calidad-aire-modelo/` | `red_monitoreo_calidad_aire.ipynb` | Modelado de la red de monitoreo. |
| `03-calidad-aire-modelo-mejorado/` | `red_monitoreo_calidad_aire3.ipynb` | Iteración mejorada del modelo. |

> El dump SQL y los `*.csv` viajan dentro de cada taller; ejecuta los notebooks desde su carpeta.
