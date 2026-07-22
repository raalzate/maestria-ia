---
name: diagrams-as-code
description: Genera los diagramas (mapa mental, mapa conceptual, diagrama esquemático) del taller usando mingrammer/diagrams (Diagram as Code). Produce PNG con paleta Univalle (#C8102E rojo / #7A0E1F vinotinto / #D4A24C dorado) en `deliverables/diagrams_output/`. Usar cuando el usuario pida agregar, modificar o regenerar diagramas del taller.
---

# diagrams-as-code

Diagrams del taller construidos con [mingrammer/diagrams](https://diagrams.mingrammer.com/). Diagram-as-Code: el código `.py` ES la fuente de verdad del diagrama. Los `.png` en `deliverables/diagrams_output/` son artefactos generados.

## Cuándo invocar

- Agregar un nuevo diagrama al taller.
- Modificar un diagrama existente (cambiar etiqueta, agregar nodo, ajustar estilo).
- Regenerar PNGs después de cambiar la paleta de colores o el helper.
- El usuario pide "regenera los diagramas", "actualiza el diagrama de X", o nombra un diagrama explícitamente.

## Estructura

```
.claude/skills/diagrams-as-code/
├── _helpers.py                     # text_node() — wrapper de Blank con texto centrado
├── 01_recomendaciones_entrevista.py
├── 02_diagrama_afinidad.py
├── 03_user_persona_anatomia.py
└── regenerate.sh                   # corre los 3 .py
```

## Cómo regenerar

```bash
# Desde la raíz del proyecto
./.claude/skills/diagrams-as-code/regenerate.sh
```

Output queda en `deliverables/diagrams_output/`.

## Dependencias

- Python ≥3.10
- Graphviz (`dot` en PATH) — en macOS: `brew install graphviz`
- Paquete `diagrams`: `pip install diagrams`

## Convenciones de diseño

### Paleta Univalle (oficial)

| Token | Hex | Uso |
|-------|-----|-----|
| Primary | `#C8102E` | Rojo institucional, nodos centrales y headers |
| Primary-dark | `#7A0E1F` | Vinotinto, edges y clusters |
| Accent | `#D4A24C` | Dorado, bordes de hojas y resaltes |
| Soft | `#fdf6f0` / `#fef9f0` | Fondos suaves de clusters/leaves |

### Helper text_node()

Usar **siempre** `text_node()` de `_helpers.py` en lugar de `Blank` directamente. El helper:

- Override `image=""` para eliminar el icono fantasma de `Blank`.
- Override `height="0.5"` para evitar el alto fijo de 1.9" que desplaza el label.
- `labelloc="c"` para centrar texto.
- Margen 0.18,0.12 razonable.

### Estructura típica

```python
from diagrams import Diagram, Cluster, Edge
from _helpers import text_node

with Diagram("Título", filename="../../../deliverables/diagrams_output/NN_nombre", outformat="png", show=False, ...):
    centro = text_node("Centro", shape="circle", fillcolor="#C8102E", fontcolor="white", width="1.5", height="1.5", fixedsize="true")
    with Cluster("Grupo", graph_attr={"bgcolor": "#fdf6f0", "color": "#C8102E", ...}):
        n1 = text_node("Hoja 1", color="#D4A24C", fillcolor="white")
    centro >> Edge(color="#C8102E", penwidth="2") >> n1
```

## Cómo agregar un nuevo diagrama

1. Crear `NN_nombre.py` siguiendo el patrón anterior.
2. Agregar `NN_nombre.py` al loop en `regenerate.sh`.
3. Ejecutar `regenerate.sh`.
4. Embeber en HTML: `<img src="diagrams_output/NN_nombre.png" alt="..." />`.
5. Re-render PDF (skill `render-pdf`).

## Notas técnicas

- `splines: "ortho"` para mapas conceptuales jerárquicos; `splines: "curved"` para mapas mentales.
- `rankdir: "TB"` (top-bottom) por defecto; `"LR"` para diagramas esquemáticos tipo persona.
- El path `../../../deliverables/diagrams_output/` en `filename` es relativo al directorio del .py (Python ejecuta desde donde está el script).
