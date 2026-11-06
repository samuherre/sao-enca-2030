"""Modelo ORM de la Actividad (tabla ``actividades``).

Tarea 7.5 (tasks.md): modelo de persistencia SQLAlchemy de la Actividad,
quinto y último nivel de la jerarquía ENCA (D-004). Estilo tipado de
SQLAlchemy 2.x (``Mapped`` / ``mapped_column``) sobre la ``Base`` compartida.

Atributos confirmados (design.md "Data Models"; conceptual-data-model.md §2.5):

- ``id``: clave primaria entera autoincremental.
- ``descripcion``: texto, NOT NULL (nombre/descripción confirmado, obligatorio).
- ``indicador_id``: clave foránea → ``indicadores.id``, NOT NULL (integridad
  referencial, Req 8.1).

Relación N→1 con ``IndicadorModel``.

Los atributos de seguimiento/evidencia de la Actividad (responsable, fecha,
estado, evidencia/fuente, región) son PENDING_VALIDATION y **no** se incluyen
como columnas en esta Spec (Req 5.8, 9.2). Capa de persistencia únicamente;
sin lógica de dominio.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.models.base import Base

if TYPE_CHECKING:
    from backend.src.models.indicador import IndicadorModel


class ActividadModel(Base):
    """Modelo ORM de la Actividad (tabla ``actividades``)."""

    __tablename__ = "actividades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    indicador_id: Mapped[int] = mapped_column(
        ForeignKey("indicadores.id"), nullable=False
    )

    indicador: Mapped["IndicadorModel"] = relationship(
        back_populates="actividades"
    )
