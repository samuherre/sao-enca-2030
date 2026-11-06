# Requirements Document

## Introduction

Este spec formaliza la **estrategia bibliométrica** del Componente B (Análisis
Bibliométrico) del proyecto SAO ENCA 2030 y especifica cómo integrar fuentes
mediante **API key**, instanciando el diseño en **OpenAlex** (el conector por
API ya existente).

El propósito de este spec es ante todo de **FORMALIZACIÓN, ANÁLISIS TÉCNICO y
ESPECIFICACIÓN** (documentación + un único cambio de código acotado). **NO** es
un spec de implementación de recolección masiva: en este spec **no** se ejecuta
una búsqueda masiva ni se consumen cuotas de las fuentes más allá de lo mínimo
necesario para un piloto controlado que aquí solo se **especifica** (no se
ejecuta a escala).

El trabajo se organiza en cuatro fases:

1. **Formalizar la estrategia bibliométrica** (documentación): alcance de
   búsqueda, familias de ecuaciones, criterios de inclusión/exclusión ampliados,
   clasificación geográfica y revisión del modelo de datos/trazabilidad.
2. **Especificar la integración por API key** (documentación + diseño genérico
   instanciado en OpenAlex).
3. **Especificar límites de recuperación** (control operativo por corrida,
   límite predeterminado de 5.000 resultados, configurable).
4. **Especificar un piloto controlado** (descrito, no ejecutado masivamente).

Los requisitos se separan explícitamente entre **DOCUMENTACIÓN/ESPECIFICACIÓN**
(la mayoría) y el **ÚNICO requisito de CAMBIO DE CÓDIGO** (soporte de
`OPENALEX_API_KEY` como parámetro `api_key` en el conector OpenAlex existente,
para habilitar la paginación por cursor más allá de la primera página).

Este spec hereda las reglas del steering del Componente B y del steering técnico:
no inventar datos ni relevancia; trazabilidad y reproducibilidad; `data/raw/`
inmutable; sin secretos en el repositorio ni en el chat; dependencias pinned;
el frontend solo consulta resultados ya procesados; y marcar como
`PENDING_VALIDATION` toda decisión que requiera confirmación de SAO.

> Estado: **Propuesta V1**. Las ecuaciones de búsqueda, los campos del contrato
> y los criterios de inclusión/exclusión son **propuesta del equipo del proyecto
> a validar con SAO**, no criterios oficiales de SAO.

## Glossary

- **Componente_B**: Módulo de Análisis Bibliométrico del proyecto SAO ENCA 2030,
  integrado en el mismo repositorio SAO (carpeta `bibliometrics/`).
- **Equipo_Proyecto**: Equipo del proyecto SAO (analistas bibliométricos y
  desarrolladores) que define, documenta y opera la estrategia bibliométrica.
- **Documentacion_Bibliometrica**: Conjunto de documentos del Componente B bajo
  `docs/bibliometrics/`, incluyendo la estrategia de búsqueda, el contrato de
  datos y los criterios de inclusión/exclusión.
- **Estrategia_Busqueda**: Documento que define alcance, cobertura, periodo,
  temática, idiomas y familias de ecuaciones de búsqueda del Componente B.
- **Corpus_Recuperado**: Conjunto de registros que una fuente devuelve para una
  búsqueda antes de aplicar deduplicación y criterios de inclusión/exclusión.
- **Corpus_Analitico**: Subconjunto definitivo de registros que, tras
  deduplicación y aplicación de criterios, forma parte del análisis
  bibliométrico.
- **Familia_Ecuaciones**: Grupo de ecuaciones de búsqueda relacionadas por una
  temática (p. ej. aves + conservación), con sinónimos y operadores OR.
- **Contrato_Datos**: Article Data Contract V1
  (`docs/bibliometrics/article-data-contract.md`) que define los campos de cada
  registro bibliográfico.
- **Criterios_Inclusion_Exclusion**: Reglas de selección de registros
  (`docs/bibliometrics/inclusion-exclusion-criteria.md`).
- **Clasificacion_Geografica**: Clasificación de cada registro según el
  territorio estudiado, con categorías `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS`
  y `SIN_DETERMINAR`.
