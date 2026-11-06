# Implementation Plan

Fuente OpenAlex por API (consulta directa, Componente B)

## Overview

El plan deriva directamente del `design.md` aprobado. OpenAlex por API se
incorpora como un **conector independiente** que reemplaza el paso manual de
exportación con Publish or Perish (PoP) del spec hermano `fuente-openalex`: un
cliente de API nuevo (`openalex_api_client.py`) y un pipeline CLI
(`process_openalex_api.py`) que reutilizan sin cambios los helpers de
`bibliometrics/pipelines/_common.py` y el contrato `ArticleRecord` (Article Data
Contract V1). Ambas vías (API y PoP) escriben en la **misma carpeta**
`data/processed/openalex/`, con el mismo `source = "OpenAlex"` y el mismo esquema
de `article_id` (prefijo `oa-`), de modo que se cuentan como una sola fuente y se
deduplican juntas. El servicio consolidado, el endpoint y la vista **no se
tocan**: el backend descubre la carpeta y agrupa por el campo `source`, por lo
que OpenAlex aparece en el consolidado sin cambios de código (Req 7).

Orden incremental respetando dependencias: primero el **setup** de dependencia y
configuración (cliente HTTP pinado + placeholder de ENV), luego la **capa HTTP**
del cliente de API (paginación por cursor, ritmo, reintentos, sin-conectividad),
después la **transformación** `work` → `ArticleRecord` (reconstrucción del
abstract, `article_id` compartido), luego el **pipeline** CLI que combina
Consultas y escribe el dataset, la **guía** de uso, un **checkpoint**, la
**verificación de no-rediseño** del consolidado y, al final, la corrida completa
de la suite más el smoke del comando.

Separación de capas (design.md, Architecture): la capa HTTP no conoce el contrato
V1 y la transformación no conoce HTTP. Esto permite probar paginación/reintentos
con el cliente HTTP **simulado** (sin red real) y la transformación con `work`s
sintéticos marcados como `DEMO_DATA`.

Convenciones de testing (design.md, Testing Strategy):
- Property-based con **hypothesis** (Python), ya pinado en
  `bibliometrics/requirements.txt`; mínimo **100 iteraciones** por propiedad, un
  test por propiedad, etiquetado con un comentario
  `# Feature: fuente-openalex-api, Property N: <texto>`.
- Las pruebas de la capa HTTP (Propiedades 7 y 8) **simulan/mockean** el cliente
  HTTP; **ningún test golpea la red real**. Las pruebas de transformación,
  abstract, id y dedupe usan `work`s sintéticos `DEMO_DATA`.
- Las sub-tareas marcadas con `*` son opcionales (tests accesorios y edge cases)
  y pueden omitirse para un MVP más rápido. Las tareas de verificación de las
  propiedades del diseño permanecen como núcleo, no opcionales.

Lenguaje e infraestructura: **Python 3.12+**, `snake_case`, `pytest`, layout de
`structure.md`.

## Tasks

- [x] 1. Setup de dependencia y configuración
  - [x] 1.1 Añadir el cliente HTTP pinado y el placeholder de la Mailto_Cortesia
    - Añadir un cliente HTTP **pinado** a `bibliometrics/requirements.txt`
      (propuesta `requests==2.32.*`, o `httpx` pinado si se prefiere; para un
      pipeline secuencial con cursor `requests` basta). Fijar la versión exacta
      conforme a `tech.md §21`.
    - Añadir a `.env.example` un placeholder **comentado** de `OPENALEX_MAILTO`
      (p. ej. `# OPENALEX_MAILTO=tu-correo@ejemplo.org`), documentando que es
      opcional y **no es un secreto**; nunca versionar un valor real.
    - No modificar `_common.py` ni `article_record.py` ni ningún conector o
      pipeline de otra fuente.
    - _Requirements: 1.4, 1.5, 9.2_

