"""Servicio de la vista de biodiversidad — Datos de GBIF.

Reutiliza el piloto GBIF (``scripts/biodiversity_pilot/``) de dos formas, sin
duplicar la lógica científica de consulta a GBIF:

1. ALMACENADO (``resumen_almacenado``): lee los ARTEFACTOS ya generados en
   ``outputs/biodiversity_pilot/gbif/`` (último corte ``bird_record_counts_*.json``,
   histórico consolidado y CSV de exportación). No consulta la red.

2. EN VIVO (``consulta_en_vivo``): ejecuta ``gbif_bird_counts.run`` ahora mismo
   para obtener el total y el ranking al momento. NO escribe archivos (no toca
   el histórico ni los artefactos), de modo que una consulta en vivo nunca
   corrompe los resultados almacenados ni se confunde con ellos.

Decisiones (tech.md §12 bibliometría/datos desacoplados, §32 manejo de errores,
structure.md §30 la interfaz consulta resultados; product.md §15 no invención):
- NO accede a la base de datos (los artefactos viven en archivos).
- El script se carga por RUTA con importlib (igual que
  ``gbif_bird_counts_history.py``), para no acoplar el backend al paquete de
  scripts ni duplicar la consulta a GBIF.
- Una consulta en vivo se serializa con un lock en proceso para evitar
  ejecuciones concurrentes (y el consiguiente gasto innecesario en GBIF).
- Un dato ausente se reporta como ``None`` (nunca 0 inventado).
"""

from __future__ import annotations

import csv
import importlib.util
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.src.domain.exceptions import NotFoundError
from backend.src.schemas.biodiversidad import (
    ArchivoExportacion,
    CorteHistoricoGBIF,
    PublicadorGBIF,
    ResumenGBIF,
)

# --- Identificación de la fuente y el alcance (constantes del piloto) --------
# Coinciden con los parámetros reales del script (country=CO, taxonKey=212).
FUENTE = "GBIF — Global Biodiversity Information Facility"
FUENTE_URL = "https://api.gbif.org/v1"
GRUPO_TAXONOMICO = "Aves (clase Aves, taxonKey=212)"
COBERTURA = "Colombia (country=CO)"
ALCANCE = (
    "Registros de ocurrencia de aves en Colombia. Son conteos AGREGADOS de GBIF "
    "(limit=0 + facet): representan registros de ocurrencia en la fuente, no un "
    "conteo de individuos ni de especies únicas."
)

# --- Rutas de artefactos (coinciden con los scripts del piloto) --------------
# backend/src/services/ -> subir 3 niveles hasta la raíz del repo.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_GBIF_DIR = _REPO_ROOT / "outputs" / "biodiversity_pilot" / "gbif"
_HISTORY_DIR = _GBIF_DIR / "history"
_NATIONAL_TOTAL_HISTORY = _HISTORY_DIR / "national_total_history.csv"
_ARCGIS_DIR = _GBIF_DIR / "arcgis"

# Ruta del script de Fase 1, cargado por importlib para reutilizar ``run``.
_FASE1_PATH = (
    _REPO_ROOT / "scripts" / "biodiversity_pilot" / "gbif_bird_counts.py"
)

# Lock en proceso para serializar consultas en vivo (evita ejecuciones
# concurrentes que gastarían llamadas a GBIF sin aportar nada).
_LIVE_QUERY_LOCK = threading.Lock()

# Timeout corto por consulta en vivo: la extracción observada dura ~10 s; se
# mantiene por debajo del timeout del frontend (30 s) con margen.
_LIVE_QUERY_TIMEOUT_S = 20


