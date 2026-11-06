# Design Document

Fuente OpenAlex de alto volumen vía Publish or Perish (Componente B)

## Overview

Este diseño incorpora **OpenAlex** como fuente bibliométrica de **alto volumen**,
reutilizando sin rediseño la infraestructura multi-fuente del Componente B
construida en el spec `multi-source-bibliometria`. OpenAlex se consulta desde
Publish or Perish (PoP), que exporta lotes grandes en JSON o CSV sin las
limitaciones prácticas de Google Scholar.

El alcance real del spec es acotado: un **conector específico de OpenAlex**, su
**pipeline de ingesta por línea de comandos** y una **guía de exportación**. No
se toca el `Servicio_Consolidado`, el `Endpoint_Consolidado` ni la
`Vista_Bibliometria`: por el Requisito 10 del spec `multi-source-bibliometria`,
el backend descubre dinámicamente cualquier carpeta de fuente bajo
`data/processed/` y agrupa por el campo `source` de cada registro. En cuanto el
`Dataset_Procesado` de OpenAlex exista en `data/processed/openalex/`, aparece en
el consolidado **sin cambios de código**.

El diseño es un **espejo deliberado** del conector y pipeline de Google Scholar
ya implementados (`bibliometrics/ingestion/extract_scholar.py`,
`bibliometrics/pipelines/process_google_scholar.py`), que a su vez comparten los
helpers de `bibliometrics/pipelines/_common.py` y el dataclass `ArticleRecord`
(Article Data Contract V1) de `bibliometrics/ingestion/article_record.py`. Al
ser ambas fuentes exports de la misma herramienta (PoP), el patrón de extracción
es casi idéntico; la diferencia está en la fuente fija (`"OpenAlex"`), el prefijo
del `article_id`, la carpeta de E/S y los matices de mapeo del export de OpenAlex.

Principios heredados del steering (`bibliometrics.md`, `tech.md`, `structure.md`,
`product.md`):

- **No inventar datos.** Campo no detectado → `None`. Obligatorio faltante o
  detección ambigua → `inclusion_status = "PENDIENTE_REVISIÓN"` con nota.
- **No falsear el origen.** `source` siempre `"OpenAlex"`; nunca Google Scholar
  ni otra fuente. Lectura exclusiva de `data/raw/openalex/`, escritura exclusiva
  en `data/processed/openalex/`.
- **No clasificar OFC** (metodología `PENDING_VALIDATION`).
- **`data/raw/` es inmutable.** Las transformaciones escriben solo en `processed/`.
- **El pipeline corre sin UI**, reproducible por un único comando CLI.

Alcance mapeado a requisitos: conector OpenAlex (Req 1–4, 7), salida reproducible
(Req 5), incorporación automática al consolidado sin rediseño (Req 6) y guía de
exportación PoP (Req 8).

## Architecture

OpenAlex se añade como un conector independiente más que confluye en su propia
carpeta de `data/processed/`. El `BibliometriaService` existente lo consolida por
descubrimiento, sin saber nada específico de OpenAlex.

```
  FUENTE existente                FUENTE NUEVA: OpenAlex (Export PoP)
  ----------------------          --------------------------------------
  data/raw/google_scholar/        data/raw/openalex/*.json | *.csv
  data/raw/boletin_sao/                 |
        |                               v
        v                         ingestion/extract_openalex.py      (NUEVO)
  (conectores existentes)               |
        |                               v
        v                         pipelines/process_openalex.py      (NUEVO)
        |   helpers compartidos: pipelines/_common.py (SIN CAMBIOS)   |
        v                               v
  data/processed/{fuente}/        data/processed/openalex/
     *_dataset_YYYY-MM-DD.json/csv    openalex_dataset_YYYY-MM-DD.json/csv
        \                               /
         \                             /
          v                           v
      +------------------------------------------+
      |  BibliometriaService (backend, SIN CAMBIOS)|
      |  - descubre fuentes por data/processed/   |
      |  - agrupa por campo `source`              |
      |  - agrega total, distribuciones,          |
      |    completitud, pendientes, duplicados,   |
      |    aporte_por_fuente                      |
      +------------------------------------------+
                        |
                        v
      GET /bibliometria/resumen  (consolidado, SIN CAMBIOS)
                        |
                        v
      Vista_Bibliometria (React, SIN CAMBIOS)
        -> OpenAlex aparece en "Aporte por fuente"
```

