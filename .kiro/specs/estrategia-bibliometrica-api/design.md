# Design Document

Estrategia bibliométrica e integración por API key (Componente B)

## Overview

Este spec es, ante todo, de **formalización, análisis técnico y
especificación**. La enorme mayoría de sus entregables son **documentos** que
consolidan la estrategia bibliométrica del Componente B y especifican cómo
integrar fuentes mediante **API key**, instanciando el diseño en **OpenAlex**.
Hay un **único cambio de código acotado**: añadir soporte de la variable de
entorno `OPENALEX_API_KEY` al conector OpenAlex ya existente, para habilitar la
paginación por cursor más allá de la primera página.

**En este spec no se ejecuta una recolección masiva ni se consumen cuotas** más
allá de lo mínimo de un piloto que aquí solo se *especifica* (no se ejecuta a
escala). El diseño respeta todas las restricciones del Requisito 10 y del
steering del Componente B.

### Naturaleza documentación-primero

El trabajo se organiza en cuatro fases heredadas del requirements:

1. Formalizar la estrategia bibliométrica (documentación).
2. Especificar la integración por API key (documentación + diseño genérico
   instanciado en OpenAlex).
3. Especificar límites de recuperación por corrida (documentación apoyada en
   código existente).
4. Especificar un piloto controlado (descrito, no ejecutado a escala).

### Mapa de entregables

La tabla separa explícitamente lo que es **DOCUMENTO** de lo que es **CÓDIGO**.
Todos los documentos viven bajo `docs/bibliometrics/` salvo donde se indique.

| # | Entregable | Tipo | Archivo | Requisitos |
|---|-----------|------|---------|------------|
| 1 | Estrategia de Búsqueda | Documento (nuevo) | `docs/bibliometrics/search-strategy.md` | 1, 2 |
| 2 | Ampliación de criterios de inclusión/exclusión | Documento (actualizar) | `docs/bibliometrics/inclusion-exclusion-criteria.md` | 3 |
| 3 | Definición de Clasificación Geográfica | Documento (nuevo) | `docs/bibliometrics/geographic-classification.md` | 4 |
| 4 | Revisión propuesta del Contrato de Datos | Documento (actualizar, como propuesta V1) | `docs/bibliometrics/article-data-contract.md` | 5 |
| 5 | Especificación de integración por API key | Documento (nuevo) | `docs/bibliometrics/api-key-integration.md` | 6 |
| 6 | Especificación del Límite de Recuperación y Resumen de Ejecución | Documento (nuevo, o sección en estrategia) | `docs/bibliometrics/retrieval-limits.md` | 8 |
| 7 | Plan de Piloto Controlado | Documento (nuevo) | `docs/bibliometrics/pilot-plan.md` | 9 |
| 8 | Listado de decisiones `PENDING_VALIDATION` | Documento (nuevo) | `docs/bibliometrics/pending-validation.md` | 11 |
| — | **ÚNICO CAMBIO DE CÓDIGO**: soporte de `OPENALEX_API_KEY` en el conector | Código | `bibliometrics/ingestion/openalex_api_client.py`, `bibliometrics/pipelines/process_openalex_api.py`, `.env.example` | 7 |

> Estado global: **Propuesta V1**. Las ecuaciones, los campos del contrato, los
> criterios y la clasificación geográfica son **propuesta del Equipo_Proyecto a
> validar con SAO**, no criterios oficiales de SAO.

### Principios heredados del steering

- **No inventar datos ni relevancia.** Campo ausente → `None`; relevancia/OFC no
  se resuelven automáticamente (`PENDING_VALIDATION`).
- **Trazabilidad y reproducibilidad.** Cada registro rastreable hasta su consulta
  y fuente; cada corrida con su `Resumen_Ejecucion`.
- **`data/raw/` inmutable**; el pipeline solo escribe en `data/processed/`.
- **Sin secretos** en el repositorio, en logs ni en el chat.
- **Sin dependencias nuevas** (`requests` ya está pinado).
- **El frontend solo consulta** resultados ya procesados; no se toca.
- **Metadatos ≠ texto completo**: no se atribuyen capacidades no confirmadas a la
  fuente.

## Architecture

