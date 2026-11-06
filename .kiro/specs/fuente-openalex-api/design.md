# Design Document

Fuente OpenAlex por API (consulta directa, Componente B)

## Overview

Este diseño reemplaza el paso **manual** de exportación con Publish or Perish
(PoP) del spec hermano `fuente-openalex` por un **conector que consulta
directamente la API pública y gratuita de OpenAlex** (https://api.openalex.org,
sin API key). Un **único comando de línea de comandos** consulta la API, pagina
los resultados, transforma cada `work` al **Article Data Contract V1** y escribe
el `Dataset_Procesado` en `data/processed/openalex/` (JSON + CSV).

Ambos specs producen **el mismo `Dataset_Procesado`** para la fuente OpenAlex;
la vía por API reemplaza la vía manual. El consolidado no distingue cómo se
obtuvo el dataset: ambas rutas escriben en la misma carpeta, con el mismo campo
`source = "OpenAlex"` y el mismo esquema de `article_id` (prefijo `oa-`), de modo
que los registros obtenidos por API y por PoP se cuentan como **una sola fuente**
y se deduplican juntos.

El alcance real del spec es acotado y es una **extensión/espejo deliberado** de
infraestructura ya probada, no una arquitectura nueva:

- Un **conector de API nuevo** (`bibliometrics/ingestion/openalex_api_client.py`)
  que consulta el endpoint `works`, pagina con cursor, filtra por año en la API,
  envía opcionalmente el `mailto` del "polite pool", aplica un ritmo de
  solicitudes configurable, reintenta errores transitorios con espera creciente y
  maneja la ausencia de conectividad inicial.
- Una **transformación `work` (JSON nativo de la API) → `ArticleRecord`**, que es
  distinta del mapeo del export PoP (la API devuelve el esquema nativo de
  OpenAlex, con objetos anidados y el `abstract` como índice invertido).
- Un **pipeline/CLI nuevo** (`bibliometrics/pipelines/process_openalex_api.py`)
  que ejecuta una o varias `Consulta`s, combina resultados, aplica
  `validate_period` + `mark_duplicates` (reutilizando `_common.py` sin tocarlo) y
  escribe JSON+CSV con `write_outputs`, imprimiendo el resumen de ingesta y de
  completitud.
- Una **guía de uso** en `docs/`.

**No se toca** el `Servicio_Consolidado`, el `Endpoint_Consolidado` ni la
`Vista_Bibliometria`: por el Requisito 10 del spec `multi-source-bibliometria`,
el backend descubre dinámicamente cualquier carpeta bajo `data/processed/` y
agrupa por el campo `source`. En cuanto `data/processed/openalex/` exista con
registros `source = "OpenAlex"`, OpenAlex aparece en el consolidado **sin cambios
de código** (Req 7).

Principios heredados del steering (`bibliometrics.md`, `tech.md`, `structure.md`,
`product.md`, `data-and-domain.md`):

- **No inventar datos.** Campo no entregado por la API → `None`. Obligatorio
  faltante o detección ambigua → `inclusion_status = "PENDIENTE_REVISIÓN"` con
  nota.
- **No falsear el origen.** `source` siempre `"OpenAlex"`; nunca otra fuente.
- **No clasificar OFC** ni evaluar relevancia temática automáticamente
  (`PENDING_VALIDATION`); en V1 los registros entran como `PENDIENTE_REVISIÓN`.
- **`data/raw/` es inmutable.** El pipeline **nunca** escribe en `data/raw/`;
  solo en `data/processed/openalex/`.
- **El pipeline corre sin UI**, reproducible por un único comando CLI.
- **Sin secretos en el repo.** La `Mailto_Cortesia` llega por variable de
  entorno; no es un secreto y nunca se versiona con un valor real.

Alcance mapeado a requisitos: consulta a la API con paginación y mailto (Req 1),
límites/errores/reintentos (Req 2), extracción conforme al contrato V1 incluida
la reconstrucción del abstract (Req 3), criterios de inclusión y período (Req 4),
deduplicación básica incluida la de varias `Consulta`s (Req 5), salida consolidada
reproducible por CLI (Req 6), incorporación automática al consolidado sin rediseño
(Req 7), trazabilidad y procedencia (Req 8) y guía de uso (Req 9).

## Architecture

OpenAlex por API se añade como un conector independiente que confluye en la misma
carpeta `data/processed/openalex/` que la vía PoP. El `BibliometriaService`
existente lo consolida por descubrimiento, sin saber nada específico de OpenAlex
ni de si el dataset vino de la API o de PoP.

