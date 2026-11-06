# Implementation Plan

Estrategia bibliométrica e integración por API key (Componente B)

## Overview

El plan deriva directamente del `design.md` aprobado. Este spec es, ante todo,
de **formalización, análisis técnico y especificación**: la enorme mayoría de
sus entregables son **documentos** bajo `docs/bibliometrics/` y hay un **único
cambio de código acotado** (soporte de `OPENALEX_API_KEY` en el conector
OpenAlex existente, para habilitar la paginación por cursor más allá de la
primera página).

**Ninguna tarea ejecuta búsquedas reales contra OpenAlex ni consume cuotas de
API.** El piloto se **especifica** (documento), no se ejecuta a escala (Req 9.5,
10.1). La verificación de los documentos es una **lista de comprobación de
contenido**, no property-based testing; solo el único cambio de código (Req 7)
tiene property tests.

El trabajo se organiza en las cuatro fases del diseño, más el cambio de código,
la guía, un checkpoint y la verificación final:

1. **Fase 1 — Documentación de la estrategia**: estrategia de búsqueda,
   criterios de inclusión/exclusión ampliados, clasificación geográfica y
   revisión propuesta del contrato de datos (Req 1–5).
2. **Fase 2 — Especificación de la integración por API key** (Req 6) + el
   **único cambio de código** (Req 7) con sus property tests.
3. **Fase 3 — Límites de recuperación por corrida** (Req 8).
4. **Fase 4 — Piloto controlado especificado** (Req 9) + listado
   `PENDING_VALIDATION` (Req 11) + guía de uso.
5. **Checkpoint** y **verificación final** (suite con cliente simulado + smoke
   del pipeline sin red real).

### Restricciones que todas las tareas respetan (Req 10)

- **Sin recolección masiva ni consumo de cuotas**: ninguna tarea lanza consultas
  reales; el piloto es un documento (Req 9.5, 10.1).
- **Sin cambios al consolidado**: no se tocan `bibliometria_service.py`,
  `api/bibliometria.py`, los schemas, la `Vista_Bibliometria` ni el
  procesamiento del Boletín SAO (Req 10.2).
- **Sin tocar la lógica no relacionada**: no se modifica `_common.py`,
  `article_record.py`, la transformación `work → ArticleRecord`, el esquema de
  `article_id`, el ritmo, los reintentos, `OPENALEX_MAILTO` ni la vía PoP
  (`extract_openalex.py` / `process_openalex.py`) (Req 7.6).
- **Sin dependencias nuevas**: `requests` y `hypothesis` ya están pinados
  (Req 10.3).
- **Sin secretos** en el repositorio, en logs ni en el chat; la API key solo por
  `OPENALEX_API_KEY` (Req 6.4, 7.4, 10.6).
- Todo lo no confirmado por SAO queda marcado como `PENDING_VALIDATION` (Req 11).

### Convenciones

- **Documentos**: estado **Propuesta V1** del Equipo_Proyecto a validar con SAO;
  no son criterios oficiales de SAO. Viven bajo `docs/bibliometrics/`.
- **Código**: **Python 3.12+**, `snake_case`, `pytest`, layout de `structure.md`.
- **Property tests**: **hypothesis** (ya pinado), **mínimo 100 iteraciones**, un
  único test por propiedad del diseño, etiquetado con el comentario
  `# Feature: estrategia-bibliometrica-api, Property N: <texto>`. Todos usan un
  **cliente HTTP simulado**: ningún test toca la red real.
- Las sub-tareas marcadas con `*` son **opcionales** (tests de ejemplo/edge
  cases accesorios). Crear/actualizar cada documento, el cambio de código y los
  property tests de las propiedades del diseño **no** son opcionales.

## Tasks

