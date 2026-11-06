"""
openalex_api_client.py — Conector de la API pública de OpenAlex (Componente B).

OBJETIVO:
  Consultar directamente la API pública y gratuita de OpenAlex
  (https://api.openalex.org, sin API key) para obtener ``work``s y, en una capa
  posterior, transformarlos al Article Data Contract V1 (``ArticleRecord``).

  Esta vía por API es el ESPEJO deliberado de la vía manual con Publish or Perish
  (``extract_openalex.py``): misma fuente fija (``"OpenAlex"``), mismo esquema de
  ``article_id`` (prefijo ``oa-``) y misma carpeta de salida
  (``data/processed/openalex/``), de modo que ambas rutas cuentan como una sola
  fuente y se deduplican juntas (design.md, Architecture).

SEPARACIÓN DE CAPAS (design.md, Architecture):
  La CAPA HTTP (este archivo, tarea 2.1) NO conoce el contrato V1: solo construye
  la ``Consulta``, pagina por cursor, aplica ritmo, reintenta errores
  transitorios y detecta la falta de conectividad. La TRANSFORMACIÓN
  ``work`` → ``ArticleRecord`` (``reconstruct_abstract``, ``_api_make_article_id``,
  ``work_to_record``) es una CAPA SEPARADA (tarea 3.1) que se añade a este mismo
  módulo más adelante y que no conoce HTTP. Esto permite probar paginación y
  reintentos con el cliente HTTP simulado (sin red real) y la transformación con
  ``work``s sintéticos ``DEMO_DATA``.

REGLAS HEREDADAS DEL STEERING (bibliometrics.md §4, tech.md §19–20):
  - Sin secretos en el repo: la ``Mailto_Cortesia`` (polite pool) llega por la
    variable de entorno ``OPENALEX_MAILTO``; es OPCIONAL y NO es un secreto.
    Nunca se exige ni se lee de un archivo versionado.
  - La capa HTTP no escribe nada en disco; el pipeline (tarea 4.1) es quien
    escribe, y solo en ``data/processed/openalex/`` (``data/raw/`` es inmutable).

ALCANCE DE ESTE ARCHIVO (tarea 2.1 — SOLO capa HTTP):
  - Constantes de la fuente y del endpoint.
  - ``Consulta`` y ``ApiConfig`` (dataclasses inmutables).
  - ``HttpError`` clasificable como transitorio/permanente.
  - ``resolve_mailto`` (lectura opcional de la ENV).
  - ``fetch_page`` / ``fetch_with_retry`` / ``iter_works`` (paginación por cursor,
    ritmo, reintentos con espera creciente, propagación de sin-conectividad).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Iterator, Optional

# --- Constantes de la fuente y del endpoint ----------------------------------
# ``source`` fijo = igual que la vía PoP (``extract_openalex.py``) para que API y
# PoP cuenten como la misma fuente (design.md, Data Models).
OPENALEX_SOURCE = "OpenAlex"
# Método de extracción propio de la vía API (distinto del de PoP) — Req 8.1.
OPENALEX_API_EXTRACTION_METHOD = "OpenAlex API V1"
# Endpoint público de works (sin API key).
OPENALEX_BASE_URL = "https://api.openalex.org/works"
# Periodo de inclusión V1 (mismo rango que ``_common.PERIODO_MIN/MAX``).
PERIODO_MIN, PERIODO_MAX = 2020, 2030
# Variable de entorno del polite pool. Opcional, NO secreto (Req 1.4, 9.2).
MAILTO_ENV_VAR = "OPENALEX_MAILTO"
# Variable de entorno de la API key de OpenAlex. SECRETO: solo por entorno;
# habilita la paginación por cursor más allá de la primera página (Req 7.1–7.3).
API_KEY_ENV_VAR = "OPENALEX_API_KEY"

# Límite máximo de ``per_page`` que admite OpenAlex.
_MAX_PER_PAGE = 200


@dataclass(frozen=True)
class Consulta:
    """Parámetros de una búsqueda a la API_OpenAlex (Req 1, 4.1).

    :param term: término/expresión de búsqueda. Es una PROPUESTA del equipo, a
        validar con SAO; no es un criterio oficial de SAO.
    :param year_from: año inicial del filtro de período (por defecto 2020).
    :param year_to: año final del filtro de período (por defecto 2030).

    Ambos años acotan el Período_Inclusión 2020–2030 mediante el filtro de año
    que se envía a la API (``publication_year:{from}-{to}``). La ``Consulta`` es
    inmutable para poder usarse como clave reproducible del resumen de ingesta.
    """

    term: str
    year_from: int = PERIODO_MIN
    year_to: int = PERIODO_MAX


@dataclass(frozen=True)
class ApiConfig:
    """Configuración operativa del cliente HTTP (todo configurable).

    :param per_page: tamaño de página solicitado a la API (máx. 200 — Req 1.3).
    :param max_results: límite máximo de works por ``Consulta``; ``None`` = sin
        límite (recupera todo el conjunto hasta agotar el cursor).
    :param pace_seconds: pausa entre páginas para acotar el ritmo (Req 2.1).
    :param max_retries: reintentos por página ante errores transitorios (Req 2.2).
    :param backoff_base: base de la espera creciente entre reintentos (segundos).
    :param mailto: correo del polite pool; viene de la ENV (Req 1.4). Opcional.
    :param api_key: API key de OpenAlex; viene de la ENV ``OPENALEX_API_KEY``
        (Req 7.1–7.3). Opcional; es un SECRETO: no se valida (una validación
        podría filtrar el valor en un mensaje de error — Req 7.4) ni se imprime.

    :raises ValueError: si ``per_page`` no está en el rango ``1..200`` o si algún
        parámetro de ritmo/reintentos es negativo (configuración inválida que no
        debe pasar silenciosamente).
    """

    per_page: int = _MAX_PER_PAGE
    max_results: Optional[int] = None
    pace_seconds: float = 0.2
    max_retries: int = 5
    backoff_base: float = 1.0
    mailto: Optional[str] = None
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        if not (1 <= self.per_page <= _MAX_PER_PAGE):
            raise ValueError(
                f"per_page debe estar entre 1 y {_MAX_PER_PAGE}; "
                f"recibido {self.per_page}."
            )
        if self.max_results is not None and self.max_results < 0:
            raise ValueError(
                f"max_results no puede ser negativo; recibido {self.max_results}."
            )
        if self.pace_seconds < 0:
            raise ValueError(
                f"pace_seconds no puede ser negativo; recibido {self.pace_seconds}."
            )
        if self.max_retries < 0:
            raise ValueError(
                f"max_retries no puede ser negativo; recibido {self.max_retries}."
            )
        if self.backoff_base < 0:
            raise ValueError(
                f"backoff_base no puede ser negativo; recibido {self.backoff_base}."
            )


class HttpError(Exception):
    """Error HTTP de la API, clasificable como transitorio o permanente.

    :param status_code: código HTTP devuelto por la API (p. ej. 429, 500, 400).
    :param transient: ``True`` si el error es transitorio y conviene reintentar
        (429 "Too Many Requests" o 5xx del servidor); ``False`` si es permanente
        (p. ej. 400) y reintentarlo no tiene sentido.
    :param message: mensaje legible opcional.

    La capa de reintentos (``fetch_with_retry``) usa ``transient`` para decidir
    si reintenta o propaga de inmediato.
    """

    def __init__(
        self,
        status_code: int,
        transient: bool,
        message: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.transient = transient
        super().__init__(
            message
            or f"HTTP {status_code} ({'transitorio' if transient else 'permanente'})"
        )


def _is_transient_status(status_code: int) -> bool:
    """Clasifica un código HTTP como transitorio (reintentable) o no.

    Transitorios: 429 (rate limit) y cualquier 5xx del servidor. El resto
    (incluidos los 4xx distintos de 429, p. ej. 400) se tratan como permanentes.
    """
    return status_code == 429 or 500 <= status_code <= 599


def resolve_mailto() -> Optional[str]:
    """Lee ``OPENALEX_MAILTO`` del entorno; ``None`` si no está (Req 1.4, 1.5).

    El polite pool de OpenAlex mejora el servicio cuando se envía un ``mailto``,
    pero es OPCIONAL: el cliente funciona sin él. Esta función NUNCA exige la
    variable ni la lee de un archivo versionado; solo consulta el entorno del
    proceso. Un valor vacío o solo espacios se trata como ausente.
    """
    value = os.environ.get(MAILTO_ENV_VAR)
    if value is None:
        return None
    value = value.strip()
    return value or None


def resolve_api_key() -> Optional[str]:
    """Lee ``OPENALEX_API_KEY`` del entorno; ``None`` si no está (Req 7.2, 7.3).

    OpenAlex **exige** la API key gratuita para continuar la paginación por
    cursor más allá de la primera página (sin key, seguir ``next_cursor``
    devuelve HTTP 401). La key es un SECRETO: esta función la obtiene ÚNICAMENTE
    del entorno del proceso y NUNCA la lee de un archivo versionado (Req 7.3).
    Un valor ausente, vacío o solo espacios se trata como ausente (``None``); un
    valor no vacío se devuelve recortado. No se registra ni se imprime el valor.
    """
    value = os.environ.get(API_KEY_ENV_VAR)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _build_params(consulta: Consulta, cursor: str, config: ApiConfig) -> dict[str, Any]:
    """Construye los parámetros de query para UNA página de ``works``.

    - ``search``: el término de la ``Consulta`` (propuesta del equipo).
    - ``filter``: acota el período con ``publication_year:{from}-{to}`` (Req 1.2).
    - ``per_page`` y ``cursor``: paginación por cursor (Req 1.3).
    - ``mailto``: solo si está configurado (polite pool, opcional — Req 1.4).
    - ``api_key``: solo si está configurada (habilita la paginación por cursor
      más allá de la primera página — Req 7.1, 7.2).

    Capa HTTP pura: no transforma works, solo arma la petición. NO imprime ni
    registra el valor de ``api_key`` (Req 7.4).
    """
    params: dict[str, Any] = {
        "search": consulta.term,
        "filter": f"publication_year:{consulta.year_from}-{consulta.year_to}",
        "per_page": config.per_page,
        "cursor": cursor,
    }
    if config.mailto:
        params["mailto"] = config.mailto
    if config.api_key:
        params["api_key"] = config.api_key
    return params


def fetch_page(
    session: Any,
    consulta: Consulta,
    cursor: str,
    config: ApiConfig,
) -> tuple[list[dict], Optional[str]]:
    """Pide UNA página de ``works`` a la API y devuelve ``(results, next_cursor)``.

    - Envía ``search`` (término), ``filter=publication_year:{from}-{to}``,
      ``per_page`` y ``cursor``; añade ``mailto`` si está configurado (Req 1.4).
    - ``next_cursor`` es ``meta.next_cursor`` de OpenAlex; ``None`` cuando ya no
      hay más páginas (fin de la paginación).

    Capa HTTP PURA: NO transforma los works; devuelve la lista cruda de dicts
    tal como vienen en ``results``. En fallo HTTP lanza ``HttpError`` clasificado
    como transitorio/permanente para que ``fetch_with_retry`` decida.

    :param session: objeto con un método ``get(url, params=..., timeout=...)``
        estilo ``requests.Session`` (se inyecta para poder simularlo en tests;
        la capa HTTP no crea la sesión).
    :raises HttpError: ante un código HTTP de error (clasificado por
        ``_is_transient_status``).

    Detección de sin-conectividad (Req 2.4): un error de red/DNS lanzado por la
    sesión (p. ej. ``requests.ConnectionError``) NO se captura aquí; se deja
    propagar para que el pipeline lo clasifique y muestre un mensaje comprensible
    sin escribir un dataset vacío.
    """
    params = _build_params(consulta, cursor, config)

    # El error de red/DNS de la sesión se propaga tal cual (Req 2.4): no lo
    # convertimos en HttpError porque no es un código HTTP, es ausencia de
    # conectividad, y el pipeline debe distinguirlo.
    response = session.get(OPENALEX_BASE_URL, params=params, timeout=30)

    status_code = getattr(response, "status_code", 200)
    if status_code >= 400:
        raise HttpError(
            status_code=status_code,
            transient=_is_transient_status(status_code),
            message=(
                f"La API_OpenAlex respondió HTTP {status_code} para la búsqueda "
                f"'{consulta.term}' ({consulta.year_from}-{consulta.year_to})."
            ),
        )

    payload = response.json()
    results = payload.get("results") or []
    if not isinstance(results, list):
        results = []
    meta = payload.get("meta") or {}
    next_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None

    return results, next_cursor


def fetch_with_retry(
    session: Any,
    consulta: Consulta,
    cursor: str,
    config: ApiConfig,
) -> tuple[list[dict], Optional[str]]:
    """Envuelve ``fetch_page`` con reintentos y espera creciente (Req 2.2).

    - Reintenta SOLO errores transitorios (429, 5xx) hasta ``config.max_retries``
      intentos adicionales, con espera creciente ``backoff_base * (intento+1)``.
    - Un error permanente (p. ej. 400) NO se reintenta: se propaga de inmediato.
    - Agotados los reintentos, propaga el último ``HttpError`` para que el
      pipeline lo registre (``Consulta`` + página) y continúe con el resto
      (Req 2.3).

    Los errores de red/DNS (sin-conectividad, Req 2.4) NO son ``HttpError`` y se
    propagan sin reintentar: la detección de conectividad la maneja el pipeline.
    """
    attempt = 0
    while True:
        try:
            return fetch_page(session, consulta, cursor, config)
        except HttpError as exc:
            # Permanente: no reintentar.
            if not exc.transient:
                raise
            # Transitorio pero sin reintentos restantes: propagar.
            if attempt >= config.max_retries:
                raise
            # Espera creciente antes del siguiente intento.
            wait = config.backoff_base * (attempt + 1)
            if wait > 0:
                time.sleep(wait)
            attempt += 1


def iter_works(
    session: Any,
    consulta: Consulta,
    config: ApiConfig,
) -> Iterator[dict]:
    """Itera TODOS los works de una ``Consulta`` paginando por cursor (Req 1.3).

    - Comienza con ``cursor="*"`` (inicio de la paginación por cursor de OpenAlex).
    - Aplica ``config.pace_seconds`` entre páginas para acotar el ritmo (Req 2.1).
    - Se detiene al agotar el cursor (``next_cursor is None``), cuando una página
      vuelve vacía, o al alcanzar ``config.max_results`` works (nunca entrega más
      que el límite).
    - Hace ``yield`` de cada ``work`` CRUDO (dict JSON de la API). NO transforma
      ni escribe nada (la transformación es la capa de la tarea 3.1).

    La propagación de ``HttpError`` (reintentos agotados) y de los errores de
    red/DNS (sin-conectividad) la decide ``fetch_with_retry`` / ``fetch_page``; el
    pipeline que consume este iterador es quien los maneja (Req 2.3, 2.4).
    """
    max_results = config.max_results
    if max_results is not None and max_results <= 0:
        return

    cursor: Optional[str] = "*"
    yielded = 0
    first_page = True

    while cursor is not None:
        if not first_page and config.pace_seconds > 0:
            time.sleep(config.pace_seconds)
        first_page = False

        results, next_cursor = fetch_with_retry(session, consulta, cursor, config)

        if not results:
            break

        for work in results:
            yield work
            yielded += 1
            if max_results is not None and yielded >= max_results:
                return

        cursor = next_cursor


# =============================================================================
# CAPA DE TRANSFORMACIÓN — work (JSON nativo de la API) → ArticleRecord V1
# (tarea 3.1). Esta capa NO conoce HTTP: opera sobre ``work``s ya recuperados
# (dicts crudos de la API) y produce registros conforme al Article Data
# Contract V1. Se mantiene en este mismo módulo como espejo de la vía PoP
# (``extract_openalex.py``), compartiendo el esquema de ``article_id`` (prefijo
# ``oa-``) para que el MISMO work produzca el MISMO id por API o por PoP y ambos
# cuenten como la fuente "OpenAlex" (design.md, Data Models).
#
# REGLAS HEREDADAS (steering Componente B §4; design.md, Overview):
#   - No inventar: campo ausente en el ``work`` → ``None`` (Req 3.3).
#   - Obligatorio (title/authors/publication_year) faltante o ambiguo →
#     ``inclusion_status = "PENDIENTE_REVISIÓN"`` con nota (Req 3.4, 4.3).
#   - Año fuera de 2020–2030 → PENDIENTE_REVISIÓN con nota, sin descartar
#     (Req 4.2). Año no detectable → ``publication_year = None`` + revisión.
#   - No clasifica OFC ni relevancia (``PENDING_VALIDATION`` — Req 4.5).
#   - ``source`` fijo = "OpenAlex"; ``extraction_method`` = "OpenAlex API V1".
#
# MAPEO FINO: se sigue la tabla del diseño (design.md, Data Models). Solo se
# leen claves que aparecen en el esquema documentado de ``works`` de OpenAlex;
# no se inventan claves. Una clave ausente simplemente deja el campo en ``None``.
# =============================================================================

import datetime as _dt
import hashlib

# Contrato de datos compartido (Article Data Contract V1). Se importa de forma
# tolerante tanto si el módulo se usa como paquete (``bibliometrics.ingestion``)
# como por ruta relativa al repo, igual que hace ``extract_openalex.py``.
try:  # pragma: no cover - selección de import según contexto de ejecución
    from ingestion.article_record import ArticleRecord  # type: ignore
    from pipelines._common import norm_title  # type: ignore
except ImportError:  # pragma: no cover
    import sys as _sys
    from pathlib import Path as _Path

    _REPO_ROOT = _Path(__file__).resolve().parents[2]
    _BIBLIO = str(_REPO_ROOT / "bibliometrics")
    if _BIBLIO not in _sys.path:
        _sys.path.insert(0, _BIBLIO)
    from ingestion.article_record import ArticleRecord  # type: ignore  # noqa: E402
    from pipelines._common import norm_title  # type: ignore  # noqa: E402


def reconstruct_abstract(inverted_index: Optional[dict]) -> Optional[str]:
    """Reconstruye el texto del ``abstract`` desde el índice invertido (Req 3.7).

    OpenAlex no entrega el resumen como texto plano sino como un **índice
    invertido** ``{palabra: [posiciones...]}``. Esta función coloca cada palabra
    en todas las posiciones indicadas y concatena las palabras en orden
    ASCENDENTE de posición, unidas por espacios.

    - Índice ausente (``None``), vacío o no-dict → ``None`` (no se inventa texto).
    - No se inventan palabras para posiciones que el índice no contiene: el texto
      resultante preserva solo lo que el índice aporta, en orden de posición.
    - Posiciones no enteras o negativas se ignoran de forma robusta (un índice
      malformado no debe tumbar la transformación).

    :param inverted_index: el ``abstract_inverted_index`` del ``work`` de la API.
    :returns: el abstract reconstruido, o ``None`` si no hay índice utilizable.
    """
    if not inverted_index or not isinstance(inverted_index, dict):
        return None

    # (posición, palabra) por cada aparición registrada en el índice.
    placed: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        if not isinstance(word, str) or not isinstance(positions, (list, tuple)):
            continue
        for pos in positions:
            if isinstance(pos, bool):  # bool es subtipo de int; excluir explícito.
                continue
            if isinstance(pos, int) and pos >= 0:
                placed.append((pos, word))

    if not placed:
        return None

    placed.sort(key=lambda item: item[0])
    text = " ".join(word for _pos, word in placed).strip()
    return text or None


def _hash12(text: str) -> str:
    """Primeros 12 caracteres hex del SHA-256 de ``text`` (determinista).

    Idéntico a ``extract_openalex._hash12`` para garantizar el MISMO
    ``article_id`` entre la vía API y la vía PoP (Req 3.6).
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _norm_doi(doi: str) -> str:
    """Normaliza un DOI para el hash: minúsculas y sin espacios alrededor.

    Idéntico a ``extract_openalex._norm_doi``. Nota: el pelado del prefijo
    ``https://doi.org/`` del DOI se aplica en ``work_to_record`` ANTES de pasar
    el DOI a esta función, de modo que el valor normalizado coincide con el que
    produce la vía PoP (donde el export de PoP ya trae el DOI pelado).
    """
    return doi.strip().lower()


