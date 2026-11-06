# Requirements Document

Fuente OpenAlex de alto volumen vía Publish or Perish (Componente B)

## Introduction

La fuente Google Scholar, incorporada en el spec `multi-source-bibliometria`,
resultó de **bajo volumen en la práctica**: Google limita el acceso automático
a Scholar y Publish or Perish (PoP) devuelve lotes pequeños (decenas de
resultados) sin captcha. Esto es coherente con el steering, que define Google
Scholar como fuente de **"descubrimiento / validación", prioridad media,
obtención "manual / exportación limitada"** (`.kiro/steering/bibliometrics.md`).

Este spec incorpora **OpenAlex** como fuente de **alto volumen** para el análisis
bibliométrico. OpenAlex es una base abierta y gratuita de trabajos académicos,
accesible desde PoP como fuente de datos, que permite exportar lotes grandes de
resultados en JSON o CSV sin las limitaciones de Scholar.

El spec **reutiliza la infraestructura existente** del Componente B sin
rediseñarla: el patrón de **conectores por fuente** (cada fuente tiene su
extractor propio pero todas producen registros conforme al **Article Data
Contract V1**, `docs/bibliometrics/article-data-contract.md`), el
**Servicio_Consolidado** que descubre cualquier carpeta bajo `data/processed/` y
agrupa por el campo `source`, y la **Vista_Bibliometria** consolidada. Por el
Requisito 10 del spec `multi-source-bibliometria`, el backend y el frontend
incorporan una fuente nueva **sin cambios de código** en cuanto existe su
`Dataset_Procesado`. Por tanto, el alcance de este spec es esencialmente el
**conector + pipeline de ingesta de OpenAlex + guía de exportación**.

Principio rector no negociable (`product.md` §15, §22; `data-and-domain.md` §37;
`tech.md` §2.1): **no falsear el origen de los datos**. Los registros de OpenAlex
se etiquetan como OpenAlex, nunca como otra fuente. No se reutiliza la carpeta ni
la etiqueta de Google Scholar para datos de OpenAlex.

Decisiones estables y contexto en `.kiro/steering/bibliometrics.md`.

## Glossary

- **Sistema_Bibliometria**: conjunto del Componente B que ingiere, procesa y
  expone información bibliométrica dentro del proyecto SAO.
- **Conector_OpenAlex**: módulo de extracción específico de OpenAlex que
  transforma el export de Publish or Perish en registros del Article Data
  Contract V1.
- **Pipeline_OpenAlex**: proceso reproducible por línea de comandos que ejecuta
  el Conector_OpenAlex sobre los archivos de entrada y escribe el dataset
  procesado.
- **Servicio_Consolidado**: componente del backend (ya existente) que lee los
  datasets procesados de todas las fuentes y calcula las agregaciones
  consolidadas.
- **Vista_Bibliometria**: página del frontend (ya existente) que presenta el
  resumen consolidado.
- **Article Data Contract V1**: contrato de datos común a todas las fuentes
  (`docs/bibliometrics/article-data-contract.md`).
- **PoP / Publish or Perish**: herramienta externa que el usuario usa para
  consultar OpenAlex y exportar un lote de resultados (JSON o CSV).
- **Export_PoP_OpenAlex**: archivo real exportado por Publish or Perish desde la
  fuente OpenAlex, colocado por el usuario en `data/raw/openalex/`.
- **Dataset_Procesado**: salida de un conector en `data/processed/{fuente}/`,
  conforme al Article Data Contract V1, en formatos JSON y CSV.
- **Período_Inclusión**: rango de años de publicación 2020–2030.
- **PENDIENTE_REVISIÓN**: valor de `inclusion_status` para registros con un
  campo obligatorio faltante, detección ambigua o año fuera del
  Período_Inclusión.
- **OFC**: Objeto Focal de Conservación (11 en total; relación con artículo es
  multilabel).

## Requirements

### Requisito 1 — Ingesta del export de OpenAlex (Publish or Perish)

**Historia:** Como equipo del proyecto, quiero procesar el export real de Publish or Perish de OpenAlex almacenado localmente, para incorporar OpenAlex como fuente de alto volumen sin captura manual registro por registro.

#### Criterios de aceptación