def _cargar_modulo_fase1() -> Any:
    """Carga ``gbif_bird_counts.py`` por ruta (sin depender del sys.path)."""
    spec = importlib.util.spec_from_file_location("gbif_bird_counts", _FASE1_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - entorno roto
        raise NotFoundError(
            "No se encontró el script de cifras GBIF (gbif_bird_counts.py)."
        )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _ultimo_corte_json() -> Path | None:
    """Devuelve el JSON del corte más reciente, o None si no hay ninguno."""
    if not _GBIF_DIR.exists():
        return None
    candidatos = sorted(_GBIF_DIR.glob("bird_record_counts_*.json"))
    return candidatos[-1] if candidatos else None


def _fecha_desde_iso(iso: str | None) -> str | None:
    """Deriva YYYY-MM-DD de un timestamp ISO; None si no es parseable."""
    if not iso or len(iso) < 10:
        return None
    candidato = iso[:10]
    partes = candidato.split("-")
    if len(partes) == 3 and all(p.isdigit() for p in partes):
        return candidato
    return None


def _publicadores_desde_report(report: dict[str, Any]) -> list[PublicadorGBIF]:
    """Convierte ``publisher_ranking`` del report al contrato de la API."""
    salida: list[PublicadorGBIF] = []
    for pos, pub in enumerate(report.get("publisher_ranking", []) or [], start=1):
        org_key = pub.get("org_key")
        occ = pub.get("occurrence_count")
        if org_key is None or not isinstance(occ, int):
            # Entrada malformada: se omite, no se inventa.
            continue
        salida.append(
            PublicadorGBIF(
                rank=pos,
                org_key=str(org_key),
                nombre=pub.get("publisher_name"),  # None si GBIF no lo resolvió
                registros_ocurrencia=occ,
            )
        )
    return salida


def _leer_historico() -> list[CorteHistoricoGBIF]:
    """Lee el histórico consolidado de total nacional (si existe)."""
    if not _NATIONAL_TOTAL_HISTORY.exists():
        return []
    cortes: list[CorteHistoricoGBIF] = []
    with _NATIONAL_TOTAL_HISTORY.open(encoding="utf-8-sig", newline="") as handle:
        for fila in csv.DictReader(handle):
            extraido = (fila.get("extracted_at_utc") or "").strip()
            total_raw = (fila.get("total_bird_records_colombia") or "").strip()
            pubs_raw = (fila.get("publishers_in_ranking") or "").strip()
            cortes.append(
                CorteHistoricoGBIF(
                    extraido_utc=extraido,
                    fecha=_fecha_desde_iso(extraido),
                    estado=(fila.get("status") or "").strip(),
                    # Vacío => None (no se inventa un 0).
                    total_registros_ocurrencia=int(total_raw) if total_raw.isdigit() else None,
                    publicadores_en_ranking=int(pubs_raw) if pubs_raw.isdigit() else None,
                )
            )
    return cortes


def _contar_filas_csv(path: Path) -> int:
    """Cuenta filas de datos de un CSV (sin la cabecera). 0 si no existe."""
    if not path.exists():
        return 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        filas = sum(1 for _ in csv.reader(handle))
    return max(0, filas - 1)


def _listar_exportaciones() -> list[ArchivoExportacion]:
    """Lista los CSV de exportación para ArcGIS disponibles en disco."""
    if not _ARCGIS_DIR.exists():
        return []
    salida: list[ArchivoExportacion] = []
    for path in sorted(_ARCGIS_DIR.glob("*.csv")):
        stat = path.stat()
        modificado = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        salida.append(
            ArchivoExportacion(
                nombre=path.name,
                ruta_relativa=path.relative_to(_REPO_ROOT).as_posix(),
                filas=_contar_filas_csv(path),
                modificado_utc=modificado.isoformat(),
            )
        )
    return salida


class BiodiversidadService:
    """Casos de uso de la vista de cifras de aves de GBIF."""

    def resumen_almacenado(self) -> ResumenGBIF:
        """Resumen del ÚLTIMO corte GBIF almacenado en disco.

        :raises NotFoundError: si no existe ningún artefacto de corte todavía.
        """
        corte_path = _ultimo_corte_json()
        if corte_path is None:
            raise NotFoundError(
                "No hay cifras GBIF almacenadas todavía. Ejecute el script "
                "scripts/biodiversity_pilot/gbif_bird_counts.py o use "
                "'Consultar GBIF' para una consulta en vivo."
            )

        report = json.loads(corte_path.read_text(encoding="utf-8"))
        historico = _leer_historico()

        return ResumenGBIF(
            fuente=FUENTE,
            fuente_url=FUENTE_URL,
            grupo_taxonomico=GRUPO_TAXONOMICO,
            cobertura_geografica=COBERTURA,
            alcance=ALCANCE,
            origen="almacenado",
            extraido_utc=report.get("extracted_at_utc"),
            finalizado_utc=report.get("finished_at_utc"),
            estado=report.get("status", "desconocido"),
            errores=list(report.get("errors", []) or []),
            nota=report.get("notes"),
            total_registros_ocurrencia=report.get("total_bird_records_colombia"),
            publicadores=_publicadores_desde_report(report),
            cortes_historicos=len(historico),
            historico=historico,
            exportaciones=_listar_exportaciones(),
        )

    def consulta_en_vivo(self, facet_limit: int = 5) -> ResumenGBIF:
        """Consulta GBIF AHORA (reutiliza ``run``) SIN escribir archivos.

        Serializa las consultas con un lock en proceso. El resultado se marca
        ``origen="en_vivo"`` y NO se persiste, de modo que no corrompe el
        histórico ni se confunde con los datos almacenados.

        :raises NotFoundError: si no se pudo cargar el script de Fase 1.
        """
        modulo = _cargar_modulo_fase1()

        with _LIVE_QUERY_LOCK:
            report = modulo.run(
                facet_limit=facet_limit,
                timeout=_LIVE_QUERY_TIMEOUT_S,
                resolve_names=True,
            )

        # El histórico y las exportaciones siguen siendo los almacenados; se
        # incluyen como contexto, pero el origen del resumen es "en_vivo".
        historico = _leer_historico()

        return ResumenGBIF(
            fuente=FUENTE,
            fuente_url=FUENTE_URL,
            grupo_taxonomico=GRUPO_TAXONOMICO,
            cobertura_geografica=COBERTURA,
            alcance=ALCANCE,
            origen="en_vivo",
            extraido_utc=report.get("extracted_at_utc"),
            finalizado_utc=report.get("finished_at_utc"),
            estado=report.get("status", "desconocido"),
            errores=list(report.get("errors", []) or []),
            nota=report.get("notes"),
            total_registros_ocurrencia=report.get("total_bird_records_colombia"),
            publicadores=_publicadores_desde_report(report),
            cortes_historicos=len(historico),
            historico=historico,
            exportaciones=_listar_exportaciones(),
        )
