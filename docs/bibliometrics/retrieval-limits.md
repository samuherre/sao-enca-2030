# Límite de Recuperación y Resumen de Ejecución — Componente B (SAO ENCA 2030)

## 1. Objetivo del documento

Este documento especifica, para el análisis bibliométrico del Componente B:

* el **Límite de Recuperación** (`Limite_Recuperacion`) por corrida de ingesta:
  su valor predeterminado recomendado, su configurabilidad y su comportamiento
  de corte;
* la posibilidad de ejecutar **corridas incrementales**;
* el **Resumen de Ejecución** (`Resumen_Ejecucion`) que cada corrida registra
  (recuperados, nuevos, duplicados y errores) y su mapeo conceptual con la
  estructura existente en el código del conector/pipeline;
* la **trazabilidad** de cada corrida.

Se apoya en el código ya existente del conector OpenAlex por API
(`bibliometrics/ingestion/openalex_api_client.py` y
`bibliometrics/pipelines/process_openalex_api.py`) y **no** introduce cambios de
código en este entregable: describe el comportamiento que esos módulos ya
soportan y documenta el valor recomendado.

Este documento se aplica junto con la Estrategia de Búsqueda
(`search-strategy.md`), los criterios de inclusión/exclusión
(`inclusion-exclusion-criteria.md`), la Clasificación Geográfica
(`geographic-classification.md`), el contrato de datos
(`article-data-contract.md`) y la especificación de integración por API key
(`api-key-integration.md`).

> Estado: **Propuesta V1** del Equipo_Proyecto, **sujeta a validación por SAO**.
> No es un criterio oficial de SAO. El **valor definitivo** del
> `Limite_Recuperacion` y la **estrategia de recuperación incremental** quedan
> registrados como `PENDING_VALIDATION` (ver `pending-validation.md` y la
> sección 7).

---

## 2. Límite de Recuperación por corrida

### 2.1 Valor predeterminado recomendado

El **Límite de Recuperación** (`Limite_Recuperacion`) es el número máximo de
resultados que una **Corrida de Ingesta** (`Corrida_Ingesta`) puede recuperar.

* **Valor predeterminado recomendado: 5.000 resultados por corrida.**

Este valor es una recomendación operativa del Equipo_Proyecto para acotar el
consumo de cuotas y mantener las corridas manejables, no un límite del corpus de
análisis (ver sección 5). El valor definitivo queda `PENDING_VALIDATION` a la
espera de confirmación por SAO.

### 2.2 El 5.000 se documenta como valor recomendado del flag `--max-results`

De forma deliberada, **el 5.000 se documenta como el valor recomendado del flag
`--max-results`** del pipeline, y **no** se cambia el valor por defecto del
código.

Estado actual del código (sin modificar en este spec):

* En `process_openalex_api.py`, el argumento de línea de comandos
  `--max-results` tiene `default=None`, es decir, **sin límite** por defecto.
* Ese valor se propaga a `ApiConfig.max_results`, que el conector usa como corte
  de recuperación.

Para aplicar el límite recomendado, la corrida debe pasar el flag de forma
explícita:

```
python bibliometrics/pipelines/process_openalex_api.py \
    --term "bird conservation" \
    --year-from 2020 --year-to 2030 \
    --max-results 5000
```

**No se cambia silenciosamente el default del código** (que hoy es `None` = sin
límite) para no alterar el comportamiento del conector ni de otros consumidores.
Si SAO confirma que 5.000 debe ser el default efectivo del pipeline, el cambio
se limitaría al `default` del argparse de `--max-results` en
`process_openalex_api.py`, dejando el conector (`iter_works`) intacto. Ese cambio
de default queda `PENDING_VALIDATION` (ver `pending-validation.md`, decisión
11.8).

> Nota de alcance del flag: en el código actual, `--max-results` /
> `ApiConfig.max_results` actúa como límite **por `Consulta`** dentro de una
> corrida (el corte se aplica al acumulado de works recuperados de cada
> `Consulta`). La semántica exacta del `Limite_Recuperacion` a nivel de
> **corrida completa** (una o varias `Consulta`s) frente al límite por
> `Consulta` es una de las decisiones sujetas a validación (ver sección 7).

