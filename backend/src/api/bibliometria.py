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
from fastapi.responses import Response

from backend.src.schemas.bibliometria import (
    ArticulosOFC,
    ResumenBibliometrico,
    ResumenConsolidado,
)
from backend.src.services.bibliometria_service import BibliometriaService

# Máximo de artículos que se devuelven en el listado JSON por OFC (para no
# volcar miles en el navegador). La descarga CSV sí trae todos.
_LIMITE_LISTA_OFC = 100


def _csv_response(contenido: str, nombre_archivo: str) -> Response:
    """Envuelve un CSV en una respuesta descargable (UTF-8 con BOM para Excel)."""
    # BOM para que Excel abra bien los acentos (títulos en español/portugués).
    cuerpo = "\ufeff" + contenido
    return Response(
        content=cuerpo,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )

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
    "/bibliometria/export.csv",
    summary="Descarga CSV del consolidado (título, enlace y metadatos básicos)",
    response_class=Response,
)
def exportar_consolidado_csv() -> Response:
    """Descarga el conjunto consolidado como CSV (una fila por artículo).

    Incluye al menos título y enlace de cada artículo (Req pedido por SAO), más
    año, fuente, revista y DOI. Refleja el dato tal cual; no inventa valores.
    """
    servicio = BibliometriaService()
    contenido = servicio.exportar_consolidado_csv()
    return _csv_response(contenido, "articulos_sao_todos.csv")


@router.get(
    "/bibliometria/export/anio/{anio}.csv",
    summary="Descarga CSV del consolidado filtrado por un año",
    response_class=Response,
)
def exportar_consolidado_csv_por_anio(anio: int) -> Response:
    """Como :func:`exportar_consolidado_csv`, pero solo los artículos de ``anio``.

    Ruta de recurso (``/anio/{anio}.csv``) por coherencia con el resumen y para
    que la demo estática pueda servir el archivo por ruta fija.
    """
    servicio = BibliometriaService()
    contenido = servicio.exportar_consolidado_csv(anio=anio)
    return _csv_response(contenido, f"articulos_sao_{anio}.csv")


@router.get(
    "/bibliometria/ofc/{ofc_id}/articulos",
    response_model=ArticulosOFC,
    summary="Artículos clasificados en un OFC (listado acotado para la vista)",
)
def articulos_de_ofc(ofc_id: str) -> ArticulosOFC:
    """Lista los artículos de un OFC para ver "detrás de" la barra del dashboard.

    Devuelve el total real del OFC y una lista acotada (``_LIMITE_LISTA_OFC``)
    con título, año, revista y enlace de cada artículo. Para el conjunto completo
    se usa la descarga CSV (``/bibliometria/ofc/{ofc_id}/export.csv``).
    """
    servicio = BibliometriaService()
    return servicio.articulos_de_ofc(ofc_id, limite=_LIMITE_LISTA_OFC)


@router.get(
    "/bibliometria/ofc/{ofc_id}/export.csv",
    summary="Descarga CSV de todos los artículos de un OFC",
    response_class=Response,
)
def exportar_articulos_ofc_csv(ofc_id: str) -> Response:
    """Descarga el conjunto COMPLETO de artículos de un OFC como CSV."""
    servicio = BibliometriaService()
    contenido = servicio.exportar_articulos_ofc_csv(ofc_id)
    return _csv_response(contenido, f"articulos_{ofc_id}.csv")


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
