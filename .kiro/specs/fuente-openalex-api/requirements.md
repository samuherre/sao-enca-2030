# Requirements Document

Fuente OpenAlex por API (consulta directa, Componente B)

## Introduction

El spec `fuente-openalex` incorporó OpenAlex como fuente de alto volumen, pero
mediante **exportación manual** con Publish or Perish (PoP): el usuario consulta
OpenAlex en PoP, exporta archivos JSON/CSV a mano y los coloca en
`data/raw/openalex/`. Esto funciona, pero conserva un paso manual y no es del
todo reproducible (depende de que la persona repita la misma consulta).

Este spec reemplaza ese paso manual por un **conector que consulta directamente
la API pública y gratuita de OpenAlex** (https://api.openalex.org), sin API key
obligatoria. El equipo ejecuta un **único comando de línea de comandos** que
consulta la API, pagina los resultados, los transforma al **Article Data
Contract V1** y escribe el `Dataset_Procesado`. La obtención deja de depender de
PoP.

El spec **reutiliza la infraestructura existente** del Componente B sin
rediseñarla: el patrón de **conectores por fuente** (cada fuente produce
registros conforme al Article Data Contract V1,
`docs/bibliometrics/article-data-contract.md`), el **Servicio_Consolidado** que
descubre cualquier carpeta bajo `data/processed/` y agrupa por el campo
`source`, y la **Vista_Bibliometria** consolidada. Por el Requisito 10 del spec
`multi-source-bibliometria`, el backend y el frontend incorporan una fuente
nueva **sin cambios de código** una vez existe su `Dataset_Procesado`.

Decisión de interfaz (acordada con el usuario): la obtención es un **script de
pipeline por línea de comandos**, NO un botón de consulta en vivo en el
frontend. Razones: (a) el volumen bibliométrico (miles de artículos paginados)
no cabe de forma sana en una petición HTTP del front; (b) mantiene la regla del
proyecto de que la UI solo consulta resultados ya procesados
(`structure.md` §30); (c) de cara a la migración a **ArcGIS Online**, el activo
que migra es el dataset reproducible generado por el script, no la UI.

Principio rector no negociable (`product.md` §15, §22; `data-and-domain.md` §37;
`tech.md` §2.1): **no inventar ni falsear datos**. Lo que la API no entregue
queda en `null`; los registros se etiquetan como OpenAlex, nunca como otra
fuente. Decisiones estables y contexto en `.kiro/steering/bibliometrics.md`.

## Glossary

- **Sistema_Bibliometria**: conjunto del Componente B que ingiere, procesa y
  expone información bibliométrica dentro del proyecto SAO.
- **API_OpenAlex**: API pública y gratuita de OpenAlex (https://api.openalex.org),
  sin API key obligatoria, que devuelve trabajos académicos (`works`) paginados.
- **Conector_OpenAlex_API**: módulo de extracción que consulta la API_OpenAlex y
  transforma cada `work` en un registro del Article Data Contract V1.
- **Pipeline_OpenAlex_API**: proceso reproducible por línea de comandos que
  ejecuta el Conector_OpenAlex_API para una o varias consultas y escribe el
  Dataset_Procesado.
- **Consulta**: conjunto de parámetros de búsqueda (términos, filtros de año,
  etc.) enviado a la API_OpenAlex.
- **Servicio_Consolidado**: componente del backend (ya existente) que lee los
  datasets procesados de todas las fuentes y calcula las agregaciones.
- **Vista_Bibliometria**: página del frontend (ya existente) que presenta el
  resumen consolidado.
- **Article Data Contract V1**: contrato de datos común a todas las fuentes
  (`docs/bibliometrics/article-data-contract.md`).
- **Dataset_Procesado**: salida de un conector en `data/processed/{fuente}/`,
  conforme al Article Data Contract V1, en formatos JSON y CSV.
- **Mailto_Cortesia**: dirección de correo opcional que OpenAlex recomienda
  enviar para acceder al "polite pool" (mejor servicio y límites), configurable
  por variable de entorno.
- **Período_Inclusión**: rango de años de publicación 2020–2030.
- **PENDIENTE_REVISIÓN**: valor de `inclusion_status` para registros con un
  campo obligatorio faltante, detección ambigua o año fuera del
  Período_Inclusión.
- **OFC**: Objeto Focal de Conservación (11 en total; relación con artículo es
  multilabel).

## Requirements

### Requisito 1 — Consulta a la API de OpenAlex

**Historia:** Como equipo del proyecto, quiero obtener trabajos de OpenAlex consultando directamente su API con un único comando, para incorporar alto volumen de forma reproducible sin exportación manual con Publish or Perish.

#### Criterios de aceptación

1. CUANDO se ejecute el Pipeline_OpenAlex_API con una o más Consultas ENTONCES EL Conector_OpenAlex_API DEBERÁ consultar el endpoint de trabajos de la API_OpenAlex y recuperar los resultados correspondientes.
2. THE Conector_OpenAlex_API SHALL funcionar sin API key, usando la API pública y gratuita de OpenAlex.
3. CUANDO una Consulta devuelva más resultados de los que caben en una sola respuesta ENTONCES EL Conector_OpenAlex_API DEBERÁ paginar hasta recuperar todos los resultados de esa Consulta o hasta alcanzar un límite máximo de resultados configurable.
4. WHERE exista una Mailto_Cortesia configurada por variable de entorno, THE Conector_OpenAlex_API SHALL incluirla en las solicitudes a la API_OpenAlex para usar el "polite pool"; WHERE no exista, THE Conector_OpenAlex_API SHALL continuar funcionando sin ella.
5. THE Conector_OpenAlex_API SHALL NO requerir ni almacenar secretos; la Mailto_Cortesia no es un secreto y nunca debe versionarse con un valor real.

### Requisito 2 — Manejo de límites y errores de la API

**Historia:** Como responsable de operación, quiero que el conector respete los límites de la API y tolere fallos de red, para no abusar del servicio ni abortar una corrida por un error transitorio.

#### Criterios de aceptación

1. THE Conector_OpenAlex_API SHALL respetar los límites de uso de la API_OpenAlex aplicando un ritmo de solicitudes acotado (p. ej. pausa entre páginas) configurable.
2. IF la API_OpenAlex responde con un error transitorio (p. ej. límite de tasa o error temporal del servidor) ENTONCES EL Conector_OpenAlex_API DEBERÁ reintentar con espera incremental hasta un número máximo de reintentos configurable.
3. IF se agotan los reintentos para una página ENTONCES EL Pipeline_OpenAlex_API DEBERÁ registrar el error indicando la Consulta y la página afectada, conservar los resultados ya recuperados y continuar con las Consultas restantes, finalizando sin dejar el dataset a medias de forma silenciosa.
4. IF no hay conectividad con la API_OpenAlex al iniciar ENTONCES EL Pipeline_OpenAlex_API DEBERÁ registrar un mensaje de error comprensible y finalizar sin escribir un Dataset_Procesado vacío que pueda confundirse con un resultado real.
5. THE Pipeline_OpenAlex_API SHALL registrar un resumen con el número de resultados recuperados, el número de páginas consultadas y el número de errores encontrados.

### Requisito 3 — Extracción conforme al Article Data Contract V1

**Historia:** Como analista, quiero que cada trabajo de OpenAlex se represente según el Article Data Contract V1, para garantizar consistencia entre fuentes.

#### Criterios de aceptación

1. CUANDO EL Conector_OpenAlex_API procese un `work` de la API ENTONCES EL Conector_OpenAlex_API DEBERÁ producir un registro conforme al Article Data Contract V1 con `source = "OpenAlex"`.
2. THE Conector_OpenAlex_API SHALL NO producir ningún registro con un valor de `source` distinto de `"OpenAlex"`; en particular, SHALL NO etiquetar los registros como Google Scholar ni ninguna otra fuente.
3. CUANDO un campo del contrato no esté presente en el `work` de la API ENTONCES EL Conector_OpenAlex_API DEBERÁ fijar ese campo en `null` sin generar un valor sustituto.
4. IF un campo obligatorio del Article Data Contract V1 está ausente o su detección es ambigua ENTONCES EL Conector_OpenAlex_API DEBERÁ fijar `inclusion_status = "PENDIENTE_REVISIÓN"` y registrar una nota explicativa en `notes`.
5. THE Article Data Contract V1 SHALL permanecer sin cambios de campos obligatorios u opcionales como consecuencia de este spec.
6. THE `article_id` generado por el Conector_OpenAlex_API SHALL ser determinista y reproducible entre corridas para el mismo `work`, y SHALL usar el mismo esquema de identificador de la fuente OpenAlex para contarse como la misma fuente en el consolidado.
7. WHERE la API entregue el resumen del trabajo en forma de índice invertido (`abstract_inverted_index`), THE Conector_OpenAlex_API SHALL reconstruir el texto del `abstract` a partir de ese índice; WHERE no lo entregue, THE Conector_OpenAlex_API SHALL dejar `abstract` en `null`.

### Requisito 4 — Criterios de inclusión y período

**Historia:** Como analista, quiero que la consulta y la extracción respeten los criterios de inclusión y el Período_Inclusión 2020–2030, para mantener el alcance acordado.

#### Criterios de aceptación

1. THE Pipeline_OpenAlex_API SHALL permitir acotar la Consulta al Período_Inclusión 2020–2030 mediante los filtros de año de la API_OpenAlex.
2. IF el `publication_year` de un registro está fuera del Período_Inclusión 2020–2030 ENTONCES EL Conector_OpenAlex_API DEBERÁ fijar `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota, sin descartar el registro.
3. IF un registro no tiene `publication_year` detectable ENTONCES EL Conector_OpenAlex_API DEBERÁ dejar el campo en `null` y fijar `inclusion_status = "PENDIENTE_REVISIÓN"` con una nota.
4. WHERE los términos de búsqueda de las Consultas se definan en configuración o documentación, THE Sistema_Bibliometria SHALL marcarlos explícitamente como propuesta del equipo a validar con SAO, sin presentarlos como criterio oficial de SAO.
5. THE evaluación automática de relevancia temática y la clasificación por OFC SHALL permanecer `PENDING_VALIDATION`; en V1 los registros entran como `PENDIENTE_REVISIÓN` para revisión posterior.

### Requisito 5 — Deduplicación básica dentro de la fuente

**Historia:** Como analista, quiero detectar duplicados evidentes dentro del dataset de OpenAlex, incluidos los que aparecen entre varias Consultas, para no contar dos veces el mismo trabajo.

#### Criterios de aceptación

1. WHEN dos registros del dataset de OpenAlex comparten el mismo título normalizado ENTONCES EL Conector_OpenAlex_API DEBERÁ marcar el segundo registro con `is_duplicate = true` y `duplicate_of` apuntando al primero, sin eliminar ningún registro.
2. CUANDO se ejecuten varias Consultas en una misma corrida ENTONCES EL Pipeline_OpenAlex_API DEBERÁ combinar sus resultados en un único Dataset_Procesado y aplicar la deduplicación básica sobre el conjunto combinado.
3. THE estrategia de deduplicación entre fuentes distintas SHALL permanecer `PENDING_VALIDATION`.

### Requisito 6 — Salida consolidada y reproducible del conector

**Historia:** Como equipo, quiero un dataset de OpenAlex en formatos usables y generado con un único comando, para revisarlo, reprocesarlo y migrarlo a ArcGIS Online sin pasos manuales.

#### Criterios de aceptación

1. CUANDO EL Pipeline_OpenAlex_API termine de procesar ENTONCES EL Pipeline_OpenAlex_API DEBERÁ escribir el Dataset_Procesado en `data/processed/openalex/` en formato JSON y en formato CSV.
2. CUANDO EL Pipeline_OpenAlex_API termine ENTONCES EL Pipeline_OpenAlex_API DEBERÁ mostrar un resumen con el número de registros procesados y la completitud por campo.
3. THE Pipeline_OpenAlex_API SHALL poder ejecutarse mediante un único comando de línea de comandos sin interfaz gráfica.
4. THE Pipeline_OpenAlex_API SHALL escribir únicamente en `data/processed/openalex/` y SHALL NO alterar archivos de `data/raw/`.

### Requisito 7 — Incorporación automática al análisis consolidado (sin rediseño)

**Historia:** Como coordinador de SAO, quiero que OpenAlex por API aparezca en el análisis consolidado existente sin modificar el servicio ni la vista, para aprovechar la base multi-fuente ya construida.

#### Criterios de aceptación

1. CUANDO EL Pipeline_OpenAlex_API haya escrito su Dataset_Procesado conforme al Article Data Contract V1 en `data/processed/openalex/` ENTONCES EL Servicio_Consolidado DEBERÁ incorporar OpenAlex al resumen consolidado (total, distribuciones, completitud, pendientes, posibles duplicados y aporte por fuente) sin cambios de código en el Servicio_Consolidado ni en la Vista_Bibliometria.
2. THE Vista_Bibliometria SHALL mostrar OpenAlex como una fuente dentro del Aporte_Por_Fuente, con su nombre de fuente real `"OpenAlex"`.
3. THE lógica específica de consulta a la API SHALL permanecer aislada en el módulo del Conector_OpenAlex_API, sin acoplarse a los conectores de otras fuentes ni modificar su comportamiento.
4. THE Dataset_Procesado de las demás fuentes existentes SHALL permanecer intacto y seguir contándose como su propia fuente en el consolidado.

### Requisito 8 — Trazabilidad y procedencia

**Historia:** Como responsable de calidad de datos, quiero que el origen y el momento de obtención de cada registro queden registrados, para preservar la trazabilidad exigida por el proyecto y las actualizaciones anuales.

#### Criterios de aceptación

1. THE Conector_OpenAlex_API SHALL registrar en cada registro la fecha de obtención (`extraction_date`) y un método de extracción (`extraction_method`) que identifique que el origen fue la consulta por API de OpenAlex.
2. WHERE un `work` conserve su identificador o URL propio de OpenAlex (p. ej. el `id` tipo `https://openalex.org/Wxxxx`), THE Conector_OpenAlex_API SHALL preservarlo en el campo de procedencia del contrato (`source_url`) cuando esté disponible, sin inventarlo cuando no lo esté.
3. THE Pipeline_OpenAlex_API SHALL NO sobrescribir de forma destructiva datasets históricos; la estrategia de versionado por fecha SHALL ser coherente con la de las demás fuentes del Componente B.

### Requisito 9 — Documentación de uso

**Historia:** Como usuario de SAO, quiero una guía de cómo ejecutar el conector por API, para poder actualizar los datos de OpenAlex de forma reproducible.

#### Criterios de aceptación

1. THE Sistema_Bibliometria SHALL incluir un documento de guía en `docs/` que describa cómo ejecutar el Pipeline_OpenAlex_API por línea de comandos, incluidos los parámetros de Consulta, el Período_Inclusión 2020–2030 y la ubicación de salida `data/processed/openalex/`.
2. THE guía SHALL documentar la variable de entorno de la Mailto_Cortesia y aclarar que es opcional y no es un secreto.
3. THE guía SHALL marcar los términos de búsqueda propuestos como propuesta del equipo a validar con SAO.
4. THE guía SHALL aclarar la relación con el spec `fuente-openalex` (exportación manual con Publish or Perish): ambas producen el mismo Dataset_Procesado de OpenAlex, y la vía por API reemplaza el paso manual.

## Fuera de alcance (explícito)

- Modificar el Servicio_Consolidado, el Endpoint_Consolidado o la
  Vista_Bibliometria: la base multi-fuente ya los cubre. Solo se verificará que
  OpenAlex por API aparece sin cambios de código.
- Un botón de "consulta en vivo" a OpenAlex en el frontend: se descarta por
  decisión de diseño (volumen + regla UI-solo-consulta + migración a ArcGIS).
- Clasificación por OFC automática (metodología `PENDING_VALIDATION`).
- Evaluación automática de relevancia temática (`PENDING_VALIDATION`).
- Deduplicación definitiva entre fuentes distintas (`PENDING_VALIDATION`).
- Uso de datos sintéticos o `DEMO_DATA` como datos reales.
- La exportación/publicación concreta hacia ArcGIS Online (se habilita al dejar
  el dataset reproducible, pero su publicación no es parte de este spec).

## Notas de PENDING_VALIDATION

- Mapeo exacto campo-a-campo del `work` de la API de OpenAlex al Article Data
  Contract V1: se definirá en la fase de **diseño**, inspeccionando la respuesta
  real de la API (no se inventa aquí).
- Términos de búsqueda de las Consultas: propuesta del equipo,
  `PENDING_VALIDATION` con SAO.
- Relevancia temática automática y clasificación por OFC: `PENDING_VALIDATION`.
- Deduplicación entre fuentes (cross-source): `PENDING_VALIDATION`.
