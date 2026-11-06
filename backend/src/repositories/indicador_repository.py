"""Repositorio de acceso a datos del Indicador (cuarto nivel de la jerarquía).

Tarea 8.4 (tasks.md): implementa el ``IndicadorRepository`` con las operaciones
``crear``, ``obtener_por_id``, ``listar_por_padre`` (por ``objetivo_id``) y
``padre_existe`` (``objetivo_id``). Es el único punto que conoce consultas y
sesiones de SQLAlchemy para la entidad Indicador (design.md "Architecture").
Devuelve entidades de dominio (``backend.src.domain.entities``), mapeando
desde/hacia el modelo ORM ``IndicadorModel`` (``backend.src.models``).

El Indicador es hijo del Objetivo SMART (D-003): su padre inmediato es un
Objetivo identificado por ``objetivo_id`` (FK NOT NULL, Req 8.1). Solo se
manejan los atributos confirmados (``nombre``, ``descripcion``); los atributos
PENDING_VALIDATION no existen en el modelo ni se mapean (Req 4.7, 9.1).

Requisitos: 4.1 (crear Indicador bajo un Objetivo), 4.4/4.5 (listar Indicadores
de un Objetivo, incluyendo ``[]``, e identificar el Objetivo padre), 8.1
(integridad referencial). ``padre_existe`` sostiene la regla de aplicación "el
Objetivo padre debe existir" aplicada en la capa de servicios (Req 8.2).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.domain.entities import Indicador
from backend.src.models.indicador import IndicadorModel
from backend.src.models.objetivo import ObjetivoModel


class IndicadorRepository:
    """Acceso a datos del Indicador mediante SQLAlchemy.

    Recibe una ``Session`` de SQLAlchemy por construcción. No gestiona el ciclo
    de vida de la sesión (corresponde a la capa superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _a_entidad(modelo: IndicadorModel) -> Indicador:
        """Mapea un ``IndicadorModel`` (ORM) a la entidad ``Indicador``."""
        return Indicador(
            id=modelo.id,
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
            objetivo_id=modelo.objetivo_id,
        )

    def crear(self, indicador: Indicador) -> Indicador:
        """Persiste un Indicador y devuelve la entidad con su ``id`` generado.

        Req 4.1: registrar un nuevo Indicador asociado a su Objetivo padre
        (``objetivo_id``).
        """
        modelo = IndicadorModel(
            nombre=indicador.nombre,
            descripcion=indicador.descripcion,
            objetivo_id=indicador.objetivo_id,
        )
        self._session.add(modelo)
        self._session.flush()
        return self._a_entidad(modelo)

    def obtener_por_id(self, indicador_id: int) -> Indicador | None:
        """Devuelve el Indicador con el ``id`` dado, o ``None`` si no existe."""
        modelo = self._session.get(IndicadorModel, indicador_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    def listar_por_padre(self, objetivo_id: int) -> list[Indicador]:
        """Devuelve los Indicadores del Objetivo dado; ``[]`` si no hay ninguno.

        Req 4.4/4.5: consultar la colección de Indicadores de un Objetivo.
        """
        modelos = self._session.scalars(
            select(IndicadorModel).where(
                IndicadorModel.objetivo_id == objetivo_id
            )
        ).all()
        return [self._a_entidad(m) for m in modelos]

    def padre_existe(self, objetivo_id: int) -> bool:
        """Indica si existe un Objetivo padre con el ``id`` dado.

        Soporta la validación "el Objetivo padre debe existir" (Req 8.2)
        aplicada en la capa de servicios antes de crear un Indicador.
        """
        existe = self._session.scalar(
            select(ObjetivoModel.id).where(ObjetivoModel.id == objetivo_id)
        )
        return existe is not None
