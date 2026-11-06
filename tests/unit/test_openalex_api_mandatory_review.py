"""Property test de la capa de transformación del Conector_OpenAlex_API (spec
fuente-openalex-api, tarea 3.4).

Property 3 del design.md — "Obligatorio faltante o ambiguo marca revisión":

    Para todo ``work`` al que le falte ``title``, ``authors`` o
    ``publication_year``, o cuyo año no sea interpretable, el conector fija
    ``inclusion_status = "PENDIENTE_REVISIÓN"`` con una nota no vacía, sin
    eliminar el registro (año no detectable → ``publication_year = None`` +
    revisión).

    **Validates: Requirements 3.4, 4.3**

Enfoque (Testing Strategy del design): se generan ``work``s sintéticos nativos
de la API_OpenAlex (``DEMO_DATA``, datos de prueba, NO reales) que omiten de
forma aleatoria ``title``, ``authorships`` (de donde salen los ``authors``) y/o
``publication_year``, o bien entregan un año NO interpretable (texto no numérico
o un dict). Para cada ``work`` se llama ``work_to_record(work)`` y se verifica:

  1. El registro SIEMPRE se produce (no es ``None``): nunca se elimina.
  2. Cuando falta un obligatorio (``title`` / ``authors`` derivados de
     ``authorships`` / ``publication_year``) o el año no es interpretable,
     ``record.inclusion_status == "PENDIENTE_REVISIÓN"`` y ``record.notes`` es un
     string NO vacío (nota explicativa).
  3. Cuando el año es NO interpretable (ambiguo), ``record.publication_year is
     None`` (no se inventa un número; Req 4.3).

Los ``work``s generados por hypothesis son SINTÉTICOS (``DEMO_DATA``) y nunca se
presentan como resultados reales.
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

from typing import Any  # noqa: E402

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.openalex_api_client import work_to_record  # noqa: E402

# Texto no vacío (tras recortar) para poblar campos presentes de forma realista.
_non_empty_text = st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != "")


@st.composite
def _authorship_list(draw: st.DrawFn) -> list[dict]:
    """Genera ``authorships`` sintéticos que SÍ producen autores utilizables.

    Ruta que lee el conector: ``authorships[*]["author"]["display_name"]``.
    """
    n = draw(st.integers(min_value=1, max_value=3))
    return [
        {"author": {"display_name": draw(_non_empty_text)}} for _ in range(n)
    ]


# Años NO interpretables: texto no numérico, un dict, o una lista. El conector
# debe tratarlos como ambiguos (publication_year=None + revisión).
_uninterpretable_year = st.one_of(
    st.text(min_size=1, max_size=8).filter(
        lambda s: s.strip() != "" and not s.strip()[:4].isdigit()
    ),
    st.dictionaries(st.text(max_size=3), st.integers(), min_size=1, max_size=2),
    st.lists(st.integers(), min_size=1, max_size=3),
)


@st.composite
def _work(draw: st.DrawFn) -> tuple[dict, bool]:
    """Genera un ``work`` sintético (DEMO_DATA) y marca si el año es ambiguo.

    Devuelve ``(work, year_is_uninterpretable)``:

    - ``title`` presente o ausente (texto no vacío cuando está).
    - ``authorships`` presentes (producen autores) o ausentes.
    - ``publication_year``: ausente, un año válido en rango, o un valor NO
      interpretable (texto/ dict / lista). Cuando es no interpretable se marca
      ``year_is_uninterpretable = True``.
    """
    work: dict[str, Any] = {}

    if draw(st.booleans()):
        work["title"] = draw(_non_empty_text)
    if draw(st.booleans()):
        work["authorships"] = draw(_authorship_list())

    year_kind = draw(st.sampled_from(["absent", "valid", "uninterpretable"]))
    year_is_uninterpretable = False
    if year_kind == "valid":
        work["publication_year"] = draw(st.integers(min_value=2020, max_value=2030))
    elif year_kind == "uninterpretable":
        work["publication_year"] = draw(_uninterpretable_year)
        year_is_uninterpretable = True
    # "absent": no se añade la clave publication_year.

    return work, year_is_uninterpretable


# Feature: fuente-openalex-api, Property 3: Obligatorio faltante o ambiguo marca revisión
@settings(max_examples=200)
@given(data=_work())
def test_obligatorio_faltante_o_ambiguo_marca_revision(
    data: tuple[dict, bool],
) -> None:
    """Falta de obligatorio o año ambiguo → PENDIENTE_REVISIÓN con nota, sin eliminar.

    Validates: Requirements 3.4, 4.3
    """
    work, year_is_uninterpretable = data

    record = work_to_record(work)

    # (1) El registro SIEMPRE se produce; nunca se elimina.
    assert record is not None, "work_to_record no debe devolver None"

    # ¿Falta algún obligatorio del contrato o el año es ambiguo?
    title_missing = not work.get("title")
    authors_missing = record.authors is None
    year_missing_or_ambiguous = (
        "publication_year" not in work or year_is_uninterpretable
    )
    debe_revisarse = (
        title_missing or authors_missing or year_missing_or_ambiguous
    )

    if debe_revisarse:
        # (2) inclusion_status marcado para revisión y nota NO vacía.
        assert record.inclusion_status == "PENDIENTE_REVISIÓN", (
            "Un obligatorio faltante o un año ambiguo debe marcar "
            f"inclusion_status='PENDIENTE_REVISIÓN'; fue {record.inclusion_status!r}"
        )
        assert isinstance(record.notes, str) and record.notes.strip() != "", (
            "Debe registrarse una nota explicativa no vacía; "
            f"notes={record.notes!r}"
        )

    # (3) Año NO interpretable → publication_year=None (no se inventa; Req 4.3).
    if year_is_uninterpretable:
        assert record.publication_year is None, (
            "Un año no interpretable debe dejar publication_year en None; "
            f"fue {record.publication_year!r}"
        )
