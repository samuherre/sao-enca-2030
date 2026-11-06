"""Entidades de dominio de la jerarquía ENCA (puras, sin framework ni ORM).

Tarea 6.1 (tasks.md): define las cinco entidades de dominio confirmadas —
``Eje``, ``Meta``, ``Objetivo``, ``Indicador`` y ``Actividad`` — como objetos
de dominio **independientes de framework y ORM** (tech.md §28, structure.md
§28). Solo utilizan la biblioteca estándar de Python (``dataclasses``): no
importan SQLAlchemy, Pydantic ni FastAPI, de modo que las entidades se
instancian sin ninguna de esas dependencias.

Atributos confirmados (requirements.md Glosario; design.md "Data Models";
docs/data/conceptual-data-model.md §2):

- ``Eje``: ``id``, ``nombre``, ``descripcion`` (opcional). Es la raíz de la
  jerarquía y **no** tiene referencia a un padre.
- ``Meta``: ``id``, ``descripcion``, ``eje_id`` (referencia al Eje padre).
- ``Objetivo`` (Objetivo SMART): ``id``, ``descripcion``, ``meta_id``
  (referencia a la Meta padre).
- ``Indicador``: ``id``, ``nombre``, ``descripcion``, ``objetivo_id``
  (referencia al Objetivo padre).
- ``Actividad``: ``id``, ``descripcion``, ``indicador_id`` (referencia al
  Indicador padre).

Jerarquía confirmada (D-001 a D-004): Eje → Meta → Objetivo SMART → Indicador
→ Actividad.

Atributos **PENDING_VALIDATION** deliberadamente omitidos en esta Spec
(requirements.md "Atributos PENDING_VALIDATION por entidad", Req 4.7/5.8):

- Indicador: unidad de medida, valor objetivo, valor actual, fecha de medición,
  fuente/evidencia, estado.
- Actividad: responsable, fecha, estado, evidencia/fuente, región.

Sobre ``id``: la clave primaria es un entero autoincremental generado por
PostgreSQL (design.md "Identificadores — TECHNICAL_DECISION"). Una entidad de
dominio puede existir **antes** de ser persistida (todavía sin ``id``
asignado), por lo que ``id`` es opcional (``None`` cuando aún no se ha
generado). Las referencias al padre (``*_id``) también admiten ``None`` para
representar una entidad hija en construcción, antes de resolver/asignar su
padre; la regla de aplicación "el padre debe existir" se valida en la capa de
servicios (tareas 9.x), no en la entidad.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Eje:
    """Eje estratégico: nivel raíz de la jerarquía ENCA (D-001).

    Atributos confirmados (conceptual-data-model.md §2.1):

    - ``id``: identificador único (entero autoincremental). ``None`` mientras
      la entidad no ha sido persistida.
    - ``nombre``: nombre del Eje (campo obligatorio confirmado).
    - ``descripcion``: descripción del Eje (campo **opcional** confirmado).

    El Eje es la raíz de la jerarquía y, por diseño, **no** tiene referencia a
    una entidad padre (Req 6.3).
    """

    nombre: str
    descripcion: str | None = None
    id: int | None = None


@dataclass
class Meta:
    """Meta: resultado esperado dentro de un Eje (D-001).

    Atributos confirmados (conceptual-data-model.md §2.2):

    - ``id``: identificador único (entero autoincremental). ``None`` antes de
      persistir.
    - ``descripcion``: enunciado/descripción de la Meta (obligatorio).
    - ``eje_id``: referencia al Eje padre inmediato.
    """

    descripcion: str
    eje_id: int | None = None
    id: int | None = None


@dataclass
class Objetivo:
    """Objetivo SMART: objetivo específico asociado a una Meta (D-002).

    Atributos confirmados (conceptual-data-model.md §2.3):

    - ``id``: identificador único (entero autoincremental). ``None`` antes de
      persistir.
    - ``descripcion``: enunciado/descripción del Objetivo (obligatorio).
    - ``meta_id``: referencia a la Meta padre inmediata.
    """

    descripcion: str
    meta_id: int | None = None
    id: int | None = None


@dataclass
class Indicador:
    """Indicador: medida de seguimiento asociada a un Objetivo SMART (D-003).

    Atributos confirmados (conceptual-data-model.md §2.4):

    - ``id``: identificador único (entero autoincremental). ``None`` antes de
      persistir.
    - ``nombre``: nombre del Indicador (obligatorio).
    - ``descripcion``: descripción del Indicador (obligatorio).
    - ``objetivo_id``: referencia al Objetivo padre inmediato.

    Los atributos de seguimiento/evidencia del Indicador (unidad de medida,
    valor objetivo, valor actual, fecha de medición, fuente/evidencia, estado)
    son PENDING_VALIDATION y **no** se incluyen en esta entidad (Req 4.7, 9.1).
    """

    nombre: str
    descripcion: str
    objetivo_id: int | None = None
    id: int | None = None


@dataclass
class Actividad:
    """Actividad: acción propuesta asociada a un Indicador (D-004).

    Atributos confirmados (conceptual-data-model.md §2.5):

    - ``id``: identificador único (entero autoincremental). ``None`` antes de
      persistir.
    - ``descripcion``: nombre/descripción de la Actividad (obligatorio).
    - ``indicador_id``: referencia al Indicador padre inmediato.

    Los atributos de seguimiento/evidencia de la Actividad (responsable, fecha,
    estado, evidencia/fuente, región) son PENDING_VALIDATION y **no** se
    incluyen en esta entidad (Req 5.8, 9.2).
    """

    descripcion: str
    indicador_id: int | None = None
    id: int | None = None
