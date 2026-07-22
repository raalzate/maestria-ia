"""Centralized help/tutorial content for DDD Studio.

Single source of truth shared by:
- the in-app "📚 Ayuda / Tutorial" sidebar section (Markdown, via Streamlit), and
- the native pywebview "Ayuda" menu windows (HTML), built in packaging/desktop_app.py.

Keep both representations in sync when editing.
"""

from __future__ import annotations

APP_VERSION = "2.1"

# ── Markdown sections (rendered inside Streamlit) ────────────────────────────

QUICK_START_MD = """
### 🚀 Guía rápida (5 pasos)

1. **Fuente de información** — elige una entrada:
   - 🎙️ **Audio**: graba en vivo o sube un archivo (MP3, WAV, M4A, OPUS). Se transcribe solo.
   - 📝 **Texto/Transcripción**: pega texto o sube TXT/PDF/MD.
   - 📚 **Documentos PDF**: sube varios; la IA filtra el ruido y arma una narrativa de negocio.
2. **(Opcional) Contexto adicional** — sube un PDF con reglas de negocio o pega un glosario.
3. **(Opcional) Directiva de foco** — una instrucción de alta prioridad para la IA
   (ej. *"enfócate solo en el flujo de vencimientos"*).
4. **🚀 Analizar** — la IA ejecuta el pipeline y te muestra el progreso en vivo.
5. **Edita, valida y descarga** — revisa los resultados y exporta a PDF, HTML, JSON o diagramas.
"""

INPUTS_MD = """
### 🎤 Opciones de entrada

- **Audio/Grabación**: la primera vez que transcribes se descarga el modelo de voz
  (puede tardar unos minutos); luego queda en caché.
- **Simulación narrativa**: un agente reescribe tu texto como si fuera un taller.
- **Taller multi-agente**: dos agentes (Facilitador + Experto) conversan y generan
  un diálogo realista de Event Storming.
- **Extracción de PDFs**: la IA propone qué temas incluir/excluir; puedes ajustarlos
  y re-extraer.
"""

RESULTS_TABS_MD = """
### 🗂️ Las pestañas de resultados

- **💬 Chat IA** — conversa con el modelo para refinarlo (agrega/edita agregados, políticas, etc.).
- **🕸️ Visualización** — grafo interactivo del *Big Picture* y los agregados.
- **✏️ Datos y Edición** — tablas editables (nodos, aristas, políticas, read models).
  Edita las celdas y pulsa **💾 Guardar y Aplicar Cambios**.
- **📊 Estadísticas** — métricas: tipos de nodos, estados, etiquetas de tecnología.
- **🚀 DDD** — genera **Context Map** (diseño estratégico) y **Modelo Táctico**
  (diagramas de clases) en PlantUML.
- **🧾 Raw & Logs** — JSON crudo y el registro de eventos del pipeline.
"""

FAQ_MD = """
### ❓ Preguntas frecuentes

**¿Qué es la "Directiva de foco"?**
Una instrucción de alta prioridad para la IA. Ej.: *"ignora reportes, modela solo la liquidación"*.

**¿Diferencia entre Simulación narrativa y Taller multi-agente?**
La narrativa reescribe tu texto con un solo agente; el taller hace conversar a dos agentes
para producir un diálogo más rico.

**¿Puedo editar el análisis después de generarlo?**
Sí, en **✏️ Datos y Edición**. Los cambios se aplican al pulsar *Guardar y Aplicar Cambios*.

**¿Dónde quedan mis análisis y configuración?**
En tu carpeta de datos de usuario (en macOS: *Library/Application Support/ddd-studio*).
No se borran al cerrar la app.

**La transcripción tarda la primera vez. ¿Es normal?**
Sí: se descarga el modelo de voz una sola vez y queda en caché para las siguientes.

**¿Necesito conexión a internet?**
Sí para la IA (Claude/Gemini) y para descargar el modelo de voz la primera vez.
"""

