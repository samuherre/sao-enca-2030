# Criterios de Inclusión y Exclusión — Componente B (SAO ENCA 2030)

## 1. Objetivo de los criterios

Estos criterios definen cómo decidir si una publicación/documento forma parte
del conjunto de datos del análisis bibliométrico del proyecto SAO.

El propósito es:

* Mantener en el análisis únicamente publicaciones relevantes para la
  **conservación de aves**.
* Acotar temporalmente el conjunto al periodo **2020–2030**.
* Permitir que los casos dudosos queden marcados para **revisión humana** en
  lugar de descartarse o aceptarse automáticamente.
* Garantizar trazabilidad y reproducibilidad en la selección de registros.

Estos criterios se aplican junto con el contrato de datos definido en
`article-data-contract.md` y de forma coordinada con la **Estrategia de
Búsqueda** (`search-strategy.md`), que define el alcance, la cobertura y las
familias de ecuaciones que producen el conjunto de registros sobre el cual se
aplican estos criterios.

> Estado: **Propuesta V1** del Equipo_Proyecto, sujeta a validación por SAO. No
> son criterios oficiales de SAO. Ver la sección final "Propuesta V1 y evolución
> futura".

---

## 2. Criterios de inclusión

Un registro será **candidato a inclusión** cuando cumpla todas las condiciones
siguientes:

* Sea una publicación/documento **identificable**.
* Su fecha de publicación esté **entre 2020 y 2030**.
* Esté **relacionado con aves**.
* Su contenido aporte potencialmente a **comprender, evaluar, monitorear o
  ejecutar** acciones relacionadas con la conservación de aves.

La relevancia para la conservación puede estar relacionada, entre otros
aspectos, con:

* conservación o manejo de aves;
* amenazas a poblaciones de aves;
* pérdida o modificación de hábitat;
* cambio climático;
* contaminación;
* cacería;
* especies invasoras;
* hábitats y ecosistemas importantes para aves;
* poblaciones, distribución o dinámica de especies cuando aporten información
  útil para conservación;
* biodiversidad de aves con utilidad para conservación;
* políticas, estrategias o monitoreo de conservación;
* otros temas relevantes que posteriormente puedan relacionarse con uno o varios
  Objetos Focales de Conservación (OFC).

### 2.1. Registros de aves + conservación por tipo de acción

Son explícitamente **incluibles** los registros relacionados con aves y
conservación que aborden cualquiera de las siguientes acciones:

* **amenazas** a las aves o a sus hábitats;
* **protección** de especies, poblaciones o hábitats;
* **manejo** (gestión) de especies o de hábitats;
* **restauración** de ecosistemas o hábitats relevantes para aves;
* **monitoreo** de poblaciones, especies o hábitats de aves.

Un registro es candidato a inclusión si aborda **al menos una** de estas
acciones en relación con aves; no es necesario que las trate todas.

### 2.2. Elegibilidad por cobertura geográfica

Los **registros internacionales relevantes son elegibles** para inclusión. La
cobertura es internacional con prioridad en Colombia (ver `search-strategy.md`),
por lo que un estudio desarrollado fuera de Colombia **no** se excluye por ese
solo hecho si es relevante para la conservación de aves. La clasificación del
territorio estudiado se documenta por separado en `geographic-classification.md`
y no determina por sí sola la inclusión o exclusión.

### 2.3. Elegibilidad por tipo de documento

Son elegibles para inclusión tanto los **documentos científicos** (p. ej.
artículos de investigación, revisiones) como los **documentos técnicos** (p. ej.
informes técnicos, documentos institucionales, tesis, literatura gris con
información bibliográfica suficiente). El tipo de documento, por sí solo, no es
motivo de exclusión mientras el registro sea identificable y relevante.

---

## 3. Criterios de exclusión

Se **excluirá** un registro cuando se presente alguna de estas situaciones.

Motivos de exclusión principales:

* sea un **duplicado** de otro registro (misma publicación recuperada más de una
  vez por varias consultas o fuentes);
* **no tenga información suficiente** para identificar o analizar la publicación
  (registros sin metadatos bibliográficos mínimos);
* mencione aves **solamente de manera incidental**, sin relación con la
  conservación de aves.

Otros motivos de exclusión:

* esté **fuera del periodo 2020–2030**;
* **no tenga relación relevante** con aves/conservación;
* **no aporte información útil** para conservación;
* **no sea una publicación/documento analizable**;
* sea una **página web, anuncio, noticia o resultado de búsqueda** sin
  información bibliográfica suficiente;
* **no pueda identificarse** mínimamente la publicación;
* resulte **irrelevante** para el objetivo del proyecto después de aplicar los
  criterios definidos.

En todos los casos de exclusión debe registrarse el motivo en `exclusion_reason`
(ver `article-data-contract.md`) para conservar la trazabilidad de la decisión.
La exclusión solo se aplica cuando el motivo es claro; ante **duda** sobre la
relevancia, se usa `PENDIENTE_REVISIÓN` (ver sección 4 y sección 5), nunca la
exclusión automática.

---

## 4. Casos que NO deben excluirse automáticamente

Un registro **no** debe excluirse de forma automática únicamente por:

* ser **internacional**;
* **no tener DOI**;
* **no tener palabras clave**;
* **no tener resumen** (abstract);
* provenir de una **fuente diferente** a las principales;
* ser una **tesis** o **documento técnico**;
* estar relacionado con **múltiples OFC**.

