# Tasks — Clasificación de artículos por OFC (Componente B)

- [x] 1. Catálogo de OFC
  - `bibliometrics/classification/ofc_catalog.json` con los 11 OFC (id, nombre,
    definición, hábitats, aves características, términos clave).
  - _Requisitos: 1.1, 1.3_

- [x] 2. ADR de la decisión de metodología
  - `docs/decisions/ADR-010-clasificacion-ofc.md`: contexto, opciones, decisión
    (reglas-keywords-v1), justificación, consecuencias, estado.
  - _Requisitos: (decisión de diseño)_

- [x] 3. Clasificador por reglas
  - `bibliometrics/classification/ofc_classifier.py`: carga catálogo, normaliza
    texto, clasifica multilabel con evidencia y confianza. `NO_CLASIFICADO` si
    no hay coincidencias.
  - _Requisitos: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3_

- [x] 4. Pruebas unitarias del clasificador
  - Casos: coincidencia simple, multilabel, sin coincidencia, insensibilidad a
    acentos/mayúsculas.
  - _Requisitos: 2.1–2.4, 3.1_

- [x] 5. Pipeline de clasificación del dataset
  - `bibliometrics/pipelines/classify_dataset.py`: dataset procesado →
    clasificado (JSON + CSV) en `data/processed/boletin_sao_clasificado/`, sin
    modificar la entrada; añade evidencia a `notes`.
  - _Requisitos: 4.1, 4.2, 5.1, 5.2, 5.3_

- [x] 6. Corrida y revisión manual sobre los 35 artículos
  - Resultado: 25/35 con ≥1 OFC, 10 NO_CLASIFICADO, 12 multilabel.
  - HALLAZGO (revisión manual): el clasificador acierta en casos claros
    (p. ej. pato de río→OFC-02, reinita en campus→OFC-08), pero genera
    FALSOS POSITIVOS cuando un término del lexicón aparece como mención
    geográfica/de contexto (p. ej. "Caribe", "Andes", "sabana" en un artículo
    de humedales activan OFC-01/06/03 indebidamente). Es la limitación prevista
    en ADR-010. Todo queda en PENDIENTE_REVISIÓN (correcto).
  - MEJORAS PROPUESTAS (tarea 9): umbral de confianza configurable; distinguir
    términos de hábitat (fuertes) de términos geográficos (débiles) en el
    lexicón; depurar términos ambiguos.
  - _Requisitos: 5.1, 5.2_

- [x] 9. (Mejora) Reducir falsos positivos
  - Catálogo v2.0: términos separados en `terminos_fuertes` (hábitat/ecosistema)
    y `terminos_debiles` (geográficos/contexto). Regla: un OFC se asigna solo si
    coincide ≥1 término fuerte; los débiles suman confianza (peso 0.5).
  - Clasificador maneja plurales (sufijo es/s) sin exigirlos en el catálogo.
  - Resultado: multilabel 12→6, OFC-06 (inflado por "Andes") 14→1. Casos antes
    erróneos corregidos (pato cariblanco 4→2 OFC reales; búho campestre pierde
    OFC-08 falso). Tests 8/8 verdes.
  - _Requisitos: 2.1, 3.3, 4.1_

- [x] 7. Exponer distribución por OFC en backend
  - `BibliometriaService` lee el dataset clasificado más reciente y agrega por
    OFC (con nombres del catálogo). `ResumenBibliometrico` añade
    `clasificacion_disponible`, `por_ofc` y `sin_ofc`. Verificado en vivo.
  - _Requisitos: 6.1_

- [x] 8. Mostrar distribución por OFC en el dashboard
  - Gráfico de barras horizontales por OFC en `BibliometriaPage`, con nota de
    "clasificación automática, sujeta a revisión" y nº de artículos sin OFC.
    Typecheck + build de producción OK.
  - _Requisitos: 6.1, 6.2_