El spec encaja en el **Componente B sin tocar** el `Servicio_Consolidado`, el
`Endpoint_Consolidado`, la `Vista_Bibliometria` ni el procesamiento del **Boletín
SAO**. El flujo `Dataset → data/processed/ → backend → frontend` **no se
modifica**: el backend ya descubre dinámicamente las carpetas bajo
`data/processed/` y agrupa por el campo `source`, de modo que OpenAlex sigue
apareciendo en el consolidado sin cambios de código.

El cambio de código se limita a la **capa HTTP del conector OpenAlex** (añadir el
parámetro `api_key` cuando la variable de entorno está presente) y a su cableado
desde el pipeline. Nada más de la lógica existente cambia.

```
  DOCUMENTACIÓN (mayoría del spec)            ÚNICO CAMBIO DE CÓDIGO            SIN CAMBIOS (ya existente)
  ---------------------------------           ----------------------            --------------------------

  Estrategia de Búsqueda  (Req 1,2)
  Criterios ampliados     (Req 3)
  Clasificación Geográfica(Req 4)
  Revisión Contrato Datos (Req 5)
  Espec. API key          (Req 6) ---------->  openalex_api_client.py
  Límites + Resumen Ejec. (Req 8)               + API_KEY_ENV_VAR
  Plan de Piloto          (Req 9)               + resolve_api_key()
  PENDING_VALIDATION      (Req 11)              + ApiConfig.api_key
                                                + _build_params(api_key si existe)
                                                       |
                                                       v
                                               process_openalex_api.py
                                                + _build_config() usa resolve_api_key()
                                                       |
                                                       v
                                               con key: cursor pagina > 1 página (desaparece 401)
                                               sin key: comportamiento actual intacto
                                                       |
                                                       v
                                               data/processed/openalex/ ----> BibliometriaService (SIN CAMBIOS)
                                                                                    |
                                                                                    v
                                                                         GET /bibliometria/resumen (SIN CAMBIOS)
                                                                                    |
                                                                                    v
                                                                         Vista_Bibliometria (SIN CAMBIOS)
```

Diagrama conceptual del spec (de la estrategia al piloto):

```mermaid
flowchart TD
    A[Estrategia bibliométrica\n(documentos: búsqueda, criterios,\ngeografía, contrato)] --> B[Especificación de\nintegración por API key\n(genérica + OpenAlex)]
    B --> C[Cambio de código:\nOPENALEX_API_KEY en el conector]
    C --> D[Piloto controlado\n(especificado, no ejecutado a escala)]
    D -. valida .-> A
    C --> E[(data/processed/openalex/)]
    E --> F[Backend consolidado\n(SIN CAMBIOS)]
    F --> G[Frontend\n(SIN CAMBIOS)]
```

## Components and Interfaces

### Componentes y entregables de documentación

Para cada documento se diseña su **estructura y contenido propuesto**, no su
volcado completo. Cada documento declara su estado **Propuesta V1** y, donde
corresponda, remite al listado `PENDING_VALIDATION`.

### 1. Estrategia de Búsqueda — `docs/bibliometrics/search-strategy.md` (Req 1, 2)

Estructura propuesta:

1. **Objetivo y estado** (Propuesta V1 del Equipo_Proyecto; Req 1.6, 2.5).
2. **Alcance y cobertura**: periodo **2020–2030 inclusive** (Req 1.1); cobertura
   **internacional con prioridad en Colombia**, sin limitar a Colombia (Req 1.2).
3. **Foco temático**: conservación de aves incluyendo amenazas, protección,
   monitoreo, restauración y gestión de especies y de hábitats (Req 1.3).
4. **Idiomas objetivo**: español, inglés y portugués, cuando la fuente permita
   filtrar por idioma (Req 1.4).
5. **Corpus recuperado vs. corpus analítico**: definición y diferencia explícita
   (Req 1.5) — ver también la sección de Data Models.
6. **Familias de ecuaciones** (Req 2.1), cada una con **sinónimos y operador
   `OR`** (Req 2.2):
   - aves + conservación;
   - aves + conservación + Colombia;
   - aves + amenazas o pérdida de hábitat;
   - aves + biodiversidad, áreas protegidas o restauración;
   - aves + especies amenazadas o monitoreo de poblaciones.
