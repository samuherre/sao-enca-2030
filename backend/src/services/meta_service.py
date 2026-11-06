"""Servicio de aplicación de la Meta (segundo nivel de la jerarquía).

Tarea 9.2 (tasks.md): implementa el ``MetaService``, que orquesta los casos de
uso de **crear** y **consultar** Metas asociadas a un Eje. Pertenece a la capa
de servicios (``design.md`` "Architecture"): coordina los repositorios y aplica
reglas de aplicación, **sin conocer FastAPI ni HTTP**. Recibe y devuelve
**entidades de dominio** y lanza **excepciones de dominio**; la traducción a
códigos HTTP corresponde a la capa de rutas.

Regla de aplicación clave (Req 2.2, 8.2): antes de crear una Meta se verifica
que el Eje padre exista; si no existe se lanza ``InvalidParentReferenceError``
y no se persiste ninguna Meta.

La validación de forma de ``descripcion`` (no nula/ no vacía tras recortar
espacios) se delega a los schemas Pydantic en la capa de rutas (Req 2.3).

Requisitos: 2.1 (crear Meta bajo un Eje), 2.2 (Eje inexistente → referencia
inválida), 2.4/2.5 (listar Metas de un Eje, incluyendo ``[]``), 2.6 (obtener
Meta por id con referencia al Eje), 2.7 (id inexistente → ``NotFoundError``),
8.2 (integridad referencial de la referencia al padre).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.domain.entities import Meta
from backend.src.domain.exceptions import (
    InvalidParentReferenceError,
    NotFoundError,
)
from backend.src.repositories.eje_repository import EjeRepository
from backend.src.repositories.meta_repository import MetaRepository


class MetaService:
    """Casos de uso de la Meta: creación (bajo un Eje) y consulta.

    Recibe una ``Session`` de SQLAlchemy y construye sus repositorios sobre
    ella. No gestiona el ciclo de vida de la sesión (corresponde a la capa
    superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repositorio = MetaRepository(session)
        self._eje_repositorio = EjeRepository(session)

    def crear(self, eje_id: int, datos: Meta) -> Meta:
        """Crea una Meta bajo el Eje ``eje_id`` y la devuelve con su ``id``.

        Verifica primero que el Eje padre exista (Req 2.2, 8.2). La referencia
        al padre se toma de la ruta anidada, no del cuerpo, y se asigna aquí.

        :raises InvalidParentReferenceError: si el Eje ``eje_id`` no existe; en
            tal caso no se persiste ninguna Meta.
        """
        if not self._repositorio.padre_existe(eje_id):
            raise InvalidParentReferenceError(
                f"No existe un Eje con id {eje_id} al que asociar la Meta."
            )
        datos.eje_id = eje_id
        return self._repositorio.crear(datos)

    def obtener(self, meta_id: int) -> Meta:
        """Devuelve la Meta con el ``id`` dado.

        Req 2.6: consultar una Meta por su identificador, con la referencia a
        su Eje.

        :raises NotFoundError: si no existe ninguna Meta con ese ``id`` (Req 2.7).
        """
        meta = self._repositorio.obtener_por_id(meta_id)
        if meta is None:
            raise NotFoundError(f"No existe una Meta con id {meta_id}.")
        return meta

    def listar_por_eje(self, eje_id: int) -> list[Meta]:
        """Devuelve las Metas del Eje ``eje_id``; ``[]`` si no tiene ninguna.

        Req 2.4/2.5: consultar la colección de Metas de un Eje existente,
        devolviendo una colección vacía sin error cuando el Eje no tiene Metas.

        :raises NotFoundError: si el Eje ``eje_id`` no existe (se consulta la
            colección de un recurso padre inexistente).
        """
        if not self._repositorio.padre_existe(eje_id):
            raise NotFoundError(f"No existe un Eje con id {eje_id}.")
        return self._repositorio.listar_por_padre(eje_id)
