# Implementation Plan

Bibliometría multi-fuente y análisis consolidado (Componente B)

## Overview

El plan deriva directamente del `design.md` aprobado. Incorpora Google Scholar
como segunda fuente y generaliza el análisis a un resumen **consolidado**,
reutilizando el pipeline del Boletín SAO ya existente.

Orden incremental respetando dependencias: primero el **refactor compartido**
(sin cambiar el comportamiento del Boletín), luego el **conector** y el
**pipeline** de Google Scholar, después **schemas → servicio → endpoint** del
backend, la **vista** del frontend, la **guía** de exportación y, al final, una
**verificación** completa.

Convenciones de testing (design.md, Testing Strategy):
- Property-based con **hypothesis** (Python), mínimo **100 iteraciones** por
  propiedad, un test por propiedad, etiquetado con un comentario
  `# Feature: multi-source-bibliometria, Property N: <texto>`.
- Las sub-tareas marcadas con `*` son opcionales (tests accesorios) y pueden
  omitirse para un MVP más rápido. Las tareas de verificación de propiedades del
  diseño permanecen como núcleo, no opcionales.

## Tasks

- [x] 1. Refactor compartido del contrato y helpers (sin cambiar la salida del Boletín)
  - [x] 1.1 Extraer `ArticleRecord` a un módulo compartido
    - Crear `bibliometrics/ingestion/article_record.py` con el dataclass
      `ArticleRecord` (contrato V1), moviéndolo tal cual desde
      `extract_boletin.py` (mismos campos, defaults y tipos).
    - Actualizar `bibliometrics/ingestion/extract_boletin.py` para importar
      `ArticleRecord` del nuevo módulo, sin alterar su comportamiento.
    - _Requirements: 2.4, 10.2_

  - [x] 1.2 Extraer helpers de pipeline a `_common.py`
    - Crear `bibliometrics/pipelines/_common.py` con `norm_title`,
      `mark_duplicates`, `validate_period`, `write_outputs`, `print_summary`,
      movidos desde `process_boletin_sao.py` (misma lógica y salida).
    - Actualizar `bibliometrics/pipelines/process_boletin_sao.py` para usar esos
      helpers, sin cambiar el formato ni el contenido del dataset del Boletín.
    - _Requirements: 4.1, 5.1, 5.2_

  - [x] 1.3 Prueba de no-regresión del pipeline del Boletín
    - Ejecutar el pipeline del Boletín sobre las muestras y comparar que el
      JSON/CSV generado es equivalente al previo al refactor.
    - _Requirements: 10.2_

- [x] 2. Conector Google Scholar (Publish or Perish → contrato V1)
  - [x] 2.1 Implementar detección de formato y extracción de registros
    - Crear `bibliometrics/ingestion/extract_scholar.py` con
      `detect_format(path) -> "json" | "csv"` (case-insensitive; `ValueError`
      si la extensión no es soportada) y
      `extract_records(input_path) -> list[ArticleRecord]`.
    - Mapear PoP → contrato V1 según la tabla del diseño: `source` fijo
      `"Google Scholar"`; columna PoP `Source` → `journal`; campo no detectado →
      `None` (sin invención); obligatorio faltante/ambiguo →
      `inclusion_status = "PENDIENTE_REVISIÓN"` con nota.
    - `article_id` determinista: `gs-<hash12(doi normalizado)>` o, sin DOI,
      `gs-<hash12(título normalizado + "|" + año)>` (SHA-256, primeros 12 hex).
    - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2_

  - [x] 2.2 Property test — detección de formato por extensión
    - **Property 1: Detección de formato por extensión (case-insensitive)**
    - **Validates: Requirements 1.2, 1.3**

  - [x] 2.3 Property test — no-invención de campos ausentes
    - **Property 2: No-invención de campos ausentes**
    - **Validates: Requirements 2.2**

  - [x] 2.4 Property test — fuente fija y conformidad del contrato
    - **Property 3: Fuente fija y conformidad del contrato**
    - **Validates: Requirements 2.1**

  - [x] 2.5 Property test — obligatorio faltante/ambiguo marca revisión
    - **Property 4: Obligatorio faltante o ambiguo marca revisión**
    - **Validates: Requirements 2.3, 3.2**

  - [x] 2.6 Property test — validación de período no descarta
    - **Property 5: Validación de período no descarta**
    - **Validates: Requirements 3.1**