Decisiones estructurales clave:

- **Cero cambios en servicio, endpoint y vista.** La incorporación de OpenAlex
  es por convención: una carpeta nueva bajo `data/processed/` + registros con
  `source = "OpenAlex"`. Esto satisface el Req 6 sin editar el consolidado.
- **Aislamiento del conector.** Toda la lógica específica de OpenAlex vive en
  `extract_openalex.py` y `process_openalex.py`. No se toca `extract_scholar.py`
  ni `extract_boletin.py` (Req 6.3).
- **Reutilización de helpers sin modificarlos.** `norm_title`, `mark_duplicates`,
  `validate_period`, `write_outputs`, `print_summary` de `_common.py` se usan tal
  cual; no se altera el comportamiento de otras fuentes (Req 6.4).
- **`article_id` con prefijo propio `oa-`** para distinguir OpenAlex de Scholar
  (`gs-`) y evitar colisiones entre fuentes (Req 2.6).

## Components and Interfaces

### Archivos nuevos

| Archivo | Responsabilidad | Requisitos |
|---------|-----------------|------------|
| `bibliometrics/ingestion/extract_openalex.py` | Conector OpenAlex: `detect_format`, `extract_records`, mapeo PoP/OpenAlex → contrato V1, `article_id` determinista con prefijo `oa-`. | Req 1.2, 1.3, 2, 3 |
| `bibliometrics/pipelines/process_openalex.py` | Pipeline CLI de OpenAlex (espejo del de Scholar): recorre la carpeta, valida período, marca duplicados, escribe JSON+CSV, imprime resúmenes. | Req 1, 3, 4, 5 |
| `docs/user-guide/exportar-openalex-pop.md` | Guía paso a paso de exportación con Publish or Perish seleccionando OpenAlex. | Req 8 |
| Tests en `tests/unit/` y `tests/integration/` | Conector (property-based) y verificación de incorporación consolidada. | Verificación |

### Archivos que NO se modifican (verificación de no-rediseño)

| Archivo | Motivo |
|---------|--------|
| `backend/src/services/bibliometria_service.py` | Ya descubre por `data/processed/` y agrupa por `source` (Req 6.1). |
| `backend/src/api/bibliometria.py` / `schemas/bibliometria.py` | El endpoint consolidado ya es genérico (Req 6). |
| `frontend/src/pages/BibliometriaPage.tsx` y afines | Ya renderiza `aporte_por_fuente` genéricamente (Req 6.2). |
| `bibliometrics/ingestion/extract_scholar.py`, `extract_boletin.py` | Aislamiento del conector (Req 6.3, 6.4). |
| `bibliometrics/pipelines/_common.py` | Se reutiliza sin alterar su comportamiento. |

### Conector OpenAlex — interfaz

```python
# bibliometrics/ingestion/extract_openalex.py

OPENALEX_SOURCE = "OpenAlex"
OPENALEX_EXTRACTION_METHOD = "Publish or Perish export (OpenAlex) V1"

def detect_format(path: Path) -> str:
    """Devuelve "json" o "csv" según la extensión (case-insensitive).

    :raises ValueError: si la extensión no es .json ni .csv.
    """

def extract_records(input_path: Path) -> list[ArticleRecord]:
    """Parsea un Export_PoP_OpenAlex (JSON o CSV) y devuelve registros V1.

    - source fijo = "OpenAlex" (Req 2.1, 2.2).
    - Campo no detectado -> None (no se inventa) (Req 2.3).
    - Obligatorio faltante/ambiguo -> inclusion_status="PENDIENTE_REVISIÓN"
      con nota (Req 2.4).
    - Año fuera de 2020-2030 o no detectable -> PENDIENTE_REVISIÓN con nota,
      sin descartar (Req 3).
    - Un registro individual malformado se descarta de forma robusta; el
      pipeline registra archivo + posición (Req 1.5).
    """
```

