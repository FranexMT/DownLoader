# DownLoader

Gestor de descargas con CLI y GUI para Python.

## Características

- ✅ **Multithreading**: Descargas más rápidas con múltiples conexiones
- ✅ **Pausar/Reanudar**: Control total sobre las descargas
- ✅ **Barra de progreso**: Visualización en tiempo real
- ✅ **Historial**: Registro de todas las descargas
- ✅ **CLI**: Interfaz de línea de comandos
- ✅ **GUI**: Interfaz gráfica con Tkinter

## Requisitos

- Python 3.8+
- requests
- tqdm
- colorama (para CLI)

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

#### Listar descargas activas
```bash
python main.py list
```

#### Ver historial
```bash
python main.py history
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
python main.py config --path ~/Downloads   # Cambiar ruta
```

## Estructura del Proyecto

```
DownLoader/
├── src/
│   ├── core/           # Motor de descargas
│   │   ├── downloader.py
│   │   ├── history.py
│   │   └── config.py
│   ├── cli/            # Interfaz CLI
│   │   └── main.py
│   └── gui/            # Interfaz GUI
│       └── main.py
├── main.py
├── setup.py
└── requirements.txt
```

## Configuración

La configuración se guarda en `~/.downloader/config.json`:
- `default_threads`: Hilos por defecto (4)
- `default_download_path`: Ruta de descarga
- `chunk_size`: Tamaño de chunk
- `max_retries`: Reintentos máximos
- `timeout`: Timeout de conexión

## Licencia

MIT
