import os
import sys
import threading
from io import BytesIO

try:
    from PIL import Image, ImageDraw

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pystray

    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

import logging

logger = logging.getLogger(__name__)


def create_default_icon():
    """Crea un icono por defecto si PIL está disponible."""
    if not HAS_PIL:
        return None

    size = (64, 64)
    image = Image.new("RGB", size, color="#e94560")
    draw = ImageDraw.Draw(image)

    draw.ellipse([8, 8, 56, 56], fill="#ffffff")
    draw.polygon([(20, 35), (45, 35), (35, 50)], fill="#e94560")

    return image


class SystemTray:
    """Gestor de system tray para la aplicación."""

    def __init__(self, root, downloader):
        self.root = root
        self.downloader = downloader
        self.tray = None
        self._running = False

        if not HAS_PYSTRAY:
            logger.warning(
                "pystray no está instalado. System tray no estará disponible."
            )
            return

        self._setup_tray()

    def _setup_tray(self):
        """Configura el icono del system tray."""
        icon_image = create_default_icon()

        if icon_image is None:
            logger.error("No se pudo crear el icono del system tray")
            return

        menu = pystray.Menu(
            pystray.MenuItem("Mostrar", self._show_window, default=True),
            pystray.MenuItem("Ocultar", self._hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Pausar Todas", self._pause_all),
            pystray.MenuItem("Reanudar Todas", self._resume_all),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._quit),
        )

        self.tray = pystray.Icon("downloader", icon_image, "DownLoader", menu)

        self._running = True

    def _show_window(self, icon=None, item=None):
        """Muestra la ventana principal."""
        if self.root:
            self.root.after(0, self._show_root)

    def _show_root(self):
        """Callback para mostrar ventana."""
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()

    def _hide_window(self, icon=None, item=None):
        """Oculta la ventana principal."""
        if self.root:
            self.root.after(0, self.root.withdraw)

    def _pause_all(self, icon=None, item=None):
        """Pausa todas las descargas activas."""
        for task_id, task in list(self.downloader.tasks.items()):
            if task.status == "DOWNLOADING":
                self.downloader.pause_task(task_id)
        logger.info("Todas las descargas pausadas")

    def _resume_all(self, icon=None, item=None):
        """Reanuda todas las descargas pausadas."""
        for task_id, task in list(self.downloader.tasks.items()):
            if task.status == "PAUSED":
                self.downloader.resume_task(task_id)
        logger.info("Todas las descargas reanudadas")

    def _quit(self, icon=None, item=None):
        """Cierra la aplicación."""
        self.stop()
        if self.root:
            self.root.after(0, self.root.quit)

    def run(self):
        """Inicia el thread del system tray."""
        if self.tray and self._running:
            self._tray_thread = threading.Thread(target=self.tray.run, daemon=True)
            self._tray_thread.start()

    def stop(self):
        """Detiene el system tray."""
        self._running = False
        if self.tray:
            self.tray.stop()

    def update_tooltip(self, message: str):
        """Actualiza el tooltip del icono."""
        if self.tray and self._running:
            try:
                self.tray.title = f"DownLoader - {message}"
            except Exception:
                pass
