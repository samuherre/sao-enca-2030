# Salidas del piloto de biodiversidad

Carpeta de **resultados exploratorios** del piloto de biodiversidad. Es
independiente del MVP de seguimiento ENCA y contiene **muestras pequeñas**, no
datasets completos. Ver `docs/biodiversity/pilot-status.md` para el estado
verificado.

> Propuesta de organización — **no implementada automáticamente**. Describe cómo
> conviene conservar los datos. No se han movido ni renombrado archivos
> existentes para no romper referencias.

## Estructura mínima propuesta

Mantener **GBIF y SiB como fuentes separadas** (no fusionar ni sumar registros):

```
outputs/biodiversity_pilot/
├── gbif/                       # Fuente: GBIF
│   ├── bird_record_counts_<UTC>.csv   # snapshot: ranking de publicadores
│   ├── bird_record_counts_<UTC>.json  # snapshot: total + ranking + metadatos
│   ├── history/                       # Fase 2: histórico consolidado (append)
│   │   ├── national_total_history.csv    # 1 fila por corte (total nacional)
│   │   └── publisher_history.csv         # 1 fila por (corte × publicador)
│   ├── arcgis/                        # Fase 3: CSV derivados para ArcGIS Online
│   │   ├── national_total_arcgis.csv     # contrato de publicación (total)
│   │   └── publisher_counts_arcgis.csv   # contrato de publicación (publicadores)
│   ├── occurrences.csv         # piloto exploratorio previo (muestra)
│   ├── occurrences_raw.json
│   ├── species.csv
│   └── summary.json            # incluye started_at/finished_at (fecha de consulta)
└── sib/                        # Fuente: SiB Colombia (fichas de especie)
    ├── sib_species_raw (1).json
    └── diagnostic_summary (1).json   # incluye checked_at_utc / run_at_utc
```

## Fase 1 — Cifras de aves GBIF

Generados por `scripts/biodiversity_pilot/gbif_bird_counts.py`. Contienen:

- `total_bird_records_colombia`: total nacional de registros de aves (GBIF).
- `publisher_ranking`: publicadores con `org_key`, `publisher_name` (resuelto
  desde GBIF cuando es posible) y `occurrence_count`.
- `source`, `query_params`, `extracted_at_utc`: procedencia y fecha/hora UTC.

El nombre incluye la marca de tiempo UTC de la corrida, de modo que cada
ejecución crea archivos nuevos sin sobrescribir corridas previas.

## Fase 2 — Histórico mensual consolidado

Generado por `scripts/biodiversity_pilot/gbif_bird_counts_history.py`, que
reutiliza la recolección de Fase 1 (mismos filtros `country=CO`, `taxonKey=212`,
total + top 5 publicadores). Cada ejecución:

1. Escribe un **snapshot** del corte (`bird_record_counts_<UTC>.*`), sin
   sobrescribir cortes anteriores ni los artefactos previos.
2. **Añade** (append) el corte a `history/`:
   - `national_total_history.csv`: una fila por corte con `extracted_at_utc`,
     `status`, `total_bird_records_colombia`, `source`, `country`, `taxon_key`,
     `errors`.
   - `publisher_history.csv`: una fila por (corte × publicador) con
     `extracted_at_utc`, `rank`, `org_key`, `publisher_name`, `occurrence_count`.

Reglas de integridad:

- El publicador se identifica por **`org_key`** (clave estable); el
  `publisher_name` puede variar entre cortes y se guarda tal cual en cada uno.
- Una consulta fallida **no** introduce ceros: si falta el total, el campo queda
  **vacío** (no `0`) y se conserva el `status` de error.
- Una corrida **sin datos usables** (ni total ni ranking) **no** añade filas al
  histórico, para no contaminarlo.
- Las diferencias entre cortes son diferencias entre los **valores agregados**
  que GBIF reporta en cada fecha; **no** representan necesariamente "registros
  nuevos".

Uso:

```
python scripts/biodiversity_pilot/gbif_bird_counts_history.py --facet-limit 5
python scripts/biodiversity_pilot/gbif_bird_counts_history.py --dry-run
```

> El programador automático (mensual) **no** está implementado todavía: por
> ahora el proceso se lanza manualmente. La automatización es una fase posterior.

## Fase 3 — Preparación para ArcGIS Online (local)

Generado por `scripts/biodiversity_pilot/export_for_arcgis.py`, que lee el
histórico de Fase 2 y produce en `arcgis/` dos CSV con un **contrato estable**
para publicar:

- Fecha normalizada `snapshot_date` (`YYYY-MM-DD`), más `extracted_at_utc` original.
- `org_key` como identificador estable del publicador; `publisher_name` como
  atributo que puede variar.
- `run_status` explícito; total vacío (nunca 0) si la consulta falló.
- **Sin coordenadas**: las cifras son agregados, no entidades geográficas.

Uso:

```
python scripts/biodiversity_pilot/export_for_arcgis.py
python scripts/biodiversity_pilot/export_for_arcgis.py --dry-run
```

> Estos CSV se **suben manualmente** a ArcGIS Online (carpeta de pruebas,
> privado). El script **no** publica nada ni usa credenciales. Procedimiento
> paso a paso en `docs/biodiversity/arcgis-upload-guide.md`.

## Fase 3 — Publicación automática mensual (Camino 3)

`scripts/biodiversity_pilot/publish_to_arcgis.py` encadena extracción (Fase 2),
exportación (Fase 3) y **publicación en ArcGIS Online**, y registra cada corrida
en `arcgis/run_log.csv`. El disparador mensual es el workflow
`.github/workflows/biodiversity-monthly.yml` (GitHub Actions), que **no** depende
de ningún PC personal.

- Credenciales: variables de entorno / GitHub Secrets. Nunca en el repositorio.
- Dependencia `arcgis`: opcional, solo en el runner de publicación
  (`requirements-publish.txt`); importada de forma perezosa.
- Modo seguro para practicar sin publicar:
  `python scripts/biodiversity_pilot/publish_to_arcgis.py --dry-run`
- `arcgis/run_log.csv`: una fila por ejecución (fecha UTC, estado, total,
  nº publicadores, si publicó y detalle). Una corrida fallida se registra como
  `published=no` sin borrar cifras previas.

Configuración inicial y verificación: `docs/biodiversity/arcgis-upload-guide.md`
(secciones 9.1–9.5).

## Reglas de procedencia

Cada conjunto debe poder responder, sin ambigüedad:

- **Fuente**: `gbif` o `sib` (dada por la subcarpeta, nunca mezclar).
- **Fecha de consulta**: tomada del campo de tiempo del propio archivo de
  resumen (`started_at_utc`/`finished_at_utc` en GBIF; `run_at_utc` /
  `checked_at_utc` en SiB). No inventar fechas.
- **Endpoint y parámetros**: quedan registrados en los `*.json` de resumen.

## Convención recomendada (a validar con SAO)

Para futuras corridas, nombrar las salidas con fuente y fecha, por ejemplo:

```
gbif/2026-10-21/occurrences.csv
sib/2026-10-21/sib_species_raw.json
```

Así se conserva el historial sin sobrescribir corridas anteriores. Esta
convención es una **propuesta**, pendiente de validación.

## Notas

- Los archivos SiB actuales tienen sufijo ` (1)` por una descarga duplicada.
  Ningún script del repositorio los lee por nombre, por lo que renombrarlos a
  `sib_species_raw.json` / `diagnostic_summary.json` sería seguro, pero se deja
  como decisión explícita (ver `docs/biodiversity/pilot-status.md` §6).
- No añadir aquí credenciales, tokens ni datasets grandes.
