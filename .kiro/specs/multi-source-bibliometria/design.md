# Design Document

Bibliometría multi-fuente y análisis consolidado (Componente B)

## Overview

Este diseño incorpora **Google Scholar** como segunda fuente bibliométrica y
generaliza el análisis para que sea **consolidado** (todas las fuentes en un solo
conjunto), respetando el patrón de **conectores por fuente** ya establecido con
el Boletín SAO.

El diseño se apoya en código existente y no reescribe el Componente B:

- La ingesta del Boletín SAO (`bibliometrics/ingestion/extract_boletin.py`),
  su pipeline (`bibliometrics/pipelines/process_boletin_sao.py`) y el dataclass
  `ArticleRecord` (Article Data Contract V1) ya funcionan con 35 PDFs reales.
- El servicio (`backend/src/services/bibliometria_service.py`) hoy lee solo
  `data/processed/boletin_sao/`; se generaliza para descubrir **todas** las
  fuentes bajo `data/processed/`.
- El frontend (`frontend/src/pages/BibliometriaPage.tsx`) ya consume un resumen
  agregado vía hook + cliente API; se actualiza para consumir el consolidado.

Principios heredados del steering (`bibliometrics.md`, `tech.md`, `structure.md`):

- **No inventar datos.** Campo no detectado → `null`. Obligatorio faltante o
  detección ambigua → `inclusion_status = PENDIENTE_REVISIÓN` con nota.
- **No clasificar OFC** (metodología `PENDING_VALIDATION`). La distribución por
  OFC solo se muestra si ya existe un dataset clasificado.
- **`data/raw/` es inmutable.** Las transformaciones escriben en `interim/` o
  `processed/`.
- **El pipeline corre sin UI**, reproducible por un único comando. El backend
  **no toca la base de datos**: lee archivos ya procesados. El frontend solo
  consulta resultados.

Alcance (mapeado a requisitos): conector Google Scholar (Req 1–5), servicio y
endpoint consolidados (Req 6–8), vista generalizada (Req 9), base para múltiples
fuentes (Req 10) y guía de exportación de Publish or Perish (Req 11).

## Architecture

El flujo multi-fuente mantiene conectores independientes que confluyen en un
dataset por fuente; el servicio consolida por lectura de archivos.

```
  FUENTE A: Boletín SAO (PDFs)        FUENTE B: Google Scholar (Export PoP)
  ------------------------------      --------------------------------------
  data/raw/boletin_sao/*.pdf          data/raw/google_scholar/*.json|*.csv
        |                                   |
        v                                   v
  ingestion/extract_boletin.py        ingestion/extract_scholar.py   (NUEVO)
        |                                   |
        v                                   v
  pipelines/process_boletin_sao.py    pipelines/process_google_scholar.py (NUEVO)
        |   (helpers compartidos: pipelines/_common.py — NUEVO)        |
        v                                   v
  data/processed/boletin_sao/         data/processed/google_scholar/
     *_dataset_YYYY-MM-DD.json/csv       *_dataset_YYYY-MM-DD.json/csv
        \                                   /
         \                                 /
          v                               v
      +------------------------------------------+
      |  BibliometriaService (backend)           |
      |  - descubre fuentes por data/processed/  |
      |  - agrupa por campo `source`             |
      |  - datasets *_clasificado -> solo OFC    |
      |  - agrega: total, año, volumen,          |
      |    completitud, pendientes, duplicados,  |
      |    por_ofc, aporte_por_fuente            |
      +------------------------------------------+
                        |
                        v
      GET /bibliometria/resumen            (NUEVO, consolidado)
      GET /bibliometria/boletin-sao/resumen (se mantiene, compatibilidad)
                        |
                        v
      Vista_Bibliometria (React + Recharts)
      - título "todas las fuentes"
      - tarjetas/gráficos sobre el conjunto
      - sección "Aporte por fuente"
      - estado vacío honesto
```

Decisiones estructurales clave:

- **Descubrimiento dinámico de fuentes** por carpeta en `data/processed/` +
  **agrupación por el campo `source`** de cada registro. Añadir una fuente nueva
  conforme al contrato no requiere tocar el servicio ni la vista (Req 10.1).
