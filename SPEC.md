# DownLoader - Especificación Completa

## 1. Información General

**Nombre:** DownLoader  
**Tipo:** Gestor de descargas de archivos  
**Lenguaje:** Python 3.8+  
**Interfaces:** CLI (línea de comandos) + GUI (gráfica)

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
│   │   └── history.py        # Gestión de historial
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py           # Interfaz CLI
│   └── gui/
│       ├── __init__.py
│       └── main.py           # Interfaz GUI (Tkinter)
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
python3-tk (para GUI)
```

---

## 4. Funcionalidades Actuales

### 4.1 Motor de Descargas (downloader.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Descarga simple | ✅ | Descarga archivos mediante requests |
| Multithreading | ✅ | Archivos >10MB usan múltiples conexiones |
| Pausar/Reanudar | ✅ | Control de estado con eventos |
| Barra de progreso | ✅ | Visualización con tqdm |
| Validación URL | ✅ | Verifica tamaño antes de descargar |
| Manejo de errores | ✅ | Captura excepciones |

**Clases:**
- `DownloadTask`: Representa una descarga individual
- `Downloader`: Gestor principal de descargas

**Estados de tarea:** `pending`, `downloading`, `paused`, `completed`, `failed`, `cancelled`

### 4.2 Historial (history.py)

| Característica | Estado | Descripción |
|----------------|--------|-------------|
| Persistencia | ✅ | JSON en ~/.downloader/history.json |
| Agregar entrada | ✅ | Registra URL, archivo, tamaño, estado |
| Ver historial | ✅ | Lista todas las descargas |
| Limpiar | ✅ | Elimina todo el historial |

### 4.3 Configuración (config.py)

| Configuración | Default | Descripción |
|--------------|---------|-------------|
| default_threads | 4 | Hilos para descargas |
| default_download_path | ~/Downloads | Ruta de descarga |
| chunk_size | 1048576 | Tamaño de chunk (1MB) |
| max_retries | 3 | Reintentos máximos |
| timeout | 30 | Timeout de conexión |

### 4.4 CLI (cli/main.py)

Comandos disponibles:
```
add <url> [destino]    - Agregar nueva descarga
list                    - Listar descargas activas
history                 - Ver historial de descargas
pause <id>             - Pausar descarga
resume <id>            - Reanudar descarga
cancel <id>            - Cancelar descarga
remove <id>            - Eliminar descarga
config --show          - Ver configuración
config --threads N     - Configurar hilos
config --path <ruta>   - Configurar ruta
```

### 4.5 GUI (gui/main.py)

**Características visuales actuales:**
- Tema oscuro (#1a1a2e, #16213e)
- Color acento rojo/coral (#e94560)
- Panel de estadísticas
- Diseño de tarjetas
- Botones modernos

**Componentes UI:**
- Campo de URL
- Selector de carpeta
- Lista de descargas activas
- Lista de historial
- Botones de control (Pausar, Reanudar, Cancelar, Eliminar)
- Ventana de configuración

---

## 5. Funcionalidades Pendientes / Mejoras Sugeridas

### 5.1 Motor de Descargas

- [ ] **Pausar/Reanudar real**: Guardar estado intermedio y continuar desde donde se quedó
- [ ] **Descarga分段 (Resume)**: Soporte completo para Range headers en descargas grandes
- [ ] **Verificación de integridad**: Checksum MD5/SHA256
- [ ] **Cola de descargas**: Queue con prioridad
- [ ] **Límite de velocidad**: Throttling de descarga
- [ ] **Proxy/SOCKS**: Soporte para proxies
- [ ] **Cookies/Headers personalizados**: Configurar headers
- [ ] **Autenticación**: HTTP Basic Auth, Bearer tokens

### 5.2 Historial

- [ ] **Buscar**: Filtrar por nombre/URL
- [ ] **Categorías**: Organizar por tipo de archivo
- [ ] **Estadísticas**: Gráficos de descargas
- [ ] **Exportar**: CSV, JSON

### 5.3 GUI

- [ ] **Barra de progreso visual**: ProgressBar dentro de las filas
- [ ] **Arrastrar y soltar**: Drag & drop de URLs
- [ ] **Notificaciones**: Sistema de notificaciones nativas
- [ ] **Temas**: Selector de temas (oscuro/claro)
- [ ] **Mini ventana**: Modo minimizado
- [ ] **Atajos de teclado**: Shortcuts
- [ ] **Icono en bandeja**: System tray
- [ ] **Actualización en tiempo real**: Live updates de progreso

### 5.4 CLI

- [ ] **Cola interactiva**: Modo interactivo
- [ ] **Comandos asíncronos**: No bloquear terminal
- [ ] **Output JSON**: Para scripting

### 5.5 General

- [ ] **Tests unitarios**: Cobertura de código
- [ ] **Type hints**: Mejor tipado
- [ ] **Logging**: Sistema de logs
- [ ] **Plugin system**: Extensibilidad
- [ ] **Multi-idioma**: i18n

---

## 6. Problemas Conocidos

1. **Multithreading inestable**: A veces las descargas multithread no completan correctamente
2. **GUI sin auto-refresh**: No actualiza progreso automáticamente
3. **Pausar no es real**: Solo cambia el estado, no reanuda desde el punto
4. **Sin manejo de redirecciones complejas**: Solo follow redirects básico

---

## 7. APIs y Librerías Utilizadas

| Librería | Uso |
|----------|-----|
| requests | HTTP requests |
| tqdm | Barras de progreso |
| colorama | Colores en CLI |
| tkinter | Interfaz gráfica |
| threading | Concurrencia |
| json | Persistencia |

---

## 8. Configuración de Usuario

Ubicación: `~/.downloader/`
```
~/.downloader/
├── config.json    # Configuración
└── history.json  # Historial
```

---

## 9. Ejemplos de Uso

### CLI
```bash
# Descargar archivo
python main.py add "https://ejemplo.com/archivo.zip" ~/Downloads

# Ver historial
python main.py history

# Configurar hilos
python main.py config --threads 8
```

### GUI
```bash
python main.py --gui
```

---

## 10. Métricas de Código

- **Líneas totales**: ~600
- **Módulos**: 6 archivos Python
- **Dependencias externas**: 3

---

## 11. Objetivos para Mejora

1. **Estabilidad**: Arreglar multithreading y pause/resume real
2. **UX**: Auto-refresh en GUI, drag & drop
3. **Features**: Proxy, autenticación, throttle
4. **Calidad**: Tests, type hints, logging

---

*Documento generado para referencia de desarrollo futuro*