- [x] 3. Pipeline Google Scholar por CLI (espejo del Boletín con `_common`)
  - [x] 3.1 Implementar el pipeline reproducible
    - Crear `bibliometrics/pipelines/process_google_scholar.py` que recorra
      `data/raw/google_scholar/` (`.json`/`.csv`), invoque `extract_records`,
      valide período 2020–2030, marque duplicados por título normalizado
      (helpers de `_common`) y escriba JSON+CSV en
      `data/processed/google_scholar/`.
    - Carpeta ausente/vacía/sin `.json` ni `.csv` → mensaje informativo y salida
      con éxito sin procesar registros.
    - Registro malformado → registrar archivo + posición, descartarlo y
      continuar el lote.
    - Imprimir resumen: leídos / procesados / descartados + completitud por
      campo. Ejecutable con un único comando sin UI.
    - _Requirements: 1.1, 1.4, 1.5, 1.6, 4.1, 5.1, 5.2, 5.3_

  - [x] 3.2 Property test — robustez ante registros malformados
    - **Property 6: Robustez ante registros malformados**
    - **Validates: Requirements 1.5**

  - [x] 3.3 Property test — conservación aritmética del resumen de ingesta
    - **Property 7: Conservación aritmética del resumen de ingesta**
    - **Validates: Requirements 1.6**

  - [x] 3.4 Property test — inmutabilidad de `data/raw`
    - **Property 8: Inmutabilidad de `data/raw`**
    - **Validates: Requirements 1.1**

  - [x] 3.5 Property test — deduplicación básica dentro de la fuente
    - **Property 9: Deduplicación básica dentro de la fuente**
    - **Validates: Requirements 4.1**

  - [x] 3.6 Tests de ejemplo / edge cases del pipeline
    - Carpeta ausente/vacía/solo `.txt` → éxito sin registros.
    - Escritura de JSON+CSV y resumen con completitud.
    - _Requirements: 1.4, 5.1, 5.2_

- [x] 4. Checkpoint — conector y pipeline de Scholar
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Contratos de datos del resumen consolidado (backend y frontend)
  - [x] 5.1 Añadir schemas Pydantic del consolidado
    - En `backend/src/schemas/bibliometria.py` añadir `AporteFuente` y
      `ResumenConsolidado` (heredan de `SchemaBase`, `extra="forbid"`) con los
      campos definidos en el diseño (incluye `alcance = "consolidado"`,
      `aporte_por_fuente`, `por_ofc`, `sin_ofc`, `fechas_dataset`).
    - _Requirements: 6.2, 6.3, 6.4, 7.1, 7.2_

  - [x] 5.2 Añadir tipos equivalentes en el frontend
    - En `frontend/src/types/bibliometria.ts` añadir `AporteFuente` y
      `ResumenConsolidado` reflejando exactamente los schemas del backend.
    - _Requirements: 9.1, 9.3_

- [x] 6. Servicio consolidado multi-fuente
  - [x] 6.1 Implementar `resumen_consolidado()`
    - Generalizar `backend/src/services/bibliometria_service.py` con
      `resumen_consolidado()` que descubra subcarpetas bajo `data/processed/`,
      agrupe registros por su campo `source`, combine (unión sin exclusión) y
      agregue: total, por año, por volumen, completitud, pendientes, posibles
      duplicados y `aporte_por_fuente`.
    - Tratar carpetas/archivos `*_clasificado` solo como origen de `por_ofc` (no
      cuentan al total). Sin deduplicación entre fuentes.
    - Sin datasets → resumen vacío coherente (todo en 0). Conservar el método
      `resumen()` del Boletín intacto.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 7.1, 7.2, 7.3, 10.1_

  - [x] 6.2 Property test — el total consolidado es la suma por fuente
    - **Property 10: El total consolidado es la suma por fuente**
    - **Validates: Requirements 6.1, 7.1**

  - [x] 6.3 Property test — agregaciones bien formadas
    - **Property 11: Agregaciones bien formadas**
    - **Validates: Requirements 6.2**

  - [x] 6.4 Property test — los datasets clasificados no se cuentan como fuente
    - **Property 12: Los datasets clasificados no se cuentan como fuente**
    - **Validates: Requirements 6.7**

  - [x] 6.5 Property test — no hay deduplicación entre fuentes
    - **Property 13: No hay deduplicación entre fuentes**
    - **Validates: Requirements 6.6**

  - [x] 6.6 Property test — extensibilidad por descubrimiento
    - **Property 14: Extensibilidad por descubrimiento**
    - **Validates: Requirements 10.1**

  - [x] 6.7 Test de ejemplo — servicio sin datasets
    - Sin datasets bajo `data/processed/` → resumen vacío coherente.
    - _Requirements: 6.5_