- **Separación de datasets de fuente vs clasificados.** Las carpetas cuyo nombre
  termina en `_clasificado` (o cuyos archivos siguen el patrón
  `*_clasificado_*.json`) **no** aportan artículos al total: solo alimentan la
  distribución por OFC (Req 6.7).
- **Reutilización de helpers de pipeline** en `pipelines/_common.py` para no
  duplicar lógica entre Boletín y Scholar (DRY), sin alterar el comportamiento
  del pipeline del Boletín.

## Components and Interfaces

### Archivos nuevos

| Archivo | Responsabilidad | Requisitos |
|---------|-----------------|------------|
| `bibliometrics/ingestion/article_record.py` | Dataclass `ArticleRecord` compartido (contrato V1) extraído desde `extract_boletin.py`. | Req 2.1, 2.4 |
| `bibliometrics/ingestion/extract_scholar.py` | Conector Google Scholar: `extract_records(input_path) -> list[ArticleRecord]`, detección de formato JSON/CSV, mapeo PoP→contrato V1. | Req 1.2, 1.3, 2, 3 |
| `bibliometrics/pipelines/_common.py` | Helpers compartidos: `norm_title`, `mark_duplicates`, `validate_period`, `write_outputs`, `print_summary`. | Req 4.1, 5.1, 5.2 |
| `bibliometrics/pipelines/process_google_scholar.py` | Pipeline por CLI de Google Scholar (espejo del de Boletín). | Req 1, 3, 4, 5 |
| `docs/user-guide/exportar-google-scholar-pop.md` | Guía de exportación con Publish or Perish. | Req 11 |
| `frontend/src/types/bibliometria.ts` (ampliación) | `ResumenConsolidado`, `AporteFuente`. | Req 9 |
| Tests en `tests/unit/` y `tests/integration/` | Conector, servicio consolidado y endpoints. | Verificación |

### Archivos modificados

| Archivo | Cambio | Requisitos |
|---------|--------|------------|
| `bibliometrics/ingestion/extract_boletin.py` | Importar `ArticleRecord` del módulo compartido (sin cambiar comportamiento). | Req 10.2 |
| `bibliometrics/pipelines/process_boletin_sao.py` | Usar helpers de `_common.py` (sin cambiar salida). | DRY |
| `backend/src/services/bibliometria_service.py` | Generalizar a consolidado multi-fuente; conservar `resumen()` del Boletín. | Req 6, 7, 8.4, 10.1 |
| `backend/src/schemas/bibliometria.py` | Añadir `ResumenConsolidado` y `AporteFuente`. | Req 6, 7 |
| `backend/src/api/bibliometria.py` | Nueva ruta `GET /bibliometria/resumen`; conservar la antigua. | Req 8 |
| `frontend/src/services/apiClient.ts` | `obtenerResumenConsolidado()`. | Req 8.1 |
| `frontend/src/hooks/useBibliometria.ts` | `useResumenConsolidado()`. | Req 9 |
| `frontend/src/pages/BibliometriaPage.tsx` | Consumir consolidado + sección aporte + título "todas las fuentes". | Req 9 |

### Conector Google Scholar — interfaz

```python
# bibliometrics/ingestion/extract_scholar.py

def detect_format(path: Path) -> str:
    """Devuelve "json" o "csv" según la extensión (case-insensitive).

    :raises ValueError: si la extensión no es .json ni .csv.
    """

def extract_records(input_path: Path) -> list[ArticleRecord]:
    """Parsea un Export_PoP (JSON o CSV) y devuelve registros del contrato V1.

    - source fijo = "Google Scholar".
    - Campo no detectado -> None (no se inventa).
    - Obligatorio faltante/ambiguo -> inclusion_status=PENDIENTE_REVISIÓN + nota.
    - Un registro malformado se descarta (se registra archivo+posición) y no
      detiene el procesamiento del resto.
    """
```

El pipeline Scholar es un espejo del de Boletín: recorre
`data/raw/google_scholar/`, invoca `extract_records`, valida período 2020–2030,
marca duplicados por título normalizado, escribe JSON+CSV en
`data/processed/google_scholar/` e imprime el resumen (leídos / procesados /
descartados + completitud).

### Servicio consolidado — interfaz

