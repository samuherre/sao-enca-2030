"""
extract_openalex.py — Conector de OpenAlex (Publish or Perish → contrato V1).

OBJETIVO:
  Tomar un archivo exportado por Publish or Perish (PoP) desde la fuente
  OpenAlex —en formato JSON (lista de objetos) o CSV (filas con columnas)— y
  producir registros conforme al Article Data Contract V1 (``ArticleRecord``).

Es un ESPEJO DELIBERADO de ``extract_scholar.py`` (ambas fuentes son exports de
la misma herramienta, PoP). Se mantienen idénticos el patrón de detección de
formato, los lectores tolerantes a BOM y JSON anidado, y la construcción del
registro. Difieren solo:
  - la fuente fija (``"OpenAlex"``),
  - el método de extracción,
  - el prefijo del ``article_id`` (``oa-``),
  - los matices de mapeo propios del export de OpenAlex.

REGLA FUNDAMENTAL (no inventar — steering Componente B §4):
  - Lo que se detecta se rellena; lo que NO se detecta queda en ``None``.
  - ``source`` SIEMPRE es ``"OpenAlex"`` (fuente de ingesta fija). Nunca Google
    Scholar ni otra fuente.
  - La columna/clave PoP ``Source`` (o los campos propios de OpenAlex
    ``host_venue`` / ``venue``) representa la REVISTA/medio del artículo, por eso
    se mapea a ``journal`` (no al campo ``source`` del contrato).
  - Si falta un campo OBLIGATORIO del contrato (title, authors,
    publication_year) o su detección es ambigua, ``inclusion_status`` pasa a
    ``"PENDIENTE_REVISIÓN"`` con una nota explicativa en ``notes``.
  - Año fuera del periodo 2020–2030 → ``PENDIENTE_REVISIÓN`` con nota, SIN
    descartar el registro.

PROCEDENCIA (Req 7.3):
  OpenAlex identifica cada work con una URL propia en el campo ``id`` (p. ej.
  ``https://openalex.org/Wxxxxxxxxx``). Cuando exista, se preserva en
  ``source_url``. Si no está, se deja ``None`` sin inventarlo.

MAPEO FINO ``PENDING_VALIDATION``:
  No se dispone todavía de un Export_PoP_OpenAlex real de muestra en el
  repositorio. La tabla de claves candidatas es la PROPUESTA del diseño basada
  en las columnas típicas de PoP y en campos propios de OpenAlex. No se inventan
  claves que no aparezcan: un campo sin clave candidata presente queda ``None``.

ALCANCE V1:
  - Parseo de un único archivo Export_PoP_OpenAlex (``extract_records``).
  - Detección de formato por extensión (``detect_format``).
  - El recorrido de la carpeta, el logging por archivo+posición, el marcado de
    duplicados y la escritura de salidas corresponden al PIPELINE
    (``process_openalex.py``), no a este módulo.

NOTA SOBRE REGISTROS MALFORMADOS:
  Dentro de ``extract_records`` un registro individual que no pueda parsearse se
  descarta de forma robusta (no detiene el lote). El pipeline añade el logging
  detallado con archivo + posición.
"""

from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

# Permite ejecutar/importar tanto como módulo (``bibliometrics.ingestion...``)
# como por ruta relativa al repo, igual que ``extract_scholar.py``.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

# Contrato de datos compartido (Article Data Contract V1).
from ingestion.article_record import ArticleRecord  # noqa: E402

# Normalizador de título: reutilizamos el helper de pipeline para que el
# article_id y la futura deduplicación compartan la MISMA normalización.
from pipelines._common import norm_title  # noqa: E402

# Fuente de ingesta fija y método de extracción de esta fuente (Req 2.1, 2.2).
OPENALEX_SOURCE = "OpenAlex"
OPENALEX_EXTRACTION_METHOD = "Publish or Perish export (OpenAlex) V1"

