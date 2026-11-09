"""Rutas del dashboard bibliométrico (Componente B).

Expone agregaciones bibliométricas a partir de los datasets YA PROCESADOS.
A diferencia de los routers de la jerarquía ENCA, estas rutas NO dependen de la
base de datos (``get_db``): los artículos viven en archivos procesados, no en
Postgres (steering bibliometrics.md, tech.md §12).

Hay dos lecturas:

- ``GET /bibliometria/resumen`` — resumen CONSOLIDADO de todas las fuentes
  descubiertas bajo ``data/processed/``. Sin datasets responde un resumen vacío
  (200) para un estado vacío honesto (Req 8.1, 8.2, 8.3).
- ``GET /bibliometria/boletin-sao/resumen`` — resumen de la fuente Boletín SAO
  (compatibilidad, Req 8.4). Si no existe dataset, el servicio lanza
  ``NotFoundError`` y el manejador de excepciones responde 404 con el cuerpo
  uniforme.
"""

from fastapi import APIRouter

from backend.src.schemas.bibliometria import (
    ResumenBibliometrico,
    ResumenConsolidado,
)
from backend.src.services.bibliometria_service import BibliometriaService

router = APIRouter(tags=["Bibliometría"])


@router.get(
    "/bibliometria/resumen",
    response_model=ResumenConsolidado,
    summary="Resumen consolidado de todas las fuentes bibliométricas",
)
def resumen_consolidado() -> ResumenConsolidado:
    """Devuelve el resumen CONSOLIDADO de todas las fuentes procesadas (todos los años).

    Descubre las fuentes bajo ``data/processed/`` y agrega el conjunto completo:
    total de artículos, distribución por año y por volumen, completitud de
    metadata, pendientes de revisión, posibles duplicados y el aporte por
    fuente. La distribución por OFC solo aparece si existe un dataset
    clasificado (``PENDING_VALIDATION``).

    ``anios_disponibles`` lista todos los años del conjunto para el desplegable
    del frontend; ``anio_seleccionado`` es ``None`` (este endpoint no filtra).

    A diferencia del resumen del Boletín, no lanza 404: sin datasets responde un
    resumen vacío coherente (200) para que el frontend muestre un estado vacío
    honesto (Req 8.3).
    """
    servicio = BibliometriaService()
    return servicio.resumen_consolidado()


@router.get(
    "/bibliometria/resumen/anio/{anio}",
    response_model=ResumenConsolidado,
    summary="Resumen consolidado filtrado por un año de publicación",
)
def resumen_consolidado_por_anio(anio: int) -> ResumenConsolidado:
    """Igual que :func:`resumen_consolidado`, pero filtrando TODO por ``anio``.

    Todas las agregaciones (total, por volumen, completitud, OFC y aporte por
    fuente) se calculan solo sobre los artículos cuyo ``publication_year`` es
    ``anio``. ``anios_disponibles`` sigue listando todos los años del conjunto
    completo, de modo que el desplegable del frontend pueda ofrecer cambiar de
    año u "Todos" sin perder las opciones.

    Se modela como ruta de recurso (``/anio/{anio}``) en vez de query string
    para que la demo estática de Vercel —que sirve archivos JSON por ruta fija—
    pueda ofrecer el mismo filtro sin un backend en vivo.
    """
    servicio = BibliometriaService()
    return servicio.resumen_consolidado(anio=anio)


@router.get(
    "/bibliometria/boletin-sao/resumen",
    response_model=ResumenBibliometrico,
    summary="Resumen agregado de la fuente Boletín SAO",
)
def resumen_boletin_sao() -> ResumenBibliometrico:
    """Devuelve el resumen agregado del dataset procesado del Boletín SAO.

    Incluye total de artículos, distribución por año y por volumen, completitud
    de metadata, pendientes de revisión y posibles duplicados. No incluye
    clasificación por OFC (``PENDING_VALIDATION``).
    """
    servicio = BibliometriaService()
    return servicio.resumen()
