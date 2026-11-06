"""Carga de configuración por variables de entorno (settings).

Expone un objeto de settings basado en Pydantic Settings que lee la
configuración del entorno. Siguiendo el Steering técnico (tech.md §19, §20):

- La configuración se separa del código.
- Las variables sensibles o dependientes del entorno se manejan mediante
  variables de entorno.
- NO se definen valores secretos por defecto. En particular, `DATABASE_URL`
  no tiene valor por defecto: si falta, la carga de settings falla de forma
  controlada con un error de validación comprensible, en lugar de usar una
  credencial inventada.

Variables leídas (ver `.env.example`):

- ``DATABASE_URL``   (obligatoria, sin valor por defecto)
- ``ENVIRONMENT``    (opcional)
- ``LOG_LEVEL``      (opcional, por defecto ``INFO`` — valor no secreto)
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings de la aplicación cargados desde el entorno.

    No se asigna ningún valor por defecto a información sensible. `DATABASE_URL`
    es obligatoria y no tiene valor por defecto: su ausencia produce un error
    de validación controlado al instanciar `Settings`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Obligatoria y sin valor por defecto (sin secreto hardcodeado).
    # Formato de referencia (tech.md §19):
    #   postgresql+psycopg://<usuario>:<password>@<host>:<puerto>/<base>
    DATABASE_URL: str = Field(
        ...,
        description=(
            "Cadena de conexión a PostgreSQL (SQLAlchemy). Obligatoria; "
            "se toma del entorno y nunca se hardcodea."
        ),
    )

    # Opcional: identifica el entorno (p. ej. development | test | production).
    # Valor no secreto; se deja vacío por defecto para no inventar un entorno.
    ENVIRONMENT: str = Field(
        default="",
        description="Entorno de ejecución (development | test | production).",
    )

    # Opcional: nivel de logging. Valor no secreto; INFO es un valor por
    # defecto razonable y no sensible.
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Nivel de logging (DEBUG | INFO | WARNING | ERROR).",
    )


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia única (cacheada) de `Settings`.

    La instanciación falla de forma controlada (``pydantic.ValidationError``)
    si una variable obligatoria como `DATABASE_URL` no está presente en el
    entorno, en lugar de recurrir a un valor inventado.
    """

    return Settings()