```python
# backend/src/services/bibliometria_service.py

class BibliometriaService:
    def resumen(self) -> ResumenBibliometrico:
        """Resumen de la fuente Boletín SAO (compatibilidad, Req 8.4)."""

    def resumen_consolidado(self) -> ResumenConsolidado:
        """Resumen de TODAS las fuentes bajo data/processed/.

        - Descubre subcarpetas de fuente (excluye las *_clasificado del conteo).
        - Agrupa registros por su campo `source`.
        - Combina (unión sin exclusión) y agrega.
        - Datasets *_clasificado solo alimentan `por_ofc`.
        - Si no hay datasets, devuelve un resumen vacío coherente (todo en 0).
        """
```

## Data Models

### Article Data Contract V1 (reutilizado)

El dataclass `ArticleRecord` ya implementa el contrato V1 como subconjunto, con
los campos: `article_id`, `title`, `doi`, `url`, `authors`, `publication_year`,
`journal`, `volume`, `issue`, `pages`, `publisher`, `language`, `abstract`,
`keywords`, `source`, `source_url`, `extraction_date`, `extraction_method`,
`processing_status`, `is_duplicate`, `duplicate_of`, `notes`, `inclusion_status`,
`exclusion_reason`, `ofcs`, `classification_method`, `classification_confidence`.

Se **extrae** a `bibliometrics/ingestion/article_record.py` para que ambos
extractores lo compartan sin duplicarlo. El contrato V1 **no cambia** sus campos
obligatorios ni opcionales (Req 2.4).

### Mapeo Publish or Perish → contrato V1

Publish or Perish exporta JSON (lista de objetos) o CSV (columnas). Mapeo
propuesto (campo no presente → `None`):

| Campo contrato V1 | Clave PoP JSON (típica) | Columna PoP CSV (típica) | Notas |
|-------------------|-------------------------|--------------------------|-------|
| `title` | `title` | `Title` | **Obligatorio.** Ausente/ambiguo → PENDIENTE_REVISIÓN. |
| `authors` | `authors` | `Authors` | **Obligatorio.** |
| `publication_year` | `year` | `Year` | **Obligatorio.** Validar 2020–2030. |
| `doi` | `doi` | `DOI` | Opcional. |
| `url` | `article_url` / `url` | `ArticleURL` | Opcional. |
| `journal` | `source` | `Source` | Opcional. Revista/medio. |
| `publisher` | `publisher` | `Publisher` | Opcional. |
| `volume` | `volume` | `Volume` | Opcional (si existe en el export). |
| `issue` | `issue` | `Issue` | Opcional. |
| `pages` | `pages` | `Pages` | Opcional. |
| `abstract` | `abstract` / `description` | `Abstract` | Opcional (mejor en JSON). |
| `keywords` | `keywords` | `Keywords` | Opcional. |
| `source` | — (fijo) | — (fijo) | **Fijo = "Google Scholar"** (Req 2.1). |
| `source_url` | `cites_url` / `url` | `CitesURL` | Opcional. |
| `extraction_date` | — (fecha de corrida) | — (fecha de corrida) | Fecha de ingesta. |
| `extraction_method` | — (fijo) | — (fijo) | p. ej. "Publish or Perish export V1". |
| `language` | `language` | `Language` | Opcional. |

> Nota: PoP usa su columna `Source` para la **revista/medio**, por eso se mapea a
> `journal`; el campo `source` del contrato (la **fuente** de ingesta) se fija a
> `"Google Scholar"`.

`article_id` **determinista** para Scholar (no se inventa un dato del artículo,
se deriva un identificador interno estable):

- Si hay DOI: `gs-<hash12(doi normalizado)>`.
- Si no hay DOI: `gs-<hash12(título normalizado + "|" + año)>`.
- `hash12` = primeros 12 hex de SHA-256. Determinista y estable entre corridas.

### Schemas Pydantic (backend)

```python
# backend/src/schemas/bibliometria.py  (se mantienen los existentes)

class AporteFuente(SchemaBase):
    fuente: str
    total_articulos: int
    completitud: list[CompletitudCampo]

class ResumenConsolidado(SchemaBase):
    alcance: str = "consolidado"          # identificador explícito (Req 6.4)
    total_articulos: int
    por_anio: list[ConteoPorClave]
    por_volumen: list[ConteoPorClave]
    completitud: list[CompletitudCampo]
    pendientes_revision: int
    posibles_duplicados: int
    fechas_dataset: list[str]             # una por fuente con dataset fechado
    clasificacion_disponible: bool = False
    por_ofc: list[ConteoOFC] = []
    sin_ofc: int = 0
    aporte_por_fuente: list[AporteFuente] = []
```

