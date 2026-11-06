# Implementation Plan

Fuente OpenAlex de alto volumen vía Publish or Perish (Componente B)

## Overview

El plan deriva directamente del `design.md` aprobado. OpenAlex se incorpora como
un **conector independiente más** que sigue el patrón ya probado de Google
Scholar: un extractor propio (`extract_openalex.py`) y un pipeline CLI
(`process_openalex.py`) que reutilizan sin cambios los helpers de
`bibliometrics/pipelines/_common.py` y el contrato `ArticleRecord` (Article Data
Contract V1). El servicio consolidado, el endpoint y la vista **no se tocan**: el
backend descubre la carpeta `data/processed/openalex/` y agrupa por el campo
`source`, por lo que OpenAlex aparece en el consolidado sin cambios de código
(Req 6).

Orden incremental respetando dependencias: primero el **conector** (parseo,
mapeo, `article_id`), luego el **pipeline** CLI, después la **guía** de
exportación con Publish or Perish, la **preparación** de la carpeta de entrada y,
al final, la **verificación de no-rediseño** del consolidado más la corrida
completa de la suite.

Convenciones de testing (design.md, Testing Strategy):
- Property-based con **hypothesis** (Python), ya pinado en
  `bibliometrics/requirements.txt`; mínimo **100 iteraciones** por propiedad, un
  test por propiedad, etiquetado con un comentario
  `# Feature: fuente-openalex, Property N: <texto>`.
- Las sub-tareas marcadas con `*` son opcionales (tests accesorios y edge cases)
  y pueden omitirse para un MVP más rápido. Las tareas de verificación de las
  propiedades del diseño permanecen como núcleo, no opcionales.

Lenguaje e infraestructura: **Python 3.12+**, `snake_case`, `pytest`, layout de
`structure.md`.

## Tasks

- [x] 1. Conector OpenAlex (Publish or Perish / OpenAlex → contrato V1)
  - [x] 1.1 Implementar detección de formato y extracción de registros
    - Crear `bibliometrics/ingestion/extract_openalex.py` como espejo de
      `extract_scholar.py`, con `detect_format(path) -> "json" | "csv"`
      (case-insensitive; `ValueError` si la extensión no es `.json` ni `.csv`) y
      `extract_records(input_path) -> list[ArticleRecord]`.
    - Definir las constantes `OPENALEX_SOURCE = "OpenAlex"` y
      `OPENALEX_EXTRACTION_METHOD = "Publish or Perish export (OpenAlex) V1"`.
    - Mapear PoP/OpenAlex → contrato V1 según la tabla del diseño, con búsqueda
      **case-insensitive** y varias claves candidatas por campo (la primera no
      vacía gana): `source` fijo `"OpenAlex"`; columna `Source`/`host_venue`/
      `venue` → `journal`; `concepts`/`keywords` → `keywords`; `id`/`url` →
      `url`; campo no detectado → `None` (sin invención); obligatorio
      faltante/ambiguo → `inclusion_status = "PENDIENTE_REVISIÓN"` con nota.
    - Preservar en `source_url` el identificador/URL propio de OpenAlex (campo
      `id`, p. ej. `https://openalex.org/Wxxxxxxxxx`) cuando exista; si no,
      dejar `None` sin inventarlo.
    - `article_id` determinista con prefijo propio `oa-`:
      `oa-<hash12(doi normalizado)>` o, sin DOI,
      `oa-<hash12(título normalizado + "|" + año)>` (SHA-256, primeros 12 hex),
      usando el mismo `norm_title` de `_common.py`.
    - Reutilizar lectores tolerantes a BOM y JSON anidado bajo
      `data`/`results`/`records`/`items` (`_iter_json_records`,
      `_iter_csv_records`), igual que el conector de Scholar.
    - Confirmar el mapeo fino inspeccionando un Export_PoP_OpenAlex real de
      muestra si está disponible (mapeo marcado `PENDING_VALIDATION` en diseño);
      no inventar claves que no aparezcan.
    - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 7.3_

  - [x] 1.2 Property test — detección de formato por extensión
    - **Property 1: Detección de formato por extensión (case-insensitive)**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 1.3 Property test — no-invención de campos ausentes
    - **Property 2: No-invención de campos ausentes**
    - **Validates: Requirements 2.3**

  - [x] 1.4 Property test — fuente fija y conformidad del contrato
    - **Property 3: Fuente fija y conformidad del contrato**
    - **Validates: Requirements 2.1, 2.2**

  - [x] 1.5 Property test — obligatorio faltante/ambiguo marca revisión
    - **Property 4: Obligatorio faltante o ambiguo marca revisión**
    - **Validates: Requirements 2.4, 3.2**

  - [x] 1.6 Property test — validación de período no descarta
    - **Property 5: Validación de período no descarta**
    - **Validates: Requirements 3.1**

  - [x] 1.7 Property test — `article_id` determinista, reproducible y con prefijo `oa-`
    - **Property 6: `article_id` determinista, reproducible y con prefijo propio**
    - **Validates: Requirements 2.6**

  - [x] 1.8 Property test — preservación de procedencia sin invención
    - **Property 11: Preservación de procedencia sin invención**
    - **Validates: Requirements 7.3**

