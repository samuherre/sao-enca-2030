# Contrato de Datos Bibliográficos — Componente B (SAO ENCA 2030)

## 1. Propósito

Este documento define el **contrato de datos** para cada publicación/artículo
procesado por el Componente B — Análisis Bibliométrico del proyecto SAO.

El contrato establece qué campos describen un artículo, cuáles son obligatorios
y cuáles opcionales, para garantizar consistencia en la ingesta, el
procesamiento y el análisis posterior.

Este contrato forma parte del mismo proyecto SAO. El Componente B está integrado
en la aplicación SAO y **no** es un proyecto independiente.

> Estado: **Propuesta V1** del Equipo_Proyecto, sujeta a validación por SAO.
>
> Estos campos representan nuestra propuesta inicial y pueden evolucionar cuando
> se obtenga el dataset real y se validen los resultados con SAO. Ver la sección
> "Propuesta V1 y evolución futura", que incorpora los campos opcionales
> propuestos y el registro único por publicación.
>
> La presente revisión documental **no** modifica el esquema de código
> `ArticleRecord`: los campos nuevos propuestos son candidatos a futuro y quedan
> registrados en `pending-validation.md` hasta que SAO los confirme.

---

## 2. Alcance y contexto

* Periodo de publicaciones considerado: **2020–2030**.
* Fuentes identificadas inicialmente por SAO:
  * Google Scholar
  * Elsevier
  * Wiley-Blackwell
  * Repositorios de la Universidad Nacional
  * Boletín SAO
* La relación **Artículo ↔ OFC** es de **muchos a muchos** (un artículo puede
  pertenecer a uno o varios de los 11 Objetos Focales de Conservación).
* El conjunto de datos **no** se limita exclusivamente a publicaciones sobre
  Colombia. Se priorizan los estudios relacionados con Colombia, pero pueden
  incluirse estudios internacionales cuando sean relevantes para la conservación
  de aves.

> Este contrato describe únicamente la **estructura lógica de datos**. No define
> todavía tablas de base de datos, endpoints, scraping ni el clasificador. Esos
> elementos quedan `PENDING_VALIDATION` / fuera del alcance de V1.

---

## 3. Convenciones

* **Obligatorio**: el campo debe estar presente y tener un valor para que el
  registro pueda procesarse normalmente. La ausencia de un campo obligatorio
  debe tratarse como un problema de calidad de datos y, cuando aplique, llevar el
  registro a `PENDIENTE_REVISIÓN`.
* **Opcional**: el campo puede estar ausente o vacío. Su ausencia **no** es, por
  sí sola, motivo de exclusión.
* Nunca inventar valores para completar campos faltantes. Preferir estados
  explícitos como "Sin información" / "No disponible".

---

## 4. Campos del contrato (V1)

### 4.1. Identificación

| Campo         | Obligatoriedad | Descripción |
|---------------|----------------|-------------|
| `article_id`  | **Obligatorio** | Identificador interno único y **determinista** del registro dentro del sistema SAO. |
| `title`       | **Obligatorio** | Título de la publicación. |
| `doi`         | Opcional       | Digital Object Identifier, si está disponible. |
| `url`         | Opcional       | URL de acceso o referencia del documento. |

> **`article_id` determinista (registro único por publicación).** El
> `article_id` se deriva de forma reproducible de la publicación: con DOI, de un
> hash del DOI normalizado; sin DOI, de un hash del título normalizado y el año.
> Cada fuente usa un prefijo propio (p. ej. `oa-` para OpenAlex, `gs-` para
> Google Scholar). Como consecuencia, **la misma publicación produce el mismo
> `article_id`** aunque se recupere por distintas vías o consultas de una misma
> fuente, lo que hace posible el **registro único por publicación** descrito en
> la sección 7. Este comportamiento ya existe en el código y **no** se modifica
> en esta revisión.

### 4.2. Información bibliográfica

| Campo              | Obligatoriedad | Descripción |
|--------------------|----------------|-------------|
| `authors`          | **Obligatorio** | Autor(es) de la publicación. |
| `publication_year` | **Obligatorio** | Año de publicación. Debe estar dentro del periodo 2020–2030 para ser candidato a inclusión. |
| `journal`          | Opcional       | Revista o medio de publicación. |
| `volume`           | Opcional       | Volumen. |
| `issue`            | Opcional       | Número/entrega. |
| `pages`            | Opcional       | Páginas. |
| `publisher`        | Opcional       | Editorial o entidad editora. |
| `language`         | Opcional       | Idioma de la publicación. |

