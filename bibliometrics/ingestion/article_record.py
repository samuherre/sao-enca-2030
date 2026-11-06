"""
article_record.py — Contrato de datos compartido (Article Data Contract V1).

Define el dataclass ``ArticleRecord`` que TODA fuente del Componente B debe
producir (Boletín SAO, Google Scholar, etc.). Antes vivía en
``extract_boletin.py``; se extrajo a un módulo compartido para que varios
conectores lo reutilicen sin duplicar el contrato.

REGLA FUNDAMENTAL (no inventar):
  - Campo no detectado → ``None``.
  - Si falta un obligatorio del contrato o la detección es ambigua, el
    conector debe marcar ``inclusion_status = "PENDIENTE_REVISIÓN"`` con nota.
    Nunca se inventan valores.

Referencia: ``docs/bibliometrics/article-data-contract.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Valores por defecto específicos de la fuente Boletín SAO. Se conservan aquí
# para no alterar el comportamiento de ``extract_boletin.py``, que importa
# ``ArticleRecord`` desde este módulo y depende de estos defaults.
SOURCE_NAME = "Boletín SAO"
EXTRACTION_METHOD = "pdfplumber + reglas (piloto V1)"


@dataclass
class ArticleRecord:
    """Registro conforme al Article Data Contract V1 (subconjunto del piloto)."""

    # Identificacion
    article_id: str
    title: Optional[str]
    doi: Optional[str] = None
    url: Optional[str] = None
    # Bibliografica
    authors: Optional[str] = None
    # Lista de autores individuales derivada de ``authors`` (tarea 9, opcional
    # V1). Se separa SOLO con separadores explícitos (coma, ';', '&', ' y ',
    # ' and '); si no hay separador explícito, queda ``[authors]`` sin partir
    # nombres por adivinación (principio de no invención). Vacía si authors=None.
    authors_list: list = field(default_factory=list)
    publication_year: Optional[int] = None
    journal: Optional[str] = SOURCE_NAME
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    # Contenido
    abstract: Optional[str] = None
    keywords: Optional[str] = None
    # Procedencia
    source: str = SOURCE_NAME
    source_url: Optional[str] = None
    extraction_date: str = ""
    extraction_method: Optional[str] = EXTRACTION_METHOD
    # Procesamiento
    processing_status: str = "EXTRAIDO"
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    notes: Optional[str] = None
    # Inclusion / Exclusion
    inclusion_status: str = "PENDIENTE_REVISIÓN"
    exclusion_reason: Optional[str] = None
    # Clasificacion (opcional V1 — no se implementa clasificador)
    ofcs: list = field(default_factory=list)
    classification_method: Optional[str] = None
    classification_confidence: Optional[float] = None