- [x] 2. Pipeline OpenAlex por CLI (espejo del de Scholar con `_common`)
  - [x] 2.1 Implementar el pipeline reproducible
    - Crear `bibliometrics/pipelines/process_openalex.py` como espejo de
      `process_google_scholar.py`, con las constantes propias:
      `DEFAULT_INPUT = data/raw/openalex`,
      `OUTPUT_DIR = data/processed/openalex`, `SOURCE_LABEL = "OpenAlex"`,
      `BASENAME = "openalex_dataset"`.
    - Recorrer `data/raw/openalex/` (descubrimiento case-insensitive de
      `.json`/`.csv`), invocar `extract_records` por archivo, aplicar
      `validate_period` a cada registro, marcar duplicados con `mark_duplicates`
      (helpers de `_common`) y escribir JSON+CSV en `data/processed/openalex/`
      con `write_outputs`.
    - Leer solo de `data/raw/openalex/` y escribir solo en
      `data/processed/openalex/`; no reutilizar la carpeta ni la etiqueta de
      Google Scholar.
    - Carpeta ausente/inaccesible/sin `.json` ni `.csv` → mensaje informativo y
      salida con éxito sin procesar registros.
    - Registro malformado → registrar archivo + posición, descartarlo y
      continuar el lote; archivo no parseable → informar y omitir sin abortar.
    - Imprimir resumen de ingesta (leídos / procesados / descartados) con
      `leídos == procesados + descartados`, y resumen de completitud por campo
      con `print_summary`. Ejecutable con un único comando sin UI.
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 4.1, 5.1, 5.2, 5.3, 7.1, 7.2_

  - [x] 2.2 Property test — robustez ante registros malformados
    - **Property 7: Robustez ante registros malformados**
    - **Validates: Requirements 1.5**

  - [x] 2.3 Property test — conservación aritmética del resumen de ingesta
    - **Property 8: Conservación aritmética del resumen de ingesta**
    - **Validates: Requirements 1.6**

  - [x] 2.4 Property test — inmutabilidad de `data/raw/openalex`
    - **Property 9: Inmutabilidad de `data/raw/openalex`**
    - **Validates: Requirements 1.1, 7.1**

  - [x] 2.5 Property test — deduplicación básica dentro de la fuente
    - **Property 10: Deduplicación básica dentro de la fuente**
    - **Validates: Requirements 4.1**

  - [ ]* 2.6 Tests de ejemplo / edge cases del pipeline
    - Carpeta ausente/vacía/solo `.txt` → éxito sin registros (Req 1.4).
    - Escritura de JSON+CSV en `data/processed/openalex/` y resumen con
      completitud (Req 5.1, 5.2).
    - Detección de JSON anidado bajo `data`/`results`/`records` y CSV con BOM.
    - _Requirements: 1.4, 5.1, 5.2_

