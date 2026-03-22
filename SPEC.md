# DownLoader - Especificación Completa

## 1. Información General

**Nombre:** DownLoader Pro  
**Tipo:** Gestor de descargas avanzado con aceleración y soporte de redes sociales  
**Versión:** 2.1.0 (Producción)  
**Lenguaje:** Python 3.8+ / JavaScript (ES6+)  
**Interfaces:** CLI + Web GUI (Global Glassmorphism)  
**Idioma Primario:** Español (i18n unificado)

---

## 2. Estructura del Proyecto

```
DownLoader/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuración y persistencia
│   │   ├── downloader.py     # Motor de descargas
│   │   ├── chunk_manager.py  # Gestión de fragmentos y resume
│   │   ├── database.py       # Base de datos SQLite
│   │   └── social_downloader.py # Descargas de redes sociales
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py           # Interfaz CLI
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main.py           # Interfaz GUI (CustomTkinter)
│   │   └── system_tray.py    # Icono de bandeja del sistema
│   └── utils/
│       ├── validators.py     # Validación de URLs
│       └── helpers.py        # Utilidades
├── main.py                   # Punto de entrada
├── setup.py                  # Setuptools
├── requirements.txt          # Dependencias
└── README.md                # Documentación
```

---

## 3. Dependencias

```
requests>=2.28.0
tqdm>=4.65.0
colorama>=0.4.6
customtkinter>=5.2.0
plyer>=2.1.0
yt-dlp>=2026.3.0
ffmpeg-python>=0.2.0
eel>=0.16.0
pystray>=0.19.0
Pillow>=10.0.0
```

---

## 4. Funcionalidades Actuales

### 4.1 Motor de Descargas (downloader.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Descarga simple | ✅ | Descarga archivos mediante requests |
| Multithreading | ✅ | Archivos >10MB usan múltiples conexiones |
| Pause/Resume real | ✅ | Guarda estado con Range headers |
| Throttling | ✅ | Límite de velocidad configurable |
| Verificación checksum | ✅ | MD5/SHA256 post-descarga |
| Barra de progreso | ✅ | Visualización en tiempo real |
| Validación URL | ✅ | Verifica tamaño antes de descargar |
| Manejo de errores | ✅ | Captura excepciones |
| Redes sociales | ✅ | Soporte para YouTube, Twitter, Instagram, etc. |

**Clases:**
- `DownloadTask`: Representa una descarga individual
- `Downloader`: Gestor principal de descargas

**Estados de tarea:** `PENDING`, `DOWNLOADING`, `PAUSED`, `VERIFYING`, `COMPLETED`, `FAILED`, `CANCELLED`

### 4.2 Gestor de Fragmentos (chunk_manager.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Crear directorio temporal | ✅ | Almacena fragmentos |
| Fusionar fragmentos | ✅ | Une archivos al completar |
| Guardar estado | ✅ | Persiste progreso para resume |
| Cargar estado | ✅ | Recupera progreso guardado |
| Limpiar fragmentos | ✅ | Elimina archivos temporales |

### 4.3 Base de Datos (database.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Persistencia SQLite | ✅ | Historial completo |
| Estadísticas | ✅ | Bytes totales, completadas, fallidas |
| Checksum | ✅ | Almacena hash de archivos |
| Índices optimizados | ✅ | Por estado y fecha |

### 4.4 Configuración (config.py)

| Configuración | Default | Descripción |
|--------------|---------|-------------|
| default_threads | 4 | Hilos para descargas |
| default_download_path | ~/Downloads | Ruta de descarga |
| chunk_size | 1048576 | Tamaño de chunk (1MB) |
| max_retries | 3 | Reintentos máximos |
| timeout | 30 | Timeout de conexión |
| max_speed_kbps | 0 | Límite de velocidad (0=sin límite) |
| checksum_type | null | Tipo de verificación (md5/sha256) |
| minimize_to_tray | true | Minimizar a bandeja |

### 4.5 System Tray (system_tray.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Icono en bandeja | ✅ | Icono animado |
| Mostrar/Ocultar | ✅ | Control de ventana |
| Pausar todas | ✅ | Pausa masiva |
| Reanudar todas | ✅ | Reanudación masiva |
| Salir | ✅ | Cierre seguro |

### 4.6 CLI (cli/main.py)

Comandos disponibles:
```
add <url> [destino]        - Agregar nueva descarga
  --quality, -q            - Calidad (best, 1080p, 720p, 480p, audio_only)
  --format, -f             - Formato (mp4, webm, mkv, mp3, m4a, flac)
  --speed, -s              - Velocidad máxima en KB/s
list                        - Listar descargas activas
history                     - Ver historial de descargas
stats                       - Ver estadísticas
dashboard                   - Panel de control
pause <id>                 - Pausar descarga
resume <id>                - Reanudar descarga
cancel <id>                - Cancelar descarga
remove <id>                - Eliminar descarga
open <id>                  - Abrir archivo descargado
clear [status]             - Limpiar historial
config --show              - Ver configuración
config --threads N         - Configurar hilos
config --path <ruta>       - Configurar ruta
config --speed N           - Configurar velocidad máxima
config --checksum <tipo>   - Tipo de checksum (none, md5, sha256)
```

