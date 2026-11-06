# Análisis de referencia — `dataportal-explorer-master`

> Análisis **estático** del repositorio externo conservado en
> `references/external/dataportal-explorer-master.zip`. **No se ejecutó código,
> no se instalaron dependencias y no se extrajo** el ZIP; su contenido se
> inspeccionó leyendo entradas en memoria. Se usa **solo como referencia
> técnica**. No forma parte del MVP ENCA.

Fecha de la revisión: 2026-10-21.

---

## 1. Qué es

- `package.json` → nombre `sib-colombia-dataportal-explorer`, versión `0.2.0`,
  descripción: *"Web application for SIB Colombia dataportal map data
  exploration"*. Autores de la Universidad / Instituto Humboldt.
- `README.md` → una sola línea: *"Sib Colombia dataportal map explore
  application."* (documentación mínima).
- El ZIP contiene **977 entradas** en total.

Es una aplicación web **Node.js / Express** (motor de vistas Jade, estilos
Stylus) para explorar en un mapa los registros biológicos del antiguo portal de
datos de SiB Colombia. Por las dependencias y versiones, es un proyecto
**antiguo** (Express/Jade clásicos, `node >=0.10.36`).

---

## 2. Arquitectura observada (archivos verificados)

```
app/
├── controllers/
│   ├── occurrences/index.js      # endpoints de ocurrencias
│   └── distribution/index.js     # endpoints de distribución
├── models/
│   ├── elasticsearch/
│   │   └── occurrencesModel.js   # consultas a Elasticsearch (~120 KB)
│   └── mongodb/
│       ├── occurrences.js        # esquema Mongoose de ocurrencias
│       ├── geooccurrences.js     # esquema Mongoose agregado geográfico
│       └── *Groups.js            # catálogos (reino, filo, clase, país, depto…)
config/
├── initializers/databases.js     # conexión a Elasticsearch
└── environments/                 # all.js / development.js / production.js
```

- `app/controllers/occurrences/index.js` **no llama a servicios externos**:
  importa `models/elasticsearch/occurrencesModel` y resuelve todas las consultas
  contra **Elasticsearch** (p. ej. `getOccurrence`, `getOccurrencesResumeName`).
- `config/initializers/databases.js` conecta a un **Elasticsearch local**
  (`host: 'localhost', port: 9200`) tanto en `development` como en `production`.
- `config/environments/all.js` monta Express (puerto `3000`), carga el entorno
  y los routers, e inicializa las bases de datos.

**Conclusión de dependencia:** la aplicación depende de **infraestructura y
datos propios** (Elasticsearch en `localhost:9200`, y esquemas MongoDB). **No**
consulta en vivo APIs públicas de SiB/GBIF. Sin esa infraestructura poblada, la
aplicación **no es operativa**. No hay evidencia de que sus servicios originales
sigan disponibles.

---

## 3. Modelo de datos de ocurrencias (campos verificados)

Del esquema Mongoose `app/models/mongodb/occurrences.js` (colección
`occurrences`):

- Identificación: `occurrenceID`, `canonical`.
- Geografía: `location { lat, lon }`, `iso_country_code`, `iso_department_code`,
  `altitude_metres`, `depth_centimetres`.
- Procedencia: `data_provider_id/name`, `data_resource_id/name`, `rights`,
  `institution_code(_id)`, `collection_code(_id)`, `catalogue_number(_id)`,
  `citation`, `created`, `modified`.
- Taxonomía: `kingdom`, `phylum`, `taxonClass`, `order_rank`, `family`, `genus`,
  `species` (+ sus `*_concept_id`).
- Temporal: `year`, `month`, `occurrence_date`.

`geooccurrences.js` (colección `geooccurrences`) es una variante **agregada**
para mapa: añade `num_occurrences` y usa `latitude`/`longitude` como string, sin
los campos taxonómicos de texto. Útil para clustering/mapa de puntos.

---

## 4. Comparación con el campo del piloto GBIF

Equivalencias aprovechables (como referencia conceptual, no para copiar código):

| Explorer (Mongo) | Piloto GBIF (`occurrences.csv`) |
| --- | --- |
| `occurrenceID` | `gbif_id` |
| `canonical` / `species` | `scientific_name` / `species` |
| `location.lat` / `.lon` | `latitude` / `longitude` |
| `iso_country_code` | `country` |
| `iso_department_code` | `state_province` |
| `data_provider_name` / `data_resource_name` | `publisher` / `dataset_key` |
| `occurrence_date` / `year` / `month` | `event_date` |
| `citation` / `rights` | (no capturado aún) |

El esquema del explorador confirma que la **procedencia** (`data_provider`,
`data_resource`, `rights`, `citation`) es un campo de primera clase en el
dominio de ocurrencias. El piloto GBIF debería conservar explícitamente esa
procedencia.

---

## 5. Conclusiones verificables

1. Es una app Node/Express antigua de **exploración en mapa**, no una API de
   ingesta reutilizable directamente.
2. **No** consulta servicios externos: depende de Elasticsearch/MongoDB propios
   con datos previamente cargados; sin ellos no funciona.
3. **No hay evidencia** de que la infraestructura o los servicios originales
   sigan operativos.
4. Su **valor como referencia** es el **modelo de datos de ocurrencias** y la
   importancia de la procedencia, no su código ni su stack.
5. Se conserva como referencia estática en `references/external/`. **No se debe
   ejecutar, instalar ni portar al MVP.**
