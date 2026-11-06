# Piloto de biodiversidad — Estado verificado

> Este documento registra **solo hechos comprobados** inspeccionando los
> archivos del repositorio y los scripts que los generaron. Las cifras provienen
> de los archivos `summary.json` / `diagnostic_summary.json` reales. No se
> reejecutaron las consultas de red durante esta revisión.

Fecha de la revisión: 2026-10-21.

---

## 1. Ubicación de los artefactos (verificada)

```
scripts/biodiversity_pilot/
├── CodigopilotoGBIF.ipynb      # notebook del piloto GBIF
└── CodigopilotoSIB.ipynb       # notebook del diagnóstico SiB

outputs/biodiversity_pilot/
├── gbif/
│   ├── occurrences.csv         # 20 ocurrencias (muestra)
│   ├── occurrences_raw.json    # respuesta cruda de GBIF (~221 KB)
│   ├── species.csv             # 10 especies enriquecidas
│   └── summary.json            # resumen de la corrida
└── sib/
    ├── sib_species_raw (1).json       # 4 fichas del Catálogo SiB
    └── diagnostic_summary (1).json    # diagnóstico de servicios SiB

references/external/
└── dataportal-explorer-master.zip     # repositorio externo (referencia, ~3.7 MB)
```

> Nota: los dos archivos SiB tienen el sufijo ` (1)` en el nombre, probablemente
> por una descarga duplicada del navegador. Los nombres "canónicos" esperados
> por el script son `sib_species_raw.json` y `diagnostic_summary.json`. Ver
> §6 (limitaciones) antes de renombrar, para no romper referencias.

---

## 2. Fuentes y endpoints comprobados

| Fuente | Endpoint | Tipo | Resultado verificado |
| --- | --- | --- | --- |
| GBIF | `https://api.gbif.org/v1/occurrence/search` | Ocurrencias | ✅ Funcional |
| GBIF | `https://api.gbif.org/v1/species/{key}` y `.../vernacularNames` | Taxonomía | ✅ Funcional (enriquecimiento) |
| SiB Catálogo | `https://api.catalogo.biodiversidad.co/record_search/search` | Especies | ⚠️ Funcional con salvedades |
| SiB Ocurrencias | `https://api.biodiversidad.co/occurrence/search` | Ocurrencias | ❌ Falla por DNS |
| SiB Ocurrencias (histórico) | `http://maps.sibcolombia.net/rest/occurrences/mappoints` | Ocurrencias | ❌ No operativo (histórico ~2016) — no reutilizar |

---

## 3. GBIF — resultado verificado

Parámetros de la consulta (según el notebook y `summary.json`):
`country=CO`, `taxonKey=212` (Aves), `limit=20`, `offset=0`.

Según `outputs/biodiversity_pilot/gbif/summary.json`:

- `occurrences_returned`: **20**
- `unique_species_found`: **17**
- `species_enriched`: **10** (límite `species_enrichment_limit=10`)
- `errors`: **[]** (sin errores)
- `status`: `completed`
- Nota del propio archivo: *muestra exploratoria; no representa el total de
  registros de aves de Colombia.*

Observaciones al inspeccionar los datos:

- `occurrences.csv` contiene 20 filas con: `gbif_id`, `scientific_name`,
  `species`, `event_date`, `country`, `state_province`, `latitude`,
  `longitude`, `dataset_key`, `publisher`, `source_url`. Las columnas
  `locality` y `publisher` aparecen vacías en la muestra.
- Todas las ocurrencias comparten `dataset_key`
  `50c9509d-22c7-4a22-a47d-8c48425ef4a7`.
- Una fila (`gbif_id=5938114431`, `Daptrius Vieillot, 1816`) no trae `species`:
  es una identificación a nivel de **género**, no de especie. Esto explica por
  qué hay 17 especies únicas y no 20.
- `species.csv` trae 10 especies con taxonomía (familia, reino, estado
  taxonómico) y nombres comunes multilingües separados por ` | `.

**Conclusión:** el piloto GBIF funciona de extremo a extremo y produce datos
coherentes de ocurrencias + taxonomía para una muestra pequeña.

---

## 4. SiB Catálogo de especies — resultado verificado

Según `diagnostic_summary (1).json`:

- Consulta `q="Leopardus pardalis"`, `size=5` → **HTTP 200**, respuesta tipo
  lista con **4 ítems**. `status=success`.
- `content_type`: `application/json; charset=utf-8`.

Observaciones al inspeccionar `sib_species_raw (1).json` (4 fichas):

- Los resultados **no son todos** `Leopardus pardalis`. Incluyen además
  `Puma yagouaroundi` y `Leopardus wiedii`. **La búsqueda no devuelve
  coincidencias exactas**; se comporta como búsqueda por relevancia/similitud.
- Son **fichas de especie (taxonomía + nombres comunes + estado de amenaza +
  imagen)**, no registros de ocurrencia.
- Campos presentes: `scientificNameSimple`, `commonNames[]`,
  `threatStatusValue`, a veces `imageInfo`, y `creation_date` (fechas de 2016–2017).