- [x] 2. Capa HTTP del cliente de API (`openalex_api_client.py`)
  - [x] 2.1 Implementar la capa HTTP (Consulta, ApiConfig, paginación, reintentos)
    - Crear `bibliometrics/ingestion/openalex_api_client.py` con las constantes
      `OPENALEX_SOURCE = "OpenAlex"`,
      `OPENALEX_API_EXTRACTION_METHOD = "OpenAlex API V1"`,
      `OPENALEX_BASE_URL = "https://api.openalex.org/works"`,
      `PERIODO_MIN, PERIODO_MAX = 2020, 2030` y
      `MAILTO_ENV_VAR = "OPENALEX_MAILTO"`.
    - Definir los dataclasses `Consulta` (`term`, `year_from`, `year_to`) y
      `ApiConfig` (`per_page<=200`, `max_results` opcional, `pace_seconds`,
      `max_retries`, `backoff_base`, `mailto`), y la excepción `HttpError` con
      `status_code` y `transient`.
    - Implementar `resolve_mailto()` que lee `OPENALEX_MAILTO` del entorno
      (`None` si no está; nunca exige la variable ni lee de archivo versionado).
    - Implementar `fetch_page(session, consulta, cursor, config)`: pide UNA
      página de `works`, envía `filter=publication_year:{from}-{to}`, `per_page`,
      `cursor` y `mailto` si está configurado; devuelve
      `(results, next_cursor)` usando `meta.next_cursor`; lanza `HttpError` en
      fallo HTTP. Capa HTTP pura, no transforma works.
    - Implementar `fetch_with_retry(...)`: reintenta solo errores transitorios
      (429, 5xx) con espera creciente hasta `max_retries`; no reintenta errores
      permanentes (p. ej. 400); agotados los reintentos, propaga `HttpError`.
    - Implementar `iter_works(session, consulta, config)`: pagina por cursor
      desde `cursor="*"`, aplica `pace_seconds` entre páginas y se detiene al
      agotar el cursor o al alcanzar `max_results`. No escribe nada.
    - Detección de sin-conectividad al iniciar: dejar el error de red/DNS
      propagable y clasificable para que el pipeline lo maneje (Req 2.4).
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 8.1_

  - [x] 2.2 Property test — paginación recupera todos los resultados hasta el límite
    - **Property 7: Paginación recupera todos los resultados hasta el límite**
    - **Validates: Requirements 1.3**
    - Simular/mockear el cliente HTTP con páginas encadenadas por cursor; sin red
      real.

  - [x] 2.3 Property test — reintento solo ante errores transitorios
    - **Property 8: Reintento solo ante errores transitorios**
    - **Validates: Requirements 2.2**
    - Simular secuencias de respuestas 200/429/5xx/4xx; verificar backoff y que
      los permanentes no se reintentan; sin red real.

  - [ ]* 2.4 Tests de ejemplo / edge cases de la capa HTTP
    - `resolve_mailto` con y sin la ENV (nunca exige la variable).
    - Cursor único (una sola página), `max_results` menor que el total,
      `next_cursor = None` que detiene la paginación.
    - Error permanente en la primera página y agotamiento de reintentos.
    - _Requirements: 1.4, 2.1, 2.3_

