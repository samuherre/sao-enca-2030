---
inclusion: fileMatch
fileMatchPattern: 'bibliometrics/**'
---

# Steering — Componente B: Bibliometría (SAO ENCA 2030)

> Este documento rige el trabajo sobre el **Componente B — Análisis
> Bibliométrico**. Complementa a `product.md`, `tech.md`, `structure.md` y
> `data-and-domain.md`. No los contradice. Ante conflicto, aplica la jerarquía
> de `tech.md §37`.

## 1. Qué es el Componente B

Procesa publicaciones científicas relacionadas con la conservación de aves para
apoyar el análisis bibliométrico de SAO. Está **integrado en el mismo proyecto
SAO** (mismo repositorio); no es un proyecto independiente. La separación con el
Componente A es **interna por carpetas y módulos** (`bibliometrics/`, `backend/`,
`frontend/`), no por repos ni aplicaciones distintas.

## 2. Decisiones confirmadas (tratar como estables)

* **Fuentes y su rol** (matriz validada en reunión con Julián):
  | Fuente | Rol | Método inicial | Prioridad |
  |--------|-----|----------------|-----------|
  | Scopus / Elsevier | Fuente principal de literatura científica | API | Alta |
  | Repositorio UNAL | Producción académica colombiana | OAI-PMH | Alta |
  | **Boletín SAO** | Fuente especializada en aves colombianas | Extracción controlada | Alta |
  | Wiley | Complementaria | TDM API (si hay acceso) | Media |
  | Google Scholar | Descubrimiento / validación | Manual / exportación limitada | Media |
* **Relación Artículo ↔ OFC: muchos a muchos (multilabel).** Confirmado por
  Julián: un artículo puede pertenecer a uno o varios de los 11 OFC.
* **Periodo de inclusión: 2020–2030** (propuesto por SAO). Se procesa lo que
  exista hoy (hasta 2026).
* **Alcance geográfico: SOLO Colombia** (decisión validada por Julián, ver
  historial abajo). La ingesta debe restringirse a artículos relacionados con
  Colombia; los que no cumplan quedan fuera. Razón dada por SAO: es preferible
  un corpus pequeño y confiable a uno grande "plagado de inconsistencias" que
  mine la credibilidad del observatorio.
  * **Historial de esta decisión:** inicialmente se validó en reunión que el
    dataset NO se limitaba a Colombia (se priorizaban estudios colombianos pero
    se incluían internacionales relevantes). Julián REVIRTIÓ esa decisión al
    revisar el corpus real (aparecían artículos de aves de Nepal, Brasil, etc.,
    sin relación con Colombia) y pidió exigir relación con Colombia.
  * **Advertencia técnica (medida sobre el corpus real):** filtrar por mención
    textual de "Colombia" dejaría ~1.774 de 23.503 artículos (se pierde ~92%) y
    es impreciso: excluiría estudios colombianos que en el texto solo dicen
    "Andes"/"Neotropical" o nombran un departamento sin el país. El criterio de
    inclusión geográfica concreto (qué cuenta como "de Colombia") queda
    `PENDING_VALIDATION`: debe afinarse con SAO para no perder material válido.
* **Article Data Contract V1** (`docs/bibliometrics/article-data-contract.md`)
  es el contrato de datos. Toda fuente debe producir registros conforme a él.
* **Criterios de inclusión/exclusión V1**
  (`docs/bibliometrics/inclusion-exclusion-criteria.md`) son nuestra propuesta.

### 2.1 Autoridad sobre campos y criterios (acuerdo con el equipo)

SAO ha dejado abierto el diseño de campos y criterios. Por eficiencia, **el
equipo define la propuesta V1** (contrato y criterios) según el mejor análisis
técnico, y la presenta a SAO como **propuesta a validar**, no como verdad de
SAO. Esto NO viola el principio de no invención: se documenta explícitamente
como propuesta nuestra y queda sujeta a validación.

## 3. Hallazgos de la fuente Boletín SAO (evidencia real)

* **1 PDF = 1 artículo** (separatas individuales). Confirmado con 35 PDFs reales.
  Cada artículo tiene un código SAO del tipo `BSAAAA-NN`.
* La **primera página** trae encabezado muy regular: cita (`Boletín SAO Vol. N -
  AÑO`), tema + `Pag: X-Y`, título ES (mayúsculas), título EN, autores,
  `Resumen`, `Palabras clave`/`Key words`, `Abstract`.
* **Licencia: Creative Commons CC BY 4.0**; ISSN 0123-9082. Permite usar y
  procesar citando autoría.
* **El sitio sao.org.co bloquea descargas automáticas simples (HTTP 403).** La
  descarga de PDFs se hace de forma **asistida** (manual o pidiendo a SAO), no
  con scraper básico. Un navegador headless (Playwright) sería la alternativa si
  se requiere automatizar, pero NO es prioridad.
* **Limitaciones conocidas de extracción** (documentadas, no bloqueantes):
  tildes/ñ sueltas (resueltas por el normalizador), espacios pegados en algunos
  párrafos, acentos ausentes en títulos en mayúscula, y ~5% de PDFs con formato
  atípico que caen en `PENDIENTE_REVISIÓN`.

## 4. Reglas de trabajo para el Componente B

1. **No inventar.** Campo no detectado → `null`. Si falta un obligatorio o la
   detección es ambigua → `inclusion_status = PENDIENTE_REVISIÓN` con nota.
2. **No clasificar OFC todavía.** La metodología de clasificación sigue
   `PENDING_VALIDATION`. No implementar clasificador ni asumir algoritmo.
3. **`data/raw/` es inmutable.** Las transformaciones generan artefactos nuevos
   en `interim/` o `processed/`. Nunca modificar los PDFs originales.