### 4.7 GUI (gui/main.py)

**Características visuales:**
- Tema oscuro (#1a1a2e, #16213e)
- Color acento rojo/coral (#e94560)
- Panel de estadísticas
- Diseño de tarjetas
- Botones modernos
- System tray integrado

**Componentes UI:**
- Campo de URL
- Selector de carpeta
- Lista de descargas activas
- Lista de historial
- Barra de progreso circular y lineal
- Botones de control (Pausar, Reanudar, Cancelar, Eliminar)
- Ventana de configuración avanzada (persistente)
- Notificaciones nativas del sistema (vía plyer)
- Sección de sustentabilidad (Soporte al desarrollador)
- Diseño responsivo y multi-vista (Cola, Panel, Historial, Ajustes)

---

## 5. Funcionalidades Pendientes / Mejoras Sugeridas

### 5.1 Motor de Descargas

- [ ] **Cola de descargas**: Queue con prioridad
- [ ] **Proxy/SOCKS**: Soporte para proxies
- [ ] **Cookies/Headers personalizados**: Configurar headers
- [ ] **Autenticación**: HTTP Basic Auth, Bearer tokens

### 5.2 Historial

- [ ] **Buscar**: Filtrar por nombre/URL
- [ ] **Categorías**: Organizar por tipo de archivo
- [ ] **Estadísticas**: Gráficos de descargas
- [ ] **Exportar**: CSV, JSON

### 5.3 GUI

- [ ] **Drag & drop**: Arrastrar URLs
- [ ] **Notificaciones**: Notificaciones nativas del sistema
- [ ] **Temas**: Selector de temas (oscuro/claro)
- [ ] **Atajos de teclado**: Shortcuts
- [ ] **Mini ventana**: Modo minimizado

### 5.4 CLI

- [ ] **Cola interactiva**: Modo interactivo
- [ ] **Comandos asíncronos**: No bloquear terminal
- [ ] **Output JSON**: Para scripting

### 5.5 General

- [ ] **Tests unitarios**: Cobertura de código
- [ ] **Type hints**: Mejor tipado
- [ ] **Plugin system**: Extensibilidad
- [ ] **Multi-idioma**: i18n

---

## 6. Problemas Conocidos

1. ~~Multithreading inestable~~ - ✅ Arreglado con manejo de errores robusto
2. ~~GUI sin auto-refresh~~ - ✅ Actualización automática cada 2 segundos
3. ~~Pausar no es real~~ - ✅ Ahora guarda estado y reanuda desde donde quedó
4. Sin manejo de redirecciones complejas

---

## 7. APIs y Librerías Utilizadas

| Librería | Uso |
|----------|-----|
| requests | HTTP requests |
| tqdm | Barras de progreso |
| colorama | Colores en CLI |
| customtkinter | Interfaz gráfica moderna |
| pystray | System tray |
| Pillow | Generación de iconos |
| threading | Concurrencia |
| sqlite3 | Persistencia |
| hashlib | Checksums |

---

## 8. Configuración de Usuario

Ubicación: `~/.downloader/`
```
~/.downloader/
├── config.json    # Configuración
└── data.db        # Base de datos SQLite
```

---

## 9. Ejemplos de Uso

### CLI
```bash
# Descargar archivo
python main.py add "https://ejemplo.com/archivo.zip" ~/Downloads

# Descargar con límite de velocidad
python main.py add "https://ejemplo.com/archivo.zip" --speed 500

# Ver historial
python main.py history

# Configurar velocidad máxima
python main.py config --speed 1000

# Configurar verificación de integridad
python main.py config --checksum sha256

# Dashboard
python main.py dashboard
```

### GUI
```bash
python main.py --gui
```

---

## 10. Métricas de Código

- **Líneas totales**: ~800
- **Módulos**: 10 archivos Python
- **Dependencias externas**: 10

---

## 11. Cambios Recientes

### v2.1 - Lanzamiento Producción (Marzo 2026)

1. **Interfaz "Pure Crystal"**
   - Rediseño completo con Glassmorphism global.
   - Animaciones fluidas y orbes ambientales.
   - Unificación de idioma a Español.

2. **Seguridad y Robustez**
   - Verificación proactiva de espacio en disco antes de iniciar descargas.
   - Limpieza automática de archivos temporales huérfanos (>24h).
   - Corrección de bugs de persistencia en configuración.

3. **Notificaciones y Feedback**
   - Notificaciones nativas de escritorio para eventos de finalización/error.
   - Sistema de "Toasts" visuales en la interfaz.

4. **Distribución**
   - Script de construcción `build.py` para generar ejecutables `.exe`.
   - Icono profesional de alta resolución (`assets/icon.ico`).
   - Sistema de soporte integrado para sustentabilidad.

---

*Documento generado para referencia de desarrollo futuro*