```
  OBTENCIÓN POR API (este spec)                 SIN CAMBIOS (ya existente)
  -----------------------------------           ------------------------------

  Consulta(s): términos + filtros de año
        |
        v
  ingestion/openalex_api_client.py      (NUEVO)
   - endpoint works, sin API key
   - paginación por cursor (cursor=*, per_page<=200)
   - filtro de año en la API (publication_year / from-to_publication_date)
   - mailto del "polite pool" (ENV, opcional)   (Req 1.4, 1.5)
   - ritmo de solicitudes configurable          (Req 2.1)
   - reintentos con espera creciente (429/5xx)  (Req 2.2)
   - sin conectividad al iniciar -> error claro (Req 2.4)
        |
        v
  transform: work (JSON OpenAlex) -> ArticleRecord
   - reconstruye abstract desde abstract_inverted_index (Req 3.7)
   - no-invención: campo ausente -> None        (Req 3.3)
   - obligatorio faltante/ambiguo -> PENDIENTE_REVISIÓN
   - article_id esquema "oa-" (igual que PoP)    (Req 3.6)
        |
        v
  pipelines/process_openalex_api.py     (NUEVO, único comando CLI)
   - combina 1..N Consultas                      (Req 5.2)
   - validate_period 2020-2030   (_common, SIN CAMBIOS)
   - mark_duplicates por título  (_common, SIN CAMBIOS)
   - write_outputs JSON+CSV      (_common, SIN CAMBIOS)
   - print_summary completitud   (_common, SIN CAMBIOS)
        |
        v
  data/processed/openalex/
     openalex_dataset_YYYY-MM-DD.json / .csv
        |  (misma carpeta y mismo source que la vía PoP)
        v
  +----------------------------------------------+
  |  BibliometriaService (backend, SIN CAMBIOS)  |
  |  - descubre fuentes por data/processed/       |
  |  - agrupa por campo `source`                  |
  |  - agrega total, distribuciones, completitud, |
  |    pendientes, duplicados, aporte_por_fuente  |
  +----------------------------------------------+
                        |
                        v
      GET /bibliometria/resumen  (consolidado, SIN CAMBIOS)
                        |
                        v
      Vista_Bibliometria (React, SIN CAMBIOS)
        -> OpenAlex aparece en "Aporte por fuente"
```

Decisiones estructurales clave:

- **Cero cambios en servicio, endpoint y vista.** La incorporación es por
  convención (carpeta `data/processed/openalex/` + registros con
  `source = "OpenAlex"`). Satisface el Req 7 sin editar el consolidado.
- **Aislamiento del conector.** Toda la lógica específica de API vive en
  `openalex_api_client.py` y `process_openalex_api.py`. No se toca
  `extract_scholar.py`, `extract_boletin.py`, `extract_openalex.py` (PoP) ni sus
  pipelines (Req 7.3).
- **Reutilización de helpers sin modificarlos.** `norm_title`, `mark_duplicates`,
  `validate_period`, `write_outputs`, `print_summary` de `_common.py` se usan tal
  cual; no se altera el comportamiento de otras fuentes (Req 7.4).
- **Capa HTTP separada de la transformación.** El cliente de API no conoce el
  contrato V1; la transformación no conoce HTTP. Esto permite probar la
  transformación con `work`s sintéticos y probar paginación/reintentos con la capa
  HTTP simulada (sin red real en tests).
- **Misma carpeta y mismo esquema de id que la vía PoP.** API y PoP cuentan como
  una sola fuente y se deduplican juntos (Req 3.6).

## Components and Interfaces

### Archivos nuevos

| Archivo | Responsabilidad | Requisitos |
|---------|-----------------|------------|
| `bibliometrics/ingestion/openalex_api_client.py` | Cliente de la API_OpenAlex: construcción de la `Consulta` (términos + filtro de año), paginación por cursor, `mailto` opcional desde ENV, ritmo configurable, reintentos con backoff, detección de sin-conectividad; transformación `work` → `ArticleRecord` (incl. reconstrucción del abstract); `article_id` determinista con prefijo `oa-`. | Req 1, 2, 3, 8 |
| `bibliometrics/pipelines/process_openalex_api.py` | Pipeline CLI (único comando): ejecuta 1..N `Consulta`s, combina resultados, valida período, marca duplicados, escribe JSON+CSV, imprime resumen de ingesta y completitud. | Req 2.3, 2.5, 4, 5, 6 |
| `docs/user-guide/consultar-openalex-api.md` | Guía del comando CLI, parámetros de `Consulta`, Período 2020–2030, salida, variable `OPENALEX_MAILTO`, términos como propuesta a validar con SAO, relación con el spec PoP. | Req 9 |
| Tests en `tests/unit/` y `tests/integration/` | Transformación e índice invertido (property-based + unit), paginación/reintentos con HTTP simulado, y verificación de incorporación consolidada. | Verificación |
| Entrada en `.env.example` (`OPENALEX_MAILTO`, placeholder comentado) | Documentar la variable del polite pool sin valor real. | Req 1.5, 9.2 |

