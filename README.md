# DownLoader Pro

**Gestor de descargas avanzado con aceleración multithreading, soporte para redes sociales e interfaz web moderna.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-208%20passing-brightgreen)](https://github.com/FranexMT/DownLoader/actions)
[![Coverage](https://img.shields.io/badge/Coverage-80%25%2B-green)](https://github.com/FranexMT/DownLoader/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Características

| Característica | Descripción |
|---------------|-------------|
| **Multithreading** | Divide archivos en fragmentos y los descarga en paralelo |
| **Pause / Resume real** | Retoma descargas desde el byte exacto donde se pausó |
| **Throttling** | Limita la velocidad de descarga en KB/s |
| **Verificación de integridad** | Checksum MD5 / SHA256 automático al completar |
| **Redes sociales** | YouTube, Instagram, TikTok, Twitter/X, Facebook, Vimeo y 15+ más |
| **GUI web moderna** | Interfaz glassmorphism con Tailwind CSS, gráficos en tiempo real |
| **CLI avanzada** | Todos los comandos con colores, progreso y dashboard interactivo |
| **System Tray** | Minimiza a la bandeja del sistema, menú contextual |
| **Scheduler** | Programa descargas a una hora específica |
| **Persistencia** | Base de datos SQLite con historial completo |

---

## Requisitos

- **Python** 3.8 o superior
- **FFmpeg** (requerido para descargas de video/audio de redes sociales)
- Sistema operativo: Windows, macOS o Linux

### Verificar FFmpeg

```bash
ffmpeg -version
```

Si no está instalado:
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Windows:** Descargar desde [ffmpeg.org](https://ffmpeg.org/download.html)

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/FranexMT/DownLoader.git
cd DownLoader

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate.bat       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

## Uso rápido

### Interfaz gráfica (GUI)

```bash
python main.py --gui
```

Abre la interfaz web en `http://localhost:8000` automáticamente.

### Línea de comandos (CLI)

```bash
# Descargar un archivo
python main.py add "https://ejemplo.com/archivo.zip"

# Descargar con carpeta de destino
python main.py add "https://ejemplo.com/video.mp4" ~/Videos

# Descargar desde YouTube en 720p
python main.py add "https://youtube.com/watch?v=ID" -q 720p -f mp4

# Solo audio (MP3) desde YouTube
python main.py add "https://youtube.com/watch?v=ID" -q audio_only -f mp3

# Descargar con límite de velocidad (500 KB/s)
python main.py add "https://ejemplo.com/archivo.zip" --speed 500
```

---

## Comandos CLI

### Gestión de descargas

```bash
python main.py add <url> [destino]        # Agregar descarga
  -q, --quality  QUALITY                  # Calidad: best, 1080p, 720p, 480p, audio_only
  -f, --format   FORMAT                   # Formato: mp4, webm, mkv, mp3, m4a, flac
  -s, --speed    KB/S                     # Límite de velocidad en KB/s

python main.py list                        # Listar descargas activas
python main.py history                     # Ver historial completo
python main.py pause   <id>               # Pausar descarga
python main.py resume  <id>               # Reanudar descarga
python main.py cancel  <id>               # Cancelar descarga
python main.py remove  <id>               # Eliminar del historial
python main.py open    <id>               # Abrir archivo descargado
python main.py clear   [status]           # Limpiar historial (opcional: por estado)
python main.py stats                       # Ver estadísticas globales
python main.py dashboard                   # Panel de control interactivo
```

### Configuración

```bash
python main.py config --show              # Ver configuración actual
python main.py config --threads 8         # Número de hilos paralelos
python main.py config --speed 1000        # Velocidad máxima en KB/s (0 = sin límite)
python main.py config --checksum sha256   # Verificación de integridad (none/md5/sha256)
python main.py config --path ~/Downloads  # Carpeta de descarga predeterminada
```

---

## Redes sociales soportadas

| Plataforma | URL de ejemplo |
|-----------|---------------|
| YouTube | `youtube.com/watch?v=...` |
| Instagram | `instagram.com/p/...` |
| Twitter / X | `twitter.com/user/status/...` |
| TikTok | `tiktok.com/@user/video/...` |
| Facebook | `facebook.com/watch/...` |
| Vimeo | `vimeo.com/...` |
| Reddit | `reddit.com/r/.../comments/...` |
| Twitch | `twitch.tv/videos/...` |
| SoundCloud | `soundcloud.com/...` |
| Dailymotion | `dailymotion.com/video/...` |
| Pinterest | `pinterest.com/pin/...` |
| Bilibili | `bilibili.com/video/...` |
| + 15 más | Soportados via yt-dlp |

---

## Configuración

El archivo de configuración se guarda en `~/.downloader/config.json`:

```json
{
  "default_threads": 4,
  "default_download_path": "~/Downloads",
  "chunk_size": 1048576,
  "max_retries": 3,
  "timeout": 30,
  "max_speed_kbps": 0,
  "checksum_type": "none",
  "notifications": true,
  "minimize_to_tray": false,
  "scheduler_enabled": false,
  "scheduler_time": "02:00",
  "auto_subtitles": false,
  "cookies_browser": "firefox"
}
```

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `default_threads` | Hilos de descarga paralelos | `4` |
| `default_download_path` | Carpeta de destino | `~/Downloads` |
| `max_speed_kbps` | Límite de velocidad (0 = ilimitado) | `0` |
| `checksum_type` | Verificación: `none`, `md5`, `sha256` | `none` |
| `timeout` | Timeout de conexión en segundos | `30` |
| `minimize_to_tray` | Minimizar a bandeja al cerrar | `false` |
| `scheduler_enabled` | Activar descargador programado | `false` |
| `scheduler_time` | Hora de ejecución programada `HH:MM` | `02:00` |

---

## Estructura del proyecto

```
DownLoader/
├── src/
│   ├── core/
│   │   ├── downloader.py         # Motor principal (multithreading, pause/resume)
│   │   ├── social_downloader.py  # Descargas de redes sociales (yt-dlp)
│   │   ├── chunk_manager.py      # Gestión de fragmentos para resume real
│   │   ├── database.py           # Persistencia SQLite
│   │   └── config.py             # Carga y guardado de configuración
│   ├── cli/
│   │   └── main.py               # Todos los comandos CLI
│   ├── gui/
│   │   ├── main.py               # GUI de escritorio (CustomTkinter)
│   │   ├── web_gui.py            # Bridge Python ↔ JavaScript (Eel)
│   │   ├── system_tray.py        # Icono de bandeja del sistema
│   │   └── web/
│   │       ├── index.html        # Interfaz web principal
│   │       └── js/main.js        # Lógica JavaScript
│   └── utils/
│       ├── validators.py         # Validación de URLs y archivos
│       └── helpers.py            # Utilidades (format_bytes, ETA, íconos)
├── tests/
│   ├── test_validators.py        # Tests unitarios de validadores
│   ├── test_helpers.py           # Tests unitarios de utilidades
│   ├── test_database.py          # Tests de base de datos
│   ├── test_downloader.py        # Tests del motor de descarga
│   ├── test_chunk_manager.py     # Tests del gestor de fragmentos
│   ├── api/
│   │   ├── server.py             # Servidor Flask para pruebas de API
│   │   └── DownLoader-API.postman_collection.json
│   └── ui/
│       └── test_gui.py           # Pruebas E2E con Playwright
├── docs/
│   ├── ARCHITECTURE.md           # Arquitectura técnica detallada
│   └── API.md                    # Referencia de la API
├── .github/workflows/
│   └── test-pipeline.yml         # CI/CD con GitHub Actions
├── main.py                        # Punto de entrada
├── requirements.txt               # Dependencias de producción
├── requirements-test.txt          # Dependencias de pruebas
└── pytest.ini                     # Configuración de pytest
```

---

## Pruebas

```bash
# Instalar dependencias de prueba
pip install -r requirements-test.txt

# Ejecutar todas las pruebas con coverage
pytest

# Solo pruebas unitarias (más rápido)
pytest tests/test_validators.py tests/test_helpers.py tests/test_database.py tests/test_downloader.py

# Pruebas de API (requiere Flask)
python tests/api/server.py &
newman run tests/api/DownLoader-API.postman_collection.json \
  --environment tests/api/DownLoader-API.postman_environment.json

# Pruebas UI (requiere GUI corriendo)
python main.py --gui &
pytest tests/ui/test_gui.py
```

### Estado actual de pruebas

| Suite | Tests | Estado |
|-------|-------|--------|
| Unitarias (validators) | 45 | ✅ Pasan |
| Unitarias (helpers) | 45 | ✅ Pasan |
| Unitarias (database) | 38 | ✅ Pasan |
| Unitarias (downloader) | 31 | ✅ Pasan |
| Unitarias (chunk_manager) | 30 | ✅ Pasan |
| API (Postman/Newman) | 13 | ✅ Pasan |
| UI (Playwright) | 22 | ✅ Pasan |
| **Total** | **208** | ✅ **Todas pasan** |

---

## CI/CD

El proyecto usa GitHub Actions con tres jobs automáticos en cada push:

1. **Pruebas Unitarias** — pytest con cobertura ≥ 80%
2. **Pruebas de API** — Newman contra servidor Flask
3. **Pruebas UI** — Playwright en Chromium headless

Ver resultados: [GitHub Actions](https://github.com/FranexMT/DownLoader/actions)

---

## Documentación adicional

- [Arquitectura técnica](docs/ARCHITECTURE.md) — Diseño interno, flujos y decisiones técnicas
- [Referencia de API](docs/API.md) — Todas las funciones expuestas a JavaScript y endpoints REST

---

## Licencia

MIT — Ver [LICENSE](LICENSE) para más detalles.
