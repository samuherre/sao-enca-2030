"""Fixtures de integración — Spec ``enca-strategy-tracking`` (tarea 16.1).

Estas fixtures preparan una **base de datos de prueba real** sobre la que se
ejecutan las migraciones versionadas de **Alembic** (``alembic upgrade head``),
y entregan a cada prueba una **sesión transaccional** que se revierte
(``rollback``) al terminar, garantizando aislamiento entre pruebas
(``structure.md`` §19).

Selección del motor de base de datos
------------------------------------
Se prefiere **PostgreSQL** cuando hay una URL de prueba disponible por variable
de entorno (``TEST_DATABASE_URL`` o, si apunta a PostgreSQL, ``DATABASE_URL``);
así la integración se valida contra el motor real del proyecto (tech.md §8).

Si **no** hay PostgreSQL disponible en el entorno, se usa como *fallback* una
base **SQLite en archivo** temporal. SQLite se usa en archivo (no ``:memory:``)
porque Alembic y la propia prueba abren conexiones distintas que deben compartir
el mismo esquema. En SQLite la verificación de claves foráneas está **desactivada
por defecto**, por lo que la prueba de integridad referencial (tarea 16.2)
**requiere** habilitarla explícitamente: esta configuración activa
``PRAGMA foreign_keys=ON`` en cada conexión mediante un *event listener*, de modo
que las restricciones FK se **apliquen realmente** y la prueba 16.2 sea válida.

En ambos motores el esquema se crea con las migraciones de Alembic (requisito de
la tarea 16.1), no con ``Base.metadata.create_all``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pytest

# ---------------------------------------------------------------------------
# 1) Resolución de la URL de la base de datos de prueba
# ---------------------------------------------------------------------------
# IMPORTANTE: ``backend.src.core.database`` construye el engine a partir de
# ``DATABASE_URL`` en tiempo de import (vía ``get_settings()``, cacheado). Por
# eso resolvemos la URL de prueba y fijamos ``DATABASE_URL`` en el entorno
# ANTES de importar cualquier módulo del backend que dependa de la conexión.

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _is_postgres_url(url: str | None) -> bool:
    """Indica si ``url`` apunta a un PostgreSQL utilizable."""
    if not url:
        return False
    scheme = urlparse(url).scheme.lower()
    return scheme.startswith("postgresql") or scheme.startswith("postgres")


# Archivo SQLite temporal (solo se usa en el fallback). Se registra a nivel de
# módulo para poder eliminarlo al finalizar la sesión de pruebas.
_SQLITE_TMP_PATH: str | None = None


def _resolve_test_database_url() -> tuple[str, bool]:
    """Devuelve ``(url, usa_postgres)`` para la base de datos de prueba.

    Preferencia (tarea 16.1):
    1. ``TEST_DATABASE_URL`` si está definida.
    2. ``DATABASE_URL`` si apunta a PostgreSQL.
    3. *Fallback*: SQLite en archivo temporal (con FK habilitadas en runtime).
    """
    global _SQLITE_TMP_PATH

    test_url = os.getenv("TEST_DATABASE_URL")
    if _is_postgres_url(test_url):
        return test_url, True  # type: ignore[return-value]

    current_url = os.getenv("DATABASE_URL")
    if _is_postgres_url(current_url):
        return current_url, True  # type: ignore[return-value]

    # Fallback: SQLite en archivo temporal. Ruta derivada del sistema (no una
    # ruta absoluta de una máquina concreta; structure.md §26). Solo se reserva
    # el NOMBRE aquí; el archivo real se crea/elimina dentro de la fixture de
    # sesión (``_apply_migrations``), cuyo ``finally`` garantiza la limpieza
    # incluso si la recolección se interrumpe.
    path = os.path.join(
        tempfile.gettempdir(), f"enca_itest_{os.getpid()}.db"
    )
    _SQLITE_TMP_PATH = path
    # SQLAlchemy requiere separadores con ``/``.
    sqlite_url = f"sqlite+pysqlite:///{Path(path).as_posix()}"
    return sqlite_url, False


_TEST_DATABASE_URL, _USES_POSTGRES = _resolve_test_database_url()

# Fija la URL de prueba en el entorno antes de importar el backend y limpia
# cualquier settings cacheado para que el engine se construya con esta URL.
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL

from backend.src.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from sqlalchemy import event  # noqa: E402

from backend.src.core import database as db_module  # noqa: E402

# Reconstruye el engine con la URL de prueba (el import pudo cachear el engine y
# ``SessionLocal`` con una URL previa, p. ej. la del proceso de pytest).
db_module.get_engine.cache_clear()
_ENGINE = db_module.get_engine()
db_module.SessionLocal.configure(bind=_ENGINE)


# En SQLite las FK están desactivadas por defecto: la prueba 16.2 necesita que
# se apliquen. Activamos ``PRAGMA foreign_keys=ON`` en cada conexión nueva.
if not _USES_POSTGRES:

    @event.listens_for(_ENGINE, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ---------------------------------------------------------------------------
# 2) Esquema vía migraciones Alembic (una vez por sesión de pruebas)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _apply_migrations():
    """Aplica ``alembic upgrade head`` sobre la base de prueba (tarea 16.1).

    Usa la configuración real de Alembic (``backend/alembic.ini`` + ``env.py``),
    que lee ``DATABASE_URL`` del entorno (ya fijada a la URL de prueba). Al
    terminar la sesión, revierte con ``downgrade base`` y elimina el archivo
    SQLite temporal si se usó el *fallback*.
    """
    from alembic import command
    from alembic.config import Config

    # Si el fallback SQLite reusa un archivo de una ejecución previa
    # interrumpida, se elimina antes de migrar para partir de un esquema limpio.
    if _SQLITE_TMP_PATH and os.path.exists(_SQLITE_TMP_PATH):
        try:
            os.remove(_SQLITE_TMP_PATH)
        except OSError:
            pass

    alembic_ini = _PROJECT_ROOT / "backend" / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))

    command.upgrade(alembic_cfg, "head")
    try:
        yield
    finally:
        try:
            command.downgrade(alembic_cfg, "base")
        except Exception:
            # La limpieza del esquema no debe enmascarar fallos de prueba.
            pass
        _ENGINE.dispose()
        if _SQLITE_TMP_PATH and os.path.exists(_SQLITE_TMP_PATH):
            try:
                os.remove(_SQLITE_TMP_PATH)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# 3) Sesión transaccional con rollback (aislamiento por prueba)
# ---------------------------------------------------------------------------
@pytest.fixture()
def db_session():
    """Entrega una sesión ligada a una transacción que se revierte al final.

    Patrón de aislamiento clásico: se abre una conexión y una transacción
    externa; la ``Session`` se liga a esa conexión. Las operaciones de la
    aplicación (incluidos los ``commit`` de los routers) ocurren dentro de un
    *savepoint* anidado, de modo que al finalizar la prueba el ``rollback`` de la
    transacción externa deshace **todo** lo escrito, sin tocar las demás pruebas
    (``structure.md`` §19).
    """
    from sqlalchemy.orm import Session

    connection = _ENGINE.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False, expire_on_commit=False)

    # Inicia un savepoint y lo reabre tras cada ``commit`` del código bajo
    # prueba, para que la transacción externa permanezca abierta hasta el
    # rollback final.
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, trans):  # noqa: ANN001
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        event.remove(session, "after_transaction_end", _restart_savepoint)
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# 4) Cliente HTTP de la API con la sesión transaccional inyectada
# ---------------------------------------------------------------------------
@pytest.fixture()
def api_client(db_session):
    """``TestClient`` de FastAPI con ``get_db`` sobreescrito por ``db_session``.

    Permite ejercitar los endpoints reales (tarea 16.3) compartiendo la misma
    sesión transaccional de la prueba, de modo que lo creado vía API se revierte
    al terminar y no contamina otras pruebas.
    """
    from fastapi.testclient import TestClient

    from backend.src.core.database import get_db
    from backend.src.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="session")
def uses_postgres() -> bool:
    """``True`` si las pruebas corren contra PostgreSQL; ``False`` si SQLite."""
    return _USES_POSTGRES