### Archivos que NO se modifican (verificación de no-rediseño)

| Archivo | Motivo |
|---------|--------|
| `backend/src/services/bibliometria_service.py` | Ya descubre por `data/processed/` y agrupa por `source` (Req 7.1). |
| `backend/src/api/bibliometria.py` / `schemas/bibliometria.py` | El endpoint consolidado ya es genérico (Req 7). |
| `frontend` `BibliometriaPage` y afines | Ya renderiza `aporte_por_fuente` genéricamente (Req 7.2). |
| `bibliometrics/ingestion/extract_scholar.py`, `extract_boletin.py` | Aislamiento del conector (Req 7.3). |
| `bibliometrics/ingestion/extract_openalex.py`, `bibliometrics/pipelines/process_openalex.py` (vía PoP) | Coexisten; la vía API no los altera. |
| `bibliometrics/pipelines/_common.py` | Se reutiliza sin alterar su comportamiento. |
| `bibliometrics/ingestion/article_record.py` | Contrato V1 inmutable (Req 3.5). |

### Dependencia nueva (cliente HTTP)

`bibliometrics/requirements.txt` hoy pina `pdfplumber` y `hypothesis` pero **no**
tiene cliente HTTP. El diseño **añade un cliente HTTP pinado** —propuesta
`requests==2.32.*` (o `httpx` pinado si se prefiere soporte async; para un
pipeline secuencial con cursor, `requests` basta)—. La versión exacta se fija en
implementación. Dependencias pinadas por `tech.md §21` / `bibliometrics.md §4.6`.

### Cliente de API — interfaz propuesta

```python
# bibliometrics/ingestion/openalex_api_client.py

OPENALEX_SOURCE = "OpenAlex"                     # Req 3.1, 3.2 (igual que PoP)
OPENALEX_API_EXTRACTION_METHOD = "OpenAlex API V1"   # Req 8.1 (distinto de PoP)
OPENALEX_BASE_URL = "https://api.openalex.org/works"
PERIODO_MIN, PERIODO_MAX = 2020, 2030            # mismo rango que _common
MAILTO_ENV_VAR = "OPENALEX_MAILTO"               # Req 1.4, 9.2 (no secreto)


@dataclass(frozen=True)
class Consulta:
    """Parámetros de una búsqueda a la API (Req 1, 4.1).

    term: término/expresión de búsqueda (propuesta del equipo, validar con SAO).
    year_from, year_to: acotan al Período_Inclusión 2020–2030 vía filtro de año.
    """
    term: str
    year_from: int = PERIODO_MIN
    year_to: int = PERIODO_MAX


@dataclass(frozen=True)
class ApiConfig:
    """Config operativa del cliente (todo configurable — Req 1.3, 2.1, 2.2)."""
    per_page: int = 200          # máximo que admite OpenAlex
    max_results: Optional[int] = None   # límite máximo configurable por Consulta
    pace_seconds: float = 0.2    # pausa entre páginas (ritmo acotado) (Req 2.1)
    max_retries: int = 5         # reintentos por página (Req 2.2)
    backoff_base: float = 1.0    # espera creciente (incremental/exponencial)
    mailto: Optional[str] = None # polite pool; viene de ENV (Req 1.4)


class HttpError(Exception):
    """Error HTTP clasificable como transitorio (429/5xx) o permanente."""
    status_code: int
    transient: bool


def resolve_mailto() -> Optional[str]:
    """Lee OPENALEX_MAILTO del entorno; None si no está (Req 1.4, 1.5).

    Nunca lee de un archivo versionado ni exige la variable.
    """


def fetch_page(session, consulta: Consulta, cursor: str,
               config: ApiConfig) -> tuple[list[dict], Optional[str]]:
    """Pide UNA página de works a la API y devuelve (results, next_cursor).

    - Envía filter=publication_year:{from}-{to} (o from/to_publication_date),
      per_page y cursor; añade mailto si está configurado (Req 1.4).
    - next_cursor es el meta.next_cursor de OpenAlex; None cuando no hay más.
    Capa HTTP pura: no transforma works. Lanza HttpError en fallo HTTP.
    """


def fetch_with_retry(session, consulta: Consulta, cursor: str,
                     config: ApiConfig) -> tuple[list[dict], Optional[str]]:
    """Envuelve fetch_page con reintentos y espera creciente (Req 2.2).

    Reintenta solo errores transitorios (429, 5xx) hasta config.max_retries;
    un error permanente (p. ej. 400) no se reintenta. Agotados los reintentos,
    propaga HttpError para que el pipeline lo registre (Consulta + página) y
    continúe con las Consultas restantes (Req 2.3).
    """


def iter_works(session, consulta: Consulta,
               config: ApiConfig) -> Iterator[dict]:
    """Itera TODOS los works de una Consulta paginando por cursor (Req 1.3).

    Comienza con cursor="*", aplica config.pace_seconds entre páginas, y se
    detiene al agotar páginas o al alcanzar config.max_results. Yield de cada
    work crudo (dict JSON de la API). No escribe nada.
    """
```

