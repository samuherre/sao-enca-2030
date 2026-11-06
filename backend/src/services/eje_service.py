"""Servicio de aplicación del Eje estratégico (nivel raíz de la jerarquía).

Tarea 9.1 (tasks.md): implementa el ``EjeService``, que orquesta los casos de
uso de **crear** y **consultar** Ejes. Pertenece a la capa de servicios
(``backend/src/services/``) descrita en ``design.md`` ("Architecture"): coordina
el repositorio y aplica reglas de aplicación, **sin conocer FastAPI ni HTTP**.
Recibe y devuelve **entidades de dominio** (``backend.src.domain.entities``) y
lanza **excepciones de dominio** (``backend.src.domain.exceptions``); la
traducción a códigos HTTP corresponde a la capa de rutas.

El Eje es la raíz de la jerarquía (D-001) y no tiene padre, por lo que su
servicio no aplica la regla "el padre debe existir".

La validación de forma de los campos obligatorios (``nombre`` no nulo/ no vacío
tras recortar espacios) se delega a los schemas Pydantic en la capa de rutas
(design.md "Contratos Pydantic"; Req 1.2); por eso este servicio no la repite.

Requisitos: 1.1 (crear Eje), 1.3 (listar Ejes), 1.4 (obtener Eje por id),
1.5 (id inexistente → ``NotFoundError``).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.src.domain.entities import Eje
from backend.src.domain.exceptions import NotFoundError
from backend.src.repositories.eje_repository import EjeRepository


class EjeService:
    """Casos de uso del Eje: creación y consulta.

    Recibe una ``Session`` de SQLAlchemy y construye su propio repositorio sobre
    ella. No gestiona el ciclo de vida de la sesión (apertura, commit o cierre),
    que corresponde a la capa superior (dependencia ``get_db`` en FastAPI).
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repositorio = EjeRepository(session)

    def crear(self, datos: Eje) -> Eje:
        """Crea un Eje y devuelve la entidad con su ``id`` generado.

        Req 1.1: registrar un nuevo Eje. La validación de ``nombre`` (no nulo,
        no vacío) la garantiza el contrato Pydantic antes de llegar aquí.
        """
        return self._repositorio.crear(datos)

    def obtener(self, eje_id: int) -> Eje:
        """Devuelve el Eje con el ``id`` dado.

        Req 1.4: consultar un Eje por su identificador.

        :raises NotFoundError: si no existe ningún Eje con ese ``id`` (Req 1.5).
        """
        eje = self._repositorio.obtener_por_id(eje_id)
        if eje is None:
            raise NotFoundError(f"No existe un Eje con id {eje_id}.")
        return eje

    def listar(self) -> list[Eje]:
        """Devuelve todos los Ejes; lista vacía (``[]``) si no hay ninguno.

        Req 1.3: consultar la colección completa de Ejes.
        """
        return self._repositorio.listar_todos()
