# LEER IMPORTANTE - Plan de Pruebas DownLoader Pro

> **Este documento describe el plan completo de pruebas automatizadas para el sistema DownLoader Pro v2.1.0, basado en ISO/IEC 29119.**

---

## RESUMEN EJECUTIVO

| Aspecto | Detalle |
|---------|---------|
| Sistema bajo prueba | DownLoader Pro v2.1.0 |
| Estándar seguido | ISO/IEC 29119 |
| Pruebas unitarias | pytest (4+ funciones) |
| Pruebas de API | Flask REST API + Postman (2+ endpoints, 3+ tests) |
| Pruebas UI | Playwright + Eel (5+ casos) |
| CI/CD | GitHub Actions |
| Lenguaje principal | Python 3.8+ / JavaScript ES6+ |

---

## 1. INTRODUCCION

### 1.1 Proposito del Plan
Este documento establece el plan formal de pruebas para el sistema **DownLoader Pro**, un gestor de descargas avanzado con aceleracion y soporte para redes sociales. El plan define la estrategia, alcance, recursos y cronograma necesarios para verificar que el sistema cumple con los requisitos funcionales y de calidad establecidos.

### 1.2 Alcance General
El plan cubre las siguientes areas del sistema:
- Motor de descargas (multithreading, pause/resume, throttling)
- Gestion de fragmentos y resume automatico
- Base de datos SQLite (persistencia, estadisticas)
- Interfaz web GUI (Eel + HTML/JS/CSS)
- API REST (Flask para pruebas de integracion)
- Validadores y utilidades

### 1.3 Referencias Normativas
- ISO/IEC 29119 - Software Testing
- ISO/IEC/IEEE 29119-3 - Test Design
- ISO/IEC/IEEE 29119-4 - Test Execution

---

## 2. OBJETIVOS DE PRUEBA

| Objetivo | Descripcion | Criterio de exito |
|----------|-------------|-------------------|
| OF-01 | Verificar la correcta validacion de URLs | 100% de URLs invalidas rechazadas |
| OF-02 | Verificar la sanitizacion de nombres de archivo | Ningun caracter invalido en nombres |
| OF-03 | Verificar el calculo de checksum (MD5/SHA256) | Hash coincide con esperado |
| OF-04 | Verificar el calculo de ETA | Formato y valores correctos |
| OF-05 | Verificar pause/resume de descargas | Estado transiciona correctamente |
| OF-06 | Verificar la interfaz GUI | Elementos visibles y funcionales |
| OF-07 | Verificar endpoints de API REST | Codigos de estado y respuestas correctas |
| OF-08 | Verificar persistencia en base de datos | Datos guardados y recuperables |
| OF-09 | Ejecutar pipeline CI/CD exitosamente | Todos los jobs completan sin errores |

---

## 3. ALCANCE

### 3.1 Funciones a probar (IN scope)

| Modulo | Funciones/Componentes |
|--------|----------------------|
| **validators.py** | is_valid_url, sanitize_filename, verify_checksum, extract_filename_from_url, is_supported_url |
| **helpers.py** | format_bytes, calculate_eta, format_speed, get_file_icon, check_ffmpeg |
| **downloader.py** | DownloadTask, Downloader.create_task, pause_task, resume_task, cancel_task |
| **database.py** | create_download, update_download, get_download, delete_download, get_statistics |
| **GUI (Eel)** | Agregar descarga, pausar, reanudar, eliminar, cambiar carpeta |
| **API REST** | CRUD de descargas, pause/resume, estadisticas |

### 3.2 Funciones NO probadas (OUT of scope)

| Razon de exclusion |
|-------------------|
| Descargas reales de archivos (requiere red externa) |
| Integracion con yt-dlp (redes sociales reales) |
| Notificaciones nativas del SO |
| System tray |
| CLI interactiva |
| Construccion de ejecutables (.exe) |

---

## 4. ESTRATEGIA DE PRUEBAS