- [x] 1. Fase 1 — Documentación de la estrategia bibliométrica
  - [x] 1.1 Escribir la Estrategia de Búsqueda (`search-strategy.md`, NUEVO)
    - Crear `docs/bibliometrics/search-strategy.md` con estado **Propuesta V1**
      del Equipo_Proyecto sujeta a validación por SAO.
    - Documentar alcance y cobertura: período **2020–2030 inclusive** y cobertura
      **internacional con prioridad en Colombia**, sin limitar a Colombia.
    - Documentar el foco temático (conservación de aves: amenazas, protección,
      monitoreo, restauración y gestión de especies y de hábitats) y los idiomas
      objetivo **español, inglés y portugués** cuando la fuente permita filtrar.
    - Diferenciar de forma explícita **Corpus_Recuperado vs. Corpus_Analitico**.
    - Documentar las cinco **Familia_Ecuaciones** (aves + conservación; aves +
      conservación + Colombia; aves + amenazas o pérdida de hábitat; aves +
      biodiversidad, áreas protegidas o restauración; aves + especies amenazadas
      o monitoreo de poblaciones), cada una con **sinónimos y operador `OR`**;
      aclarar que una ecuación no exige que todos los términos aparezcan a la vez
      y que la **sintaxis se adapta a cada fuente** (instanciación en OpenAlex:
      `search` + `filter`), marcando las ecuaciones como propuesta del equipo.
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.2 Ampliar los criterios de inclusión/exclusión (`inclusion-exclusion-criteria.md`, ACTUALIZAR)
    - Actualizar `docs/bibliometrics/inclusion-exclusion-criteria.md` conservando
      su estructura V1, sin romper el contenido existente.
    - Añadir como incluibles los registros de aves + conservación que aborden
      amenazas, protección, manejo, restauración o monitoreo; la elegibilidad de
      registros **internacionales** relevantes y de documentos **científicos y
      técnicos**.
    - Documentar como excluibles los duplicados, los registros sin información
      suficiente y las menciones incidentales de aves sin relación con
      conservación; reforzar la regla de **`PENDIENTE_REVISIÓN`** para casos
      dudosos en lugar de exclusión automática.
    - Añadir una sección que distinga de forma explícita **Corpus_Recuperado vs.
      Corpus_Analitico**, alineada con la Estrategia de Búsqueda.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 1.3 Definir la Clasificación Geográfica (`geographic-classification.md`, NUEVO)
    - Crear `docs/bibliometrics/geographic-classification.md` con estado
      **Propuesta V1** sujeta a validación por SAO.
    - Definir las categorías `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS` y
      `SIN_DETERMINAR`.
    - Documentar que la clasificación se basa en el **Territorio_Estudiado** (área
      objeto del estudio), **no** únicamente en la afiliación institucional de los
      autores; y la regla de no invención: si el territorio no se puede determinar
      a partir de los metadatos, se asigna `SIN_DETERMINAR` sin inventar
      territorio.
    - Aclarar que en este spec **no** se implementa un clasificador geográfico;
      solo se define la metodología.
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 1.4 Revisar el Contrato de Datos (`article-data-contract.md`, ACTUALIZAR, propuesta V1)
    - Actualizar `docs/bibliometrics/article-data-contract.md` como **propuesta
      V1**, **sin** cambiar el esquema de código `ArticleRecord` en este spec.
    - Confirmar que V1 ya permite registrar identificador, título, autores, año,
      DOI, resumen, palabras clave, fuente, fecha de extracción, estado de
      procesamiento, estado de inclusión, motivo de exclusión y clasificación por
      OFC.
    - Añadir una sección "Propuesta V1, evolución futura" con los campos
      **opcionales** propuestos: `geographic_scope` y `studied_territory`
      (Clasificacion_Geografica y Territorio_Estudiado), `source_query` /
      `retrieved_by_query` (consulta que recuperó el registro) y `document_type`
      (tipo de documento).
    - Documentar el **registro único por publicación** (una publicación en varias
      consultas o fuentes = un único registro bibliográfico), alineado con el
      `article_id` determinista existente; proponer entidades/relaciones
      adicionales **solo** si son necesarias para la trazabilidad, sin cambios
      innecesarios de arquitectura; registrar las adiciones como propuesta V1.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 2. Fase 2 — Especificación de la integración por API key (Req 6)
  - [x] 2.1 Escribir la Especificación de integración por API key (`api-key-integration.md`, NUEVO)
    - Crear `docs/bibliometrics/api-key-integration.md` con una sección
      **genérica** (plantilla para cualquier `Proveedor_API`) que cubra los **12
      puntos** del Req 6.1: servicio; autenticación requerida; variables de
      entorno; endpoints; parámetros de búsqueda; filtros por año, idioma y tipo
      de documento cuando existan; paginación; límites de solicitudes y de
      resultados; cuotas y posibles costos; manejo de errores, reintentos y
      límites de velocidad; campos bibliográficos devueltos; y condiciones de uso
      y restricciones de almacenamiento.
    - **Instanciar en OpenAlex** como único `Proveedor_API` implementado:
      autenticación **únicamente** por `OPENALEX_API_KEY`, que **nunca** se
      almacena en código, documentación pública, frontend ni repositorio; la key
      se pasa como parámetro de query `api_key`; sin key la paginación por cursor
      devuelve HTTP 401 al pasar de la primera página (razón del cambio de
      código). Documentar cuotas/costos aproximados **según el proveedor** y
      marcar lo no confirmado como `PENDING_VALIDATION`, sin inventar cifras.
    - Documentar que una API basada en **metadatos ≠ texto completo** (no se
      asumen capacidades no confirmadas) y marcar `Scopus`, `Wiley` y `UNAL
      OAI-PMH` como `PENDING_VALIDATION`, **sin** implementarlos en este spec.
    - Citar las fuentes oficiales de OpenAlex consultadas, con nota de que el
      contenido fue reformulado por restricciones de licencia.
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 2.2 Implementar el soporte de `OPENALEX_API_KEY` en el conector (ÚNICO CAMBIO DE CÓDIGO)
    - En `bibliometrics/ingestion/openalex_api_client.py`: añadir la constante
      `API_KEY_ENV_VAR = "OPENALEX_API_KEY"` junto a `MAILTO_ENV_VAR`; añadir
      `resolve_api_key()` (espejo de `resolve_mailto()`): lee del entorno, `None`
      si ausente/vacía/solo-espacios (se recorta), **nunca** de archivo
      versionado; extender `ApiConfig` con `api_key: Optional[str] = None` (sin
      validaciones que puedan filtrar el valor); en `_build_params` añadir
      `params["api_key"] = config.api_key` **solo si** `config.api_key` es no
      vacío.
    - En `bibliometrics/pipelines/process_openalex_api.py`: importar
      `resolve_api_key` desde `ingestion.openalex_api_client` y, en
      `_build_config`, poblar `api_key=resolve_api_key()` junto a
      `mailto=resolve_mailto()`. **No** cambiar el default de `--max-results`
      (sigue `None`); el 5.000 se documenta como recomendado (ver tarea 3.1) y
      cambiar el default queda `PENDING_VALIDATION`.
    - Protección del secreto: asegurar que la key **nunca** aparece en logs ni en
      mensajes de error (`HttpError` y los `print` del pipeline referencian
      `status_code` / `Consulta` / página, **nunca** `config.api_key`).
    - No tocar la transformación `work → ArticleRecord`, el esquema `article_id`,
      el ritmo, los reintentos ni `OPENALEX_MAILTO`.
    - _Requirements: 7.1, 7.2, 7.3, 7.6_

  - [x] 2.3 Añadir el placeholder de `OPENALEX_API_KEY` a `.env.example`
    - Añadir a `.env.example` un `OPENALEX_API_KEY` como **placeholder comentado
      sin valor real**, análogo al bloque de `OPENALEX_MAILTO`, explicando que
      habilita la paginación por cursor y que se obtiene gratis en openalex.org;
      nunca versionar un valor real.
    - _Requirements: 7.7_

  - [x] 2.4 Property test — inclusión condicional del parámetro `api_key`
    - **Property 1: Inclusión condicional del parámetro `api_key`**
    - **Validates: Requirements 7.1, 7.2**
    - Generar `api_key` (incluidas `None`/vacía), `Consulta` y cursor aleatorios;
      afirmar que `_build_params` incluye `api_key` con el valor exacto **sii**
      `config.api_key` es no vacío, y que el resto de params (`search`, `filter`,
      `per_page`, `cursor`) es invariante en ambos casos. Cliente HTTP simulado;
      sin red real.

  - [x] 2.5 Property test — resolución de la API key desde el entorno
    - **Property 2: Resolución de la API key desde el entorno**
    - **Validates: Requirements 7.3**
    - `monkeypatch` del entorno con valores aleatorios (ausente, `""`, `"   "`,
      texto); afirmar que `resolve_api_key()` devuelve `None` cuando está
      ausente/vacía/espacios y el valor recortado cuando es no vacía; verificar
      que el valor proviene solo del entorno y que no se accede a disco.

  - [x] 2.6 Property test — el valor de la API key nunca se filtra en textos
    - **Property 3: El valor de la API key nunca se filtra en textos**
    - **Validates: Requirements 7.4**
    - Generar una key no trivial; forzar `HttpError` (401/429/permanente) y las
      rutas de error/resumen del pipeline con sesión simulada; recoger todos los
      textos emitidos (mensajes de `HttpError`, repr de excepciones de paginación
      y `print`) y afirmar que la key no aparece en ninguno. Sin red real.

  - [x]* 2.7 Tests de ejemplo / integración simulada del cambio de código
    - **Req 7.5**: sesión simulada de 2–3 páginas con `next_cursor`; con
      `api_key` en la config, afirmar que se recorren **todas** las páginas (no se
      corta en la primera) y que **cada** solicitud llevó `api_key`.
    - **Req 7.6**: no-regresión — `OPENALEX_MAILTO` sigue poblándose junto a
      `api_key`; transformación, ritmo y reintentos intactos.
    - **Req 7.7**: verificación de contenido de `.env.example` (placeholder
      comentado presente, sin valor real).
    - Cliente HTTP simulado; ningún test toca la red real.
    - _Requirements: 7.5, 7.6, 7.7_

