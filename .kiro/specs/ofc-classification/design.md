# Design — Clasificación de artículos por OFC (Componente B)

## Decisión de metodología (V1): reglas por palabras clave

Entre las opciones (reglas, ML supervisado, embeddings, LLM) se eligió **reglas
por palabras clave (lexicón por OFC)**. Justificación atada al contexto:

- **Trazabilidad** (product.md, steering): se puede explicar *por qué* un
  artículo quedó en un OFC (términos coincidentes). ML/embeddings/LLM no ofrecen
  esa transparencia de forma directa.
- **Sin dataset etiquetado**: no existen artículos pre-clasificados por OFC, lo
  que descarta ML supervisado en V1.
- **Local y reproducible** (tech.md §26, §33): sin servicios externos ni modelos
  pesados; resultado determinista.
- **Multilabel natural**: un artículo activa todos los OFC cuyos términos
  aparezcan.
- **Evolución**: se puede añadir embeddings/semántica por encima de las reglas
  sin rehacer el diseño.

Esta decisión se registra como ADR (ver `docs/decisions/`).

## Visión general

```text
dataset procesado (una fuente)        ofc_catalog.json
        │                                    │
        └──────────────┬─────────────────────┘
                       ▼
          Clasificador por reglas (multilabel)
                       │   (texto: title + abstract + keywords)
                       ▼
   dataset clasificado (ofcs, método, confianza, evidencia)
                       │
                       ├─ JSON + CSV en data/processed/
                       └─ backend → dashboard (distribución por OFC)
```

## Componentes

### 1. `classification/ofc_catalog.json`
Catálogo editable de los 11 OFC. Campo `terminos_clave` = lexicón por OFC. Dato
de dominio, no código: SAO puede ajustarlo.

### 2. `classification/ofc_classifier.py`
- Carga el catálogo.
- `clasificar(texto) -> ResultadoClasificacion`: normaliza el texto (minúsculas,
  sin acentos, reutilizando el normalizador existente), busca los términos de
  cada OFC y devuelve la lista de OFC con coincidencias + la evidencia (términos
  que coincidieron) + un score de confianza por OFC.
- Multilabel; si no hay coincidencias devuelve lista vacía.

### 3. `pipelines/classify_dataset.py`
- Toma un dataset procesado (p. ej. `data/processed/boletin_sao/*.json`),
  clasifica cada artículo, rellena `ofcs`, `classification_method`,
  `classification_confidence` y una nota con la evidencia.
- Escribe el dataset clasificado (JSON + CSV) sin modificar el de entrada.
- Mantiene `PENDIENTE_REVISIÓN` cuando la confianza es baja o `NO_CLASIFICADO`.

### 4. Backend + dashboard
- Extiende `BibliometriaService` para leer el dataset clasificado y agregar la
  distribución por OFC.
- Añade la distribución por OFC al `ResumenBibliometrico` y al dashboard.

## Modelo de confianza (explicable)

`classification_confidence` por OFC = número de términos distintos que
coincidieron para ese OFC, normalizado (p. ej. coincidencias / umbral de
referencia, acotado a 1.0). Es un indicador simple y auditable, NO una
probabilidad estadística. Su significado se documenta para no inducir a error.

Umbrales (configurables):
- `>= 1` coincidencia → OFC asignado.
- Confianza "baja" (p. ej. una sola coincidencia débil) → el artículo
  permanece en `PENDIENTE_REVISIÓN`.

## Reglas de calidad

- Comparación insensible a mayúsculas/acentos (via normalizador existente).
- Coincidencia por término completo cuando sea posible (evitar que "río" dispare
  dentro de otra palabra); se evaluará límite de palabra.
- No se inventan OFC; no se modifican definiciones del catálogo.
- La clasificación automática se marca como tal (método + evidencia); nunca se
  presenta como validación humana.

## Limitaciones conocidas (aceptadas en V1)

- Las reglas no capturan sinónimos no listados ni lenguaje indirecto → algunos
  artículos quedarán `NO_CLASIFICADO` o con baja confianza (van a revisión).
- La calidad depende de la cobertura del lexicón, que es editable y mejorará con
  revisión de SAO.

## Verificación

- Pruebas unitarias del clasificador con textos de ejemplo (incluyendo
  multilabel y `NO_CLASIFICADO`).
- Corrida sobre los 35 artículos reales del Boletín SAO: revisar manualmente una
  muestra para validar coherencia (no se espera 100% automático).
