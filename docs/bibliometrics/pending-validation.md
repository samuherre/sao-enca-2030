# Decisiones PENDING_VALIDATION — Componente B (SAO ENCA 2030)

## 1. Objetivo de este documento

Este documento consolida, en un único lugar, las **decisiones de la estrategia
bibliométrica del Componente B que todavía deben ser confirmadas por SAO** antes
de convertirse en reglas rígidas del sistema.

Todo lo que aquí aparece es **propuesta V1 del Equipo_Proyecto**: una base de
trabajo razonada a partir de la información disponible, no un criterio oficial de
SAO. Mientras una decisión figure en este listado como `PENDING_VALIDATION`:

* **No** debe tratarse como una regla de negocio obligatoria.
* **No** debe implementarse como comportamiento automático irreversible.
* **No** debe usarse para inventar datos, relevancia ni relaciones no
  confirmadas.

Este documento acompaña al resto de la documentación bibliométrica:

* Estrategia de Búsqueda (`search-strategy.md`).
* Criterios de inclusión/exclusión (`inclusion-exclusion-criteria.md`).
* Clasificación Geográfica (`geographic-classification.md`).
* Contrato de Datos (`article-data-contract.md`).
* Especificación de integración por API key (`api-key-integration.md`).
* Límites de recuperación y Resumen de Ejecución (`retrieval-limits.md`).
* Plan de Piloto Controlado (`pilot-plan.md`).

> Estado global: **Propuesta V1** del Equipo_Proyecto, **sujeta a validación por
> SAO**. Cuando SAO confirme o modifique una decisión, debe retirarse de este
> listado, documentarse el acuerdo y, si afecta la arquitectura, registrarse
> mediante un ADR en `docs/decisions/`.

---

## 2. Cómo usar este listado

Cada decisión incluye:

* **Qué está pendiente**: la decisión concreta que requiere confirmación.
* **Propuesta V1**: lo que el Equipo_Proyecto propone como punto de partida.
* **Por qué está pendiente**: la razón por la que no puede fijarse sin SAO.
* **Documento relacionado**: dónde está descrita en detalle.

El identificador entre paréntesis (p. ej. 11.1) corresponde al criterio de
aceptación del Requisito 11 del spec `estrategia-bibliometrica-api`.

---

## 3. Listado de decisiones pendientes

### 3.1 Familias de ecuaciones de búsqueda (11.1)

* **Qué está pendiente**: la confirmación de las cinco familias de ecuaciones de
  búsqueda, sus sinónimos y sus términos.
* **Propuesta V1**: aves + conservación; aves + conservación + Colombia; aves +
  amenazas o pérdida de hábitat; aves + biodiversidad, áreas protegidas o
  restauración; y aves + especies amenazadas o monitoreo de poblaciones, cada
  una con sinónimos y operador `OR`.
* **Por qué está pendiente**: las ecuaciones son una propuesta del
  Equipo_Proyecto, no un criterio oficial de SAO; los términos y sinónimos deben
  revisarse con el conocimiento de dominio de SAO y ajustarse tras observar los
  resultados reales por fuente.
* **Documento relacionado**: `search-strategy.md`.

### 3.2 Definición de relevancia temática (11.2)

* **Qué está pendiente**: la definición precisa de qué hace que un registro sea
  **relevante** para la conservación de aves (umbral temático).
* **Propuesta V1**: se consideran relevantes los registros de aves + conservación
  que aborden amenazas, protección, manejo, restauración o monitoreo; los casos
  dudosos se marcan `PENDIENTE_REVISIÓN` en lugar de excluirse automáticamente.
* **Por qué está pendiente**: la frontera entre "relevante" y "mención
  incidental" depende del criterio de dominio de SAO; fijarla automáticamente
  arriesgaría excluir material válido o incluir ruido. No se automatiza la
  decisión de relevancia.
* **Documento relacionado**: `inclusion-exclusion-criteria.md` (y la distinción
  Corpus_Recuperado vs. Corpus_Analitico en `search-strategy.md`).

### 3.3 Categorías y metodología de la Clasificación Geográfica (11.3)

* **Qué está pendiente**: la confirmación de las categorías `COLOMBIA`,
  `INTERNACIONAL`, `MULTIPAIS` y `SIN_DETERMINAR`, y la metodología para
  determinar el Territorio_Estudiado a partir de los metadatos.
* **Propuesta V1**: cuatro categorías basadas en el Territorio_Estudiado (no solo
  en la afiliación institucional), con `SIN_DETERMINAR` por defecto cuando el
  territorio no es determinable, sin inventar territorio.
* **Por qué está pendiente**: deben validarse las definiciones, la convención
  para estudios `MULTIPAIS` que incluyen a Colombia y el peso de la afiliación
  como señal secundaria; además, en este spec **no** se implementa un
  clasificador geográfico, solo se define la metodología.
* **Documento relacionado**: `geographic-classification.md`.

### 3.4 Campos añadidos al Contrato de Datos (11.4)

* **Qué está pendiente**: la confirmación de los campos **opcionales** propuestos
  para el Contrato de Datos, incluidos:
  * `document_type` — tipo de documento del registro;
  * `source_query` / `retrieved_by_query` — consulta que recuperó el registro;
  * `studied_territory` — Territorio_Estudiado;
  * `geographic_scope` — alcance geográfico (Clasificación Geográfica).
* **Propuesta V1**: añadir estos campos como **opcionales** en la sección de
  evolución futura del contrato, sin cambiar el esquema de código `ArticleRecord`
  en este spec ni volverlos obligatorios.
* **Por qué está pendiente**: incorporar campos nuevos al contrato es una
  decisión de modelo de datos que debe confirmarse con SAO antes de volverse
  obligatoria o de modificar el esquema persistido.