- **Territorio_Estudiado**: Área geográfica objeto del estudio descrito por la
  publicación, que puede diferir de la afiliación institucional de los autores.
- **OFC**: Objeto Focal de Conservación. Existen 11 OFC. La relación
  Artículo ↔ OFC es muchos a muchos (multilabel).
- **Especificacion_API_Key**: Documento que describe, de forma genérica y luego
  instanciada en OpenAlex, cómo integrar una fuente que requiere API key.
- **Proveedor_API**: Servicio externo de datos bibliográficos accesible por API.
- **OpenAlex**: Proveedor_API instanciado en este spec
  (`https://api.openalex.org`).
- **Conector_OpenAlex**: Código existente del conector OpenAlex por API
  (`bibliometrics/ingestion/openalex_api_client.py` y
  `bibliometrics/pipelines/process_openalex_api.py`).
- **OPENALEX_API_KEY**: Variable de entorno que contiene la API key gratuita de
  OpenAlex. Se trata como secreto: solo por variable de entorno.
- **Parametro_api_key**: Parámetro de query `api_key` que OpenAlex requiere para
  continuar la paginación por cursor más allá de la primera página.
- **Paginacion_Cursor**: Mecanismo de paginación de OpenAlex basado en
  `next_cursor`, que sin API key devuelve HTTP 401 al pasar de la primera
  página.
- **Limite_Recuperacion**: Número máximo de resultados que una corrida de
  ingesta puede recuperar; valor predeterminado 5.000, configurable.
- **Corrida_Ingesta**: Una ejecución del pipeline de ingesta para una o varias
  ecuaciones de búsqueda.
- **Resumen_Ejecucion**: Registro por Corrida_Ingesta de resultados recuperados,
  nuevos, duplicados y errores, conservado para trazabilidad.
- **Piloto_Controlado**: Procedimiento acotado (especificado, no ejecutado a
  escala) que recupera un conjunto reducido de metadatos para validar el flujo.
- **Recoleccion_Masiva**: Recuperación a gran escala de todo el Corpus_Recuperado
  de una fuente. Explícitamente **fuera del alcance** de este spec.
- **Decision_Pendiente**: Decisión marcada como `PENDING_VALIDATION` que requiere
  confirmación de SAO o verificación externa antes de implementarse.

## Requirements

### Requirement 1: Formalizar el alcance de búsqueda de la estrategia bibliométrica

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero que el
alcance de búsqueda quede documentado de forma explícita, para que la estrategia
sea reproducible y revisable por SAO sin ambigüedad.

#### Acceptance Criteria

1. THE Estrategia_Busqueda SHALL documentar el periodo de inclusión como los
   años 2020 a 2030 inclusive.
2. THE Estrategia_Busqueda SHALL documentar una cobertura internacional con
   prioridad en Colombia, sin limitar el alcance exclusivamente a Colombia.
3. THE Estrategia_Busqueda SHALL documentar el foco temático en conservación de
   aves, incluyendo amenazas, protección, monitoreo, restauración y gestión de
   especies y de hábitats.
4. THE Estrategia_Busqueda SHALL documentar los idiomas español, inglés y
   portugués como idiomas objetivo cuando la fuente permita filtrar por idioma.
5. THE Estrategia_Busqueda SHALL diferenciar de forma explícita entre
   Corpus_Recuperado y Corpus_Analitico.
6. THE Estrategia_Busqueda SHALL registrarse como propuesta V1 del
   Equipo_Proyecto sujeta a validación por SAO.

### Requirement 2: Documentar las familias de ecuaciones de búsqueda

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero familias
de ecuaciones de búsqueda documentadas con sinónimos y operadores, para que las
búsquedas sean consistentes y adaptables a cada fuente.

#### Acceptance Criteria

1. THE Estrategia_Busqueda SHALL documentar las siguientes Familia_Ecuaciones:
   aves + conservación; aves + conservación + Colombia; aves + amenazas o
   pérdida de hábitat; aves + biodiversidad, áreas protegidas o restauración; y
   aves + especies amenazadas o monitoreo de poblaciones.
