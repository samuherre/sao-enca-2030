"""Modelo ORM del Indicador (tabla ``indicadores``).

Tarea 7.4 (tasks.md): modelo de persistencia SQLAlchemy del Indicador, cuarto
nivel de la jerarquía ENCA (D-003). Estilo tipado de SQLAlchemy 2.x
(``Mapped`` / ``mapped_column``) sobre la ``Base`` compartida.

Atributos confirmados (design.md "Data Models"; conceptual-data-model.md §2.4):

- ``id``: clave primaria entera autoincremental.
- ``nombre``: texto, NOT NULL (obligatorio).
- ``descripcion``: texto, NOT NULL (obligatorio).
- ``objetivo_id``: clave foránea → ``objetivos.id``, NOT NULL (integridad
  referencial, Req 8.1).

Relación N→1 con ``ObjetivoModel`` y 1→N con ``ActividadModel``.

Los atributos de seguimiento/evidencia del Indicador (unidad de medida, valor
objetivo, valor actual, fecha de medición, fuente/evidencia, estado) son
PENDING_VALIDATION y **no** se incluyen como columnas en esta Spec (Req 4.7,
9.1). Capa de persistencia únicamente; sin lógica de dominio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.models.base import Base

if TYPE_CHECKING:
    from backend.src.models.actividad import ActividadModel
    from backend.src.models.objetivo import ObjetivoModel


class IndicadorModel(Base):
    """Modelo ORM del Indicador (tabla ``indicadores``)."""

    __tablename__ = "indicadores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    objetivo_id: Mapped[int] = mapped_column(
        ForeignKey("objetivos.id"), nullable=False
    )

    objetivo: Mapped["ObjetivoModel"] = relationship(
        back_populates="indicadores"
    )
    actividades: Mapped[list["ActividadModel"]] = relationship(
        back_populates="indicador"
    )
