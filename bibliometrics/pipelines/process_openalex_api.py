"""
process_openalex_api.py — Pipeline de ingesta por API de la fuente OpenAlex.

Consulta DIRECTAMENTE la API pública y gratuita de OpenAlex
(https://api.openalex.org, sin API key) con un ÚNICO comando de línea de
comandos y produce un dataset consolidado conforme al Article Data Contract V1.
Es el ESPEJO DELIBERADO de la vía manual con Publish or Perish
(``process_openalex.py``): misma carpeta de salida
(``data/processed/openalex/``), mismo ``source = "OpenAlex"`` y mismo esquema de
``article_id`` (prefijo ``oa-``), de modo que API y PoP cuentan como UNA sola
fuente y se deduplican juntas. Reutiliza los helpers compartidos de
``pipelines/_common.py`` SIN modificarlos.

Etapas (design.md, Architecture; structure.md §15):
    Consulta(s): términos + filtros de año (por CLI o archivo de config)
        -> ingestion/openalex_api_client.iter_works (paginación por cursor)
        -> ingestion/openalex_api_client.work_to_record (work -> ArticleRecord)
        -> validacion de periodo 2020-2030 (_common.validate_period)
        -> consolidacion de 1..N Consultas en un único dataset
        -> deteccion simple de duplicados por title (_common.mark_duplicates)
        -> JSON + CSV (_common.write_outputs)
        -> resumen de ingesta (recuperados / páginas / errores) + completitud

REGLAS (steering Componente B §4; design.md, Overview):
    - No inventa datos (hereda la lógica del conector).
    - No clasifica OFC (PENDING_VALIDATION); todos entran PENDIENTE_REVISIÓN.
    - No falsea el origen: source siempre "OpenAlex"; nunca otra fuente.
    - data/raw es INMUTABLE: NO se lee ni se escribe en data/raw/. La entrada
      del pipeline son las Consultas (CLI o archivo de config no secreto); la
      salida es ÚNICAMENTE data/processed/openalex/ (Req 6.4).
    - Sin secretos: la Mailto_Cortesia llega por la ENV OPENALEX_MAILTO vía
      ``resolve_mailto()``; es opcional y no es un secreto (Req 1.4, 1.5).

Manejo de errores (design.md, Error Handling):
    - Sin conectividad al iniciar (Req 2.4): si la PRIMERA solicitud falla por
      falta de conectividad (error de red/DNS), se registra un mensaje
      comprensible y se finaliza SIN escribir un dataset vacío.
    - Reintentos agotados en una página (Req 2.3): se registra la Consulta y la
      página afectada, se conserva lo ya recuperado y se continúa con las
      Consultas restantes; al final se escribe el dataset con lo recuperado y el
      resumen deja constancia de los errores (no se deja a medias en silencio).
    - Work individual malformado (Req 3.4): se descarta de forma robusta sin
      abortar la corrida.
    - Resumen final (Req 2.5, 6.2): works recuperados, páginas consultadas,
      errores encontrados, registros procesados y completitud por campo.

Uso (con el .venv activado) — un único comando, sin UI (Req 6.3):
    python bibliometrics/pipelines/process_openalex_api.py --term "bird conservation"
    python bibliometrics/pipelines/process_openalex_api.py \\
        --term "aves Colombia" --term "bird migration" \\
        --year-from 2020 --year-to 2030 --max-results 500
    python bibliometrics/pipelines/process_openalex_api.py --config consultas.json

Términos de búsqueda: son PROPUESTA del equipo a validar con SAO
(bibliometrics.md §2.1); no son criterio oficial de SAO.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
# Permite importar el conector (ingestion/) y los helpers (pipelines/).
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from ingestion.openalex_api_client import (  # noqa: E402
    ApiConfig,
    Consulta,
    HttpError,
    PERIODO_MAX,
    PERIODO_MIN,
    fetch_with_retry,
    resolve_api_key,
    resolve_mailto,
    work_to_record,
)
from pipelines._common import (  # noqa: E402
    mark_duplicates,
    print_summary,
    validate_period,
    write_outputs,
)

OUTPUT_DIR = _REPO_ROOT / "data" / "processed" / "openalex"
SOURCE_LABEL = "OpenAlex"
BASENAME = "openalex_dataset"

# Carpeta inmutable que el pipeline NUNCA debe tocar (Req 6.4).
_RAW_DIR = _REPO_ROOT / "data" / "raw"


# ---------------------------------------------------------------------------
# Detección de sin-conectividad (Req 2.4)
# ---------------------------------------------------------------------------
# El cliente HTTP (openalex_api_client) deja PROPAGAR el error de red/DNS de la
# sesión sin convertirlo en HttpError, para que el pipeline lo distinga de un
# error HTTP con código. Importamos el tipo de ``requests`` de forma tolerante:
# si ``requests`` no está instalado (p. ej. tests que inyectan una sesión
# simulada y nunca tocan la red), caemos a ``OSError`` como base razonable de
# los errores de conectividad de bajo nivel.
try:  # pragma: no cover - selección según entorno de ejecución
    from requests.exceptions import ConnectionError as _RequestsConnectionError
    from requests.exceptions import Timeout as _RequestsTimeout

    _CONNECTIVITY_ERRORS: tuple[type[BaseException], ...] = (
        _RequestsConnectionError,
        _RequestsTimeout,
        OSError,
    )
except ImportError:  # pragma: no cover - requests ausente en el entorno
    _CONNECTIVITY_ERRORS = (OSError,)


class _NoConnectivityError(Exception):
    """Marca interna de 'sin conectividad al iniciar' (Req 2.4).

    Se usa para abortar la corrida sin escribir ningún archivo cuando la PRIMERA
    solicitud a la API falla por falta de conectividad (red/DNS/timeout).
    """


@dataclass
class _IngestStats:
    """Contadores del resumen de ingesta (Req 2.5).

    :ivar works_recuperados: works crudos recuperados de la API (antes de
        transformar).
    :ivar paginas_consultadas: número total de páginas pedidas a la API.
    :ivar errores: número de errores encontrados (páginas con reintentos
        agotados o errores permanentes, y works malformados descartados).
    """

    works_recuperados: int = 0
    paginas_consultadas: int = 0
    errores: int = 0
    paginas_con_error: list[str] = field(default_factory=list)


def _crear_sesion() -> Any:
    """Crea la sesión HTTP real (``requests.Session``).

    Aislada en una función para poder sustituirla por una sesión simulada en los
    tests (inyección por el parámetro ``session`` de ``run_pipeline``) sin tocar
    la red real. El cliente HTTP no crea la sesión: la recibe inyectada.
    """
    import requests  # import local: solo se necesita en la corrida real.

    return requests.Session()


def _iter_consulta_pages(
    session: Any,
    consulta: Consulta,
    config: ApiConfig,
    stats: _IngestStats,
    *,
    es_primera_solicitud: bool,
) -> list[dict]:
    """Recupera TODOS los works de una ``Consulta`` paginando por cursor.

    A diferencia de ``iter_works`` (que oculta las páginas), aquí paginamos a
    nivel de página para poder (a) contar páginas, (b) registrar la ``Consulta``
    y la PÁGINA afectada cuando se agotan los reintentos (Req 2.3) y (c) detectar
    la falta de conectividad en la PRIMERA solicitud (Req 2.4).

    - Reintentos agotados / error permanente en una página → se registra el
      error indicando Consulta + número de página, se conserva lo ya recuperado
      de esta Consulta y se DETIENE esta Consulta (no hay cursor válido para
      continuar), devolviendo lo recuperado. El pipeline sigue con el resto.
    - Error de red/DNS en la PRIMERA solicitud de toda la corrida → se eleva
      ``_NoConnectivityError`` para abortar sin escribir (Req 2.4).

    :returns: lista de works crudos (dicts) recuperados de esta ``Consulta``.
    """
    import time

    max_results = config.max_results
    if max_results is not None and max_results <= 0:
        return []

    recuperados: list[dict] = []
    cursor: Optional[str] = "*"
    pagina = 0
    primera_pagina_consulta = True

    while cursor is not None:
        if not primera_pagina_consulta and config.pace_seconds > 0:
            time.sleep(config.pace_seconds)

        pagina += 1
        try:
            results, next_cursor = fetch_with_retry(session, consulta, cursor, config)
        except HttpError as exc:
            # Reintentos agotados (transitorio) o error permanente (p. ej. 400):
            # registrar Consulta + página, conservar lo recuperado y detener esta
            # Consulta; el pipeline continúa con las restantes (Req 2.3).
            stats.paginas_consultadas += 1
            stats.errores += 1
            etiqueta = (
                f"Consulta '{consulta.term}' "
                f"({consulta.year_from}-{consulta.year_to}), página {pagina}"
            )
            stats.paginas_con_error.append(etiqueta)
            print(
                f"  [ERR ] {etiqueta} -> HTTP {exc.status_code} "
                f"({'transitorio' if exc.transient else 'permanente'}); "
                f"se conservan {len(recuperados)} work(s) recuperado(s) de esta "
                f"Consulta y se continúa con el resto."
            )
            return recuperados
        except _CONNECTIVITY_ERRORS as exc:
            stats.paginas_consultadas += 1
            if es_primera_solicitud and primera_pagina_consulta:
                # Sin conectividad al iniciar: abortar sin escribir (Req 2.4).
                raise _NoConnectivityError(str(exc)) from exc
            # Pérdida de conectividad a mitad de corrida: tratar como error de
            # página, conservar lo recuperado y continuar con el resto.
            stats.errores += 1
            etiqueta = (
                f"Consulta '{consulta.term}' "
                f"({consulta.year_from}-{consulta.year_to}), página {pagina}"
            )
            stats.paginas_con_error.append(etiqueta)
            print(
                f"  [ERR ] {etiqueta} -> error de red/conectividad: {exc}; "
                f"se conservan {len(recuperados)} work(s) y se continúa."
            )
            return recuperados

        primera_pagina_consulta = False
        stats.paginas_consultadas += 1

        if not results:
            break

        for work in results:
            recuperados.append(work)
            if max_results is not None and len(recuperados) >= max_results:
                return recuperados

        cursor = next_cursor

    return recuperados


def _transformar_works(works: list[dict], stats: _IngestStats) -> list:
    """Transforma works crudos en ``ArticleRecord`` descartando malformados.

    Un work individual malformado (``work_to_record`` lanza) se descarta de
    forma robusta sin abortar la corrida (Req 3.4, Req 2.3); se cuenta como
    error en el resumen. Tras transformar se aplica ``validate_period`` a cada
    registro (de ``_common``, sin cambios).
    """
    records: list = []
    for idx, work in enumerate(works):
        if not isinstance(work, dict):
            stats.errores += 1
            print(
                f"  [DESCARTE] work #{idx}: entrada malformada "
                f"(no es un objeto); se descarta y continúa."
            )
            continue
        try:
            rec = work_to_record(work)
        except Exception as exc:  # noqa: BLE001 — un work roto no tumba la corrida
            stats.errores += 1
            print(
                f"  [DESCARTE] work #{idx}: no transformable ({exc}); "
                f"se descarta y continúa."
            )
            continue
        validate_period(rec)
        records.append(rec)
    return records


def run_pipeline(
    consultas: list[Consulta],
    config: ApiConfig,
    *,
    session: Optional[Any] = None,
    out_dir: Path = OUTPUT_DIR,
) -> tuple[list, _IngestStats, Optional[Path], Optional[Path]]:
    """Ejecuta el pipeline para 1..N ``Consulta``s y escribe el dataset.

    Combina los resultados de todas las ``Consulta``s en un ÚNICO dataset
    (Req 5.2), marca duplicados sobre el conjunto COMBINADO con
    ``mark_duplicates`` (Req 5.1) y escribe JSON+CSV con ``write_outputs``
    (Req 6.1). El cliente HTTP se inyecta por ``session`` (para tests sin red);
    si es ``None``, se crea una sesión real.

    :returns: ``(records, stats, json_path, csv_path)``. ``json_path`` y
        ``csv_path`` son ``None`` si no se escribió nada (sin registros válidos).
    :raises _NoConnectivityError: si la PRIMERA solicitud falla por falta de
        conectividad (el llamador NO debe escribir dataset — Req 2.4).
    """
    if session is None:
        session = _crear_sesion()

    stats = _IngestStats()
    todos_los_works: list[dict] = []

    print(f"Consultando la API_OpenAlex para {len(consultas)} Consulta(s)\n")
    es_primera_solicitud = True
    for consulta in consultas:
        print(
            f"  -> Consulta '{consulta.term}' "
            f"({consulta.year_from}-{consulta.year_to})"
        )
        works = _iter_consulta_pages(
            session,
            consulta,
            config,
            stats,
            es_primera_solicitud=es_primera_solicitud,
        )
        es_primera_solicitud = False
        stats.works_recuperados += len(works)
        todos_los_works.extend(works)

    # Transformación work -> ArticleRecord (descarta malformados) + período.
    records = _transformar_works(todos_los_works, stats)

    # Deduplicación básica sobre el conjunto COMBINADO de todas las Consultas.
    mark_duplicates(records)

    json_path: Optional[Path] = None
    csv_path: Optional[Path] = None
    if records:
        json_path, csv_path = write_outputs(records, out_dir, BASENAME)

    return records, stats, json_path, csv_path


def _print_ingest_summary(stats: _IngestStats, procesados: int) -> None:
    """Resumen de ingesta: recuperados / páginas / errores (Req 2.5, 6.2)."""
    print("\n" + "=" * 60)
    print(f"RESUMEN DE INGESTA — Fuente: {SOURCE_LABEL}")
    print("=" * 60)
    print(f"  Works recuperados     : {stats.works_recuperados}")
    print(f"  Páginas consultadas   : {stats.paginas_consultadas}")
    print(f"  Errores encontrados   : {stats.errores}")
    print(f"  Registros procesados  : {procesados}")
    if stats.paginas_con_error:
        print("  Páginas con error     :")
        for etiqueta in stats.paginas_con_error:
            print(f"    - {etiqueta}")


# ---------------------------------------------------------------------------
# Lectura de Consultas desde CLI / archivo de configuración (nunca data/raw)
# ---------------------------------------------------------------------------
def _consultas_desde_config(path: Path, year_from: int, year_to: int) -> list[Consulta]:
    """Lee las ``Consulta``s de un archivo de configuración JSON no secreto.

    Formato aceptado (flexible, sin secretos):
        ["term1", "term2", ...]
    o:
        {"consultas": [
            {"term": "...", "year_from": 2020, "year_to": 2030},
            {"term": "..."}
        ]}

    Los años por defecto son los del CLI (``--year-from`` / ``--year-to``) cuando
    una entrada no los especifica. NUNCA se leen Consultas de ``data/raw/``.
    """
    data = json.loads(path.read_text(encoding="utf-8"))

    entradas: list
    if isinstance(data, dict):
        entradas = data.get("consultas") or []
    elif isinstance(data, list):
        entradas = data
    else:
        raise ValueError(
            "El archivo de configuración debe ser una lista de términos o un "
            "objeto con la clave 'consultas'."
        )

    consultas: list[Consulta] = []
    for entrada in entradas:
        if isinstance(entrada, str):
            term = entrada.strip()
            if term:
                consultas.append(Consulta(term=term, year_from=year_from, year_to=year_to))
        elif isinstance(entrada, dict):
            term = str(entrada.get("term", "")).strip()
            if not term:
                continue
            yf = int(entrada.get("year_from", year_from))
            yt = int(entrada.get("year_to", year_to))
            consultas.append(Consulta(term=term, year_from=yf, year_to=yt))
    return consultas


def _build_consultas(args: argparse.Namespace) -> list[Consulta]:
    """Construye las ``Consulta``s a partir de los argumentos del CLI."""
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = _REPO_ROOT / config_path
        # Guardarraíl: el archivo de config NO puede vivir en data/raw/ (Req 6.4).
        try:
            config_path.resolve().relative_to(_RAW_DIR.resolve())
            raise SystemExit(
                "El archivo de configuración no puede estar en data/raw/ "
                "(carpeta inmutable). Colóquelo fuera de data/raw/."
            )
        except ValueError:
            pass  # No está bajo data/raw/: correcto.
        if not config_path.is_file():
            raise SystemExit(f"No se encontró el archivo de configuración: {config_path}")
        return _consultas_desde_config(config_path, args.year_from, args.year_to)

    return [
        Consulta(term=term, year_from=args.year_from, year_to=args.year_to)
        for term in args.term
    ]


def _build_config(args: argparse.Namespace) -> ApiConfig:
    """Construye la ``ApiConfig`` desde la ENV (Req 1.4, 7.1–7.3).

    - ``mailto``: polite pool opcional, de ``OPENALEX_MAILTO`` (Req 1.4).
    - ``api_key``: API key de ``OPENALEX_API_KEY``, que habilita la paginación
      por cursor más allá de la primera página (Req 7.1–7.3). Es un SECRETO: se
      resuelve por entorno y nunca se imprime. El default de ``--max-results``
      sigue siendo ``None`` (el 5.000 es un valor recomendado documentado, no el
      default del código — Req 11.8).
    """
    return ApiConfig(
        per_page=args.per_page,
        max_results=args.max_results,
        pace_seconds=args.pace_seconds,
        max_retries=args.max_retries,
        mailto=resolve_mailto(),
        api_key=resolve_api_key(),
    )


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline de ingesta OpenAlex por API (consulta directa, un único "
            "comando, sin UI). Escribe en data/processed/openalex/."
        ),
    )
    parser.add_argument(
        "--term", action="append", default=[], metavar="TÉRMINO",
        help=(
            "Término de búsqueda de una Consulta. Repetible para varias "
            "Consultas (p. ej. --term 'aves' --term 'bird conservation'). "
            "Propuesta del equipo a validar con SAO."
        ),
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help=(
            "Archivo JSON (no secreto) con las Consultas. Alternativa a --term. "
            "Nunca debe estar en data/raw/."
        ),
    )
    parser.add_argument(
        "--year-from", type=int, default=PERIODO_MIN, dest="year_from",
        help=f"Año inicial del Período_Inclusión (por defecto {PERIODO_MIN}).",
    )
    parser.add_argument(
        "--year-to", type=int, default=PERIODO_MAX, dest="year_to",
        help=f"Año final del Período_Inclusión (por defecto {PERIODO_MAX}).",
    )
    parser.add_argument(
        "--per-page", type=int, default=200, dest="per_page",
        help="Tamaño de página solicitado a la API (máx. 200).",
    )
    parser.add_argument(
        "--max-results", type=int, default=None, dest="max_results",
        help="Límite máximo de works por Consulta (por defecto sin límite).",
    )
    parser.add_argument(
        "--pace-seconds", type=float, default=0.2, dest="pace_seconds",
        help="Pausa entre páginas para acotar el ritmo de solicitudes.",
    )
    parser.add_argument(
        "--max-retries", type=int, default=5, dest="max_retries",
        help="Reintentos por página ante errores transitorios (429/5xx).",
    )
    return parser.parse_args(argv)


def _load_env_file() -> None:
    """Carga variables desde el archivo ``.env`` de la raíz del repo, si existe.

    Usa python-dotenv SIN sobrescribir el entorno ya definido: una variable
    exportada en la terminal (p. ej. ``OPENALEX_API_KEY``) tiene prioridad sobre
    el ``.env``. Esto replica el comportamiento del backend, que ya carga
    ``.env`` vía pydantic-settings (backend/src/core/config.py).

    La dependencia es OPCIONAL: si python-dotenv no está instalado, el pipeline
    sigue funcionando y las variables deben venir del entorno del proceso. El
    valor de la API key NUNCA se imprime (Req 7.4, estrategia-bibliometrica-api).
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return  # dependencia opcional ausente: se usa solo el entorno.
    env_path = _REPO_ROOT / ".env"
    if env_path.is_file():
        # override=False: lo ya exportado en el entorno gana sobre el .env.
        load_dotenv(dotenv_path=env_path, override=False)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    # Carga .env (si existe) antes de resolver la configuración, de modo que
    # OPENALEX_API_KEY / OPENALEX_MAILTO del .env estén disponibles para
    # _build_config() sin exportarlas manualmente en cada terminal.
    _load_env_file()

    consultas = _build_consultas(args)
    if not consultas:
        print(
            "(info) No se indicó ninguna Consulta. Use --term 'búsqueda' "
            "(repetible) o --config archivo.json. Finalizando sin registros."
        )
        return 0

    config = _build_config(args)

    try:
        records, stats, json_path, csv_path = run_pipeline(consultas, config)
    except _NoConnectivityError as exc:
        # Sin conectividad al iniciar: mensaje comprensible y NO escribir nada
        # (Req 2.4). No se genera ningún archivo en data/processed/openalex/.
        print(
            "\n[ERROR] No hay conectividad con la API_OpenAlex al iniciar "
            f"({exc}). No se escribió ningún Dataset_Procesado para no generar "
            "un resultado vacío que pueda confundirse con datos reales. "
            "Verifique su conexión a internet e intente de nuevo."
        )
        return 2

    procesados = len(records)
    _print_ingest_summary(stats, procesados)

    if not records:
        print(
            "\nNo se produjeron registros válidos a partir de las Consultas "
            "(no se escribió dataset)."
        )
        return 0

    print_summary(records, SOURCE_LABEL)
    print("\nArchivos generados:")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
