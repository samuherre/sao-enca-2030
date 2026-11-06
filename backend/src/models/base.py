"""Base declarativa de SQLAlchemy compartida por los modelos ORM.

Define la clase `Base` (estilo declarativo de SQLAlchemy 2.x, mediante
`DeclarativeBase`) de la que heredan todos los modelos de persistencia del
backend (`backend/src/models/`). Todas las tablas definidas por los modelos se
registran en `Base.metadata`, que a su vez es utilizado por Alembic como
`target_metadata` para generar y aplicar migraciones versionadas (tech.md §10).

Este módulo pertenece exclusivamente a la capa de persistencia y no contiene
lógica de dominio ni dependencias de FastAPI/Pydantic (tech.md §28,
structure.md §28).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa común a todos los modelos ORM del proyecto.

    Los modelos de persistencia (p. ej. `EjeModel`, `MetaModel`, ...) heredan de
    esta clase. Su `metadata` agrupa el esquema de todas las tablas registradas
    y es la fuente para las migraciones de Alembic.
    """
