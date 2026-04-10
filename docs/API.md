# Referencia de API — DownLoader Pro

Este documento describe todas las interfaces programáticas disponibles:

1. [Funciones Python → JavaScript (Eel)](#funciones-eel)
2. [API REST (Flask — pruebas)](#api-rest)
3. [Módulos Python internos](#módulos-python)

---

## Funciones Eel

La GUI web se comunica con Python a través de **Eel**. Desde JavaScript se llaman con:

```javascript
const resultado = await eel.nombre_funcion(args)();
```

---

### `add_download(url, quality, file_format)`

Crea e inicia una descarga.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `url` | string | URL a descargar |
| `quality` | string | `"best"`, `"1080p"`, `"720p"`, `"480p"`, `"audio_only"`, `"video_only"` |
| `file_format` | string \| null | `"mp4"`, `"webm"`, `"mkv"`, `"mp3"`, `"m4a"`, `"flac"` o `null` |

**Retorna:** `true` si la tarea se creó, `false` si la URL es inválida.

---

### `add_download_with_options(url, quality, file_format, destination, max_speed_kbps, title, thumbnail)`

Descarga con todas las opciones configurables.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `url` | string | URL a descargar |
| `quality` | string | Calidad de video |
| `file_format` | string \| null | Formato de salida |
| `destination` | string \| null | Carpeta de destino (null = predeterminada) |
| `max_speed_kbps` | number | Límite de velocidad en KB/s (0 = sin límite) |
| `title` | string \| null | Título personalizado |
| `thumbnail` | string \| null | URL de miniatura |

**Retorna:** `true` / `false`

---

### `check_url_type(url)`

Detecta si una URL pertenece a una red social.

**Retorna:** `true` si es red social, `false` si es descarga directa.

---

### `get_quality_options()`

**Retorna:** Array de opciones de calidad disponibles.

```json
[
  {"value": "best",       "label": "Mejor calidad"},
  {"value": "1080p",      "label": "1080p Full HD"},
  {"value": "720p",       "label": "720p HD"},
  {"value": "480p",       "label": "480p SD"},
  {"value": "audio_only", "label": "Solo audio"},
  {"value": "video_only", "label": "Solo video"}
]
```

---

### `get_format_options()`

**Retorna:** Array de formatos de salida disponibles.

```json
[
  {"value": "mp4",  "label": "MP4 (Video)"},
  {"value": "webm", "label": "WebM (Video)"},
  {"value": "mkv",  "label": "MKV (Video)"},
  {"value": "mp3",  "label": "MP3 (Audio)"},
  {"value": "m4a",  "label": "M4A (Audio)"},
  {"value": "flac", "label": "FLAC (Audio)"}
]
```

---

### `get_available_formats(url)`

Consulta los formatos disponibles para una URL de red social (llama a yt-dlp).

**Retorna:** Objeto con formatos o `{}` si no aplica.

---

### `pause_task(task_id)`

Pausa una descarga activa.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `task_id` | number | ID de la tarea |

**Retorna:** `true` si se pausó, `false` si el ID no existe.

---

### `resume_task(task_id)`

Reanuda una descarga pausada.

**Retorna:** `true` / `false`

---

### `cancel_task(task_id)`

Cancela y detiene una descarga.

**Retorna:** `true` / `false`

---

### `remove_task(task_id)`

Cancela la descarga y la elimina del historial.

**Retorna:** `true` / `false`

---

### `delete_download(download_id)`

Elimina un registro del historial (sin cancelar si está activo).

**Retorna:** `true` / `false`

---

### `get_all_downloads()`

Retorna el estado completo de la aplicación para actualizar la UI.

**Retorna:**
```json
{
  "stats": {
    "total": 10,
    "completed": 7,
    "failed": 1,
    "total_bytes": 1073741824
  },
  "active": [
    {
      "id": 3,
      "url": "https://ejemplo.com/file.zip",
      "filename": "file.zip",
      "status": "DOWNLOADING",
      "progress": 45.2,
      "downloaded_size": 10485760,
      "total_size": 23195648,
      "speed": 524288,
      "destination": "/home/user/Downloads",
      "title": null,
      "thumbnail": null
    }
  ],
  "history": [...]
}
```

---

### `get_history(status)`

Obtiene el historial filtrado por estado.

| Parámetro | Tipo | Valores |
|-----------|------|---------|
| `status` | string \| null | `"COMPLETED"`, `"FAILED"`, `"CANCELLED"` o `null` (todos) |

**Retorna:** Objeto `{history: [...], stats: {...}}`

---

### `get_stats()`

**Retorna:**
```json
{
  "total": 10,
  "completed": 7,
  "failed": 1,
  "total_bytes": 1073741824
}
```

---

### `get_config()`

**Retorna:** Objeto con toda la configuración actual (ver [Configuración en README](../README.md#configuración)).

---

### `save_settings(new_config)`

Guarda configuración desde la UI.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `new_config` | object | Llaves permitidas: `default_threads`, `default_download_path`, `max_speed_kbps`, `checksum_type`, `timeout`, `minimize_to_tray` |

**Retorna:** `true` si se guardó correctamente.

> **Seguridad:** Solo se aceptan las llaves de la allowlist. Cualquier otra llave es ignorada.

---

### `browse_folder()`

Abre un diálogo nativo para seleccionar carpeta.

**Retorna:** Ruta seleccionada (string) o `""` si se canceló.

---

### `open_download(download_id)`

Abre el archivo descargado con la aplicación nativa del sistema.

**Retorna:** `true` si el archivo existe y se abrió, `false` en caso contrario.

---

### `check_engine_status()`

Verifica si FFmpeg y yt-dlp están disponibles.

**Retorna:**
```json
{
  "ffmpeg": true,
  "ytdlp": true
}
```

---

### `clear_history(status)`

Elimina registros del historial.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `status` | string \| null | Si se pasa, elimina solo ese estado; si es null elimina todo |

**Retorna:** Número de registros eliminados.

---

## API REST

El servidor Flask en `tests/api/server.py` expone una API REST para pruebas de integración. Se inicia con:

```bash
python tests/api/server.py
# Escucha en http://localhost:5001
```

---

### `POST /api/downloads`

Crea una nueva descarga.

**Body:**
```json
{
  "url": "https://ejemplo.com/archivo.zip",
  "destination": "/tmp",
  "filename": "archivo.zip"
}
```

**Respuestas:**

| Código | Situación |
|--------|-----------|
| `201` | Descarga creada |
| `400` | Sin campo `url` |
| `422` | URL inválida |

```json
{
  "success": true,
  "data": {
    "id": 1,
    "download": { ... }
  }
}
```

---

### `GET /api/downloads`

Lista todas las descargas con paginación.

**Query params:**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `page` | int | `1` | Página |
| `limit` | int | `20` | Resultados por página |
| `status` | string | — | Filtrar por estado |

**Respuesta `200`:**
```json
{
  "success": true,
  "data": [...],
  "total": 10,
  "page": 1,
  "limit": 20
}
```

---

### `GET /api/downloads/:id`

Obtiene el detalle de una descarga.

**Respuestas:**

| Código | Situación |
|--------|-----------|
| `200` | OK |
| `404` | ID no encontrado |

```json
{
  "success": true,
  "data": {
    "id": 1,
    "url": "https://ejemplo.com/archivo.zip",
    "filename": "archivo.zip",
    "status": "PENDING",
    "total_size": 0,
    "downloaded_size": 0,
    "destination": "/tmp"
  }
}
```

---

### `POST /api/downloads/:id/pause`

Pausa una descarga (cambia `status` a `PAUSED`).

**Respuestas:**

| Código | Situación |
|--------|-----------|
| `200` | Estado actualizado a `PAUSED` |
| `404` | ID no encontrado |

---

### `POST /api/downloads/:id/resume`

Reanuda una descarga (cambia `status` a `DOWNLOADING`).

**Respuestas:**

| Código | Situación |
|--------|-----------|
| `200` | Estado actualizado a `DOWNLOADING` |
| `404` | ID no encontrado |

---

### `DELETE /api/downloads/:id`

Elimina una descarga del historial.

**Respuestas:**

| Código | Situación |
|--------|-----------|
| `200` | Eliminada correctamente |
| `404` | ID no encontrado |

```json
{
  "success": true,
  "message": "Descarga 1 eliminada"
}
```

---

### `GET /api/stats`

Retorna estadísticas globales.

**Respuesta `200`:**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "completed": 7,
    "failed": 1,
    "total_bytes": 1073741824
  }
}
```

---

### `POST /api/validate`

Valida si una URL es aceptada por el sistema.

**Body:**
```json
{ "url": "https://ejemplo.com/archivo.zip" }
```

**Respuesta `200`:**
```json
{
  "success": true,
  "data": {
    "url": "https://ejemplo.com/archivo.zip",
    "valid": true
  }
}
```

---

## Módulos Python

### `src.utils.validators`

```python
from src.utils.validators import (
    is_valid_url,
    sanitize_filename,
    verify_checksum,
    extract_filename_from_url,
    get_file_hash,
    is_supported_url,
)
```

| Función | Signature | Descripción |
|---------|-----------|-------------|
| `is_valid_url` | `(url: Any) -> bool` | Valida URL HTTP/HTTPS |
| `sanitize_filename` | `(filename: str) -> str` | Elimina caracteres inválidos |
| `verify_checksum` | `(filepath, expected, algorithm="sha256") -> bool` | Verifica integridad |
| `extract_filename_from_url` | `(url, headers=None) -> str` | Extrae nombre del archivo |
| `get_file_hash` | `(filepath, algorithm="sha256") -> str` | Calcula hash del archivo |
| `is_supported_url` | `(url: Any) -> bool` | Verifica protocolo soportado |

---

### `src.utils.helpers`

```python
from src.utils.helpers import (
    format_bytes,
    format_speed,
    calculate_eta,
    format_timestamp,
    get_file_extension,
    get_file_icon,
    check_ffmpeg,
    open_file,
    send_notification,
)
```

| Función | Signature | Retorna | Ejemplo |
|---------|-----------|---------|---------|
| `format_bytes` | `(size: int) -> str` | `"1.50 GB"` | `format_bytes(1610612736)` |
| `format_speed` | `(bytes_per_sec: float) -> str` | `"512 KB/s"` | `format_speed(524288)` |
| `calculate_eta` | `(downloaded, total, speed) -> str` | `"2:30"` | `calculate_eta(0, 150, 1)` |
| `format_timestamp` | `(timestamp: float) -> str` | `"2026-04-09 18:00:00"` | `format_timestamp(time.time())` |
| `get_file_extension` | `(filename: str) -> str` | `"zip"` | `get_file_extension("file.zip")` |
| `get_file_icon` | `(extension: str) -> str` | `"📦"` | `get_file_icon("zip")` |
| `check_ffmpeg` | `() -> bool` | `True` si disponible | — |
| `open_file` | `(filepath: str) -> bool` | `True` si se abrió | — |
| `send_notification` | `(title, message) -> None` | — | — |

---

### `src.core.database.Database`

```python
from src.core.database import Database, db  # db = instancia global

db = Database(db_path="~/.downloader/data.db")
```

| Método | Signature | Retorna |
|--------|-----------|---------|
| `create_download` | `(url, filename, destination, title=None, thumbnail=None) -> int` | ID del registro |
| `update_download` | `(download_id, **kwargs) -> None` | — |
| `get_download` | `(download_id: int) -> dict \| None` | Registro o None |
| `get_all_downloads` | `(status: str = None) -> list[dict]` | Lista de registros |
| `get_active_downloads` | `() -> list[dict]` | PENDING + DOWNLOADING + PAUSED |
| `get_completed_downloads` | `() -> list[dict]` | Solo COMPLETED |
| `delete_download` | `(download_id: int) -> bool` | True si se eliminó |
| `clear_history` | `(status: str = None) -> int` | Registros eliminados |
| `get_statistics` | `() -> dict` | `{total, completed, failed, total_bytes}` |

---

### `src.core.downloader.Downloader`

```python
from src.core.downloader import downloader  # instancia global

# O crear instancia propia
from src.core.downloader import Downloader
dl = Downloader()
```

| Método | Signature | Retorna |
|--------|-----------|---------|
| `create_task` | `(url, destination=None, quality="best", file_format=None, max_speed_kbps=0, title=None, thumbnail=None) -> DownloadTask \| None` | Tarea creada |
| `start_download` | `(task_id: int) -> bool` | True si completó |
| `pause_task` | `(task_id: int) -> bool` | True si pausó |
| `resume_task` | `(task_id: int) -> bool` | True si reanudó |
| `cancel_task` | `(task_id: int) -> bool` | True si canceló |
| `remove_task` | `(task_id: int) -> bool` | True si eliminó |
| `get_task` | `(task_id: int) -> DownloadTask \| None` | Tarea o None |
| `set_progress_callback` | `(task_id, callback) -> None` | — |

**Callback de progreso:**
```python
def mi_callback(progress: float, speed: float, extra: str = None, value: str = None):
    print(f"{progress:.1f}% a {speed/1024:.1f} KB/s")

downloader.set_progress_callback(task_id, mi_callback)
```