### 4.1 Pruebas Unitarias

**Herramienta:** pytest >= 7.4.0
**Framework adicional:** pytest-cov >= 4.1.0 (coverage minimo 80%)

**Funciones bajo prueba disenadas (minimo 4):**

| ID | Funcion | Descripcion | Flujo Correcto | Flujo Incorrecto |
|----|---------|-------------|---------------|------------------|
| TU-01 | `is_valid_url()` | Valida formato de URL | https://ejemplo.com -> True | ftp://ejemplo.com -> False |
| TU-02 | `sanitize_filename()` | Limpia caracteres invalidos | file<>.txt -> file__.txt | "" -> "download" |
| TU-03 | `verify_checksum()` | Verifica integridad de archivo | Hash correcto -> True | Hash incorrecto -> False |
| TU-04 | `calculate_eta()` | Calcula tiempo restante | 100 bytes, 10B/s -> "10s" | Speed=0 -> "--:--" |

**Archivos de prueba:**
```
tests/
  test_validators.py    # Expandido (ya existe)
  test_helpers.py       # Expandido (ya existe)
  test_downloader.py    # Nueva
  test_database.py     # Expandido (ya existe)
  conftest.py          # Fixtures compartidos
```

**Justificacion de automatizacion:**
- Funciones de validacion son core del sistema
- Ejecucion rapida (<1s por test)
- Resultados deterministicos y reproducibles
- Alto ROI: deteccion temprana de regresiones

### 4.2 Pruebas de API

**Herramienta:** Flask + Postman (newman CLI)
**Endpoints implementados:**

| Metodo | Endpoint | Descripcion | Pruebas |
|--------|----------|-------------|---------|
| POST | `/api/downloads` | Crear descarga | Status 201, ID retornado, URL valida |
| GET | `/api/downloads` | Listar descargas | Status 200, array, paginacion |
| GET | `/api/downloads/{id}` | Detalle de descarga | Status 200, campos completos |
| POST | `/api/downloads/{id}/pause` | Pausar descarga | Status 200, estado PAUSED |
| POST | `/api/downloads/{id}/resume` | Reanudar descarga | Status 200, estado DOWNLOADING |
| DELETE | `/api/downloads/{id}` | Eliminar descarga | Status 200, confirmacion |
| GET | `/api/stats` | Estadisticas | Status 200, campos numericos |
| POST | `/api/validate` | Validar URL | Status 200, resultado booleano |

**Archivos:**
```
tests/api/
  DownLoader-API.postman_collection.json
  DownLoader-API.postman_environment.json
  server.py  # Flask API minimal
```

**Justificacion de automatizacion:**
- API es punto de integracion critico
- Tests ejecutables en CI/CD automaticamente
- Coleccion reusable para QA manual
- Coverage de casos de borde (edge cases)

### 4.3 Pruebas de UI

**Herramienta:** Playwright >= 1.40.0
**Navegador:** Chromium (headless, en CI)
**Servidor:** Eel en puerto 8000 (localhost)

**Casos disenados (minimo 5):**

| ID | Escenario | Precondicion | Paso | Resultado Esperado (Correcto) | Resultado Incorrecto |
|----|-----------|--------------|------|-------------------------------|---------------------|
| UI-01 | Agregar descarga por URL | GUI iniciada | Ingresar URL valida y enviar | Descarga aparece en cola | Error de validacion visible |
| UI-02 | Error con URL invalida | GUI iniciada | Ingresar "noesunaurl" y enviar | Mensaje de error mostrado | Sin mensaje (bug) |
| UI-03 | Pausar descarga | Descarga en curso | Click en boton pausar | Estado cambia a PAUSED | Estado no cambia |
| UI-04 | Reanudar descarga | Descarga pausada | Click en boton reanudar | Estado cambia a DOWNLOADING | Error silencioso |
| UI-05 | Eliminar descarga | Descarga en cola | Click en eliminar | Descarga removida de lista | Todavia visible |