- [x] 3. Transformación `work` → contrato V1 (en `openalex_api_client.py`)
  - [x] 3.1 Implementar la transformación, el abstract y el `article_id`
    - Implementar `reconstruct_abstract(inverted_index)`: coloca cada palabra en
      sus posiciones y concatena en orden ascendente; índice ausente/`None`/vacío
      → `None` (no se inventa texto).
    - Implementar `_api_make_article_id(doi, title, year)` con el **mismo esquema
      que la vía PoP**: con DOI `oa-<hash12(doi normalizado)>`; sin DOI
      `oa-<hash12(norm_title(title) + "|" + año)>`; `hash12` = primeros 12 hex de
      SHA-256; reutilizar `norm_title` de `_common.py` (sin modificarlo).
    - Implementar `work_to_record(work)` según la tabla de mapeo del diseño:
      `source` fijo `"OpenAlex"`; campo ausente → `None` (sin invención);
      obligatorio (`title`/`authors`/`publication_year`) faltante o ambiguo →
      `inclusion_status = "PENDIENTE_REVISIÓN"` con nota; año fuera de 2020–2030 →
      `PENDIENTE_REVISIÓN` con nota sin descartar; año no detectable →
      `publication_year = None` + `PENDIENTE_REVISIÓN`; `abstract` reconstruido;
      `extraction_method = "OpenAlex API V1"`; `source_url = work["id"]` cuando
      exista, si no `None`. No clasifica OFC ni relevancia (`PENDING_VALIDATION`).
    - Confirmar el mapeo fino (pelado del DOI, nombre de revista, forma de
      `keywords`/`concepts`) inspeccionando una respuesta real de la API si está
      disponible (mapeo marcado `PENDING_VALIDATION` en diseño); no inventar
      claves que no aparezcan.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 3.7, 4.2, 4.3, 4.5, 8.1, 8.2_

  - [x] 3.2 Property test — fuente fija y conformidad del contrato
    - **Property 1: Fuente fija y conformidad del contrato**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 3.3 Property test — no-invención de campos ausentes
    - **Property 2: No-invención de campos ausentes**
    - **Validates: Requirements 3.3**

  - [x] 3.4 Property test — obligatorio faltante o ambiguo marca revisión
    - **Property 3: Obligatorio faltante o ambiguo marca revisión**
    - **Validates: Requirements 3.4, 4.3**

  - [x] 3.5 Property test — año fuera de período marca revisión sin descartar
    - **Property 4: Año fuera de período marca revisión sin descartar**
    - **Validates: Requirements 4.2**

  - [x] 3.6 Property test — `article_id` determinista, reproducible y con esquema compartido
    - **Property 5: `article_id` determinista, reproducible y con esquema compartido**
    - **Validates: Requirements 3.6**

  - [x] 3.7 Property test — reconstrucción correcta del abstract desde el índice invertido
    - **Property 6: Reconstrucción correcta del abstract desde el índice invertido**
    - **Validates: Requirements 3.7**

  - [x] 3.8 Property test — procedencia preservada sin invención
    - **Property 10: Procedencia preservada sin invención**
    - **Validates: Requirements 8.2**

  - [ ]* 3.9 Tests de ejemplo / edge cases de la transformación
    - `reconstruct_abstract` con índice típico, palabra repetida en varias
      posiciones, índice vacío y `None`.
    - `work_to_record` con `work` completo, sin `authorships`, sin
      `publication_year`, con año fuera de rango, con/sin `doi`, con/sin `id`.
    - _Requirements: 3.3, 3.4, 3.7, 4.2_

