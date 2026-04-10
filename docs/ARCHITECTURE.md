# Arquitectura Técnica — DownLoader Pro

## Visión general

DownLoader Pro es una aplicación de escritorio/web construida en Python con tres interfaces de usuario: **GUI web** (Eel + HTML/CSS/JS), **GUI de escritorio** (CustomTkinter) y **CLI** (argparse). Comparten el mismo motor de descargas en `src/core/`.

---

## Diagrama de capas

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACES DE USUARIO                  │
│                                                           │
│   GUI Web (Eel)     │  GUI Escritorio   │  CLI (argparse) │
│   web_gui.py        │  gui/main.py      │  cli/main.py    │
│   index.html + JS   │  CustomTkinter    │  colorama/tqdm  │
└────────────┬────────┴────────┬──────────┴────────┬────────┘
             │                 │                    │
             └─────────────────┼────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                       CORE ENGINE                         │
│                                                           │
│  Downloader          ChunkManager     SocialDownloader   │
│  (downloader.py)     (chunk_mgr.py)  (social_dl.py)     │
│                                                           │
│  DownloadTask (estado, progreso, pause/resume/cancel)    │
└──────────────┬──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│                    INFRAESTRUCTURA                         │
│                                                           │
│  Database (SQLite)   Config (JSON)   Validators/Helpers  │
│  database.py         config.py       utils/              │
└─────────────────────────────────────────────────────────┘
```

---

## Componentes

### `src/core/downloader.py` — Motor principal

**Clase `DownloadTask`**

Representa una unidad de descarga. Contiene todo el estado necesario para controlar su ciclo de vida:

```
PENDING → DOWNLOADING → VERIFYING → COMPLETED
                ↓              ↑
              PAUSED ──────────┘
                ↓
           CANCELLED / FAILED
```

| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `id` | int | ID único (FK con BD) |
| `url` | str | URL de descarga |
| `destination` | Path | Carpeta de destino |
| `status` | str | Estado actual |
| `progress` | float | Porcentaje 0–100 |
| `total_size` | int | Bytes totales |
| `downloaded_size` | int | Bytes descargados |
| `speed` | float | Velocidad actual (bytes/s) |
| `_pause_event` | Event | threading.Event para pause/resume |
| `_stop_event` | Event | threading.Event para cancelación |
| `chunk_manager` | ChunkManager | Gestor de fragmentos |

**Clase `Downloader`**

Singleton global (`downloader = Downloader()` al final del módulo). Gestiona todas las tareas activas en un diccionario `{task_id: DownloadTask}`.

Decisiones de diseño:
- Si `total_size < 10 MB` o `threads = 1` → descarga con un solo hilo
- Si `total_size >= 10 MB` → descarga multihilo con `Range` headers
- Auto-actualiza `yt-dlp` en un thread daemon al arrancar
- Scheduler thread verifica cada 30 segundos si hay descargas programadas

---

### `src/core/chunk_manager.py` — Gestión de fragmentos

Responsable de:
1. Crear un directorio temporal `.{filename}.tmp/` junto al archivo final
2. Guardar el estado de progreso en `state.json` cada ~1 MB
3. Fusionar los fragmentos al completar (`merge_chunks`)
4. Limpiar archivos huérfanos al arrancar

**Estructura de directorios en disco:**

```
~/Downloads/
├── archivo.zip              ← archivo final (solo existe al completar)
└── .archivo.zip.tmp/        ← directorio temporal durante descarga
    ├── state.json            ← {downloaded_size, total_size, elapsed}
    ├── part_0                ← fragmento hilo 0
    ├── part_1                ← fragmento hilo 1
    └── part_2                ← fragmento hilo 2
