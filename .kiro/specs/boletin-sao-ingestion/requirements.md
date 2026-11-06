# Requirements — Ingesta de la fuente Boletín SAO (Componente B)

## Introducción

Este spec cubre la **ingesta y extracción de metadata de artículos del Boletín
SAO** hacia el Article Data Contract V1. Es el primer conector del Componente B
(bibliometría) y sienta la base de arquitectura para las demás fuentes
(Scopus/Elsevier, UNAL, Wiley, Google Scholar).

Alcance de este spec: **solo la fuente Boletín SAO**. NO incluye clasificación
por OFC, análisis bibliométrico ni dashboard (quedan fuera / `PENDING_VALIDATION`).

Contexto y decisiones estables en `.kiro/steering/bibliometrics.md`.

## Requisitos

### Requisito 1 — Ingesta de PDFs del Boletín SAO

**Historia:** Como equipo del proyecto, quiero procesar los PDFs del Boletín SAO
(2020–2030) almacenados localmente, para obtener un dataset estructurado de
artículos sin captura manual.

#### Criterios de aceptación

1. CUANDO haya PDFs del Boletín SAO en `data/raw/boletin_sao/` ENTONCES el
   sistema DEBERÁ procesarlos en lote sin modificar los archivos originales.
2. CUANDO un PDF corresponda a una separata ENTONCES el sistema DEBERÁ tratarlo
   como **un** artículo (1 PDF = 1 artículo).
3. SI la carpeta de entrada no contiene PDFs ENTONCES el sistema DEBERÁ
   informarlo claramente sin fallar.
4. SI un PDF individual no puede abrirse o procesarse ENTONCES el sistema DEBERÁ
   registrar el error y continuar con los demás.

### Requisito 2 — Extracción conforme al Article Data Contract V1

**Historia:** Como analista, quiero que cada artículo se represente según el
contrato V1, para garantizar consistencia entre fuentes.

#### Criterios de aceptación

1. CUANDO se procese un artículo ENTONCES el sistema DEBERÁ extraer, cuando
   estén presentes: `title`, `authors`, `publication_year`, `volume`, `pages`,
   `abstract`, `keywords`, y fijar `source = "Boletín SAO"`.
2. CUANDO un campo no pueda detectarse ENTONCES el sistema DEBERÁ dejarlo en
   `null` y NUNCA inventar un valor.
3. CUANDO el texto extraído tenga tildes/ñ separadas ENTONCES el sistema DEBERÁ
   normalizarlas.
4. CUANDO falte un campo obligatorio del contrato o la detección sea ambigua
   ENTONCES el sistema DEBERÁ fijar `inclusion_status = PENDIENTE_REVISIÓN` con
   una nota explicativa.

### Requisito 3 — Validación de periodo

**Historia:** Como analista, quiero que se valide el periodo 2020–2030, para
mantener el alcance acordado.

#### Criterios de aceptación

1. CUANDO `publication_year` esté fuera de 2020–2030 ENTONCES el sistema DEBERÁ
   marcar el registro como `PENDIENTE_REVISIÓN` con nota, sin descartarlo
   silenciosamente.

### Requisito 4 — Deduplicación básica

**Historia:** Como analista, quiero detectar duplicados evidentes, para no
contar dos veces el mismo artículo.

#### Criterios de aceptación

1. CUANDO dos registros tengan el mismo título normalizado ENTONCES el sistema
   DEBERÁ marcar el segundo con `is_duplicate = true` y `duplicate_of`
   apuntando al primero, SIN eliminar ningún registro.
2. LA estrategia definitiva de deduplicación permanece `PENDING_VALIDATION`.

### Requisito 5 — Salida consolidada y reproducible

**Historia:** Como equipo, quiero un dataset consolidado en formatos usables,
para revisarlo y presentarlo.

#### Criterios de aceptación

1. CUANDO termine el procesamiento ENTONCES el sistema DEBERÁ escribir el
   dataset en `data/processed/boletin_sao/` en formato JSON y CSV.
2. CUANDO termine ENTONCES el sistema DEBERÁ mostrar un resumen con el número de
   PDFs procesados y la tasa de completitud por campo.
3. EL proceso DEBERÁ ser reproducible ejecutando un único comando.

### Requisito 6 — Base para múltiples fuentes

**Historia:** Como equipo, quiero que este conector respete un contrato de
salida común, para incorporar luego Scopus, UNAL, Wiley y Scholar sin rediseñar.

#### Criterios de aceptación

1. CUANDO se añada una nueva fuente en el futuro ENTONCES DEBERÁ producir
   registros conforme al mismo Article Data Contract V1.
2. LA lógica específica de Boletín SAO DEBERÁ permanecer aislada en su propio
   módulo de extracción.

## Fuera de alcance (explícito)

* Clasificación por OFC (metodología `PENDING_VALIDATION`).
* Análisis bibliométrico y dashboard.
* Descarga automática desde sao.org.co (el sitio bloquea con HTTP 403; la
  descarga es asistida en V1).
* Evaluación de relevancia temática automática.