def _api_make_article_id(
    doi: Optional[str],
    title: Optional[str],
    year: Optional[int],
) -> str:
    """Identificador interno determinista para OpenAlex por API (Req 3.6).

    MISMO esquema que la vía PoP (``extract_openalex._make_article_id``):

    - Con DOI: ``oa-<hash12(doi normalizado)>``.
    - Sin DOI: ``oa-<hash12(norm_title(title) + "|" + año)>``.

    ``hash12`` = primeros 12 hex de SHA-256; ``norm_title`` se reutiliza de
    ``_common.py`` sin modificarlo. Como el DOI se pela del prefijo
    ``https://doi.org/`` en ``work_to_record``, el MISMO work produce el MISMO
    id por API o por PoP, por lo que ambas rutas cuentan como la misma fuente y
    se deduplican juntas. Si no hay ni DOI ni título/año utilizables, el hash se
    calcula sobre la cadena disponible (p. ej. ``"|"``), manteniendo determinismo.
    """
    if doi:
        return "oa-" + _hash12(_norm_doi(doi))
    base = f"{norm_title(title)}|{year if year is not None else ''}"
    return "oa-" + _hash12(base)


def _clean_str(value: Any) -> Optional[str]:
    """Normaliza un valor de la API a texto no vacío o ``None`` (sin inventar).

    Conservador: ``str`` → recortado; vacío → ``None``. Cualquier otro escalar
    (números) → su representación textual. No aplana estructuras complejas aquí;
    el mapeo de objetos anidados (autores, revista, biblio) se hace de forma
    explícita en ``work_to_record`` siguiendo la tabla del diseño.
    """
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        s = str(value).strip()
        return s or None
    return None


