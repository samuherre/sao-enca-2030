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
* **El dataset NO se limita a Colombia.** Se priorizan estudios de Colombia pero
  se incluyen internacionales relevantes (confirmado por los datos reales: hay
  artículos de Panamá, Ecuador, México, El Salvador).
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

* Metodología y algoritmo de clasificación OFC.
* Métricas bibliométricas definitivas.
* Estrategia de deduplicación entre fuentes (hoy: dedupe simple por título).
* Acceso a Scopus (API key), Wiley (TDM) y mecanismo OAI-PMH de UNAL.
* Si se automatiza la descarga de PDFs de SAO (navegador headless) o se mantiene
  asistida.