7. **Semántica de las ecuaciones**: una ecuación **no** exige que todos los
   términos aparezcan simultáneamente (Req 2.3); la **sintaxis se adapta a cada
   fuente** sin asumir operadores o campos idénticos (Req 2.4). Se documenta
   cómo se instancia cada familia en OpenAlex (parámetro `search` + `filter`),
   diferenciándolo de otras fuentes futuras.
8. **Estado de propuesta**: las ecuaciones son propuesta del equipo, no criterio
   oficial de SAO (Req 2.5), y quedan listadas en `pending-validation.md`.

### 2. Ampliación de criterios de inclusión/exclusión — `inclusion-exclusion-criteria.md` (Req 3)

Se **actualiza** el documento existente conservando su estructura V1 y añadiendo:

- Inclusión explícita de registros de aves + conservación que aborden amenazas,
  protección, manejo, restauración o monitoreo (Req 3.1).
- Elegibilidad de registros **internacionales** relevantes (Req 3.2) y de
  documentos **científicos y técnicos** (Req 3.3).
- Exclusión de duplicados, registros sin información suficiente y menciones
  incidentales de aves sin relación con conservación (Req 3.4).
- Regla de **`PENDIENTE_REVISIÓN`** para casos dudosos en lugar de exclusión
  automática (Req 3.5) — ya presente en V1, se refuerza.
- Nueva sección que distingue **Corpus_Recuperado vs. Corpus_Analitico**
  (Req 3.6), alineada con la Estrategia de Búsqueda.

### 3. Definición de Clasificación Geográfica — `geographic-classification.md` (Req 4)

Estructura propuesta:

1. **Categorías**: `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS`, `SIN_DETERMINAR`
   (Req 4.1).
2. **Base de la clasificación**: el **Territorio_Estudiado** (área objeto del
   estudio), **no** únicamente la afiliación institucional de los autores
   (Req 4.2).
3. **Regla de no invención**: si el territorio no puede determinarse a partir de
   los metadatos, se asigna `SIN_DETERMINAR` sin inventar territorio (Req 4.3).
4. **Estado**: Propuesta V1 a validar con SAO (Req 4.4); categorías y metodología
   listadas en `pending-validation.md`.

> No se implementa un clasificador geográfico en este spec; solo se define.

### 4. Revisión propuesta del Contrato de Datos — `article-data-contract.md` (Req 5)

Se **revisa** el contrato (actualización documental, **propuesta V1**, sin
cambiar el esquema de código `ArticleRecord` en este spec):

- Confirmar que V1 ya permite registrar: identificador, título, autores, año,
  DOI, resumen, palabras clave, fuente, fecha de extracción, estado de
  procesamiento, estado de inclusión, motivo de exclusión y clasificación por
  OFC (Req 5.1) — todos ya existen en el contrato.
- **Campos nuevos propuestos** (sección "Propuesta V1, evolución futura"), no
  obligatorios:
  - `geographic_scope`: la `Clasificacion_Geografica` del registro (Req 5.2);
  - `studied_territory`: el `Territorio_Estudiado` (Req 5.2);
  - `source_query` / `retrieved_by_query`: la consulta que recuperó el registro
    (Req 5.3);
  - `document_type`: tipo de documento del registro (Req 5.4).
- **Registro único por publicación**: una publicación que aparece en varias
  consultas o fuentes se identifica como **un único** registro bibliográfico
  (Req 5.5) — alineado con el `article_id` determinista ya existente.
- Proponer entidades/relaciones adicionales **solo si** son necesarias para la
  trazabilidad, sin cambios innecesarios de arquitectura (Req 5.6).
- Registrar las adiciones como **propuesta V1** sujeta a validación (Req 5.7);
  todas en `pending-validation.md`.

### 5. Especificación de integración por API key — `api-key-integration.md` (Req 6)

Documento genérico instanciado en OpenAlex. Sección **genérica** (plantilla para
cualquier `Proveedor_API`) con los **12 puntos** del Req 6.1:

1. Servicio; 2. Autenticación requerida; 3. Variables de entorno; 4. Endpoints;
5. Parámetros de búsqueda; 6. Filtros por año, idioma y tipo de documento cuando
existan; 7. Paginación; 8. Límites de solicitudes y de resultados; 9. Cuotas y
posibles costos; 10. Manejo de errores, reintentos y límites de velocidad;
11. Campos bibliográficos devueltos; 12. Condiciones de uso y restricciones de
almacenamiento.

