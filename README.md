# Maestria: Data & ML Labs

Repositorio con ejercicios, notebooks y recursos para análisis de datos, modelos de ML y experimentos (PyTorch, scikit-learn, notebooks). Incluye ejemplos, datos locales (no versionados) y algunos artefactos de modelo.

---

## 💡 Resumen
Este repositorio contiene varios subproyectos organizados por carpetas:

- `data_science/` — Talleres y notebooks datamart y DW.
- `machine_learning/` — Ejercicios y notebooks de aprendizaje supervisado, redes y ejemplos prácticos.
- `project/model/` — Modelos guardados (`*.joblib`) y notebooks de experimentos.
- `script/nodejs/` — Pequeños scripts Node.js para tareas de pre/procesamiento y empaquetado.
- `paython/`, `pnl/`, `script/` — Material adicional y scripts.

> **Nota**: Los datasets pesados, dumps y modelos no se versionan por defecto (revisar `.gitignore`).


---

## ▶️ Requisitos / Setup básico

### Recomendado: crear y activar un entorno virtual (venv)
```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
````

### Instalar dependencias (ejemplo)

Crea un `requirements.txt` si no existe. Un ejemplo mínimo:

```
pandas
numpy
scikit-learn
jupyterlab
matplotlib
seaborn
joblib
openpyxl
```

Instala:

```bash
pip install -r requirements.txt
```

### Notebooks

Arranca JupyterLab:

```bash
jupyter lab
# o
jupyter notebook
```

Abre los notebooks `.ipynb` desde la interfaz.

---

## 🐳 Docker / docker-compose

Este repositorio incluye `docker-compose.yml` para orquestar servicios (p. ej. base de datos PostgreSQL). Para levantar:

```bash
docker-compose up -d
```

> Si usas Podman, el `docker-compose.yml` suele funcionar con `podman-compose` o `podman play kube` tras conversión.

### Restaurar dump SQL (local)

Si tienes el archivo `dump-*.sql`:

```bash
# ejemplo para PostgreSQL local
psql -U <username> -d <db_name> -f dump-202511031104.sql
```

---

## 🗄️ Datos y modelos

* Las carpetas con `*.csv` en data_science grandes están excluidas por `.gitignore`.
* Si quieres compartir datasets pequeños, añade una excepción con `!ruta/archivo.csv` en `.gitignore`.
* Los modelos (`*.joblib`, `*.pkl`, `*.pt`) están excluidos para evitar repositorios pesados. Si quieres versionar un modelo pequeño, coméntalo en `README`.


---

## 🔧 Comandos útiles

Abrir Jupyter:

```bash
jupyter lab
```

Ejecutar script Python:

```bash
python data_science/taller1/conexion.py
```

Levantar servicios:

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

Instalar dependencias Node (si trabajas en `script/nodejs`):

```bash
cd script/nodejs
npm install
node abstractive-summary.mjs
```

---


## 📬 Contacto

Autor / Mantenedor: `raul alzate`
Si hay problemas con datos o notebooks, abrir `issue` con la reproducción mínima.

---