* **Documento relacionado**: `article-data-contract.md`.

### 3.5 Metodología y algoritmo de clasificación por OFC (11.5)

* **Qué está pendiente**: la metodología y el algoritmo para clasificar los
  registros según los 11 Objetos Focales de Conservación (OFC), incluida la
  naturaleza del clasificador (reglas, machine learning, modelos de lenguaje o
  enfoque híbrido) y su evaluación.
* **Propuesta V1**: ninguna. El spec documenta la **compatibilidad** con la
  clasificación OFC existente pero **no** implementa ni fija un clasificador; la
  relación Artículo ↔ OFC es muchos a muchos (multilabel), y la relevancia/OFC no
  se resuelven automáticamente.
* **Por qué está pendiente**: la metodología de clasificación por OFC depende de
  los criterios de dominio de SAO, del dataset real y de validaciones que aún no
  se han realizado; no debe asumirse una metodología no confirmada.
* **Documento relacionado**: `pilot-plan.md` (compatibilidad con OFC sin
  implementar el clasificador).

### 3.6 Incorporación de Scopus, Wiley y UNAL OAI-PMH (11.6)

* **Qué está pendiente**: la decisión de incorporar los proveedores **Scopus**,
  **Wiley** y **UNAL OAI-PMH** como fuentes del Componente B.
* **Propuesta V1**: marcarlos como `PENDING_VALIDATION` y **no** implementarlos
  en este spec; el único `Proveedor_API` instanciado e implementado es OpenAlex.
* **Por qué está pendiente**: cada proveedor tiene autenticación, cuotas, costos,
  condiciones de uso y restricciones de almacenamiento propias que deben
  verificarse con SAO antes de integrarlo; no se atribuyen capacidades no
  confirmadas (p. ej. texto completo frente a solo metadatos).
* **Documento relacionado**: `api-key-integration.md`.

### 3.7 Estrategia de deduplicación entre fuentes (11.7)

* **Qué está pendiente**: la estrategia de deduplicación cuando los registros
  provengan de **varias fuentes** (p. ej. qué identificadores y qué combinaciones
  de metadatos se usan para decidir que dos registros son la misma publicación).
* **Propuesta V1**: mantener el principio de **registro único por publicación**
  (una publicación que aparece en varias consultas o fuentes se identifica como
  un único registro), alineado con el `article_id` determinista existente; la
  regla concreta de deduplicación entre fuentes queda pendiente.
* **Por qué está pendiente**: la deduplicación entre fuentes depende de los
  identificadores realmente disponibles (DOI, títulos, autores, año, fuente) y de
  la calidad de los metadatos, que solo pueden evaluarse con los datasets reales;
  no se fija una regla de deduplicación antes de analizar los datos.
* **Documento relacionado**: `article-data-contract.md` (registro único por
  publicación) y `retrieval-limits.md` (conteo de nuevos vs. duplicados en el
  Resumen_Ejecucion).

### 3.8 Valor definitivo del Límite de Recuperación y estrategia incremental (11.8)

* **Qué está pendiente**: el valor **definitivo** del `Limite_Recuperacion` por
  corrida y la estrategia de **recuperación incremental** entre corridas.
* **Propuesta V1**: `Limite_Recuperacion` predeterminado de **5.000** resultados
  por `Corrida_Ingesta`, configurable; documentado como **valor recomendado del
  flag `--max-results`** sin cambiar el default del código (hoy `None`). Cambiar
  el default efectivo del pipeline a 5.000 queda pendiente de confirmación de
  SAO.
* **Estrategia incremental — ADOPTADA como propuesta V1 (a validar con SAO)**:
  el resumen consolidado del dashboard es **ACUMULATIVO**: combina todos los
  datasets históricos de cada fuente y deduplica por `article_id` dentro de la
  fuente (ver `multi-source-bibliometria`, tarea 13). Así el corpus crece con
  cada corrida anual sin perder lo anterior. Queda pendiente: (a) la dedup ENTRE
  fuentes distintas (ver 11.7) y (b) si a gran volumen conviene un corpus maestro
  persistente en lugar de acumular en memoria al vuelo.
* **Por qué está pendiente**: el valor adecuado depende de las cuotas y costos
  reales de cada fuente y del volumen objetivo del Corpus_Analitico; el
  `Limite_Recuperacion` es un **control operativo por corrida**, no el límite del
  Corpus_Analitico, y la estrategia incremental debe acordarse con SAO.
* **Documento relacionado**: `retrieval-limits.md`.

---

## 4. Resumen

| # | Decisión pendiente | Documento relacionado |
|---|--------------------|-----------------------|
| 11.1 | Familias de ecuaciones de búsqueda | `search-strategy.md` |
| 11.2 | Definición de relevancia temática | `inclusion-exclusion-criteria.md` |
| 11.3 | Categorías y metodología de la Clasificación Geográfica | `geographic-classification.md` |
| 11.4 | Campos añadidos al Contrato de Datos (tipo de documento, consulta de origen, territorio estudiado, alcance geográfico) | `article-data-contract.md` |
| 11.5 | Metodología y algoritmo de clasificación por OFC | `pilot-plan.md` |
| 11.6 | Incorporación de Scopus, Wiley y UNAL OAI-PMH | `api-key-integration.md` |
| 11.7 | Estrategia de deduplicación entre fuentes | `article-data-contract.md`, `retrieval-limits.md` |
| 11.8 | Valor definitivo del `Limite_Recuperacion` y estrategia incremental | `retrieval-limits.md` |

Cuando SAO confirme una decisión, debe retirarse de este listado, documentarse el
acuerdo y, si afecta la arquitectura, registrarse mediante un ADR en
`docs/decisions/`. No deben eliminarse decisiones sin registrar el cambio.