GLOSSARY_MD = """
### 📖 Glosario DDD

- **Bounded Context** — frontera donde un modelo y su lenguaje son consistentes.
- **Subdominio** — una parte del dominio del negocio (core, soporte o genérico).
- **Agregado** — grupo de objetos tratado como una unidad; tiene una *raíz de agregado*.
- **Entidad** — objeto con identidad propia que persiste en el tiempo.
- **Value Object** — objeto sin identidad, definido por sus valores.
- **Política / Policy** — regla de reacción ("cuando pasa X, entonces Y").
- **Read Model** — vista optimizada para consulta (lado de lectura).
- **Context Map** — diagrama estratégico de cómo se relacionan los bounded contexts.
- **Lenguaje ubicuo** — vocabulario común entre negocio y desarrollo.
"""

HELP_SECTIONS = [
    ("🚀 Guía rápida", QUICK_START_MD),
    ("🎤 Opciones de entrada", INPUTS_MD),
    ("🗂️ Pestañas de resultados", RESULTS_TABS_MD),
    ("❓ Preguntas frecuentes", FAQ_MD),
    ("📖 Glosario DDD", GLOSSARY_MD),
]


# ── HTML (rendered in native pywebview windows from the "Ayuda" menu) ─────────


def _md_blocks_to_html() -> str:
    """Very small Markdown→HTML for our own controlled content (headings, bold,
    list items, paragraphs). Avoids pulling a markdown dependency into the build."""
    import html as _html
    import re

    out: list[str] = []
    in_list = False
    text = "\n".join(md for _title, md in HELP_SECTIONS)
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        stripped = line.strip()

        def _inline(s: str) -> str:
            s = _html.escape(s)
            s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
            s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
            s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
            return s

        if stripped.startswith("### "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{_inline(stripped[4:])}</h2>")
        elif re.match(r"^\d+\.\s", stripped) or stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^(\d+\.\s|- )", "", stripped)
            out.append(f"<li>{_inline(item)}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<p>{_inline(stripped)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


_STYLE = """
<style>
  :root { color-scheme: dark; }
  body { background:#0E1117; color:#FAFAFA; font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         line-height:1.55; margin:0; padding:28px 34px; }
  h1 { color:#FF4B4B; font-size:22px; margin:0 0 4px; }
  h2 { color:#FF6B6B; font-size:16px; margin:22px 0 6px; border-bottom:1px solid #262730; padding-bottom:4px; }
  p, li { font-size:13.5px; }
  ul { margin:4px 0 10px; padding-left:20px; }
  code { background:#262730; color:#7EE787; padding:1px 5px; border-radius:4px; font-size:12.5px; }
  .sub { color:#9aa0aa; font-size:12px; margin-bottom:14px; }
  a { color:#FF8585; }
</style>
"""


def help_html() -> str:
    """Full tutorial as a self-contained HTML document (native 'Guía rápida' window)."""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        + _STYLE
        + "</head><body>"
        + "<h1>📚 DDD Studio — Ayuda y Tutorial</h1>"
        + "<div class='sub'>Cómo convertir un taller en un modelo de dominio DDD.</div>"
        + _md_blocks_to_html()
        + "</body></html>"
    )


def about_html() -> str:
    """Short 'Acerca de' document for the native menu."""
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        + _STYLE
        + "</head><body>"
        + "<h1>🧠 DDD Studio</h1>"
        + f"<div class='sub'>Versión {APP_VERSION}</div>"
        + "<p>Herramienta con IA que convierte transcripciones de talleres "
        + "(Event Storming) en modelos de dominio <strong>Domain-Driven Design</strong>.</p>"
        + "<h2>Flujo</h2><ul>"
        + "<li>Audio / texto / PDFs → transcripción y análisis</li>"
        + "<li>Modelo DDD editable (agregados, políticas, read models)</li>"
        + "<li>Context Map y modelo táctico en PlantUML</li>"
        + "<li>Exportación a PDF, HTML, JSON y diagramas</li>"
        + "</ul>"
        + "<p class='sub'>Powered by Raul A.</p>"
        + "</body></html>"
    )


# External reference opened by the "Documentación DDD" menu item.
DDD_DOCS_URL = "https://martinfowler.com/tags/domain%20driven%20design.html"
