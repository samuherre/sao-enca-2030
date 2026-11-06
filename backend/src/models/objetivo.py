"""Modelo ORM del Objetivo SMART (tabla ``objetivos``).

Tarea 7.3 (tasks.md): modelo de persistencia SQLAlchemy del Objetivo SMART,
tercer nivel de la jerarquía ENCA (D-002). Estilo tipado de SQLAlchemy 2.x
(``Mapped`` / ``mapped_column``) sobre la ``Base`` compartida.

Atributos confirmados (design.md "Data Models"; conceptual-data-model.md §2.3):

- ``id``: clave primaria entera autoincremental.
- ``descripcion``: texto, NOT NULL (obligatorio).
- ``meta_id``: clave foránea → ``metas.id``, NOT NULL (integridad referencial,
  Req 8.1).

Relación N→1 con ``MetaModel`` y 1→N con ``IndicadorModel``.

Capa de persistencia únicamente; sin lógica de dominio ni PENDING_VALIDATION.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.models.base import Base

if TYPE_CHECKING:
    from backend.src.models.indicador import IndicadorModel
    from backend.src.models.meta import MetaModel


class ObjetivoModel(Base):
    """Modelo ORM del Objetivo SMART (tabla ``objetivos``)."""

    __tablename__ = "objetivos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    meta_id: Mapped[int] = mapped_column(
        ForeignKey("metas.id"), nullable=False
    )

    meta: Mapped["MetaModel"] = relationship(back_populates="objetivos")
    indicadores: Mapped[list["IndicadorModel"]] = relationship(
        back_populates="objetivo"
    )