# Periodo de inclusión V1 (steering Componente B §2). La validación de período
# también la aplica el pipeline vía ``_common.validate_period``; aquí dejamos la
# constancia a nivel de conector para cumplir Req 3.1 desde la extracción.
PERIODO_MIN, PERIODO_MAX = 2020, 2030

# --- Mapeo PoP/OpenAlex → contrato V1 ----------------------------------------
# Para cada campo del contrato se lista una o varias claves candidatas. Se busca
# de forma case-insensitive sobre las claves del registro de entrada, probando
# en orden; la primera que exista (con valor no vacío) gana. Esto cubre tanto el
# JSON (claves tipo ``title``, ``author``, ``concepts``, ``host_venue``) como el
# CSV que PoP produce (columnas ``Title``, ``Authors``, ``Source``) sin mantener
# dos tablas separadas.
#
# PENDING_VALIDATION del mapeo fino: la tabla es la propuesta del diseño basada
# en columnas típicas de PoP y campos propios de OpenAlex; se confirmará con un
# Export_PoP_OpenAlex real. No se inventan claves que no aparezcan.
#
# Campos del contrato que NO provienen del export (source, extraction_date,
# extraction_method, article_id) se fijan aparte.
FIELD_CANDIDATES: dict[str, tuple[str, ...]] = {
    "title": ("title",),
    "authors": ("authors", "author"),
    "publication_year": ("year", "publication_year"),
    "doi": ("doi",),
    # OpenAlex usa ``id`` como URL del work; se acepta como último candidato de
    # ``url`` tras las columnas PoP habituales.
    "url": ("article_url", "url", "id"),
    # PoP 'Source' = revista/medio; OpenAlex expone host_venue / venue.
    "journal": ("source", "host_venue", "venue"),
    "publisher": ("publisher",),
    "volume": ("volume",),
    "issue": ("issue",),
    "pages": ("pages",),
    "abstract": ("abstract", "description"),
    # OpenAlex expone ``concepts``; PoP/CSV pueden traer ``keywords``.
    "keywords": ("keywords", "concepts"),
    "language": ("language",),
    # Procedencia propia de OpenAlex: su URL/ID del work (campo ``id``). Se
    # prueban variantes; ``url`` queda al final para no pisar la detección de
    # ``url`` de arriba cuando exista un id propio.
    "source_url": ("id", "cites_url", "url"),
}


def detect_format(path: Path) -> str:
    """Devuelve ``"json"`` o ``"csv"`` según la extensión (case-insensitive).

    :param path: Ruta del archivo de Export_PoP_OpenAlex.
    :raises ValueError: si la extensión no es ``.json`` ni ``.csv``.
    """
    ext = Path(path).suffix.lower()
    if ext == ".json":
        return "json"
    if ext == ".csv":
        return "csv"
    raise ValueError(
        f"Extensión no soportada: '{Path(path).suffix}'. Use .json o .csv."
    )


