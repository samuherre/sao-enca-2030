"""Contratos Pydantic del Objetivo SMART (tarea 10.4).

Define los schemas de **entrada** (``ObjetivoCreate``) y de **salida**
(``ObjetivoResponse``) del tercer nivel de la jerarquía ENCA, conforme a
``design.md`` ("Contratos Pydantic") y a los requisitos 3.1, 3.6 y 6.2.

Reglas aplicadas:

- Ambos contratos heredan de :class:`backend.src.schemas.base.SchemaBase`
  (``extra="forbid"``; Req 9.4).
- ``ObjetivoCreate.descripcion`` es obligatorio: usa :data:`TextoRequerido`
  (Req 3.3). El ``meta_id`` se toma de la ruta ``/metas/{meta_id}/objetivos``,
  no del cuerpo; enviarlo en el cuerpo produce 422 por campos extra.
- ``ObjetivoResponse`` expone ``id``, ``descripcion`` y ``meta_id`` (navegación
  hija→padre, Req 6.2). Se habilita ``from_attributes=True``.

No contiene atributos PENDING_VALIDATION.
"""

from __future__ import annotations

from pydantic import ConfigDict

from backend.src.schemas.base import SchemaBase, TextoRequerido


class ObjetivoCreate(SchemaBase):
    """Contrato de entrada para crear un Objetivo bajo una Meta.

    :ivar descripcion: Descripción del Objetivo. Obligatoria (no nula, no vacía
        tras ``strip``). El ``meta_id`` se toma de la ruta, no del cuerpo.
    """

    descripcion: TextoRequerido


class ObjetivoResponse(SchemaBase):
    """Contrato de salida de un Objetivo.

    :ivar id: Identificador único del Objetivo.
    :ivar descripcion: Descripción del Objetivo.
    :ivar meta_id: Identificador de la Meta padre (navegación hija→padre, Req 6.2).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    descripcion: str
    meta_id: int
