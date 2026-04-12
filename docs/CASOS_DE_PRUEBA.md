# Diseno de Casos de Prueba - DownLoader Pro

**Version:** 1.0 | **Fecha:** Abril 2026 | **Equipo:** [NOMBRE DEL EQUIPO]

---

## Pruebas Unitarias

### CP-U-01: Validacion de URL valida e invalida

**Modulo:** `src/utils/validators.py` — `is_valid_url()`
**Objetivo:** Verificar que la funcion distingue correctamente URLs validas de invalidas.

| Datos de prueba | Resultado esperado |
|---|---|
| `"https://example.com/archivo.zip"` | `True` |
| `"http://example.com"` | `True` |
| `"esto-no-es-url"` | `False` |
| `""` | `False` |
| `None` | `False` |
| `"ftp://servidor.com"` | `False` |

#### Matriz de Decision CP-U-01

| Condicion / Regla | R1 (Correcto) | R2 (Incorrecto) | R3 | R4 |
|---|:---:|:---:|:---:|:---:|
| C1: URL tiene esquema http/https | SI | NO | SI | NO |
| C2: URL tiene host/dominio valido | SI | SI | NO | NO |
| **A1: Retorna True** | **X** | | | |
| **A2: Retorna False** | | **X** | **X** | **X** |

**Prueba automatizada:** `tests/test_validators.py::TestIsValidUrl`

---

### CP-U-02: Sanitizacion de nombre de archivo

**Modulo:** `src/utils/validators.py` — `sanitize_filename()`
**Objetivo:** Verificar que los caracteres invalidos son reemplazados y el nombre queda usable.

| Datos de prueba | Resultado esperado |
|---|---|
| `"archivo_normal.mp4"` | `"archivo_normal.mp4"` (sin cambios) |
| `'archivo<>:".txt'` | `"archivo____.txt"` |
| `""` | `"download"` |
| `"a" * 250 + ".txt"` | Nombre truncado a <= 200 chars |

#### Matriz de Decision CP-U-02

| Condicion / Regla | R1 (Correcto) | R2 (Incorrecto A) | R3 (Incorrecto B) |
|---|:---:|:---:|:---:|
| C1: Nombre contiene solo caracteres validos | SI | NO | N/A |
| C2: Nombre esta vacio o es solo puntos | NO | NO | SI |
| C3: Nombre supera 200 caracteres | NO | NO | NO |
| **A1: Retorna nombre sin modificar** | **X** | | |
| **A2: Reemplaza caracteres invalidos** | | **X** | |
| **A3: Retorna "download"** | | | **X** |

**Prueba automatizada:** `tests/test_validators.py::TestSanitizeFilename`

---

### CP-U-03: Formateo de tamano en bytes

**Modulo:** `src/utils/helpers.py` — `format_bytes()`
**Objetivo:** Verificar la conversion correcta de bytes a unidades legibles (B, KB, MB, GB).

| Datos de prueba | Resultado esperado |
|---|---|
| `0` | `"0 B"` |
| `-100` | `"0 B"` |
| `500` | `"500 B"` |
| `1024` | contiene `"KB"` |
| `1048576` | contiene `"MB"` |
| `1073741824` | contiene `"GB"` |

#### Matriz de Decision CP-U-03

| Condicion / Regla | R1 (Correcto) | R2 | R3 | R4 (Incorrecto) |
|---|:---:|:---:|:---:|:---:|
| C1: Valor entre 1 y 1023 (Bytes) | SI | NO | NO | NO |
| C2: Valor entre 1024 y 1048575 (KB) | NO | SI | NO | NO |
| C3: Valor >= 1048576 (MB+) | NO | NO | SI | NO |
| C4: Valor <= 0 (invalido) | NO | NO | NO | SI |
| **A1: Retorna "X B"** | **X** | | | |
| **A2: Retorna "X.XX KB"** | | **X** | | |
| **A3: Retorna "X.XX MB" o mayor** | | | **X** | |
| **A4: Retorna "0 B"** | | | | **X** |

**Prueba automatizada:** `tests/test_helpers.py::TestFormatBytes`

---

## Pruebas UI

### CP-UI-01: Carga correcta de la pagina principal

**Herramienta:** Playwright | **URL:** `http://localhost:5001/`
**Objetivo:** Verificar que la pagina web carga con el titulo y estructura correcta.

**Pasos:**
1. Navegar a `http://localhost:5001/`
2. Verificar titulo del documento
3. Verificar visibilidad del encabezado `#app-title`

#### Matriz de Decision CP-UI-01

| Condicion / Regla | R1 (Correcto) | R2 (Incorrecto) |
|---|:---:|:---:|
| C1: Servidor disponible en puerto 5001 | SI | NO |
| C2: HTML se renderiza correctamente | SI | N/A |
| **A1: Titulo correcto, encabezado visible** | **X** | |
| **A2: Error de conexion o timeout** | | **X** |

**Prueba automatizada:** `test_page_loads_correctly`, `test_app_title_visible`

---

### CP-UI-02: Validacion de URL valida en la interfaz

**Herramienta:** Playwright
**Objetivo:** Verificar que el formulario procesa una URL valida y muestra el resultado correcto.

**Pasos:**
1. Navegar a `http://localhost:5001/`
2. Ingresar `"https://example.com/archivo.zip"` en `#url-input`
3. Hacer clic en `#validate-btn`
4. Verificar que `#validation-result` contiene "URL valida"

#### Matriz de Decision CP-UI-02

| Condicion / Regla | R1 (Correcto) | R2 (Incorrecto) |
|---|:---:|:---:|
| C1: Entrada tiene formato URL valido | SI | NO |
| C2: API `/api/validate-url` responde 200 | SI | SI |
| **A1: Muestra "URL valida"** | **X** | |
| **A2: Muestra "URL invalida"** | | **X** |

**Prueba automatizada:** `test_valid_url_shows_success_message`, `test_invalid_url_shows_error_message`

---

### CP-UI-03: Carga asincrona de estadisticas

**Herramienta:** Playwright
**Objetivo:** Verificar que la seccion de estadisticas se actualiza automaticamente al cargar la pagina.

**Pasos:**
1. Navegar a `http://localhost:5001/`
2. Esperar estado `networkidle` (fetches JS completados)
3. Verificar que `#stats-content` contiene "Total:"

#### Matriz de Decision CP-UI-03

| Condicion / Regla | R1 (Correcto) | R2 (Incorrecto) |
|---|:---:|:---:|
| C1: API `/api/stats` responde con 200 | SI | NO |
| C2: JavaScript procesa la respuesta JSON | SI | N/A |
| **A1: Muestra estadisticas con "Total:"** | **X** | |
| **A2: Muestra "Error cargando estadisticas"** | | **X** |

**Prueba automatizada:** `test_stats_section_loads_with_data`