```

**Resume real:** Al reanudar, `load_state()` devuelve `downloaded_size`. Si hay fragmentos parciales en disco, los hilos envían `Range: bytes={existente}-{fin}` para continuar desde donde dejaron.

---

### `src/core/social_downloader.py` — Redes sociales

Wrapper sobre `yt-dlp`. Detecta si una URL pertenece a una red social por coincidencia de dominio contra una lista de 20+ plataformas.

**Flujo:**
1. `is_social_media_url(url)` → True/False
2. `SocialMediaDownloader.__init__()` construye las `ydl_opts` para yt-dlp
3. `download()` ejecuta `yt-dlp.YoutubeDL(opts).download([url])`
4. El `progress_hook` de yt-dlp actualiza `progress`, `speed` y `status`
5. FFmpeg post-procesa para conversión de formato o extracción de audio

**Opciones de calidad → formato yt-dlp:**

| Calidad | `format` de yt-dlp |
|---------|-------------------|
| `best` | `bestvideo+bestaudio/best` |
| `1080p` | `bestvideo[height<=1080]+bestaudio/best[height<=1080]` |
| `720p` | `bestvideo[height<=720]+bestaudio/best[height<=720]` |
| `480p` | `bestvideo[height<=480]+bestaudio/best[height<=480]` |
| `audio_only` | `bestaudio/best` |
| `video_only` | `bestvideo/best` |

---

### `src/core/database.py` — Persistencia SQLite

Base de datos en `~/.downloader/data.db`. Una sola tabla `downloads`.

**Schema:**

```sql
CREATE TABLE downloads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    filename        TEXT,
    destination     TEXT,
    title           TEXT,
    thumbnail       TEXT,
    total_size      INTEGER DEFAULT 0,
    downloaded_size INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'PENDING',
    speed           REAL DEFAULT 0,
    start_time      REAL,
    end_time        REAL,
    error_message   TEXT,
    checksum        TEXT,
    created_at      TEXT,
    updated_at      TEXT
);
```

**Migración:** Al construir `Database()`, si la columna `title` o `thumbnail` no existen (versión anterior), se agregan con `ALTER TABLE`. Idempotente.

---

### `src/core/config.py` — Configuración

Archivo JSON en `~/.downloader/config.json`. Si no existe, se crea con valores por defecto.

`load_config()` siempre aplica los defaults antes de retornar, por lo que es seguro agregar nuevas claves sin romper instalaciones existentes.

---

### `src/gui/web_gui.py` — Bridge Eel

**Eel** expone funciones Python al navegador mediante `@eel.expose`. El frontend las llama con `await eel.nombre_funcion(args)()`.

El servidor Eel abre en `localhost:8000` (Chromium embebido o navegador del sistema si no hay Chromium).

**Seguridad:** `save_settings()` tiene una allowlist de llaves permitidas para evitar que el frontend modifique configuraciones internas del sistema.

---

### `src/utils/validators.py` — Validación

`is_valid_url()` usa `urllib.parse.urlparse` y verifica:
1. Esquema debe ser `http` o `https`
2. `netloc` no vacío
3. Input debe ser `str`

`sanitize_filename()` reemplaza los caracteres prohibidos en Windows y Unix (`< > : " / \ | ? *`) por `_`, elimina espacios/puntos al inicio y fin, y trunca a 200 caracteres.

---

## Flujos detallados

### Descarga multihilo

```
create_task(url)
    └─ HEAD request → content-length, accept-ranges
         └─ Si accept-ranges = bytes:
              total_size / num_threads → ranges[(start,end), ...]
              Por cada rango → Thread(download_chunk, start, end, thread_id)
                  └─ GET con Range: bytes={start}-{end}
                  └─ Escribe en .tmp/part_{thread_id}
                  └─ Lock → downloaded_bytes[thread_id] += len(chunk)
              Espera threads → merge_chunks() → archivo final
         └─ Si no soporta ranges:
              _download_single() → un hilo, Range: bytes={resume_pos}-
```

### Pause / Resume multihilo

```
pause_task(id)
    └─ task._pause_event.clear()
         └─ Todos los hilos están en: task._pause_event.wait() → se bloquean
         └─ chunk_manager.save_state(downloaded_size, total_size)
         └─ BD: status = PAUSED

resume_task(id)
    └─ task._pause_event.set()
         └─ Hilos se desbloquean y continúan
    └─ BD: status = DOWNLOADING
```

---

## Decisiones técnicas

| Decisión | Alternativas | Razón |
|----------|-------------|-------|
| Eel para GUI web | Flask+pywebview, Electron | Eel es más ligero y bidireccional nativo Python↔JS |
| SQLite para persistencia | JSON file, PostgreSQL | Sin dependencias externas, suficiente para uso desktop |
| yt-dlp para redes sociales | youtube-dl, pytube | Más activo, más plataformas, mejor mantenimiento |
| threading estándar | asyncio, multiprocessing | Compatible con requests y el patrón pause/resume con Events |
| Fragmentos en disco | En memoria | Permite resume real tras crash o reinicio del sistema |

---

## Limitaciones conocidas

- **Descargas sociales:** No soportan resume real (yt-dlp reinicia desde cero al reanudar)
- **GUI de escritorio (CustomTkinter):** Menos funcionalidades que la GUI web; ambas coexisten pero la web es la principal
- **Windows:** Requiere Chromium instalado para la GUI web embebida; sin él usa el navegador del sistema
- **scheduler:** Actualmente no inicia descargas en un proceso separado; requiere que la app esté corriendo