Todos heredan de `SchemaBase` (`extra="forbid"`). Los tipos del frontend
(`ResumenConsolidado`, `AporteFuente`) reflejan exactamente estos schemas.

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse en todas
las ejecuciones válidas del sistema: un enunciado formal de lo que el sistema
debe hacer. Las propiedades son el puente entre especificaciones legibles por
personas y garantías de correctitud verificables por máquina.*

> Tras la reflexión, se consolidaron solapamientos: la detección de formato
> JSON/CSV (1.2, 1.3) se unifica en una sola propiedad de "round-trip" de
> extensión; el año faltante (3.2) queda cubierto por la propiedad de obligatorios
> faltantes (2.3); y las invariantes de rango de las agregaciones (6.2) se
> agrupan en una propiedad de agregaciones bien formadas.

### Property 1: Detección de formato por extensión (case-insensitive)

*Para todo* nombre de archivo cuya extensión sea `.json` o `.csv` en cualquier
combinación de mayúsculas y minúsculas, `detect_format` devuelve `"json"` o
`"csv"` respectivamente, de forma independiente del casing.

**Validates: Requirements 1.2, 1.3**

### Property 2: No-invención de campos ausentes

*Para todo* registro del Export_PoP, cada campo del contrato que no esté presente
en el registro de entrada queda en `None` en el `ArticleRecord` producido (no se
sustituye por un valor inventado).

**Validates: Requirements 2.2**

### Property 3: Fuente fija y conformidad del contrato

*Para todo* registro producido por el conector de Google Scholar, `source ==
"Google Scholar"` y el registro cumple el contrato V1 (todos los obligatorios
presentes, o bien `inclusion_status == "PENDIENTE_REVISIÓN"`).

**Validates: Requirements 2.1**

### Property 4: Obligatorio faltante o ambiguo marca revisión

*Para todo* registro al que le falte `title`, `authors` o `publication_year`, o
cuya detección sea ambigua, el conector fija `inclusion_status =
"PENDIENTE_REVISIÓN"` con una nota no vacía, sin eliminar el registro.

**Validates: Requirements 2.3, 3.2**

### Property 5: Validación de período no descarta

*Para todo* registro con `publication_year` fuera de 2020–2030, el conector fija
`inclusion_status = "PENDIENTE_REVISIÓN"` con una nota y conserva el registro;
para años dentro del rango no fuerza ese estado por motivo de período.

**Validates: Requirements 3.1**

### Property 6: Robustez ante registros malformados

*Para toda* mezcla de registros válidos y malformados en la entrada, el pipeline
produce exactamente los registros válidos, descarta solo los malformados y no
aborta el lote.

**Validates: Requirements 1.5**

### Property 7: Conservación aritmética del resumen de ingesta

*Para toda* ejecución del pipeline, `registros_leídos == registros_procesados +
registros_descartados`.

**Validates: Requirements 1.6**

### Property 8: Inmutabilidad de `data/raw`

*Para todo* conjunto de archivos de entrada en `data/raw/google_scholar/`, tras
ejecutar el pipeline el contenido, nombre y fecha de modificación de esos
archivos permanecen idénticos, y ninguna escritura ocurre dentro de
`data/raw/google_scholar/`.

**Validates: Requirements 1.1**

### Property 9: Deduplicación básica dentro de la fuente

*Para todo* dataset de una fuente, dos registros con el mismo título normalizado
hacen que el segundo quede marcado `is_duplicate = true` con `duplicate_of`
apuntando al primero, sin eliminar ningún registro.

**Validates: Requirements 4.1**

### Property 10: El total consolidado es la suma por fuente

*Para toda* colección de datasets de fuente bajo `data/processed/`, el
`total_articulos` del resumen consolidado es igual a la suma de los totales de
cada fuente (unión sin exclusión), y es igual a la suma de los
`aporte_por_fuente[*].total_articulos`.

**Validates: Requirements 6.1, 7.1**

### Property 11: Agregaciones bien formadas

