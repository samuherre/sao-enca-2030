"""Configuración de la conexión a PostgreSQL (engine y sesión).

Tarea 3 (tasks.md): define el `engine` de SQLAlchemy, la factoría de sesiones
`SessionLocal` y la dependencia `get_db()` para FastAPI.

Principios del Steering técnico respetados:

- La conexión usa **exclusivamente** la variable de entorno `DATABASE_URL`
  (tech.md §19). No se inventan credenciales ni se hardcodea ningún secreto:
  la cadena de conexión se obtiene de `get_settings().DATABASE_URL`, que a su
  vez falla de forma controlada si la variable no está presente.
- Se usa SQLAlchemy 2.x (`sqlalchemy.orm.sessionmaker` / `Session`).
- La dependencia `get_db()` abre una sesión por petición y garantiza su cierre
  al terminar (incluso si ocurre una excepción), evitando fugas de conexiones.

Esta tarea NO crea tablas ni modelos; solo prepara el acceso a datos que será
consumido por los repositorios (capa `repositories/`).
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Crea (y cachea) el `engine` de SQLAlchemy a partir de `DATABASE_URL`.

    El `engine` administra el pool de conexiones a PostgreSQL. Se construye de
    forma perezosa y se cachea para reutilizar un único pool en toda la
    aplicación.

    La cadena de conexión se toma exclusivamente de la configuración basada en
    el entorno (`get_settings().DATABASE_URL`); si falta, la obtención de
    settings lanza un error de validación controlado antes de llegar aquí.

    - ``pool_pre_ping=True``: valida la conexión antes de usarla, evitando
      errores por conexiones caídas tras periodos de inactividad.
    - ``future=True``: habilita el estilo de API de SQLAlchemy 2.x.
    """
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )


# Factoría de sesiones. `autoflush=False` y `autocommit=False` siguen el
# comportamiento recomendado en SQLAlchemy 2.x: el control de la transacción es
# explícito (commit/rollback) y queda a cargo de la capa que use la sesión.
SessionLocal = sessionmaker(
    bind=get_engine(),
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI que entrega una sesión por petición.

    Abre una sesión de SQLAlchemy, la cede al manejador de la petición y la
    cierra siempre al finalizar (bloque ``finally``), tanto si la petición
    termina correctamente como si lanza una excepción. Así se garantiza que la
    conexión regrese al pool y no queden sesiones abiertas.

    Uso en un endpoint::

        from fastapi import Depends
        from sqlalchemy.orm import Session

        @app.get("/ejemplo")
        def leer(db: Session = Depends(get_db)):
            ...

    Resultado verificable (tasks.md §3): `get_db()` entrega una sesión
    utilizable y la cierra al terminar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
