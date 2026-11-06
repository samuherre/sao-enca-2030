"""Property test del conector OpenAlex — detección de formato por extensión.

Spec: fuente-openalex, tarea 1.2.
Función bajo prueba: ``detect_format(path)`` de
``bibliometrics/ingestion/extract_openalex.py``.

Property 1 (design.md): Para todo nombre de archivo cuya extensión sea ``.json``
o ``.csv`` en cualquier combinación de mayúsculas/minúsculas, ``detect_format``
devuelve ``"json"`` o ``"csv"`` respectivamente, independiente del casing.

Datos de prueba sintéticos (no reales): nombres base y variaciones de casing de
la extensión se generan con hypothesis. No se tocan archivos del disco; la
detección es puramente por la extensión de la ruta.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el conector desde bibliometrics/ (mismo patrón que el resto
# de pruebas unitarias que ejercen módulos del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

import pytest  # noqa: E402
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import detect_format  # noqa: E402


def _case_variations(ext_letters: str) -> st.SearchStrategy[str]:
    """Genera la extensión (sin el punto) con casing arbitrario por carácter.

    Para ``"json"`` produce p. ej. ``"JSON"``, ``"Json"``, ``"jSoN"``, etc.,
    cubriendo todas las combinaciones de mayúsculas/minúsculas.
    """
    char_strategies = [st.sampled_from([c.lower(), c.upper()]) for c in ext_letters]
    return st.tuples(*char_strategies).map("".join)


# Nombres base plausibles de archivo: evitan separadores de ruta, el punto y los
# caracteres nulos para que ``suffix`` corresponda exactamente a la extensión
# generada. Se exige al menos un carácter de "stem" porque un nombre como
# ``.csv`` (sin stem) es un dotfile sin extensión según ``pathlib`` (suffix
# vacío) y no representa un archivo con extensión ``.json``/``.csv``, que es el
# dominio de la propiedad (Req 1.2/1.3).
_base_names = st.text(
    alphabet=st.characters(
        blacklist_characters="./\\\x00",
        blacklist_categories=("Cs", "Cc"),
    ),
    min_size=1,
    max_size=40,
).filter(lambda s: s.strip() != "" and not s.endswith("."))


# Feature: fuente-openalex, Property 1: Detección de formato por extensión (case-insensitive)
@settings(max_examples=300)
@given(
    base=_base_names,
    fmt=st.sampled_from(["json", "csv"]),
    data=st.data(),
)
def test_detect_format_case_insensitive(base: str, fmt: str, data: st.DataObject) -> None:
    """``detect_format`` devuelve el formato en minúsculas sin importar el casing.

    **Validates: Requirements 1.2, 1.3**
    """
    ext = data.draw(_case_variations(fmt))
    path = Path(f"{base}.{ext}")

    result = detect_format(path)

    assert result == fmt


# Verificación complementaria (no es la propiedad núcleo): una extensión no
# soportada debe producir ValueError (Error Handling del diseño, Req 1.2/1.3).
_unsupported_ext = st.text(
    alphabet=st.characters(
        blacklist_characters="./\\\x00",
        blacklist_categories=("Cs", "Cc"),
    ),
    min_size=1,
    max_size=6,
).filter(lambda e: e.lower() not in {"json", "csv"})


@settings(max_examples=100)
@given(base=_base_names, ext=_unsupported_ext)
def test_detect_format_extension_no_soportada_valueerror(base: str, ext: str) -> None:
    """Una extensión distinta de .json/.csv levanta ValueError."""
    path = Path(f"{base}.{ext}")
    with pytest.raises(ValueError):
        detect_format(path)
