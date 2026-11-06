"""Capa de dominio del Sistema_ENCA — entidades y reglas puras.

Este paquete contiene las entidades de dominio de la jerarquía confirmada de la
ENCA 2030 (Eje → Meta → Objetivo SMART → Indicador → Actividad) y, en módulos
posteriores, las reglas invariantes y las excepciones de dominio.

Principio arquitectónico (tech.md §28, structure.md §28): el dominio es
**independiente del framework y del ORM**. Los módulos de este paquete no
importan SQLAlchemy, Pydantic ni FastAPI; solo utilizan la biblioteca estándar
de Python. Esto preserva la dirección de dependencias hacia el dominio y
facilita las pruebas y la evolución tecnológica.

Alcance (requirements.md): únicamente las cinco entidades confirmadas con sus
atributos confirmados. Los atributos marcados como PENDING_VALIDATION
(Indicador: unidad de medida, valor objetivo, valor actual, fecha de medición,
fuente/evidencia, estado; Actividad: responsable, fecha, estado,
evidencia/fuente, región) **no** se modelan en esta Spec.
"""

from backend.src.domain.entities import (
    Actividad,
    Eje,
    Indicador,
    Meta,
    Objetivo,
)

__all__ = [
    "Eje",
    "Meta",
    "Objetivo",
    "Indicador",
    "Actividad",
]
