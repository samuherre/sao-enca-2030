"""Contratos Pydantic del árbol jerárquico (tarea 10.7).

Define el contrato de salida del endpoint de navegación
``GET /ejes/{eje_id}/arbol``: el árbol anidado completo de los cinco niveles de
la jerarquía ENCA (Eje → Meta → Objetivo → Indicador → Actividad), conforme a
``design.md`` ("Schema del árbol jerárquico") y a los requisitos 6.1 y 6.4.

Reglas aplicadas:

- Todos los nodos heredan de :class:`backend.src.schemas.base.SchemaBase`
  (``extra="forbid"``).
- Cada nodo expone sus **campos confirmados** y la **lista de hijos** del nivel
  inmediatamente inferior. Las listas de hijos pueden ser vacías (``[]``) cuando
  el nodo no tiene hijos; por defecto son ``[]`` (Req 6.4).
- En el árbol, la referencia al padre es **implícita por el anidamiento**, por
  lo que los nodos anidados **omiten** el ``*_id`` del padre para evitar
  redundancia (design.md "Schema del árbol jerárquico"). El Eje raíz tampoco
  incluye referencia a padre (Req 6.3).
- Se habilita ``from_attributes=True`` en cada nodo para serializar desde las
  entidades de dominio ensambladas por el ``HierarchyService``.

No contiene atributos PENDING_VALIDATION.
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase


class ActividadArbol(SchemaBase):
    """Nodo hoja del árbol: Actividad (nivel 5).

    :ivar id: Identificador único de la Actividad.
    :ivar descripcion: Descripción de la Actividad.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str


class IndicadorArbol(SchemaBase):
    """Nodo del árbol: Indicador (nivel 4) con sus Actividades.

    :ivar id: Identificador único del Indicador.
    :ivar nombre: Nombre del Indicador.
    :ivar descripcion: Descripción del Indicador.
    :ivar actividades: Actividades hijas (puede ser ``[]``).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    actividades: list[ActividadArbol] = []


class ObjetivoArbol(SchemaBase):
    """Nodo del árbol: Objetivo SMART (nivel 3) con sus Indicadores.

    :ivar id: Identificador único del Objetivo.
    :ivar descripcion: Descripción del Objetivo.
    :ivar indicadores: Indicadores hijos (puede ser ``[]``).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str
    indicadores: list[IndicadorArbol] = []


class MetaArbol(SchemaBase):
    """Nodo del árbol: Meta (nivel 2) con sus Objetivos.

    :ivar id: Identificador único de la Meta.
    :ivar descripcion: Descripción de la Meta.
    :ivar objetivos: Objetivos hijos (puede ser ``[]``).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str
    objetivos: list[ObjetivoArbol] = []


class EjeArbolResponse(SchemaBase):
    """Nodo raíz del árbol: Eje (nivel 1) con sus Metas.

    No incluye referencia a padre: el Eje es la raíz (Req 6.3).

    :ivar id: Identificador único del Eje.
    :ivar nombre: Nombre del Eje.
    :ivar descripcion: Descripción del Eje (puede ser nula).
    :ivar metas: Metas hijas (puede ser ``[]``).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    nombre: str
    descripcion: str | None = None
    metas: list[MetaArbol] = []
