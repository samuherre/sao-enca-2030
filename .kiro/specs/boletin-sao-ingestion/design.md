# Design — Ingesta de la fuente Boletín SAO (Componente B)

## Visión general

Pipeline por lotes, sin interfaz gráfica, que convierte PDFs del Boletín SAO en
un dataset estructurado conforme al Article Data Contract V1. Diseñado como el
primer **conector de fuente**; el contrato de salida es común a todas las
fuentes futuras.

```
data/raw/boletin_sao/*.pdf
        │
        ▼
 [1] Extracción por PDF        ingestion/extract_boletin.py
        │   (texto → campos)
        ▼
 [2] Normalización de texto    preprocessing/text_normalizer.py
        │
        ▼
 [3] Orquestación en lote      pipelines/process_boletin_sao.py
        │   (validación periodo + dedupe + consolidación)
        ▼
 data/processed/boletin_sao/   dataset JSON + CSV
```

## Componentes

### 1. `preprocessing/text_normalizer.py`
Corrige artefactos de extracción de PDF: acentos combinantes sueltos
(`Bolet´ın` → `Boletín`), ñ partida (`Castan˜o` → `Castaño`), i sin punto, y
normaliza espacios. **No** re-segmenta palabras pegadas (requeriría diccionario
→ riesgo de inventar). Función pública: `normalize_text(text) -> str`.

### 2. `ingestion/extract_boletin.py`
Extrae de la primera página los campos del contrato. Decisiones de diseño:
- **Alta confianza por regex** para volumen/año (línea de cita) y páginas.
  La regex tolera espacios opcionales (`BoletínSAOVol`) por variaciones de
  extracción.
- **Heurística para título/autores** (texto en mayúsculas, delimitado por el
  inicio del título en inglés; autores por superíndices de afiliación). Cuando
  es ambigua, el registro va a `PENDIENTE_REVISIÓN`.
- **Abstract/keywords** entre marcadores `Resumen` / `Palabras clave` /
  `Key words` / `Abstract`.
- Devuelve un `ArticleRecord` (dataclass) con todos los campos del contrato V1.
  Función pública: `extract_article(pdf_path) -> ArticleRecord`.

### 3. `pipelines/process_boletin_sao.py`
Orquesta el lote: recorre la carpeta, llama al extractor, valida el periodo
2020–2030, marca duplicados por título normalizado (sin borrar), consolida y
escribe JSON + CSV, e imprime un resumen de completitud. Acepta `--input` para
elegir carpeta; por defecto `data/raw/boletin_sao/` (con fallback a `samples`
para desarrollo).

## Modelo de datos (salida)

Cada registro sigue `docs/bibliometrics/article-data-contract.md`. Campos
siempre fijados por este conector: `source = "Boletín SAO"`,
`journal = "Boletín SAO"`, `extraction_method`, `extraction_date`,
`processing_status`, `inclusion_status`, `is_duplicate`.

## Manejo de errores

- Un PDF que falla no detiene el lote: se registra `[ERR]` y se continúa.
- Campos no detectados → `null`; nunca se inventan.
- Faltante obligatorio o ambigüedad → `PENDIENTE_REVISIÓN` con nota.

## Decisiones técnicas

- **pdfplumber** (pinned en `bibliometrics/requirements.txt`): conserva mejor el
  layout que pypdf, útil para delimitar el encabezado.
- **Reglas/heurísticas en V1**, no ML: el formato del boletín es regular y las
  reglas son transparentes y depurables. ML/LLM queda `PENDING_VALIDATION`.
- **Separación de responsabilidades**: normalización, extracción y orquestación
  en módulos distintos (structure.md §2).

## Limitaciones conocidas (aceptadas en V1)

- Palabras pegadas en algunos abstracts (párrafos justificados).
- Acentos ausentes en títulos en MAYÚSCULA (el PDF los separa en otra fila).
- ~5% de PDFs con formato atípico (título en minúscula, sin la palabra
  "Resumen") caen en `PENDIENTE_REVISIÓN`. Es el comportamiento correcto:
  señalar para revisión humana en vez de inventar.

## Estrategia de verificación

- Corrida real sobre los 35 PDFs: medir completitud por campo.
- Revisión manual del CSV para confirmar que la metadata no está inventada.
- Los casos `PENDIENTE_REVISIÓN` deben tener nota explicativa.
