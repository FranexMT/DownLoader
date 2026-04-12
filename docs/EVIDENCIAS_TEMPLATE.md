# Reporte de Evidencias - DownLoader Pro

**Equipo:** [NOMBRE DEL EQUIPO]
**Integrantes:** [Listar nombres completos]
**Fecha de entrega:** 12 de Abril 2026

---

## 1. Resumen en GitHub Actions

> Insertar captura de la vista principal de GitHub Actions mostrando los 3 jobs:
> - Pruebas Unitarias (pytest) - VERDE
> - Pruebas de API (Postman/Newman) - VERDE
> - Pruebas UI (Playwright) - VERDE

*[INSERTAR CAPTURA AQUI]*

---

## 2. Pruebas Unitarias

### 2.1 Ejecucion en terminal (pytest)
> Insertar captura del log de GitHub Actions — job "Pruebas Unitarias"

*[INSERTAR CAPTURA AQUI]*

### 2.2 Reporte de cobertura (htmlcov)
> Insertar captura del artefacto `coverage-report` mostrando porcentaje >= 70%

*[INSERTAR CAPTURA AQUI]*

### 2.3 Reporte HTML de pytest
> Insertar captura del artefacto `unit-test-report`

*[INSERTAR CAPTURA AQUI]*

### 2.4 Justificacion de cada prueba automatizada

| Prueba | Funcion probada | Por que se automatizo |
|---|---|---|
| `test_valid_http_url` | `is_valid_url()` | Funcion critica: si falla, ninguna descarga inicia. Automatizar previene regresiones. |
| `test_invalid_no_scheme` | `is_valid_url()` | Cubre el caso negativo principal; sin esto, URLs malformadas pasarian al motor. |
| `test_removes_invalid_chars` | `sanitize_filename()` | Evita errores de sistema de archivos en cada descarga. |
| `test_empty_becomes_download` | `sanitize_filename()` | Caso borde critico; sin fallback la app podria crashear. |
| `test_kilobytes` | `format_bytes()` | La conversion KB es la mas frecuente en la UI; rapido de automatizar. |
| `test_create_download_returns_id` | `Database.create_download()` | La persistencia es fundamental; errores silenciosos sin prueba son peligrosos. |
| `test_update_status` | `Database.update_download()` | El cambio de estado es la operacion mas frecuente en el ciclo de descarga. |
| `test_merge_multiple_chunks` | `ChunkManager.merge_chunks()` | La fusion incorrecta corrompe archivos; debe probarse siempre. |
| `test_pause_requires_downloading_status` | `DownloadTask.pause()` | La logica de estados es compleja; automatizar previene regresiones de control de flujo. |

---

## 3. Pruebas de API

### 3.1 Ejecucion de Newman en GitHub
> Insertar captura del log del job "Pruebas de API"

*[INSERTAR CAPTURA AQUI]*

### 3.2 Reporte HTML de API (htmlextra)
> Insertar captura del artefacto `api-test-report`

*[INSERTAR CAPTURA AQUI]*

### 3.3 Justificacion de las pruebas de API

| Endpoint | Assertion | Por que se automatizo |
|---|---|---|
| `GET /api/stats` — Status 200 | Verifica que el servidor responde | Prueba de disponibilidad basica; falla si el servidor no arranca. |
| `GET /api/stats` — tiene campo `total` | Valida el contrato JSON | Sin esto, cambios en el formato JSON romperian la UI silenciosamente. |
| `GET /api/downloads` — tiene array `downloads` | Valida estructura de la respuesta | Garantiza que el cliente puede iterar la lista sin errores. |
| `POST /api/validate-url` valida — `valid=true` | Prueba el camino feliz | Es la operacion que mas ejecuta el usuario antes de descargar. |
| `POST /api/validate-url` invalida — `valid=false` | Prueba el rechazo de entrada | Evita que URLs malas inicien descargas que fallaran. |

---

## 4. Pruebas UI

### 4.1 Ejecucion de Playwright en GitHub
> Insertar captura del log del job "Pruebas UI"

*[INSERTAR CAPTURA AQUI]*

### 4.2 Reporte HTML de UI
> Insertar captura del artefacto `ui-test-report`

*[INSERTAR CAPTURA AQUI]*

### 4.3 Justificacion de las pruebas UI

| Prueba | Elemento probado | Por que se automatizo |
|---|---|---|
| `test_page_loads_correctly` | Titulo de la pagina | Detecta inmediatamente si el servidor falla o sirve contenido incorrecto. |
| `test_app_title_visible` | Encabezado `#app-title` | Verifica la integridad basica del DOM; detecta cambios HTML accidentales. |
| `test_url_form_elements_exist` | Input + Boton + Resultado | Todos los elementos del formulario deben existir para que la funcion principal opere. |
| `test_valid_url_shows_success_message` | Flujo completo validacion OK | Prueba la integracion JS → API → DOM; la mas importante para el usuario final. |
| `test_invalid_url_shows_error_message` | Flujo de rechazo de URL | Verifica que el sistema informa errores al usuario (UX critico). |
| `test_stats_section_loads_with_data` | Carga asincrona de datos | Verifica que los fetch JS funcionan y el DOM se actualiza correctamente. |

---

## 5. Video de Falla Intencional

**Falla introducida:** [Describir que linea se modifico]
**Archivo modificado:** [Ej: `src/utils/validators.py`]
**Cambio realizado:** [Ej: Cambiar `return all([...])` por `return False`]

**Pasos grabados en el video:**
1. Modificar el codigo para introducir la falla → commit → push.
2. Mostrar el job "Pruebas Unitarias" en ROJO en GitHub Actions.
3. Restaurar el codigo correcto → commit → push.
4. Mostrar todos los jobs en VERDE en GitHub Actions.

**Enlace al video:** [URL del video]

---

## 6. Artefactos en GitHub

> Insertar captura de la seccion de Artifacts en un run de GitHub Actions mostrando:
> - coverage-report
> - unit-test-report
> - api-test-report
> - ui-test-report

*[INSERTAR CAPTURA AQUI]*

---

## 7. Conclusiones

[Redactar 1-2 parrafos describiendo:
- Resultados generales obtenidos.
- Dificultades encontradas y como se resolvieron.
- Lecciones aprendidas sobre pruebas automatizadas.]