- [x] 7. Endpoint consolidado (conservando el endpoint actual)
  - [x] 7.1 Añadir ruta `GET /bibliometria/resumen`
    - En `backend/src/api/bibliometria.py` exponer `GET /bibliometria/resumen`
      con `response_model=ResumenConsolidado` invocando
      `resumen_consolidado()`; sin datasets responde un resumen vacío (200) para
      un estado vacío honesto. Conservar `GET /bibliometria/boletin-sao/resumen`.
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 7.2 Tests de integración de los endpoints
    - `TestClient`: `/bibliometria/resumen` con datasets de ejemplo (shape de
      Req 6 y 7), sin datasets (estado vacío honesto) y
      `/bibliometria/boletin-sao/resumen` sigue operativa.
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 8. Checkpoint — backend consolidado
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Vista generalizada en el frontend
  - [x] 9.1 Añadir cliente y hook del consolidado
    - En `frontend/src/services/apiClient.ts` añadir
      `obtenerResumenConsolidado()` que llame a `GET /bibliometria/resumen`.
    - En `frontend/src/hooks/useBibliometria.ts` añadir `useResumenConsolidado()`
      reutilizando `useAsyncData`.
    - _Requirements: 8.1, 9.1_

  - [x] 9.2 Actualizar `BibliometriaPage` al consolidado
    - Consumir `useResumenConsolidado()`; título que indique "todas las fuentes";
      tarjetas y gráficos sobre el conjunto; sección "Aporte por fuente";
      estado vacío honesto; aviso de clasificación automática sujeta a revisión
      cuando exista `por_ofc`.
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 9.3 Typecheck/build del frontend
    - Ejecutar el typecheck/build del frontend y resolver errores de tipos.
    - _Requirements: 9.1_

- [x] 10. Guía de exportación con Publish or Perish
  - [x] 10.1 Escribir la guía en `docs/`
    - Crear `docs/user-guide/exportar-google-scholar-pop.md` con los pasos:
      instalar PoP, consulta del tema de conservación de aves, Período 2020–2030,
      exportar en JSON (recomendado por conservar mejor la metadata y el resumen
      abreviado), guardar en `data/raw/google_scholar/`, y nota de que Google
      Scholar no tiene API y la obtención es manual/asistida.
    - _Requirements: 11.1, 11.2, 11.3_

- [x] 11. Verificación final y preparación del flujo real
  - [x] 11.1 Preparar la carpeta de entrada sin datos sintéticos
    - Crear `data/raw/google_scholar/` con un `.gitkeep` si no existe, sin
      `DEMO_DATA`, dejando el flujo listo para el Export_PoP real del usuario.
    - _Requirements: 1.1, 1.4_

  - [x] 11.2 Correr toda la suite y dejar el estado verde
    - Ejecutar pytest del backend y de `bibliometrics`, y el typecheck/build del
      frontend; corregir lo que falle.
    - Ensure all tests pass, ask the user if questions arise.
    - _Requirements: 5.3, 8.1, 9.1_

- [x] 12. Generalización del pipeline de clasificación OFC a multi-fuente (post-plan)
  - Generalizar `bibliometrics/pipelines/classify_dataset.py` para clasificar
    CUALQUIER fuente, no solo el Boletín: nuevo argumento `--source <nombre>`
    que lee de `data/processed/<nombre>/` y escribe en
    `data/processed/<nombre>_clasificado/` con el prefijo `<nombre>_clasificado_`.
    Sin argumentos conserva el comportamiento por defecto del Boletín (no
    regresión). El servicio consolidado ya descubre las carpetas `*_clasificado`
    automáticamente (tarea 6.1), por lo que la nueva fuente aparece en `por_ofc`
    sin cambios de backend.
  - Corrida real: clasificado el dataset de OpenAlex (5.000 artículos) →
    `data/processed/openalex_clasificado/`. Verificado que el consolidado suma la
    distribución por OFC de Boletín + OpenAlex sin contar los clasificados al
    total (total consolidado intacto).
  - Nota de trazabilidad: cambio realizado después del plan original para
    habilitar la clasificación de las fuentes añadidas (OpenAlex, Google
    Scholar). La clasificación OFC sigue siendo automática V1 (ADR-010),
    PENDING_VALIDATION con SAO; todo registro sin coincidencia permanece en
    PENDIENTE_REVISIÓN (no se inventa OFC).
  - _Requirements: 10.1_