### 2.3 Configurabilidad por corrida

El `Limite_Recuperacion` es **configurable por `Corrida_Ingesta`**: cada corrida
puede fijar su propio valor mediante el flag `--max-results`, sin recompilar ni
modificar código. Una corrida puede, por ejemplo, usar un límite menor para una
prueba acotada y el valor recomendado (5.000) para una corrida regular.

---

## 3. Comportamiento de corte

Cuando una corrida alcanza el `Limite_Recuperacion`, **detiene la recuperación
sin exceder el límite**.

Este comportamiento ya está soportado por el corte en `max_results` del
conector/pipeline. En `process_openalex_api.py`, la paginación por cursor
acumula los works recuperados y, en cuanto el número recuperado alcanza
`max_results`, la recuperación se detiene de inmediato y devuelve lo acumulado
sin pedir más páginas:

* si `max_results` es `None`, no hay corte por límite (se recorren todas las
  páginas disponibles de la `Consulta`);
* si `max_results` es un entero positivo, la recuperación se detiene al alcanzar
  exactamente ese número de works, sin excederlo;
* si `max_results` es `0` o negativo, no se recupera nada para esa `Consulta`.

El corte es **determinista** y no depende de la red: una vez alcanzado el límite,
no se emiten solicitudes adicionales para esa `Consulta`.

---

## 4. Corridas incrementales

El Componente B **permite varias `Corrida_Ingesta` incrementales**: la
recuperación no tiene que hacerse en una única ejecución masiva.

* Cada corrida es una ejecución independiente del pipeline
  (`process_openalex_api.py`) para una o varias `Consulta`s.
* Las corridas sucesivas pueden recuperar nuevos resultados sin rehacer todo el
  proceso desde cero.
* La **deduplicación** del pipeline (hoy, deduplicación simple por título
  mediante `mark_duplicates`, coherente con el `article_id` determinista de la
  fuente) permite que registros ya vistos se identifiquen como duplicados en
  lugar de contarse como nuevos.

La **estrategia incremental definitiva** (cómo se encadenan las corridas, cómo se
acumulan los resultados entre ejecuciones y cómo se versiona el corpus a lo largo
del tiempo) queda `PENDING_VALIDATION` (ver sección 7 y `pending-validation.md`,
decisión 11.8). Este documento solo confirma que las corridas incrementales
**están permitidas**; no fija aún su mecánica definitiva.

---

## 5. El `Limite_Recuperacion` es un control operativo por corrida, no el límite del corpus analítico

Es importante distinguir dos conceptos que **no** son lo mismo:

* **`Limite_Recuperacion`**: un **control operativo por corrida**. Acota cuántos
  resultados recupera **una** `Corrida_Ingesta` de la fuente, para controlar el
  consumo de cuotas y mantener las corridas acotadas. Se aplica sobre el
  **Corpus Recuperado** (lo que la fuente devuelve antes de deduplicar y de
  aplicar los criterios de inclusión/exclusión).

* **`Corpus_Analitico`**: el subconjunto definitivo de registros que, tras la
  deduplicación y la aplicación de los `Criterios_Inclusion_Exclusion`, forma
  parte del análisis bibliométrico.

El `Limite_Recuperacion` **no** es el límite del `Corpus_Analitico`. No define el
tamaño del corpus de análisis ni decide qué registros son relevantes: solo limita
cuánto se recupera en una corrida concreta. Esta distinción es coherente con la
diferencia **Corpus_Recuperado vs. Corpus_Analitico** descrita en la Estrategia
de Búsqueda y en los criterios de inclusión/exclusión.

---

## 6. Resumen de Ejecución y trazabilidad

### 6.1 Contenido del Resumen de Ejecución

Cuando una `Corrida_Ingesta` finaliza, registra un **Resumen de Ejecución**
(`Resumen_Ejecucion`) con, como mínimo, el número de resultados:

