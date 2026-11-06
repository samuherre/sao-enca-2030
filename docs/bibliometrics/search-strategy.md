# Estrategia de Búsqueda — Componente B (SAO ENCA 2030)

## 1. Objetivo y estado

Este documento define la **estrategia de búsqueda** del análisis bibliométrico
del proyecto SAO (Componente B): el alcance, la cobertura, el periodo, el foco
temático, los idiomas objetivo y las familias de ecuaciones de búsqueda que
guían la recuperación de publicaciones.

Su propósito es que la estrategia sea **reproducible** y **revisable** por SAO
sin ambigüedad, de modo que cualquier integrante del equipo pueda entender
qué se busca, con qué términos y con qué límites.

> Estado: **Propuesta V1** del Equipo_Proyecto, **sujeta a validación por SAO**.
> El periodo, la cobertura, el foco temático, los idiomas y, en particular, las
> familias de ecuaciones son una **propuesta del equipo del proyecto**, no
> criterios oficiales de SAO. Las decisiones no confirmadas quedan listadas en
> `pending-validation.md`.

Esta estrategia se aplica junto con los criterios de selección definidos en
`inclusion-exclusion-criteria.md` y el contrato de datos de
`article-data-contract.md`.

---

## 2. Alcance y cobertura

### 2.1. Periodo

El periodo de inclusión de la búsqueda son los años **2020 a 2030 inclusive**.

Se recuperan publicaciones cuyo año de publicación esté comprendido en ese
rango (ambos extremos incluidos).

### 2.2. Cobertura geográfica

La cobertura es **internacional con prioridad en Colombia**.

Esto significa que:

* la búsqueda **no se limita exclusivamente a Colombia**;
* los estudios **internacionales relevantes** para la conservación de aves son
  elegibles para la estrategia;
* Colombia recibe **prioridad** mediante una familia de ecuaciones específica
  (ver la sección de familias de ecuaciones), sin que ello excluya la cobertura
  internacional.

La clasificación de cada registro según el territorio estudiado se define
aparte, en `geographic-classification.md`.

---

## 3. Foco temático

El foco temático de la estrategia es la **conservación de aves**, entendida de
forma amplia e incluyendo, entre otros aspectos:

* **amenazas** a las poblaciones de aves;
* **protección** de aves, sus hábitats y ecosistemas;
* **monitoreo** de poblaciones y de especies;
* **restauración** de hábitats y ecosistemas relevantes para aves;
* **gestión** (manejo) de especies y de hábitats.

El foco cubre tanto la gestión de **especies** como la gestión de **hábitats**
cuando aportan a comprender, evaluar, monitorear o ejecutar acciones de
conservación de aves.

> La definición precisa de "relevancia temática para la conservación de aves"
> queda como decisión a validar con SAO (ver `pending-validation.md`).

---

## 4. Idiomas objetivo

Los idiomas objetivo de la estrategia son **español, inglés y portugués**.

El filtrado por idioma se aplica **cuando la fuente permite filtrar por idioma**.
Si una fuente no ofrece filtro por idioma, el idioma no se usa como criterio de
recuperación en esa fuente y la depuración por idioma, si procede, se realiza en
etapas posteriores.

---

## 5. Corpus recuperado vs. corpus analítico

La estrategia distingue de forma explícita entre dos conjuntos de registros:

| Concepto | Definición |
|----------|------------|
| **Corpus_Recuperado** | Conjunto de registros que una fuente **devuelve** para una búsqueda, **antes** de aplicar deduplicación y los criterios de inclusión/exclusión. Puede contener duplicados, registros sin información suficiente y registros no relevantes. |
| **Corpus_Analitico** | Subconjunto **definitivo** de registros que, tras la **deduplicación** y la aplicación de los `Criterios_Inclusion_Exclusion`, forma parte del **análisis bibliométrico**. |

La relación entre ambos es:

```text
Corpus_Recuperado
      │
      ├── deduplicación
      │
      ├── criterios de inclusión / exclusión
      │        (dudosos → PENDIENTE_REVISIÓN)
      │
      ▼
Corpus_Analitico
```

Un registro recuperado **no** forma parte automáticamente del Corpus_Analitico:
solo lo hace tras pasar la deduplicación y los criterios de selección. Los casos
dudosos quedan en estado `PENDIENTE_REVISIÓN`, no se incluyen ni se excluyen
automáticamente (ver `inclusion-exclusion-criteria.md`).

