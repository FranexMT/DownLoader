"""
Configuracion y fixtures para pruebas UI con Playwright.
ISO/IEC 29119 - Test Plan, seccion 4.3
"""

import os
import sys
import time
import subprocess
import socket
import pytest

# Puerto donde corre el servidor Eel/GUI
GUI_PORT = int(os.environ.get("GUI_PORT", 8000))
GUI_HOST = os.environ.get("GUI_HOST", "localhost")
GUI_BASE_URL = f"http://{GUI_HOST}:{GUI_PORT}"

# Directorio raiz del proyecto
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _port_is_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Comprueba si un puerto esta abierto."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def _wait_for_port(host: str, port: int, retries: int = 30, delay: float = 1.0) -> bool:
    """Espera a que el puerto este disponible."""
    for _ in range(retries):
        if _port_is_open(host, port):
            return True
        time.sleep(delay)
    return False


@pytest.fixture(scope="session")
def gui_server():
    """
    Inicia el servidor Eel si no esta corriendo.
    En CI se espera que el servidor ya este corriendo antes de ejecutar los tests.
    Retorna la URL base del servidor.
    """
    if _port_is_open(GUI_HOST, GUI_PORT):
        yield GUI_BASE_URL
        return

    # Intentar iniciar el servidor
    proc = subprocess.Popen(
        [sys.executable, "-m", "src.gui.web_gui"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    available = _wait_for_port(GUI_HOST, GUI_PORT, retries=30, delay=1.0)
    if not available:
        proc.terminate()
        pytest.skip(f"GUI server no disponible en {GUI_BASE_URL}")

    yield GUI_BASE_URL

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="function")
def page_with_gui(page, gui_server):
    """Pagina de Playwright apuntando a la GUI."""
    page.goto(gui_server)
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture(scope="function")
def screenshot_dir(tmp_path):
    """Directorio para guardar capturas de pantalla de los tests."""
    screenshots = tmp_path / "screenshots"
    screenshots.mkdir()
    return screenshots
