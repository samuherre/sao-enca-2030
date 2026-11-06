"""Property test del pipeline Google Scholar (spec multi-source-bibliometria, tarea 3.5).

Property 9 del design.md — "Deduplicación básica dentro de la fuente":

    Para todo dataset de una fuente, dos registros con el mismo título
    normalizado hacen que el segundo quede marcado ``is_duplicate = true`` con
    ``duplicate_of`` apuntando al primero, sin eliminar ningún registro.

    **Validates: Requirements 4.1**

Bajo prueba: ``mark_duplicates`` y ``norm_title`` de
``bibliometrics/pipelines/_common.py`` (los helpers que usa el pipeline de
Google Scholar ``process_google_scholar.py`` tras la extracción). La detección
V1 es CONSERVADORA: marca duplicado exacto por título normalizado (casing,
tildes/acentos y espaciado colapsados), no borra nada y los títulos
vacíos/None nunca se marcan.

Enfoque (Testing Strategy del design): se construyen listas de ``ArticleRecord``
sintéticos directamente (lo más limpio para ejercitar ``mark_duplicates``),
mezclando:
  - grupos de títulos que normalizan a la MISMA clave mediante variantes de
    casing, acentos y espaciado (deben deduplicarse entre sí), y
  - registros con título vacío o ``None`` (nunca se marcan).

Aserciones:
  - No se elimina ningún registro (el conteo se conserva; ``mark_duplicates``
    opera in place).
  - Para cada grupo que comparte clave normalizada no vacía: la PRIMERA
    aparición no es duplicado y cada aparición posterior tiene
    ``is_duplicate == True`` y ``duplicate_of == article_id`` del primero.
  - Los registros con título vacío/None no se marcan (``is_duplicate == False``,
    ``duplicate_of is None``).

Los datos generados por hypothesis son SINTÉTICOS (DEMO_DATA, no reales).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el contrato y los helpers desde bibliometrics/ (mismo patrón
# que el resto de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from ingestion.article_record import ArticleRecord  # noqa: E402
from pipelines._common import mark_duplicates, norm_title  # noqa: E402

# --- Generación de títulos base y de variantes que normalizan a la misma clave --

# Un título base con letras ASCII y espacios: garantiza que su clave normalizada
# NO sea vacía (contiene al menos un alfanumérico). Evitamos construir el título
# solo con separadores para que cada grupo tenga una clave real.
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
    además de posible espaciado/relleno con separadores en los bordes. Todas
    estas transformaciones son absorbidas por ``norm_title``.
    """
    out_chars: list[str] = []
    for ch in base:
        if ch == " ":
            # Espaciado variable (1..3 espacios) — colapsado por norm_title.
            out_chars.append(" " * draw(st.integers(min_value=1, max_value=3)))
            continue
        c = ch
        if c in _ACCENT_MAP and draw(st.booleans()):
            c = _ACCENT_MAP[c]
        if draw(st.booleans()):
            c = c.upper()
        out_chars.append(c)

    variant = "".join(out_chars)
    # Relleno con separadores en los bordes (también colapsado/stripeado).
    pad = draw(st.sampled_from(["", " ", "  ", " - ", "... "]))
    return f"{pad}{variant}{pad}"


@st.composite
def record_lists(draw: st.DrawFn) -> list[ArticleRecord]:
    """Construye una lista de ArticleRecord con grupos de títulos equivalentes.

    - Genera 1..4 títulos base DISTINTOS (claves normalizadas no vacías y
      distintas entre sí).
    - Para cada base, genera 1..4 registros cuyas variantes normalizan a la
      misma clave.
    - Añade 0..3 registros con título vacío o None (no deben marcarse).
    - Mezcla el orden de aparición para no asumir agrupamiento contiguo.
    Cada registro recibe un ``article_id`` único y determinista.
    """
    # Bases con claves normalizadas distintas (de lo contrario dos "bases"
    # podrían colisionar y romper el conteo esperado por grupo).
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

    records: list[ArticleRecord] = []
    counter = 0

    for base in bases:
        n = draw(st.integers(min_value=1, max_value=4))
        for _ in range(n):
            title = draw(title_variant(base))
            records.append(ArticleRecord(article_id=f"gs-{counter:04d}", title=title))
            counter += 1

    # Registros con título vacío/None: nunca deben marcarse.
    empties = draw(st.lists(st.sampled_from([None, "", "   ", "   -  "]), max_size=3))
    for e in empties:
        records.append(ArticleRecord(article_id=f"gs-{counter:04d}", title=e))
        counter += 1

    # Mezcla el orden para no depender de agrupamiento contiguo.
    perm = draw(st.permutations(records))
    return list(perm)


# Feature: multi-source-bibliometria, Property 9: Deduplicación básica dentro de la fuente
@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(records=record_lists())
def test_dedup_basica_dentro_de_la_fuente(records: list[ArticleRecord]) -> None:
    """La primera aparición de cada título normalizado queda; las siguientes se marcan.

    - No se elimina ningún registro (conteo preservado; opera in place).
    - Por grupo de clave normalizada no vacía: el primero no es duplicado y cada
      siguiente tiene ``is_duplicate == True`` y ``duplicate_of`` == id del
      primero.
    - Título vacío/None nunca se marca.

    **Validates: Requirements 4.1**
    """
    original_count = len(records)
    original_ids = [r.article_id for r in records]

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
            # Título vacío/None: nunca se marca.
            assert rec.is_duplicate is False, (
                f"Registro con título vacío/None no debe marcarse: {rec.article_id}"
            )
            assert rec.duplicate_of is None, (
                f"Registro con título vacío/None no debe tener duplicate_of: {rec.article_id}"
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
