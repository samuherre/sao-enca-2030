"""Property test de la transformación del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 3.3).

Property 2 del design.md — "No-invención de campos ausentes":

    Para todo ``work``, cada campo del contrato que NO esté presente en el
    ``work`` de entrada queda en ``None`` en el ``ArticleRecord`` producido (no
    se sustituye por un valor inventado).

    **Validates: Requirements 3.3**

Enfoque (Testing Strategy del design): se generan ``work``s sintéticos nativos
de la API_OpenAlex (``DEMO_DATA``, datos de prueba, NUNCA presentados como
resultados reales) OMITIENDO aleatoriamente claves opcionales
(``doi``, ``abstract_inverted_index``, ``primary_location``, ``biblio``,
``concepts``/``keywords``, ``language``, ``id``, ``authorships``, ...). Se llama
a ``work_to_record(work)`` y, para cada campo opcional del contrato, se verifica:

    si NINGUNA de las claves/rutas de origen de ese campo está presente en el
    ``work``, el campo del ``ArticleRecord`` producido es ``None`` (no se
    inventa/sustituye un valor).

La verificación es POR CAMPO, no por clave: un campo solo debe quedar en ``None``
cuando ninguna de sus posibles rutas de origen aporta valor, porque la
transformación admite rutas de respaldo (p. ej. ``url`` cae al DOI,
``journal`` cae a ``host_venue``, ``keywords`` acepta ``keywords`` o
``concepts``). Por eso cada campo define el CONJUNTO de rutas que podrían
alimentarlo y la aserción "debe ser None" solo aplica cuando TODAS están
ausentes.

Campos EXCLUIDOS de la aserción "ausente → None" (design.md, enunciado de la
tarea): ``source`` es FIJO ("OpenAlex", no inventado); ``extraction_date`` y
``extraction_method`` son procedencia fijada por el conector; ``article_id`` es
un id interno determinista. ``title``/``authors``/``publication_year`` son
obligatorios y, aunque también quedan en ``None`` si faltan, su comportamiento
de revisión lo cubre otra propiedad; aquí se centran los OPCIONALES del mapeo.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que los demás
# tests de este paquete).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from typing import Any, Callable  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import (  # noqa: E402
    OPENALEX_SOURCE,
    work_to_record,
)

# ---------------------------------------------------------------------------
# Generadores de "piezas" sintéticas (DEMO_DATA) para un ``work`` de la API.
# Cada pieza produce un valor NO vacío/util, de modo que "presente" signifique
# realmente que el campo tiene algo que mapear (y no un vacío que _clean_str
# reduciría a None, lo que confundiría ausencia con presencia-vacía).
# ---------------------------------------------------------------------------

# Texto no vacío (sin espacios al borde que _clean_str recorte a vacío).
_nonempty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=20,
)


@st.composite
def _authorships(draw: st.DrawFn) -> list[dict]:
    """``authorships`` con al menos un ``author.display_name`` utilizable."""
    n = draw(st.integers(min_value=1, max_value=3))
    return [
        {"author": {"display_name": draw(_nonempty_text)}}
        for _ in range(n)
    ]


@st.composite
def _primary_location(draw: st.DrawFn) -> dict:
    """``primary_location`` con subclaves OPCIONALES presentes de forma aleatoria.

    Puede aportar ``landing_page_url`` (→ url), ``source.display_name``
    (→ journal) y ``source.host_organization_name`` (→ publisher). Cada subclave
    aparece o no de forma independiente.
    """
    loc: dict[str, Any] = {}
    if draw(st.booleans()):
        loc["landing_page_url"] = draw(_nonempty_text)
    source: dict[str, Any] = {}
    if draw(st.booleans()):
        source["display_name"] = draw(_nonempty_text)
    if draw(st.booleans()):
        source["host_organization_name"] = draw(_nonempty_text)
    if source:
        loc["source"] = source
    return loc


@st.composite
def _biblio(draw: st.DrawFn) -> dict:
    """``biblio`` con ``volume``/``issue``/``first_page``/``last_page`` opcionales."""
    biblio: dict[str, Any] = {}
    for key in ("volume", "issue", "first_page", "last_page"):
        if draw(st.booleans()):
            biblio[key] = draw(_nonempty_text)
    return biblio


@st.composite
def _inverted_index(draw: st.DrawFn) -> dict:
    """``abstract_inverted_index`` bien formado {palabra: [posiciones]} no vacío."""
    words = draw(st.lists(_nonempty_text, min_size=1, max_size=4, unique=True))
    index: dict[str, list[int]] = {}
    pos = 0
    for word in words:
        index[word] = [pos]
        pos += 1
    return index


@st.composite
def _concept_list(draw: st.DrawFn) -> list[dict]:
    """``concepts``/``keywords`` con al menos un ``display_name`` utilizable."""
    n = draw(st.integers(min_value=1, max_value=3))
    return [{"display_name": draw(_nonempty_text)} for _ in range(n)]


@st.composite
def synthetic_work(draw: st.DrawFn) -> dict[str, Any]:
    """Genera un ``work`` sintético (DEMO_DATA) OMITIENDO claves al azar.

    Cada clave opcional del esquema nativo de OpenAlex aparece o no de forma
    independiente. Cuando aparece, trae un valor utilizable; cuando no, está
    ausente por completo (no una cadena vacía), que es el caso que ejerce la
    no-invención: ausencia → ``None``.
    """
    work: dict[str, Any] = {}

    # Obligatorios: presencia variable (no afecta la aserción de opcionales).
    if draw(st.booleans()):
        work["title"] = draw(_nonempty_text)
    if draw(st.booleans()):
        work["display_name"] = draw(_nonempty_text)
    if draw(st.booleans()):
        work["authorships"] = draw(_authorships())
    if draw(st.booleans()):
        work["publication_year"] = draw(st.integers(min_value=2020, max_value=2030))

    # Opcionales del mapeo.
    if draw(st.booleans()):
        # DOI como URL nativa de OpenAlex (se pela el prefijo en el conector).
        work["doi"] = "https://doi.org/10." + draw(_nonempty_text)
    if draw(st.booleans()):
        work["primary_location"] = draw(_primary_location())
    if draw(st.booleans()):
        work["host_venue"] = {"display_name": draw(_nonempty_text)}
    if draw(st.booleans()):
        work["biblio"] = draw(_biblio())
    if draw(st.booleans()):
        work["abstract_inverted_index"] = draw(_inverted_index())
    if draw(st.booleans()):
        work["keywords"] = draw(_concept_list())
    if draw(st.booleans()):
        work["concepts"] = draw(_concept_list())
    if draw(st.booleans()):
        work["language"] = draw(_nonempty_text)
    if draw(st.booleans()):
        work["id"] = "https://openalex.org/W" + draw(_nonempty_text)

    return work


# ---------------------------------------------------------------------------
# Predicados "este campo del contrato PODRÍA tener un origen presente en el work".
# Si el predicado es False (ninguna ruta de origen presente/utilizable), el campo
# producido DEBE ser None (no-invención). Los predicados reflejan la tabla de
# mapeo del diseño y las rutas de respaldo implementadas en el conector.
# ---------------------------------------------------------------------------


def _has(work: dict, key: str) -> bool:
    return key in work


def _primary_loc(work: dict) -> dict:
    loc = work.get("primary_location")
    return loc if isinstance(loc, dict) else {}


def _loc_source(work: dict) -> dict:
    src = _primary_loc(work).get("source")
    return src if isinstance(src, dict) else {}


def _biblio_has(work: dict, key: str) -> bool:
    biblio = work.get("biblio")
    return isinstance(biblio, dict) and key in biblio


def _source_present_doi(work: dict) -> bool:
    return _has(work, "doi")


def _source_present_url(work: dict) -> bool:
    # url ← primary_location.landing_page_url, o respaldo al DOI.
    return "landing_page_url" in _primary_loc(work) or _has(work, "doi")


def _source_present_journal(work: dict) -> bool:
    # journal ← primary_location.source.display_name, o respaldo host_venue.
    if "display_name" in _loc_source(work):
        return True
    hv = work.get("host_venue")
    return isinstance(hv, dict) and "display_name" in hv


def _source_present_publisher(work: dict) -> bool:
    return "host_organization_name" in _loc_source(work)


def _source_present_volume(work: dict) -> bool:
    return _biblio_has(work, "volume")


def _source_present_issue(work: dict) -> bool:
    return _biblio_has(work, "issue")


def _source_present_pages(work: dict) -> bool:
    return _biblio_has(work, "first_page") or _biblio_has(work, "last_page")


def _source_present_abstract(work: dict) -> bool:
    return _has(work, "abstract_inverted_index")


def _source_present_keywords(work: dict) -> bool:
    return _has(work, "keywords") or _has(work, "concepts")


def _source_present_language(work: dict) -> bool:
    return _has(work, "language")


def _source_present_source_url(work: dict) -> bool:
    return _has(work, "id")


# Campo del contrato → predicado "podría tener origen presente en el work".
OPTIONAL_FIELD_SOURCE_PRESENT: dict[str, Callable[[dict], bool]] = {
    "doi": _source_present_doi,
    "url": _source_present_url,
    "journal": _source_present_journal,
    "publisher": _source_present_publisher,
    "volume": _source_present_volume,
    "issue": _source_present_issue,
    "pages": _source_present_pages,
    "abstract": _source_present_abstract,
    "keywords": _source_present_keywords,
    "language": _source_present_language,
    "source_url": _source_present_source_url,
}


# Feature: fuente-openalex-api, Property 2: No-invención de campos ausentes
@settings(max_examples=200)
@given(work=synthetic_work())
def test_no_invencion_de_campos_ausentes(work: dict[str, Any]) -> None:
    """Un campo opcional sin ninguna ruta de origen presente queda en None.

    Para cada campo opcional del contrato, si NINGUNA de sus rutas de origen
    está presente en el ``work`` de entrada, el campo del ``ArticleRecord``
    producido por ``work_to_record`` debe ser ``None`` (no-invención, Req 3.3).

    **Validates: Requirements 3.3**
    """
    record = work_to_record(work)

    for field, source_present in OPTIONAL_FIELD_SOURCE_PRESENT.items():
        if not source_present(work):
            value = getattr(record, field)
            assert value is None, (
                f"Campo opcional del contrato '{field}' no es None pese a que "
                f"ninguna de sus rutas de origen está presente en el work de "
                f"entrada: {value!r} (no-invención violada). work={work!r}"
            )

    # Invariantes de los campos FIJOS (no provienen del work; nunca None por
    # ausencia). Garantizan que su exclusión de la aserción es correcta.
    assert record.source == OPENALEX_SOURCE == "OpenAlex"
    assert record.extraction_date is not None and record.extraction_date != ""
    assert record.extraction_method is not None
    assert record.article_id is not None and record.article_id.startswith("oa-")