### 4.3. Contenido

| Campo       | Obligatoriedad | Descripción |
|-------------|----------------|-------------|
| `abstract`  | Opcional       | Resumen de la publicación. |
| `keywords`  | Opcional       | Palabras clave. |

### 4.4. Procedencia

| Campo               | Obligatoriedad | Descripción |
|---------------------|----------------|-------------|
| `source`            | **Obligatorio** | Fuente de origen del registro (p. ej. Google Scholar, Elsevier, Wiley-Blackwell, Repositorios UNAL, Boletín SAO). |
| `source_url`        | Opcional       | URL específica dentro de la fuente. |
| `extraction_date`   | **Obligatorio** | Fecha en que se obtuvo/registró el dato. |
| `extraction_method` | Opcional       | Método o proceso mediante el cual se obtuvo el registro. |

### 4.5. Procesamiento

| Campo               | Obligatoriedad | Descripción |
|---------------------|----------------|-------------|
| `processing_status` | **Obligatorio** | Estado del procesamiento del registro dentro del pipeline. |
| `is_duplicate`      | **Obligatorio** | Indica si el registro fue identificado como duplicado. |
| `duplicate_of`      | Opcional       | Referencia (`article_id`) al registro del que es duplicado, cuando aplique. |
| `notes`             | Opcional       | Notas internas sobre el procesamiento del registro. |

### 4.6. Inclusión / Exclusión

| Campo               | Obligatoriedad | Descripción |
|---------------------|----------------|-------------|
| `inclusion_status`  | **Obligatorio** | Estado de inclusión: `INCLUIDO`, `EXCLUIDO` o `PENDIENTE_REVISIÓN`. Ver `inclusion-exclusion-criteria.md`. |
| `exclusion_reason`  | Opcional       | Motivo de exclusión cuando `inclusion_status = EXCLUIDO`. |

### 4.7. Clasificación

| Campo                       | Obligatoriedad (V1) | Descripción |
|-----------------------------|---------------------|-------------|
| `ofcs`                      | Opcional (inicial)  | Lista de Objetos Focales de Conservación asociados. Multilabel: un artículo puede tener uno o varios OFC. |
| `classification_method`     | Opcional (inicial)  | Método con el que se produjo la clasificación. |
| `classification_confidence` | Opcional (inicial)  | Nivel de confianza de la clasificación. |

> Los campos de clasificación son **opcionales en V1** porque el clasificador y
> su metodología todavía **no** están definidos. No implementar aún el
> clasificador ni asumir un algoritmo concreto.

---

## 5. Resumen de obligatoriedad

**Campos obligatorios (V1):**

* `article_id`
* `title`
* `authors`
* `publication_year`
* `source`
* `extraction_date`
* `processing_status`
* `is_duplicate`
* `inclusion_status`

**Campos opcionales (V1):**

* `doi`, `url`
* `journal`, `volume`, `issue`, `pages`, `publisher`, `language`
* `abstract`, `keywords`
* `source_url`, `extraction_method`
* `duplicate_of`, `notes`
* `exclusion_reason`
* `ofcs`, `classification_method`, `classification_confidence`

> **Importante:** no convertir los campos opcionales en obligatorios y no agregar
> campos adicionales al contrato V1 sin indicarlo expresamente como propuesta
> futura.

---

## 6. Relación Artículo ↔ OFC

* Existen **11 Objetos Focales de Conservación (OFC)**.
* Un mismo artículo puede pertenecer a **uno o varios** OFC.
* Por lo tanto, la relación es **muchos a muchos (N:N)**.
* La clasificación por OFC será **multilabel**.
* La metodología y el algoritmo de clasificación quedan `PENDING_VALIDATION` y
  no se implementan en V1.

---

## 7. Propuesta V1, evolución futura

Este contrato es nuestra **propuesta inicial (V1)** del Equipo_Proyecto y podrá
modificarse cuando:

* Se obtenga el dataset real de artículos y se conozcan los campos realmente
  disponibles.
* SAO valide o ajuste los campos, su obligatoriedad y su significado.
* Se defina la metodología de clasificación por OFC (lo que podría volver
  obligatorios los campos de la sección 4.7).
* Se definan reglas de deduplicación concretas a partir de los metadatos reales.

### 7.1. Confirmación de la cobertura actual (V1)

La revisión confirma que el contrato V1 **ya permite registrar** toda la
información mínima requerida por el Componente B, sin añadir campos nuevos:

| Información | Campo(s) en V1 | Sección |
|-------------|----------------|---------|
| Identificador | `article_id` | 4.1 |
| Título | `title` | 4.1 |
| Autores | `authors` | 4.2 |
| Año | `publication_year` | 4.2 |
| DOI | `doi` | 4.1 |
| Resumen | `abstract` | 4.3 |
| Palabras clave | `keywords` | 4.3 |
| Fuente | `source` | 4.4 |
| Fecha de extracción | `extraction_date` | 4.4 |
| Estado de procesamiento | `processing_status` | 4.5 |
| Estado de inclusión | `inclusion_status` | 4.6 |
| Motivo de exclusión | `exclusion_reason` | 4.6 |
| Clasificación por OFC | `ofcs` | 4.7 |

No es necesario modificar el esquema de código `ArticleRecord` para cubrir estos
elementos.

### 7.2. Campos opcionales propuestos (propuesta V1, evolución futura)

Los siguientes campos se proponen como **opcionales** para una evolución futura
del contrato. **No** forman parte del contrato V1 vigente, **no** son
obligatorios y **no** se implementan en el código en este momento. Siguen la
regla de no invención: si el valor no puede determinarse a partir de los
metadatos, el campo queda ausente / `None`, nunca se inventa.

| Campo (propuesto) | Obligatoriedad | Descripción |
|-------------------|----------------|-------------|
| `geographic_scope` | Opcional (propuesta V1) | `Clasificacion_Geografica` del registro: `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS` o `SIN_DETERMINAR`. Ver `geographic-classification.md`. |
| `studied_territory` | Opcional (propuesta V1) | `Territorio_Estudiado`: área geográfica objeto del estudio. `None` si no es determinable a partir de los metadatos (no inventar). |
| `source_query` / `retrieved_by_query` | Opcional (propuesta V1) | Consulta (ecuación / `Familia_Ecuaciones`) que recuperó el registro. Apoya la trazabilidad hasta la búsqueda de origen. |
| `document_type` | Opcional (propuesta V1) | Tipo de documento del registro (p. ej. artículo, documento técnico), cuando la fuente lo provea. |

> Estos campos y su obligatoriedad quedan registrados como `PENDING_VALIDATION`
> en `pending-validation.md` a la espera de confirmación por SAO. La relación
> entre `geographic_scope` / `studied_territory` y la metodología de
> clasificación geográfica se define en `geographic-classification.md`, donde
> tampoco se implementa un clasificador en este spec.

### 7.3. Registro único por publicación

Una misma publicación puede aparecer en **varias consultas** (distintas
`Familia_Ecuaciones`) o en **varias fuentes**. El contrato establece que, en ese
caso, debe existir **un único registro bibliográfico** por publicación y no un
registro duplicado por cada aparición:

* La identificación de "misma publicación" se apoya en el `article_id`
  **determinista** ya descrito en la sección 4.1: la misma publicación produce el
  mismo `article_id`, de modo que las apariciones repetidas de una fuente
  convergen naturalmente en el mismo registro.
* Las apariciones que sí generan registros separados (p. ej. duplicados
  detectados entre fuentes o variantes de metadatos) se gestionan con los campos
  de procesamiento ya existentes: `is_duplicate` marca el duplicado y
  `duplicate_of` referencia el `article_id` del registro canónico (sección 4.5).
  Así se conserva la trazabilidad sin perder la relación entre registros.

**Entidades/relaciones adicionales.** Para la trazabilidad del "registro único
por publicación" **no** se requieren nuevas entidades ni cambios de arquitectura:
los campos actuales (`article_id`, `is_duplicate`, `duplicate_of`, `source`) ya
son suficientes. La única relación conceptual que podría necesitar modelado
futuro es **publicación ↔ consulta de origen** (una publicación puede haber sido
recuperada por varias consultas o fuentes), que hoy se representa de forma
simplificada con el campo opcional `source_query` / `retrieved_by_query`
propuesto en la sección 7.2. Su formalización como entidad/relación aparte queda
como **propuesta V1** sujeta a validación por SAO (`pending-validation.md`), y
solo se implementaría si la trazabilidad real lo exige, evitando sobreingeniería.

### 7.4. Otras líneas de evolución

Posibles líneas de evolución adicionales (propuestas futuras, **no** parte del
contrato V1):

* Campos adicionales de metadatos (p. ej. instituciones, país, citaciones).
* Campos de trazabilidad del pipeline (versión de pipeline, configuración).
* Formalización de los campos de clasificación como obligatorios.

Cualquier cambio relevante en este contrato debe documentarse y, cuando afecte
la arquitectura, registrarse mediante un ADR en `docs/decisions/`.