**Instanciación en OpenAlex** (único `Proveedor_API` implementado — Req 6.2),
con los hallazgos técnicos confirmados (fuentes oficiales de OpenAlex, 2026):

- **Autenticación**: la API key se provee **únicamente** por la variable de
  entorno `OPENALEX_API_KEY` (Req 6.3) y **nunca** se almacena en código,
  documentación pública, frontend ni repositorio (Req 6.4). Se pasa a la API como
  parámetro de query `api_key`. La key gratuita se obtiene en openalex.org
  (Settings → API key) según el proveedor.
- **Paginación**: OpenAlex **exige** la API key gratuita para continuar la
  paginación por cursor más allá de la primera página: sin key, `cursor=*`
  funciona pero seguir `next_cursor` devuelve **HTTP 401**. Esta es la razón por
  la que hoy el conector recupera ~200 registros por búsqueda.
- **Cuotas y costos** (aproximados, *según el proveedor*; marcar lo no confirmado
  como `PENDING_VALIDATION`): sin key, cupo diario pequeño compartido por IP; con
  key gratuita, cupo diario mayor (del orden de ~USD 1/día de uso según el
  proveedor). No se inventan cifras exactas.
- **Campos devueltos**: esquema nativo de `work` (ya mapeado por el conector).
- **Metadatos ≠ texto completo**: una API basada en metadatos **no** implica
  acceso al texto completo; no se asumen capacidades no confirmadas (Req 6.6).
- **Otros proveedores** (`Scopus`, `Wiley`, `UNAL OAI-PMH`): se marcan como
  `PENDING_VALIDATION` y **no** se implementan en este spec (Req 6.5).

