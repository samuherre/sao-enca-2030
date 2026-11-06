"""Contratos Pydantic de la Actividad (tarea 10.6).

Define los schemas de **entrada** (``ActividadCreate``) y de **salida**
(``ActividadResponse``) del quinto nivel de la jerarquía ENCA, conforme a
``design.md`` ("Contratos Pydantic") y a los requisitos 5.1, 5.6, 5.8, 9.2 y 6.2.

Reglas aplicadas:

- Ambos contratos heredan de :class:`backend.src.schemas.base.SchemaBase`
  (``extra="forbid"``; Req 9.4).
- ``ActividadCreate.descripcion`` es obligatorio: usa :data:`TextoRequerido`
  (Req 5.3). El ``indicador_id`` se toma de la ruta
  ``/indicadores/{indicador_id}/actividades``, no del cuerpo.
- ``ActividadResponse`` expone ``id``, ``descripcion`` e ``indicador_id``
  (navegación hija→padre, Req 6.2). Se habilita ``from_attributes=True``.

**No** incluye ningún atributo PENDING_VALIDATION (responsable, fecha, estado,
evidencia/fuente, región) ni en el Create ni en el Response (Req 5.8, 9.2;
design.md "Columnas futuras no implementadas").
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase, TextoRequerido


class ActividadCreate(SchemaBase):
    """Contrato de entrada para crear una Actividad bajo un Indicador.

    :ivar descripcion: Descripción de la Actividad. Obligatoria (no nula, no
        vacía tras ``strip``). El ``indicador_id`` se toma de la ruta, no del
        cuerpo.
    """

    descripcion: TextoRequerido


class ActividadResponse(SchemaBase):
    """Contrato de salida de una Actividad.

    No expone atributos PENDING_VALIDATION (Req 5.8, 9.2).

    :ivar id: Identificador único de la Actividad.
    :ivar descripcion: Descripción de la Actividad.
    :ivar indicador_id: Identificador del Indicador padre (navegación hija→padre,
        Req 6.2).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str
    indicador_id: int
