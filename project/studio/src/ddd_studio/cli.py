import subprocess
import sys
from pathlib import Path


def main():
    """Punto de entrada para el CLI.

    - En modo desarrollo lanza Streamlit como subproceso (`streamlit run app.py`).
    - En el bundle de escritorio (PyInstaller, `sys.frozen`) ese subproceso no
      funciona: `sys.executable` es el propio ejecutable y no existe el
      console-script `streamlit`. En ese caso delegamos en el bootstrap que
      arranca Streamlit en proceso y abre la ventana nativa (pywebview).
    """
    if getattr(sys, "frozen", False):
        from desktop_app import main as desktop_main

        return desktop_main()

    # Encuentra la carpeta donde está instalado este script
    app_dir = Path(__file__).parent
    app_path = app_dir / "app.py"

    comando = [sys.executable, "-m", "streamlit", "run", str(app_path)] + sys.argv[1:]

    try:
        # cwd=app_dir obliga a Streamlit a ejecutarse desde la carpeta interna
        subprocess.run(comando, cwd=app_dir, check=True)
    except KeyboardInterrupt:
        print("\nSaliendo de la aplicación...")
