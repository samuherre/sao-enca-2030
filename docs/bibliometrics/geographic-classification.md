# Clasificación Geográfica — Componente B (SAO ENCA 2030)

## 1. Objetivo de la clasificación

Este documento define la **Clasificación Geográfica** de los registros
bibliográficos del análisis bibliométrico del Componente B.

El propósito es:

* Distinguir de forma consistente los estudios cuyo territorio de estudio es
  **Colombia** de los que son **internacionales**.
* Permitir filtros y agregaciones por alcance geográfico en el análisis
  bibliométrico, de acuerdo con la cobertura definida en la Estrategia de
  Búsqueda (internacional con prioridad en Colombia).
* Garantizar trazabilidad y **no invención**: un registro cuyo territorio no
  pueda determinarse a partir de los metadatos no recibe un territorio
  inventado.

Esta clasificación se aplica junto con el contrato de datos
(`article-data-contract.md`), los criterios de inclusión/exclusión
(`inclusion-exclusion-criteria.md`) y la estrategia de búsqueda
(`search-strategy.md`).

> Estado: **Propuesta V1** del Equipo_Proyecto, **sujeta a validación por SAO**.
> No es un criterio oficial de SAO. Ver la sección final "Propuesta V1 y
> evolución futura" y el listado `pending-validation.md`.

---

## 2. Categorías de la Clasificación Geográfica

La Clasificación Geográfica utiliza cuatro categorías:

| Categoría        | Significado |
|------------------|-------------|
| `COLOMBIA`       | El territorio estudiado está, de forma determinable, dentro de Colombia (todo o una parte del país). |
| `INTERNACIONAL`  | El territorio estudiado está, de forma determinable, fuera de Colombia (uno o varios países distintos de Colombia). |
| `MULTIPAIS`      | El territorio estudiado abarca, de forma determinable, varios países, **incluida** una escala continental, regional o global que involucre a más de un país. |
| `SIN_DETERMINAR` | El territorio estudiado **no puede determinarse** a partir de los metadatos disponibles. Es la categoría por defecto cuando falta información. |

Notas sobre las categorías:

* `COLOMBIA` e `INTERNACIONAL` son mutuamente excluyentes para un territorio
  único determinable.
* `MULTIPAIS` aplica cuando el estudio cubre explícitamente más de un país; si
  entre esos países está Colombia, sigue siendo `MULTIPAIS` (no `COLOMBIA`),
  porque el alcance del estudio es multipaís. La convención exacta para los
  estudios multipaís que incluyen a Colombia queda sujeta a validación por SAO
  (ver sección 6).
* `SIN_DETERMINAR` **no** es un juicio sobre la relevancia del registro; es
  únicamente una constatación de que los metadatos no permiten asignar un
  territorio.

---

## 3. Base de la clasificación: el Territorio_Estudiado

La Clasificación Geográfica se basa en el **Territorio_Estudiado**: el área
geográfica que es **objeto del estudio** descrito por la publicación.

El Territorio_Estudiado **no** es, necesariamente, la afiliación institucional
de los autores. La clasificación **no** debe basarse únicamente en la afiliación
institucional, porque el país de la institución de un autor puede diferir del
país o la región que el estudio investiga.

Ejemplos del principio (ilustrativos, `DEMO_DATA`, no representan registros
reales de SAO):

* Un estudio **sobre aves de los Andes colombianos** firmado por autores de una
  universidad extranjera tiene Territorio_Estudiado en Colombia → `COLOMBIA`,
  aunque la afiliación sea internacional.
* Un estudio **sobre aves migratorias de Norteamérica** firmado por una
  institución colombiana tiene Territorio_Estudiado fuera de Colombia →
  `INTERNACIONAL` o `MULTIPAIS` según el alcance, aunque la afiliación sea
  colombiana.

La afiliación institucional **puede** usarse como **señal secundaria** cuando el
territorio no sea evidente, pero no sustituye al Territorio_Estudiado como base
de la clasificación, y nunca justifica inventar un territorio (ver sección 4).

Posibles fuentes de evidencia del Territorio_Estudiado en los metadatos (según
disponibilidad real de cada fuente; no se asume que todas existan):

* el título, el resumen y las palabras clave;
* topónimos, nombres de regiones, ecosistemas o áreas protegidas mencionados;
* campos geográficos estructurados cuando la fuente los provea.

---

## 4. Regla de no invención

Si el Territorio_Estudiado **no puede determinarse** a partir de los metadatos
disponibles, el registro se clasifica como `SIN_DETERMINAR`.

En este caso:

* **No** se inventa un territorio.
* **No** se asume que el estudio es de Colombia por el contexto del proyecto.
* **No** se deduce un país a partir únicamente de la afiliación institucional
  cuando esta no corresponde al objeto de estudio.

`SIN_DETERMINAR` es un estado válido y preferible frente a una asignación
geográfica no respaldada por los metadatos. Esta regla es coherente con el
principio de **no invención de datos** del steering del proyecto.

---

## 5. Alcance en este spec

En este spec **no** se implementa un **clasificador geográfico** (ni basado en
reglas, ni en machine learning, ni en modelos de lenguaje). Aquí solo se
**define la metodología y las categorías**.

La forma de registrar la Clasificación Geográfica y el Territorio_Estudiado en
cada registro se propone, como campos opcionales de evolución futura
(`geographic_scope` y `studied_territory`), en el contrato de datos
(`article-data-contract.md`), sin convertirlos en obligatorios ni implementarlos
en el código V1.

---

## 6. Propuesta V1 y evolución futura

Las categorías y la metodología descritas son la **propuesta inicial (V1)** del
Equipo_Proyecto para clasificar geográficamente los registros del Componente B,
y están **sujetas a validación por SAO**.

Quedan registradas como `PENDING_VALIDATION` (ver `pending-validation.md`), entre
otras, las siguientes decisiones:

* la confirmación de las cuatro categorías (`COLOMBIA`, `INTERNACIONAL`,
  `MULTIPAIS`, `SIN_DETERMINAR`) y de sus definiciones;
* la convención exacta para los estudios `MULTIPAIS` que incluyen a Colombia;
* la metodología concreta para determinar el Territorio_Estudiado a partir de
  los metadatos de cada fuente;
* el uso y el peso de la afiliación institucional como señal secundaria.

Estos criterios podrán evolucionar tras trabajar con el dataset real, observar
los casos límite y validar los resultados con SAO. Los cambios relevantes deben
documentarse y, cuando afecten decisiones arquitectónicas, registrarse mediante
un ADR en `docs/decisions/`.
