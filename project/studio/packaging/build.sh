#!/usr/bin/env bash
# Build the DDD Studio desktop bundle on macOS or Linux.
#
#   bash packaging/build.sh
#
# Output:
#   macOS -> dist/DDD Studio.app
#   Linux -> dist/DDD Studio/  (wrap into an AppImage in a later step)
#
# Requires the system `graphviz` package (provides `dot`) installed beforehand:
#   macOS:  brew install graphviz
#   Linux:  sudo apt-get install -y graphviz libwebkit2gtk-4.1-0 libgtk-3-0
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Installing desktop toolchain (pyinstaller, pywebview)"
uv sync --group desktop

echo "==> Collecting a relocatable Graphviz into packaging/graphviz/"
bash packaging/collect_graphviz.sh "$ROOT/packaging/graphviz"

echo "==> Running PyInstaller"
uv run pyinstaller packaging/ddd_studio.spec --noconfirm --clean

echo "==> Done. Artifacts in dist/:"
ls -lh dist/
