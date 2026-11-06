# Piloto de Extracción de PDFs — Hallazgos (Componente B, SAO ENCA 2030)

> Estado: **Piloto V1 — completado**
>
> Este documento registra los hallazgos del primer piloto de extracción
> automática de artículos a partir de PDFs del Boletín SAO. Es la base empírica
> para decidir cómo procesar los 35 boletines. No sustituye al
> `article-data-contract.md`; lo complementa con evidencia real.

---

## 1. Objetivo del piloto

Antes de recopilar y clasificar manualmente miles de artículos, comprobar con
una muestra pequeña **cuánto del proceso puede automatizarse** y qué queda como
trabajo humano. El piloto NO procesa los 35 boletines ni implementa
clasificación OFC.

## 2. Muestra utilizada

6 PDFs de separatas del Boletín SAO (1 por año), en `data/samples/`:

| Archivo              | Vol. | Año  | Páginas |
|----------------------|------|------|---------|
| `BSVol29_2020.pdf`   | 29   | 2020 | 1-5     |
| `BSVol30_2021.pdf`   | 30   | 2021 | 32-36   |
| `BSVol31_2022.pdf`   | 31   | 2022 | 7-15    |
| `BSVol32_2023.pdf`   | 32   | 2023 | 19-23   |
| `BSVol33_2024.pdf`   | 33   | 2024 | 12-16   |
| `BSVol34_2025.pdf`   | 34   | 2025 | 35-38   |

También se usó `InstruccionesBolSAO2023.md` (instrucciones para autores) para
conocer la estructura esperada de los manuscritos.

## 3. Pipeline probado

```text
PDF
 ↓  (pdfplumber)
texto crudo
 ↓  (preprocessing/text_normalizer.py)
texto normalizado
 ↓  (ingestion/extract_boletin.py)
registro JSON conforme a Article Data Contract V1
```

Salida generada: `data/interim/piloto_boletines/articulos_piloto.json`.

## 4. Hallazgos principales

### 4.1. 1 PDF = 1 artículo (en estas separatas)

En los 6 PDFs aparece **exactamente un** artículo: un solo `Resumen`, un solo
`Abstract` y un solo bloque de palabras clave. Estas separatas **no** contienen
varios artículos.

> ⚠️ **Pendiente de validación:** estos PDFs son separatas individuales. El PDF
> de un **boletín completo** podría contener varios artículos y requerir lógica
> de segmentación. No se puede confirmar con esta muestra.

### 4.2. La primera página es muy consistente

El encabezado sigue siempre el mismo orden:

```text
<autores-corto> Boletín SAO Vol. <N> - <AÑO>
<tema> (No. ...) – Pag: <X>-<Y>
TÍTULO EN ESPAÑOL (mayúsculas, puede ocupar varias líneas)
TÍTULO EN INGLÉS
Autores (con superíndices de afiliación)
Resumen  → abstract (español)
Palabras clave / Key words → keywords
Abstract → abstract (inglés)
```

### 4.3. Resultado de extracción (6/6)

| Campo              | Resultado | Nota |
|--------------------|-----------|------|
| `volume`           | 6/6 ✅     | Fiable (regex sobre línea de cita) |
| `publication_year` | 6/6 ✅     | Fiable |
| `pages`            | 6/6 ✅     | Fiable |
| `title`            | 6/6 ✅     | Correcto tras mejorar la detección |
| `authors`          | 6/6 ✅     | Legible; separación por autor imperfecta |
| `abstract`         | 6/6 ✅     | 2 con palabras pegadas (ver 4.4) |
| `keywords`         | 6/6 ✅     | Respaldo a `Key words` cuando falta `Palabras clave` |
| `source`           | 6/6 ✅     | Fijo: "Boletín SAO" |
| `doi`, `url`       | 0/6       | No presentes en estas separatas → `null` (no se inventan) |

## 5. Limitaciones conocidas (honestas, no resueltas en V1)

1. **Espacios perdidos en 2 abstracts** (`ElPatodeTorrentes...`): en párrafos
   justificados algunas palabras quedan pegadas. No se re-segmentan porque
   requeriría un diccionario y podría introducir errores inventados. El abstract
   sigue siendo legible.
2. **Acentos en títulos en MAYÚSCULA** (`DISTRIBUCION`, `BUHO`, `RIO`): el PDF
   coloca el acento en una fila aparte que se descarta; recuperarlo de forma
   fiable no es viable. Es cosmético y no afecta identificar el artículo.
3. **Separación autor por autor**: los nombres se extraen juntos y legibles,
   pero no siempre separados individualmente de forma limpia.
4. **DOI/URL ausentes**: estas separatas no los traen. Se dejan en `null`.

Todas las limitaciones son coherentes con la regla de **no inventar datos**.

## 6. Decisión de clasificación/inclusión en el piloto

Los 6 registros se marcan como `PENDIENTE_REVISIÓN` **a propósito**:

* La metadata se extrajo, pero la **relevancia temática** y la **clasificación
  por OFC** no se evalúan automáticamente en V1 (requieren validación de SAO).
* No se excluye ningún artículo automáticamente por falta de DOI, keywords, etc.
  (coherente con `inclusion-exclusion-criteria.md`).

## 7. Respuesta a las preguntas del piloto

| Pregunta | Respuesta |
|----------|-----------|
| ¿Cómo están estructurados los boletines? | Separatas con 1ª página de encabezado muy regular |
| ¿Cuántos artículos por PDF? | 1 PDF = 1 artículo (en separatas) |
| ¿Cómo detectar artículos? | Por marcadores: cita, `Pag:`, `Resumen`, `Palabras clave`, `Abstract` |
| ¿Qué metadata se extrae auto? | Volumen, año, páginas, título, autores, abstract, keywords, source |
| ¿Qué queda faltante? | DOI/URL; espacios en 2 abstracts; acentos en títulos en mayúscula |
| ¿Cuánto trabajo humano real? | Mínimo: revisar relevancia y clasificar OFC. La metadata ya está |
| ¿Se puede automatizar para los 35? | Sí, el pipeline escala; validar antes el formato de un boletín completo |

## 8. Próximos pasos propuestos (NO ejecutados aún)

1. Conseguir un PDF de **boletín completo** y validar si trae varios artículos.
2. Si trae varios: añadir una etapa de **segmentación** de artículos.
3. Procesar un lote mayor y medir tasa de éxito de la extracción.
4. Definir con SAO la metodología de **clasificación OFC** (sigue `PENDING_VALIDATION`).

## 9. Reproducibilidad

```powershell
# Desde la raíz del repo, con el .venv activado:
pip install -r bibliometrics/requirements.txt
python bibliometrics/ingestion/explore_pdfs.py      # exploración
python bibliometrics/ingestion/extract_boletin.py   # extracción → JSON
```

Artefactos del piloto:

* `bibliometrics/ingestion/explore_pdfs.py` — exploración estructural.
* `bibliometrics/preprocessing/text_normalizer.py` — normalización de texto.
* `bibliometrics/ingestion/extract_boletin.py` — extractor a contrato V1.
* `data/interim/piloto_boletines/articulos_piloto.json` — salida (regenerable).