- [x] 4. Pipeline OpenAlex por API (CLI, único comando)
  - [x] 4.1 Implementar el pipeline reproducible
    - Crear `bibliometrics/pipelines/process_openalex_api.py` con las constantes
      `OUTPUT_DIR = data/processed/openalex`, `SOURCE_LABEL = "OpenAlex"`,
      `BASENAME = "openalex_dataset"`.
    - Recibir las `Consulta`s por argumentos CLI (o archivo de configuración no
      secreto), nunca desde `data/raw/`. Por cada `Consulta`: `iter_works` →
      `work_to_record` → `validate_period` (de `_common`, sin cambios).
    - Combinar los resultados de 1..N `Consulta`s en un único dataset y marcar
      duplicados sobre el conjunto combinado con `mark_duplicates` (de `_common`),
      escribir JSON+CSV en `data/processed/openalex/` con `write_outputs`.
    - Manejo de errores del diseño: reintentos agotados en una página → registrar
      `Consulta` + página, conservar lo recuperado y continuar con el resto;
      sin conectividad al iniciar → mensaje comprensible y **no** escribir un
      dataset vacío; `work` individual malformado → descartar sin abortar la
      corrida.
    - Imprimir el resumen de ingesta (works recuperados / páginas consultadas /
      errores encontrados) y el de completitud por campo con `print_summary`.
      Ejecutable con un único comando sin UI. Escribir solo en
      `data/processed/openalex/`; nunca en `data/raw/`.
    - _Requirements: 2.3, 2.4, 2.5, 4.1, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 8.3_

  - [x] 4.2 Property test — deduplicación básica sobre el conjunto combinado
    - **Property 9: Deduplicación básica sobre el conjunto combinado**
    - **Validates: Requirements 5.1, 5.2**

  - [x] 4.3 Property test — inmutabilidad de `data/raw/`
    - **Property 11: Inmutabilidad de `data/raw/`**
    - **Validates: Requirements 6.4**

  - [x] 4.4 Property test — conservación aritmética del resumen
    - **Property 12: Conservación aritmética del resumen**
    - **Validates: Requirements 2.5, 6.2**

  - [x] 4.5 Property test — robustez ante works malformados
    - **Property 13: Robustez ante works malformados**
    - **Validates: Requirements 2.3, 3.4**

  - [ ]* 4.6 Tests de ejemplo / edge cases del pipeline
    - Sin conectividad al iniciar → mensaje comprensible y **no** se escribe
      dataset (Req 2.4).
    - Reintentos agotados en una página → se registra `Consulta` + página, se
      conserva lo recuperado y continúa (Req 2.3).
    - Escritura de JSON+CSV en `data/processed/openalex/` y resumen con
      completitud (Req 6.1, 6.2).
    - _Requirements: 2.3, 2.4, 6.1, 6.2_

- [x] 5. Guía de uso del conector por API
  - [x] 5.1 Escribir la guía en `docs/`
    - Crear `docs/user-guide/consultar-openalex-api.md` con: el comando CLI para
      ejecutar el `Pipeline_OpenAlex_API`, los parámetros de `Consulta` (términos
      y filtros de año), el Período_Inclusión 2020–2030 y la ubicación de salida
      `data/processed/openalex/`.
    - Documentar la variable de entorno `OPENALEX_MAILTO` aclarando que es
      **opcional y no es un secreto** (polite pool).
    - Marcar explícitamente los términos de búsqueda como **propuesta del equipo a
      validar con SAO**, no como criterio oficial de SAO.
    - Aclarar la relación con el spec `fuente-openalex` (exportación manual con
      Publish or Perish): ambas producen el **mismo `Dataset_Procesado`** de
      OpenAlex y la vía por API reemplaza el paso manual.
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 6. Checkpoint — cliente, transformación y pipeline de OpenAlex por API
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Verificación de incorporación automática al consolidado (sin rediseño)
  - [x] 7.1 Test de integración — OpenAlex aparece en el consolidado sin tocar servicio ni vista
    - Poblar un `data/processed/openalex/` de prueba con un dataset conforme al
      contrato V1 (`source = "OpenAlex"`) y comprobar vía `BibliometriaService` /
      `GET /bibliometria/resumen` que OpenAlex aparece en el total y en
      `aporte_por_fuente` con el nombre `"OpenAlex"`, **sin** modificar
      `bibliometria_service.py`, `api/bibliometria.py`, los schemas ni la
      `BibliometriaPage`.
    - Comprobar que el `Dataset_Procesado` de otra fuente (p. ej. Google Scholar)
      sigue contándose como su propia fuente y permanece intacto.
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 8. Verificación final
  - [x] 8.1 Correr toda la suite y dejar el estado verde
    - Ejecutar pytest de `bibliometrics` y del backend (incluido el test de
      integración del consolidado) y corregir lo que falle. Los tests de la capa
      HTTP usan el cliente simulado; ningún test golpea la red real.
    - Smoke del pipeline por un único comando CLI
      (`python bibliometrics/pipelines/process_openalex_api.py ...`) con el
      cliente HTTP simulado o una `Consulta` mínima.
    - Ensure all tests pass, ask the user if questions arise.
    - _Requirements: 6.2, 6.3, 7.1_

