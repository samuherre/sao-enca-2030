# Requirements Document

Bibliometría multi-fuente y análisis consolidado (Componente B)

## Introduction

Hoy la vista de Bibliometría muestra el análisis de **una sola fuente**: el
Boletín SAO. Este spec incorpora **Google Scholar** como segunda fuente y
generaliza el análisis para que sea **consolidado** (todas las fuentes juntas en
un único análisis), nunca una vista o pestaña por fuente. Como dato
complementario se añade el **aporte por fuente** (cuántos artículos y qué
completitud aporta cada fuente al total), sin fragmentar el análisis.

El spec respeta el patrón de **conectores por fuente** ya establecido: cada
fuente tiene su propio extractor pero todas producen registros conforme al
**Article Data Contract V1** (`docs/bibliometrics/article-data-contract.md`) y
escriben su dataset procesado en `data/processed/{fuente}/`. El servicio y la
vista consumen esos datasets ya procesados.

Decisiones estables y contexto en `.kiro/steering/bibliometrics.md`. Alcance de
este spec: **conector Google Scholar + servicio/endpoint consolidado + vista
generalizada + guía de exportación de Publish or Perish**. Fuera de alcance al
final del documento.

## Glossary

- **Sistema_Bibliometria**: conjunto del Componente B que ingiere, procesa y
  expone información bibliométrica dentro del proyecto SAO.
- **Conector_Scholar**: módulo de extracción específico de Google Scholar que
  transforma el export de Publish or Perish en registros del Article Data
  Contract V1.
- **Pipeline_Scholar**: proceso reproducible por línea de comandos que ejecuta
  el Conector_Scholar sobre los archivos de entrada y escribe el dataset
  procesado.
- **Servicio_Consolidado**: componente del backend que lee los datasets
  procesados de todas las fuentes y calcula las agregaciones consolidadas.
- **Endpoint_Consolidado**: ruta HTTP que expone el resumen consolidado al
  frontend.
- **Vista_Bibliometria**: página del frontend que presenta el resumen
  consolidado.
- **Article Data Contract V1**: contrato de datos común a todas las fuentes
  (`docs/bibliometrics/article-data-contract.md`).
- **PoP / Publish or Perish**: herramienta externa que el usuario usa para
  consultar Google Scholar y exportar un lote de resultados (JSON o CSV).
- **Export_PoP**: archivo real exportado por Publish or Perish, colocado por el
  usuario en `data/raw/google_scholar/`.
- **Dataset_Procesado**: salida de un conector en `data/processed/{fuente}/`,
  conforme al Article Data Contract V1, en formatos JSON y CSV.
- **Dataset_Procesado de fuente**: Dataset_Procesado que representa los
  artículos aportados por una fuente concreta (p. ej. Boletín SAO o Google
  Scholar) y que cuenta al total consolidado de artículos.
- **dataset clasificado**: dataset derivado que contiene la clasificación por
  OFC de artículos ya existentes; se usa únicamente como origen de la
  distribución por OFC y no cuenta como fuente adicional de artículos.
- **Aporte_Por_Fuente**: desglose complementario que indica, por fuente, el
  número de artículos y la completitud de metadata que aporta al total
  consolidado.
- **Período_Inclusión**: rango de años de publicación 2020–2030.
- **PENDIENTE_REVISIÓN**: valor de `inclusion_status` para registros con un
  campo obligatorio faltante, detección ambigua o año fuera del
  Período_Inclusión.
- **OFC**: Objeto Focal de Conservación (11 en total; relación con artículo es
  multilabel).

## Requirements

### Requisito 1 — Ingesta del export de Google Scholar (Publish or Perish)

**Historia:** Como equipo del proyecto, quiero procesar el export real de Publish or Perish de Google Scholar almacenado localmente, para incorporar Google Scholar como segunda fuente sin captura manual registro por registro.

#### Criterios de aceptación