2. THE Estrategia_Busqueda SHALL documentar el uso de sinónimos y del operador
   OR dentro de cada Familia_Ecuaciones.
3. THE Estrategia_Busqueda SHALL documentar que una ecuación no exige que todos
   los términos aparezcan simultáneamente en un registro.
4. THE Estrategia_Busqueda SHALL documentar que la sintaxis de cada ecuación se
   adapta a cada fuente, sin asumir operadores o campos idénticos entre fuentes.
5. THE Estrategia_Busqueda SHALL registrar las ecuaciones como propuesta del
   Equipo_Proyecto, no como criterio oficial de SAO.

### Requirement 3: Ampliar los criterios de inclusión y exclusión

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero los
criterios de inclusión y exclusión formalizados y ampliados, para que la
selección de registros sea trazable y los casos dudosos queden para revisión
humana.

#### Acceptance Criteria

1. THE Criterios_Inclusion_Exclusion SHALL documentar como incluibles los
   registros relacionados con aves y conservación que aborden amenazas,
   protección, manejo, restauración o monitoreo.
2. THE Criterios_Inclusion_Exclusion SHALL documentar que los registros
   internacionales relevantes son elegibles para inclusión.
3. THE Criterios_Inclusion_Exclusion SHALL documentar que los documentos
   científicos y técnicos son elegibles para inclusión.
4. THE Criterios_Inclusion_Exclusion SHALL documentar como excluibles los
   duplicados, los registros sin información suficiente y las menciones
   incidentales de aves sin relación con conservación.
5. IF un registro es dudoso respecto a su relevancia, THEN THE
   Criterios_Inclusion_Exclusion SHALL asignarle el estado `PENDIENTE_REVISIÓN`
   en lugar de excluirlo automáticamente.
6. THE Criterios_Inclusion_Exclusion SHALL distinguir de forma explícita entre
   Corpus_Recuperado y Corpus_Analitico.

### Requirement 4: Formalizar la clasificación geográfica

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero una
clasificación geográfica basada en el territorio estudiado, para distinguir los
estudios de Colombia de los internacionales de forma consistente.

#### Acceptance Criteria

1. THE Documentacion_Bibliometrica SHALL definir la Clasificacion_Geografica con
   las categorías `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS` y `SIN_DETERMINAR`.
2. THE Clasificacion_Geografica SHALL basarse en el Territorio_Estudiado y no
   únicamente en la afiliación institucional de los autores.
3. WHERE el Territorio_Estudiado no puede determinarse a partir de los
   metadatos disponibles, THE Clasificacion_Geografica SHALL asignar la
   categoría `SIN_DETERMINAR` sin inventar un territorio.
4. THE Documentacion_Bibliometrica SHALL registrar la Clasificacion_Geografica
   como propuesta V1 del Equipo_Proyecto sujeta a validación por SAO.

### Requirement 5: Revisar el contrato de datos y la trazabilidad

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero revisar
el Contrato_Datos para confirmar que registra toda la trazabilidad necesaria,
para que cada registro sea rastreable hasta su consulta y fuente de origen.

#### Acceptance Criteria

1. THE Equipo_Proyecto SHALL revisar el Contrato_Datos para verificar que
   permite registrar identificador, título, autores, año, DOI, resumen, palabras
   clave, fuente, fecha de extracción, estado de procesamiento, estado de
   inclusión, motivo de exclusión y clasificación por OFC.
2. THE Contrato_Datos SHALL documentar un campo que registre el
   Territorio_Estudiado y la Clasificacion_Geografica del registro.
3. THE Contrato_Datos SHALL documentar un campo que registre la consulta que
   recuperó el registro.
4. THE Contrato_Datos SHALL documentar un campo que registre el tipo de
   documento del registro.
5. THE Contrato_Datos SHALL documentar que una publicación que aparece en varias
   consultas o fuentes se identifica como un único registro bibliográfico.
6. WHERE una entidad o relación adicional sea necesaria para la trazabilidad,
   THE Contrato_Datos SHALL proponerla sin introducir cambios innecesarios en la
   arquitectura existente.
