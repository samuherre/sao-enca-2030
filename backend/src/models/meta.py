"""Modelo ORM de la Meta (tabla ``metas``).

Tarea 7.2 (tasks.md): modelo de persistencia SQLAlchemy de la Meta, segundo
nivel de la jerarquía ENCA (D-001). Estilo tipado de SQLAlchemy 2.x
(``Mapped`` / ``mapped_column``) sobre la ``Base`` compartida.

Atributos confirmados (design.md "Data Models"; conceptual-data-model.md §2.2):

- ``id``: clave primaria entera autoincremental.
- ``descripcion``: texto, NOT NULL (obligatorio).
- ``eje_id``: clave foránea → ``ejes.id``, NOT NULL (integridad referencial,
  Req 8.1).

Relación N→1 con ``EjeModel`` y 1→N con ``ObjetivoModel``.

Capa de persistencia únicamente; sin lógica de dominio ni PENDING_VALIDATION.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.models.base import Base

if TYPE_CHECKING:
    from backend.src.models.eje import EjeModel
    from backend.src.models.objetivo import ObjetivoModel


class MetaModel(Base):
    """Modelo ORM de la Meta (tabla ``metas``)."""

    __tablename__ = "metas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    descripcion: Mapped[str] = mapped_column(String, nullable=False)
    eje_id: Mapped[int] = mapped_column(
        ForeignKey("ejes.id"), nullable=False
    )

    eje: Mapped["EjeModel"] = relationship(back_populates="metas")
    objetivos: Mapped[list["ObjetivoModel"]] = relationship(
        back_populates="meta"
    )