1. CUANDO existan uno o más archivos de Export_PoP en `data/raw/google_scholar/` ENTONCES EL Pipeline_Scholar DEBERÁ procesarlos conservando los archivos originales sin alteración de contenido, nombre ni fecha de modificación, escribiendo cualquier resultado únicamente en rutas distintas de `data/raw/google_scholar/`.
2. CUANDO un archivo de Export_PoP tenga extensión `.json` (sin distinción entre mayúsculas y minúsculas) ENTONCES EL Conector_Scholar DEBERÁ interpretarlo como formato JSON.
3. CUANDO un archivo de Export_PoP tenga extensión `.csv` (sin distinción entre mayúsculas y minúsculas) ENTONCES EL Conector_Scholar DEBERÁ interpretarlo como formato CSV.
4. IF `data/raw/google_scholar/` no existe, no es accesible, o no contiene ningún archivo con extensión `.json` ni `.csv` ENTONCES EL Pipeline_Scholar DEBERÁ registrar un mensaje informativo indicando la ausencia de archivos de entrada y finalizar con estado de éxito sin procesar ningún registro.
5. IF un registro individual del Export_PoP está malformado o no puede procesarse ENTONCES EL Pipeline_Scholar DEBERÁ registrar el problema indicando el archivo de origen y la posición del registro dentro de ese archivo, descartar únicamente ese registro, y continuar procesando los registros restantes.
6. CUANDO el Pipeline_Scholar finalice el procesamiento de todos los archivos ENTONCES DEBERÁ registrar un resumen con el número total de registros leídos, el número de registros procesados correctamente y el número de registros descartados por estar malformados.

### Requisito 2 — Extracción conforme al Article Data Contract V1

**Historia:** Como analista, quiero que cada artículo de Google Scholar se
represente según el Article Data Contract V1, para garantizar consistencia entre
fuentes.

#### Criterios de aceptación

1. CUANDO EL Conector_Scholar procese un registro ENTONCES EL Conector_Scholar
   DEBERÁ producir un registro conforme al Article Data Contract V1 con
   `source = "Google Scholar"`.
2. CUANDO un campo del contrato no pueda detectarse en el Export_PoP ENTONCES EL
   Conector_Scholar DEBERÁ fijar ese campo en `null` sin generar un valor
   sustituto.
3. IF un campo obligatorio del Article Data Contract V1 está ausente o su
   detección es ambigua ENTONCES EL Conector_Scholar DEBERÁ fijar
   `inclusion_status = "PENDIENTE_REVISIÓN"` y registrar una nota explicativa en
   `notes`.
4. THE Article Data Contract V1 SHALL permanecer sin cambios de campos
   obligatorios u opcionales como consecuencia de este spec.

### Requisito 3 — Validación de período de inclusión

**Historia:** Como analista, quiero que se valide el Período_Inclusión 2020–2030
sobre los artículos de Google Scholar, para mantener el alcance acordado.

#### Criterios de aceptación

1. IF el `publication_year` de un registro está fuera del Período_Inclusión
   2020–2030 ENTONCES EL Conector_Scholar DEBERÁ fijar
   `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota, sin descartar el
   registro.
2. IF un registro no tiene `publication_year` detectable ENTONCES EL
   Conector_Scholar DEBERÁ dejar el campo en `null` y fijar
   `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota.

### Requisito 4 — Deduplicación básica dentro de la fuente

**Historia:** Como analista, quiero detectar duplicados evidentes dentro del
dataset de Google Scholar, para no contar dos veces el mismo artículo.

#### Criterios de aceptación

1. WHEN dos registros del dataset de Google Scholar comparten el mismo título
   normalizado ENTONCES EL Conector_Scholar DEBERÁ marcar el segundo registro
   con `is_duplicate = true` y `duplicate_of` apuntando al primero, sin eliminar
   ningún registro.
2. THE estrategia de deduplicación entre fuentes distintas SHALL permanecer
   `PENDING_VALIDATION`.

### Requisito 5 — Salida consolidada y reproducible del conector

**Historia:** Como equipo, quiero un dataset de Google Scholar en formatos
usables y generado con un único comando, para revisarlo y reprocesarlo sin pasos
manuales.

#### Criterios de aceptación

1. CUANDO EL Pipeline_Scholar termine de procesar ENTONCES EL Pipeline_Scholar
   DEBERÁ escribir el Dataset_Procesado en `data/processed/google_scholar/` en
   formato JSON y en formato CSV.
2. CUANDO EL Pipeline_Scholar termine ENTONCES EL Pipeline_Scholar DEBERÁ
   mostrar un resumen con el número de registros procesados y la completitud por
   campo.
