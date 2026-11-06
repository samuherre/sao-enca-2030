# ADR-010 — Metodología de clasificación de artículos por OFC

- **Estado:** Aceptada
- **Fecha:** 2026-10-08
- **Ámbito:** Clasificación automática de artículos científicos por Objeto Focal
  de Conservación (OFC) en el Componente B (bibliometría).
- **Relación:** Resuelve el punto que quedaba `PENDING_VALIDATION` sobre la
  metodología de clasificación (`tech.md` §13, `data-and-domain.md` §19–§20,
  steering `bibliometrics.md` §6). No modifica el stack de ADR-001.

---

## Contexto

El Componente B debe clasificar artículos por los 11 OFC de la ENCA 2030. SAO
no impuso una metodología: entregó el contexto, los OFC y las fuentes, y dejó la
decisión de algoritmo al equipo SAO-EAFIT. Para no postergar una decisión que
de todos modos corresponde al equipo, se define aquí la metodología V1.

Hechos relevantes:
- La relación Artículo ↔ OFC es **muchos a muchos (multilabel)** (confirmado por
  Julián, SAO).
- **No existe un dataset etiquetado** de artículos pre-clasificados por OFC.
- El sistema debe ser **trazable** (explicar por qué un artículo quedó en un
  OFC), **reproducible** y **ejecutable localmente** (product.md, tech.md §26).
- Los 11 OFC están **caracterizados** (definición, hábitats, aves) en el
  documento oficial ENCA 2030, insumo directo para un lexicón.

---

## Problema

Elegir una metodología de clasificación que sea trazable, reproducible, local,
multilabel y viable **sin datos de entrenamiento**.

---

## Opciones consideradas

- **Reglas por palabras clave / lexicón por OFC** (elegida): asigna OFC según
  coincidencias de términos (hábitats, ecosistemas, aves) en título, abstract y
  keywords. Transparente, sin entrenamiento, multilabel natural, local.
- **ML supervisado:** requiere un dataset etiquetado inexistente; implicaría
  etiquetar cientos de artículos a mano antes de empezar. Inviable en V1.
- **Embeddings / similitud semántica:** capta sinónimos mejor, pero añade
  modelos/dependencias pesadas y reduce la transparencia del "porqué".
- **LLM:** costo/API, no determinista, caja negra; en tensión con el requisito
  de trazabilidad.

---

## Decisión

Se adopta la **clasificación por reglas de palabras clave (multilabel),
versión `reglas-keywords-v1`**:

- Un catálogo editable (`bibliometrics/classification/ofc_catalog.json`) define
  los 11 OFC y su lexicón (`terminos_clave`).
- El clasificador normaliza el texto (minúsculas, sin acentos) y asigna cada OFC
  con al menos una coincidencia; registra la **evidencia** (términos
  coincidentes) y una **confianza explicable** (basada en el nº de
  coincidencias).
- Sin coincidencias → `NO_CLASIFICADO`; baja confianza → permanece en
  `PENDIENTE_REVISIÓN`.

---

## Justificación

- **Trazabilidad** (product.md, steering): la evidencia de términos permite
  explicar y auditar cada asignación.
- **Viabilidad inmediata**: no depende de un dataset etiquetado ni de servicios
  externos.
- **Local y reproducible** (tech.md §26, §33): resultado determinista.
- **Multilabel** sin esfuerzo adicional.
- **Evolución**: se puede añadir una capa de embeddings/semántica sobre las
  reglas en el futuro sin rehacer el diseño.

---

## Consecuencias

### Positivas

- Clasificación operativa desde V1, trazable y revisable por SAO.
- El lexicón es dato editable: SAO/EAFIT lo mejoran sin tocar código.

### Negativas / limitaciones

- Las reglas no capturan sinónimos no listados ni lenguaje indirecto; algunos
  artículos quedarán `NO_CLASIFICADO` o con baja confianza y pasarán a revisión
  humana. Esto es intencional (no inventar), no un defecto.
- La calidad depende de la cobertura del lexicón.

---

## Evolución del lexicón (post-decisión)

El catálogo (`bibliometrics/classification/ofc_catalog.json`) es un dato
editable; su cobertura se amplía sin modificar el algoritmo. Historial:

- **v2.0** — lexicón inicial, mayoritariamente en español (términos fuertes de
  hábitat vs. débiles geográficos/de contexto).
- **v2.1** — añadidos sinónimos de hábitat en inglés derivados de las
  definiciones/hábitats ya listados en cada OFC, para mejorar la cobertura en
  corpus en inglés (p. ej. OpenAlex). No se añadieron categorías ni aves nuevas.
- **v2.2** — añadidos términos de hábitat en inglés validados **uno a uno**
  contra la frecuencia real en el corpus y mapeables a un OFC **colombiano**
  concreto (p. ej. `riparian`, `reservoir`, `reef` → OFC-02/01; `shrubland`,
  `scrub` → OFC-04; `orchard`, `paddy` → OFC-09). Se **excluyeron
  deliberadamente** biomas templados/boreales (`woodland`, `steppe`,
  `boreal/temperate/deciduous forest`) por **no corresponder a ningún OFC de la
  ENCA Colombia**: incluirlos habría generado falsos positivos.

Efecto medido sobre la corrida de OpenAlex (5.000 artículos), artículos sin OFC:
2.793 (v2.0) → 2.619 (v2.1) → 2.526 (v2.2). La reducción es por mayor cobertura
real del lexicón, **no** por forzar clasificaciones: los artículos de
conservación general sin ecosistema focal, y los estudios de biomas ajenos al
esquema colombiano, permanecen `NO_CLASIFICADO` / `PENDIENTE_REVISIÓN` por
diseño (principio de no invención, `product.md` §15, `bibliometrics.md` §4.1).
Llegar a "0 sin clasificar" NO es un objetivo: el objetivo es cero
clasificaciones inventadas.

---
## Actualización del Steering

`tech.md` §13, `data-and-domain.md` §19–§20 y `bibliometrics.md` §6 marcan la
clasificación como `PENDING_VALIDATION`. Esta ADR define la metodología V1. La
modificación de los archivos de Steering requiere indicación explícita
(`tech.md` §36.6); se deja anotado aquí para su actualización por quien
corresponda.