### Transformación `work` → contrato V1 — interfaz propuesta

```python
def reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    """Reconstruye el texto del abstract desde abstract_inverted_index (Req 3.7).

    El índice invertido es {palabra: [posiciones...]}. Se coloca cada palabra en
    todas sus posiciones y se unen por espacios en orden ascendente de posición.
    - index ausente/None/vacío -> None (no se inventa) (Req 3.7).
    - No inventa palabras faltantes: si una posición no aparece, simplemente no
      se rellena (el texto resultante preserva solo lo que el índice contiene).
    """


def _api_make_article_id(doi, title, year) -> str:
    """Mismo esquema que el conector PoP (Req 3.6): prefijo 'oa-'.

    - Con DOI: 'oa-' + hash12(doi normalizado).
    - Sin DOI: 'oa-' + hash12(norm_title(title) + '|' + year).
    hash12 = primeros 12 hex de SHA-256. Reutiliza norm_title de _common para
    coherencia con la dedupe y con la vía PoP: el MISMO work produce el MISMO id
    en API y en PoP, por lo que cuentan como la misma fuente.
    """


def work_to_record(work: dict) -> ArticleRecord:
    """Transforma un work nativo de la API_OpenAlex en un ArticleRecord V1.

    - source fijo = 'OpenAlex' (Req 3.1, 3.2).
    - Campo ausente en el work -> None (Req 3.3).
    - Obligatorio (title/authors/publication_year) faltante o ambiguo ->
      inclusion_status='PENDIENTE_REVISIÓN' con nota (Req 3.4, 4.3).
    - Año fuera de 2020–2030 -> PENDIENTE_REVISIÓN con nota, sin descartar
      (Req 4.2). No clasifica OFC ni relevancia (Req 4.5).
    - abstract reconstruido con reconstruct_abstract (Req 3.7).
    - extraction_method='OpenAlex API V1' (Req 8.1); source_url = work['id']
      (URL https://openalex.org/Wxxxx) cuando exista (Req 8.2).
    """
```

### Constantes del pipeline

```python
# bibliometrics/pipelines/process_openalex_api.py
OUTPUT_DIR   = <repo>/data/processed/openalex   # misma carpeta que la vía PoP
SOURCE_LABEL = "OpenAlex"
BASENAME     = "openalex_dataset"
```

El pipeline NO recibe ni toca `data/raw/` (Req 6.4): su entrada son las
`Consulta`s (por argumentos CLI o archivo de configuración no secreto). Ejecuta
`iter_works` por cada `Consulta`, transforma cada work con `work_to_record`,
aplica `validate_period` a cada registro, combina todos los resultados, marca
duplicados sobre el conjunto combinado con `mark_duplicates` (Req 5.2), escribe
JSON+CSV con `write_outputs` e imprime el resumen de ingesta (recuperados /
páginas / errores — Req 2.5) y el de completitud con `print_summary`.

## Data Models

### Article Data Contract V1 (reutilizado sin cambios)