*Para todo* resumen consolidado, se cumple: `total_articulos >= 0`; la suma de
conteos de `por_anio` (sobre registros con año) no excede `total_articulos`; cada
porcentaje de `completitud` está en `[0, 100]`; y `pendientes_revision` y
`posibles_duplicados` están en `[0, total_articulos]`.

**Validates: Requirements 6.2**

### Property 12: Los datasets clasificados no se cuentan como fuente

*Para toda* presencia de un dataset clasificado (`*_clasificado`) derivado de una
fuente ya contada, el `total_articulos` consolidado no cambia respecto a contar
solo las fuentes; el dataset clasificado solo contribuye a `por_ofc`.

**Validates: Requirements 6.7**

### Property 13: No hay deduplicación entre fuentes

*Para todo* conjunto combinado con títulos repetidos en fuentes distintas, el
servicio no elimina ni combina esos registros: el `total_articulos` sigue siendo
la suma de los totales por fuente.

**Validates: Requirements 6.6**

### Property 14: Extensibilidad por descubrimiento

*Para toda* carpeta de fuente nueva en `data/processed/{fuente}/` con registros
conformes al contrato V1, el resumen consolidado incorpora esa fuente (en el
total y en `aporte_por_fuente`) sin cambios de código en el servicio ni en la
vista.

**Validates: Requirements 10.1**

## Error Handling

- **Entrada ausente o vacía (Req 1.4):** si `data/raw/google_scholar/` no existe,
  no es accesible, o no contiene `.json` ni `.csv`, el pipeline registra un
  mensaje informativo y **finaliza con éxito** sin procesar registros.
- **Registro malformado (Req 1.5):** se registra el archivo de origen y la
  posición del registro, se descarta solo ese registro y continúa el lote.
- **Campo obligatorio faltante/ambiguo (Req 2.3, 3.2):** no es un error de
  ejecución; el registro se conserva con `inclusion_status = PENDIENTE_REVISIÓN`
  y nota. Nunca se inventan valores.
- **Formato de archivo no soportado:** `detect_format` levanta `ValueError`; el
  pipeline lo captura por archivo, lo informa y continúa con los demás.
- **Servicio sin datasets (Req 6.5):** `resumen_consolidado()` devuelve un
  resumen vacío coherente (`total_articulos = 0`, distribuciones vacías,
  completitud 0, pendientes/duplicados 0) sin inventar datos.
- **Endpoint sin datasets (Req 8.3):** el endpoint consolidado responde de forma
  que el frontend pueda mostrar un estado vacío honesto (resumen vacío 200). El
  endpoint antiguo `boletin-sao/resumen` mantiene su contrato actual (404 vía
  `NotFoundError` si no hay dataset del Boletín).
- **API no expone trazas:** se mantiene el manejador de excepciones uniforme
  existente (`api/error_handlers.py`); los errores internos no filtran stack
  traces (tech.md §32).

## Technical Decisions

- **Descubrir fuentes por el campo `source`, no por un mapa fijo (Req 10.1).**
  Agrupar registros por su campo `source` es más robusto que mantener un mapa
  `{carpeta: nombre}`: añadir una fuente conforme al contrato no requiere editar
  el servicio. El nombre de carpeta solo sirve para localizar archivos y para
  detectar los `*_clasificado`.
- **Extraer `ArticleRecord` a un módulo compartido.** Evita duplicar el contrato
  entre extractores y aísla la fuente (Req 10.2). Refactor mínimo: `extract_boletin`
  pasa a importarlo; su comportamiento no cambia.
- **Extraer helpers de pipeline a `_common.py` (DRY).** `norm_title`,
  `mark_duplicates`, `validate_period`, `write_outputs`, `print_summary` se
  comparten entre Boletín y Scholar sin alterar la salida del Boletín.
- **`article_id` determinista para Scholar.** Derivar un id interno estable desde
  DOI o (título normalizado + año) permite reproducibilidad e idempotencia de
  reprocesos, sin inventar datos del artículo.
- **JSON recomendado para el Export_PoP (Req 11.3).** PoP preserva mejor la
  metadata y el resumen abreviado en JSON; la guía lo recomienda como formato por
  defecto. CSV se soporta igualmente.
- **Deduplicación cross-source `PENDING_VALIDATION` (Req 4.2, 6.6).** Hoy solo se
  aplica dedupe básico por título dentro de cada fuente; entre fuentes no se
  elimina ni combina nada.