**Casos adicionales (para coverage):**

| ID | Escenario |
|----|-----------|
| UI-06 | Navegacion entre vistas (Cola, Panel, Historial, Ajustes) |
| UI-07 | Cambiar carpeta de destino |
| UI-08 | Verificar que estadisticas se actualizan |

**Archivos:**
```
tests/ui/
  test_gui.py           # Casos de prueba Playwright
  conftest.py          # Configuracion y fixtures
  playwright.config.py # Configuracion general
```

**Justificacion de automatizacion:**
- UI es la interfaz principal para usuarios finales
- Pruebas manuales repetitivas son costosas
- Detecta regresiones visuales y funcionales
- Screenshots automaticos como evidencia

---

## 5. ENTORNO DE PRUEBAS

### 5.1 Requisitos de Software

| Componente | Version minima | Proposito |
|------------|---------------|-----------|
| Python | 3.8+ | Runtime principal |
| Node.js | 16+ | Playwright CLI |
| Chrome/Chromium | Latest | Navegador para UI |
| Git | 2.30+ | Control de versiones |
| pip | 23.0+ | Gestion de paquetes Python |

### 5.2 Dependencias Python (requirements-test.txt)

```
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-html>=4.0
pytest-xdist>=3.3  # Ejecucion paralela

# API
flask>=3.0.0
flask-cors>=4.0

# UI
playwright>=1.40.0

# Coverage
coverage>=7.3
```

### 5.3 Estructura de Directorios en CI

```
$RUNNER_TEMP/
  downloader-tests/
    tests/           # Codigo fuente de pruebas
    .venv/          # Virtual environment
    htmlcov/        # Reporte coverage
    test-results/   # Resultados JUnit
    ui-report/      # Screenshots y reportes UI
    api-report/     # Reportes Postman
```

### 5.4 Configuracion de Base de Datos para Pruebas

- Usar base de datos temporal en memoria o archivo temporal
- Tablas creadas automaticamente por el codigo
- Datos de prueba insertados por fixtures
- Limpieza automatica al finalizar cada test

---

## 6. CRITERIOS DE ENTRADA Y SALIDA

### 6.1 Criterios de Entrada

| Fase | Criterio | Evidencia |
|------|----------|----------|
| Unitarias | Codigo fuente en repositorio, dependencias instaladas | requirements-test.txt |
| API | Flask server funcional, endpoints definidos | tests/api/server.py |
| UI | GUI funciona localmente, Playwright instalado | tests/ui/test_gui.py |
| CI/CD | Pipeline configurado, runners disponibles | .github/workflows/test-pipeline.yml |
| Evidencias | Todas las pruebas ejecutadas al menos 1 vez | Reportes generados |

### 6.2 Criterios de Salida

| Fase | Criterio | Metrica minima |
|------|----------|----------------|
| Unitarias | Todos los tests pasan, coverage >= 80% | 100% pass rate |
| API | Todos los endpoints probados, respuestas correctas | 100% pass rate |
| UI | Todos los casos ejecutados, screenshots generados | 100% pass rate |
| Pipeline | Jobs completan exitosamente | 100% pass rate |
| Documentacion | Plan, matrices y evidencias completos | 100% documentos |

### 6.3 Condiciones de Suspension

- Si coverage unitario < 60%, suspender y reporta coverage gaps
- Si API server falla mas de 3 veces, pausar y depurar servidor
- Si UI tests fallan > 30%, verificar compatibilidad de navegador
- Si pipeline falla por infrastructure, reportar a DevOps

---

## 7. ROLES Y RESPONSABILIDADES

| Rol | Responsabilidad | Persona |
|-----|-----------------|---------|
| Test Manager | Propietario del plan, coordina fases | Equipo |
| QA Engineer | Disena y ejecuta casos de prueba | Equipo |
| Developer | Implementa fixes basados en bugs encontrados | Equipo |
| DevOps | Mantiene pipeline CI/CD | Equipo |
| Reviewer | Evalua calidad de pruebas (Codex) | AI (Codex) |