def _strip_doi_prefix(doi: Any) -> Optional[str]:
    """Pela el prefijo ``https://doi.org/`` del DOI nativo de OpenAlex.

    OpenAlex expone ``work["doi"]`` como URL completa (p. ej.
    ``https://doi.org/10.1234/abc``). Se devuelve solo el DOI (``10.1234/abc``)
    para que coincida con el DOI pelado que trae el export de PoP, de modo que
    el ``article_id`` sea el mismo por ambas vías (Req 3.6). Campo ausente →
    ``None`` (no se inventa).
    """
    s = _clean_str(doi)
    if s is None:
        return None
    low = s.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
        if low.startswith(prefix):
            return s[len(prefix):] or None
    return s


def _extract_authors(work: dict) -> Optional[str]:
    """Une los nombres de autor de ``authorships`` por ``"; "`` (tabla diseño).

    Ruta: ``work["authorships"][*]["author"]["display_name"]``. Ausente o sin
    nombres utilizables → ``None`` (no se inventa). Obligatorio del contrato:
    su ausencia la marca ``work_to_record`` como PENDIENTE_REVISIÓN.
    """
    authorships = work.get("authorships")
    if not isinstance(authorships, (list, tuple)):
        return None
    names: list[str] = []
    for authorship in authorships:
        if not isinstance(authorship, dict):
            continue
        author = authorship.get("author")
        if not isinstance(author, dict):
            continue
        name = _clean_str(author.get("display_name"))
        if name:
            names.append(name)
    return "; ".join(names) or None


