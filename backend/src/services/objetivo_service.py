"""Servicio de aplicación del Objetivo SMART (tercer nivel de la jerarquía).

Tarea 9.3 (tasks.md): implementa el ``ObjetivoService``, que orquesta los casos
de uso de **crear** y **consultar** Objetivos asociados a una Meta. Pertenece a
la capa de servicios (``design.md`` "Architecture"): coordina los repositorios y
aplica reglas de aplicación, **sin conocer FastAPI ni HTTP**. Recibe y devuelve
**entidades de dominio** y lanza **excepciones de dominio**.

Regla de aplicación clave (Req 3.2, 8.2): antes de crear un Objetivo se verifica
que la Meta padre exista; si no existe se lanza ``InvalidParentReferenceError``
y no se persiste ningún Objetivo.

La validación de forma de ``descripcion`` (no nula/ no vacía tras recortar
espacios) se delega a los schemas Pydantic en la capa de rutas (Req 3.3).

Requisitos: 3.1 (crear Objetivo bajo una Meta), 3.2 (Meta inexistente →
referencia inválida), 3.4/3.5 (listar Objetivos de una Meta, incluyendo ``[]``,
o 404 si la Meta no existe), 3.6 (obtener Objetivo por id), 3.7 (id inexistente
→ ``NotFoundError``), 8.2 (integridad referencial de la referencia al padre).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.domain.entities import Objetivo
from backend.src.domain.exceptions import (
    InvalidParentReferenceError,
    NotFoundError,
)
from backend.src.repositories.meta_repository import MetaRepository
from backend.src.repositories.objetivo_repository import ObjetivoRepository


class ObjetivoService:
    """Casos de uso del Objetivo: creación (bajo una Meta) y consulta.

    Recibe una ``Session`` de SQLAlchemy y construye sus repositorios sobre
    ella. No gestiona el ciclo de vida de la sesión (corresponde a la capa
    superior).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repositorio = ObjetivoRepository(session)
        self._meta_repositorio = MetaRepository(session)

    def crear(self, meta_id: int, datos: Objetivo) -> Objetivo:
        """Crea un Objetivo bajo la Meta ``meta_id`` y lo devuelve con su ``id``.

        Verifica primero que la Meta padre exista (Req 3.2, 8.2). La referencia
        al padre se toma de la ruta anidada, no del cuerpo, y se asigna aquí.

        :raises InvalidParentReferenceError: si la Meta ``meta_id`` no existe; en
            tal caso no se persiste ningún Objetivo.
        """
        if not self._repositorio.padre_existe(meta_id):
            raise InvalidParentReferenceError(
                f"No existe una Meta con id {meta_id} a la que asociar el "
                "Objetivo."
            )
        datos.meta_id = meta_id
        return self._repositorio.crear(datos)

    def obtener(self, objetivo_id: int) -> Objetivo:
        """Devuelve el Objetivo con el ``id`` dado.

        Req 3.6: consultar un Objetivo por su identificador, con la referencia
        a su Meta.

        :raises NotFoundError: si no existe ningún Objetivo con ese ``id``
            (Req 3.7).
        """
        objetivo = self._repositorio.obtener_por_id(objetivo_id)
        if objetivo is None:
            raise NotFoundError(
                f"No existe un Objetivo con id {objetivo_id}."
            )
        return objetivo

    def listar_por_meta(self, meta_id: int) -> list[Objetivo]:
        """Devuelve los Objetivos de la Meta ``meta_id``; ``[]`` si no tiene.

        Req 3.4: consultar la colección de Objetivos de una Meta existente,
        devolviendo una colección vacía sin error cuando no tiene Objetivos.

        :raises NotFoundError: si la Meta ``meta_id`` no existe (Req 3.5).
        """
        if not self._repositorio.padre_existe(meta_id):
            raise NotFoundError(f"No existe una Meta con id {meta_id}.")
        return self._repositorio.listar_por_padre(meta_id)
