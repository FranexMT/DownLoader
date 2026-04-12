# Plan de Pruebas del Sistema DownLoader Pro

**Version:** 1.0 | **Fecha:** Abril 2026 | **Estandar:** ISO/IEC 29119-3
**Equipo:** [NOMBRE DEL EQUIPO]

---

## 1. Introduccion

Este documento define el plan de pruebas de **DownLoader Pro**, un gestor de descargas con soporte multihilo, historial SQLite, interfaz web y descarga de redes sociales. Sigue la estructura del estandar ISO/IEC 29119-3.

### 1.1 Integrantes

| Nombre completo | Rol |
|---|---|
| [Integrante 1] | Lider / Pruebas unitarias |
| [Integrante 2] | Pruebas de API |
| [Integrante 3] | Pruebas UI / Playwright |
| [Integrante 4] | CI/CD |
| [Integrante 5] | Documentacion y evidencias |

---

## 2. Objetivos de Prueba

- **OP-01:** Verificar que `is_valid_url()` distingue correctamente URLs validas e invalidas.
- **OP-02:** Verificar que `format_bytes()` produce salidas correctas en todas las unidades.
- **OP-03:** Validar que las operaciones CRUD de `Database` funcionan de forma aislada.
- **OP-04:** Validar que `ChunkManager` crea, fusiona y limpia fragmentos correctamente.
- **OP-05:** Verificar que la API REST responde con codigos HTTP y JSON correctos.
- **OP-06:** Verificar que la interfaz web responde a interacciones del usuario.
- **OP-07:** Lograr cobertura minima del 70% en pruebas unitarias.

---

## 3. Alcance

### 3.1 En alcance

| Modulo | Ruta | Tipo de prueba |
|---|---|---|
| Validadores de URL | `src/utils/validators.py` | Unitaria |
| Funciones de formato | `src/utils/helpers.py` | Unitaria |
| Base de datos SQLite | `src/core/database.py` | Unitaria |
| Motor de descarga | `src/core/downloader.py` | Unitaria |
| Gestion de fragmentos | `src/core/chunk_manager.py` | Unitaria |
| API REST Flask | `tests/api/server.py` | API (Newman) |
| Interfaz web | Servida por Flask en puerto 5001 | UI (Playwright) |

### 3.2 Fuera de alcance

- Descarga real de archivos (requiere red externa).
- Integracion con YouTube, Instagram, etc.
- Pruebas de rendimiento y carga.
- Interfaz de escritorio (CustomTkinter).

---

## 4. Estrategia de Pruebas

### 4.1 Pruebas Unitarias

**Herramienta:** pytest + pytest-cov
**Criterio de exito:** >= 70% cobertura; 0 pruebas fallidas
**Aislamiento:** `tmp_path` para sistema de archivos; `unittest.mock.patch` para dependencias

### 4.2 Pruebas de API

**Herramienta:** Postman / Newman
**Servidor:** Flask en `http://localhost:5001`
**Coleccion:** `tests/api/DownLoader-API.postman_collection.json`

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `/api/stats` | GET | Estadisticas del sistema |
| `/api/downloads` | GET | Lista de descargas |
| `/api/validate-url` | POST | Validacion de URL |
| `/api/config` | GET | Configuracion del sistema |

### 4.3 Pruebas UI

**Herramienta:** Playwright (pytest-playwright)
**URL:** `http://localhost:5001/`
**Casos:** 6 (minimo requerido: 5)

| ID | Caso de prueba |
|---|---|
| CP-UI-01 | Pagina carga con titulo correcto |
| CP-UI-02 | Encabezado principal visible |
| CP-UI-03 | Formulario tiene todos sus elementos |
| CP-UI-04 | URL valida muestra mensaje de exito |
| CP-UI-05 | URL invalida muestra mensaje de error |
| CP-UI-06 | Seccion de estadisticas carga con datos |

---

## 5. Entorno de Pruebas

