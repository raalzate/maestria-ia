#!/usr/bin/env bash
# Regenera todos los diagramas (Diagram as Code) en deliverables/diagrams_output/.
# Requiere: python3, graphviz (dot), pip install diagrams.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
OUT_DIR="$PROJECT_ROOT/deliverables/diagrams_output"
mkdir -p "$OUT_DIR"
cd "$SCRIPT_DIR"
for f in 01_recomendaciones_entrevista.py 02_diagrama_afinidad.py 03_user_persona_anatomia.py; do
  echo "→ $f"
  python3 "$f"
done
echo "Output: $OUT_DIR"
ls -la "$OUT_DIR"
