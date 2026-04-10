"""
Configuracion de Playwright para pruebas UI - DownLoader Pro v2.1.0
ISO/IEC 29119 - Test Plan, seccion 4.3
"""

import os

# URL base del servidor GUI
BASE_URL = os.environ.get("GUI_BASE_URL", "http://localhost:8000")

# Configuracion del navegador
BROWSER = os.environ.get("PLAYWRIGHT_BROWSER", "chromium")
HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

# Timeouts (ms)
DEFAULT_TIMEOUT = 30_000
NAVIGATION_TIMEOUT = 30_000
ACTION_TIMEOUT = 10_000

# Capturas de pantalla
SCREENSHOT_ON_FAILURE = True
SCREENSHOTS_DIR = os.environ.get("PLAYWRIGHT_SCREENSHOTS_DIR", "test-results/screenshots")

# Videos
RECORD_VIDEO = os.environ.get("PLAYWRIGHT_RECORD_VIDEO", "false").lower() == "true"
VIDEOS_DIR = os.environ.get("PLAYWRIGHT_VIDEOS_DIR", "test-results/videos")

# Configuracion de pytest-playwright (usada en conftest.py via fixture browser_context_args)
BROWSER_CONTEXT_ARGS = {
    "viewport": {"width": 1280, "height": 720},
    "locale": "es-MX",
    "timezone_id": "America/Mexico_City",
}