### CI/CD (GitHub Actions)

| Componente | Valor |
|---|---|
| OS | ubuntu-latest |
| Python | 3.12 |
| Node.js | 18 (Newman) |
| Navegador | Chromium headless (Playwright) |
| BD de pruebas | SQLite en directorio temporal |

### Local

```bash
pip install -r requirements.txt -r requirements-test.txt
playwright install chromium
```

---

## 6. Criterios de Entrada y Salida

### Entrada
- Codigo fuente disponible en el repositorio.
- Dependencias instaladas.
- Servidor Flask inicia sin errores.
- Archivos de Postman existen en `tests/api/`.

### Salida — PASS
- Todas las pruebas unitarias pasan (0 failures).
- Cobertura >= 70%.
- Todos los assertions de Newman pasan.
- Los 6 casos UI pasan.
- 4 artefactos disponibles en GitHub (coverage, unit, api, ui).

### Salida — FAIL
- Una o mas pruebas unitarias fallan.
- Cobertura < 70%.
- Un assertion de API falla.
- Un caso UI falla.

---

## 7. Roles y Responsabilidades

| Rol | Responsabilidad | Asignado a |
|---|---|---|
| Lider de pruebas | Coordinar el proceso | [Integrante 1] |
| Tester unitario | `tests/test_*.py` | [Integrante 1] |
| Tester de API | Coleccion Postman + servidor Flask | [Integrante 2] |
| Tester UI | `tests/ui/test_gui.py` | [Integrante 3] |
| DevOps | Pipeline `.github/workflows/` | [Integrante 4] |
| Documentador | Reporte de evidencias | [Integrante 5] |

---

## 8. Riesgos

| ID | Riesgo | Prob. | Impacto | Mitigacion |
|---|---|---|---|---|
| R-01 | Dependencias no disponibles en CI | Media | Alta | Versiones fijas; ubuntu-latest |
| R-02 | Servidor Flask no inicia a tiempo | Baja | Alta | `sleep 3` + verificacion con `curl` |
| R-03 | Pruebas UI fallan por timing asincrono | Media | Media | `networkidle` + retry de Playwright |
| R-04 | Cobertura < 70% | Baja | Media | Tests para todos los modulos principales |
| R-05 | Codigo cambia sin actualizar pruebas | Alta | Alta | Code review obligatorio antes de merge |

---

## 9. Entregables

| Entregable | Ubicacion |
|---|---|
| Plan de Pruebas | `docs/PLAN_DE_PRUEBAS.md` |
| Casos de Prueba | `docs/CASOS_DE_PRUEBA.md` |
| Pruebas unitarias | `tests/test_*.py` |
| Pruebas API | `tests/api/` |
| Pruebas UI | `tests/ui/test_gui.py` |
| Pipeline CI/CD | `.github/workflows/test-pipeline.yml` |
| Reporte HTML unitario | Artefacto GitHub: `unit-test-report` |
| Reporte coverage | Artefacto GitHub: `coverage-report` |
| Reporte HTML API | Artefacto GitHub: `api-test-report` |
| Reporte HTML UI | Artefacto GitHub: `ui-test-report` |
| Evidencias | `docs/EVIDENCIAS_TEMPLATE.md` |

---

## 10. Cronograma

| Fase | Actividad | Fecha |
|---|---|---|
| 1 | Registro del proyecto | Semana 1 |
| 2 | Plan de Pruebas | Semana 2 |
| 3 | Diseno de casos y matrices | Semana 3 |
| 4 | Pruebas unitarias | Semana 4 |
| 5 | Pruebas de API | Semana 4-5 |
| 6 | Pruebas UI | Semana 5 |
| 7 | Pipeline CI/CD | Semana 5-6 |
| 8 | Evidencias y reporte | Semana 6 |
| **Entrega** | **Entrega del proyecto** | **12 Abril 2026** |
| **Presentacion** | **Presentacion al grupo** | **13-14 Abril 2026** |