El pipeline `process_openalex.py` es el espejo exacto del de Scholar, con estas
constantes propias:

```python
DEFAULT_INPUT = <repo>/data/raw/openalex
OUTPUT_DIR    = <repo>/data/processed/openalex
SOURCE_LABEL  = "OpenAlex"
BASENAME      = "openalex_dataset"
```

Recorre `data/raw/openalex/` (descubrimiento case-insensitive de `.json`/`.csv`),
invoca `extract_records` por archivo, aplica `validate_period` a cada registro,
marca duplicados con `mark_duplicates`, escribe JSON+CSV con `write_outputs` e
imprime el resumen de ingesta (leídos / procesados / descartados) y el de
completitud con `print_summary`.

## Data Models

### Article Data Contract V1 (reutilizado sin cambios)

Se reutiliza el dataclass `ArticleRecord` existente
(`bibliometrics/ingestion/article_record.py`), que implementa el contrato V1. El
contrato **no cambia** sus campos obligatorios ni opcionales como consecuencia de
este spec (Req 2.5).

### Mapeo Export_PoP_OpenAlex → contrato V1

> **PENDING_VALIDATION del mapeo fino.** El mapeo campo-a-campo definitivo debe
> confirmarse inspeccionando un **Export_PoP_OpenAlex real de muestra** (no se
> inventa aquí). La tabla siguiente es la **propuesta inicial** basada en las
> columnas típicas que Publish or Perish produce (las mismas etiquetas que ya se
> usan para Scholar, porque PoP normaliza su salida) y en campos propios de
> OpenAlex. El conector busca **case-insensitive** y prueba varias claves
> candidatas por campo; la primera presente con valor no vacío gana. Campo no
> presente → `None`.

| Campo contrato V1 | Claves PoP/OpenAlex candidatas (propuesta) | Notas |
|-------------------|--------------------------------------------|-------|
| `title` | `title`, `Title` | **Obligatorio.** Ausente/ambiguo → PENDIENTE_REVISIÓN. |
| `authors` | `authors`, `author`, `Authors` | **Obligatorio.** |
| `publication_year` | `year`, `Year`, `publication_year` | **Obligatorio.** Validar 2020–2030. |
| `doi` | `doi`, `DOI` | Opcional. |
| `url` | `article_url`, `url`, `ArticleURL`, `id` | Opcional. OpenAlex usa `id` como URL del work. |
| `journal` | `source`, `Source`, `host_venue`, `venue` | Opcional. Revista/medio (PoP `Source` = medio). |
| `publisher` | `publisher`, `Publisher` | Opcional. |
| `volume` | `volume`, `Volume` | Opcional. |
| `issue` | `issue`, `Issue` | Opcional. |
| `pages` | `pages`, `Pages` | Opcional. |
| `abstract` | `abstract`, `description`, `Abstract` | Opcional (mejor en JSON). |
| `keywords` | `keywords`, `concepts`, `Keywords` | Opcional. OpenAlex expone `concepts`. |
| `language` | `language`, `Language` | Opcional. |
| `source` | — (fijo) | **Fijo = "OpenAlex"** (Req 2.1). |
| `source_url` | `id`, `cites_url`, `url`, `CitesURL` | Opcional. Preservar URL/ID propio de OpenAlex si existe (Req 7.3). |
| `extraction_date` | — (fecha de corrida) | Fecha de ingesta. |
| `extraction_method` | — (fijo) | `"Publish or Perish export (OpenAlex) V1"`. |

