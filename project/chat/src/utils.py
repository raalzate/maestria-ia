import os

def load_html_template():
    """Carga el template HTML para el reproductor intérprete."""
    template_path = os.path.join("public", "template.html")
    if not os.path.exists(template_path):
        # Fallback simple si no existe el archivo
        return """
        <div style="padding: 20px; text-align: center; color: red;">
            <h3>Error: Template not found</h3>
            <p>Please ensure public/template.html exists.</p>
        </div>
        """
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def ensure_directories():
    """Asegura que existan los directorios necesarios."""
    dirs = ["public", "debug_files"]
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"📁 Directorio creado: {d}")
