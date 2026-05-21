"""
Configuracion y fixtures para pruebas UI con Playwright.
ISO/IEC 29119 - Test Plan, seccion 4.3
"""

import os
import sys
import time
import socket
import threading
import pytest
import pytest_playwright

GUI_PORT = 8000
GUI_HOST = "localhost"
GUI_BASE_URL = f"http://{GUI_HOST}:{GUI_PORT}"

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _port_is_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError):
        return False


def _wait_for_port(host: str, port: int, retries: int = 30, delay: float = 1.0) -> bool:
    for _ in range(retries):
        if _port_is_open(host, port):
            return True
        time.sleep(delay)
    return False


def _run_flask_server(port: int):
    sys.path.insert(0, PROJECT_ROOT)
    from tests.api.server import app

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


@pytest.fixture(scope="session")
def gui_server():
    if _port_is_open(GUI_HOST, GUI_PORT):
        yield GUI_BASE_URL
        return

    thread = threading.Thread(target=_run_flask_server, args=(GUI_PORT,), daemon=True)
    thread.start()

    if not _wait_for_port(GUI_HOST, GUI_PORT, retries=30, delay=1.0):
        pytest.skip(f"GUI server no disponible en {GUI_BASE_URL}")

    yield GUI_BASE_URL


@pytest.fixture(scope="function")
def page_with_gui(page, gui_server):
    page.goto(gui_server)
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture(scope="function")
def screenshot_dir(tmp_path):
    screenshots = tmp_path / "screenshots"
    screenshots.mkdir()
    return screenshots


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    page = item.funcargs.get("page")
    if page:
        screenshots_dir = "test-results/screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)
        if report.when == "call" and report.failed:
            page.screenshot(path=f"{screenshots_dir}/{item.name}_failure.png")
            print(f"\nScreenshot guardado: {screenshots_dir}/{item.name}_failure.png")
        elif report.when == "call" and report.passed:
            page.screenshot(path=f"{screenshots_dir}/{item.name}_passed.png")
            print(f"\nScreenshot guardado: {screenshots_dir}/{item.name}_passed.png")