- [x] 3. Fase 3 — Especificación del límite de recuperación por corrida
  - [x] 3.1 Escribir la Especificación de límites y Resumen de Ejecución (`retrieval-limits.md`, NUEVO)
    - Crear `docs/bibliometrics/retrieval-limits.md` con el `Limite_Recuperacion`:
      valor predeterminado **5.000** resultados por `Corrida_Ingesta`,
      **configurable** por corrida; comportamiento de corte (al alcanzar el
      límite, la corrida detiene la recuperación sin excederlo, apoyado en el
      corte por `max_results` existente); y corridas incrementales permitidas.
    - Documentar el `Resumen_Ejecucion` por corrida (recuperados, nuevos,
      duplicados y errores), con el mapeo conceptual a `_IngestStats` existente,
      y la trazabilidad de cada corrida.
    - Aclarar de forma explícita que el `Limite_Recuperacion` es un **control
      operativo por corrida**, **no** el límite del `Corpus_Analitico`; documentar
      el 5.000 como **valor recomendado del flag `--max-results`** sin cambiar el
      default del código, y dejar el valor definitivo y la estrategia incremental
      como `PENDING_VALIDATION`.
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [x] 4. Fase 4 — Piloto, decisiones pendientes y guía
  - [x] 4.1 Escribir el Plan de Piloto Controlado (`pilot-plan.md`, NUEVO)
    - Crear `docs/bibliometrics/pilot-plan.md` como procedimiento **especificado,
      no ejecutado a escala**.
    - Especificar el uso de una o dos fuentes accesibles y un conjunto **reducido**
      de ecuaciones; los pasos (recuperación de metadatos → deduplicación →
      aplicación de los Criterios_Inclusion_Exclusion → Clasificacion_Geografica);
      la compatibilidad con la clasificación OFC existente **sin implementar** el
      clasificador; y que los registros de relevancia incierta se marcan
      `PENDIENTE_REVISIÓN`, nunca "incluido" automático.
    - Dejar explícito que el piloto se documenta como procedimiento y **no** se
      ejecuta como recolección masiva en este spec.
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 4.2 Escribir el listado de decisiones `PENDING_VALIDATION` (`pending-validation.md`, NUEVO)
    - Crear `docs/bibliometrics/pending-validation.md` con el listado explícito de
      decisiones para que SAO confirme antes de volverlas reglas rígidas: familias
      de ecuaciones (11.1); definición de relevancia temática (11.2);
      categorías/metodología de la Clasificacion_Geografica (11.3); campos
      añadidos al contrato, incluidos tipo de documento, consulta de origen,
      territorio estudiado y alcance geográfico (11.4); metodología/algoritmo OFC
      (11.5); incorporación de Scopus/Wiley/UNAL OAI-PMH (11.6); estrategia de
      deduplicación entre fuentes (11.7); y valor definitivo del
      `Limite_Recuperacion` + estrategia incremental (11.8).
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

  - [x] 4.3 Actualizar la guía de uso con `OPENALEX_API_KEY` (`consultar-openalex-api.md`, ACTUALIZAR)
    - Actualizar `docs/user-guide/consultar-openalex-api.md` para documentar el
      uso de `OPENALEX_API_KEY`: cómo obtener la key gratuita (openalex.org →
      Settings → API key), cómo exportarla por variable de entorno, que habilita
      la paginación por cursor completa (más allá de la primera página) y que
      **no** se guarda en el repositorio.
    - Referir la Especificación de integración por API key
      (`api-key-integration.md`) y el valor recomendado del `Limite_Recuperacion`
      (`retrieval-limits.md`).
    - _Requirements: 6.3, 6.4, 7.7_

