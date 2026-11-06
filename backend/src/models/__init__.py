"""Capa `models` del backend — modelos ORM (persistencia) de SQLAlchemy.

Contiene la ``Base`` declarativa compartida (``base.py``) y los modelos ORM de
cada entidad de la jerarquía ENCA (tarea 7): ``EjeModel``, ``MetaModel``,
``ObjetivoModel``, ``IndicadorModel`` y ``ActividadModel``.

Todos los modelos se importan aquí para que sus tablas se registren en
``Base.metadata`` y Alembic las detecte en ``revision --autogenerate``
(tech.md §10). El ``env.py`` de Alembic importa este paquete con esa finalidad.
"""

from backend.src.models.actividad import ActividadModel
from backend.src.models.base import Base
from backend.src.models.eje import EjeModel
from backend.src.models.indicador import IndicadorModel
from backend.src.models.meta import MetaModel
from backend.src.models.objetivo import ObjetivoModel

__all__ = [
    "Base",
    "EjeModel",
    "MetaModel",
    "ObjetivoModel",
    "IndicadorModel",
    "ActividadModel",
]
