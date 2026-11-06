"""Punto de entrada de la aplicación FastAPI — SAO ENCA 2030.

Tarea 2.2: instancia la app FastAPI y configura el logging básico del backend.
Tarea 11.8: registra todos los routers de la API y los manejadores de
excepciones de dominio/validación.

Alcance de la app (tasks.md §2.2 y §11.8):
- Instanciar la aplicación FastAPI y configurar el logging básico sin exponer
  secretos ni trazas al cliente (tech.md §31 logging, §32 manejo de errores).
- Registrar los seis routers por entidad y de la jerarquía (tareas 11.2–11.7),
  de modo que el esquema OpenAPI liste todos los endpoints de negocio.
- Registrar los manejadores de excepciones (tarea 11.1) para traducir las
  excepciones de dominio y los errores de validación al cuerpo JSON uniforme.

El logging escribe a los logs del servidor; la respuesta al cliente nunca
incluye trazas de pila ni detalles internos (tech.md §32, Req 7.9).
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.api import register_exception_handlers
from backend.src.api.actividades import router as actividades_router
from backend.src.api.bibliometria import router as bibliometria_router
from backend.src.api.biodiversidad import router as biodiversidad_router
from backend.src.api.ejes import router as ejes_router
from backend.src.api.indicadores import router as indicadores_router
from backend.src.api.jerarquia import router as jerarquia_router
from backend.src.api.metas import router as metas_router
from backend.src.api.objetivos import router as objetivos_router

# --- Metadatos de la aplicación ---------------------------------------------
APP_TITLE = "SAO ENCA 2030 API"
APP_DESCRIPTION = (
    "API de seguimiento de la estructura ENCA "
    "(Eje → Meta → Objetivo SMART → Indicador → Actividad)."
)
APP_VERSION = "0.1.0"

# Orígenes del frontend permitidos por CORS en desarrollo local. Vite sirve el
# frontend en http://localhost:5173 (y la variante 127.0.0.1) por defecto.
# Estos NO son secretos: son orígenes de desarrollo local (tech.md §26 ejecución
# local, §30 seguridad: no exponer secretos). El valor es configurable por
# entorno; se mantiene mínimo y orientado a desarrollo local (tech.md §33, §40).
_DEFAULT_LOCAL_FRONTEND_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _resolve_cors_origins() -> list[str]:
    """Determina los orígenes permitidos por CORS a partir del entorno.

    Lee ``CORS_ALLOW_ORIGINS`` (lista separada por comas) del entorno
    (tech.md §19: configuración por variables de entorno). Si no está definida,
    usa los orígenes del frontend local de Vite por defecto, de modo que el
    frontend (http://localhost:5173) pueda consumir la API en ejecución local
    (Req 7.1) sin configuración adicional. No lee ni expone ningún secreto.
    """
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return list(_DEFAULT_LOCAL_FRONTEND_ORIGINS)
    # Separa por comas, recorta espacios y descarta entradas vacías.
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _resolve_log_level() -> int:
    """Determina el nivel de logging a partir del entorno.

    Lee ``LOG_LEVEL`` del entorno (tech.md §19: configuración por variables de
    entorno). Si no está definido o es inválido, usa ``INFO`` como valor seguro
    por defecto. No lee ni expone ningún secreto.
    """
    raw_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    # logging.getLevelName devuelve un int para nombres válidos; de lo contrario
    # devuelve una cadena "Level <name>". Validamos para evitar valores inválidos.
    level = logging.getLevelName(raw_level)
    if isinstance(level, int):
        return level
    return logging.INFO


def configure_logging() -> None:
    """Configura el logging básico del backend.

    - Nivel tomado de ``LOG_LEVEL`` (por defecto INFO).
    - Formato legible con marca de tiempo, nivel y logger de origen.
    - No se registran secretos (tech.md §20, §31); los mensajes de aplicación
      son responsables de no incluir credenciales ni datos sensibles.
    """
    logging.basicConfig(
        level=_resolve_log_level(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def create_app() -> FastAPI:
    """Crea y configura la instancia de la aplicación FastAPI.

    Registra los seis routers de la API (Eje, Meta, Objetivo, Indicador,
    Actividad y navegación de la jerarquía; tareas 11.2–11.7) y los manejadores
    de excepciones de dominio/validación (tarea 11.1). Como resultado, el
    esquema OpenAPI lista todos los endpoints de negocio y la app responde a
    cada ruta.
    """
    configure_logging()
    logger = logging.getLogger(__name__)

    environment = os.getenv("ENVIRONMENT", "local").strip() or "local"

    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
    )

    # CORS: permite que el frontend React (Vite, http://localhost:5173) consuma
    # la API desde el navegador en ejecución local (Req 7.1). Los orígenes son
    # configurables por entorno (CORS_ALLOW_ORIGINS) con un valor por defecto
    # local; se mantiene mínimo y orientado a desarrollo local, sin comodines
    # abiertos ni credenciales (tech.md §30 seguridad, §33/§40 evitar
    # sobreingeniería). Solo se exponen los métodos usados por la API (GET/POST).
    cors_origins = _resolve_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    logger.info("CORS habilitado para orígenes: %s", ", ".join(cors_origins))

    # Routers por entidad y de la jerarquía. Cada módulo define las rutas
    # completas (sin prefijo compartido), de modo que el OpenAPI resultante
    # expone todos los endpoints confirmados de la Spec (Req 1.1, 2.1, 3.1,
    # 4.1, 5.1, 6.1).
    app.include_router(ejes_router)
    app.include_router(metas_router)
    app.include_router(objetivos_router)
    app.include_router(indicadores_router)
    app.include_router(actividades_router)
    app.include_router(jerarquia_router)
    # Router del dashboard bibliométrico (Componente B). No usa base de datos:
    # lee el dataset ya procesado de data/processed/boletin_sao/.
    app.include_router(bibliometria_router)
    # Router de la vista de biodiversidad (Datos de GBIF). Tampoco usa base de
    # datos: lee artefactos de outputs/biodiversity_pilot/gbif/ o consulta GBIF
    # en vivo reutilizando el script del piloto, sin persistir archivos.
    app.include_router(biodiversidad_router)

    # Manejadores de excepciones: traducen las excepciones de dominio y los
    # errores de validación al cuerpo JSON uniforme, sin exponer trazas
    # (tech.md §32, Req 7.9).
    register_exception_handlers(app)

    # Registro de arranque sin exponer secretos ni configuración sensible.
    logger.info("Aplicación FastAPI inicializada (entorno=%s)", environment)

    return app


# Instancia de la aplicación usada por el servidor ASGI (p. ej. uvicorn):
#   uvicorn backend.src.main:app --reload
app = create_app()
