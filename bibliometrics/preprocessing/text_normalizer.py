"""
text_normalizer.py — Normalizacion de texto extraido de PDFs (Componente B).

PROBLEMA OBSERVADO en el piloto (boletines SAO):
  1. Tildes separadas: el PDF codifica las vocales acentuadas como la vocal
     base seguida de un acento combinante suelto, p. ej. "Bolet´ın",
     "Distribuci´on", "Gorrio´n". Visualmente son dos caracteres.
  2. Espacios perdidos: en los parrafos justificados (resumen) las palabras
     aparecen pegadas, p. ej. "ElGorrio´n-mont´esdeanteojos".

ALCANCE (conservador, no inventar):
  - (1) se corrige de forma fiable con normalizacion Unicode.
  - (2) solo se corrige donde es SEGURO (acento mal colocado entre letras).
    No intentamos re-segmentar palabras pegadas mediante diccionarios en V1,
    porque eso introduciria suposiciones. Se deja documentado como pendiente.
"""

from __future__ import annotations

import re
import unicodedata

# Acentos combinantes que aparecen sueltos en el texto extraido.
# U+00B4 ACUTE ACCENT (´) y U+0060 GRAVE ACCENT (`) usados como "tilde".
_LOOSE_ACUTE = "\u00b4"  # ´
_COMBINING_ACUTE = "\u0301"  # ́ (acento agudo combinante)

# Patron: letra + acento suelto + letra  -> reposiciona el acento sobre la
# vocal correcta. En estos PDFs el patron es "o´n" = "ón", "ı´" (i sin punto)
# tambien aparece. Tratamos la i sin punto (U+0131, ı) como i normal.
_DOTLESS_I = "\u0131"  # ı

# Tilde de la enie: en el texto extraido aparece como "n" + "˜" (U+02DC SMALL
# TILDE) o "n" + "~", p. ej. "Castan˜o" -> "Castaño", "Mun˜oz" -> "Muñoz".
_SMALL_TILDE = "\u02dc"  # ˜
_COMBINING_TILDE = "\u0303"  # ̃


def _fix_loose_accents(text: str) -> str:
    """Convierte secuencias 'vocal + ´' en la vocal acentuada precompuesta.

    En el texto de los boletines el acute (´) aparece DESPUES de la vocal que
    debe acentuar (p. ej. "Bolet´ın" -> la i debe llevar tilde: "Boletín";
    "Gorrio´n" -> "Gorrión"). Reglas observadas:
      - "<vocal>´" justo antes de otra letra: la tilde pertenece a esa vocal
        previa cuando la vocal previa + tilde forma una palabra con tilde en
        esa silaba. Para ser conservadores aplicamos el caso dominante del
        corpus: el acute se asocia a la vocal INMEDIATAMENTE anterior.
    """
    # Normaliza la i sin punto a i normal antes de acentuar.
    text = text.replace(_DOTLESS_I, "i")

    # Enie: "n˜" o "n~" -> "ñ" (y mayuscula). Se corrige antes del resto.
    def repl_enie(match: re.Match) -> str:
        base = match.group(1)
        return unicodedata.normalize("NFC", base + _COMBINING_TILDE)

    text = re.sub(rf"([nN])[{_SMALL_TILDE}~]", repl_enie, text)

    # Caso "vocal + ´"  ->  vocal + acento combinante  -> precompuesta.
    # Ej: "o´" -> "ó", "ı´"/"i´" -> "í".
    def repl_after(match: re.Match) -> str:
        vocal = match.group(1)
        combined = unicodedata.normalize("NFC", vocal + _COMBINING_ACUTE)
        return combined

    text = re.sub(rf"([aeiouAEIOU]){_LOOSE_ACUTE}", repl_after, text)

    # Caso "´ + vocal" (el acute aparece ANTES de la vocal, visto en titulos
    # en mayuscula: "´ ´ ´" y "DISTRIBUCION"). Ej: "´o" -> "ó".
    def repl_before(match: re.Match) -> str:
        vocal = match.group(1)
        combined = unicodedata.normalize("NFC", vocal + _COMBINING_ACUTE)
        return combined

    text = re.sub(rf"{_LOOSE_ACUTE}([aeiouAEIOU])", repl_before, text)

    # Elimina acutes sueltos remanentes (p. ej. filas "´ ´ ´" sobre titulos).
    text = text.replace(_LOOSE_ACUTE, "")

    return text


def _collapse_whitespace(text: str) -> str:
    """Normaliza espacios y saltos de linea sin fusionar palabras."""
    # Une guion de corte de linea: "palabra-\nparte" -> "palabraparte".
    text = re.sub(r"-\n", "", text)
    # Convierte saltos de linea simples dentro de parrafo en espacio.
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    # Colapsa espacios multiples.
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def normalize_text(text: str) -> str:
    """Normalizacion principal: tildes sueltas + espacios.

    NO re-segmenta palabras pegadas (p. ej. "ElGorrion...") porque eso
    requeriria suposiciones. Ese problema se marca como pendiente en el piloto.
    """
    if not text:
        return ""
    text = _fix_loose_accents(text)
    text = _collapse_whitespace(text)
    return text


__all__ = ["normalize_text"]