Se reutiliza el dataclass `ArticleRecord`
(`bibliometrics/ingestion/article_record.py`), que implementa el contrato V1. El
contrato **no cambia** sus campos obligatorios ni opcionales como consecuencia de
este spec (Req 3.5). Obligatorios: `article_id`, `title`, `authors`,
`publication_year`, `source`, `extraction_date`, `processing_status`,
`is_duplicate`, `inclusion_status`.

### Mapeo `work` (API OpenAlex) → contrato V1

> **PENDING_VALIDATION del mapeo fino.** El mapeo campo-a-campo definitivo debe
> confirmarse inspeccionando una **respuesta real de la API_OpenAlex** (no se
> inventa aquí). La tabla siguiente es la **propuesta del equipo** basada en el
> esquema documentado de `works` de OpenAlex. Difiere del mapeo del export PoP
> porque la API devuelve el JSON nativo de OpenAlex (objetos anidados, listas,
> abstract como índice invertido). Campo no presente → `None`.

| Campo contrato V1 | Ruta propuesta en el `work` de la API | Notas |
|-------------------|----------------------------------------|-------|
| `title` | `work["title"]` o `work["display_name"]` | **Obligatorio.** Ausente/ambiguo → PENDIENTE_REVISIÓN. |
| `authors` | join de `work["authorships"][*]["author"]["display_name"]` | **Obligatorio.** Unir por `; `. |
| `publication_year` | `work["publication_year"]` | **Obligatorio.** Validar 2020–2030. |
| `doi` | `work["doi"]` | Opcional. Quitar prefijo `https://doi.org/` si está (propuesta, confirmar). |
| `url` | `work["primary_location"]["landing_page_url"]` o `work["doi"]` | Opcional. Enlace al artículo. |
| `journal` | `work["primary_location"]["source"]["display_name"]` (o `host_venue` en esquema antiguo) | Opcional. Revista/medio. |
| `publisher` | `work["primary_location"]["source"]["host_organization_name"]` | Opcional. |
| `volume` | `work["biblio"]["volume"]` | Opcional. |
| `issue` | `work["biblio"]["issue"]` | Opcional. |
| `pages` | `work["biblio"]["first_page"]`–`work["biblio"]["last_page"]` | Opcional. Combinar si ambos existen. |
| `abstract` | reconstruido desde `work["abstract_inverted_index"]` | Opcional. Ausente → `None` (Req 3.7). |
| `keywords` | `work["concepts"][*]["display_name"]` o `work["keywords"]` | Opcional. Unir por `; `. |
| `language` | `work["language"]` | Opcional. |
| `source` | — (fijo) | **Fijo = "OpenAlex"** (Req 3.1). |
| `source_url` | `work["id"]` (URL `https://openalex.org/Wxxxx`) | Opcional. Procedencia propia (Req 8.2). |
| `extraction_date` | — (fecha de corrida) | Fecha de obtención (Req 8.1). |
| `extraction_method` | — (fijo) | `"OpenAlex API V1"` (Req 8.1). |

> Detalle fino marcado para confirmar contra la respuesta real: el pelado del
> prefijo del DOI, el nombre exacto de la revista (`primary_location.source`
> vs. `host_venue`), y la forma de `keywords`/`concepts` pueden variar según la
> versión del esquema que devuelva la API. Se cierra en implementación.

### `article_id` determinista para OpenAlex (Req 3.6)

Idéntico al esquema de la vía PoP, para que el **mismo work produzca el mismo id**
por cualquiera de las dos rutas y ambos cuenten como la fuente OpenAlex:

- Con DOI: `oa-<hash12(doi normalizado)>`.
- Sin DOI: `oa-<hash12(norm_title(title) + "|" + año)>`.
- `hash12` = primeros 12 hex de SHA-256; `norm_title` reutilizado de `_common.py`.

### Reconstrucción del `abstract_inverted_index` (Req 3.7)

OpenAlex no entrega el abstract como texto plano sino como un **índice invertido**
`{palabra: [posiciones]}`. La reconstrucción crea un arreglo donde cada palabra se
coloca en todas sus posiciones indicadas y luego se concatenan en orden ascendente
de posición. Si el índice está ausente, es `None` o vacío → `abstract = None` (no
se inventa texto).

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en todas
las ejecuciones válidas del sistema: un enunciado formal de lo que el sistema
debe hacer. Las propiedades son el puente entre especificaciones legibles por
personas y garantías de correctitud verificables por máquina.*

