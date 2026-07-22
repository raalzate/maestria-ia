"""Desktop bootstrap for DDD Studio (PyInstaller entry point).

Runs the Streamlit server in-process on a free localhost port and shows it in a
native window via pywebview. This is the entry the .spec freezes — NOT the dev
`streamlit run` path. Responsibilities, in order:

1. Put both source roots on ``sys.path`` (the project mixes ``from ui.*`` /
   ``from domain.*`` top-level imports with ``from ddd_studio.*`` imports, so
   both ``src/`` and ``src/ddd_studio/`` must be importable).
2. Point all user-writable data (analyses, drafts, cache, whisper models) at a
   per-user directory, since the frozen bundle is read-only.
3. Prepend the bundled Graphviz ``dot`` binary to PATH.
4. Load an optional user ``.env`` (secrets are never bundled).
5. Start Streamlit on a daemon thread, wait for it to serve, then open the
   pywebview window on the main thread. Hard-exit on close so the daemon dies.
"""

from __future__ import annotations

import multiprocessing
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

# CRITICAL for the frozen bundle: on macOS/Windows the multiprocessing start
# method is "spawn", which re-executes this binary for every worker process a
# dependency starts (faster-whisper/ctranslate2/tokenizers, etc.). Without
# freeze_support() each child would re-run main() and pop a NEW window —
# producing windows that keep reopening. This call makes children short-circuit.
multiprocessing.freeze_support()


