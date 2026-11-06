"""Repositorio de acceso a datos del Eje estratégico (nivel raíz).

Tarea 8.1 (tasks.md): implementa el ``EjeRepository`` con las operaciones
``crear``, ``obtener_por_id`` y ``listar_todos``. Es el único punto que conoce
consultas y sesiones de SQLAlchemy para la entidad Eje (design.md
"Architecture"). Devuelve entidades de dominio (``backend.src.domain.entities``),
mapeando desde/hacia el modelo ORM ``EjeModel`` (``backend.src.models``).

El Eje es la raíz de la jerarquía (D-001) y, por tanto, **no** tiene referencia
a un padre: no se implementan ``listar_por_padre`` ni ``padre_existe`` (Req 6.3).

Requisitos: 1.1 (crear Eje), 1.3 (obtener Eje por id), 1.4 (listar todos los
Ejes, devolviendo ``[]`` cuando no hay ninguno).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.src.domain.entities import Eje
from backend.src.models.eje import EjeModel


class EjeRepository:
    """Acceso a datos del Eje mediante SQLAlchemy.

    Recibe una ``Session`` de SQLAlchemy por construcción y la utiliza para
    todas sus operaciones. No gestiona el ciclo de vida de la sesión (apertura
    y cierre), que corresponde a la capa superior (dependencia ``get_db`` en
    FastAPI).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _a_entidad(modelo: EjeModel) -> Eje:
        """Mapea un ``EjeModel`` (ORM) a la entidad de dominio ``Eje``."""
        return Eje(
            id=modelo.id,
            nombre=modelo.nombre,
            descripcion=modelo.descripcion,
        )

    def crear(self, eje: Eje) -> Eje:
        """Persiste un Eje y devuelve la entidad con su ``id`` generado.

        Req 1.1: registrar un nuevo Eje. El ``id`` se genera en PostgreSQL
        (entero autoincremental); tras el ``flush`` queda disponible en el
        modelo y se refleja en la entidad devuelta.
        """
        modelo = EjeModel(nombre=eje.nombre, descripcion=eje.descripcion)
        self._session.add(modelo)
        self._session.flush()
        return self._a_entidad(modelo)

    def obtener_por_id(self, eje_id: int) -> Eje | None:
        """Devuelve el Eje con el ``id`` dado, o ``None`` si no existe.

        Req 1.3: consultar un Eje por su identificador.
        """
        modelo = self._session.get(EjeModel, eje_id)
        if modelo is None:
            return None
        return self._a_entidad(modelo)

    def listar_todos(self) -> list[Eje]:
        """Devuelve todos los Ejes; lista vacía (``[]``) si no hay ninguno.

        Req 1.4: consultar la colección completa de Ejes.
        """
        modelos = self._session.scalars(select(EjeModel)).all()
        return [self._a_entidad(m) for m in modelos]
