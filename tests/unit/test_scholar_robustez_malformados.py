"""Property test del Pipeline_Scholar (spec multi-source-bibliometria, tarea 3.2).

Property 6 del design.md — "Robustez ante registros malformados":

    Para toda mezcla de registros válidos y malformados en la entrada, el
    pipeline produce exactamente los registros válidos, descarta solo los
    malformados y NO aborta el lote.

    **Validates: Requirements 1.5**

Enfoque (Testing Strategy del design): se genera una mezcla aleatoria de
registros PoP válidos (objetos JSON = dicts) y entradas malformadas (elementos
que NO son objetos clave→valor dentro de una lista JSON: cadenas, números,
booleanos, ``null`` y listas anidadas). La mezcla se serializa a un archivo
``.json`` dentro de un directorio temporal FUERA de ``data/raw`` y se ejecuta el
pipeline real mediante ``process_folder`` (API de función, sin UI).

El conector (``extract_scholar.extract_records``) descarta de forma robusta toda
entrada que no sea un ``dict`` y construye un ``ArticleRecord`` por cada objeto
(incluso un objeto vacío produce un registro válido marcado
``PENDIENTE_REVISIÓN``, pero sigue siendo un registro PRODUCIDO, no descartado).
Por eso en esta propiedad:

    - "válido"   = entrada que es un objeto JSON (``dict``)  → se produce.
    - "malformado" = entrada que NO es un objeto JSON        → se descarta.

Aserciones, sobre la tupla ``(records, leidos, procesados, descartados)`` que
devuelve ``process_folder``:
    - ``procesados  == número de objetos (válidos)``.
    - ``descartados == número de no-objetos (malformados)``.
    - ``leidos      == total de entradas`` (y ``== procesados + descartados``).
    - ``len(records) == procesados`` (se producen exactamente los válidos).
    - el lote NO aborta: que ``process_folder`` retorne ya evidencia que una
      entrada malformada no detuvo el procesamiento del resto.

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales):
se escriben en un directorio temporal del sistema (``tmp_path``), nunca en
``data/raw``, y se limpian automáticamente al terminar cada ejemplo.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Permite importar el pipeline y el conector desde bibliometrics/ (mismo patrón
# que el resto de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from pipelines.process_google_scholar import process_folder  # noqa: E402

# --- Generadores -------------------------------------------------------------

# Texto no vacío plausible para valores de campos (sin surrogates ni controles).
_nonempty_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=33),
    min_size=1,
    max_size=20,
)

# Un registro PoP VÁLIDO = objeto JSON (dict). Se incluyen claves mapeables
# plausibles (algunas opcionales). Incluso un dict vacío es "válido" en el
# sentido de esta propiedad (produce un ArticleRecord, no se descarta), por eso
# min_size=0: cubre el caso límite del objeto sin claves.
_valid_record = st.dictionaries(
    keys=st.sampled_from(
        ["title", "authors", "year", "doi", "journal", "source", "abstract", "keywords"]
    ),
    values=_nonempty_text,
    min_size=0,
    max_size=6,
)

# Una entrada MALFORMADA = cualquier cosa que NO sea un objeto clave→valor dentro
# de la lista JSON: cadena, número (int/float), booleano, null y listas anidadas.
_malformed_entry = st.one_of(
    st.text(max_size=20),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=3),
)


@st.composite
def mixed_entries(draw: st.DrawFn) -> list:
    """Lista JSON con una mezcla barajada de entradas válidas y malformadas.

    Se generan por separado ambos grupos (para conocer sus tamaños exactos) y se
    combinan en un orden arbitrario controlado por una permutación. El tamaño
    total es >= 0; puede haber cero válidos, cero malformados o ambos presentes.
    """
    valids = draw(st.lists(_valid_record, min_size=0, max_size=8))
    malformed = draw(st.lists(_malformed_entry, min_size=0, max_size=8))

    combined = valids + malformed
    # Permutación determinista a partir de una lista de índices barajada por
    # hypothesis, para intercalar válidos y malformados en posiciones variadas.
    order = draw(st.permutations(list(range(len(combined)))))
    shuffled = [combined[i] for i in order]
    return shuffled


def _is_valid_entry(entry: object) -> bool:
    """Entrada "válida" para esta propiedad = objeto JSON (dict)."""
    return isinstance(entry, dict)


# Feature: multi-source-bibliometria, Property 6: Robustez ante registros malformados
@settings(
    max_examples=150,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(entries=mixed_entries())
def test_robustez_ante_registros_malformados(entries: list) -> None:
    """El pipeline produce los válidos, descarta solo los malformados y no aborta.

    **Validates: Requirements 1.5**
    """
    esperados_validos = sum(1 for e in entries if _is_valid_entry(e))
    esperados_malformados = len(entries) - esperados_validos

    # Directorio temporal FUERA del repo (data/raw es inmutable). Se usa el
    # tmp del sistema y se limpia al salir del bloque.
    with tempfile.TemporaryDirectory() as tmp:
        input_dir = Path(tmp)
        (input_dir / "export_pop.json").write_text(
            json.dumps(entries), encoding="utf-8"
        )

        # El lote NO debe abortar ante entradas malformadas: si abortara,
        # process_folder lanzaría y el test fallaría aquí.
        records, leidos, procesados, descartados = process_folder(input_dir)

    # Se producen EXACTAMENTE los registros válidos.
    assert procesados == esperados_validos, (
        f"procesados={procesados} debe igualar el número de objetos válidos "
        f"({esperados_validos})."
    )
    assert len(records) == esperados_validos, (
        f"len(records)={len(records)} debe igualar los válidos "
        f"({esperados_validos})."
    )

    # Se descartan SOLO los malformados.
    assert descartados == esperados_malformados, (
        f"descartados={descartados} debe igualar el número de entradas "
        f"malformadas ({esperados_malformados})."
    )

    # Conservación aritmética: nada se pierde ni se duplica en el conteo.
    assert leidos == len(entries), (
        f"leidos={leidos} debe igualar el total de entradas ({len(entries)})."
    )
    assert leidos == procesados + descartados, (
        f"leidos={leidos} != procesados({procesados}) + descartados({descartados})."
    )
