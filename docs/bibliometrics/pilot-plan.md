# Plan de Piloto Controlado — Componente B (SAO ENCA 2030)

## 1. Objetivo y naturaleza del piloto

Este documento especifica un **Piloto Controlado** del flujo bibliométrico del
Componente B: un procedimiento acotado que recupera un conjunto **reducido** de
metadatos para **validar el flujo completo** de principio a fin (recuperación →
deduplicación → criterios de inclusión/exclusión → clasificación geográfica),
verificando además su **compatibilidad** con la clasificación por OFC existente.

El piloto sirve para comprobar, con un volumen pequeño y controlado, que:

* las ecuaciones de búsqueda de la Estrategia de Búsqueda
  (`search-strategy.md`) producen un `Corpus_Recuperado` manejable;
* la deduplicación, los criterios de inclusión/exclusión
  (`inclusion-exclusion-criteria.md`) y la clasificación geográfica
  (`geographic-classification.md`) se encadenan de forma coherente;
* el contrato de datos (`article-data-contract.md`) registra la trazabilidad
  necesaria en cada registro;
* los casos de relevancia incierta se marcan `PENDIENTE_REVISIÓN`, nunca como
  "incluido" automático.

> **Naturaleza del documento.** Este es un procedimiento **especificado, no
> ejecutado a escala**. En este spec el piloto se documenta como procedimiento y
> **no** se ejecuta como recolección masiva (`Recoleccion_Masiva`). No se lanzan
> búsquedas reales contra las fuentes ni se consumen cuotas más allá de lo mínimo
> indispensable que, en todo caso, queda fuera del alcance de este spec. La
> ejecución real del piloto requiere la validación previa de SAO y la
> verificación de cuotas, restricciones y costos de la fuente.

> Estado: **Propuesta V1** del Equipo_Proyecto, **sujeta a validación por SAO**.
> No es un criterio oficial de SAO. Las decisiones no confirmadas quedan
> listadas en `pending-validation.md`.

---

## 2. Alcance del piloto

### 2.1. Fuentes

El piloto utiliza **una o dos fuentes accesibles**, no todas las fuentes
posibles del Componente B.

* Fuente primaria propuesta: **OpenAlex**, el único `Proveedor_API` instanciado
  e implementado en este spec (ver `api-key-integration.md`). Es accesible por
  API de metadatos y no requiere costos de suscripción.
* Fuente secundaria opcional: una segunda fuente accesible, **solo si** aporta
  valor para validar la deduplicación **entre fuentes**. Su incorporación queda
  `PENDING_VALIDATION` (ver `pending-validation.md`); los proveedores Scopus,
  Wiley y UNAL OAI-PMH **no** se usan en este piloto.

El piloto se concibe para funcionar incluso con **una sola fuente**; la segunda
fuente es opcional y no es un requisito del procedimiento.

### 2.2. Ecuaciones de búsqueda

El piloto usa un **conjunto reducido** de ecuaciones, no las cinco familias
completas de la Estrategia de Búsqueda.

* Selección propuesta: **una o dos** `Familia_Ecuaciones`, por ejemplo
  "aves + conservación" y, si se desea priorizar el territorio nacional,
  "aves + conservación + Colombia" (ver `search-strategy.md`, sección 6).
* Cada ecuación se **instancia** según la sintaxis de la fuente (en OpenAlex,
  `search` + `filter`), aplicando el periodo **2020–2030 inclusive** y, cuando la
  fuente lo permita, el filtro por idioma (español, inglés, portugués).

### 2.3. Volumen y límite de recuperación

El piloto es **deliberadamente pequeño**. Se recupera un número reducido de
registros, muy por debajo del `Limite_Recuperacion` recomendado de 5.000 por
corrida (ver `retrieval-limits.md`). El objetivo es validar el flujo, **no**
construir el `Corpus_Analitico` definitivo ni recuperar todo el
`Corpus_Recuperado` de la fuente.

---

## 3. Pasos del procedimiento

El piloto ejecuta, en orden, los siguientes pasos. Cada paso se apoya en los
documentos y el código ya existentes y **no** introduce lógica nueva.