En estos casos, si existe duda sobre la relevancia, el registro debe quedar como
`PENDIENTE_REVISIÓN` en lugar de excluirse.

---

## 5. Estados de inclusión

Se utilizan inicialmente tres estados:

| Estado                | Significado |
|-----------------------|-------------|
| `INCLUIDO`            | El registro cumple los criterios de inclusión y forma parte del análisis. |
| `EXCLUIDO`            | El registro cumple uno o más criterios de exclusión. Debe registrarse el motivo en `exclusion_reason`. |
| `PENDIENTE_REVISIÓN`  | El registro es dudoso y requiere revisión humana antes de decidir. |

Los **casos dudosos** deben poder quedar como `PENDIENTE_REVISIÓN` para
posteriormente realizar revisión manual. No se debe forzar una decisión
automática cuando la relevancia es incierta.

> Regla reforzada: la aparición de cualquier incertidumbre sobre la relevancia
> de un registro **obliga** a asignar `PENDIENTE_REVISIÓN` en lugar de excluirlo
> (o incluirlo) automáticamente. La revisión humana resuelve el estado
> definitivo.

---

## 6. Corpus_Recuperado vs. Corpus_Analitico

Estos criterios de inclusión/exclusión operan sobre dos conjuntos distintos que
deben diferenciarse de forma explícita, en coherencia con la **Estrategia de
Búsqueda** (`search-strategy.md`):

| Conjunto | Definición | Momento |
|----------|------------|---------|
| **Corpus_Recuperado** | Conjunto de registros que una fuente devuelve para las ecuaciones de búsqueda, **antes** de aplicar deduplicación y criterios de inclusión/exclusión. | Resultado directo de la recuperación. |
| **Corpus_Analitico** | Subconjunto definitivo de registros que, **tras** la deduplicación y la aplicación de estos criterios, forma parte del análisis bibliométrico. | Resultado de la selección. |

Relación conceptual:

```text
Ecuaciones de búsqueda (search-strategy.md)
        ↓
  Corpus_Recuperado        (todo lo que devuelve la fuente)
        ↓   deduplicación   → registros duplicados marcados (is_duplicate)
        ↓   criterios        → INCLUIDO / EXCLUIDO / PENDIENTE_REVISIÓN
        ↓
  Corpus_Analitico         (registros INCLUIDO; PENDIENTE_REVISIÓN a la espera
                            de revisión humana; EXCLUIDO fuera del análisis)
```

Puntos clave:

* El **Corpus_Recuperado** puede contener duplicados, registros irrelevantes y
  registros sin información suficiente; su tamaño depende de la fuente y de las
  ecuaciones, no de estos criterios.
* El **Corpus_Analitico** es el conjunto que efectivamente se analiza: lo
  conforman los registros con estado `INCLUIDO`. Los registros
  `PENDIENTE_REVISIÓN` quedan a la espera de revisión humana antes de
  incorporarse o descartarse; los `EXCLUIDO` quedan fuera del análisis pero se
  conservan con su `exclusion_reason` para trazabilidad.
* Ningún registro del Corpus_Recuperado se elimina de forma irreversible: la
  transición de un conjunto al otro se registra mediante el estado de inclusión
  y los campos de trazabilidad del contrato de datos.

---

## 7. Ejemplos

> Los ejemplos siguientes son ilustrativos (`DEMO_DATA`) y no representan
> registros reales de SAO.

### 7.1. Casos incluidos

* Artículo de 2022 sobre el **efecto de la pérdida de hábitat** en poblaciones
  de aves de bosque húmedo en Colombia.
* Estudio internacional de 2021 sobre **monitoreo de aves migratorias** cuyos
  métodos y resultados son útiles para la conservación.
* Tesis de 2023, sin DOI, sobre **distribución de especies de aves** con
  información útil para conservación.
* Artículo de 2024 sobre **impacto del cambio climático** en ecosistemas
  importantes para aves.

### 7.2. Casos excluidos

* Publicación de **2015** (fuera del periodo 2020–2030).
* Artículo de economía que **menciona aves solo de forma incidental**, sin aporte
  a la conservación.
* **Noticia web** sin información bibliográfica suficiente para identificar la
  publicación.
* Registro **duplicado** de otro ya incluido (se marca `is_duplicate = true` y
  se referencia `duplicate_of`).

### 7.3. Casos pendientes de revisión

* Registro de 2023 relacionado con aves cuyo **resumen es ambiguo** y no permite
  determinar con claridad su aporte a la conservación.
* Documento técnico internacional **sin DOI ni palabras clave**, posiblemente
  relevante, que requiere revisión humana.
* Artículo cuyo **año de publicación no está claramente indicado** pero parece
  dentro del periodo.

---

## 8. Propuesta V1 y evolución futura

Estos criterios son nuestra **propuesta inicial (V1)** para la selección de
publicaciones del Componente B.

Podrán **evolucionar** después de:

* trabajar con el **dataset real** y observar los casos límite reales;
* **validar los resultados con SAO**;
* definir con mayor precisión qué se considera "relevante para la conservación";
* establecer reglas concretas de **deduplicación** según los metadatos
  disponibles;
* ajustar o ampliar los **estados de inclusión** si la revisión manual lo
  requiere.

Mientras tanto, ante cualquier incertidumbre, debe preferirse el estado
`PENDIENTE_REVISIÓN` sobre una decisión automática no respaldada. Los cambios
relevantes en estos criterios deben documentarse y, cuando afecten decisiones
arquitectónicas, registrarse mediante un ADR en `docs/decisions/`.