> Nota de procedencia (Req 7.3): cuando el export traiga el identificador o URL
> propio de OpenAlex (típicamente el campo `id`, p. ej.
> `https://openalex.org/Wxxxxxxxxx`), se preserva en `source_url`. Si no está, se
> deja `None` sin inventarlo.

### `article_id` determinista para OpenAlex (Req 2.6)

Identificador interno estable y reproducible entre corridas, con prefijo propio
para no colisionar con otras fuentes:

- Si hay DOI: `oa-<hash12(doi normalizado)>`.
- Si no hay DOI: `oa-<hash12(título normalizado + "|" + año)>`.
- `hash12` = primeros 12 hex de SHA-256. Determinista; usa el mismo `norm_title`
  de `_common.py` que la deduplicación, para coherencia.

El prefijo `oa-` lo distingue del `gs-` de Scholar, evitando colisiones de
`article_id` entre fuentes.

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en todas
las ejecuciones válidas del sistema: un enunciado formal de lo que el sistema
debe hacer. Las propiedades son el puente entre especificaciones legibles por
personas y garantías de correctitud verificables por máquina.*

> Tras la reflexión de redundancia: la detección de formato (1.2, 1.3) se unifica
> en una sola propiedad; el año faltante/ambiguo (3.2) queda cubierto por la
> propiedad de obligatorios faltantes (2.4); la no-invención de campos (2.3) y la
> preservación de procedencia (7.3) son facetas de una misma regla de fidelidad y
> se expresan por separado solo donde aportan verificación única.

### Property 1: Detección de formato por extensión (case-insensitive)

*Para todo* nombre de archivo cuya extensión sea `.json` o `.csv` en cualquier
combinación de mayúsculas y minúsculas, `detect_format` devuelve `"json"` o
`"csv"` respectivamente, independientemente del casing.

**Validates: Requirements 1.2, 1.3**

### Property 2: No-invención de campos ausentes

*Para todo* registro del Export_PoP_OpenAlex, cada campo del contrato que no esté
presente en el registro de entrada queda en `None` en el `ArticleRecord`
producido (no se sustituye por un valor inventado).

**Validates: Requirements 2.3**

### Property 3: Fuente fija y conformidad del contrato

*Para todo* registro producido por el conector de OpenAlex, `source == "OpenAlex"`
(nunca otra fuente) y el registro cumple el contrato V1 (todos los obligatorios
presentes, o bien `inclusion_status == "PENDIENTE_REVISIÓN"`).

**Validates: Requirements 2.1, 2.2**

### Property 4: Obligatorio faltante o ambiguo marca revisión

*Para todo* registro al que le falte `title`, `authors` o `publication_year`, o
cuyo año no sea interpretable, el conector fija `inclusion_status =
"PENDIENTE_REVISIÓN"` con una nota no vacía, sin eliminar el registro.

**Validates: Requirements 2.4, 3.2**

### Property 5: Validación de período no descarta

*Para todo* registro con `publication_year` fuera de 2020–2030, el conector fija
`inclusion_status = "PENDIENTE_REVISIÓN"` con una nota y conserva el registro;
para años dentro del rango no fuerza ese estado por motivo de período.

**Validates: Requirements 3.1**

### Property 6: `article_id` determinista, reproducible y con prefijo propio

*Para todo* registro de entrada, aplicar el conector dos veces produce el mismo
`article_id`, el `article_id` empieza por `oa-`, y nunca coincide con el prefijo
`gs-` de Google Scholar.

**Validates: Requirements 2.6**

### Property 7: Robustez ante registros malformados

*Para toda* mezcla de registros válidos y malformados en la entrada, el pipeline
produce exactamente los registros válidos, descarta solo los malformados y no
aborta el lote.

**Validates: Requirements 1.5**

