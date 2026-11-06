"""Pruebas unitarias del clasificador de OFC (spec ofc-classification, tarea 4).

Ejercen el clasificador real por reglas de palabras clave sobre textos de
ejemplo. No requieren base de datos ni servicios externos.

Casos cubiertos:
  - Coincidencia simple (un OFC).
  - Multilabel (varios OFC en un mismo texto).
  - Sin coincidencia -> NO_CLASIFICADO.
  - Insensibilidad a mayúsculas y acentos.
  - Evidencia y confianza presentes y coherentes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permite importar el clasificador desde bibliometrics/.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

from classification.ofc_classifier import (  # noqa: E402
    ESTADO_CLASIFICADO,
    ESTADO_NO_CLASIFICADO,
    OFCClassifier,
)

import pytest  # noqa: E402


@pytest.fixture(scope="module")
def clasificador() -> OFCClassifier:
    return OFCClassifier()


def test_coincidencia_simple_alta_montana(clasificador: OFCClassifier) -> None:
    """Un texto claramente de páramo/alta montaña activa OFC-07."""
    texto = "Nuevos registros de un colibrí en el páramo de alta montaña."
    res = clasificador.clasificar(texto)
    assert res.estado == ESTADO_CLASIFICADO
    assert "OFC-07" in res.ofcs


def test_multilabel(clasificador: OFCClassifier) -> None:
    """Un texto que menciona varios ecosistemas activa varios OFC."""
    texto = (
        "Observaciones de aves en manglares costeros del Caribe y también en "
        "humedales de agua dulce interiores."
    )
    res = clasificador.clasificar(texto)
    assert res.estado == ESTADO_CLASIFICADO
    # Debe reconocer tanto marino/costero (OFC-01) como humedales (OFC-02).
    assert "OFC-01" in res.ofcs
    assert "OFC-02" in res.ofcs
    assert len(res.ofcs) >= 2


def test_sin_coincidencia_es_no_clasificado(clasificador: OFCClassifier) -> None:
    """Un texto sin términos del lexicón queda NO_CLASIFICADO, sin inventar OFC."""
    texto = "Esta nota describe un método estadístico abstracto sin contexto ecológico."
    res = clasificador.clasificar(texto)
    assert res.estado == ESTADO_NO_CLASIFICADO
    assert res.ofcs == []
    assert res.confianza == 0.0


def test_texto_vacio_es_no_clasificado(clasificador: OFCClassifier) -> None:
    res = clasificador.clasificar("")
    assert res.estado == ESTADO_NO_CLASIFICADO
    assert res.ofcs == []


def test_insensible_a_acentos_y_mayusculas(clasificador: OFCClassifier) -> None:
    """'PARAMO' (sin tilde, en mayúsculas) debe activar igual que 'páramo'."""
    con_tilde = clasificador.clasificar("estudio en el páramo")
    sin_tilde_mayus = clasificador.clasificar("ESTUDIO EN EL PARAMO")
    assert con_tilde.ofcs == sin_tilde_mayus.ofcs
    assert "OFC-07" in sin_tilde_mayus.ofcs


def test_evidencia_y_confianza(clasificador: OFCClassifier) -> None:
    """La clasificación registra evidencia (términos) y confianza en (0,1]."""
    texto = "aviturismo y observación de aves en una ruta de aviturismo sostenible"
    res = clasificador.clasificar(texto)
    assert res.estado == ESTADO_CLASIFICADO
    assert "OFC-11" in res.ofcs
    match = next(m for m in res.detalle if m.ofc_id == "OFC-11")
    assert match.evidencia  # al menos un término coincidente
    assert 0.0 < match.confianza <= 1.0


def test_limite_de_palabra_evita_falsos_positivos(clasificador: OFCClassifier) -> None:
    """Un término corto no debe coincidir dentro de otra palabra.

    'isla' (OFC-01) no debe dispararse por 'aislado'/'aislamiento'.
    """
    texto = "El individuo permaneció aislado durante el aislamiento del experimento."
    res = clasificador.clasificar(texto)
    assert "OFC-01" not in res.ofcs


def test_clasificar_articulo_combina_campos(clasificador: OFCClassifier) -> None:
    """clasificar_articulo combina title + abstract + keywords."""
    articulo = {
        "title": "Aves en un campus universitario",
        "abstract": "Registro en entorno urbano de la ciudad.",
        "keywords": "ecoparque, zona verde",
    }
    res = clasificador.clasificar_articulo(articulo)
    assert "OFC-08" in res.ofcs  # sistemas urbanos