4. **Arquitectura de conectores.** Cada fuente tiene su extractor específico,
   pero todas producen el mismo Article Data Contract V1 y confluyen en un
   dataset maestro. Al añadir una fuente, respetar ese contrato de salida.
5. **El pipeline corre sin UI** (scripts), de forma reproducible. El frontend
   solo consulta resultados ya procesados (structure.md §30).
6. **Dependencias pinned** en `bibliometrics/requirements.txt` (tech.md §21).

## 5. Estado del pipeline (fuente Boletín SAO)

Implementado y probado con 35 PDFs reales:

```
data/raw/boletin_sao/*.pdf
  → ingestion/extract_boletin.py   (PDF → Article Data Contract V1)
  → preprocessing/text_normalizer.py (tildes, ñ, espacios)
  → pipelines/process_boletin_sao.py (lote → JSON + CSV + dedupe básica)
  → data/processed/boletin_sao/
```

## 6. Pendiente de validación (`PENDING_VALIDATION`)

* Métricas bibliométricas definitivas.
* Acceso a Scopus (API key), Wiley (TDM) y mecanismo OAI-PMH de UNAL.
* Si se automatiza la descarga de PDFs de SAO (navegador headless) o se mantiene
  asistida.

### 6.1 Decisiones ya resueltas (antes `PENDING_VALIDATION`)

* **Clasificación OFC — CERRADA:** se mantiene el clasificador actual
  (reglas por palabras clave, multilabel). Julián confirmó no afinarlo: la idea
  es reflejar solo lo que encaja en los 11 OFC priorizados; lo que no cumpla
  queda fuera (es aceptable que muchos artículos queden "sin OFC").
* **Deduplicación entre fuentes — RESUELTA (Julián):** la clave primaria de
  identidad entre fuentes es el **DOI** (mismo DOI = mismo artículo, se cuenta
  una vez). Plan B para el ~8% de artículos SIN DOI: título normalizado + año
  (no se descartan por carecer de DOI; se evita tanto el doble conteo como la
  pérdida). Se implementa al incorporar las fuentes nuevas.

## 7. Re-ingesta OpenAlex + nuevas gráficas (aprobado por Julián)

Julián dio visto bueno a una re-ingesta ÚNICA de OpenAlex (~23.000 works, filtro
solo-Colombia) que amplía el Article Data Contract y alimenta nuevas vistas. Se
hace de una sola vez para no descargar dos veces. Campos/gráficas aprobados:

* **Instituciones** que más publican (gráfica/tabla). Ponderación por rol de
  autor: `PENDING_VALIDATION` (ver abajo, hay dos reglas en conflicto).
* **Tipo de documento** (artículo, review, capítulo, resumen de congreso, libro,
  tesis, "letter"≈nota corta) → gráfica de barras.
* **Open Access** (abierto vs. cerrado) con filtro OA/privado en la vista.
* **Keywords** más comunes.
* **Financiación** (funders): el campo existe pero viene casi vacío en el
  dominio de aves/conservación; se mostrará SOLO si hay datos suficientes (si
  no, no se muestra para no engañar).
* **Tipo de colaboración por año**: (1) una sola institución, (2) colaboración
  nacional (varias instituciones colombianas), (3) internacional (instituciones
  de >1 país). Usa institución+país de cada autor (mismo dato que instituciones).
  Artículos sin afiliación completa → "sin dato" (no se infiere).
* **Citas, país/institución por autor** disponibles para traer en la misma pasada.
* **Abstracts: NO se descargan** (acuerdo con Julián): no alimentan gráficas y
  pesan; se reconsideraría solo si se hace búsqueda por texto.

### 7.1 Decisiones que BLOQUEAN arrancar la re-ingesta

1. **Ponderación de instituciones — CONFLICTO sin resolver.** Julián dio dos
   reglas incompatibles en mensajes distintos: (a) primer autor = 2 puntos,
   coautor = 1; y (b) contar solo 1 autor/institución/artículo (presencia
   simple). Debe elegir UNA. No decidir por el equipo (tech.md §37.4).
2. **Criterio "de Colombia" concreto.** Filtrar por mención textual de
   "Colombia" pierde ~92% del corpus y es impreciso (deja fuera estudios
   colombianos que dicen "Andes"/"Neotropical" o solo el departamento). Hay que
   afinar qué cuenta como "de Colombia" (p. ej. país de afiliación + menciones).
3. **Departamentos (geografía).** Piloto hecho: buscar departamentos en
   título+abstract rinde <5% útil y con falsos positivos (p. ej. "Meta" =
   meta-análisis). El tiempo NO es el problema (~37 s para todo). Decisión de
   SAO sobre si vale la pena con esa cobertura. Correspondencia
   departamento→región ENCA debe darla SAO.

### 7.2 Fuentes nuevas propuestas por Julián (evaluación del equipo)

Priorizar por aporte real (varias solapan con lo que OpenAlex ya agrega):

* **SciELO (ArticleMeta) y Redalyc — ALTA prioridad.** Literatura
  latinoamericana en español, justo lo que OpenAlex cubre peor y lo más
  relevante para Colombia.
* **OpenAIRE, DOAJ — prioridad media.** Complementan (DOAJ = solo OA).
* **Crossref, Semantic Scholar — bajo aporte marginal.** OpenAlex ya se nutre
  de ellas; añadirlas duplica en gran parte el mismo material.
* **DataCite — baja pertinencia.** Es sobre todo datasets, no artículos.
* Editoriales de pago (Scopus/ScienceDirect/Web of Science): sin credenciales
  institucionales no hay acceso; en pausa hasta que una universidad las provea.