> Tras la reflexión de redundancia: la no-invención de campos (3.3) y la
> preservación de procedencia (8.2) son facetas de una misma regla de fidelidad,
> pero se expresan por separado porque cada una aporta verificación única
> (ausencia → `None` vs. presencia → se preserva). El año faltante (4.3) y el año
> ambiguo quedan cubiertos por la propiedad de obligatorios (Property 3), mientras
> que el año fuera de rango (4.2) es una propiedad distinta porque conserva el
> registro con un año válido pero marcado. La dedupe dentro de una Consulta (5.1)
> y sobre el conjunto combinado de varias Consultas (5.2) se unifican en una sola
> propiedad sobre el conjunto final.

### Property 1: Fuente fija y conformidad del contrato

*Para todo* `work` transformado por el conector, `source == "OpenAlex"` (nunca
otra fuente) y el registro cumple el contrato V1 (todos los obligatorios
presentes, o bien `inclusion_status == "PENDIENTE_REVISIÓN"`).

**Validates: Requirements 3.1, 3.2**

### Property 2: No-invención de campos ausentes

*Para todo* `work`, cada campo del contrato que no esté presente en el `work` de
entrada queda en `None` en el `ArticleRecord` producido (no se sustituye por un
valor inventado).

**Validates: Requirements 3.3**

### Property 3: Obligatorio faltante o ambiguo marca revisión

*Para todo* `work` al que le falte `title`, `authors` o `publication_year`, o
cuyo año no sea interpretable, el conector fija `inclusion_status =
"PENDIENTE_REVISIÓN"` con una nota no vacía, sin eliminar el registro (año no
detectable → `publication_year = None` + revisión).

**Validates: Requirements 3.4, 4.3**

### Property 4: Año fuera de período marca revisión sin descartar

*Para todo* `work` con `publication_year` fuera de 2020–2030, el conector
conserva el registro con ese año y fija `inclusion_status = "PENDIENTE_REVISIÓN"`
con una nota; para años dentro del rango no fuerza ese estado por motivo de
período.

**Validates: Requirements 4.2**

### Property 5: `article_id` determinista, reproducible y con esquema compartido

*Para todo* `work`, transformarlo dos veces produce el mismo `article_id`, el id
empieza por `oa-`, y para un `work` con el mismo DOI (o mismo título+año) el id
coincide con el que produciría la vía PoP para esos mismos datos.

**Validates: Requirements 3.6**

### Property 6: Reconstrucción correcta del abstract desde el índice invertido

*Para todo* `abstract_inverted_index` bien formado, el texto reconstruido coloca
cada palabra exactamente en las posiciones indicadas por el índice (orden
ascendente de posición); *para todo* índice ausente, `None` o vacío, `abstract`
queda en `None`.

**Validates: Requirements 3.7**

### Property 7: Paginación recupera todos los resultados hasta el límite

*Para toda* `Consulta` cuyos resultados abarquen varias páginas, `iter_works`
recupera todos los works siguiendo el cursor hasta agotarlo, o exactamente
`max_results` works cuando hay un límite configurado (nunca más que el límite,
nunca menos que el total cuando no hay límite).

**Validates: Requirements 1.3**

### Property 8: Reintento solo ante errores transitorios

*Para toda* secuencia de respuestas HTTP, `fetch_with_retry` reintenta únicamente
errores transitorios (429, 5xx) con espera creciente hasta `max_retries`, no
reintenta errores permanentes, y si agota los reintentos propaga el error para que
el pipeline lo registre y continúe.

**Validates: Requirements 2.2**

### Property 9: Deduplicación básica sobre el conjunto combinado

*Para todo* dataset resultante de una o varias `Consulta`s, dos registros con el
mismo título normalizado hacen que el segundo quede marcado `is_duplicate = true`
con `duplicate_of` apuntando al primero, sin eliminar ningún registro, aplicado
sobre el conjunto combinado de todas las `Consulta`s.

**Validates: Requirements 5.1, 5.2**

### Property 10: Procedencia preservada sin invención

*Para todo* `work` que traiga su `id` propio de OpenAlex, ese valor se preserva en
`source_url`; *para todo* `work` que no lo traiga, `source_url` queda en `None`
(no se inventa).

**Validates: Requirements 8.2**

### Property 11: Inmutabilidad de `data/raw/`

*Para toda* ejecución del pipeline, ninguna escritura ocurre dentro de
`data/raw/`; el pipeline solo escribe en `data/processed/openalex/`.

**Validates: Requirements 6.4**

### Property 12: Conservación aritmética del resumen

