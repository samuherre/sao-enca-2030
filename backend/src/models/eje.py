"""Modelo ORM del Eje estratégico (tabla ``ejes``).

Tarea 7.1 (tasks.md): modelo de persistencia SQLAlchemy del nivel raíz de la
jerarquía ENCA (D-001). Usa el estilo tipado de SQLAlchemy 2.x (``Mapped`` /
``mapped_column``) sobre la ``Base`` declarativa compartida
(``backend.src.models.base``).

Atributos confirmados (design.md "Data Models"; conceptual-data-model.md §2.1):

- ``id``: clave primaria entera autoincremental generada por PostgreSQL
  (design.md "Identificadores — TECHNICAL_DECISION").
- ``nombre``: texto, NOT NULL (campo obligatorio confirmado).
- ``descripcion``: texto, NULL permitido (campo opcional confirmado).

Relación 1→N con ``MetaModel`` (un Eje contiene varias Metas). El Eje es la
raíz y no tiene referencia a un padre (Req 6.3).

Esta clase pertenece exclusivamente a la capa de persistencia y no contiene
lógica de dominio ni dependencias de FastAPI/Pydantic (tech.md §28,
structure.md §28). No incluye atributos PENDING_VALIDATION.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.models.base import Base

if TYPE_CHECKING:
    from backend.src.models.meta import MetaModel


class EjeModel(Base):
    """Modelo ORM del Eje estratégico (tabla ``ejes``)."""

    __tablename__ = "ejes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)

    metas: Mapped[list["MetaModel"]] = relationship(back_populates="eje")