### Responsabilidades por fase:

| Fase | Responsable primario | Secundario |
|------|--------------------|-----------|
| Plan documentado | Todos | Test Manager |
| Pruebas unitarias | Developer | QA |
| Pruebas API | QA | Developer |
| Pruebas UI | QA | Developer |
| Pipeline CI/CD | DevOps | Todos |
| Evidencias | Test Manager | Todos |

---

## 8. RIESGOS

| ID | Riesgo | Probabilidad | Impacto | Mitigacion |
|----|--------|-------------|---------|------------|
| R-01 | Cambios frecuentes en codigo fuente | Media | Alta | Re-ejecutar suite completa en cada merge |
| R-02 | Incompatibilidad de versiones de dependencias | Baja | Alta | Fijar versiones en requirements.txt |
| R-03 | Recursos de CI/CD limitados | Media | Media | Optimizar tiempo de ejecucion, cachear dependencias |
| R-04 | Fallos por dependencias de red externas | Baja | Media | Usar mocks para llamadas HTTP externas |
| R-05 | Cambios en GUI que rompen selectores | Alta | Alta | Usar selectores robustos, actualizarlos frecuentemente |
| R-06 | Datos de prueba contaminantes entre tests | Media | Media | Limpiar estado en cada test (fixtures) |
| R-07 | Tiempo insuficiente para completar | Media | Alta | Priorizar pruebas criticas, deferir opcional |

---

## 9. ENTREGABLES