- [x] 3. Checkpoint — conector y pipeline de OpenAlex
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Guía de exportación con Publish or Perish (OpenAlex)
  - [x] 4.1 Escribir la guía en `docs/`
    - Crear `docs/user-guide/exportar-openalex-pop.md` con los pasos: abrir
      Publish or Perish, seleccionar **OpenAlex** como fuente de datos, consultar
      el tema de conservación de aves, Período_Inclusión 2020–2030, formato
      **JSON recomendado** (preserva mejor metadata y resumen) y destino
      `data/raw/openalex/`.
    - Describir la estrategia de **varias consultas complementarias** (un archivo
      por consulta) para cubrir el tema con mayor volumen, e indicar que el
      pipeline combina todos los archivos de la carpeta y marca duplicados por
      título.
    - Marcar explícitamente los términos de búsqueda y nombres de archivo como
      **propuesta del equipo a validar con SAO**, no como criterio oficial.
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 5. Preparación del flujo real (sin datos sintéticos)
  - [x] 5.1 Preparar la carpeta de entrada
    - Crear `data/raw/openalex/` con un `.gitkeep` si no existe, sin `DEMO_DATA`,
      dejando el flujo listo para el Export_PoP_OpenAlex real del usuario.
    - _Requirements: 1.1, 1.4, 7.1_

- [x] 6. Verificación de incorporación automática al consolidado (sin rediseño)
  - [x] 6.1 Test de integración — OpenAlex aparece en el consolidado sin tocar servicio ni vista
    - Poblar un `data/processed/openalex/` de prueba con un dataset conforme al
      contrato V1 (`source = "OpenAlex"`) y comprobar vía `BibliometriaService` /
      `GET /bibliometria/resumen` que OpenAlex aparece en el total y en
      `aporte_por_fuente` con el nombre `"OpenAlex"`, **sin** modificar
      `bibliometria_service.py`, `api/bibliometria.py`, los schemas ni la
      `BibliometriaPage`.
    - Comprobar que el `Dataset_Procesado` de Google Scholar (u otra fuente)
      sigue contándose como su propia fuente y permanece intacto.
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 7. Verificación final
  - [x] 7.1 Correr toda la suite y dejar el estado verde
    - Ejecutar pytest de `bibliometrics` y del backend (incluido el test de
      integración del consolidado) y corregir lo que falle.
    - Smoke del pipeline por un único comando CLI
      (`python bibliometrics/pipelines/process_openalex.py`).
    - Ensure all tests pass, ask the user if questions arise.
    - _Requirements: 5.3, 6.1_

## Notes

- Tareas marcadas con `*` son opcionales (tests accesorios y edge cases) y pueden
  omitirse para un MVP más rápido; las tareas núcleo nunca se marcan así.
- Cada property test referencia explícitamente una Property del `design.md` y la
  cláusula de requisitos que valida (trazabilidad).
- Los property tests usan `hypothesis` (≥100 iteraciones) con el comentario
  etiqueta `# Feature: fuente-openalex, Property N: <texto>`.
- El conector y el pipeline son espejo del de Google Scholar; no se refactoriza a
  una base común en este spec para no tocar código de otras fuentes (Req 6.3).
- No se modifica el servicio, el endpoint ni la vista: la incorporación es por
  convención (carpeta `data/processed/openalex/` + campo `source = "OpenAlex"`).
- No se incluyen tareas de despliegue, scraping, consultas programáticas a la API
  de OpenAlex ni clasificación OFC (`PENDING_VALIDATION`), conforme al alcance.
- El mapeo fino PoP-OpenAlex → contrato V1 queda `PENDING_VALIDATION`: se confirma
  en la tarea 1.1 inspeccionando un export real de muestra si está disponible.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1", "5.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "6.1"] },
    { "id": 3, "tasks": ["7.1"] }
  ]
}
```
