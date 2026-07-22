---
name: render-pdf
description: Renderiza un archivo HTML a PDF editorial A4 usando Puppeteer (Chrome headless). Respeta CSS de impresión (`@page`, `page-break-*`, headers/footers). Usar cuando el usuario pida regenerar el PDF del taller, convertir HTML a PDF, o aplique cambios al `taller_resuelto.html`.
---

# render-pdf

Convierte HTML con CSS de impresión en PDF A4 listo para entrega académica.

## Cuándo invocar

- El usuario pide "regenera el PDF", "vuelve a sacar el PDF del taller", "render el PDF".
- Se modificó `deliverables/taller_resuelto.html` y se necesita propagar al PDF.
- Se modificaron diagramas (PNG en `deliverables/diagrams_output/`) y el PDF debe reflejarlos.

## Cómo usar

Desde la raíz del proyecto:

```bash
# Defaults: lee deliverables/taller_resuelto.html, escribe deliverables/Act_7_Taller_Investigacion_Usuarios_Resuelto.pdf
node .claude/skills/render-pdf/render.cjs

# Con argumentos explícitos
node .claude/skills/render-pdf/render.cjs <input.html> <output.pdf>
```

## Dependencias

- Node.js ≥18
- Puppeteer (instalado en `node_modules/` adyacente). El binario de Chrome se descarga la primera vez vía `~/.cache/puppeteer/`.

Si falta puppeteer, reinstalar:

```bash
cd .claude/skills/render-pdf && npm install
```

## Convenciones de estilo soportadas

El HTML debe declarar CSS `@page` para tamaño A4, márgenes y `@top-left/@top-right/@bottom-center` para encabezados/pies. La portada típicamente desactiva headers con `@page :first { @top-left { content: ""; } ... }`. `printBackground: true` está activado, así que gradientes, fondos sólidos y SVGs renderizan tal cual.

## Output esperado

PDF A4, una página por sección con `<div class="pagebreak"></div>` antes de cada sección o `page-break-after: always`. Imágenes embebidas (PNG en `deliverables/diagrams_output/`) referenciadas con paths relativos resuelven correctamente porque puppeteer carga el HTML como `file://`.