### Property 8: Conservación aritmética del resumen de ingesta

*Para toda* ejecución del pipeline, `registros_leídos == registros_procesados +
registros_descartados`.

**Validates: Requirements 1.6**

### Property 9: Inmutabilidad de `data/raw/openalex`

*Para todo* conjunto de archivos de entrada en `data/raw/openalex/`, tras ejecutar
el pipeline el contenido, nombre y fecha de modificación de esos archivos
permanecen idénticos, y ninguna escritura ocurre dentro de `data/raw/openalex/`.

**Validates: Requirements 1.1, 7.1**

### Property 10: Deduplicación básica dentro de la fuente

*Para todo* dataset de OpenAlex, dos registros con el mismo título normalizado
hacen que el segundo quede marcado `is_duplicate = true` con `duplicate_of`
apuntando al primero, sin eliminar ningún registro.

**Validates: Requirements 4.1**

### Property 11: Preservación de procedencia sin invención

*Para todo* registro que traiga un identificador o URL propio de OpenAlex, ese
valor se preserva en `source_url`; *para todo* registro que no lo traiga,
`source_url` queda en `None` (no se inventa).

**Validates: Requirements 7.3**

## Error Handling

- **Entrada ausente o vacía (Req 1.4):** si `data/raw/openalex/` no existe, no es
  accesible, o no contiene `.json` ni `.csv`, el pipeline registra un mensaje
  informativo y **finaliza con éxito** sin procesar registros.
- **Registro malformado (Req 1.5):** se registra el archivo de origen y la
  posición del registro dentro de ese archivo, se descarta solo ese registro y
  continúa el lote.
- **Campo obligatorio faltante/ambiguo o año fuera de rango (Req 2.4, 3):** no es
  un error de ejecución; el registro se conserva con `inclusion_status =
  "PENDIENTE_REVISIÓN"` y nota. Nunca se inventan valores.
- **Formato de archivo no soportado o contenido no parseable:** `detect_format`
  levanta `ValueError`; el pipeline captura por archivo (ValueError de extensión,
  JSON inválido, archivo ilegible), lo informa y continúa con los demás archivos
  sin abortar el lote.
- **Resumen final (Req 1.6):** siempre imprime leídos / procesados / descartados,
  con la invariante `leídos == procesados + descartados`.
- **Backend sin cambios:** el `BibliometriaService` ya maneja el caso sin datasets
  (resumen vacío coherente) y no expone trazas; este spec no altera ese manejo.

## Technical Decisions

- **Espejo del conector de Scholar, no una abstracción nueva.** Ambas fuentes son
  exports de PoP; clonar el patrón probado (`extract_scholar` /
  `process_google_scholar`) minimiza riesgo y respeta el aislamiento por fuente
  (Req 6.3). No se refactoriza a una base común en este spec para no tocar código
  de otras fuentes.
- **Cero cambios en servicio/vista.** La incorporación es por convención
  (carpeta + campo `source`), cumpliendo Req 6 sin rediseño. La verificación es
  de integración (poblar `data/processed/openalex/` y comprobar que aparece).
- **Prefijo `oa-` en `article_id`.** Garantiza unicidad entre fuentes y evita
  colisiones con `gs-` (Req 2.6).
- **JSON recomendado para el Export_PoP_OpenAlex (Req 8.2).** PoP preserva mejor
  metadata y resumen en JSON; la guía lo recomienda por defecto. CSV igualmente
  soportado.
- **Varias consultas complementarias, un archivo por consulta (Req 8.3).** El
  pipeline combina todos los archivos de la carpeta y marca duplicados por título,
  lo que permite acumular alto volumen desde varias búsquedas.
- **Mapeo fino `PENDING_VALIDATION`.** Se cierra en implementación tras inspeccionar
  un export real; la tabla de mapeo es propuesta del equipo (coherente con
  `bibliometrics.md §2.1`).
