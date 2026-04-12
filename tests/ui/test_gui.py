"""
Pruebas UI automatizadas con Playwright para DownLoader Pro.
Requiere que el servidor Flask (tests/api/server.py) este corriendo en puerto 5001.

Ejecutar: pytest tests/ui/test_gui.py -v
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5001"


def test_page_loads_correctly(page: Page):
    """CP-UI-01: Verifica que la pagina principal carga con el titulo correcto."""
    page.goto(BASE_URL)
    expect(page).to_have_title("DownLoader Pro - Test UI")


def test_app_title_visible(page: Page):
    """CP-UI-02: Verifica que el encabezado principal es visible."""
    page.goto(BASE_URL)
    heading = page.locator("#app-title")
    expect(heading).to_be_visible()
    expect(heading).to_contain_text("DownLoader Pro")


def test_url_form_elements_exist(page: Page):
    """CP-UI-03: Verifica que el formulario tiene todos sus elementos."""
    page.goto(BASE_URL)
    expect(page.locator("#url-input")).to_be_visible()
    expect(page.locator("#validate-btn")).to_be_visible()
    expect(page.locator("#validation-result")).to_be_attached()


def test_valid_url_shows_success_message(page: Page):
    """CP-UI-04: URL valida muestra mensaje de exito."""
    page.goto(BASE_URL)
    page.fill("#url-input", "https://example.com/archivo.zip")
    page.click("#validate-btn")
    result = page.locator("#validation-result")
    expect(result).to_contain_text("URL valida")


def test_invalid_url_shows_error_message(page: Page):
    """CP-UI-05: URL invalida muestra mensaje de error."""
    page.goto(BASE_URL)
    page.fill("#url-input", "esto-no-es-una-url")
    page.click("#validate-btn")
    result = page.locator("#validation-result")
    expect(result).to_contain_text("invalida")


def test_stats_section_loads_with_data(page: Page):
    """CP-UI-06: La seccion de estadisticas carga datos del servidor."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    stats = page.locator("#stats-content")
    expect(stats).to_contain_text("Total:")