*Para toda* ejecución del pipeline, el resumen cumple que el número de registros
procesados equivale a los works recuperados que pudieron transformarse, y el
resumen reporta de forma consistente works recuperados, páginas consultadas y
errores encontrados.

**Validates: Requirements 2.5, 6.2**

### Property 13: Robustez ante works malformados

*Para toda* mezcla de works válidos y malformados recuperados de la API, la
transformación produce registros para los válidos, descarta robustamente los
malformados y no aborta la corrida.

**Validates: Requirements 2.3, 3.4**

## Error Handling

- **Sin conectividad al iniciar (Req 2.4):** si la primera solicitud a la API
  falla por falta de conectividad (error de red/DNS), el pipeline registra un
  mensaje de error **comprensible** y **finaliza sin escribir** un
  `Dataset_Procesado` vacío que pueda confundirse con un resultado real. No se
  genera ningún archivo en `data/processed/openalex/`.
- **Reintentos agotados para una página (Req 2.3):** tras `max_retries` fallos
  transitorios en una página, el pipeline **registra el error indicando la
  `Consulta` y la página afectada**, **conserva los resultados ya recuperados** y
  **continúa con las `Consulta`s restantes**. Al final escribe el dataset con lo
  recuperado y deja constancia en el resumen de que hubo errores, para no dejar el
  dataset a medias de forma silenciosa.
- **Error permanente (p. ej. 400):** no se reintenta; se registra y se trata como
  fallo de esa `Consulta`/página, continuando con el resto.
- **Work individual malformado:** se descarta de forma robusta (no detiene la
  corrida); se registra de forma agregada en el resumen.
- **Campo obligatorio faltante/ambiguo o año fuera de rango (Req 3.4, 4.2, 4.3):**
  no son errores de ejecución; el registro se conserva con
  `inclusion_status = "PENDIENTE_REVISIÓN"` y nota. Nunca se inventan valores.
- **Resumen final (Req 2.5, 6.2):** siempre imprime works recuperados, páginas
  consultadas, errores encontrados, registros procesados y completitud por campo.
- **Backend sin cambios:** el `BibliometriaService` ya maneja el caso sin datasets
  (resumen vacío coherente) y no expone trazas; este spec no altera ese manejo.

## Technical Decisions

- **Pipeline CLI, no botón de consulta en vivo.** Decisión acordada con el
  usuario (Req / Introduction): (a) el volumen bibliométrico (miles de artículos
  paginados) no cabe de forma sana en una petición HTTP del front; (b) mantiene la
  regla del proyecto de que la UI solo consulta resultados ya procesados
  (`structure.md §30`); (c) de cara a la migración a **ArcGIS Online**, el activo
  que migra es el dataset reproducible generado por el script, no la UI.
- **Espejo del patrón de conector probado.** Se refleja el patrón de
  `extract_openalex.py` / `process_openalex.py` (vía PoP): mismas constantes de
  fuente, mismo esquema de `article_id`, misma carpeta de salida, mismos helpers
  de `_common.py`. Se minimiza riesgo y no se refactoriza a una base común para no
  tocar código de otras fuentes.
- **Paginación por cursor.** OpenAlex recomienda `cursor=*` + `meta.next_cursor`
  con `per_page` hasta 200, que es estable para recorrer conjuntos grandes (más
  robusto que la paginación por `page`, limitada en profundidad).
- **Polite pool vía `mailto` de ENV.** Mejor servicio y límites. No es secreto;
  llega por `OPENALEX_MAILTO` y es opcional (el conector funciona sin ella).
- **Cliente HTTP pinado.** Se añade `requests` (o `httpx`) pinado a
  `bibliometrics/requirements.txt` (`tech.md §21`).
- **Reutilización de `_common.py` sin modificarlo.** `validate_period`,
  `mark_duplicates`, `write_outputs`, `print_summary`, `norm_title`, `CSV_FIELDS`,
  `PERIODO_MIN/MAX` se usan tal cual.
- **Esquema de id compartido `oa-`.** API y PoP cuentan como una sola fuente y se
  deduplican juntos (Req 3.6).
- **Mapeo fino `PENDING_VALIDATION`.** Se cierra en implementación tras inspeccionar
  una respuesta real de la API; la tabla de mapeo es propuesta del equipo
  (coherente con `bibliometrics.md §2.1`).

## Testing Strategy

Enfoque dual: **property-based + unit** para la lógica pura (transformación,
reconstrucción del abstract, id, dedupe, paginación/reintentos con HTTP simulado),
e **integración** para la incorporación al consolidado.

