"""Servicio de aplicación del Indicador (cuarto nivel de la jerarquía).

Tarea 9.4 (tasks.md): implementa el ``IndicadorService``, que orquesta los
casos de uso de **crear** y **consultar** Indicadores asociados a un Objetivo
SMART. Pertenece a la capa de servicios (``design.md`` "Architecture"): coordina
los repositorios y aplica reglas de aplicación, **sin conocer FastAPI ni HTTP**.
Recibe y devuelve **entidades de dominio** y lanza **excepciones de dominio**.

Regla de aplicación clave (Req 4.2, 8.2): antes de crear un Indicador se
verifica que el Objetivo padre exista; si no existe se lanza
``InvalidParentReferenceError`` y no se persiste ningún Indicador.

Solo se manejan los atributos confirmados (``nombre``, ``descripcion``); los
atributos PENDING_VALIDATION del Indicador no se implementan ni se exponen
(Req 4.7, 9.1). La validación de forma de ``nombre`` (no nulo/ no vacío tras
recortar espacios) se delega a los schemas Pydantic en la capa de rutas
(Req 4.3).

Requisitos: 4.1 (crear Indicador bajo un Objetivo), 4.2 (Objetivo inexistente →
referencia inválida), 4.4 (listar Indicadores de un Objetivo, incluyendo ``[]``),
4.5 (obtener Indicador por id), 4.6 (id inexistente → ``NotFoundError``), 8.2
(integridad referencial de la referencia al padre).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.domain.entities import Indicador
from backend.src.domain.exceptions import (
    InvalidParentReferenceError,
    NotFoundError,
)
from backend.src.repositories.indicador_repository import IndicadorRepository
from backend.src.repositories.objetivo_repository import ObjetivoRepository


class IndicadorService:
    """Casos de uso del Indicador: creación (bajo un Objetivo) y consulta.

    Recibe una ``Session`` de SQLAlchemy y construye sus repositorios sobre
    ella. No gestiona el ciclo de vida de la sesión (corresponde a la capa
    superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repositorio = IndicadorRepository(session)
        self._objetivo_repositorio = ObjetivoRepository(session)

    def crear(self, objetivo_id: int, datos: Indicador) -> Indicador:
        """Crea un Indicador bajo el Objetivo ``objetivo_id`` y lo devuelve.

        Verifica primero que el Objetivo padre exista (Req 4.2, 8.2). La
        referencia al padre se toma de la ruta anidada, no del cuerpo, y se
        asigna aquí.

        :raises InvalidParentReferenceError: si el Objetivo ``objetivo_id`` no
            existe; en tal caso no se persiste ningún Indicador.
        """
        if not self._repositorio.padre_existe(objetivo_id):
            raise InvalidParentReferenceError(
                f"No existe un Objetivo con id {objetivo_id} al que asociar el "
                "Indicador."
            )
        datos.objetivo_id = objetivo_id
        return self._repositorio.crear(datos)

    def obtener(self, indicador_id: int) -> Indicador:
        """Devuelve el Indicador con el ``id`` dado.

        Req 4.5: consultar un Indicador por su identificador, con la referencia
        a su Objetivo.

        :raises NotFoundError: si no existe ningún Indicador con ese ``id``
            (Req 4.6).
        """
        indicador = self._repositorio.obtener_por_id(indicador_id)
        if indicador is None:
            raise NotFoundError(
                f"No existe un Indicador con id {indicador_id}."
            )
        return indicador

    def listar_por_objetivo(self, objetivo_id: int) -> list[Indicador]:
        """Devuelve los Indicadores del Objetivo ``objetivo_id``; ``[]`` si no.

        Req 4.4: consultar la colección de Indicadores de un Objetivo existente,
        devolviendo una colección vacía sin error cuando no tiene Indicadores.

        :raises NotFoundError: si el Objetivo ``objetivo_id`` no existe (se
            consulta la colección de un recurso padre inexistente).
        """
        if not self._repositorio.padre_existe(objetivo_id):
            raise NotFoundError(
                f"No existe un Objetivo con id {objetivo_id}."
            )
        return self._repositorio.listar_por_padre(objetivo_id)
