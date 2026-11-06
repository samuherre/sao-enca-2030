"""Pruebas unitarias de la utilidad de normalización de texto.

Cubre la tarea 6.3 (tasks.md) y la regla de validación de campos obligatorios
(requirements.md Req 1.2, 2.3, 3.3, 4.3, 5.3): un campo obligatorio es inválido
cuando es ``None``, ``""`` o solo espacios; y válido cuando, tras recortar los
espacios, conserva al menos un carácter.

Resultado verificable (tasks.md 6.3): la función clasifica correctamente
``None``, ``""`` y ``"   "`` como inválidos y ``" x "`` como válido ("x").
"""

import pytest

from backend.src.utils.text import (
    es_texto_vacio,
    normalizar_texto,
    normalizar_texto_requerido,
)


class TestEsTextoVacio:
    """`es_texto_vacio`: clasificación de validez de campos obligatorios."""

    @pytest.mark.parametrize("valor", [None, "", "   ", "\t", "\n", " \t\n "])
    def test_valores_invalidos_son_vacios(self, valor):
        # None, vacío o solo espacios en blanco => inválido (True).
        assert es_texto_vacio(valor) is True

    @pytest.mark.parametrize(
        "valor", [" x ", "x", "texto", "  texto  ", "0", " 0 "]
    )
    def test_valores_con_contenido_no_son_vacios(self, valor):
        # Al menos un carácter tras recortar => válido (False).
        assert es_texto_vacio(valor) is False

    def test_resultado_verificable_tarea_6_3(self):
        # Caso explícito del resultado verificable de la tarea 6.3.
        assert es_texto_vacio(None) is True
        assert es_texto_vacio("") is True
        assert es_texto_vacio("   ") is True
        assert es_texto_vacio(" x ") is False


class TestNormalizarTexto:
    """`normalizar_texto`: recorta espacios y preserva ``None``."""

    def test_recorta_espacios_inicio_y_final(self):
        assert normalizar_texto(" x ") == "x"
        assert normalizar_texto("  texto  ") == "texto"

    def test_solo_espacios_queda_cadena_vacia(self):
        assert normalizar_texto("   ") == ""

    def test_none_se_preserva(self):
        assert normalizar_texto(None) is None

    def test_texto_sin_espacios_externos_no_cambia(self):
        assert normalizar_texto("texto") == "texto"

    def test_no_altera_espacios_internos(self):
        assert normalizar_texto("  dos palabras  ") == "dos palabras"


class TestNormalizarTextoRequerido:
    """`normalizar_texto_requerido`: texto válido o ``None`` si queda vacío."""

    def test_valor_valido_devuelve_texto_recortado(self):
        assert normalizar_texto_requerido(" x ") == "x"
        assert normalizar_texto_requerido("  texto  ") == "texto"

    @pytest.mark.parametrize("valor", [None, "", "   ", "\t\n"])
    def test_valores_invalidos_devuelven_none(self, valor):
        assert normalizar_texto_requerido(valor) is None