1. CUANDO existan uno o más archivos de Export_PoP_OpenAlex en `data/raw/openalex/` ENTONCES EL Pipeline_OpenAlex DEBERÁ procesarlos conservando los archivos originales sin alteración de contenido, nombre ni fecha de modificación, escribiendo cualquier resultado únicamente en rutas distintas de `data/raw/openalex/`.
2. CUANDO un archivo de Export_PoP_OpenAlex tenga extensión `.json` (sin distinción entre mayúsculas y minúsculas) ENTONCES EL Conector_OpenAlex DEBERÁ interpretarlo como formato JSON.
3. CUANDO un archivo de Export_PoP_OpenAlex tenga extensión `.csv` (sin distinción entre mayúsculas y minúsculas) ENTONCES EL Conector_OpenAlex DEBERÁ interpretarlo como formato CSV.
4. IF `data/raw/openalex/` no existe, no es accesible, o no contiene ningún archivo con extensión `.json` ni `.csv` ENTONCES EL Pipeline_OpenAlex DEBERÁ registrar un mensaje informativo indicando la ausencia de archivos de entrada y finalizar con estado de éxito sin procesar ningún registro.
5. IF un registro individual del Export_PoP_OpenAlex está malformado o no puede procesarse ENTONCES EL Pipeline_OpenAlex DEBERÁ registrar el problema indicando el archivo de origen y la posición del registro dentro de ese archivo, descartar únicamente ese registro, y continuar procesando los registros restantes.
6. CUANDO el Pipeline_OpenAlex finalice el procesamiento de todos los archivos ENTONCES DEBERÁ registrar un resumen con el número total de registros leídos, el número de registros procesados correctamente y el número de registros descartados por estar malformados.

### Requisito 2 — Extracción conforme al Article Data Contract V1

**Historia:** Como analista, quiero que cada trabajo de OpenAlex se represente según el Article Data Contract V1, para garantizar consistencia entre fuentes.

#### Criterios de aceptación

1. CUANDO EL Conector_OpenAlex procese un registro ENTONCES EL Conector_OpenAlex DEBERÁ producir un registro conforme al Article Data Contract V1 con `source = "OpenAlex"`.
2. THE Conector_OpenAlex SHALL NO producir ningún registro con un valor de `source` distinto de `"OpenAlex"`; en particular, SHALL NO etiquetar los registros como Google Scholar ni como ninguna otra fuente.
3. CUANDO un campo del contrato no pueda detectarse en el Export_PoP_OpenAlex ENTONCES EL Conector_OpenAlex DEBERÁ fijar ese campo en `null` sin generar un valor sustituto.
4. IF un campo obligatorio del Article Data Contract V1 está ausente o su detección es ambigua ENTONCES EL Conector_OpenAlex DEBERÁ fijar `inclusion_status = "PENDIENTE_REVISIÓN"` y registrar una nota explicativa en `notes`.
5. THE Article Data Contract V1 SHALL permanecer sin cambios de campos obligatorios u opcionales como consecuencia de este spec.
6. THE `article_id` generado por el Conector_OpenAlex SHALL ser determinista y reproducible entre corridas para el mismo registro de entrada, y SHALL distinguirse de los identificadores de otras fuentes para evitar colisiones.

### Requisito 3 — Validación de período de inclusión

**Historia:** Como analista, quiero que se valide el Período_Inclusión 2020–2030 sobre los trabajos de OpenAlex, para mantener el alcance acordado.

#### Criterios de aceptación

1. IF el `publication_year` de un registro está fuera del Período_Inclusión 2020–2030 ENTONCES EL Conector_OpenAlex DEBERÁ fijar `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota, sin descartar el registro.
2. IF un registro no tiene `publication_year` detectable ENTONCES EL Conector_OpenAlex DEBERÁ dejar el campo en `null` y fijar `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota.

### Requisito 4 — Deduplicación básica dentro de la fuente

**Historia:** Como analista, quiero detectar duplicados evidentes dentro del dataset de OpenAlex, para no contar dos veces el mismo trabajo.

#### Criterios de aceptación

1. WHEN dos registros del dataset de OpenAlex comparten el mismo título normalizado ENTONCES EL Conector_OpenAlex DEBERÁ marcar el segundo registro con `is_duplicate = true` y `duplicate_of` apuntando al primero, sin eliminar ningún registro.
2. THE estrategia de deduplicación entre fuentes distintas SHALL permanecer `PENDING_VALIDATION`.

### Requisito 5 — Salida consolidada y reproducible del conector

**Historia:** Como equipo, quiero un dataset de OpenAlex en formatos usables y generado con un único comando, para revisarlo y reprocesarlo sin pasos manuales.

#### Criterios de aceptación

1. CUANDO EL Pipeline_OpenAlex termine de procesar ENTONCES EL Pipeline_OpenAlex DEBERÁ escribir el Dataset_Procesado en `data/processed/openalex/` en formato JSON y en formato CSV.
2. CUANDO EL Pipeline_OpenAlex termine ENTONCES EL Pipeline_OpenAlex DEBERÁ mostrar un resumen con el número de registros procesados y la completitud por campo.
3. THE Pipeline_OpenAlex SHALL poder ejecutarse mediante un único comando de línea de comandos sin interfaz gráfica.

### Requisito 6 — Incorporación automática al análisis consolidado (sin rediseño)

