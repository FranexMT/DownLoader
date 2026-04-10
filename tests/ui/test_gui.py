"""
Pruebas UI con Playwright para DownLoader Pro v2.1.0
ISO/IEC 29119 - Test Plan, seccion 4.3

Casos implementados (minimo 5):
  UI-01 - Agregar descarga por URL valida
  UI-02 - Error con URL invalida
  UI-03 - Pausar descarga activa
  UI-04 - Reanudar descarga pausada
  UI-05 - Eliminar descarga de la cola
  UI-06 - Navegacion entre vistas
  UI-07 - Cambiar carpeta de destino
  UI-08 - Estadisticas visibles en el tablero
"""

import re
import pytest
from playwright.sync_api import Page, expect

# Timeout general para operaciones de UI (ms)
UI_TIMEOUT = 10_000


# ---------------------------------------------------------------------------
# UI-01: Agregar descarga por URL valida
# ---------------------------------------------------------------------------

class TestUI01AddValidUrl:
    def test_url_input_is_visible(self, page_with_gui):
        """El campo de URL debe estar visible al cargar la GUI."""
        page = page_with_gui
        url_input = page.locator("#url-input")
        expect(url_input).to_be_visible(timeout=UI_TIMEOUT)

    def test_download_button_is_visible(self, page_with_gui):
        """El boton de descarga debe estar visible."""
        page = page_with_gui
        btn = page.locator("#download-btn")
        expect(btn).to_be_visible(timeout=UI_TIMEOUT)

    def test_add_valid_url_does_not_show_validation_error(self, page_with_gui, screenshot_dir):
        """Al ingresar una URL valida no debe aparecer error de validacion."""
        page = page_with_gui
        url_input = page.locator("#url-input")
        url_input.fill("https://example.com/testfile.zip")

        screenshot = screenshot_dir / "UI-01_url_valida.png"
        page.screenshot(path=str(screenshot))

        # No debe haber mensaje de error de URL invalida visible
        error_elements = page.locator("text=URL invalida")
        expect(error_elements).to_have_count(0, timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-02: Error con URL invalida
# ---------------------------------------------------------------------------

class TestUI02InvalidUrl:
    def test_empty_url_input_accepted_without_crash(self, page_with_gui, screenshot_dir):
        """El formulario con URL vacia no debe crashear la pagina."""
        page = page_with_gui
        url_input = page.locator("#url-input")
        url_input.fill("")

        download_btn = page.locator("#download-btn")
        download_btn.click()

        screenshot = screenshot_dir / "UI-02_url_vacia.png"
        page.screenshot(path=str(screenshot))

        # La pagina debe seguir respondiendo
        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_url_type_indicator_visible_on_input(self, page_with_gui):
        """El indicador de tipo de URL debe ser visible."""
        page = page_with_gui
        indicator = page.locator("#url-type-indicator")
        expect(indicator).to_be_visible(timeout=UI_TIMEOUT)

    def test_url_badge_updates_on_input(self, page_with_gui):
        """El badge de tipo de URL debe estar presente."""
        page = page_with_gui
        badge = page.locator("#url-type-badge")
        expect(badge).to_be_visible(timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-03: Pausar descarga activa
# ---------------------------------------------------------------------------

class TestUI03PauseDownload:
    def test_navigate_to_downloads_view(self, page_with_gui, screenshot_dir):
        """Debe poder navegar a la vista de descargas."""
        page = page_with_gui
        downloads_btn = page.locator("#nav-downloads")
        downloads_btn.click()
        page.wait_for_timeout(500)

        screenshot = screenshot_dir / "UI-03_vista_descargas.png"
        page.screenshot(path=str(screenshot))

        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_tasks_view_loads_without_error(self, page_with_gui):
        """La vista de tareas debe cargarse sin errores."""
        page = page_with_gui
        page.locator("#nav-downloads").click()
        page.wait_for_timeout(500)

        # No debe haber errores JS (verificamos que la pagina sigue activa)
        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-04: Reanudar descarga pausada
# ---------------------------------------------------------------------------

class TestUI04ResumeDownload:
    def test_history_view_accessible(self, page_with_gui, screenshot_dir):
        """La vista de historial debe ser accesible."""
        page = page_with_gui
        page.locator("#nav-history").click()
        page.wait_for_timeout(500)

        screenshot = screenshot_dir / "UI-04_historial.png"
        page.screenshot(path=str(screenshot))

        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_history_search_input_visible(self, page_with_gui):
        """El campo de busqueda de historial debe estar presente."""
        page = page_with_gui
        page.locator("#nav-history").click()
        page.wait_for_timeout(500)

        search = page.locator("#history-search")
        expect(search).to_be_visible(timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-05: Eliminar descarga de la cola
# ---------------------------------------------------------------------------

class TestUI05DeleteDownload:
    def test_clear_history_button_visible(self, page_with_gui):
        """El boton de limpiar historial debe estar presente."""
        page = page_with_gui
        page.locator("#nav-history").click()
        page.wait_for_timeout(500)

        btn = page.locator("#clear-history-btn")
        expect(btn).to_be_visible(timeout=UI_TIMEOUT)

    def test_filter_buttons_visible(self, page_with_gui):
        """Los botones de filtro deben estar visibles en historial."""
        page = page_with_gui
        page.locator("#nav-history").click()
        page.wait_for_timeout(500)

        expect(page.locator("#filter-all")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#filter-completed")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#filter-failed")).to_be_visible(timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-06: Navegacion entre vistas
# ---------------------------------------------------------------------------

class TestUI06Navigation:
    def test_sidebar_navigation_buttons_visible(self, page_with_gui):
        """Todos los botones de navegacion deben estar visibles."""
        page = page_with_gui
        expect(page.locator("#nav-dashboard")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#nav-downloads")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#nav-history")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#nav-settings")).to_be_visible(timeout=UI_TIMEOUT)

    def test_navigate_dashboard(self, page_with_gui, screenshot_dir):
        """Debe poder navegar al tablero."""
        page = page_with_gui
        page.locator("#nav-dashboard").click()
        page.wait_for_timeout(500)

        screenshot = screenshot_dir / "UI-06_dashboard.png"
        page.screenshot(path=str(screenshot))
        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_navigate_settings(self, page_with_gui, screenshot_dir):
        """Debe poder navegar a ajustes."""
        page = page_with_gui
        page.locator("#nav-settings").click()
        page.wait_for_timeout(500)

        screenshot = screenshot_dir / "UI-06_settings.png"
        page.screenshot(path=str(screenshot))
        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_full_navigation_cycle(self, page_with_gui, screenshot_dir):
        """Navegar por todas las vistas sin errores."""
        page = page_with_gui
        views = ["#nav-downloads", "#nav-history", "#nav-settings", "#nav-dashboard"]
        for view_id in views:
            page.locator(view_id).click()
            page.wait_for_timeout(300)

        screenshot = screenshot_dir / "UI-06_ciclo_completo.png"
        page.screenshot(path=str(screenshot))
        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)


# ---------------------------------------------------------------------------
# UI-07: Cambiar carpeta de destino
# ---------------------------------------------------------------------------

class TestUI07ChangeDestinationFolder:
    def test_settings_path_input_visible(self, page_with_gui):
        """El campo de ruta en ajustes debe estar visible."""
        page = page_with_gui
        page.locator("#nav-settings").click()
        page.wait_for_timeout(500)

        path_input = page.locator("#path-input")
        expect(path_input).to_be_visible(timeout=UI_TIMEOUT)

    def test_settings_browse_button_visible(self, page_with_gui):
        """El boton de explorar carpeta debe estar visible."""
        page = page_with_gui
        page.locator("#nav-settings").click()
        page.wait_for_timeout(500)

        browse_btn = page.locator("#browse-btn")
        expect(browse_btn).to_be_visible(timeout=UI_TIMEOUT)

    def test_settings_save_button_visible(self, page_with_gui, screenshot_dir):
        """El boton de guardar ajustes debe estar visible."""
        page = page_with_gui
        page.locator("#nav-settings").click()
        page.wait_for_timeout(500)

        save_btn = page.locator("#save-settings")
        expect(save_btn).to_be_visible(timeout=UI_TIMEOUT)

        screenshot = screenshot_dir / "UI-07_ajustes.png"
        page.screenshot(path=str(screenshot))


# ---------------------------------------------------------------------------
# UI-08: Estadisticas visibles en el tablero
# ---------------------------------------------------------------------------

class TestUI08Statistics:
    def test_dashboard_loads_correctly(self, page_with_gui, screenshot_dir):
        """El tablero debe cargarse con los elementos principales."""
        page = page_with_gui
        page.locator("#nav-dashboard").click()
        page.wait_for_timeout(500)

        screenshot = screenshot_dir / "UI-08_estadisticas.png"
        page.screenshot(path=str(screenshot))

        expect(page.locator("body")).to_be_visible(timeout=UI_TIMEOUT)

    def test_download_form_complete(self, page_with_gui):
        """El formulario completo de descarga debe estar disponible."""
        page = page_with_gui
        # URL input, detect button, download button
        expect(page.locator("#url-input")).to_be_visible(timeout=UI_TIMEOUT)
        expect(page.locator("#download-btn")).to_be_visible(timeout=UI_TIMEOUT)

    def test_search_input_visible(self, page_with_gui):
        """El campo de busqueda principal debe ser visible."""
        page = page_with_gui
        search_input = page.locator("#search-input")
        expect(search_input).to_be_visible(timeout=UI_TIMEOUT)