- **No se reutiliza carpeta ni etiqueta de Scholar (Req 7.1, 7.2).** Lectura solo
  de `data/raw/openalex/`, escritura solo en `data/processed/openalex/`.

## Testing Strategy

Enfoque dual: **property-based + unit** para la lógica pura del conector, e
**integración** para la incorporación al consolidado.

**Librería de property-based testing:** `hypothesis` (Python), ya pinada en
`bibliometrics/requirements.txt`. No se implementa PBT desde cero. Cada propiedad
se implementa con **un** test de propiedad, mínimo **100 iteraciones**, etiquetado
con un comentario: `# Feature: fuente-openalex, Property N: <texto>`.

Property-based (pytest + hypothesis), con generadores de registros PoP/OpenAlex
sintéticos marcados como datos de prueba (subconjuntos aleatorios de campos, años
dentro/fuera de rango, con/sin DOI, títulos repetidos, registros malformados):

- Conector OpenAlex: Propiedades 1–6, 10, 11.
- Pipeline (robustez y aritmética): Propiedades 7, 8.
- Inmutabilidad de raw (Propiedad 9): generar carpeta temporal con archivos
  arbitrarios, snapshot de (nombre, hash, mtime), ejecutar el pipeline sobre esa
  carpeta y verificar igualdad y que no se escribe dentro de `data/raw/openalex/`.

Ejemplos / edge cases (pytest):

- Carpeta ausente / vacía / solo `.txt` → éxito sin registros (Req 1.4).
- Escritura de JSON+CSV en `data/processed/openalex/` y resumen con completitud
  (Req 5.1, 5.2).
- Detección JSON anidado bajo `data`/`results`/`records` y CSV con BOM (variantes
  reales de PoP).

Integración (verificación de no-rediseño, Req 6):

- Poblar un `data/processed/openalex/` de prueba con un dataset conforme al
  contrato (`source = "OpenAlex"`) y comprobar vía `BibliometriaService` /
  `GET /bibliometria/resumen` que OpenAlex aparece en el total y en
  `aporte_por_fuente` con el nombre `"OpenAlex"`, **sin** modificar servicio ni
  vista (Req 6.1, 6.2).
- Comprobar que el `Dataset_Procesado` de Google Scholar (u otra fuente) sigue
  contándose como su propia fuente y permanece intacto (Req 6.4).

Smoke / documentación:

- Ejecución del pipeline por un único comando CLI (Req 5.3).
- Existencia y contenido de la guía PoP OpenAlex: pasos, selección de OpenAlex
  como fuente, consulta del tema, período 2020–2030, JSON recomendado, destino
  `data/raw/openalex/`, estrategia de varias consultas y la marca explícita de que
  términos y nombres de archivo son propuesta a validar con SAO (Req 8.1–8.4).

## Limitaciones conocidas / PENDING_VALIDATION

- **Mapeo campo-a-campo del export de PoP-OpenAlex al contrato V1:** se confirma
  en implementación inspeccionando un Export_PoP_OpenAlex real de muestra. La
  tabla de mapeo es propuesta del equipo.
- **Términos de búsqueda y nombres de archivo de la guía:** propuesta del equipo,
  `PENDING_VALIDATION` con SAO (Req 8.4).
- **Deduplicación entre fuentes (cross-source):** `PENDING_VALIDATION` (Req 4.2).
  Hoy solo dedupe básico por título dentro de la fuente.
- **Clasificación por OFC:** metodología y algoritmo `PENDING_VALIDATION`; no se
  implementa clasificador.
- **Obtención de OpenAlex:** manual/asistida vía Publish or Perish. No se
  implementan consultas programáticas a la API de OpenAlex ni scraping (coherente
  con el resto del Componente B).
- **Columnas PoP variables:** el export puede no traer `volume`/`issue`/`abstract`
  según la consulta; esos campos quedan `None` sin invención.
