# DownLoader

Gestor de descargas con CLI y GUI para Python.

## Características

- ✅ **Multithreading**: Descargas más rápidas con múltiples conexiones
- ✅ **Pause/Resume real**: Continúa descargas desde donde se quedó
- ✅ **Throttling**: Limita la velocidad de descarga
- ✅ **Verificación de integridad**: Checksum MD5/SHA256
- ✅ **System Tray**: Minimiza a la bandeja del sistema
- ✅ **Redes sociales**: Soporte para YouTube, Twitter, Instagram, etc.
- ✅ **CLI**: Interfaz de línea de comandos avanzada
- ✅ **GUI**: Interfaz gráfica moderna con CustomTkinter

## Requisitos

- Python 3.8+
- Ver `requirements.txt`

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Interfaz Gráfica (GUI)

```bash
python main.py --gui
```

### Línea de Comandos (CLI)

#### Agregar descarga
```bash
python main.py add "https://ejemplo.com/archivo.zip" /ruta/destino
```

#### Agregar con límite de velocidad
```bash
python main.py add "https://ejemplo.com/archivo.zip" --speed 500
```

#### Listar descargas activas
```bash
python main.py list
```

#### Ver historial
```bash
python main.py history
```

#### Dashboard
```bash
python main.py dashboard
```

#### Pausar descarga
```bash
python main.py pause <id>
```

#### Reanudar descarga
```bash
python main.py resume <id>
```

#### Cancelar descarga
```bash
python main.py cancel <id>
```

#### Configuración
```bash
python main.py config --show              # Ver configuración
python main.py config --threads 8         # Cambiar hilos
python main.py config --speed 1000         # Velocidad máxima KB/s
python main.py config --checksum sha256    # Verificación MD5/SHA256
python main.py config --path ~/Downloads   # Cambiar ruta
```

## Estructura del Proyecto

```
DownLoader/
├── src/
│   ├── core/           # Motor de descargas
│   │   ├── downloader.py      # Descargador principal
│   │   ├── chunk_manager.py   # Gestión de fragmentos y resume
│   │   ├── database.py        # Base de datos SQLite
│   │   └── config.py          # Configuración
│   ├── cli/            # Interfaz CLI
│   │   └── main.py
│   ├── gui/            # Interfaz GUI
│   │   ├── main.py
│   │   └── system_tray.py     # Icono de bandeja
│   └── utils/          # Utilidades
├── main.py
├── setup.py
└── requirements.txt
```

## Configuración

La configuración se guarda en `~/.downloader/config.json`:
- `default_threads`: Hilos por defecto (4)
- `default_download_path`: Ruta de descarga
- `max_speed_kbps`: Velocidad máxima (0 = sin límite)
- `checksum_type`: Tipo de verificación (none/md5/sha256)
- `timeout`: Timeout de conexión
- `minimize_to_tray`: Minimizar a bandeja al cerrar

## Licencia

MIT
