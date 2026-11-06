"""Servicio de aplicación de la Actividad (quinto y último nivel).

Tarea 9.5 (tasks.md): implementa el ``ActividadService``, que orquesta los
casos de uso de **crear** y **consultar** Actividades asociadas a un Indicador.
Pertenece a la capa de servicios (``design.md`` "Architecture"): coordina los
repositorios y aplica reglas de aplicación, **sin conocer FastAPI ni HTTP**.
Recibe y devuelve **entidades de dominio** y lanza **excepciones de dominio**.

Regla de aplicación clave (Req 5.2, 8.2): antes de crear una Actividad se
verifica que el Indicador padre exista; si no existe se lanza
``InvalidParentReferenceError`` y no se persiste ninguna Actividad.

Solo se maneja el atributo confirmado (``descripcion``); los atributos
PENDING_VALIDATION de la Actividad no se implementan ni se exponen (Req 5.8,
9.2). La validación de forma de ``descripcion`` (no nula/ no vacía tras recortar
espacios) se delega a los schemas Pydantic en la capa de rutas (Req 5.3).

Requisitos: 5.1 (crear Actividad bajo un Indicador), 5.2 (Indicador inexistente
→ referencia inválida), 5.4/5.5 (listar Actividades de un Indicador, incluyendo
``[]``), 5.6 (obtener Actividad por id), 5.7 (id inexistente → ``NotFoundError``),
8.2 (integridad referencial de la referencia al padre).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.domain.entities import Actividad
from backend.src.domain.exceptions import (
    InvalidParentReferenceError,
    NotFoundError,
)
from backend.src.repositories.actividad_repository import ActividadRepository
from backend.src.repositories.indicador_repository import IndicadorRepository


class ActividadService:
    """Casos de uso de la Actividad: creación (bajo un Indicador) y consulta.

    Recibe una ``Session`` de SQLAlchemy y construye sus repositorios sobre
    ella. No gestiona el ciclo de vida de la sesión (corresponde a la capa
    superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repositorio = ActividadRepository(session)
        self._indicador_repositorio = IndicadorRepository(session)

    def crear(self, indicador_id: int, datos: Actividad) -> Actividad:
        """Crea una Actividad bajo el Indicador ``indicador_id`` y la devuelve.

        Verifica primero que el Indicador padre exista (Req 5.2, 8.2). La
        referencia al padre se toma de la ruta anidada, no del cuerpo, y se
        asigna aquí.

        :raises InvalidParentReferenceError: si el Indicador ``indicador_id`` no
            existe; en tal caso no se persiste ninguna Actividad.
        """
        if not self._repositorio.padre_existe(indicador_id):
            raise InvalidParentReferenceError(
                f"No existe un Indicador con id {indicador_id} al que asociar "
                "la Actividad."
            )
        datos.indicador_id = indicador_id
        return self._repositorio.crear(datos)

    def obtener(self, actividad_id: int) -> Actividad:
        """Devuelve la Actividad con el ``id`` dado.

        Req 5.6: consultar una Actividad por su identificador, con la referencia
        a su Indicador.

        :raises NotFoundError: si no existe ninguna Actividad con ese ``id``
            (Req 5.7).
        """
        actividad = self._repositorio.obtener_por_id(actividad_id)
        if actividad is None:
            raise NotFoundError(
                f"No existe una Actividad con id {actividad_id}."
            )
        return actividad

    def listar_por_indicador(self, indicador_id: int) -> list[Actividad]:
        """Devuelve las Actividades del Indicador ``indicador_id``; ``[]`` si no.

        Req 5.4/5.5: consultar la colección de Actividades de un Indicador
        existente, devolviendo una colección vacía sin error cuando no tiene
        Actividades.

        :raises NotFoundError: si el Indicador ``indicador_id`` no existe (se
            consulta la colección de un recurso padre inexistente).
        """
        if not self._repositorio.padre_existe(indicador_id):
            raise NotFoundError(
                f"No existe un Indicador con id {indicador_id}."
            )
        return self._repositorio.listar_por_padre(indicador_id)
