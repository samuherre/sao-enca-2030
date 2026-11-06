# Requirements — Clasificación de artículos por OFC (Componente B)

## Introducción

Este spec cubre la **clasificación multilabel de artículos por Objeto Focal de
Conservación (OFC)**. Es la etapa transversal del Componente B que se aplica al
dataset producido por cualquier fuente (hoy: Boletín SAO) conforme al Article
Data Contract V1.

**Metodología decidida (V1): reglas por palabras clave (lexicón por OFC).**
La decisión fue tomada por el equipo SAO-EAFIT ante la ausencia de una
metodología impuesta por SAO, priorizando trazabilidad, reproducibilidad,
ejecución local y la inexistencia de un dataset etiquetado para entrenamiento.
La justificación completa está en `design.md` y en un ADR.

Contexto en `.kiro/steering/bibliometrics.md`. Catálogo de OFC en
`bibliometrics/classification/ofc_catalog.json`.

## Requisitos

### Requisito 1 — Catálogo de OFC como fuente de verdad

**Historia:** Como equipo, quiero un catálogo editable de los 11 OFC, para que
la clasificación se base en definiciones y términos verificados sin tocar código.

#### Criterios de aceptación

1. EL sistema DEBERÁ leer los 11 OFC desde `ofc_catalog.json` (id, nombre,
   definición, hábitats, aves características, términos clave).
2. CUANDO se edite el catálogo (añadir/ajustar términos) ENTONCES la
   clasificación DEBERÁ reflejar el cambio sin modificar código.
3. EL sistema NO DEBERÁ crear OFC nuevos ni modificar las definiciones oficiales.

### Requisito 2 — Clasificación multilabel por reglas

**Historia:** Como analista, quiero que cada artículo se clasifique en cero, uno
o varios OFC según coincidencias de términos, para reflejar que un artículo
puede pertenecer a varios OFC.

#### Criterios de aceptación

1. CUANDO se clasifique un artículo ENTONCES el sistema DEBERÁ buscar los
   términos clave de cada OFC en el texto relevante (título, abstract,
   keywords) y asignar los OFC con al menos una coincidencia.
2. EL resultado DEBERÁ ser multilabel: `ofcs` es una lista que puede tener 0, 1
   o varios OFC.
3. CUANDO ningún OFC coincida ENTONCES `ofcs` DEBERÁ quedar vacío y el estado de
   clasificación DEBERÁ ser `NO_CLASIFICADO` (no se inventa un OFC).
4. LA comparación DEBERÁ ser insensible a mayúsculas y a acentos.

### Requisito 3 — Trazabilidad y confianza

**Historia:** Como SAO, quiero saber por qué un artículo quedó en un OFC, para
poder revisar y confiar en el resultado.

#### Criterios de aceptación

1. CUANDO se asigne un OFC ENTONCES el sistema DEBERÁ registrar los términos que
   coincidieron (evidencia) para ese OFC.
2. EL sistema DEBERÁ fijar `classification_method = "reglas-keywords-v1"`.
3. EL sistema DEBERÁ calcular un `classification_confidence` simple y explicable
   (p. ej. basado en el número de coincidencias), documentando su significado.

### Requisito 4 — Revisión humana

**Historia:** Como SAO, quiero revisar los casos dudosos, para corregir la
clasificación automática.

#### Criterios de aceptación

1. CUANDO la confianza sea baja o el resultado sea `NO_CLASIFICADO` ENTONCES el
   artículo DEBERÁ permanecer en `inclusion_status = PENDIENTE_REVISIÓN`.
2. LA clasificación automática NO DEBERÁ presentarse como definitiva; debe poder
   distinguirse de una validación humana.

### Requisito 5 — Integración con el pipeline

**Historia:** Como equipo, quiero clasificar el dataset existente, para ver la
distribución por OFC en el dashboard.

#### Criterios de aceptación

1. EL sistema DEBERÁ ofrecer una etapa que tome el dataset procesado de una
   fuente y produzca un dataset clasificado (JSON + CSV) sin modificar el
   dataset de entrada.
2. EL dataset clasificado DEBERÁ conservar todos los campos del contrato V1 y
   rellenar `ofcs`, `classification_method`, `classification_confidence`.
3. EL proceso DEBERÁ ser reproducible con un único comando.

### Requisito 6 — Visualización por OFC

**Historia:** Como SAO, quiero ver la distribución de artículos por OFC en el
dashboard.

#### Criterios de aceptación

1. CUANDO exista un dataset clasificado ENTONCES el backend DEBERÁ exponer la
   distribución por OFC y el dashboard DEBERÁ mostrarla.
2. LA visualización DEBERÁ dejar claro que la clasificación es automática y
   sujeta a revisión.

## Fuera de alcance (V1)

* Entrenamiento de modelos ML supervisados (no hay dataset etiquetado).
* Embeddings / similitud semántica (posible evolución futura sobre las reglas).
* Clasificación mediante LLM.
