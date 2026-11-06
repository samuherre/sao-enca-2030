"""Property test del Conector_OpenAlex (spec fuente-openalex, tarea 1.5).

Property 4 del design.md — "Obligatorio faltante o ambiguo marca revisión":

    Para todo registro al que le falte ``title``, ``authors`` o
    ``publication_year``, o cuyo año no sea interpretable, el conector fija
    ``inclusion_status = "PENDIENTE_REVISIÓN"`` con una nota NO vacía, sin
    eliminar el registro.

    **Validates: Requirements 2.4, 3.2**

Enfoque (Testing Strategy del design): se generan registros PoP/OpenAlex
SINTÉTICOS (datos de prueba, no reales) en los que SIEMPRE falta al menos un
campo obligatorio (title / authors / year), o bien el año es NO INTERPRETABLE
(texto que no empieza por 4 dígitos). Cada registro se escribe a un
Export_PoP_OpenAlex real (JSON y CSV) y se verifica que ``extract_records``:

  - devuelve el registro (NO lo descarta),
  - con ``inclusion_status == "PENDIENTE_REVISIÓN"``,
  - y una ``notes`` no vacía.

Caso específico de Req 3.2 (año faltante o no detectable): además de marcar
revisión con nota, ``publication_year`` debe quedar en ``None`` (no se inventa).

El conector de OpenAlex acepta varias claves candidatas por campo obligatorio
(``authors``/``author`` para autores; ``year``/``publication_year`` para el
año); por eso el generador puede omitir TODAS las variantes de un obligatorio
para forzar la condición de revisión.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que el resto
# de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import extract_records  # noqa: E402

# Claves candidatas por campo OBLIGATORIO del contrato V1 en OpenAlex.
# El conector prueba varias; para forzar "faltante" hay que omitirlas todas.
_TITLE_KEYS = ("title",)
_AUTHORS_KEYS = ("authors", "author")
_YEAR_KEYS = ("year", "publication_year")

# Todas las claves de obligatorios (para la cabecera CSV).
_REQUIRED_POP_KEYS = _TITLE_KEYS + _AUTHORS_KEYS + _YEAR_KEYS

# Claves opcionales que pueden aparecer como ruido sin afectar la propiedad.
_OPTIONAL_POP_KEYS = (
    "doi",
    "url",
    "article_url",
    "id",
    "source",       # -> journal
    "host_venue",
    "venue",
    "publisher",
    "volume",
    "issue",
    "pages",
    "abstract",
    "description",
    "keywords",
    "concepts",
    "language",
    "cites_url",
)

# Texto no vacío plausible para valores presentes (sin bordes que _clean_str
# recorte a vacío). Excluye sustitutos y controles.
_non_empty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=20,
)

# Valor de año NO INTERPRETABLE: presente pero sin 4 dígitos al inicio (p. ej.
# "N/A", "veinte", "mil"). Se excluye todo lo que _parse_year sí interpretaría.
_ambiguous_year = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc", "Nd"), min_codepoint=33),
    min_size=1,
    max_size=10,
).filter(lambda s: s.strip() != "" and not s.strip()[:4].isdigit())


@st.composite
def pop_openalex_records_que_requieren_revision(draw: st.DrawFn) -> dict[str, str]:
    """Genera un registro PoP/OpenAlex que DEBE caer en PENDIENTE_REVISIÓN.

    Garantiza que al menos un obligatorio esté ausente (todas sus variantes de
    clave omitidas) o que el año sea no interpretable. Estrategia:

    1. Año: FALTANTE, NO INTERPRETABLE o VÁLIDO (numérico de 4 dígitos).
    2. title y authors: presentes o ausentes de forma independiente.
    3. Si por azar el registro quedó completo y con año válido, se FUERZA la
       condición rompiendo un obligatorio o volviendo el año no interpretable.
    4. Se añaden claves opcionales aleatorias (ruido) que no deben afectar.
    """
    record: dict[str, str] = {}

    # --- Año: faltante / no interpretable / válido ---
    year_mode = draw(st.sampled_from(["missing", "ambiguous", "valid"]))
    if year_mode == "ambiguous":
        record[draw(st.sampled_from(_YEAR_KEYS))] = draw(_ambiguous_year)
    elif year_mode == "valid":
        record[draw(st.sampled_from(_YEAR_KEYS))] = str(
            draw(st.integers(min_value=2020, max_value=2030))
        )
    # "missing" → no se añade ninguna clave de año.

    # --- title / authors: presentes o ausentes ---
    title_present = draw(st.booleans())
    authors_present = draw(st.booleans())
    if title_present:
        record["title"] = draw(_non_empty_text)
    if authors_present:
        record[draw(st.sampled_from(_AUTHORS_KEYS))] = draw(_non_empty_text)

    # --- Forzar que el registro requiera revisión ---
    year_ok = year_mode == "valid"
    if title_present and authors_present and year_ok:
        broken = draw(st.sampled_from(["title", "authors", "year"]))
        if broken == "title":
            for k in _TITLE_KEYS:
                record.pop(k, None)
        elif broken == "authors":
            for k in _AUTHORS_KEYS:
                record.pop(k, None)
        else:  # year → no interpretable
            for k in _YEAR_KEYS:
                record.pop(k, None)
            record[draw(st.sampled_from(_YEAR_KEYS))] = draw(_ambiguous_year)

    # --- Ruido: claves opcionales aleatorias (no deben afectar la propiedad) ---
    optional_present = draw(
        st.lists(
            st.sampled_from(_OPTIONAL_POP_KEYS),
            unique=True,
            min_size=0,
            max_size=len(_OPTIONAL_POP_KEYS),
        )
    )
    for key in optional_present:
        record[key] = draw(_non_empty_text)

    return record


def _year_is_missing_or_ambiguous(raw: dict[str, str]) -> bool:
    """True si el año está ausente o no es interpretable (Req 3.2)."""
    value = None
    for k in _YEAR_KEYS:
        if k in raw:
            value = raw[k]
            break
    if value is None:
        return True
    s = str(value).strip()
    if s == "":
        return True
    if s.isdigit():
        return False
    if len(s) >= 4 and s[:4].isdigit():
        return False
    return True


# Feature: fuente-openalex, Property 4: Obligatorio faltante o ambiguo marca revisión
@settings(
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(raw=pop_openalex_records_que_requieren_revision())
def test_obligatorio_faltante_o_ambiguo_marca_revision(raw: dict[str, str]) -> None:
    """Obligatorio faltante/ambiguo → PENDIENTE_REVISIÓN + nota, sin eliminar.

    Se escribe el registro a un Export_PoP_OpenAlex real (JSON y CSV) y se
    verifica, vía ``extract_records``, que el registro se conserva (no se
    descarta), queda marcado para revisión y con una nota no vacía. Esto cubre
    la cláusula "sin eliminar el registro" de la Property 4.

    **Validates: Requirements 2.4, 3.2**
    """
    year_missing_or_ambiguous = _year_is_missing_or_ambiguous(raw)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # --- JSON: lista con un único objeto-registro ---
        json_file = tmp_path / "export.json"
        json_file.write_text(json.dumps([raw]), encoding="utf-8")
        json_records = extract_records(json_file)
        assert len(json_records) == 1, (
            f"El registro no debe eliminarse (JSON); entrada={raw!r}"
        )
        assert json_records[0].inclusion_status == "PENDIENTE_REVISIÓN", (
            f"Se esperaba PENDIENTE_REVISIÓN (JSON); entrada={raw!r}"
        )
        assert json_records[0].notes and json_records[0].notes.strip() != "", (
            f"Se esperaba una nota no vacía (JSON); entrada={raw!r}, "
            f"notes={json_records[0].notes!r}"
        )
        if year_missing_or_ambiguous:
            assert json_records[0].publication_year is None, (
                "Año faltante/no interpretable debe dejar publication_year en "
                f"None (sin inventar); entrada={raw!r}"
            )

        # --- CSV: cabecera con TODAS las claves posibles; valores vacíos para
        #     las ausentes (equivalen a ausencia según _clean_str del conector).
        csv_file = tmp_path / "export.csv"
        all_keys = list(_REQUIRED_POP_KEYS) + list(_OPTIONAL_POP_KEYS)
        with csv_file.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_keys)
            writer.writeheader()
            writer.writerow({k: raw.get(k, "") for k in all_keys})
        csv_records = extract_records(csv_file)
        assert len(csv_records) == 1, (
            f"El registro no debe eliminarse (CSV); entrada={raw!r}"
        )
        assert csv_records[0].inclusion_status == "PENDIENTE_REVISIÓN", (
            f"Se esperaba PENDIENTE_REVISIÓN (CSV); entrada={raw!r}"
        )
        assert csv_records[0].notes and csv_records[0].notes.strip() != "", (
            f"Se esperaba una nota no vacía (CSV); entrada={raw!r}, "
            f"notes={csv_records[0].notes!r}"
        )
