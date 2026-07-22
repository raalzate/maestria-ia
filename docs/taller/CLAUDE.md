# Taller Investigación de Usuarios — IHC · Maestría CODING Univalle

Proyecto académico para la **Actividad 7** del curso *Fundamentos de Interacción Humano–Computador* de la Maestría en Computación para el Desarrollo de Aplicaciones Inteligentes (CODING) de la Universidad del Valle.

El taller resuelve, mediante cognotécnicas (línea de tiempo, mapa mental, mapa conceptual, cuadro sinóptico, cuadro comparativo, diagrama esquemático), siete preguntas sobre **Investigación de Usuarios**, contextualizadas al proyecto base **Agentic Loop UI** — interfaz determinista para asistentes conversacionales de banca digital colombiana.

---

## Estructura del proyecto

```
taller/
├── CLAUDE.md                                   # este archivo
├── .claude/
│   └── skills/                                 # código reusable, instrucciones de uso
│       ├── render-pdf/                         # HTML → PDF (Puppeteer)
│       │   ├── SKILL.md
│       │   ├── render.cjs
│       │   ├── package.json
│       │   └── node_modules/
│       └── diagrams-as-code/                   # diagramas (mingrammer/diagrams)
│           ├── SKILL.md
│           ├── _helpers.py
│           ├── 01_recomendaciones_entrevista.py
│           ├── 02_diagrama_afinidad.py
│           ├── 03_user_persona_anatomia.py
│           └── regenerate.sh
├── knowledge_base/                             # base de conocimiento del proyecto
│   ├── README.md
│   ├── propuesta_original.pdf                  # propuesta de proyecto IHC original (Carlos auditor banca)
│   ├── propuesta_reformulada.md                # propuesta concretada (dominio: banca digital colombiana)
│   ├── taller_enunciado.pdf                    # enunciado oficial Act_7
│   └── contexto_proyecto.md                    # síntesis del problema/solución/persona
└── deliverables/                               # entregables finales
    ├── taller_resuelto.html                    # source del taller resuelto
    ├── Act_7_Taller_Investigacion_Usuarios_Resuelto.pdf
    ├── respuesta_foro.txt                      # respuesta al foro virtual de la actividad
    └── diagrams_output/                        # PNGs generados por diagrams-as-code
        ├── 01_recomendaciones_entrevista.png
        ├── 02_diagrama_afinidad.png
        └── 03_user_persona_anatomia.png
```

---

## Reglas de operación

### Principios

1. **Diagram-as-Code.** Todo diagrama del taller se construye desde un `.py` en `.claude/skills/diagrams-as-code/`. Nunca editar PNGs a mano — siempre regenerar desde código.
2. **Single source of truth para el PDF.** El `taller_resuelto.html` en `deliverables/` es la fuente; el PDF se regenera de ahí. No editar el PDF.
3. **Knowledge base es contexto, no entregable.** Los archivos en `knowledge_base/` informan decisiones (qué dominio, qué persona, qué stack) pero no se modifican como parte de la entrega académica.
4. **Skills agnósticas, contenido específico.** Las skills (`render-pdf`, `diagrams-as-code`) deben quedar reutilizables para futuros trabajos. La especialización del contenido vive en `deliverables/` y `knowledge_base/`.

### Paleta de colores (Universidad del Valle — oficial)

| Token | Hex | Uso |
|-------|-----|-----|
| `--primary` | `#C8102E` | Rojo institucional, h1/h2/headers de tabla, nodos centrales |
| `--primary-dark` | `#7A0E1F` | Vinotinto, edges de diagrams, gradientes |
| `--accent` | `#D4A24C` | Dorado, regla bajo títulos, bordes de leaves |
| `--ink` | `#1a1a1a` | Texto principal |
| `--muted` | `#4a4a4a` | Subtexto, captions |
| `--soft` | `#f5f5f5` | Fondos suaves |

Esta paleta debe respetarse tanto en CSS del HTML como en los `.py` de diagrams.

### Persona primaria del proyecto

**Carlos — Auditor de Customer Service en banca digital colombiana**, 41 años. Persona primaria de toda investigación y prototipo. Las personas Ana (TDAH) y Doña Elsa (adultos mayores) son **secundarias de validación de inclusión**, no foco principal.

### Dominio fijado

**Banca digital colombiana — flujo de cancelación de tarjeta de crédito.** Marco regulatorio: Ley 1581 de 2012 (Habeas Data) + Circular Externa 029 de la SFC. Stack técnico: Claude API + tool use + orquestador propio.

---

## Workflows comunes

### Cambiar contenido del taller

1. Editar `deliverables/taller_resuelto.html`.
2. Re-render: `node .claude/skills/render-pdf/render.cjs`.

### Modificar un diagrama

1. Editar el `.py` correspondiente en `.claude/skills/diagrams-as-code/`.
2. Regenerar: `./.claude/skills/diagrams-as-code/regenerate.sh`.
3. Re-render PDF: `node .claude/skills/render-pdf/render.cjs`.

### Agregar un nuevo diagrama

Ver `.claude/skills/diagrams-as-code/SKILL.md` — sección "Cómo agregar un nuevo diagrama".

### Cambiar la paleta de colores

1. Actualizar variables `:root` en el `<style>` del HTML.
2. Buscar en los `.py` de diagrams las constantes hex (`#C8102E`, `#7A0E1F`, `#D4A24C`) y reemplazar.
3. Regenerar diagramas + re-render PDF.

### Reformular la propuesta o cambiar de dominio

Editar `knowledge_base/propuesta_reformulada.md` y propagar cambios al `taller_resuelto.html` (sección 0 Contexto, sección 6 personas, sección 8 conclusiones).

---

## Comandos rápidos

```bash
# Regenerar diagramas
./.claude/skills/diagrams-as-code/regenerate.sh

# Re-render PDF
node .claude/skills/render-pdf/render.cjs

# Pipeline completo
./.claude/skills/diagrams-as-code/regenerate.sh && \
  node .claude/skills/render-pdf/render.cjs
```

---

## Dependencias del entorno

| Herramienta | Versión mínima | Instalación macOS |
|-------------|----------------|--------------------|
| Node.js | 18 | `brew install node` |
| Python | 3.10 | viene con macOS o `brew install python@3.13` |
| Graphviz | 2.x | `brew install graphviz` |
| Puppeteer | gestionado por npm | `cd .claude/skills/render-pdf && npm install` |
| diagrams (Python) | 0.25+ | `pip install diagrams` |

---

## Identidad académica

- **Curso:** Fundamentos de Interacción Humano–Computador
- **Maestría:** Computación para el Desarrollo de Aplicaciones Inteligentes (CODING)
- **Universidad:** del Valle — Facultad de Ingeniería · Escuela de Ingeniería de Sistemas y Computación
- **Estudiante:** Raúl Andrés Alzate
- **Período:** Mayo 2026