**Historia:** Como coordinador de SAO, quiero que OpenAlex aparezca en el análisis consolidado existente sin modificar el servicio ni la vista, para aprovechar la base multi-fuente ya construida.

#### Criterios de aceptación

1. CUANDO EL Pipeline_OpenAlex haya escrito su Dataset_Procesado conforme al Article Data Contract V1 en `data/processed/openalex/` ENTONCES EL Servicio_Consolidado DEBERÁ incorporar OpenAlex al resumen consolidado (total, distribuciones, completitud, pendientes, posibles duplicados y aporte por fuente) sin cambios de código en el Servicio_Consolidado ni en la Vista_Bibliometria.
2. THE Vista_Bibliometria SHALL mostrar OpenAlex como una fuente más dentro del Aporte_Por_Fuente, con su nombre de fuente real `"OpenAlex"`.
3. THE lógica específica de extracción de OpenAlex SHALL permanecer aislada en el módulo del Conector_OpenAlex, sin acoplarse al Conector_Scholar ni modificar su comportamiento.
4. THE Dataset_Procesado de Google Scholar existente SHALL permanecer intacto y seguir contándose como su propia fuente en el consolidado.

### Requisito 7 — Trazabilidad y no falsear el origen

**Historia:** Como responsable de calidad de datos, quiero que el origen de cada registro sea fiel a su fuente real, para preservar la trazabilidad exigida por el proyecto.

#### Criterios de aceptación

1. THE Conector_OpenAlex SHALL leer exclusivamente de `data/raw/openalex/` y SHALL escribir exclusivamente en `data/processed/openalex/`.
2. THE Sistema_Bibliometria SHALL NO requerir ni sugerir colocar exports de OpenAlex en `data/raw/google_scholar/` ni etiquetarlos como Google Scholar.
3. WHERE un registro conserve un identificador o URL propio de OpenAlex, THE Conector_OpenAlex SHALL preservarlo en los campos de procedencia del contrato (p. ej. `source_url`) cuando esté disponible, sin inventarlo cuando no lo esté.

### Requisito 8 — Guía de exportación desde Publish or Perish (OpenAlex)

**Historia:** Como usuario de SAO, quiero una guía paso a paso para exportar los datos de OpenAlex con Publish or Perish, para generar el Export_PoP_OpenAlex real de forma reproducible y de alto volumen.

#### Criterios de aceptación

1. THE Sistema_Bibliometria SHALL incluir un documento de guía en `docs/` que describa, paso a paso, cómo generar el Export_PoP_OpenAlex con Publish or Perish seleccionando OpenAlex como fuente de datos.
2. THE guía SHALL indicar la consulta del tema de conservación de aves, el Período_Inclusión 2020–2030, el formato JSON recomendado y la ubicación de destino `data/raw/openalex/`.
3. THE guía SHALL describir la estrategia de varias consultas complementarias (un archivo por consulta) para cubrir el tema con mayor volumen, y SHALL indicar que el Pipeline_OpenAlex combina todos los archivos de la carpeta y marca los duplicados por título.
4. WHERE los términos de búsqueda y los nombres de archivo se presenten en la guía, THE guía SHALL marcarlos explícitamente como propuesta del equipo a validar con SAO, sin presentarlos como criterio oficial de SAO.

## Fuera de alcance (explícito)

- Modificar el Servicio_Consolidado, el Endpoint_Consolidado o la
  Vista_Bibliometria: la base multi-fuente ya los cubre (Req 10 del spec
  `multi-source-bibliometria`). Solo se verificará que OpenAlex aparece sin
  cambios de código.
- Clasificación por OFC automática (metodología `PENDING_VALIDATION`).
- Deduplicación definitiva entre fuentes distintas (`PENDING_VALIDATION`).
- Consultas programáticas a la API de OpenAlex o scraping: la obtención es
  **manual/asistida** vía Publish or Perish (coherente con la obtención de las
  demás fuentes del Componente B).
- Reutilizar la carpeta o la etiqueta de Google Scholar para datos de OpenAlex.
- Uso de datos sintéticos o `DEMO_DATA` como datos reales: el pipeline procesa
  el Export_PoP_OpenAlex real cuando exista.

## Notas de PENDING_VALIDATION

- Mapeo exacto campo-a-campo del export de PoP-OpenAlex al Article Data
  Contract V1: se definirá en la fase de **diseño**, inspeccionando un
  Export_PoP_OpenAlex real de muestra (no se inventa aquí).
- Términos de búsqueda y nombres de archivo de la guía: propuesta del equipo,
  `PENDING_VALIDATION` con SAO.
- Deduplicación entre fuentes (cross-source): `PENDING_VALIDATION`.
- Metodología y algoritmo de clasificación por OFC: `PENDING_VALIDATION`.