```text
Ecuaciones reducidas (search-strategy.md)
        │
        ▼
 1. Recuperación de metadatos  ─────────────►  Corpus_Recuperado (reducido)
        │
        ▼
 2. Deduplicación               (article_id determinista; is_duplicate / duplicate_of)
        │
        ▼
 3. Criterios de inclusión/exclusión  ──────►  INCLUIDO / EXCLUIDO / PENDIENTE_REVISIÓN
        │
        ▼
 4. Clasificación geográfica    (COLOMBIA / INTERNACIONAL / MULTIPAIS / SIN_DETERMINAR)
        │
        ▼
 Corpus_Analitico (reducido) + registros PENDIENTE_REVISIÓN
```

### 3.1. Recuperación de metadatos

Se ejecutan las ecuaciones reducidas contra la fuente accesible y se obtiene el
`Corpus_Recuperado`: los metadatos bibliográficos que la fuente devuelve, antes
de deduplicar y aplicar criterios. Para OpenAlex, la recuperación usa el conector
existente; la paginación por cursor más allá de la primera página requiere la
API key provista por `OPENALEX_API_KEY` (ver `api-key-integration.md`).

> **Metadatos ≠ texto completo.** El piloto trabaja únicamente con **metadatos**;
> una API de metadatos no implica acceso al texto completo. No se atribuyen a la
> fuente capacidades no confirmadas.

### 3.2. Deduplicación

Se identifican las publicaciones duplicadas. La identificación de "misma
publicación" se apoya en el **`article_id` determinista** ya existente: la misma
publicación produce el mismo `article_id`, de modo que las apariciones repetidas
convergen en un único registro. Los duplicados que sí generan registros separados
(p. ej. entre fuentes) se marcan con `is_duplicate` y se referencian con
`duplicate_of` (ver `article-data-contract.md`). Ningún registro se elimina de
forma irreversible: la relación se conserva para trazabilidad.

> La estrategia definitiva de deduplicación **entre fuentes** queda
> `PENDING_VALIDATION` (ver `pending-validation.md`); el piloto aplica la
> deduplicación ya soportada por el código.

### 3.3. Aplicación de los criterios de inclusión/exclusión

Sobre el corpus deduplicado se aplican los `Criterios_Inclusion_Exclusion`
(`inclusion-exclusion-criteria.md`). Cada registro recibe uno de los estados:

| Estado | Significado en el piloto |
|--------|--------------------------|
| `INCLUIDO` | Cumple los criterios de inclusión; forma parte del `Corpus_Analitico` reducido. |
| `EXCLUIDO` | Cumple un criterio de exclusión; se registra el motivo en `exclusion_reason`. |
| `PENDIENTE_REVISIÓN` | Relevancia incierta; queda para revisión humana (ver sección 5). |

El resultado permite distinguir explícitamente el `Corpus_Recuperado` del
`Corpus_Analitico` (registros `INCLUIDO`), con los `PENDIENTE_REVISIÓN` a la
espera de revisión y los `EXCLUIDO` conservados con su motivo.

### 3.4. Clasificación geográfica

A cada registro se le asocia su `Clasificacion_Geografica` según el
**Territorio_Estudiado**: `COLOMBIA`, `INTERNACIONAL`, `MULTIPAIS` o
`SIN_DETERMINAR` (ver `geographic-classification.md`). Rige la **regla de no
invención**: si el territorio no puede determinarse a partir de los metadatos, se
asigna `SIN_DETERMINAR`, sin inventar un territorio y sin asumir que el estudio
es de Colombia por el contexto del proyecto.

> En este spec **no** se implementa un clasificador geográfico; el piloto solo
> **aplica la metodología definida** para registrar el alcance geográfico cuando
> sea determinable, apoyándose en los campos propuestos `geographic_scope` y
> `studied_territory` del contrato de datos (opcionales, propuesta V1).

---

## 4. Compatibilidad con la clasificación por OFC (sin implementar el clasificador)

El piloto es **compatible** con la clasificación por Objetos Focales de
Conservación (OFC) existente, **sin implementar** el clasificador.

* El contrato de datos ya prevé el campo `ofcs` (multilabel, opcional): un
  artículo puede asociarse a **uno o varios** de los 11 OFC (relación N:N; ver
  `article-data-contract.md`, sección 6).
