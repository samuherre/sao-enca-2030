"""Utilidades transversales del backend del Sistema_ENCA.

Este paquete agrupa funciones de apoyo **puras** (sin estado y sin dependencias
de framework ni ORM), reutilizables por las capas superiores (schemas,
servicios, dominio). Conforme a `structure.md` §6 y `design.md` ("Utils"):
`backend/src/utils/` contiene utilidades como la normalización de texto para la
regla "recortar espacios" de los campos obligatorios.

Principio arquitectónico (tech.md §28, structure.md §28): estas utilidades no
importan SQLAlchemy, Pydantic ni FastAPI; solo utilizan la biblioteca estándar
de Python.
"""

from backend.src.utils.text import (
    es_texto_vacio,
    normalizar_texto,
    normalizar_texto_requerido,
)

__all__ = [
    "normalizar_texto",
    "es_texto_vacio",
    "normalizar_texto_requerido",
]