def _primary_location(work: dict) -> dict:
    """Devuelve ``work["primary_location"]`` como dict (``{}`` si no aplica)."""
    loc = work.get("primary_location")
    return loc if isinstance(loc, dict) else {}


def _location_source(work: dict) -> dict:
    """Devuelve ``primary_location.source`` como dict (``{}`` si no aplica)."""
    source = _primary_location(work).get("source")
    return source if isinstance(source, dict) else {}


def _extract_journal(work: dict) -> Optional[str]:
    """Nombre de la revista/medio (tabla diseño).

    Ruta preferida: ``primary_location.source.display_name``. Como respaldo del
    esquema antiguo, ``work["host_venue"]["display_name"]``. Ausente → ``None``.
    """
    name = _clean_str(_location_source(work).get("display_name"))
    if name:
        return name
    host_venue = work.get("host_venue")
    if isinstance(host_venue, dict):
        return _clean_str(host_venue.get("display_name"))
    return None


def _extract_publisher(work: dict) -> Optional[str]:
    """Editorial (tabla diseño): ``primary_location.source.host_organization_name``."""
    return _clean_str(_location_source(work).get("host_organization_name"))


def _extract_url(work: dict) -> Optional[str]:
    """Enlace al artículo (tabla diseño).

    Preferido: ``primary_location.landing_page_url``; respaldo: el DOI como URL
    (``https://doi.org/<doi>``) si existe. Ausente ambos → ``None``.
    """
    landing = _clean_str(_primary_location(work).get("landing_page_url"))
    if landing:
        return landing
    doi = _strip_doi_prefix(work.get("doi"))
    if doi:
        return f"https://doi.org/{doi}"
    return None


