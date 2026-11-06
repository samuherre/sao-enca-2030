"""
ofc_classifier.py — Clasificador de artículos por OFC (Componente B).

Metodología V1 (ADR-010): reglas por palabras clave (lexicón por OFC),
MULTILABEL. Transparente, reproducible y local; no requiere entrenamiento.

Flujo:
    texto (título + abstract + keywords)
        -> normalización (minúsculas, sin acentos)
        -> búsqueda de términos de cada OFC (límite de palabra)
        -> OFC con >=1 coincidencia, con evidencia y confianza

Reglas (steering bibliometrics.md, ADR-010):
    - No se inventan OFC (solo los 11 del catálogo).
    - Sin coincidencias -> estado NO_CLASIFICADO (ofcs vacío).
    - La confianza es un indicador EXPLICABLE (nº de términos coincidentes
      normalizado), NO una probabilidad estadística.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from preprocessing.text_normalizer import normalize_text  # noqa: E402

CATALOG_PATH = Path(__file__).resolve().parent / "ofc_catalog.json"

CLASSIFICATION_METHOD = "reglas-keywords-v1"
ESTADO_NO_CLASIFICADO = "NO_CLASIFICADO"
ESTADO_CLASIFICADO = "CLASIFICADO"

# Nº de términos distintos coincidentes que consideramos "confianza plena" (1.0).
# Por encima de este valor la confianza se satura en 1.0. Es un umbral de
# referencia explicable, configurable; NO una probabilidad.
_CONFIANZA_REFERENCIA = 3


@dataclass
class OFCMatch:
    """Coincidencia de un OFC: id, nombre, términos que coincidieron y confianza."""

    ofc_id: str
    nombre: str
    evidencia: list[str]
    confianza: float


@dataclass
class ResultadoClasificacion:
    """Resultado multilabel de clasificar un artículo."""

    ofcs: list[str] = field(default_factory=list)
    estado: str = ESTADO_NO_CLASIFICADO
    method: str = CLASSIFICATION_METHOD
    confianza: float = 0.0  # confianza global (máx. de las confianzas por OFC)
    detalle: list[OFCMatch] = field(default_factory=list)

    def evidencia_texto(self) -> str:
        """Resumen legible de la evidencia, para notas/trazabilidad."""
        if not self.detalle:
            return "Sin coincidencias con el lexicón de OFC."
        partes = [
            f"{m.ofc_id}: {', '.join(m.evidencia)}" for m in self.detalle
        ]
        return " | ".join(partes)


def _norm(texto: str) -> str:
    """Normaliza para comparación: normalize_text + minúsculas + sin acentos."""
    t = normalize_text(texto or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t


class OFCClassifier:
    """Clasificador multilabel por reglas de palabras clave."""

    def __init__(self, catalog_path: Path = CATALOG_PATH) -> None:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        self._ofc = data["ofc"]
        # Pre-normaliza y precompila los términos de cada OFC. Se separan
        # FUERTES (hábitat/ecosistema que define el OFC) y DÉBILES (geográficos
        # o de contexto). Estructura por OFC:
        #   (ofc_id, nombre, [(termino, patron, es_fuerte), ...])
        self._reglas: list[tuple[str, str, list[tuple[str, re.Pattern, bool]]]] = []
        for ofc in self._ofc:
            terminos: list[tuple[str, re.Pattern, bool]] = []
            for termino in ofc.get("terminos_fuertes", []):
                self._agregar(terminos, termino, es_fuerte=True)
            for termino in ofc.get("terminos_debiles", []):
                self._agregar(terminos, termino, es_fuerte=False)
            self._reglas.append((ofc["id"], ofc["nombre"], terminos))

    @staticmethod
    def _agregar(
        destino: list[tuple[str, re.Pattern, bool]], termino: str, es_fuerte: bool
    ) -> None:
        termino_norm = _norm(termino)
        if not termino_norm:
            return
        # Límite de palabra al inicio para no coincidir dentro de otra palabra
        # (p. ej. "isla" dentro de "aislado"). Al final se permite un sufijo de
        # plural opcional en español ("manglar" -> "manglares", "costero" ->
        # "costeros") sin exigir plurales explícitos en el catálogo.
        patron = re.compile(rf"(?<!\w){re.escape(termino_norm)}(?:es|s)?(?!\w)")
        destino.append((termino, patron, es_fuerte))

    def clasificar(self, texto: str) -> ResultadoClasificacion:
        """Clasifica un texto en cero, uno o varios OFC (multilabel).

        REGLA (ADR-010, mejora anti-falsos-positivos): un OFC solo se asigna si
        coincide AL MENOS UN término FUERTE (hábitat/ecosistema). Los términos
        débiles (geográficos/contexto) suman a la evidencia y la confianza, pero
        NO bastan por sí solos para asignar un OFC.
        """
        texto_norm = _norm(texto)
        if not texto_norm.strip():
            return ResultadoClasificacion()

        matches: list[OFCMatch] = []
        for ofc_id, nombre, terminos in self._reglas:
            fuertes = sorted(
                {t for t, patron, es_fuerte in terminos if es_fuerte and patron.search(texto_norm)}
            )
            if not fuertes:
                # Sin ningún término fuerte, NO se asigna el OFC (evita falsos
                # positivos por menciones geográficas de contexto).
                continue
            debiles = sorted(
                {t for t, patron, es_fuerte in terminos if not es_fuerte and patron.search(texto_norm)}
            )
            evidencia = fuertes + debiles
            # Confianza: los fuertes pesan 1.0 y los débiles 0.5.
            puntaje = len(fuertes) + 0.5 * len(debiles)
            confianza = min(1.0, puntaje / _CONFIANZA_REFERENCIA)
            matches.append(
                OFCMatch(
                    ofc_id=ofc_id,
                    nombre=nombre,
                    evidencia=evidencia,
                    confianza=round(confianza, 2),
                )
            )

        if not matches:
            return ResultadoClasificacion()

        # Orden por confianza descendente para presentación.
        matches.sort(key=lambda m: m.confianza, reverse=True)
        return ResultadoClasificacion(
            ofcs=[m.ofc_id for m in matches],
            estado=ESTADO_CLASIFICADO,
            confianza=max(m.confianza for m in matches),
            detalle=matches,
        )

    def clasificar_articulo(self, articulo: dict) -> ResultadoClasificacion:
        """Clasifica un registro de artículo (contrato V1) combinando los campos
        de texto relevantes: título, abstract y keywords."""
        partes = [
            articulo.get("title") or "",
            articulo.get("abstract") or "",
            articulo.get("keywords") or "",
        ]
        return self.clasificar(" \n ".join(partes))


__all__ = [
    "OFCClassifier",
    "ResultadoClasificacion",
    "OFCMatch",
    "CLASSIFICATION_METHOD",
    "ESTADO_NO_CLASIFICADO",
    "ESTADO_CLASIFICADO",
]
