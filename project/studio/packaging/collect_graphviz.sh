#!/usr/bin/env bash
# Collect a RELOCATABLE Graphviz `dot` (+ its dylibs and layout plugins) into
# packaging/graphviz/ so the frozen app can render diagrams/PDF without a system
# graphviz install.
#
# macOS: dot references its dylibs by absolute Cellar path, so we rewrite every
#        load command to @loader_path with install_name_tool and ad-hoc re-sign
#        (Apple Silicon kills modified Mach-O binaries that aren't re-signed).
# Linux: copy dot + dylibs + plugins; the bootstrap sets LD_LIBRARY_PATH/GVBINDIR.
#
# Exits 0 with a warning (not an error) if graphviz can't be collected — the
# bundle still builds and falls back to a system `dot` on PATH if present.
set -uo pipefail

GV_DIR="$1"
rm -rf "$GV_DIR"
mkdir -p "$GV_DIR"

# Run a command with a hard timeout (seconds). A mis-relocated `dot` can hang on
# any invocation, so EVERY call to the bundled binary must be guarded or it
# stalls the whole build. `timeout(1)` isn't on stock macOS, hence this watchdog.
_timed() {
  local secs="$1"; shift
  "$@" </dev/null >/dev/null 2>&1 &
  local p=$!
  local i=0
  while kill -0 "$p" 2>/dev/null; do
    i=$((i + 1))
    [ "$i" -ge "$((secs * 2))" ] && { kill -9 "$p" 2>/dev/null; return 124; }
    sleep 0.5
  done
  wait "$p"
}

DOT_LINK="$(command -v dot || true)"
if [ -z "$DOT_LINK" ]; then
  echo "WARN: 'dot' not found on PATH — skipping graphviz bundling." >&2
  echo "      Diagrams/PDF will require a system graphviz install at runtime." >&2
  exit 0
fi

DOT="$(readlink -f "$DOT_LINK" 2>/dev/null || echo "$DOT_LINK")"
LIBDIR="$(cd "$(dirname "$DOT")/.." && pwd)/lib"
OS="$(uname)"

cp "$DOT" "$GV_DIR/dot"
chmod u+w "$GV_DIR/dot"

if [ "$OS" = "Darwin" ]; then
  # Core dylibs + the layout plugins.
  cp "$LIBDIR"/lib*.dylib "$GV_DIR"/ 2>/dev/null || true
  mkdir -p "$GV_DIR/graphviz"
  cp "$LIBDIR"/graphviz/*.dylib "$GV_DIR/graphviz/" 2>/dev/null || true
  # libltdl lives outside the graphviz prefix (libtool).
  LTDL="$(otool -L "$DOT" | awk 'NR>1{print $1}' | grep -i libltdl | head -1 || true)"
  if [ -n "$LTDL" ] && [ -f "$LTDL" ]; then
    cp "$LTDL" "$GV_DIR/" && chmod u+w "$GV_DIR/$(basename "$LTDL")"
  fi
  chmod -R u+w "$GV_DIR"

  # Rewrite absolute load paths -> @loader_path.
  _rewrite() {  # $1 = mach-o file, $2 = prefix for core libs (e.g. "" or "../")
    local f="$1" up="$2" ref leaf
    for ref in $(otool -L "$f" | awk 'NR>1{print $1}'); do
      case "$ref" in
        */graphviz/*/lib/*|*/libltdl*|*/Cellar/*)
          leaf="$(basename "$ref")"
          install_name_tool -change "$ref" "@loader_path/${up}${leaf}" "$f" 2>/dev/null || true
          ;;
      esac
    done
  }
  install_name_tool -id "@loader_path/dot" "$GV_DIR/dot" 2>/dev/null || true
  _rewrite "$GV_DIR/dot" ""
  for lib in "$GV_DIR"/*.dylib; do
    [ -f "$lib" ] || continue
    install_name_tool -id "@loader_path/$(basename "$lib")" "$lib" 2>/dev/null || true
    _rewrite "$lib" ""
  done
  for plug in "$GV_DIR"/graphviz/*.dylib; do
    [ -f "$plug" ] || continue
    install_name_tool -id "@loader_path/$(basename "$plug")" "$plug" 2>/dev/null || true
    _rewrite "$plug" "../"  # core libs are one dir up from the plugin dir
  done

  # Ad-hoc re-sign first (install_name_tool invalidated signatures; Apple Silicon
  # SIGKILLs unsigned modified Mach-O), THEN regenerate the plugin config —
  # guarded by the watchdog so a hanging dot cannot stall the build.
  find "$GV_DIR" \( -name 'dot' -o -name '*.dylib' \) -print0 \
    | xargs -0 -I{} codesign --force --sign - {} 2>/dev/null || true
  GVBINDIR="$GV_DIR/graphviz" _timed 10 "$GV_DIR/dot" -c || true

elif [ "$OS" = "Linux" ]; then
  cp "$LIBDIR"/lib*graphviz* "$GV_DIR"/ 2>/dev/null || true
  cp "$LIBDIR"/lib{gvc,cgraph,cdt,pathplan,xdot,gvpr}*.so* "$GV_DIR"/ 2>/dev/null || true
  mkdir -p "$GV_DIR/graphviz"
  cp "$LIBDIR"/graphviz/*.so* "$GV_DIR/graphviz/" 2>/dev/null || true
  LD_LIBRARY_PATH="$GV_DIR" GVBINDIR="$GV_DIR/graphviz" "$GV_DIR/dot" -c 2>/dev/null || true
fi

# Sanity check (watchdog-guarded): the bundled dot must actually render an SVG.
# If it does not verify we DISCARD the bundle so the app cleanly falls back to a
# system `dot` on PATH (documented external dep) instead of shipping a broken one.
export DYLD_LIBRARY_PATH="$GV_DIR" LD_LIBRARY_PATH="$GV_DIR" GVBINDIR="$GV_DIR/graphviz"
printf 'digraph{a->b}\n' > "$GV_DIR/.probe.dot"
if _timed 10 "$GV_DIR/dot" -Tsvg -o "$GV_DIR/.probe.svg" "$GV_DIR/.probe.dot" \
   && [ -s "$GV_DIR/.probe.svg" ]; then
  rm -f "$GV_DIR/.probe.dot" "$GV_DIR/.probe.svg"
  echo "==> Bundled relocatable graphviz verified (renders SVG)."
else
  echo "WARN: bundled 'dot' did not verify — discarding it." >&2
  echo "      The app will use a system graphviz at runtime (install via brew/apt/choco)." >&2
  rm -rf "$GV_DIR"
fi