- [x] 5. Checkpoint — cambio de código y documentación
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Verificación final
  - [x] 6.1 Correr la suite con cliente simulado y hacer smoke del pipeline sin red real
    - Ejecutar `pytest` de `bibliometrics` y del backend y corregir lo que falle;
      los property tests del cambio de código usan el **cliente HTTP simulado**:
      ningún test toca la red real.
    - Smoke del pipeline con sesión simulada o `python
      bibliometrics/pipelines/process_openalex_api.py --help` (sin ejecutar una
      consulta real contra OpenAlex ni consumir cuotas).
    - Confirmar por checklist que los documentos de las Fases 1–4 cubren sus
      criterios de aceptación; dejar el estado verde.
    - Ensure all tests pass, ask the user if questions arise.
    - _Requirements: 7.1, 7.4, 7.5, 7.6_

## Notes

- Tareas marcadas con `*` son opcionales (tests de ejemplo/edge cases accesorios)
  y pueden omitirse para un MVP más rápido; las tareas núcleo (crear/actualizar
  cada documento, el cambio de código y los property tests de las propiedades del
  diseño) nunca se marcan así.
- **Ninguna tarea ejecuta búsquedas reales ni consume cuotas de API**; el piloto
  es un documento (Req 9.5, 10.1). El smoke de la tarea 6.1 usa sesión simulada o
  `--help`.