| # | Entregable | Formato | Ubicacion | Estado |
|---|------------|---------|-----------|--------|
| 1 | Plan de Pruebas | Markdown/PDF | docs/PLAN_DE_PRUEBAS.md | [X] Planificado |
| 2 | Matrices de Decision | Markdown | docs/MATRICES_DE_DECISION.md | [ ] Pendiente |
| 3 | Pruebas Unitarias | Python/pytest | tests/*.py | [ ] Pendiente |
| 4 | Coleccion Postman | JSON | tests/api/*.json | [ ] Pendiente |
| 5 | Pruebas Playwright | Python | tests/ui/test_gui.py | [ ] Pendiente |
| 6 | Pipeline CI/CD | YAML | .github/workflows/*.yml | [ ] Pendiente |
| 7 | Reporte de Ejecucion | HTML | test-results/ | [ ] Pendiente |
| 8 | Evidencias Visuales | Screenshots | test-results/screenshots/ | [ ] Pendiente |
| 9 | Video de Falla Intencional | MP4 | videos/ | [ ] Pendiente |
| 10 | Presentacion Final | PDF/PPTX | docs/presentacion/ | [ ] Pendiente |

---

## 10. CRONOGRAMA

### 10.1 Timeline General (4 semanas)

```
Semana 1: Documentacion + API Flask + Matrices
Semana 2: Pruebas Unitarias + Coleccion Postman
Semana 3: Playwright UI + Pipeline CI/CD
Semana 4: Evidencias + Video + Presentacion
```

### 10.2 Detalle por Semana

| Semana | Dias | Actividades |
|--------|------|------------|
| **1** | 1-2 | Crear documento PLAN_DE_PRUEBAS.md |
| | 3-4 | Implementar API Flask minima en tests/api/server.py |
| | 5 | Crear Matrices de Decision en docs/MATRICES_DE_DECISION.md |
| **2** | 6-8 | Expandir pruebas unitarias (4+ funciones) |
| | 9-10 | Crear coleccion Postman (2+ endpoints, 3+ tests) |
| **3** | 11-13 | Implementar pruebas UI con Playwright (5+ casos) |
| | 14-15 | Configurar pipeline GitHub Actions |
| | 16 | Verificacion de pipeline completo |
| **4** | 17-18 | Generar reportes HTML de todas las pruebas |
| | 19 | Grabar video de falla intencional |
| | 20 | Preparar presentacion final |

### 10.3 Milestones

| Milestone | Fecha | Criterio de aceptacion |
|-----------|-------|------------------------|
| M1: Plan Completo | Fin Semana 1 | Todos los documentos creados y revisados |
| M2: Unitarias + API | Fin Semana 2 | pytest pass 100%, Postman pass 100% |
| M3: UI + CI/CD | Fin Semana 3 | Playwright pass 100%, pipeline verde |
| M4: Entrega Final | Fin Semana 4 | Video + Presentacion + Reportes |

---

## 11. MATRICES DE DECISION

### 11.1 TU-01: is_valid_url()

```
+------------------------+------------------+------------------+----------+
| Condicion: URL input   | Scheme valido    | Netloc presente | Resultado|
|                        | (http/https)     | (no vacio)      |          |
+------------------------+------------------+------------------+----------+
| "https://example.com"  | Si               | Si               | TRUE     |
| "http://test.com:8080"  | Si               | Si               | TRUE     |
| "ftp://files.com"       | No               | Si               | FALSE    |
| "example.com"           | No (falta)       | No               | FALSE    |
| ""                      | N/A              | N/A              | FALSE    |
| None                    | N/A              | N/A              | FALSE    |
| 12345                   | N/A              | N/A              | FALSE    |
| "https://"              | Si               | No (vacio)       | FALSE    |
+------------------------+------------------+------------------+----------+
```

**Codigo de resultado:**
- TRUE = URL valida para descarga
- FALSE = URL rechazada con mensaje de error

### 11.2 TU-02: sanitize_filename()

```
+---------------------------+--------------------------+------------+
| Condicion: Input          | Caracteres invalidos     | Resultado  |
|                           | presentes                |            |
+---------------------------+--------------------------+------------+
| "video<valid>.mp4"       | < >                      | "video__valid_.mp4" |
| 'file<>:"/\\|?*.txt'      | Todos presentes          | "file____________.txt" |
| "  ..myfile.zip.. "      | Espacios y puntos        | "myfile.zip" |
| "a" * 300 + ".txt"       | Nombre > 200 chars       | Truncado a 200 |
| ""                       | Vacio                    | "download" |
| "..."                    | Solo invalidos           | "download" |
| "normal_file-v1.2.tar.gz"| Ninguno                  | Igual input |
+---------------------------+--------------------------+------------+
```

### 11.3 TU-03: verify_checksum()

```
+---------------------------+--------------------+------------------+----------+
| Condicion: Archivo existe | Hash coincide      | Algoritmo valido | Resultado|
+---------------------------+--------------------+------------------+----------+
| Si                        | Si                 | Si               | TRUE     |
| Si                        | Si                 | No (desconocido) | TRUE*    |
| Si                        | No                  | Si               | FALSE    |
| Si                        | Vacio/None         | -                | TRUE**   |
| No                        | -                  | -                | FALSE    |
+---------------------------+--------------------+------------------+----------+
* Retorna True si algoritmo desconocido (ValueError capturado)
** Retorna True si no hay hash esperado (verificacion saltada)
```

### 11.4 TU-04: calculate_eta()

```
+---------------------------+------------------------+------------------+----------+
| downloaded                | total                  | speed            | Resultado|
+---------------------------+------------------------+------------------+----------+
| 0                         | 100                    | 10.0             | "10s"    |
| 0                         | 600                    | 10.0             | "1:00"   |
| 0                         | 7200                   | 1.0              | "2h 0m"  |
| 0                         | 100                    | 0                | "--:--"  |
| 0                         | 100                    | -5.0 (negativo)  | "--:--"  |
| 100                       | 100                    | 100.0            | "--:--"  |
| 150                       | 100                    | 100.0            | "--:--"  |
| 50                        | 90                     | 1.0              | "0:40"   |
+---------------------------+------------------------+------------------+----------+
```

### 11.5 UI-01: Agregar descarga por URL

```
+---------------------------+------------------------+---------------------------+----------+
| Estado inicial GUI        | URL ingresada          | Accion                    | Resultado|
+---------------------------+------------------------+---------------------------+----------+
| Iniciada, sin descargas   | "https://ejemplo.com/f.zip" | Click en agregar      | Nueva entrada en cola, estado PENDING |
| Iniciada, sin descargas   | "noesunaurl"          | Click en agregar          | Mensaje de error "URL invalida" |
| Iniciada, sin descargas   | "" (vacio)            | Click en agregar          | Mensaje de error "URL requerida" |
| Iniciada, sin descargas   | "ftp://test.com/f.zip"| Click en agregar          | Mensaje de error "Protocolo no soportado" |
+---------------------------+------------------------+---------------------------+----------+
```

### 11.6 UI-03: Pausar descarga activa

```
+---------------------------+------------------------+---------------------------+----------+
| Estado de descarga        | Accion del usuario     | Estado del sistema        | Resultado|
+---------------------------+------------------------+---------------------------+----------+
| DOWNLOADING               | Click en boton pausar  | Estado cambio a PAUSED    | Correcto |
| PENDING                   | Click en boton pausar  | Sin cambio de estado      | Incorrecto|
| PAUSED                    | Click en boton pausar  | Sin cambio (ya pausada)   | N/A      |
| COMPLETED                 | Click en boton pausar  | Sin cambio (ya completa)  | N/A      |
| FAILED                    | Click en boton pausar  | Sin cambio (fallida)      | N/A      |
+---------------------------+------------------------+---------------------------+----------+
```

---

## 12. JUSTIFICACION DE AUTOMATIZACION

### 12.1 Pruebas Unitarias

| Prueba | Justificacion |
|--------|---------------|
| is_valid_url() | Funcion critica usada en cada descarga. Fallos causan descargas invalidas. |
| sanitize_filename() | Seguridad: caracteres invalidos pueden causar errores del SO o vulnerabilidades. |
| verify_checksum() | Garantiza integridad de archivos descargados. Critico para archivos importantes. |
| calculate_eta() | UX: valores incorrectos confunden al usuario. |

**ROI estimado:** 1 hora de automatizacion vs 15+ horas de pruebas manuales por sprint.

### 12.2 Pruebas API

| Prueba | Justificacion |
|--------|---------------|
| CRUD downloads | API es punto de integracion. Fallos rompen todas las integraciones. |
| Pause/Resume | Funcionalidad clave de diferenciacion. Debe funcionar siempre. |
| Validacion | Prevenir datos invalidos en BD. |

**ROI estimado:** Suite ejecutable en CI detecta regresiones automaticamente.

### 12.3 Pruebas UI

| Prueba | Justificacion |
|--------|---------------|
| Agregar URL | Camino feliz principal. 60%+ de uso. |
| URL invalida | Casos de borde criticos para UX. |
| Pause/Resume botones | Interacciones frecuentes. Fallos frustran usuarios. |

**ROI estimado:** Eliminacion de 2+ horas de testing manual por ciclo de release.

---

## 13. ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
DownLoader/
|
|-- docs/
|   |-- PLAN_DE_PRUEBAS.md              # Este documento
|   |-- MATRICES_DE_DECISION.md         # Matrices por caso
|   |-- EVIDENCIAS.md                    # Reporte de evidencias
|   '-- presentacion/                    # Materiales de presentacion
|
|-- tests/
|   |-- api/
|   |   |-- DownLoader-API.postman_collection.json
|   |   |-- DownLoader-API.postman_environment.json
|   |   '-- server.py                    # Flask API server
|   |
|   |-- ui/
|   |   |-- test_gui.py                  # Playwright tests
|   |   |-- conftest.py                  # Fixtures Playwright
|   |   '-- playwright.config.py         # Configuracion
|   |
|   |-- test_validators.py               # Expandido
|   |-- test_helpers.py                  # Expandido
|   |-- test_downloader.py               # Nuevo
|   |-- test_database.py                 # Expandido
|   '-- conftest.py                      # Fixtures compartidos
|
|-- .github/
|   '-- workflows/
|       '-- test-pipeline.yml            # Pipeline CI/CD
|
|-- pytest.ini                          # Configuracion pytest
|-- requirements-test.txt                # Dependencias de prueba
'-- videos/                             # Video de falla intencional
```

---

## 14. pipeline CI/CD - GitHub Actions

### 14.1 Jobs del Pipeline

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest --cov=src --cov-report=html --cov-report=xml
      - name: Upload coverage
        uses: actions/upload-artifact@v4

  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Newman
        run: npm install -g newman
      - name: Start Flask server
        run: python tests/api/server.py &
      - name: Run Postman tests
        run: newman run tests/api/collection.json
      - name: Upload results
        uses: actions/upload-artifact@v4

  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Playwright
        run: pip install playwright && playwright install chromium
      - name: Start Eel server
        run: python -m src.gui.web_gui &
      - name: Run UI tests
        run: pytest tests/ui/test_gui.py
      - name: Upload screenshots
        uses: actions/upload-artifact@v4
```

### 14.2 Artefactos Generados

| Artefacto | Contenido | Usado para |
|-----------|-----------|------------|
| test-results.xml | Resultados JUnit | Dashboard GitHub |
| coverage/ | Reporte HTML coverage | Revisor de codigo |
| api-report/ | Reporte HTML Postman | Validacion API |
| ui-screenshots/ | Capturas de pantalla | Evidencias |
| ui-report.html | Reporte Playwright | Documentacion |

---

## 15. VIDEO DE FALLA INTENCIONAL

### Procedimiento:

1. **Introducir bug en codigo fuente:**
   - Modificar `is_valid_url()` para retornar invertido (not)
   - Commit: "feat: introduce intentional bug for demo"

2. **Ejecutar pipeline (mostrar falla):**
   - Push a branch
   - GitHub Actions muestra job fallido
   - Capturar pantalla del log de error

3. **Corregir bug:**
   - Revetir cambio
   - Commit: "fix: revert intentional bug"
   - Push

4. **Ejecutar pipeline (mostrar exito):**
   - GitHub Actions muestra todos los jobs verdes
   - Capturar pantalla final

### Archivos generados:
- `videos/falla-intencional-antes.mp4` - Pipeline fallido
- `videos/falla-intencional-despues.mp4` - Pipeline exitoso
- `videos/falla-intencional-completo.mp4` - Video completo

---

## 16. PRESENTACION FINAL

### Estructura (15 minutos):

1. **Introduccion (2 min)**
   - Nombre del equipo
   - Sistema bajo prueba: DownLoader Pro
   - Resumen del plan

2. **Metodologia (3 min)**
   - Estandar ISO/IEC 29119
   - Fases del plan
   - Roles y responsabilidades

3. **Diseno de Pruebas (4 min)**
   - Casos unitarios disenados
   - Casos API (Postman)
   - Casos UI (Playwright)
   - Matrices de decision

4. **Implementacion (3 min)**
   - Demo en vivo del pipeline CI/CD
   - Resultados de ejecucion
   - Coverage achieved

5. **Evidencias (2 min)**
   - Screenshots
   - Reportes generados
   - Video de falla

6. **Lecciones Aprendidas (1 min)**
   - Desafios encontrados
   - Mejoras propuestas

### Materiales:
- `docs/presentacion/presentacion.pdf`
- `docs/presentacion/guion.pdf`
- `docs/presentacion/diapositivas.pptx`

---

**Documento creado:** Abril 2026
**Version:** 1.0
**Estado:** Planificado - Pendiente de implementacion
