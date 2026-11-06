"""Repositorio de acceso a datos de la Actividad (quinto y último nivel).

Tarea 8.5 (tasks.md): implementa el ``ActividadRepository`` con las operaciones
``crear``, ``obtener_por_id``, ``listar_por_padre`` (por ``indicador_id``) y
``padre_existe`` (``indicador_id``). Es el único punto que conoce consultas y
sesiones de SQLAlchemy para la entidad Actividad (design.md "Architecture").
Devuelve entidades de dominio (``backend.src.domain.entities``), mapeando
desde/hacia el modelo ORM ``ActividadModel`` (``backend.src.models``).

La Actividad es hija del Indicador (D-004): su padre inmediato es un Indicador
identificado por ``indicador_id`` (FK NOT NULL, Req 8.1). Solo se maneja el
atributo confirmado (``descripcion``); los atributos PENDING_VALIDATION no
existen en el modelo ni se mapean (Req 5.8, 9.2).

Requisitos: 5.1 (crear Actividad bajo un Indicador), 5.4/5.5 (listar
Actividades de un Indicador, incluyendo ``[]``), 5.6 (identificar el Indicador
padre), 8.1 (integridad referencial). ``padre_existe`` sostiene la regla de
aplicación "el Indicador padre debe existir" aplicada en la capa de servicios
(Req 8.2).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.domain.entities import Actividad
from backend.src.models.actividad import ActividadModel
from backend.src.models.indicador import IndicadorModel


class ActividadRepository:
    """Acceso a datos de la Actividad mediante SQLAlchemy.

    Recibe una ``Session`` de SQLAlchemy por construcción. No gestiona el ciclo
    de vida de la sesión (corresponde a la capa superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _a_entidad(modelo: ActividadModel) -> Actividad:
        """Mapea un ``ActividadModel`` (ORM) a la entidad ``Actividad``."""
        return Actividad(
            id=modelo.id,
            descripcion=modelo.descripcion,
            indicador_id=modelo.indicador_id,
        )

    def crear(self, actividad: Actividad) -> Actividad:
        """Persiste una Actividad y devuelve la entidad con su ``id`` generado.

        Req 5.1: registrar una nueva Actividad asociada a su Indicador padre
        (``indicador_id``).
        """
        modelo = ActividadModel(
            descripcion=actividad.descripcion,
            indicador_id=actividad.indicador_id,
        )
        self._session.add(modelo)
        self._session.flush()
        return self._a_entidad(modelo)

    def obtener_por_id(self, actividad_id: int) -> Actividad | None:
        """Devuelve la Actividad con el ``id`` dado, o ``None`` si no existe."""
        modelo = self._session.get(ActividadModel, actividad_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    def listar_por_padre(self, indicador_id: int) -> list[Actividad]:
        """Devuelve las Actividades del Indicador dado; ``[]`` si no hay ninguna.

        Req 5.4/5.5: consultar la colección de Actividades de un Indicador.
        """
        modelos = self._session.scalars(
            select(ActividadModel).where(
                ActividadModel.indicador_id == indicador_id
            )
        ).all()
        return [self._a_entidad(m) for m in modelos]

    def padre_existe(self, indicador_id: int) -> bool:
        """Indica si existe un Indicador padre con el ``id`` dado.

        Soporta la validación "el Indicador padre debe existir" (Req 8.2)
        aplicada en la capa de servicios antes de crear una Actividad.
        """
        existe = self._session.scalar(
            select(IndicadorModel.id).where(IndicadorModel.id == indicador_id)
        )
        return existe is not None
