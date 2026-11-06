"""Pruebas unitarias de split_authors (spec boletin-sao-ingestion, tarea 9).

Verifican la separacion CONSERVADORA de la cadena de autores en lista:
  - Separadores explicitos: coma, punto y coma, '&', y conjunciones ' y '/' and '.
  - Sin separador explicito: NO se parten nombres pegados (no invencion); se
    devuelve la cadena completa como unico elemento y se marca incertidumbre si
    aparenta varios autores.
  - Casos borde: None, cadena vacia, un solo autor.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from ingestion.extract_boletin import split_authors  # noqa: E402


def test_separador_coma():
    lista, incierto = split_authors("Diego Molina, Christian Aguirre-Alas, Luis Pineda")
    assert lista == ["Diego Molina", "Christian Aguirre-Alas", "Luis Pineda"]
    assert incierto is False


def test_separador_ampersand():
    lista, incierto = split_authors("Vladislav Marcuk & Donovan de Boer")
    assert lista == ["Vladislav Marcuk", "Donovan de Boer"]
    assert incierto is False


def test_conjuncion_y():
    lista, incierto = split_authors("Ramon David Ruiz-Correa y Ana Maria Castano")
    assert lista == ["Ramon David Ruiz-Correa", "Ana Maria Castano"]
    assert incierto is False


def test_coma_y_conjuncion_mezcladas():
    lista, incierto = split_authors(
        "Michael Castano-Diaz, Elisa Lotero-Velasquez, y Sergio Chaparro-Herrera"
    )
    assert lista == [
        "Michael Castano-Diaz",
        "Elisa Lotero-Velasquez",
        "Sergio Chaparro-Herrera",
    ]
    assert incierto is False


def test_punto_y_coma():
    lista, incierto = split_authors("A. Perez; B. Gomez; C. Ruiz")
    assert lista == ["A. Perez", "B. Gomez", "C. Ruiz"]
    assert incierto is False


def test_un_solo_autor():
    lista, incierto = split_authors("Saul Sanchez-Soto")
    assert lista == ["Saul Sanchez-Soto"]
    assert incierto is False  # 2 nombres propios: no aparenta varios pegados


def test_autores_pegados_sin_separador_no_se_parten():
    """Caso critico: varios autores pegados por espacios, sin separador.

    No se deben partir nombres (no invencion). Se devuelve la cadena completa
    como unico elemento y se marca incertidumbre.
    """
    crudo = "Sergio Chaparro-Herrera Andrea Lopera-Salazar Ramon David Ruiz-Correa"
    lista, incierto = split_authors(crudo)
    assert lista == [crudo]       # sin dividir
    assert incierto is True        # aparenta varios autores pegados


def test_none_y_vacio():
    assert split_authors(None) == ([], False)
    assert split_authors("") == ([], False)
    assert split_authors("   ") == ([], False)


def test_sin_vacios_por_separadores_colgantes():
    """Separadores redundantes/colgantes no producen elementos vacios."""
    lista, _ = split_authors("A. Perez, , B. Gomez &")
    assert lista == ["A. Perez", "B. Gomez"]
    assert "" not in lista