def _extract_pages(work: dict) -> Optional[str]:
    """Combina ``biblio.first_page`` y ``biblio.last_page`` (tabla diseño).

    - Ambos presentes → ``"first-last"``.
    - Solo uno → ese valor.
    - Ninguno → ``None`` (no se inventa).
    """
    biblio = work.get("biblio")
    if not isinstance(biblio, dict):
        return None
    first = _clean_str(biblio.get("first_page"))
    last = _clean_str(biblio.get("last_page"))
    if first and last:
        return f"{first}-{last}"
    return first or last or None


def _extract_biblio_field(work: dict, key: str) -> Optional[str]:
    """Lee un campo escalar de ``work["biblio"]`` (``volume`` / ``issue``)."""
    biblio = work.get("biblio")
    if not isinstance(biblio, dict):
        return None
    return _clean_str(biblio.get(key))


def _extract_keywords(work: dict) -> Optional[str]:
    """Une palabras clave por ``"; "`` (tabla diseño).

    Preferido: ``work["keywords"][*]["display_name"]`` (o strings sueltos).
    Respaldo: ``work["concepts"][*]["display_name"]``. Ausente → ``None``.
    """
    for field_key in ("keywords", "concepts"):
        items = work.get(field_key)
        if not isinstance(items, (list, tuple)):
            continue
        names: list[str] = []
        for item in items:
            if isinstance(item, dict):
                name = _clean_str(item.get("display_name"))
            else:
                name = _clean_str(item)
            if name:
                names.append(name)
        if names:
            return "; ".join(names)
    return None


