"""Repositorio de acceso a datos del Objetivo SMART (tercer nivel).

Tarea 8.3 (tasks.md): implementa el ``ObjetivoRepository`` con las operaciones
``crear``, ``obtener_por_id``, ``listar_por_padre`` (por ``meta_id``) y
``padre_existe`` (``meta_id``). Es el único punto que conoce consultas y
sesiones de SQLAlchemy para la entidad Objetivo (design.md "Architecture").
Devuelve entidades de dominio (``backend.src.domain.entities``), mapeando
desde/hacia el modelo ORM ``ObjetivoModel`` (``backend.src.models``).

El Objetivo SMART es hijo de la Meta (D-002): su padre inmediato es una Meta
identificada por ``meta_id`` (FK NOT NULL, Req 8.1).

Requisitos: 3.1 (crear Objetivo bajo una Meta), 3.4/3.6 (listar Objetivos de
una Meta, incluyendo ``[]``, e identificar la Meta padre), 8.1 (integridad
referencial). ``padre_existe`` sostiene la regla de aplicación "la Meta padre
debe existir" aplicada en la capa de servicios (Req 8.2).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.domain.entities import Objetivo
from backend.src.models.meta import MetaModel
from backend.src.models.objetivo import ObjetivoModel


class ObjetivoRepository:
    """Acceso a datos del Objetivo SMART mediante SQLAlchemy.

    Recibe una ``Session`` de SQLAlchemy por construcción. No gestiona el ciclo
    de vida de la sesión (corresponde a la capa superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _a_entidad(modelo: ObjetivoModel) -> Objetivo:
        """Mapea un ``ObjetivoModel`` (ORM) a la entidad ``Objetivo``."""
        return Objetivo(
            id=modelo.id,
            descripcion=modelo.descripcion,
            meta_id=modelo.meta_id,
        )

    def crear(self, objetivo: Objetivo) -> Objetivo:
        """Persiste un Objetivo y devuelve la entidad con su ``id`` generado.

        Req 3.1: registrar un nuevo Objetivo asociado a su Meta padre
        (``meta_id``).
        """
        modelo = ObjetivoModel(
            descripcion=objetivo.descripcion, meta_id=objetivo.meta_id
        )
        self._session.add(modelo)
        self._session.flush()
        return self._a_entidad(modelo)

    def obtener_por_id(self, objetivo_id: int) -> Objetivo | None:
        """Devuelve el Objetivo con el ``id`` dado, o ``None`` si no existe."""
        modelo = self._session.get(ObjetivoModel, objetivo_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    def listar_por_padre(self, meta_id: int) -> list[Objetivo]:
        """Devuelve los Objetivos de la Meta dada; ``[]`` si no hay ninguno.

        Req 3.4/3.6: consultar la colección de Objetivos de una Meta.
        """
        modelos = self._session.scalars(
            select(ObjetivoModel).where(ObjetivoModel.meta_id == meta_id)
        ).all()
        return [self._a_entidad(m) for m in modelos]

    def padre_existe(self, meta_id: int) -> bool:
        """Indica si existe una Meta padre con el ``id`` dado.

        Soporta la validación "la Meta padre debe existir" (Req 8.2) aplicada en
        la capa de servicios antes de crear un Objetivo.
        """
        existe = self._session.scalar(
            select(MetaModel.id).where(MetaModel.id == meta_id)
        )
        return existe is not None