* **recuperados** — works crudos que la fuente devolvió en la corrida;
* **nuevos** — registros no duplicados tras la deduplicación;
* **duplicados** — registros identificados como duplicados;
* **errores** — fallos encontrados (páginas con reintentos agotados o errores
  permanentes, y works malformados descartados).

El Resumen de Ejecución se conserva como parte de la **trazabilidad** de la
corrida, para que cada corrida sea reproducible y auditable.

### 6.2 Mapeo conceptual con `_IngestStats` existente

El pipeline ya define la estructura `_IngestStats` en
`process_openalex_api.py`, con los contadores `works_recuperados`,
`paginas_consultadas`, `errores` y `paginas_con_error`, y los imprime en
`_print_ingest_summary`. El `Resumen_Ejecucion` se apoya conceptualmente en esa
estructura ya disponible:

| Concepto del `Resumen_Ejecucion` | Fuente en el código existente | Nota |
|----------------------------------|-------------------------------|------|
| Recuperados | `_IngestStats.works_recuperados` | works crudos recuperados de la API (antes de transformar). |
| Nuevos | registros no duplicados tras `mark_duplicates` | registros **no** marcados `is_duplicate`. |
| Duplicados | registros con `is_duplicate = true` | resultado de `mark_duplicates`. |
| Errores | `_IngestStats.errores` (+ `paginas_con_error`) | páginas con reintentos agotados / errores permanentes y works malformados descartados. |

El contador `paginas_consultadas` complementa la trazabilidad (número de páginas
pedidas a la API) y `paginas_con_error` deja constancia de **qué** `Consulta` y
**qué** página fallaron.

La formalización explícita de **"nuevos vs. duplicados"** dentro del resumen
impreso es un ajuste **documental/menor** derivado de datos que el pipeline ya
produce (`works_recuperados` del `_IngestStats` y el marcado `is_duplicate` de
`mark_duplicates`): **no** altera la lógica de deduplicación ni la lógica de
corte por `max_results`. Este documento no modifica el código; solo describe el
mapeo.

### 6.3 Trazabilidad de la corrida

El Componente B **conserva la trazabilidad de cada `Corrida_Ingesta`**. Además
del Resumen de Ejecución, la trazabilidad se apoya en:

* el dataset de salida en `data/processed/openalex/` (la corrida nunca escribe en
  `data/raw/`, que es inmutable);
* la identificación de la fuente (`source = "OpenAlex"`) y el esquema de
  `article_id` determinista que permite relacionar un registro con su origen;
* el registro de las `Consulta`s ejecutadas (términos y periodo) y de las páginas
  con error.

Los campos de trazabilidad a nivel de registro (por ejemplo, la consulta que
recuperó cada registro, propuestos en `article-data-contract.md` como evolución
futura) se documentan allí como propuesta V1 y quedan `PENDING_VALIDATION`.

---

## 7. Propuesta V1 y evolución futura

El valor recomendado (5.000) y el comportamiento descrito son la **propuesta
inicial (V1)** del Equipo_Proyecto, **sujeta a validación por SAO**. Quedan
registradas como `PENDING_VALIDATION` (ver `pending-validation.md`, decisión
11.8), entre otras, las siguientes decisiones:

* el **valor definitivo** del `Limite_Recuperacion` por corrida;
* si 5.000 debe pasar a ser el **default efectivo** del flag `--max-results` del
  pipeline (hoy `None`), en lugar de un valor recomendado;
* la **semántica exacta** del límite por corrida completa frente al límite por
  `Consulta` que aplica hoy el código;
* la **estrategia de recuperación incremental** (encadenamiento y acumulación de
  corridas, y versionamiento del corpus a lo largo del tiempo).

Estas decisiones podrán concretarse tras trabajar con el dataset real, observar
el consumo de cuotas y validar los resultados con SAO. Los cambios relevantes
deben documentarse y, cuando afecten decisiones arquitectónicas o el default del
código, registrarse mediante un ADR en `docs/decisions/`.