3. THE Pipeline_Scholar SHALL poder ejecutarse mediante un único comando de
   línea de comandos sin interfaz gráfica.

### Requisito 6 — Resumen bibliométrico consolidado (todas las fuentes)

**Historia:** Como coordinador de SAO, quiero un análisis bibliométrico que consolide todas las fuentes en un solo conjunto, para ver el panorama completo sin fragmentarlo por fuente.

#### Criterios de aceptación

1. CUANDO existan uno o más Dataset_Procesado de fuente en `data/processed/` ENTONCES EL Servicio_Consolidado DEBERÁ calcular las agregaciones sobre el conjunto combinado formado por la unión de los registros de todos los Dataset_Procesado de fuente disponibles, sin excluir ninguno.
2. THE Servicio_Consolidado SHALL incluir en el resumen consolidado los siguientes valores calculados sobre el conjunto combinado: total de artículos como conteo entero mayor o igual a 0; distribución por año como conteo de artículos por cada año presente en los datos; distribución por volumen como conteo de artículos por cada valor de volumen presente; completitud de metadata como porcentaje entre 0 y 100 de registros con los campos requeridos presentes; número de artículos pendientes de revisión como conteo entero mayor o igual a 0; y número de posibles duplicados como conteo entero mayor o igual a 0.
3. WHERE exista al menos un Dataset_Procesado con clasificación por OFC disponible, THE Servicio_Consolidado SHALL incluir la distribución por OFC como conteo de artículos por cada uno de los 11 OFC sobre el conjunto combinado, e indicar de forma explícita en el resultado que la clasificación por OFC es automática y está sujeta a revisión humana.
4. THE Servicio_Consolidado SHALL incluir en el resultado un identificador explícito que lo marque como resumen consolidado de múltiples fuentes y no como resumen específico de una única fuente.
5. IF no existe ningún Dataset_Procesado de fuente en `data/processed/` ENTONCES EL Servicio_Consolidado DEBERÁ devolver un resultado con total de artículos igual a 0, todas las distribuciones vacías, completitud de metadata igual a 0 y los conteos de pendientes y posibles duplicados iguales a 0, sin inventar datos ni registros.
6. THE estrategia de deduplicación de artículos que aparecen en más de una fuente SHALL permanecer `PENDING_VALIDATION`; mientras permanezca en ese estado, EL Servicio_Consolidado SHALL aplicar únicamente la deduplicación básica ya realizada dentro de cada Dataset_Procesado y SHALL NO eliminar ni combinar registros duplicados entre fuentes distintas.
7. WHERE `data/processed/` contenga subcarpetas de datasets clasificados además de los Dataset_Procesado de fuente, THE Servicio_Consolidado SHALL tratar los datasets clasificados únicamente como origen de la distribución por OFC del criterio 3 y SHALL NO contarlos como fuentes adicionales al calcular el total de artículos del conjunto combinado, evitando el doble conteo de un mismo artículo.

### Requisito 7 — Aporte por fuente (información complementaria)

**Historia:** Como coordinador de SAO, quiero ver cuánto aporta cada fuente al
total, para entender la composición del conjunto sin partir el análisis.

#### Criterios de aceptación

1. THE Servicio_Consolidado SHALL incluir un Aporte_Por_Fuente que, por cada
   fuente con Dataset_Procesado, reporte el número de artículos que aporta al
   total.
2. THE Servicio_Consolidado SHALL incluir en el Aporte_Por_Fuente la completitud
   de metadata correspondiente a cada fuente.
3. THE Aporte_Por_Fuente SHALL presentarse como información complementaria del
   resumen consolidado y no como análisis separado por fuente.

### Requisito 8 — Endpoint consolidado y transición del endpoint actual

**Historia:** Como desarrollador del frontend, quiero un endpoint que exponga el
resumen consolidado, para que la vista consuma el análisis de todas las fuentes.

#### Criterios de aceptación

1. CUANDO EL frontend solicite el resumen consolidado ENTONCES EL
   Endpoint_Consolidado DEBERÁ responder con el resumen consolidado definido en
   los Requisitos 6 y 7.
