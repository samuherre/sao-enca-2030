# Tasks — Ingesta de la fuente Boletín SAO (Componente B)

> Estado: el pipeline V1 está implementado y probado con 35 PDFs reales. Las
> tareas marcadas `[x]` están hechas; las `[ ]` son mejoras futuras.

- [x] 1. Preparar entorno y dependencias
  - Instalar `pdfplumber` y fijarlo en `bibliometrics/requirements.txt`.
  - _Requisitos: 1_

- [x] 2. Normalizador de texto
  - Implementar `preprocessing/text_normalizer.py` (tildes, ñ, i sin punto,
    espacios).
  - _Requisitos: 2.3_

- [x] 3. Exploración estructural de los PDFs
  - `ingestion/explore_pdfs.py`: páginas, pistas estructurales, 1 PDF = 1
    artículo.
  - _Requisitos: 1.2_

- [x] 4. Extractor por PDF al contrato V1
  - `ingestion/extract_boletin.py`: volumen/año/páginas, título/autores,
    abstract/keywords; `null` cuando no se detecta; `PENDIENTE_REVISIÓN` ante
    faltantes/ambigüedad.
  - _Requisitos: 2.1, 2.2, 2.4_

- [x] 5. Orquestador en lote
  - `pipelines/process_boletin_sao.py`: recorrido de carpeta, validación de
    periodo, dedupe por título, salida JSON + CSV, resumen de completitud,
    tolerancia a PDFs con error.
  - _Requisitos: 1.1, 1.3, 1.4, 3.1, 4.1, 5.1, 5.2, 5.3_

- [x] 6. Procesar los 35 PDFs reales y verificar
  - Corrida completa; completitud: año 100%, autores 97%, abstract 97%,
    keywords 100%, título 94%. Casos atípicos en `PENDIENTE_REVISIÓN`.
  - _Requisitos: 5.1, 5.2_

- [x] 7. Documentar hallazgos
  - `docs/bibliometrics/pilot-pdf-extraction-findings.md`.
  - _Requisitos: 6_

- [x] 8. (Mejora) Recuperar casos atípicos de encabezado
  - Título ahora 100% (35/35). Se manejan nombres científicos partidos en el
    título y boletines con orden invertido (inglés primero) o sin la palabra
    "Resumen" (se corta también en "Abstract"). Los 2 casos irreductibles del
    Vol. 35 dejan `authors = null` + `PENDIENTE_REVISIÓN` en vez de valor sucio.
  - _Requisitos: 2.1, 2.4_

- [x] 9. (Mejora) Separación de autores individuales
  - Dividir la cadena de autores en lista limpia por autor. Implementado como
    `split_authors()` en `extract_boletin.py` (CONSERVADOR, principio de no
    invención): divide SOLO por separadores explícitos (coma, `;`, `&`, ` y `,
    ` e `, ` and `). Si no hay separador explícito y aparentan varios autores
    pegados por espacios, NO se parten nombres: se deja la cadena completa como
    único elemento y se añade nota de "separación incierta" (PENDIENTE_REVISIÓN).
  - Nuevo campo opcional `authors_list: list` en el contrato `ArticleRecord`
    (conserva `authors` como cadena); se expone en el JSON y en el CSV (columna
    unida por "; "). Corrida real sobre 35 PDFs: 24/33 separados en >=2 autores,
    3 marcados inciertos, resto autores únicos. 9 tests unitarios
    (`tests/unit/test_split_authors.py`), suite completa verde (237 passed).
  - _Requisitos: 2.1_

- [ ] 10. (Mejora, PENDING_VALIDATION — BLOQUEADA) Enriquecer con código SAO `BSAAAA-NN`
  - OBJETIVO: capturar/registrar el código de artículo de SAO como identificador
    de procedencia cuando esté disponible.
  - HALLAZGO (verificado sobre los 8 PDFs reales, 2026-10-30): el código
    `BSAAAA-NN` que menciona el steering (`bibliometrics.md` §3) **NO aparece**
    en los PDFs. En la primera página solo hay: encabezado de volumen/año
    (`Boletín SAO Vol. 29 - 2020`), número de artículo (`No. 1 & 2`), páginas e
    `ISSN: 0123-9082` (común a todos los artículos). Búsqueda ampliada en TODAS
    las páginas con varios patrones: 0 coincidencias de un código tipo
    `BS2020-01`.
  - DECISIÓN: NO implementar. Capturar un código que no existe en los datos sería
    inventar un identificador (viola el principio de no invención,
    `product.md` §15 / `bibliometrics.md` §4.1). Queda BLOQUEADA hasta que SAO
    aclare: (a) qué es exactamente el código `BSAAAA-NN`, (b) su formato exacto,
    y (c) de dónde se obtiene (p. ej. del sitio del boletín o de un índice
    editorial, NO del texto del PDF). 
  - ALTERNATIVA DISPONIBLE (propuesta a validar, no implementada): si SAO lo
    aprueba, podría registrarse como procedencia el identificador que SÍ existe
    en el PDF — volumen + año + número de artículo —, que no es el `BSAAAA-NN`.
  - _Requisitos: 2.1, 6_

- [ ] 11. (Futuro) Interfaz común de conector de fuente
  - Extraer una interfaz mínima que las demás fuentes (Scopus, UNAL, Wiley,
    Scholar) implementen, produciendo el mismo contrato V1.
  - _Requisitos: 6.1, 6.2_