- **Backend sin base de datos.** El servicio lee archivos de `data/processed/`;
  coherente con tech.md §12 y structure.md §30.
- **Compatibilidad del endpoint antiguo (Req 8.4).** `GET
  /bibliometria/boletin-sao/resumen` se mantiene durante la transición; el destino
  final de esa ruta queda `PENDING_VALIDATION`.

## Testing Strategy

Enfoque dual: **tests unitarios/property-based** para la lógica pura del conector
y del servicio, e **integración** para los endpoints y la vista.

**Librería de property-based testing:** `hypothesis` (Python), pinada en
`bibliometrics/requirements.txt` (y en el entorno de test del backend). No se
implementa PBT desde cero. Cada propiedad se implementa con **un** test de
propiedad, mínimo **100 iteraciones**, etiquetado con un comentario:
`# Feature: multi-source-bibliometria, Property N: <texto>`.

Property-based (pytest + hypothesis):

- Conector Scholar: Propiedades 1–7, 9 con generadores de registros PoP
  sintéticos (subconjuntos aleatorios de campos, años dentro/fuera de rango,
  títulos repetidos, registros malformados). Marcados como datos de prueba, no
  reales.
- Inmutabilidad de raw (Propiedad 8): generar carpetas temporales con archivos
  arbitrarios, snapshot de (nombre, hash, mtime), ejecutar pipeline sobre copia,
  verificar igualdad y que no se escribe dentro de raw.
- Servicio consolidado: Propiedades 10–14 con datasets de fuente sintéticos en
  carpetas temporales bajo un `data/processed/` de prueba (incluida una fuente
  "nueva" y un dataset `*_clasificado`).

Ejemplos / edge cases (pytest):

- Carpeta ausente/vacía/solo `.txt` → éxito sin registros (Req 1.4).
- Escritura de JSON+CSV y resumen con completitud (Req 5.1, 5.2).
- Servicio sin datasets → resumen vacío coherente (Req 6.5).
- Shape de salida: identificador de consolidado (Req 6.4), `aporte_por_fuente`
  con completitud en rango (Req 7.2).
- Guard del contrato: conjunto de obligatorios no cambia (Req 2.4).

Integración (FastAPI `TestClient`):

- `GET /bibliometria/resumen` con datasets de ejemplo → shape de Req 6 y 7
  (Req 8.1, 8.2).
- `GET /bibliometria/resumen` sin datasets → estado vacío honesto (Req 8.3).
- `GET /bibliometria/boletin-sao/resumen` sigue operativa (Req 8.4).

Verificación manual del frontend:

- Vista consume el consolidado; título "todas las fuentes" (Req 9.2); tarjetas y
  gráficos sobre el conjunto (Req 9.1); sección "Aporte por fuente" (Req 9.3);
  estado vacío honesto (Req 9.4); aviso de clasificación automática si hay OFC
  (Req 9.5).

Smoke / documentación:

- Ejecución del pipeline por un único comando CLI (Req 5.3).
- Existencia y contenido de la guía PoP: pasos, consulta, período 2020–2030,
  JSON recomendado, destino `data/raw/google_scholar/` (Req 11.1–11.3).

## Limitaciones conocidas / PENDING_VALIDATION

- **Deduplicación entre fuentes (cross-source):** `PENDING_VALIDATION`. Hoy solo
  dedupe básico por título dentro de cada fuente (Req 4.2, 6.6).
- **Clasificación por OFC:** metodología y algoritmo `PENDING_VALIDATION`. La
  vista solo muestra `por_ofc` si existe un dataset ya clasificado, indicando que
  es automática y sujeta a revisión humana (steering §4.2).
- **Destino final de `boletin-sao/resumen`** tras migrar el frontend:
  `PENDING_VALIDATION` (¿eliminar o conservar como filtro por fuente?).
- **Métricas bibliométricas avanzadas:** fuera de alcance; las agregaciones se
  limitan a las de la vista actual.
- **Obtención de Google Scholar:** no hay API; la descarga es manual/asistida vía
  Publish or Perish (coherente con el steering). No se implementa scraping.
- **Columnas PoP variables:** el export puede no traer `volume`/`issue`/`abstract`
  según la consulta; esos campos quedan `None` sin invención.
