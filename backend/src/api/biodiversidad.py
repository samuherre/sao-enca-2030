"""Rutas de la vista de biodiversidad — Datos de GBIF.

Expone cifras de registros de ocurrencia de aves de Colombia obtenidas del
piloto GBIF (``scripts/biodiversity_pilot/``). Como el dashboard bibliométrico,
estas rutas NO dependen de la base de datos: los datos viven en archivos de
``outputs/biodiversity_pilot/gbif/`` o se consultan en vivo a GBIF.

Dos endpoints, con una distinción explícita del ORIGEN del dato:

- ``GET  /biodiversidad/gbif/resumen``    → datos ALMACENADOS (último corte en disco).
- ``POST /biodiversidad/gbif/consultar``  → consulta EN VIVO a GBIF (no persiste).

El endpoint de consulta en vivo es POST porque dispara una acción con efecto
externo (una llamada a GBIF), aunque no modifica el estado del servidor.

Errores:
- Si no hay artefactos almacenados, el servicio lanza ``NotFoundError`` (404).
- Si la consulta en vivo no obtiene ninguna cifra (total ni ranking), se
  traduce a un error de dominio que el manejador global convierte en una
  respuesta uniforme, sin exponer trazas (tech.md §32).
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.src.domain.exceptions import DomainError
from backend.src.schemas.biodiversidad import ResumenGBIF
from backend.src.services.biodiversidad_service import BiodiversidadService

router = APIRouter(tags=["Biodiversidad"])


class ConsultaGbifFallidaError(DomainError):
    """La consulta en vivo a GBIF no devolvió ninguna cifra utilizable.

    Se usa cuando GBIF no respondió con un total ni con un ranking (p. ej. fallo
    de red o respuesta inesperada). Mapeo HTTP por defecto: 422 (el manejador
    global evita exponerlo como 500 con traza).
    """

    error_code = "gbif_query_failed"


@router.get(
    "/biodiversidad/gbif/resumen",
    response_model=ResumenGBIF,
    summary="Resumen del último corte GBIF almacenado (aves de Colombia)",
)
def resumen_gbif_almacenado() -> ResumenGBIF:
    """Devuelve el resumen del último corte GBIF guardado en disco.

    Lee los artefactos del piloto (``outputs/biodiversity_pilot/gbif/``): total
    nacional de registros de ocurrencia, ranking de publicadores, contexto del
    histórico y CSV de exportación disponibles. No consulta la red.

    :raises NotFoundError: 404 si aún no existe ningún corte almacenado.
    """
    return BiodiversidadService().resumen_almacenado()


@router.post(
    "/biodiversidad/gbif/consultar",
    response_model=ResumenGBIF,
    summary="Consulta EN VIVO a GBIF (no persiste archivos)",
)
def consultar_gbif_en_vivo() -> ResumenGBIF:
    """Ejecuta una consulta EN VIVO a GBIF reutilizando el script de Fase 1.

    Obtiene el total y el ranking al momento, SIN escribir archivos (no toca el
    histórico ni los artefactos almacenados). El resultado viene marcado como
    ``origen="en_vivo"`` para distinguirlo de los datos guardados.

    :raises ConsultaGbifFallidaError: 422 si GBIF no devolvió ninguna cifra.
    """
    resumen = BiodiversidadService().consulta_en_vivo()
    if resumen.total_registros_ocurrencia is None and not resumen.publicadores:
        detalle = "; ".join(resumen.errores) or "sin respuesta utilizable de GBIF."
        raise ConsultaGbifFallidaError(
            f"La consulta en vivo a GBIF no devolvió cifras: {detalle}"
        )
    return resumen