def _hash12(text: str) -> str:
    """Primeros 12 caracteres hex del SHA-256 de ``text`` (determinista)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _norm_doi(doi: str) -> str:
    """Normaliza un DOI para el hash: minúsculas y sin espacios alrededor.

    Se mantiene conservador (no reescribe el DOI del registro, solo deriva una
    clave estable para el identificador interno).
    """
    return doi.strip().lower()


def _make_article_id(doi: Optional[str], title: Optional[str], year: Optional[int]) -> str:
    """Identificador interno determinista para OpenAlex (Req 2.6).

    - Con DOI: ``oa-<hash12(doi normalizado)>``.
    - Sin DOI: ``oa-<hash12(título normalizado + "|" + año)>``.

    El prefijo ``oa-`` distingue OpenAlex del ``gs-`` de Google Scholar y evita
    colisiones de ``article_id`` entre fuentes. No inventa un dato del artículo:
    deriva un id interno estable y reproducible entre corridas. Si no hay ni DOI
    ni título/año utilizables, el hash se calcula sobre la cadena disponible
    (p. ej. ``"|"``), manteniendo determinismo.
    """
    if doi:
        return "oa-" + _hash12(_norm_doi(doi))
    base = f"{norm_title(title)}|{year if year is not None else ''}"
    return "oa-" + _hash12(base)


def _lower_key_map(raw: dict[str, Any]) -> dict[str, Any]:
    """Mapa de claves en minúscula → valor, para búsqueda case-insensitive.

    Si hay colisión de claves al bajar a minúsculas (poco habitual en exports
    reales), gana la primera encontrada.
    """
    result: dict[str, Any] = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        lk = k.strip().lower()
        if lk not in result:
            result[lk] = v
    return result


def _clean_str(value: Any) -> Optional[str]:
    """Normaliza un valor a texto no vacío o ``None`` (sin inventar).

    OpenAlex puede exponer campos como listas (p. ej. ``concepts``) o como
    objetos anidados. Se aplanan de forma conservadora a texto legible sin
    inventar contenido: listas → elementos unidos por ``;``; dicts → el primer
    valor de texto plausible (``display_name`` / ``name`` / ``value``) o su
    representación. Si tras aplanar queda vacío → ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, (list, tuple)):
        parts = [_clean_str(item) for item in value]
        parts = [p for p in parts if p]
        return "; ".join(parts) or None
    if isinstance(value, dict):
        for key in ("display_name", "name", "value", "title"):
            if key in value:
                cleaned = _clean_str(value[key])
                if cleaned is not None:
                    return cleaned
        return None
    # Numéricos / booleanos u otros escalares: representación textual directa.
    s = str(value).strip()
    return s or None


def _pick(lower_map: dict[str, Any], candidates: tuple[str, ...]) -> Optional[str]:
    """Primera clave candidata presente con valor no vacío; si no, ``None``."""
    for cand in candidates:
        if cand in lower_map:
            cleaned = _clean_str(lower_map[cand])
            if cleaned is not None:
                return cleaned
    return None


def _parse_year(value: Optional[str]) -> tuple[Optional[int], bool]:
    """Convierte el valor de año a ``int`` cuando sea posible.

    Devuelve ``(year, ambiguo)``. ``ambiguo`` es ``True`` si había un valor
    presente pero no se pudo interpretar como un año entero (p. ej. texto),
    para marcar revisión sin inventar un número.
    """
    if value is None:
        return None, False
    s = value.strip()
    if s.isdigit():
        return int(s), False
    # Algunos exports traen el año embebido (p. ej. "2021-05"). Tomamos los
    # primeros 4 dígitos solo si forman un año plausible de 4 cifras al inicio.
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4]), False
    # Valor presente pero no interpretable como año → ambiguo (no inventar).
    return None, True