**Librería de property-based testing:** `hypothesis` (Python), ya pinada en
`bibliometrics/requirements.txt`. Cada propiedad se implementa con **un** test de
propiedad, mínimo **100 iteraciones**, etiquetado con un comentario:
`# Feature: fuente-openalex-api, Property N: <texto>`.

Property-based (pytest + hypothesis), con generadores de `work`s sintéticos
marcados como `DEMO_DATA` (subconjuntos aleatorios de campos, años dentro/fuera de
rango, con/sin DOI, títulos repetidos, índices invertidos arbitrarios, works
malformados):

- Transformación y contrato: Propiedades 1–5, 10.
- Reconstrucción del abstract: Propiedad 6 (generar índices invertidos arbitrarios
  y verificar posiciones; índice vacío/ausente → `None`).
- Capa HTTP (sin red real): Propiedades 7, 8 — **mock/stub** del cliente HTTP que
  simula páginas con cursores y secuencias de respuestas 200/429/5xx; se verifica
  que la paginación agota el cursor hasta el límite y que el backoff reintenta solo
  transitorios. **Ningún test golpea la red real.**
- Pipeline (dedupe, robustez, aritmética): Propiedades 9, 12, 13.
- Inmutabilidad de raw (Propiedad 11): ejecutar el pipeline con HTTP simulado y
  verificar que no se escribe nada dentro de `data/raw/` y que solo se escribe en
  `data/processed/openalex/`.

Unit / edge cases (pytest):

- `reconstruct_abstract` con índice típico, índice de una palabra repetida en
  varias posiciones, índice vacío, `None`.
- `work_to_record` con `work` completo, `work` sin `authorships`, sin
  `publication_year`, con año fuera de rango, con/sin `doi`, con/sin `id`.
- Sin conectividad al iniciar → mensaje comprensible y **no** se escribe dataset
  (Req 2.4).
- Reintentos agotados en una página → se registra `Consulta`+página, se conserva lo
  recuperado y continúa (Req 2.3).
- `resolve_mailto` → lee la ENV si existe; `None` si no (nunca exige la variable).

Integración (verificación de no-rediseño, Req 7):

- Poblar un `data/processed/openalex/` de prueba con un dataset conforme al
  contrato (`source = "OpenAlex"`) y comprobar vía `BibliometriaService` /
  `GET /bibliometria/resumen` que OpenAlex aparece en el total y en
  `aporte_por_fuente` con el nombre `"OpenAlex"`, **sin** modificar servicio ni
  vista (Req 7.1, 7.2).
- Comprobar que el `Dataset_Procesado` de otras fuentes (p. ej. Google Scholar)
  sigue contándose como su propia fuente y permanece intacto (Req 7.4).

Smoke / documentación:

- Ejecución del pipeline por un único comando CLI (Req 6.3).
- Existencia y contenido de la guía: comando CLI, parámetros de `Consulta`, Período
  2020–2030, salida `data/processed/openalex/`, variable `OPENALEX_MAILTO`
  (opcional, no secreta), términos como propuesta a validar con SAO, y relación con
  el spec PoP (mismo `Dataset_Procesado`) (Req 9.1–9.4).

## Limitaciones conocidas / PENDING_VALIDATION

- **Mapeo campo-a-campo del `work` de la API al contrato V1:** se confirma en
  implementación inspeccionando una respuesta real de la API_OpenAlex. La tabla de
  mapeo es propuesta del equipo (detalle fino del DOI, nombre de revista,
  `keywords`/`concepts`).
- **Términos de búsqueda de las `Consulta`s:** propuesta del equipo,
  `PENDING_VALIDATION` con SAO (Req 4.4, 9.3). No se presentan como criterio
  oficial de SAO.
- **Relevancia temática automática y clasificación por OFC:** `PENDING_VALIDATION`
  (Req 4.5); en V1 los registros entran como `PENDIENTE_REVISIÓN`. No se implementa
  clasificador.
- **Deduplicación entre fuentes (cross-source):** `PENDING_VALIDATION` (Req 5.3).
  Hoy solo dedupe básico por título normalizado dentro de la fuente OpenAlex
  (combinando API + PoP por compartir carpeta y esquema de id).
- **Comportamiento y límites de la API:** los límites de uso, el esquema de
  respuesta y la disponibilidad del "polite pool" pueden cambiar en el tiempo; el
  conector aplica ritmo y reintentos configurables para adaptarse sin reescribir.
