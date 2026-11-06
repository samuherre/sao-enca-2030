"""Property test del pipeline OpenAlex (spec fuente-openalex, tarea 2.5).

Property 10 del design.md — "Deduplicación básica dentro de la fuente":

    Para todo dataset de OpenAlex, dos registros con el mismo título
    normalizado hacen que el segundo quede marcado ``is_duplicate = true`` con
    ``duplicate_of`` apuntando al primero, sin eliminar ningún registro.

    **Validates: Requirements 4.1**

Enfoque (Testing Strategy del design): se ejercita el MISMO camino que recorre
el pipeline ``process_openalex.py`` tras descubrir un archivo de entrada:

    archivo de Export_PoP_OpenAlex (.json)
        -> ingestion.extract_openalex.extract_records  (conector)
        -> pipelines._common.mark_duplicates            (dedupe por título)

Es decir, se generan registros PoP/OpenAlex SINTÉTICOS (datos de prueba, no
reales; subconjuntos con/sin DOI, años variados y, crucialmente, grupos de
títulos que normalizan a la MISMA clave mediante variantes de casing, acentos y
espaciado), se escriben a un archivo ``.json`` temporal, se extraen con el
conector y se marcan los duplicados tal como lo hace el pipeline.

Para que la aserción "el segundo apunta al primero" sea significativa, cada
registro sintético lleva un DOI ÚNICO: así el conector deriva un ``article_id``
determinista DISTINTO por registro (``oa-<hash12(doi)>``), aunque sus títulos
compartan la misma clave normalizada. De ese modo ``duplicate_of`` del segundo
referencia el ``article_id`` del primero (y no un id idéntico).

Aserciones:
  - No se elimina ningún registro (el conteo se conserva; ``mark_duplicates``
    opera in place sobre la lista extraída).
  - Para cada grupo que comparte clave normalizada no vacía: la PRIMERA
    aparición no es duplicado y cada aparición posterior tiene
    ``is_duplicate == True`` y ``duplicate_of == article_id`` del primero.
  - Los registros cuyo título normaliza a clave vacía no se marcan
    (``is_duplicate == False``, ``duplicate_of is None``).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Permite importar el conector y los helpers desde bibliometrics/ (mismo patrón
# que el resto de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.extract_openalex import extract_records  # noqa: E402
from pipelines._common import mark_duplicates, norm_title  # noqa: E402

# --- Generación de títulos base y de variantes que normalizan a la misma clave --

# Un título base con letras ASCII y espacios: garantiza que su clave normalizada
# NO sea vacía (contiene al menos un alfanumérico).
_base_title = st.text(
    alphabet=st.sampled_from(list("abcdefghijklmnopqrstuvwxyz0123456789")),
    min_size=1,
    max_size=12,
).map(lambda s: " ".join(s))  # separa en "palabras" de un carácter

# Reemplazos de acentos: cada forma acentuada normaliza (NFKD + quita combining)
# a su letra base, de modo que la clave de norm_title no cambia.
_ACCENT_MAP = {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "n": "ñ"}


@st.composite
def title_variant(draw: st.DrawFn, base: str) -> str:
    """Devuelve una variante del título base que normaliza a la MISMA clave.

    Aplica, de forma aleatoria e independiente por carácter/espacio:
      - cambios de casing (mayúsculas/minúsculas),
      - sustitución de vocales/ñ por su versión acentuada,
      - expansión de los espacios a espaciado múltiple,
    además de posible relleno con separadores en los bordes. Todas estas
    transformaciones son absorbidas por ``norm_title``.
    """
    out_chars: list[str] = []
    for ch in base:
        if ch == " ":
            out_chars.append(" " * draw(st.integers(min_value=1, max_value=3)))
            continue
        c = ch
        if c in _ACCENT_MAP and draw(st.booleans()):
            c = _ACCENT_MAP[c]
        if draw(st.booleans()):
            c = c.upper()
        out_chars.append(c)

    variant = "".join(out_chars)
    pad = draw(st.sampled_from(["", " ", "  ", " - ", "... "]))
    return f"{pad}{variant}{pad}"


@st.composite
def pop_openalex_records(draw: st.DrawFn) -> list[dict[str, str]]:
    """Construye registros PoP/OpenAlex sintéticos con grupos de títulos equivalentes.

    - Genera 1..4 títulos base DISTINTOS (claves normalizadas no vacías y
      distintas entre sí).
    - Para cada base, genera 1..4 registros cuyas variantes normalizan a la
      misma clave.
    - Añade 0..3 registros con título que normaliza a clave vacía (no deben
      marcarse): clave ``title`` ausente o con solo separadores.
    - Mezcla el orden de aparición para no asumir agrupamiento contiguo.

    Cada registro recibe un ``doi`` ÚNICO para que el conector derive un
    ``article_id`` distinto por registro (``oa-<hash12(doi)>``); así
    ``duplicate_of`` del segundo referencia el id del primero de su grupo.
    """
    bases: list[str] = []
    seen_keys: set[str] = set()
    raw_bases = draw(st.lists(_base_title, min_size=1, max_size=4))
    for b in raw_bases:
        k = norm_title(b)
        if k and k not in seen_keys:
            seen_keys.add(k)
            bases.append(b)
    if not bases:  # salvaguarda: asegura al menos un grupo con clave válida
        bases = ["x"]

    records: list[dict[str, str]] = []
    counter = 0

    for base in bases:
        n = draw(st.integers(min_value=1, max_value=4))
        for _ in range(n):
            title = draw(title_variant(base))
            records.append(
                {
                    "title": title,
                    "author": "Autor de prueba",
                    "year": "2024",
                    "doi": f"10.9999/demo.{counter:04d}",  # DOI único -> id único
                }
            )
            counter += 1

    # Registros con título de clave vacía: nunca deben marcarse. Alternan entre
    # omitir la clave 'title' y traerla con solo separadores.
    empties = draw(st.lists(st.sampled_from(["omit", "", "   ", "   -  "]), max_size=3))
    for e in empties:
        rec: dict[str, str] = {
            "author": "Autor de prueba",
            "year": "2024",
            "doi": f"10.9999/demo.{counter:04d}",
        }
        if e != "omit":
            rec["title"] = e
        records.append(rec)
        counter += 1

    perm = draw(st.permutations(records))
    return list(perm)


# Feature: fuente-openalex, Property 10: Deduplicación básica dentro de la fuente
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(raw_records=pop_openalex_records())
def test_dedup_basica_dentro_de_la_fuente_openalex(
    raw_records: list[dict[str, str]],
) -> None:
    """Segundo registro con título duplicado -> is_duplicate + duplicate_of al primero.

    Ejercita el camino del pipeline: extracción del conector + ``mark_duplicates``.

    - No se elimina ningún registro (conteo preservado; opera in place).
    - Por grupo de clave normalizada no vacía: el primero no es duplicado y cada
      siguiente tiene ``is_duplicate == True`` y ``duplicate_of`` == id del
      primero.
    - Título de clave vacía nunca se marca.

    **Validates: Requirements 4.1**
    """
    # Escribe los registros sintéticos a un Export_PoP_OpenAlex JSON temporal y
    # los extrae con el conector, igual que hace el pipeline por archivo. Se usa
    # un directorio temporal propio por ejemplo (en lugar de la fixture
    # function-scoped ``tmp_path``) para que cada entrada generada tenga su
    # propio archivo, como recomienda hypothesis.
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = Path(tmp_dir) / "openalex_demo.json"
        input_file.write_text(
            json.dumps(raw_records, ensure_ascii=False), encoding="utf-8"
        )
        records = extract_records(input_file)

    # El conector produce exactamente un ArticleRecord por objeto de entrada
    # (todos son dicts válidos). Verifica la premisa del test.
    assert len(records) == len(raw_records), (
        "El conector debe producir un registro por objeto de entrada válido."
    )

    original_count = len(records)
    original_ids = [r.article_id for r in records]

    # Dedupe tal como lo aplica el pipeline tras la extracción.
    mark_duplicates(records)

    # No se elimina ningún registro: conteo e identidades preservados y en orden.
    assert len(records) == original_count, "mark_duplicates no debe eliminar registros."
    assert [r.article_id for r in records] == original_ids, (
        "mark_duplicates no debe reordenar ni eliminar registros (opera in place)."
    )

    # Primera aparición por clave normalizada no vacía, en el orden actual.
    first_by_key: dict[str, str] = {}
    for rec in records:
        key = norm_title(rec.title)

        if not key:
            # Título de clave vacía: nunca se marca.
            assert rec.is_duplicate is False, (
                f"Registro con título de clave vacía no debe marcarse: {rec.article_id}"
            )
            assert rec.duplicate_of is None, (
                f"Registro con título de clave vacía no debe tener duplicate_of: "
                f"{rec.article_id}"
            )
            continue

        if key not in first_by_key:
            # Primera aparición del grupo: no es duplicado.
            first_by_key[key] = rec.article_id
            assert rec.is_duplicate is False, (
                f"Primera aparición de '{key}' ({rec.article_id}) no debe ser duplicado."
            )
            assert rec.duplicate_of is None, (
                f"Primera aparición de '{key}' ({rec.article_id}) no debe tener duplicate_of."
            )
        else:
            # Aparición posterior: duplicado del primero de su clave.
            assert rec.is_duplicate is True, (
                f"Aparición posterior de '{key}' ({rec.article_id}) debe marcarse duplicado."
            )
            assert rec.duplicate_of == first_by_key[key], (
                f"duplicate_of de {rec.article_id} debe apuntar al primero "
                f"({first_by_key[key]}); se obtuvo {rec.duplicate_of!r}."
            )
