"""Property test del Conector_OpenAlex_API (spec fuente-openalex-api, tarea 3.7).

Property 6 del design.md — "Reconstrucción correcta del abstract desde el índice
invertido":

    Para todo ``abstract_inverted_index`` bien formado, el texto reconstruido
    coloca cada palabra exactamente en las posiciones indicadas por el índice
    (en orden ascendente de posición); para todo índice ausente, ``None`` o
    vacío, ``abstract`` es ``None``.

    **Validates: Requirements 3.7**

Enfoque (Testing Strategy del design): se genera una lista aleatoria de palabras
SINTÉTICAS (``DEMO_DATA``), cada una un token no vacío y SIN espacios para que la
reconstrucción sea inequívoca; se les asigna posiciones contiguas ascendentes
``0..n-1`` (permitiendo opcionalmente que una palabra se repita en varias
posiciones) y se construye el índice invertido ``{palabra: [posiciones]}``. Se
verifica que ``reconstruct_abstract`` devuelve las palabras unidas por espacios en
el orden original de posición. Se cubre además el comportamiento vacío/ausente:
índice ``None`` → ``None``; dict vacío ``{}`` → ``None``; índice con solo entradas
inutilizables → ``None`` (ver ``reconstruct_abstract``).

Los datos generados por hypothesis son SINTÉTICOS (``DEMO_DATA``, no reales).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar los conectores desde bibliometrics/ (mismo patrón que los
# demás tests de este paquete, p. ej. test_openalex_api_article_id.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

# Función bajo prueba: reconstrucción del abstract desde el índice invertido.
from ingestion.openalex_api_client import reconstruct_abstract  # noqa: E402

# Tokens sintéticos (DEMO_DATA): no vacíos y SIN espacios, para que el texto
# reconstruido (unido por espacios) sea inequívoco respecto al orden de posición.
_word = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),  # letras y dígitos
    ),
    min_size=1,
    max_size=12,
)


@st.composite
def words_and_inverted_index(draw: st.DrawFn) -> tuple[list[str], dict]:
    """Genera ``(palabras_en_orden, indice_invertido)`` bien formado (DEMO_DATA).

    - Se toma una lista no vacía de palabras y se les asignan posiciones
      contiguas ascendentes ``0..n-1`` (la posición ``i`` corresponde a la
      palabra ``i`` en el orden original).
    - El índice invertido ``{palabra: [posiciones]}`` agrupa todas las posiciones
      de cada palabra, de modo que una palabra repetida aparece en varias
      posiciones (ejerciendo la ruta de repetición).
    - El orden de iteración del dict NO sigue las posiciones, para comprobar que
      la reconstrucción reordena por posición ascendente y no por inserción.
    """
    words = draw(st.lists(_word, min_size=1, max_size=40))

    # inverted_index: palabra -> lista de posiciones donde aparece.
    inverted_index: dict[str, list[int]] = {}
    for pos, word in enumerate(words):
        inverted_index.setdefault(word, []).append(pos)

    # Reordenar las claves para que el orden del dict no coincida con el de las
    # posiciones (así el test verifica que se ordena por posición, no por dict).
    keys = list(inverted_index.keys())
    perm = draw(st.permutations(keys))
    shuffled = {k: inverted_index[k] for k in perm}

    return words, shuffled


# Feature: fuente-openalex-api, Property 6: Reconstrucción correcta del abstract desde el índice invertido
@settings(max_examples=200)
@given(data=words_and_inverted_index())
def test_reconstruccion_correcta_del_abstract_desde_indice_invertido(
    data: tuple[list[str], dict],
) -> None:
    """Para un índice bien formado, el texto reconstruido coloca cada palabra en
    sus posiciones y las concatena en orden ascendente de posición.

    Validates: Requirements 3.7
    """
    words, inverted_index = data

    result = reconstruct_abstract(inverted_index)

    expected = " ".join(words)
    assert result == expected, (
        "El abstract reconstruido no coincide con las palabras en orden de "
        f"posición ascendente: esperado {expected!r}, obtenido {result!r}"
    )


# Feature: fuente-openalex-api, Property 6: Reconstrucción correcta del abstract desde el índice invertido
def test_indice_none_vacio_o_inutilizable_devuelve_none() -> None:
    """Índice ausente/None/vacío o con solo entradas inutilizables → None.

    Validates: Requirements 3.7
    """
    # Ausente / None → None (no se inventa texto).
    assert reconstruct_abstract(None) is None
    # Dict vacío {} → None.
    assert reconstruct_abstract({}) is None
    # Solo entradas inutilizables (posiciones vacías, no-enteras o negativas)
    # → None: no hay ninguna posición válida que colocar.
    assert reconstruct_abstract({"hola": []}) is None
    assert reconstruct_abstract({"hola": [-1], "mundo": ["x"]}) is None