def _resource_base() -> Path:
    """Root of bundled resources. ``sys._MEIPASS`` when frozen by PyInstaller,
    else the repo root (one level up from this file) for running unfrozen."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def _setup_paths() -> Path:
    """Insert both import roots and return the package dir (holds app.py)."""
    base = _resource_base()
    src_root = base / "src"  # makes `ddd_studio.*` importable
    pkg_root = src_root / "ddd_studio"  # makes `ui.*`, `domain.*`, `config.*` importable
    for p in (str(pkg_root), str(src_root)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return pkg_root


def _setup_data_dir() -> Path:
    """Create and export a writable per-user data dir + model cache."""
    if sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "ddd-studio"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", str(Path.home()))) / "ddd-studio"
    else:
        xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        root = Path(xdg) / "ddd-studio"

    for sub in ("static", "drafts", ".cache", "hf-cache"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    # Honored by ui/utils/storage.py and config/settings.py.
    os.environ.setdefault("DDD_STUDIO_DATA_DIR", str(root))
    # faster-whisper / huggingface model downloads -> writable cache.
    os.environ.setdefault("HF_HOME", str(root / "hf-cache"))
    return root


def _augment_path() -> None:
    """Rebuild a usable PATH for the GUI process.

    macOS/Linux GUI apps launched from Finder/Dock inherit a stripped PATH that
    omits user dirs, so CLIs the app shells out to — `claude` (Claude Code, in
    ~/.local/bin) and a system `dot` — are invisible. We merge the login shell's
    real PATH plus the usual install dirs ahead of the inherited one.
    """
    extra = [
        os.path.expanduser("~/.local/bin"),
        os.path.expanduser("~/bin"),
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    if os.name != "nt":
        try:
            shell = os.environ.get("SHELL", "/bin/zsh")
            out = subprocess.run(
                [shell, "-lic", 'printf %s "$PATH"'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for d in out.stdout.strip().split(os.pathsep):
                if d and d not in extra:
                    extra.append(d)
        except Exception:
            pass
    cur = os.environ.get("PATH", "")
    dirs = [p for p in extra if os.path.isdir(p)]
    os.environ["PATH"] = os.pathsep.join(dirs + ([cur] if cur else []))


def _setup_graphviz() -> None:
    """Make the bundled relocatable `dot` discoverable: prepend it to PATH and
    point the dynamic loader + plugin lookup at the bundled dirs. Falls back to
    a system `dot` automatically when nothing was bundled."""
    gv_dir = _resource_base() / "graphviz"
    if not gv_dir.is_dir():
        # No bundled graphviz: fall back to a system `dot`. GUI-launched apps on
        # macOS don't inherit the shell PATH, so probe the usual install dirs.
        for cand in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
            if os.path.exists(os.path.join(cand, "dot")):
                os.environ["PATH"] = cand + os.pathsep + os.environ.get("PATH", "")
                break
        return
    os.environ["PATH"] = str(gv_dir) + os.pathsep + os.environ.get("PATH", "")
    # dylibs/.so live next to dot; plugins + config in the graphviz/ subdir.
    plugin_dir = gv_dir / "graphviz"
    if plugin_dir.is_dir():
        os.environ["GVBINDIR"] = str(plugin_dir)
    if sys.platform == "darwin":
        os.environ["DYLD_LIBRARY_PATH"] = str(gv_dir) + os.pathsep + os.environ.get("DYLD_LIBRARY_PATH", "")
    elif os.name != "nt":
        os.environ["LD_LIBRARY_PATH"] = str(gv_dir) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")


def _seed_user_data(pkg_root: Path) -> None:
    """Copy bundled seed JSON into the writable static dir on first run."""
    try:
        from ui.utils.storage import seed_user_data

        seed_user_data(str(pkg_root / "static"))
    except Exception:
        # Seeding is best-effort; the app recreates these files as needed.
        pass


def _load_user_env(data_dir: Path) -> None:
    """Load an optional `.env` from the user data dir (secrets, not bundled)."""
    env_file = data_dir / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
        except Exception:
            pass


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _wait_until_up(port: int, timeout: float = 90.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.25)
    return False


def _run_streamlit(app_path: Path, port: int) -> None:
    """Launch Streamlit in-process (blocks). Runs on a daemon thread.

    Streamlit's bootstrap installs SIGTERM/SIGINT handlers, but signal.signal()
    only works on the main interpreter thread — and pywebview owns the main
    thread here. Neutralize that one call so the server starts on this thread;
    we shut down via os._exit() on window close, so the handlers aren't needed.
    """
    import signal as _signal

    _orig_signal = _signal.signal

    def _safe_signal(sig, handler):
        try:
            return _orig_signal(sig, handler)
        except ValueError:
            return None  # not on the main thread — Streamlit can run without it

    _signal.signal = _safe_signal

    from streamlit.web import bootstrap

    flag_options = {
        "server.port": port,
        "server.address": "127.0.0.1",
        "server.headless": True,
        "server.fileWatcherType": "none",
        "server.runOnSave": False,
        "browser.gatherUsageStats": False,
        "global.developmentMode": False,
    }
    bootstrap.load_config_options(flag_options=flag_options)
    bootstrap.run(str(app_path), False, [], flag_options)


def main() -> None:
    pkg_root = _setup_paths()
    data_dir = _setup_data_dir()
    _augment_path()
    _setup_graphviz()
    _seed_user_data(pkg_root)
    _load_user_env(data_dir)

    # Match the dev layout: Streamlit adds the script's dir as sys.path[0] and
    # any residual relative paths resolve against the package dir.
    os.chdir(pkg_root)

    app_path = pkg_root / "app.py"
    port = _free_port()

    server = threading.Thread(target=_run_streamlit, args=(app_path, port), daemon=True)
    server.start()

    if not _wait_until_up(port):
        raise SystemExit("DDD Studio: Streamlit server failed to start in time")

    import webview

    webview.create_window(
        "DDD Studio",
        f"http://127.0.0.1:{port}",
        width=1400,
        height=900,
        min_size=(900, 600),
    )
    # pywebview must own the main thread (required on macOS). Blocks until the
    # window closes; then hard-exit so the daemon Streamlit/tornado thread dies.
    webview.start(menu=_build_help_menu(webview))
    os._exit(0)


def _build_help_menu(webview):
    """Native "Ayuda" menu: opens the tutorial / docs / about from the menu bar."""
    from ui.components.help_content import DDD_DOCS_URL, about_html, help_html
    from webview.menu import Menu, MenuAction, MenuSeparator

    def open_guide():
        webview.create_window("Guía rápida — DDD Studio", html=help_html(), width=840, height=900)

    def open_about():
        webview.create_window("Acerca de DDD Studio", html=about_html(), width=540, height=580)

    def open_docs():
        import webbrowser

        webbrowser.open(DDD_DOCS_URL)

    return [
        Menu(
            "Ayuda",
            [
                MenuAction("Guía rápida y tutorial", open_guide),
                MenuAction("Documentación DDD (web)", open_docs),
                MenuSeparator(),
                MenuAction("Acerca de DDD Studio", open_about),
            ],
        )
    ]


if __name__ == "__main__":
    main()