El `Limite_Recuperacion` (ver `retrieval-limits.md`) es un control operativo
sobre el Corpus_Recuperado por corrida y **no** es el límite del
Corpus_Analitico.

---

## 6. Familias de ecuaciones de búsqueda

La estrategia organiza las búsquedas en **cinco familias de ecuaciones**
(`Familia_Ecuaciones`), cada una enfocada en una temática relacionada con la
conservación de aves. Cada familia usa **sinónimos** combinados con el operador
**`OR`** para ampliar la cobertura de términos.

Las familias propuestas son:

1. **Aves + conservación**
2. **Aves + conservación + Colombia**
3. **Aves + amenazas o pérdida de hábitat**
4. **Aves + biodiversidad, áreas protegidas o restauración**
5. **Aves + especies amenazadas o monitoreo de poblaciones**

### 6.1. Sinónimos y operador `OR`

Dentro de cada familia, los términos de un mismo concepto se combinan con `OR`
para incluir variantes e idiomas. Los conjuntos de sinónimos siguientes son una
**propuesta inicial** y no una lista cerrada.

* **Aves**: `aves OR pájaros OR avifauna OR birds OR avian OR aves (pt)` — p. ej.
  `birds`, `avian`, `aves`, `avifauna`.
* **Conservación**: `conservación OR conservation OR conservação OR protección OR
  protection OR manejo OR management`.
* **Colombia**: `Colombia OR colombiano OR colombiana OR Colombian`.
* **Amenazas / pérdida de hábitat**: `amenaza OR amenazas OR threat OR threats OR
  pérdida de hábitat OR habitat loss OR perda de habitat OR degradación OR
  degradation`.
* **Biodiversidad / áreas protegidas / restauración**: `biodiversidad OR
  biodiversity OR biodiversidade OR área protegida OR áreas protegidas OR
  protected area OR protected areas OR restauración OR restoration OR
  restauração`.
* **Especies amenazadas / monitoreo de poblaciones**: `especie amenazada OR
  especies amenazadas OR threatened species OR endangered species OR monitoreo OR
  monitoring OR monitoramento OR población OR poblaciones OR population OR
  populations`.

> Los sinónimos de cada concepto se amplían o ajustan durante la validación con
> SAO y al trabajar con los datos reales de cada fuente.

### 6.2. Semántica de las ecuaciones

* Una ecuación **no exige que todos los términos aparezcan simultáneamente** en
  un mismo registro. La ecuación describe un espacio de términos relevantes
  combinados con `OR`; un registro es recuperado si satisface la condición de la
  fuente para esa combinación, no por contener todas las palabras a la vez.
* La **sintaxis de cada ecuación se adapta a cada fuente**. No se asume que los
  operadores, los campos de búsqueda ni la forma de filtrar sean idénticos entre
  fuentes. Cada familia se **instancia** según las capacidades de cada
  `Proveedor_API`.

### 6.3. Instanciación en OpenAlex

En **OpenAlex** (único proveedor instanciado en este spec), las familias se
expresan combinando:

* el parámetro **`search`** para los términos temáticos (aves, conservación,
  amenazas, etc.);
* el parámetro **`filter`** para acotar por periodo (año **2020–2030
  inclusive**), por idioma (español, inglés, portugués) cuando se filtra por
  idioma, y por otros atributos soportados por la fuente.

De este modo, la misma familia de ecuaciones se traduce a la sintaxis concreta
de OpenAlex (`search` + `filter`), mientras que para otras fuentes futuras
(ver `pending-validation.md`) la sintaxis se adaptaría a sus propios operadores y
campos. La especificación detallada de la integración por API vive en
`api-key-integration.md`.

---

## 7. Estado de propuesta y evolución futura

Las familias de ecuaciones, sus sinónimos, el periodo, la cobertura, el foco
temático y los idiomas objetivo son una **propuesta V1 del Equipo_Proyecto**, no
un criterio oficial de SAO.

Estas decisiones podrán **evolucionar** tras:

* la **validación con SAO** de las familias de ecuaciones y de la definición de
  relevancia temática;
* el trabajo con los **datos reales** de cada fuente y la observación de los
  casos límite;
* el ajuste de **sinónimos** e idiomas según la cobertura real de cada fuente.

Las decisiones no confirmadas quedan registradas de forma explícita en
`pending-validation.md`. Los cambios relevantes de la estrategia deben
documentarse y, cuando afecten decisiones arquitectónicas, registrarse mediante
un ADR en `docs/decisions/`.