def _parse_year(value: Any) -> tuple[Optional[int], bool]:
    """Interpreta ``publication_year`` como ``int``. Devuelve ``(year, ambiguo)``.

    - ``None`` ausente → ``(None, False)`` (faltante, no ambiguo).
    - ``int`` directo → ``(int, False)``.
    - Texto con 4 dígitos de año al inicio → ``(int, False)``.
    - Valor presente pero no interpretable → ``(None, True)`` (ambiguo; no se
      inventa un número).
    """
    if value is None:
        return None, False
    if isinstance(value, bool):
        return None, True
    if isinstance(value, int):
        return value, False
    s = _clean_str(value)
    if s is None:
        return None, False
    if s.isdigit():
        return int(s), False
    if len(s) >= 4 and s[:4].isdigit():
        return int(s[:4]), False
    return None, True


def work_to_record(work: dict) -> ArticleRecord:
    """Transforma un ``work`` nativo de la API_OpenAlex en un ``ArticleRecord`` V1.

    Sigue la tabla de mapeo del diseño (design.md, Data Models):

    - ``source`` fijo = ``"OpenAlex"`` (Req 3.1, 3.2); nunca otra fuente.
    - Campo ausente en el ``work`` → ``None`` (Req 3.3); no se inventa valor.
    - Obligatorio (``title``/``authors``/``publication_year``) faltante o
      ambiguo → ``inclusion_status = "PENDIENTE_REVISIÓN"`` con nota (Req 3.4,
      4.3). Año no detectable → ``publication_year = None`` + revisión.
    - Año fuera de 2020–2030 → PENDIENTE_REVISIÓN con nota, SIN descartar el
      registro (Req 4.2). No clasifica OFC ni relevancia (Req 4.5).
    - ``abstract`` reconstruido desde ``abstract_inverted_index`` (Req 3.7).
    - ``extraction_method`` = ``"OpenAlex API V1"`` (Req 8.1); ``source_url`` =
      ``work["id"]`` cuando exista, si no ``None`` (Req 8.2).

    :param work: dict crudo de un ``work`` devuelto por la API_OpenAlex.
    :returns: un ``ArticleRecord`` conforme al contrato V1.
    """
    # --- Campos del contrato (tabla de mapeo del diseño) ---------------------
    # title: preferir "title"; respaldo "display_name".
    title = _clean_str(work.get("title")) or _clean_str(work.get("display_name"))
    authors = _extract_authors(work)
    year, year_ambiguo = _parse_year(work.get("publication_year"))

    doi = _strip_doi_prefix(work.get("doi"))
    url = _extract_url(work)
    journal = _extract_journal(work)
    publisher = _extract_publisher(work)
    volume = _extract_biblio_field(work, "volume")
    issue = _extract_biblio_field(work, "issue")
    pages = _extract_pages(work)
    abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
    keywords = _extract_keywords(work)
    language = _clean_str(work.get("language"))
    # Procedencia propia de OpenAlex: la URL del work (campo ``id``). Ausente →
    # None (no se inventa) (Req 8.2).
    source_url = _clean_str(work.get("id"))

    # --- Reglas de inclusión / notas (no inventar) ---------------------------
    notes_parts: list[str] = []
    missing_required: list[str] = []
    if not title:
        missing_required.append("title")
    if not authors:
        missing_required.append("authors")
    if year is None:
        missing_required.append("publication_year")

    inclusion = "PENDIENTE_REVISIÓN"  # estado base del contrato V1

    if missing_required:
        notes_parts.append(
            "Faltan campos obligatorios: " + ", ".join(missing_required)
        )
    if year_ambiguo:
        notes_parts.append(
            "Año no interpretable; requiere revisión."
        )
    # Período 2020–2030 (Req 4.2): fuera de rango → nota, sin descartar. Solo
    # aplica si hay un año interpretable.
    if year is not None and not (PERIODO_MIN <= year <= PERIODO_MAX):
        notes_parts.append(
            f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}."
        )

    if not notes_parts:
        # Metadata obligatoria completa y año en rango. Relevancia temática y OFC
        # NO se evalúan automáticamente en V1 (PENDING_VALIDATION) → revisión.
        notes_parts.append(
            "Metadata extraída; pendiente de revisión de relevancia y clasificación OFC."
        )

    article_id = _api_make_article_id(doi, title, year)

    return ArticleRecord(
        article_id=article_id,
        title=title,
        doi=doi,
        url=url,
        authors=authors,
        publication_year=year,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        publisher=publisher,
        language=language,
        abstract=abstract,
        keywords=keywords,
        source=OPENALEX_SOURCE,
        source_url=source_url,
        extraction_date=_dt.date.today().isoformat(),
        extraction_method=OPENALEX_API_EXTRACTION_METHOD,
        inclusion_status=inclusion,
        notes=" | ".join(notes_parts),
    )