Fuentes consultadas (OpenAlex Help Center / docs oficiales, 2026):
[Authentication](https://help.openalex.org/api/authentication/),
[Paging](https://help.openalex.org/api/paging/),
[Quickstart](https://help.openalex.org/quickstart/). *Contenido reformulado para
cumplir con las restricciones de licencia.*

### 6. Especificación del Límite de Recuperación y Resumen de Ejecución — `retrieval-limits.md` (Req 8)

Estructura propuesta:

1. **Limite_Recuperacion**: valor predeterminado **5.000** resultados por
   `Corrida_Ingesta` (Req 8.1), **configurable** por corrida (Req 8.2).
2. **Comportamiento de corte**: al alcanzar el límite, la corrida **detiene** la
   recuperación sin excederlo (Req 8.3) — ya soportado por el corte en
   `max_results` del conector/pipeline.
3. **Corridas incrementales** permitidas (Req 8.4).
4. **Resumen_Ejecucion** por corrida: recuperados, nuevos, duplicados y errores
   (Req 8.5) — apoyado en `_IngestStats` existente (ver Data Models).
5. **Trazabilidad** de cada corrida (Req 8.6).
6. Aclaración explícita: el `Limite_Recuperacion` es un **control operativo por
   corrida**, **no** el límite del `Corpus_Analitico` (Req 8.7). Su valor
   definitivo y la estrategia incremental quedan en `pending-validation.md`.

### 7. Plan de Piloto Controlado — `pilot-plan.md` (Req 9)

Procedimiento **especificado, no ejecutado a escala** (Req 9.5):

1. Una o dos fuentes accesibles y un conjunto **reducido** de ecuaciones
   (Req 9.1).
2. Pasos: recuperación de metadatos → deduplicación → aplicación de criterios de
   inclusión/exclusión → clasificación geográfica (Req 9.2).
3. Compatibilidad con la clasificación OFC existente **sin implementar** el
   clasificador (Req 9.3).
4. Registros de relevancia incierta → `PENDIENTE_REVISIÓN`, nunca "incluido"
   automático (Req 9.4).

### 8. Listado de decisiones `PENDING_VALIDATION` — `pending-validation.md` (Req 11)

Listado explícito para que SAO confirme antes de volverlas reglas rígidas:
familias de ecuaciones (11.1), definición de relevancia temática (11.2),
categorías/metodología de clasificación geográfica (11.3), campos añadidos al
contrato incluidos tipo de documento, consulta de origen, territorio estudiado y
alcance geográfico (11.4), metodología/algoritmo OFC (11.5), incorporación de
Scopus/Wiley/UNAL OAI-PMH (11.6), estrategia de deduplicación entre fuentes
(11.7) y valor definitivo del `Limite_Recuperacion` + estrategia incremental
(11.8).

## Diseño del único cambio de código (Requirement 7)

Se añade soporte de `OPENALEX_API_KEY` al **conector OpenAlex existente**, de
forma **análoga a `OPENALEX_MAILTO`**, sin romper nada. Diseño mínimo e
incremental.

### En `bibliometrics/ingestion/openalex_api_client.py`

1. **Nueva constante** junto a `MAILTO_ENV_VAR`:
   ```python
   API_KEY_ENV_VAR = "OPENALEX_API_KEY"
   ```
2. **Nueva función** `resolve_api_key()`, espejo de `resolve_mailto()`:
   - lee `os.environ.get(API_KEY_ENV_VAR)`;
   - `None` si ausente; cadena vacía o solo espacios → `None` (se recorta);
   - **nunca** lee de un archivo versionado (Req 7.3).
   ```python
   def resolve_api_key() -> Optional[str]:
       value = os.environ.get(API_KEY_ENV_VAR)
       if value is None:
           return None
       value = value.strip()
       return value or None
   ```
3. **Extender `ApiConfig`** con un campo nuevo, opcional y con default seguro:
   ```python
   api_key: Optional[str] = None
   ```
   No se añaden validaciones que puedan filtrar el valor; `__post_init__` no lo
   imprime ni lo incluye en mensajes.
4. **`_build_params`** añade el parámetro `api_key` **solo si está presente**,
   igual que ya hace con `mailto`:
   ```python
   if config.api_key:
       params["api_key"] = config.api_key
   ```
   Con key presente, la paginación por cursor continúa más allá de la primera
   página (desaparece el 401 — Req 7.1, 7.5). Sin key, el comportamiento actual
   se conserva idéntico (Req 7.2).

### En `bibliometrics/pipelines/process_openalex_api.py`

5. **`_build_config`** puebla el nuevo campo con `resolve_api_key()`, junto al
   `mailto` ya existente (Req 7.6 conserva `OPENALEX_MAILTO`):
   ```python
   return ApiConfig(
       per_page=args.per_page,
       max_results=args.max_results,
       pace_seconds=args.pace_seconds,
       max_retries=args.max_retries,
       mailto=resolve_mailto(),
       api_key=resolve_api_key(),
   )
   ```
   Se importa `resolve_api_key` desde `ingestion.openalex_api_client`.

### Protección del secreto (Req 7.4)

La key **nunca** debe aparecer en logs ni en mensajes de error:

- `_build_params` no imprime nada; solo arma el dict.
- `HttpError` ya construye su mensaje con `status_code`, `transient` y el término
  de la `Consulta` — **no** incluye los params, por lo que no filtra la key. Se
  mantiene así.
- Los `print` del pipeline (`_iter_consulta_pages`, `_print_ingest_summary`,
  mensajes de error) referencian la `Consulta`, la página y el `status_code`,
  **no** el valor de la key. Se revisa que ninguno imprima `config.api_key`.

### En `.env.example` (Req 7.7)

Añadir `OPENALEX_API_KEY` como **placeholder comentado sin valor real**, análogo
al bloque de `OPENALEX_MAILTO`, explicando que habilita la paginación por cursor
y que se obtiene gratis en openalex.org.

### Decisión de diseño: el Límite por corrida (5.000)

El default de `max_results` representa, **a nivel de documentación y plan**, el
`Limite_Recuperacion` recomendado de **5.000** por corrida. **Decisión explícita
para no romper nada existente**:

- **Preferido**: documentar 5.000 como el **valor recomendado del flag
  `--max-results`** en la guía y en `retrieval-limits.md`, sin cambiar
  silenciosamente el default del código (que hoy es `None` = sin límite).
- Si SAO confirma que 5.000 debe ser el default efectivo del **pipeline**
  (`process_openalex_api.py`), se cambia **solo** el `default` del argparse de
  `--max-results` en el pipeline, dejando `iter_works` intacto. Este cambio de
  default queda marcado como `PENDING_VALIDATION` (Req 11.8) para evitar alterar
  el comportamiento del conector o de otros consumidores.

> No se modifica `_common.py`, ni `article_record.py`, ni la transformación
> `work → ArticleRecord`, ni el esquema de `article_id`, ni la vía PoP.

## Data Models

Este spec **no cambia** el esquema de código `ArticleRecord`. Define/propone
modelos a nivel de **documentación** y describe la estructura ya existente que se
reutiliza.

### Campos propuestos del Contrato (propuesta V1, NO obligatorios)

| Campo | Obligatoriedad | Descripción | Req |
|-------|----------------|-------------|-----|
| `geographic_scope` | Opcional (propuesta V1) | `COLOMBIA` / `INTERNACIONAL` / `MULTIPAIS` / `SIN_DETERMINAR`. | 5.2, 4.1 |
| `studied_territory` | Opcional (propuesta V1) | Territorio_Estudiado; `None` si no determinable (no inventar). | 5.2, 4.3 |
| `source_query` / `retrieved_by_query` | Opcional (propuesta V1) | Consulta que recuperó el registro. | 5.3 |
| `document_type` | Opcional (propuesta V1) | Tipo de documento del registro. | 5.4 |

Estos campos se documentan como propuesta futura en `article-data-contract.md`;
no se convierten en obligatorios ni se implementan en el código V1.

### Resumen_Ejecucion (apoyado en `_IngestStats` existente)

El pipeline ya define `_IngestStats` con `works_recuperados`,
`paginas_consultadas`, `errores` y `paginas_con_error`, y lo imprime en
`_print_ingest_summary`. Como **base** del `Resumen_Ejecucion` por corrida
(Req 8.5), se documenta el mapeo conceptual:

| Concepto `Resumen_Ejecucion` | Fuente en código existente | Nota |
|------------------------------|----------------------------|------|
| Recuperados | `_IngestStats.works_recuperados` | works crudos recuperados. |
| Nuevos | `len(records)` no duplicados tras `mark_duplicates` | registros no marcados `is_duplicate`. |
| Duplicados | registros con `is_duplicate = true` | de `mark_duplicates`. |
| Errores | `_IngestStats.errores` (+ `paginas_con_error`) | páginas con reintentos agotados / works descartados. |

La formalización de "nuevos vs. duplicados" en el resumen impreso es un ajuste
**documental/menor** derivado de datos ya disponibles; no altera la lógica de
deduplicación ni de corte.

### ApiConfig (tras el cambio de código)

`ApiConfig` gana un único campo `api_key: Optional[str] = None`; el resto
(`per_page`, `max_results`, `pace_seconds`, `max_retries`, `backoff_base`,
`mailto`) permanece sin cambios.

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en todas
las ejecuciones válidas de un sistema: una afirmación formal de lo que el sistema
debe hacer. Las propiedades son el puente entre una especificación legible por
humanos y una garantía de corrección verificable por máquina.*

Las propiedades aplican **solo al único cambio de código (Req 7)**, que es lógica
pura (construcción de parámetros y resolución de una variable de entorno). Todos
los tests usan un **cliente HTTP simulado**; ninguno toca la red real. Los
requisitos de documentación (1–6, 8–11) se verifican por **revisión/checklist de
contenido**, no por property-based testing.

### Property 1: Inclusión condicional del parámetro `api_key`

*Para cualquier* `ApiConfig` y *cualquier* `Consulta` y cursor, `_build_params`
incluye la clave `api_key` con exactamente el valor de `config.api_key` **si y
solo si** `config.api_key` es una cadena no vacía; cuando `api_key` es `None` o
vacía, la clave `api_key` **no** aparece, y el resto de parámetros (`search`,
`filter`, `per_page`, `cursor`) se mantiene en ambos casos.

**Validates: Requirements 7.1, 7.2**

### Property 2: Resolución de la API key desde el entorno

*Para cualquier* valor de la variable de entorno `OPENALEX_API_KEY`,
`resolve_api_key()` devuelve `None` cuando la variable está ausente, vacía o
contiene solo espacios, y devuelve el valor recortado cuando es no vacía; la
función obtiene el valor únicamente del entorno del proceso y nunca lee de un
archivo.

**Validates: Requirements 7.3**

### Property 3: El valor de la API key nunca se filtra en textos

*Para cualquier* API key, ninguno de los textos emitidos por el conector o el
pipeline (mensajes de `HttpError`, representación de excepciones de paginación y
mensajes de error/resumen impresos) contiene el valor literal de la key, incluso
cuando se provocan errores HTTP (401/429/permanente) durante la paginación.

**Validates: Requirements 7.4**

## Error Handling

El conector ya maneja reintentos de errores transitorios (429/5xx) con espera
creciente, errores permanentes, works malformados y la falta de conectividad
inicial. Este spec añade/especifica el manejo relativo a la API key:

- **401 por falta de key en la paginación**: al seguir `next_cursor` sin key,
  OpenAlex responde HTTP 401. El conector lo trata como `HttpError` permanente
  (no es 429 ni 5xx), registra la `Consulta` y la página afectada, conserva lo ya
  recuperado y continúa con el resto. El mensaje debe ser **comprensible** y
  sugerir configurar `OPENALEX_API_KEY`, **sin exponer** ningún valor de key.
- **Agotamiento de cuota / 429 diario**: se reintenta como transitorio hasta
  `max_retries`; agotados los reintentos, se registra el error por página y la
  corrida continúa/termina conservando lo recuperado. El mensaje no incluye la
  key.
- **Sin conectividad**: comportamiento existente (abortar sin escribir dataset en
  la primera solicitud; a mitad de corrida, conservar lo recuperado).
- **Regla transversal**: la key **nunca** aparece en mensajes de registro ni de
  error (Req 7.4) — ver Property 3.

No se añaden reintentos nuevos; solo se cubre que la ausencia de key produzca un
mensaje claro y seguro.

## Testing Strategy

### Enfoque dual

- **Property-based tests** (solo Req 7): propiedades universales sobre la lógica
  pura del parámetro `api_key` y la resolución del entorno.
- **Tests de ejemplo / integración simulada** (Req 7.5, 7.6): sesión HTTP
  simulada multipágina y no-regresión.
- **Revisión de contenido / checklist** (Req 1–6, 8–11): la "verificación" de los
  entregables de documentación es una lista de comprobación de contenido, no
  tests automatizados.

### Property-based testing (aplica — lógica pura)

- Biblioteca: **Hypothesis** (ya usada en el proyecto; sin dependencias nuevas).
- **Mínimo 100 iteraciones** por property test.
- Un **único** property test por propiedad del diseño.
- Etiqueta en cada test: `# Feature: estrategia-bibliometrica-api, Property N: {texto}`.
- **Cliente HTTP simulado**: ningún test realiza solicitudes de red reales. La
  `session` se inyecta por el parámetro existente de `run_pipeline` / las
  funciones de fetch.

Cobertura de propiedades:

- **Property 1** → genera `api_key` (incluida `None`/vacía), `Consulta` y cursor
  aleatorios; afirma la presencia/ausencia de `api_key` y la invariancia del
  resto de parámetros.
- **Property 2** → `monkeypatch` del entorno con valores aleatorios (ausente,
  `""`, `"   "`, texto); afirma `None` vs. valor recortado; verifica que no se
  accede a disco.
- **Property 3** → genera una key no trivial; fuerza `HttpError` (401/429/
  permanente) y las rutas de error del pipeline con sesión simulada; recoge todos
  los textos emitidos y afirma que la key no aparece en ninguno.

### Tests de ejemplo / integración simulada

- **Req 7.5**: sesión simulada de 2–3 páginas con `next_cursor`; con `api_key` en
  la config, afirmar que se recorren **todas** las páginas (no se corta en la
  primera) y que **cada** solicitud llevó `api_key`. La paginación por cursor ya
  tiene cobertura del spec previo; aquí solo se valida el delta.
- **Req 7.6**: no-regresión — `OPENALEX_MAILTO` sigue poblándose junto a
  `api_key`; la transformación `work → ArticleRecord`, el ritmo y los reintentos
  no se tocan.
- **Req 7.7**: verificación de contenido de `.env.example` (placeholder comentado
  presente, sin valor real).

### Verificación de los entregables de documentación (checklist)

Para los Req 1–6, 8–11 se usa una **lista de comprobación** por documento: cada
criterio de aceptación corresponde a un ítem verificable del contenido (p. ej.
"la Estrategia_Busqueda documenta el periodo 2020–2030", "la Especificacion_API_Key
lista los 12 puntos del Req 6.1"). No se escriben tests unitarios para el
contenido documental.