- Las tres propiedades del diseño (1, 2, 3) tienen exactamente un property test
  cada una (tareas 2.4, 2.5, 2.6), con `hypothesis` (≥100 iteraciones) y el
  comentario etiqueta `# Feature: estrategia-bibliometrica-api, Property N:
  <texto>`; todos usan cliente HTTP simulado.
- La "verificación" de los entregables de documentación (Req 1–6, 8–11) es una
  **lista de comprobación de contenido**, no tests automatizados.
- No se modifica el servicio consolidado, el endpoint, la vista ni el
  procesamiento del Boletín SAO (Req 10.2); tampoco `_common.py`,
  `article_record.py`, la transformación `work → ArticleRecord`, el esquema
  `article_id`, el ritmo, los reintentos, `OPENALEX_MAILTO` ni la vía PoP
  (Req 7.6).
- Sin dependencias nuevas (`requests` y `hypothesis` ya pinados — Req 10.3). Sin
  secretos en repo/logs/chat; la API key solo por `OPENALEX_API_KEY` (Req 6.4,
  7.4, 10.6).
- Los documentos son **Propuesta V1** del Equipo_Proyecto a validar con SAO; lo
  no confirmado queda en `pending-validation.md` como `PENDING_VALIDATION`.
- El cambio de default de `--max-results` a 5.000 NO se hace aquí: queda
  `PENDING_VALIDATION` (Req 11.8); el 5.000 se documenta como valor recomendado.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "2.1", "3.1", "4.1", "4.2"] },
    { "id": 1, "tasks": ["2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "2.5", "2.6", "2.7", "4.3"] },
    { "id": 3, "tasks": ["6.1"] }
  ]
}
```
