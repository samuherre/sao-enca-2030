# bibliometrics/

Procesamiento específico relacionado con el análisis bibliométrico.

Esta carpeta se mantiene separada del backend porque el procesamiento
bibliométrico debe poder ejecutarse de forma independiente de la interfaz
(ver `structure.md` §7 y §30).

## Estado

Lenguaje DEFINIDO: **Python** (`tech.md` §3, §11, §39, ADR-001). El resto del
componente bibliométrico está deliberadamente **DESACOPLADO y SIN IMPLEMENTAR**,
y permanece `PENDING_VALIDATION`. No existe todavía:

- Dataset real de artículos (`data-inventory.md` DATA-012, prioridad P0).
- Definición de categorías de clasificación (`data-inventory.md` DATA-013).
- Relación confirmada artículo ↔ OFC, incluida su cardinalidad (`tech.md` §14;
  `data-and-domain.md` §12, §20).
- Metodología/algoritmo/modelo de clasificación (`tech.md` §13).
- Estrategia de deduplicación (`tech.md` §24) y métricas (`tech.md` §15).

NO se implementa el clasificador ni la ingesta real de artículos hasta que SAO
proporcione el dataset y las definiciones. El lenguaje está fijado, pero el
método NO: no asumir reglas, ML, embeddings ni LLM (`tech.md` §13).

## Submódulos (esqueleto conceptual, según structure.md §7–§15)

- `ingestion/` — incorporar nuevos datasets (pendiente de dataset real).
- `preprocessing/` — preparar artículos antes del análisis.
- `deduplication/` — identificar duplicados (regla no definida).
- `classification/` — clasificación de artículos (metodología no definida).
- `evaluation/` — métricas de calidad de clasificación.
- `analysis/` — estadísticas y análisis sobre resultados.
- `pipelines/` — coordinación reproducible de etapas.
- `models/` — modelos/componentes y sus versiones.

## Regla

El pipeline bibliométrico debe poder ejecutarse sin abrir la interfaz gráfica
(`structure.md` §30). La interfaz consulta resultados almacenados, no ejecuta
procesamiento pesado.
