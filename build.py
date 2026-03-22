import os
import sys
import shutil
import PyInstaller.__main__

def build():
    # Nombre de la aplicación
    app_name = "DownLoader"
    
    # Directorio de salida
    dist_path = "dist"
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)

    # Definir carpetas de recursos
    # Eel necesita la carpeta 'web' y yt-dlp/ffmpeg si estuvieran embebidos
    web_folder = os.path.join("src", "gui", "web")
    
    # Argumentos para PyInstaller
    args = [
        "main.py",                         # Script principal
        f"--name={app_name}",              # Nombre del ejecutable
        "--onefile",                       # Un solo archivo
        "--windowed",                      # Sin consola (GUI)
        f"--add-data={web_folder}:src/gui/web", # Incluir archivos web
        "--icon=assets/icon.ico",          # Icono (si existe)
        "--clean",                         # Limpiar cache
        "--noconfirm",                     # No preguntar para sobrescribir
    ]

    print(f"Iniciando construcción de {app_name}...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n¡Construcción completada exitosamente!")
        print(f"El ejecutable se encuentra en la carpeta '{dist_path}'.")
    except Exception as e:
        print(f"\nError durante la construcción: {e}")

if __name__ == "__main__":
    # Asegurarse de que PyInstaller esté instalado
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller no está instalado. Ejecuta 'pip install pyinstaller' primero.")
        sys.exit(1)
        
    build()