- [x] 9. Carga automática del `.env` en el pipeline (post-plan)
  - Añadir `_load_env_file()` en `bibliometrics/pipelines/process_openalex_api.py`
    que, al inicio de `main()`, cargue el `.env` de la raíz del repo con
    python-dotenv **sin sobrescribir** el entorno ya definido (`override=False`):
    una variable exportada en la terminal gana sobre el `.env`. Replica el
    comportamiento del backend (pydantic-settings, `env_file=".env"`), de modo
    que `OPENALEX_API_KEY` / `OPENALEX_MAILTO` se leen del `.env` local sin
    exportarlas en cada terminal.
  - La dependencia `python-dotenv==1.0.1` se fija (pin) en
    `bibliometrics/requirements.txt`; la carga es tolerante a su ausencia (si no
    está instalada, el pipeline sigue usando solo el entorno). De paso se eliminó
    un bloque duplicado de `hypothesis` en el requirements.
  - El conector `openalex_api_client.py` NO cambia: sigue resolviendo la key solo
    del entorno del proceso (los property tests de `estrategia-bibliometrica-api`
    siguen verdes). El valor de la API key nunca se imprime.
  - Verificado: smoke `--help` OK; prueba de prioridad entorno-sobre-`.env`;
    14 property/unit tests verdes (API key + clasificador OFC).
  - _Requirements: 1.4_

## Notes

- Tareas marcadas con `*` son opcionales (tests accesorios y edge cases) y pueden
  omitirse para un MVP más rápido; las tareas núcleo nunca se marcan así.
- Cada property test referencia explícitamente una Property del `design.md` y la
  cláusula de requisitos que valida (trazabilidad). Las 13 propiedades del diseño
  tienen exactamente un test de propiedad.
- Los property tests usan `hypothesis` (≥100 iteraciones) con el comentario
  etiqueta `# Feature: fuente-openalex-api, Property N: <texto>`.
- Las pruebas de la capa HTTP (Propiedades 7 y 8) **simulan/mockean** el cliente
  HTTP; **ningún test golpea la red real**. Las pruebas de transformación,
  abstract, id y dedupe usan `work`s sintéticos marcados como `DEMO_DATA`.
- El cliente y el pipeline son espejo del patrón de la vía PoP; no se refactoriza
  a una base común en este spec para no tocar código de otras fuentes (Req 7.3).
- No se modifica el servicio, el endpoint ni la vista: la incorporación es por
  convención (carpeta `data/processed/openalex/` + campo `source = "OpenAlex"`).
  Tampoco se modifican `_common.py`, `article_record.py`, los conectores/pipelines
  de otras fuentes ni la vía PoP (`extract_openalex.py` / `process_openalex.py`).
- Misma carpeta y mismo esquema de `article_id` (`oa-`) que la vía PoP: el mismo
  `work` produce el mismo id por API o por PoP, por lo que cuentan como una sola
  fuente y se deduplican juntos.
- No se incluyen tareas de despliegue, scraping, botón de consulta en vivo,
  publicación a ArcGIS Online ni clasificación OFC (`PENDING_VALIDATION`),
  conforme al alcance.
- El mapeo fino `work` → contrato V1 queda `PENDING_VALIDATION`: se confirma en la
  tarea 3.1 inspeccionando una respuesta real de la API si está disponible.
- `OPENALEX_MAILTO` es opcional y no es un secreto; nunca se versiona con un valor
  real.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "5.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "4.1"] },
    { "id": 4, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6", "7.1"] },
    { "id": 5, "tasks": ["8.1"] }
  ]
}
```
