"""Configuración y fixtures de las pruebas unitarias de backend (tarea 15.1).

Objetivo (tasks.md 15.1): proveer un ``TestClient`` de FastAPI cableado a una
sesión de base de datos **aislada** por prueba, con esquema fresco en cada test,
sobrescribiendo la dependencia ``get_db`` de la app.

Decisiones técnicas de las fixtures:

- **DATABASE_URL dummy antes de importar la app.** El módulo
  ``backend/src/core/database.py`` construye ``SessionLocal`` (y, por tanto, el
  engine real de PostgreSQL) en **tiempo de importación** a partir de
  ``DATABASE_URL``. Para poder importar la aplicación en un entorno de prueba sin
  una base PostgreSQL real, se fija una ``DATABASE_URL`` ficticia en el entorno
  **antes** de cualquier importación de ``backend.src`` (ver el bloque superior
  de este módulo). El engine real nunca se usa porque ``get_db`` se sobrescribe.

- **SQLite en memoria compartida (nivel unitario).** Se crea un engine SQLite
  en memoria con ``StaticPool`` para que todas las sesiones de una misma prueba
  compartan la **misma** conexión y, por tanto, el mismo esquema y datos. El
  esquema se crea con ``Base.metadata.create_all`` al inicio de cada prueba y se
  elimina al terminar, garantizando aislamiento total entre tests.

- **Integridad referencial en SQLite.** SQLite no aplica claves foráneas por
  defecto; se habilita con ``PRAGMA foreign_keys=ON`` por conexión, de modo que
  las FK NOT NULL del modelo tengan efecto también a nivel unitario.

- **Override de ``get_db``.** La app de producción abre su propia sesión por
  petición; en pruebas se sustituye por una dependencia que entrega la sesión de
  prueba enlazada al engine SQLite en memoria. Así, el ``TestClient`` ejerce la
  pila real (routers → services → repositories → models) sobre una base aislada.

Estas fixtures NO introducen mocks de la lógica de negocio: ejercitan el código
real contra una base de datos real (SQLite en memoria), según structure.md §19.
"""

from __future__ import annotations

import os

# --- DATABASE_URL ficticia ANTES de importar cualquier módulo de backend. ----
# database.py evalúa get_engine() en tiempo de importación; sin esta variable la
# importación fallaría. El valor es un placeholder: el engine real no se usa en
# pruebas porque get_db se sobrescribe por una sesión SQLite en memoria.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test_db"
)
os.environ.setdefault("ENVIRONMENT", "test")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

# Importar el paquete de modelos registra TODAS las tablas en Base.metadata, de
# modo que create_all construya el esquema completo de la jerarquía ENCA.
from backend.src.core.database import get_db  # noqa: E402
from backend.src.main import create_app  # noqa: E402
from backend.src.models import Base  # noqa: E402


@event.listens_for(Engine, "connect")
def _habilitar_foreign_keys(dbapi_connection, connection_record):  # noqa: ANN001
    """Activa la verificación de claves foráneas en conexiones SQLite.

    SQLite no aplica FK por defecto; este listener ejecuta
    ``PRAGMA foreign_keys=ON`` en cada conexión para que las restricciones de
    integridad referencial del modelo tengan efecto a nivel unitario. Para otros
    motores (no SQLite) el PRAGMA simplemente no aplica y se ignora el error.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:  # pragma: no cover - motores que no soportan el PRAGMA
        pass


@pytest.fixture()
def db_session() -> Iterator[Session]:
    """Entrega una sesión SQLAlchemy aislada sobre SQLite en memoria.

    Crea un engine SQLite en memoria con ``StaticPool`` (conexión compartida),
    construye el esquema completo (``create_all``), cede una sesión y, al
    terminar la prueba, cierra la sesión y elimina el esquema. Cada prueba
    obtiene así un estado limpio e independiente.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def app(db_session: Session) -> Iterator[FastAPI]:
    """Crea la app FastAPI con ``get_db`` sobrescrito por la sesión de prueba.

    La sobrescritura garantiza que routers, services y repositories reales
    operen sobre la base SQLite en memoria aislada de la prueba, en lugar de la
    base PostgreSQL de producción.
    """
    application = create_app()

    def _get_test_db() -> Iterator[Session]:
        # Reutiliza la MISMA sesión de la prueba. No se cierra aquí: su ciclo de
        # vida lo gobierna la fixture db_session.
        yield db_session

    application.dependency_overrides[get_db] = _get_test_db
    try:
        yield application
    finally:
        application.dependency_overrides.clear()


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """Cliente de pruebas HTTP que ejercita la app sobre la base aislada."""
    with TestClient(app) as test_client:
        yield test_client