7. THE Contrato_Datos SHALL registrar las adiciones de campos como propuesta V1
   del Equipo_Proyecto sujeta a validación por SAO.

### Requirement 6: Especificar la integración de fuentes mediante API key

**User Story:** Como desarrollador del Equipo_Proyecto, quiero una
especificación de integración por API key genérica e instanciada en OpenAlex,
para que la incorporación de fuentes autenticadas sea clara y segura.

#### Acceptance Criteria

1. THE Especificacion_API_Key SHALL documentar, para el Proveedor_API, el
   servicio, la autenticación requerida, las variables de entorno, los
   endpoints, los parámetros de búsqueda, los filtros por año, idioma y tipo de
   documento cuando existan, la paginación, los límites de solicitudes y de
   resultados, las cuotas y posibles costos, el manejo de errores, reintentos y
   límites de velocidad, los campos bibliográficos devueltos, y las condiciones
   de uso y restricciones de almacenamiento.
2. THE Especificacion_API_Key SHALL instanciar la especificación en OpenAlex
   como único Proveedor_API implementado en este spec.
3. THE Especificacion_API_Key SHALL documentar que la API key se provee
   únicamente mediante la variable de entorno `OPENALEX_API_KEY`.
4. THE Especificacion_API_Key SHALL documentar que la API key no se almacena en
   código, documentación pública, frontend ni repositorio.
5. THE Especificacion_API_Key SHALL marcar como `PENDING_VALIDATION` los
   proveedores Scopus, Wiley y UNAL OAI-PMH, sin implementarlos en este spec.
6. THE Especificacion_API_Key SHALL documentar que una API basada en metadatos
   no implica acceso al texto completo, sin asumir capacidades no confirmadas de
   la fuente.

### Requirement 7: Añadir soporte de API key al conector OpenAlex (ÚNICO CAMBIO DE CÓDIGO)

**User Story:** Como desarrollador del Equipo_Proyecto, quiero que el
Conector_OpenAlex admita la API key por variable de entorno, para habilitar la
Paginacion_Cursor más allá de la primera página sin exponer secretos.

> Este es el **único requisito de cambio de código** del spec. Todos los demás
> requisitos son de documentación/especificación. No se modifica ninguna otra
> lógica existente del Conector_OpenAlex.

#### Acceptance Criteria

1. WHERE la variable de entorno `OPENALEX_API_KEY` está definida con un valor no
   vacío, THE Conector_OpenAlex SHALL incluir el Parametro_api_key en los
   parámetros de query de cada solicitud a OpenAlex.
2. WHERE la variable de entorno `OPENALEX_API_KEY` no está definida o está vacía,
   THE Conector_OpenAlex SHALL continuar funcionando sin el Parametro_api_key.
3. THE Conector_OpenAlex SHALL leer el valor de `OPENALEX_API_KEY` únicamente del
   entorno del proceso, sin leerlo de un archivo versionado.
4. THE Conector_OpenAlex SHALL excluir el valor de `OPENALEX_API_KEY` de los
   mensajes de registro y de los mensajes de error.
5. WHERE la API key está presente, THE Conector_OpenAlex SHALL continuar la
   Paginacion_Cursor más allá de la primera página.
6. THE Conector_OpenAlex SHALL conservar sin cambios la lógica existente de
   transformación `work` a `ArticleRecord`, de ritmo, de reintentos y de la
   variable `OPENALEX_MAILTO`.
7. THE `.env.example` SHALL documentar `OPENALEX_API_KEY` como placeholder sin
   valor real.

### Requirement 8: Especificar los límites de recuperación por corrida

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero un
límite de recuperación por corrida configurable, para controlar el consumo de
cuotas y permitir recuperación incremental con trazabilidad.

#### Acceptance Criteria

1. THE Limite_Recuperacion SHALL tener un valor predeterminado de 5.000
   resultados por Corrida_Ingesta.
2. THE Limite_Recuperacion SHALL ser configurable por Corrida_Ingesta.
3. WHEN una Corrida_Ingesta alcanza el Limite_Recuperacion, THE Componente_B
   SHALL detener la recuperación de esa corrida sin exceder el límite.
