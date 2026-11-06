"""Repositorio de acceso a datos de la Meta (segundo nivel de la jerarquía).

Tarea 8.2 (tasks.md): implementa el ``MetaRepository`` con las operaciones
``crear``, ``obtener_por_id``, ``listar_por_padre`` (por ``eje_id``) y
``padre_existe`` (``eje_id``). Es el único punto que conoce consultas y
sesiones de SQLAlchemy para la entidad Meta (design.md "Architecture").
Devuelve entidades de dominio (``backend.src.domain.entities``), mapeando
desde/hacia el modelo ORM ``MetaModel`` (``backend.src.models``).

La Meta es hija del Eje (D-001): su padre inmediato es un Eje identificado por
``eje_id`` (FK NOT NULL, Req 8.1).

Requisitos: 2.1 (crear Meta bajo un Eje), 2.4/2.5 (listar Metas de un Eje,
incluyendo ``[]``), 2.6 (identificar el Eje padre), 8.1 (integridad
referencial). ``padre_existe`` sostiene la regla de aplicación "el Eje padre
debe existir" aplicada en la capa de servicios (Req 8.2).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.domain.entities import Meta
from backend.src.models.eje import EjeModel
from backend.src.models.meta import MetaModel


class MetaRepository:
    """Acceso a datos de la Meta mediante SQLAlchemy.

    Recibe una ``Session`` de SQLAlchemy por construcción. No gestiona el ciclo
    de vida de la sesión (corresponde a la capa superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _a_entidad(modelo: MetaModel) -> Meta:
        """Mapea un ``MetaModel`` (ORM) a la entidad de dominio ``Meta``."""
        return Meta(
            id=modelo.id,
            descripcion=modelo.descripcion,
            eje_id=modelo.eje_id,
        )

    def crear(self, meta: Meta) -> Meta:
        """Persiste una Meta y devuelve la entidad con su ``id`` generado.

        Req 2.1: registrar una nueva Meta asociada a su Eje padre (``eje_id``).
        """
        modelo = MetaModel(descripcion=meta.descripcion, eje_id=meta.eje_id)
        self._session.add(modelo)
        self._session.flush()
        return self._a_entidad(modelo)

    def obtener_por_id(self, meta_id: int) -> Meta | None:
        """Devuelve la Meta con el ``id`` dado, o ``None`` si no existe."""
        modelo = self._session.get(MetaModel, meta_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    def listar_por_padre(self, eje_id: int) -> list[Meta]:
        """Devuelve las Metas del Eje dado; ``[]`` si no hay ninguna.

        Req 2.4/2.5: consultar la colección de Metas de un Eje.
        """
        modelos = self._session.scalars(
            select(MetaModel).where(MetaModel.eje_id == eje_id)
        ).all()
        return [self._a_entidad(m) for m in modelos]

    def padre_existe(self, eje_id: int) -> bool:
        """Indica si existe un Eje padre con el ``id`` dado.

        Soporta la validación "el Eje padre debe existir" (Req 8.2) aplicada en
        la capa de servicios antes de crear una Meta.
        """
        existe = self._session.scalar(
            select(EjeModel.id).where(EjeModel.id == eje_id)
        )
        return existe is not None
