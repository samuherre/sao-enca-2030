"""Servicio del dashboard bibliométrico (Componente B).

Lee los datasets YA PROCESADOS bajo ``data/processed/`` y calcula agregaciones
para el dashboard. Hoy expone dos lecturas:

- :meth:`BibliometriaService.resumen` — resumen de la fuente Boletín SAO
  (compatibilidad, Req 8.4). Lee solo ``data/processed/boletin_sao/``.
- :meth:`BibliometriaService.resumen_consolidado` — resumen CONSOLIDADO de
  todas las fuentes descubiertas bajo ``data/processed/`` (Req 6, 7, 10.1).

Decisiones (steering bibliometrics.md, tech.md §12, structure.md §30):
- NO ejecuta el pipeline ni procesa PDFs por request.
- NO accede a la base de datos (los artículos viven en archivos, no en Postgres).
- Si no hay dataset, devuelve un resumen vacío coherente (no inventa datos).
- El consolidado descubre fuentes por carpeta y agrupa registros por su campo
  ``source`` (no depende de un mapa fijo carpeta→nombre): añadir una fuente
  conforme al contrato no requiere tocar este servicio (Req 10.1).
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from backend.src.domain.exceptions import NotFoundError
from backend.src.schemas.bibliometria import (
    AporteFuente,
    CompletitudCampo,
    ConteoOFC,
    ConteoPorClave,
    ResumenBibliometrico,
    ResumenConsolidado,
)

FUENTE = "Boletín SAO"

# Raíz del repo: backend/src/services/ -> subir 4 niveles.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROCESSED_DIR = _REPO_ROOT / "data" / "processed"
_DATASET_DIR = _PROCESSED_DIR / "boletin_sao"
_CLASIFICADO_DIR = _PROCESSED_DIR / "boletin_sao_clasificado"
_OFC_CATALOG = _REPO_ROOT / "bibliometrics" / "classification" / "ofc_catalog.json"

# Campos cuya completitud reportamos en el dashboard.
_CAMPOS_COMPLETITUD = ["title", "authors", "abstract", "keywords", "doi"]

# Sufijo que marca una carpeta/archivo como dataset CLASIFICADO: no aporta
# artículos al total; solo alimenta la distribución por OFC (Req 6.7).
_SUFIJO_CLASIFICADO = "_clasificado"


def _ultimo_dataset() -> Path | None:
    """Devuelve el JSON de dataset más reciente, o None si no existe ninguno."""
    if not _DATASET_DIR.exists():
        return None
    candidatos = sorted(_DATASET_DIR.glob("boletin_sao_dataset_*.json"))
    return candidatos[-1] if candidatos else None


def _ultimo_clasificado() -> Path | None:
    """Devuelve el dataset CLASIFICADO más reciente, o None si no existe."""
    if not _CLASIFICADO_DIR.exists():
        return None
    candidatos = sorted(_CLASIFICADO_DIR.glob("boletin_sao_clasificado_*.json"))
    return candidatos[-1] if candidatos else None


def _nombres_ofc() -> dict[str, str]:
    """Mapa ofc_id -> nombre desde el catálogo (para etiquetas del dashboard)."""
    if not _OFC_CATALOG.exists():
        return {}
    data = json.loads(_OFC_CATALOG.read_text(encoding="utf-8"))
    return {o["id"]: o["nombre"] for o in data.get("ofc", [])}


def _fecha_desde_nombre(path: Path) -> str | None:
    """Extrae la fecha YYYY-MM-DD del nombre del archivo de dataset."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return m.group(1) if m else None


def _es_carpeta_clasificado(carpeta: Path) -> bool:
    """Indica si una carpeta corresponde a datasets clasificados (Req 6.7).

    Una carpeta es de datasets clasificados si su nombre termina en
    ``_clasificado`` o si contiene archivos con el patrón
    ``*_clasificado_*.json``. Estas carpetas no aportan artículos al total: solo
    alimentan la distribución por OFC.
    """
    if carpeta.name.endswith(_SUFIJO_CLASIFICADO):
        return True
    return any(carpeta.glob("*_clasificado_*.json"))