4. THE Componente_B SHALL permitir varias Corrida_Ingesta incrementales.
5. WHEN una Corrida_Ingesta finaliza, THE Componente_B SHALL registrar un
   Resumen_Ejecucion con el número de resultados recuperados, nuevos, duplicados
   y errores.
6. THE Componente_B SHALL conservar la trazabilidad de cada Corrida_Ingesta.
7. THE Documentacion_Bibliometrica SHALL documentar que el Limite_Recuperacion
   es un control operativo por corrida y no el límite del Corpus_Analitico.

### Requirement 9: Especificar el piloto controlado (sin ejecución masiva)

**User Story:** Como analista bibliométrico del Equipo_Proyecto, quiero un
piloto controlado especificado en detalle, para validar el flujo completo sin
ejecutar una recolección masiva ni consumir cuotas innecesariamente.

#### Acceptance Criteria

1. THE Piloto_Controlado SHALL especificar el uso de una o dos fuentes
   accesibles y un conjunto reducido de ecuaciones de búsqueda.
2. THE Piloto_Controlado SHALL especificar la recuperación de metadatos, la
   deduplicación, la aplicación de los Criterios_Inclusion_Exclusion y la
   Clasificacion_Geografica.
3. THE Piloto_Controlado SHALL especificar su compatibilidad con la
   clasificación OFC existente, sin implementar el clasificador.
4. IF un registro del Piloto_Controlado es de relevancia incierta, THEN THE
   Piloto_Controlado SHALL asignarle el estado `PENDIENTE_REVISIÓN` sin marcarlo
   como incluido automáticamente.
5. THE Piloto_Controlado SHALL documentarse como procedimiento especificado y no
   como ejecución masiva realizada en este spec.

### Requirement 10: Restricciones de alcance del spec

**User Story:** Como miembro del Equipo_Proyecto, quiero que las restricciones de
alcance queden explícitas, para evitar ejecuciones masivas, exposición de
credenciales y cambios no justificados.

#### Acceptance Criteria

1. THE Componente_B SHALL abstenerse de ejecutar una Recoleccion_Masiva dentro
   del alcance de este spec.
2. THE Componente_B SHALL conservar sin cambios las funcionalidades existentes
   del módulo de bibliometría, incluido el procesamiento del Boletín SAO.
3. THE Equipo_Proyecto SHALL abstenerse de introducir tecnologías o dependencias
   nuevas sin justificación documentada.
4. THE Documentacion_Bibliometrica SHALL abstenerse de atribuir a una fuente
   capacidades no confirmadas, incluido el acceso a texto completo cuando la API
   solo entrega metadatos.
5. WHEN se requiere una búsqueda a mayor escala, THE Equipo_Proyecto SHALL
   verificar las cuotas, restricciones y costos de la fuente antes de ejecutarla.
6. THE Equipo_Proyecto SHALL excluir cualquier credencial del repositorio y de
   los mensajes del chat.

### Requirement 11: Decisiones PENDING_VALIDATION a confirmar con SAO

**User Story:** Como miembro del Equipo_Proyecto, quiero un listado explícito de
decisiones pendientes de validación, para que SAO pueda confirmarlas antes de
convertirlas en reglas rígidas del sistema.

#### Acceptance Criteria

1. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente las
   familias de ecuaciones de búsqueda propuestas por el Equipo_Proyecto.
2. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente la
   definición de relevancia temática para la conservación de aves.
3. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente las
   categorías y la metodología de la Clasificacion_Geografica.
4. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente los
   campos añadidos al Contrato_Datos, incluidos tipo de documento, consulta de
   origen, territorio estudiado y alcance geográfico.
5. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente la
   metodología y el algoritmo de clasificación por OFC.
6. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente la
   incorporación de los proveedores Scopus, Wiley y UNAL OAI-PMH.
7. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente la
   estrategia de deduplicación entre fuentes.
8. THE Documentacion_Bibliometrica SHALL registrar como Decision_Pendiente el
   valor definitivo del Limite_Recuperacion y la estrategia de recuperación
   incremental.
