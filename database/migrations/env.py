"""Entorno de ejecución de migraciones de Alembic — SAO ENCA 2030.

Este `env.py` adapta el entorno estándar de Alembic a las decisiones del
proyecto (tech.md §10, §19, §20; structure.md §16):

- La cadena de conexión se toma de la variable de entorno ``DATABASE_URL``
  mediante los settings del backend (``backend.src.core.config``). NO se lee
  de ``alembic.ini`` ni se hardcodea ninguna credencial.
- ``target_metadata`` es ``Base.metadata`` (``backend.src.models.base``), de modo
  que ``alembic revision --autogenerate`` compara el esquema de la base con los
  modelos ORM registrados. Mientras no existan modelos (tarea 7), el metadata
  está vacío y el autogenerate produce una migración vacía sin error de
  configuración.
- El esquema físico se gestiona EXCLUSIVAMENTE con migraciones versionadas; no
  se crea SQL manual (tech.md §10).
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Resolución de imports del proyecto
# ---------------------------------------------------------------------------
# Aunque alembic.ini define `prepend_sys_path = ..`, se asegura aquí que la
# raíz del proyecto esté en sys.path para que los imports `backend.src...`
# resuelvan sin depender del directorio de invocación.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.core.config import get_settings  # noqa: E402
from backend.src.models.base import Base  # noqa: E402

# Importa el paquete de modelos para que todas las tablas se registren en
# `Base.metadata` antes de que Alembic calcule el autogenerate. Hoy el paquete
# `models` solo contiene la Base declarativa; cuando se añadan los modelos ORM
# (tarea 7) deberán quedar importados aquí (p. ej. desde `backend.src.models`)
# para que el autogenerate los detecte.
import backend.src.models  # noqa: E402,F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData de los modelos ORM: fuente para el autogenerate de migraciones.
target_metadata = Base.metadata


def _database_url() -> str:
    """Devuelve la cadena de conexión desde la variable de entorno.

    Se obtiene de ``DATABASE_URL`` vía los settings del backend (tech.md §19).
    Si falta, ``get_settings()`` falla de forma controlada con un error de
    validación comprensible, en lugar de usar una credencial inventada.
    """
    return get_settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Ejecuta las migraciones en modo 'offline'.

    Configura el contexto solo con una URL (sin Engine). La URL se toma de
    ``DATABASE_URL`` del entorno, no de ``alembic.ini``.
    """
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta las migraciones en modo 'online'.

    Crea un Engine a partir de la configuración de Alembic, inyectando la
    ``sqlalchemy.url`` desde ``DATABASE_URL`` del entorno en tiempo de ejecución.
    """
    configuration = config.get_section(config.config_ini_section, {})
    # Inyecta la URL desde el entorno (no se persiste en alembic.ini).
    configuration["sqlalchemy.url"] = _database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