def _ultimo_json(carpeta: Path) -> Path | None:
    """Devuelve el JSON con la fecha más reciente en una carpeta, o None.

    Elige entre los ``*.json`` el de nombre mayor (los nombres incluyen la fecha
    ``YYYY-MM-DD``, por lo que el orden lexicográfico coincide con el cronológico,
    igual que en :func:`_ultimo_dataset`).
    """
    if not carpeta.exists():
        return None
    candidatos = sorted(carpeta.glob("*.json"))
    return candidatos[-1] if candidatos else None


def _acumular_json(carpeta: Path) -> tuple[list[dict], list[str]]:
    """Acumula los registros de TODOS los ``*.json`` de una carpeta (modelo
    acumulativo) deduplicando por ``article_id`` DENTRO de la carpeta/fuente.

    Lee los datasets en orden cronológico (los nombres incluyen la fecha
    ``YYYY-MM-DD``, por lo que el orden lexicográfico coincide con el
    cronológico). Cuando el mismo ``article_id`` aparece en varias corridas de la
    misma fuente (p. ej. la misma publicación recuperada el 28 y el 30), se
    conserva UNA sola copia y gana la versión del dataset MÁS RECIENTE (por si
    cambió algún metadato). Los registros sin ``article_id`` se conservan todos
    (no se pueden deduplicar sin clave) para no perder información.

    Deduplica solo DENTRO de la fuente, apoyándose en el ``article_id``
    determinista. La deduplicación ENTRE fuentes distintas sigue
    ``PENDING_VALIDATION`` y no se fuerza aquí (coherente con Req 6.6).

    Devuelve ``(registros_acumulados, fechas_de_los_datasets_leidos)``.
    """
    if not carpeta.exists():
        return [], []
    archivos = sorted(carpeta.glob("*.json"))  # cronológico asc. por nombre.
    por_id: dict[str, dict] = {}
    sin_id: list[dict] = []
    fechas: list[str] = []
    for archivo in archivos:
        try:
            registros = json.loads(archivo.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(registros, list):
            continue
        fecha = _fecha_desde_nombre(archivo)
        if fecha is not None:
            fechas.append(fecha)
        for r in registros:
            if not isinstance(r, dict):
                continue
            aid = r.get("article_id")
            if aid:
                # El más reciente gana: al leer en orden cronológico, la última
                # asignación para un article_id es la del dataset más nuevo.
                por_id[aid] = r
            else:
                sin_id.append(r)
    return list(por_id.values()) + sin_id, fechas


def _carpetas_procesadas() -> list[Path]:
    """Descubre las subcarpetas de datasets bajo ``data/processed/``.

    No asume nombres concretos: cualquier subcarpeta se considera una posible
    fuente o un dataset clasificado. Devuelve la lista ordenada por nombre para
    un resultado determinista.
    """
    if not _PROCESSED_DIR.exists():
        return []
    return sorted(p for p in _PROCESSED_DIR.iterdir() if p.is_dir())


def _clave_volumen(item: tuple[str, int]) -> tuple[int, object]:
    """Orden robusto de volúmenes: numéricos por valor, el resto alfabético.

    A diferencia del resumen del Boletín (donde el volumen siempre es numérico),
    el consolidado combina fuentes heterogéneas cuyo ``volume`` puede no ser
    numérico. Ordena primero los numéricos por su valor entero y después los no
    numéricos alfabéticamente, sin fallar ante valores arbitrarios.
    """
    clave = item[0]
    # ``str.isdigit()`` acepta dígitos Unicode no ASCII (p. ej. superíndices
    # ``¹``/``²``) que ``int()`` rechaza. Restringir a dígitos ASCII evita el
    # ValueError al ordenar volúmenes heterogéneos de fuentes arbitrarias.
    if clave.isascii() and clave.isdigit():
        return (0, int(clave))
    return (1, clave)


def _completitud(registros: list[dict]) -> list[CompletitudCampo]:
    """Completitud por campo sobre un conjunto de registros."""
    total = len(registros)
    return [
        CompletitudCampo(
            campo=campo,
            con_dato=sum(1 for r in registros if r.get(campo)),
            total=total,
        )
        for campo in _CAMPOS_COMPLETITUD
    ]


class BibliometriaService:
    """Casos de uso de lectura del dataset bibliométrico procesado."""

    def resumen(self) -> ResumenBibliometrico:
        """Calcula el resumen agregado del dataset de la fuente Boletín SAO.

        :raises NotFoundError: si no existe ningún dataset procesado todavía.
        """
        dataset_path = _ultimo_dataset()
        if dataset_path is None:
            raise NotFoundError(
                "No hay dataset bibliométrico procesado. "
                "Ejecute el pipeline de ingesta del Boletín SAO."
            )

        registros = json.loads(dataset_path.read_text(encoding="utf-8"))

        por_anio = Counter(
            str(r["publication_year"]) for r in registros if r.get("publication_year")
        )
        por_volumen = Counter(
            str(r["volume"]) for r in registros if r.get("volume")
        )
        completitud = [
            CompletitudCampo(
                campo=campo,
                con_dato=sum(1 for r in registros if r.get(campo)),
                total=len(registros),
            )
            for campo in _CAMPOS_COMPLETITUD
        ]
        pendientes = sum(
            1 for r in registros if r.get("inclusion_status") == "PENDIENTE_REVISIÓN"
        )
        duplicados = sum(1 for r in registros if r.get("is_duplicate"))

        # --- Clasificación por OFC (si existe un dataset clasificado) --------
        clasificacion_disponible = False
        por_ofc: list[ConteoOFC] = []
        sin_ofc = 0
        clasificado_path = _ultimo_clasificado()
        if clasificado_path is not None:
            clasificacion_disponible = True
            clasificados = json.loads(clasificado_path.read_text(encoding="utf-8"))
            nombres = _nombres_ofc()
            dist = Counter()
            for r in clasificados:
                ofcs = r.get("ofcs") or []
                if not ofcs:
                    sin_ofc += 1
                for ofc_id in ofcs:
                    dist[ofc_id] += 1
            por_ofc = [
                ConteoOFC(ofc_id=ofc_id, nombre=nombres.get(ofc_id, ofc_id), conteo=n)
                for ofc_id, n in sorted(dist.items())
            ]

        return ResumenBibliometrico(
            fuente=FUENTE,
            total_articulos=len(registros),
            por_anio=[
                ConteoPorClave(clave=k, conteo=v) for k, v in sorted(por_anio.items())
            ],
            por_volumen=[
                ConteoPorClave(clave=k, conteo=v)
                for k, v in sorted(por_volumen.items(), key=lambda x: int(x[0]))
            ],
            completitud=completitud,
            pendientes_revision=pendientes,
            posibles_duplicados=duplicados,
            fecha_dataset=_fecha_desde_nombre(dataset_path),
            clasificacion_disponible=clasificacion_disponible,
            por_ofc=por_ofc,
            sin_ofc=sin_ofc,
        )

    def resumen_consolidado(self) -> ResumenConsolidado:
        """Calcula el resumen CONSOLIDADO de todas las fuentes procesadas.

        Descubre las subcarpetas bajo ``data/processed/``, agrupa los registros
        por su campo ``source`` y combina el conjunto por UNIÓN SIN EXCLUSIÓN,
        sin deduplicación entre fuentes (Req 6.6): solo cuenta la deduplicación
        básica ya realizada dentro de cada dataset. Sobre el conjunto combinado
        agrega total, distribución por año y por volumen, completitud,
        pendientes de revisión, posibles duplicados y el aporte por fuente
        (Req 6, 7).

        Las carpetas/archivos ``*_clasificado`` NO aportan artículos al total:
        solo alimentan la distribución por OFC (Req 6.7). Si no existe ningún
        dataset de fuente, devuelve un resumen vacío coherente (todo en 0) sin
        inventar datos (Req 6.5).

        A diferencia de :meth:`resumen`, no lanza ``NotFoundError``: el estado
        vacío es un resultado válido para que el frontend muestre un estado
        vacío honesto (Req 8.3).
        """
        # --- 1) Descubrir fuentes vs datasets clasificados -------------------
        carpetas_fuente: list[Path] = []
        carpetas_clasificado: list[Path] = []
        for carpeta in _carpetas_procesadas():
            if _es_carpeta_clasificado(carpeta):
                carpetas_clasificado.append(carpeta)
            else:
                carpetas_fuente.append(carpeta)

        # --- 2) Cargar y combinar registros de fuente (unión, sin dedup) -----
        # Agrupamos por el campo `source` de cada registro, no por el nombre de
        # la carpeta (Req 10.1). El nombre de carpeta solo sirve para localizar
        # el archivo y para detectar los *_clasificado.
        combinados: list[dict] = []
        por_fuente: dict[str, list[dict]] = defaultdict(list)
        fechas_dataset: list[str] = []
        for carpeta in carpetas_fuente:
            # Modelo ACUMULATIVO: se combinan TODOS los datasets de la carpeta
            # (todo el histórico de corridas de esa fuente), deduplicando por
            # article_id dentro de la fuente. Antes se tomaba solo el más
            # reciente (_ultimo_json); ahora se acumula el histórico.
            registros, fechas = _acumular_json(carpeta)
            if not registros:
                continue
            fechas_dataset.extend(fechas)
            for r in registros:
                # El nombre de la fuente proviene del propio registro; si falta,
                # usamos el nombre de la carpeta como respaldo (no se inventa un
                # valor "bonito": se refleja el origen tal cual).
                fuente = r.get("source") or carpeta.name
                por_fuente[fuente].append(r)
                combinados.append(r)

        # --- 3) Agregaciones sobre el conjunto combinado ---------------------
        por_anio = Counter(
            str(r["publication_year"]) for r in combinados if r.get("publication_year")
        )
        por_volumen = Counter(str(r["volume"]) for r in combinados if r.get("volume"))
        pendientes = sum(
            1 for r in combinados if r.get("inclusion_status") == "PENDIENTE_REVISIÓN"
        )
        duplicados = sum(1 for r in combinados if r.get("is_duplicate"))

        # --- 4) Aporte por fuente (información complementaria, Req 7) ---------
        aporte_por_fuente = [
            AporteFuente(
                fuente=fuente,
                total_articulos=len(registros),
                completitud=_completitud(registros),
            )
            for fuente, registros in sorted(por_fuente.items())
        ]

        # --- 5) Clasificación por OFC desde datasets *_clasificado (Req 6.7) -
        clasificacion_disponible = False
        por_ofc: list[ConteoOFC] = []
        sin_ofc = 0
        nombres = _nombres_ofc()
        dist: Counter = Counter()
        for carpeta in carpetas_clasificado:
            # Modelo ACUMULATIVO: se combinan TODOS los datasets clasificados de
            # la carpeta, deduplicando por article_id (el más reciente gana), de
            # modo que la distribución por OFC refleje el histórico acumulado y
            # sea coherente con el total acumulado de las fuentes.
            clasificados, _fechas_clasif = _acumular_json(carpeta)
            if not clasificados:
                continue
            clasificacion_disponible = True
            for r in clasificados:
                ofcs = r.get("ofcs") or []
                if not ofcs:
                    sin_ofc += 1
                for ofc_id in ofcs:
                    dist[ofc_id] += 1
        if clasificacion_disponible:
            por_ofc = [
                ConteoOFC(ofc_id=ofc_id, nombre=nombres.get(ofc_id, ofc_id), conteo=n)
                for ofc_id, n in sorted(dist.items())
            ]

        return ResumenConsolidado(
            total_articulos=len(combinados),
            por_anio=[
                ConteoPorClave(clave=k, conteo=v) for k, v in sorted(por_anio.items())
            ],
            por_volumen=[
                ConteoPorClave(clave=k, conteo=v)
                for k, v in sorted(por_volumen.items(), key=_clave_volumen)
            ],
            completitud=_completitud(combinados),
            pendientes_revision=pendientes,
            posibles_duplicados=duplicados,
            fechas_dataset=sorted(fechas_dataset),
            clasificacion_disponible=clasificacion_disponible,
            por_ofc=por_ofc,
            sin_ofc=sin_ofc,
            aporte_por_fuente=aporte_por_fuente,
        )