2. THE Endpoint_Consolidado SHALL exponerse en una ruta que refleje su carácter
   consolidado y no específico de la fuente Boletín SAO.
3. IF no existe ningún Dataset_Procesado ENTONCES EL Endpoint_Consolidado DEBERÁ
   responder de forma que el frontend pueda mostrar un estado vacío honesto.
4. THE ruta actual `GET /bibliometria/boletin-sao/resumen` SHALL mantenerse
   operativa durante la transición para no romper consumidores existentes.

> `PENDING_VALIDATION`: si la ruta actual `boletin-sao/resumen` debe eliminarse
> tras la migración del frontend o conservarse como filtro por fuente, queda por
> validar con el equipo.

### Requisito 9 — Vista generalizada en el frontend

**Historia:** Como usuario de SAO, quiero que la vista de Bibliometría muestre el
análisis consolidado de todas las fuentes, para no navegar por pestañas por
fuente.

#### Criterios de aceptación

1. CUANDO EL Endpoint_Consolidado devuelva un resumen consolidado ENTONCES LA
   Vista_Bibliometria DEBERÁ mostrar total de artículos, distribución por año,
   distribución por volumen, completitud de metadata y, cuando exista,
   distribución por OFC, calculados sobre el conjunto consolidado.
2. THE Vista_Bibliometria SHALL presentar un título que indique que el análisis
   abarca todas las fuentes y no una fuente individual.
3. THE Vista_Bibliometria SHALL mostrar una sección de Aporte_Por_Fuente como
   información complementaria.
4. IF el resumen consolidado no contiene ningún artículo ENTONCES LA
   Vista_Bibliometria DEBERÁ mostrar un estado vacío honesto sin inventar datos.
5. WHERE la distribución por OFC esté disponible, THE Vista_Bibliometria SHALL
   indicar que la clasificación es automática y está sujeta a revisión humana.

### Requisito 10 — Base para múltiples fuentes

**Historia:** Como equipo, quiero que incorporar una tercera fuente en el futuro
no requiera rediseñar el servicio ni la vista, para escalar el análisis con solo
añadir conectores.

#### Criterios de aceptación

1. CUANDO una nueva fuente escriba su Dataset_Procesado conforme al Article Data
   Contract V1 en `data/processed/{fuente}/` ENTONCES EL Servicio_Consolidado
   DEBERÁ incorporar esa fuente al resumen consolidado sin cambios de código en
   el servicio ni en la Vista_Bibliometria.
2. THE lógica específica de extracción de Google Scholar SHALL permanecer
   aislada en el módulo del Conector_Scholar.

### Requisito 11 — Guía de exportación desde Publish or Perish

**Historia:** Como usuario de SAO, quiero una guía paso a paso para exportar los
datos de Google Scholar con Publish or Perish, para generar el Export_PoP real de
forma reproducible.

#### Criterios de aceptación

1. THE Sistema_Bibliometria SHALL incluir un documento de guía en `docs/` que
   describa los pasos para generar el Export_PoP.
2. THE guía SHALL indicar la consulta del tema de conservación de aves, el
   Período_Inclusión 2020–2030, el formato JSON recomendado y la ubicación de
   destino `data/raw/google_scholar/`.
3. THE guía SHALL indicar que el formato JSON es el recomendado por conservar
   mejor la metadata e incluir el resumen abreviado disponible en Google
   Scholar.

## Fuera de alcance (explícito)

- Clasificación por OFC automática (metodología `PENDING_VALIDATION`).
- Deduplicación definitiva entre fuentes distintas (`PENDING_VALIDATION`).
- Scraping o automatización de la descarga desde Google Scholar (obtención
  manual vía Publish or Perish).
- Métricas bibliométricas avanzadas no presentes en la vista actual.
- Uso de datos sintéticos o `DEMO_DATA`: el pipeline procesa el Export_PoP real
  cuando exista.

## Notas de PENDING_VALIDATION

- Deduplicación entre fuentes (cross-source): `PENDING_VALIDATION`.
- Metodología y algoritmo de clasificación por OFC: `PENDING_VALIDATION`.
- Destino final de la ruta `boletin-sao/resumen` tras la migración del frontend:
  `PENDING_VALIDATION`.
- Métricas bibliométricas definitivas: `PENDING_VALIDATION`.