## Notes

- Tareas marcadas con `*` son opcionales (tests accesorios y verificaciones) y
  pueden omitirse para un MVP más rápido; las tareas núcleo nunca se marcan así.
- Cada property test referencia explícitamente una Property del `design.md` y la
  cláusula de requisitos que valida (trazabilidad).
- Los property tests usan `hypothesis` (≥100 iteraciones) con el comentario
  etiqueta `# Feature: multi-source-bibliometria, Property N: <texto>`.
- El refactor de la tarea 1 no debe cambiar la salida del pipeline del Boletín.
- No se incluyen tareas de despliegue, scraping ni clasificación OFC
  (`PENDING_VALIDATION`), conforme al alcance del spec.

- Fix de robustez de tests (post-plan): los generadores de nombres de carpeta de
  las Properties 12 y 14 (`test_consolidado_clasificado_no_cuenta.py`,
  `test_consolidado_extensibilidad.py`) ahora descartan los nombres de
  dispositivo RESERVADOS de Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9) mediante
  `_es_nombre_reservado_windows`. Antes, Hypothesis podía generar una carpeta
  `NUL`, lo que hacía fallar la escritura del dataset con `FileNotFoundError` en
  Windows (flaky). El código de producción no cambió: es un acotamiento del
  dominio de datos de PRUEBA a nombres válidos en el sistema de archivos.

## Cambios post-plan

- [x] 12. Generalización del clasificador OFC a multi-fuente (ver nota en sección anterior).
- [x] 13. Modelo ACUMULATIVO del resumen consolidado (decisión de producto, a validar con SAO)
  - CONTEXTO: antes el servicio mostraba solo el dataset MÁS RECIENTE por carpeta
    (`_ultimo_json`). Por decisión del equipo (alineada con el documento de
    contexto `docs/user-guide/contexto_bibliometria_SAO.md`: "corpus único
    maestro" y la actualización anual del proyecto), el dashboard debe mostrar el
    corpus ACUMULADO a lo largo del tiempo, no solo la última corrida.
  - CAMBIO (Opción A, al vuelo en lectura): nuevo helper `_acumular_json(carpeta)`
    en `bibliometria_service.py` que combina TODOS los `*.json` de la carpeta y
    deduplica por `article_id` DENTRO de la fuente (la versión del dataset más
    reciente gana; los registros sin `article_id` se conservan). Se usa tanto
    para las carpetas de fuente como para las `*_clasificado`. No se cambió el
    pipeline ni la forma de guardar datasets (reversible).
  - DEDUP ENTRE FUENTES: sigue SIN forzarse (PENDING_VALIDATION, Req 6.6); solo
    se deduplica dentro de cada fuente apoyándose en el `article_id` determinista.
  - VERIFICACIÓN: 4 tests nuevos (`tests/unit/test_consolidado_acumulativo.py`);
    se añadió `deadline=None` a los 5 property tests del consolidado (Properties
    10-14) porque acumular el histórico es algo más costoso que leer un solo
    archivo y el deadline de 200ms por ejemplo era frágil (miden correctitud, no
    rendimiento). Suite unitaria completa verde (241 passed).
  - PENDIENTE: la dedup entre fuentes y la estrategia incremental definitiva
    siguen en `pending-validation.md` (decisión 11.8). A gran volumen (cientos de
    miles) convendría evaluar un corpus maestro persistente (Opción B) en lugar
    de acumular al vuelo.
  - _Requirements: 6.1, 6.6, 7.1, 10.1_
## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "5.1", "5.2", "10.1", "11.1"] },
    { "id": 2, "tasks": ["1.3", "2.1", "6.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4", "2.5", "2.6", "3.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "7.1", "9.1"] },
    { "id": 4, "tasks": ["3.2", "3.3", "3.4", "3.5", "3.6", "7.2", "9.2"] },
    { "id": 5, "tasks": ["9.3", "11.2"] }
  ]
}
```