def _record_from_mapping(raw: dict[str, Any]) -> ArticleRecord:
    """Construye un ``ArticleRecord`` (contrato V1) desde un registro PoP/OpenAlex.

    Aplica el mapeo PoP/OpenAlex → contrato, la regla de no-invención (campo
    ausente → ``None``), la marca de obligatorios faltantes/ambiguos y la
    validación de período 2020–2030. ``source`` se fija a ``"OpenAlex"``.
    """
    lower_map = _lower_key_map(raw)

    values: dict[str, Optional[str]] = {
        field: _pick(lower_map, candidates)
        for field, candidates in FIELD_CANDIDATES.items()
    }

    # Año: conversión explícita a int (los demás campos quedan como texto o None).
    year, year_ambiguo = _parse_year(values["publication_year"])

    # --- Reglas de inclusión / notas (no inventar) ---------------------------
    notes_parts: list[str] = []
    missing_required: list[str] = []
    if not values["title"]:
        missing_required.append("title")
    if not values["authors"]:
        missing_required.append("authors")
    if year is None:
        missing_required.append("publication_year")

    inclusion = "PENDIENTE_REVISIÓN"  # estado base del contrato V1

    if missing_required:
        notes_parts.append(
            "Faltan campos obligatorios: " + ", ".join(missing_required)
        )
    if year_ambiguo:
        notes_parts.append(
            f"Año no interpretable ('{values['publication_year']}'); requiere revisión."
        )

    # Validación de período (Req 3.1): fuera de rango → PENDIENTE_REVISIÓN + nota,
    # sin descartar. Solo aplica si hay un año interpretable.
    if year is not None and not (PERIODO_MIN <= year <= PERIODO_MAX):
        notes_parts.append(
            f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."
        )

    if not notes_parts:
        # Metadata obligatoria completa y año en rango. Relevancia temática y OFC
        # NO se evalúan automáticamente en V1 → sigue en revisión.
        notes_parts.append(
            "Metadata extraída; pendiente de revisión de relevancia y clasificación OFC."
        )

    article_id = _make_article_id(values["doi"], values["title"], year)

    return ArticleRecord(
        article_id=article_id,
        title=values["title"],
        doi=values["doi"],
        url=values["url"],
        authors=values["authors"],
        publication_year=year,
        journal=values["journal"],
        volume=values["volume"],
        issue=values["issue"],
        pages=values["pages"],
        publisher=values["publisher"],
        language=values["language"],
        abstract=values["abstract"],
        keywords=values["keywords"],
        source=OPENALEX_SOURCE,
        source_url=values["source_url"],
        extraction_date=_dt.date.today().isoformat(),
        extraction_method=OPENALEX_EXTRACTION_METHOD,
        inclusion_status=inclusion,
        notes=" | ".join(notes_parts),
    )


def _iter_json_records(input_path: Path) -> list[dict[str, Any]]:
    """Lee un Export_PoP_OpenAlex JSON y devuelve la lista de objetos-registro.

    PoP exporta una lista de objetos. Se aceptan también variantes comunes donde
    los registros vienen anidados bajo una clave contenedora (``data`` /
    ``results`` / ``records`` / ``items``) —OpenAlex usa típicamente
    ``results``—. Cualquier elemento que no sea un objeto se ignora en
    ``extract_records`` (registro malformado).

    Se usa ``utf-8-sig`` para tolerar el BOM UTF-8 que Publish or Perish añade
    a los exports JSON en Windows (igual que ya se hace para el CSV).
    """
    text = input_path.read_text(encoding="utf-8-sig")
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "records", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        # Un único objeto-registro suelto.
        return [data]
    return []


def _iter_csv_records(input_path: Path) -> list[dict[str, Any]]:
    """Lee un Export_PoP_OpenAlex CSV y devuelve filas como diccionarios."""
    # utf-8-sig tolera el BOM que suelen traer los CSV de PoP en Windows.
    with input_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def extract_records(input_path: Path) -> list[ArticleRecord]:
    """Parsea un Export_PoP_OpenAlex (JSON o CSV) y devuelve registros V1.

    - ``source`` fijo = ``"OpenAlex"``.
    - Campo no detectado → ``None`` (no se inventa).
    - Obligatorio faltante/ambiguo → ``inclusion_status = "PENDIENTE_REVISIÓN"``
      con nota.
    - Un registro individual malformado se descarta de forma robusta y no
      detiene el procesamiento del resto (el pipeline registra archivo+posición).

    :param input_path: Ruta a un archivo ``.json`` o ``.csv`` de
        Export_PoP_OpenAlex.
    :raises ValueError: si la extensión no es soportada (vía ``detect_format``).
    """
    input_path = Path(input_path)
    fmt = detect_format(input_path)

    if fmt == "json":
        raw_records = _iter_json_records(input_path)
    else:
        raw_records = _iter_csv_records(input_path)

    records: list[ArticleRecord] = []
    for raw in raw_records:
        # Registro malformado = no es un objeto clave→valor. Se descarta sin
        # abortar el lote (robustez; el pipeline añade el log de posición).
        if not isinstance(raw, dict):
            continue
        try:
            records.append(_record_from_mapping(raw))
        except Exception:  # noqa: BLE001 — un registro roto no debe tumbar el lote
            continue

    return records