- Los ejemplos devueltos son **mamíferos** (felinos), no aves — consecuencia de
  usar `Leopardus pardalis` como término de prueba.

> Observación adicional sobre un intento previo documentado en el propio
> notebook: una consulta con `q="aves Colombia"&size=10` devolvió **HTTP 406**.
> Esto sugiere que ciertos términos/parámetros no son aceptados por el servicio.
> Esta corrida no está en `diagnostic_summary (1).json`; se cita como
> comportamiento observado, pendiente de reproducir.

**Conclusión:** el Catálogo SiB responde y entrega fichas taxonómicas, pero
(1) la búsqueda es aproximada y (2) **no provee ocurrencias**.

---

## 5. SiB Ocurrencias — errores verificados

- `https://api.biodiversidad.co/occurrence/search` (`country=CO`, `limit=10`):
  **falla por resolución DNS** (`NameResolutionError`,
  `Failed to resolve 'api.biodiversidad.co'`). Registrado en
  `diagnostic_summary (1).json`.
- `http://maps.sibcolombia.net/rest/occurrences/mappoints`: endpoint
  **histórico (~2016)**, falla por DNS. **No debe reutilizarse** como si
  estuviera operativo.
- El script `pilot_sib_occurrences.py` mencionado en notas previas **no existe**
  en el repositorio. Los archivos que supuestamente generaría
  (`occurrences_raw.json`, `occurrences.csv`, `occurrences_summary.json` del
  lado SiB) **no se encontraron**. Dado que la consulta falló por DNS, se asume
  que no se generaron. No se reconstruyen ni se inventan.

**Conclusión:** **no hay una vía verificada para obtener ocurrencias de SiB**
en este momento. Las ocurrencias disponibles provienen únicamente de GBIF.

---

## 6. Limitaciones y riesgos abiertos

1. **Sin ocurrencias de SiB.** Los dos endpoints de ocurrencias SiB probados no
   resuelven por DNS. Falta confirmar con SiB/SAO cuál es el servicio vigente.
2. **Búsqueda SiB aproximada.** El Catálogo devuelve taxones que no coinciden
   exactamente con la consulta; no debe tratarse como coincidencia exacta.
3. **Muestras pequeñas.** GBIF: 20 ocurrencias / 17 especies. SiB: 4 fichas. No
   son representativas; son pruebas de conectividad y forma de los datos.
4. **Nombres de archivo con sufijo ` (1)`** en la carpeta SiB. Renombrarlos a
   los nombres canónicos no rompería código (ningún script del repo los lee),
   pero se deja la decisión documentada para evitar confusión. Ver recomendación
   en `overview.md`.
5. **Notebooks escritos para Google Colab.** Las rutas de salida internas de los
   notebooks apuntan a `outputs/gbif_pilot` y `outputs/sib_pilot`
   (no a `outputs/biodiversity_pilot/...`). Es decir, los archivos actuales
   fueron colocados manualmente en la estructura del repo; reejecutar los
   notebooks tal cual escribiría en otras rutas. Ver nota en §1.
6. **Versionado de datos.** `outputs/` y `references/` no están cubiertos por
   `.gitignore`. Los artefactos actuales son pequeños y no contienen secretos,
   pero conviene decidir con SAO si estos outputs deben versionarse.
7. **Licencias y atribución.** No se ha verificado el régimen de licencias de los
   datos de GBIF y SiB para el uso previsto. `PENDING_VALIDATION`.

---

## 7. Conteos agregados GBIF (verificado 2026-10-21)

Para un sitio de **cifras** (no de descarga masiva), GBIF permite pedir conteos
sin traer registros, usando `limit=0` y `facet`:

- `GET /v1/occurrence/search?country=CO&taxonKey=212&limit=0`
  → campo `count`. Valor observado: **26.753.542** registros de aves en Colombia.
- `...&limit=0&facet=publishingOrg&facetLimit=N`
  → ranking de publicadores (orgKey + conteo). El publicador principal concentra
  la gran mayoría (~24,15 M de ~26,75 M).

Implicación: el objetivo de "Biodiversidad en Cifras para aves" se resuelve con
**consultas de agregación livianas** (respuesta de pocos KB), sin descargar las
ocurrencias. Los orgKey se pueden resolver a nombre con `GET /v1/organization/{key}`.

> Nota: `count` es el total "vivo" en el momento de la consulta; para tener
> histórico comparable mes a mes conviene **almacenar un corte mensual** con su
> fecha (decisión en `overview.md` §5).

## 8. Resumen

- **Funciona:** piloto GBIF (ocurrencias + taxonomía), conteos agregados GBIF y
  Catálogo de especies SiB (fichas, con búsqueda aproximada).
- **No funciona:** ocurrencias de SiB (DNS) y el endpoint histórico de mapas.
- **No existe:** `pilot_sib_occurrences.py` ni sus salidas.
- **Fuente única de ocurrencias/cifras hoy:** GBIF.