* El piloto **deja disponible** la estructura para registrar los OFC, pero **no**
  ejecuta ninguna clasificación automática ni asigna OFC por sí mismo.
* La **metodología y el algoritmo** de clasificación por OFC quedan
  `PENDING_VALIDATION` (ver `pending-validation.md`) y no se implementan en este
  spec. El piloto no asume si un artículo pertenece a uno o varios OFC, ni define
  reglas de asignación.

En otras palabras, el piloto valida que el flujo encaja con la clasificación por
OFC **ya contemplada** en el modelo de datos, sin construir el clasificador.

---

## 5. Registros de relevancia incierta → `PENDIENTE_REVISIÓN`

Regla central del piloto: **todo registro de relevancia incierta se marca
`PENDIENTE_REVISIÓN`, nunca "incluido" automático**.

* Si existe cualquier duda sobre si un registro es relevante para la conservación
  de aves, se asigna `PENDIENTE_REVISIÓN` y queda a la espera de **revisión
  humana**, en lugar de incluirse o excluirse de forma automática.
* El piloto **no** fuerza una decisión automática ante la incertidumbre. La
  revisión humana resuelve el estado definitivo (`INCLUIDO` o `EXCLUIDO`).
* Esta regla es coherente con los `Criterios_Inclusion_Exclusion`
  (`inclusion-exclusion-criteria.md`, secciones 4 y 5) y con el principio de
  **no invención** del steering del proyecto.

---

## 6. Trazabilidad y resultados del piloto

Aun siendo reducido, el piloto conserva la trazabilidad definida en el contrato
de datos:

* cada registro mantiene su `article_id`, su `source`, su `extraction_date`, su
  `inclusion_status` y, cuando aplique, su `exclusion_reason` y su clasificación
  geográfica;
* la consulta que recuperó cada registro puede registrarse mediante el campo
  propuesto de origen de la consulta (`source_query` / `retrieved_by_query`,
  opcional, propuesta V1 en `article-data-contract.md`);
* la corrida del piloto se resume con un `Resumen_Ejecucion` (recuperados,
  nuevos, duplicados y errores), de forma análoga a cualquier `Corrida_Ingesta`
  (ver `retrieval-limits.md`).

El piloto se considera satisfactorio si el flujo completo se encadena de forma
coherente, los estados de inclusión y la clasificación geográfica se asignan sin
invención de datos, y los casos dudosos quedan correctamente en
`PENDIENTE_REVISIÓN`.

---

## 7. Qué NO hace este piloto

Para evitar ambigüedad sobre el alcance:

* **No** ejecuta una `Recoleccion_Masiva` ni una recuperación a gran escala en
  este spec.
* **No** consume cuotas de las fuentes dentro del alcance de este spec: el
  procedimiento se documenta, no se ejecuta a escala.
* **No** implementa el clasificador por OFC ni un clasificador geográfico.
* **No** define la estrategia de deduplicación entre fuentes ni el valor
  definitivo del `Limite_Recuperacion` (ambos `PENDING_VALIDATION`).
* **No** modifica el servicio consolidado, el endpoint, la vista bibliométrica ni
  el procesamiento del Boletín SAO.

---

## 8. Propuesta V1 y evolución futura

Este plan es la **propuesta inicial (V1)** del Equipo_Proyecto para validar el
flujo bibliométrico del Componente B con un piloto controlado, y está **sujeta a
validación por SAO**.

Quedan registradas como `PENDING_VALIDATION` (ver `pending-validation.md`), entre
otras, las decisiones sobre: las familias de ecuaciones usadas en el piloto, la
definición de relevancia temática, las categorías y la metodología de la
clasificación geográfica, la estrategia de deduplicación entre fuentes, la
metodología/algoritmo de clasificación por OFC, la incorporación de otras fuentes
y el valor definitivo del `Limite_Recuperacion`.

La **ejecución real** del piloto, cuando SAO la autorice, debe verificar
previamente las cuotas, restricciones y costos de la fuente, y documentar sus
resultados. Los cambios relevantes derivados del piloto deben documentarse y,
cuando afecten decisiones arquitectónicas, registrarse mediante un ADR en
`docs/decisions/`.
