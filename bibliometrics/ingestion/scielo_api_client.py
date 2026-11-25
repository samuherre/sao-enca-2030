"""
scielo_api_client.py — Conector de la API ArticleMeta de SciELO (Componente B).

OBJETIVO:
  Recuperar artículos de la **colección Colombia** de SciELO vía la API pública
  ArticleMeta (https://articlemeta.scielo.org/api/v1, sin API key) y
  transformarlos al Article Data Contract V1 (``ArticleRecord``), igual que el
  conector de OpenAlex. SciELO aporta literatura latinoamericana en español,
  que OpenAlex cubre peor y que es muy relevante para Colombia
  (steering bibliometrics.md §7.3).

POR QUÉ ESTE DISEÑO (harvesting, no búsqueda):
  ArticleMeta NO es un buscador: no se puede consultar "aves Colombia" y recibir
  resultados. Es una API de COSECHA: se listan colecciones/revistas y se baja
  cada artículo. El buscador web (search.scielo.org) bloquea el acceso
  automatizado (HTTP 403), así que NO es una opción fiable.

  Por eso el flujo es:
    1. Listar las revistas de la colección Colombia ('col').
    2. Quedarse con las de ÁREAS relevantes (Ciencias Biológicas/Agrícolas),
       medido sobre el universo real (35 de 255 revistas).
    3. Bajar los identificadores de artículos de cada revista.
    4. Bajar cada artículo y aplicar el FILTRO ESTRICTO de aves (términos de
       aves en título/abstract/keywords), igual de exigente que en OpenAlex,
       para no colar ruido (SciELO Colombia publica estudios de otros países y
       de muchos temas).
    5. Mapear a ``ArticleRecord`` V1 (source="SciELO", prefijo id "scielo-").

REGLAS HEREDADAS (steering Componente B §4; tech.md §19–20):
  - No inventar: campo ausente en el artículo → ``None``. Obligatorio faltante o
    ambiguo → ``inclusion_status = "PENDIENTE_REVISIÓN"`` con nota.
  - Alcance SOLO Colombia: la colección 'col' ya ES Colombia por definición
    (revistas colombianas), así que el criterio geográfico queda cubierto en
    origen. Aun así, se exige el filtro de aves para acotar el tema.
  - La capa HTTP no escribe en disco; el pipeline escribe, y solo en
    ``data/processed/scielo/`` (``data/raw/`` es inmutable).

SEPARACIÓN DE CAPAS (espejo de openalex_api_client.py):
  - CAPA HTTP: ``iter_journal_issns``, ``iter_article_codes``, ``fetch_article``
    (listar revistas, listar códigos de artículo, bajar un artículo). No conoce
    el contrato V1.
  - CAPA DE TRANSFORMACIÓN: ``article_to_record`` (artículo crudo ArticleMeta →
    ``ArticleRecord``) + helpers de lectura de campos ``vNN``. No conoce HTTP.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

# --- Constantes de la fuente y del endpoint ---------------------------------
SCIELO_SOURCE = "SciELO"
SCIELO_EXTRACTION_METHOD = "SciELO ArticleMeta API V1"
ARTICLEMETA_BASE_URL = "https://articlemeta.scielo.org/api/v1"
# Colección Colombia de SciELO (acrónimo oficial de la red).
COLOMBIA_COLLECTION = "col"
# Período de inclusión V1 (mismo rango que OpenAlex / _common).
PERIODO_MIN, PERIODO_MAX = 2020, 2030

# Áreas temáticas de revista (campo v441, en inglés) que se consideran
# relevantes para aves/conservación. Medido sobre el universo real de la
# colección 'col': 14 biológicas + 21 agrícolas = 35 revistas (de 255). El resto
# (ciencias sociales, salud humana, ingeniería, lingüística…) se descarta: no
# aporta artículos de aves y solo añadiría ruido y tráfico.
AREAS_RELEVANTES = frozenset(
    {
        "biological sciences",
        "agricultural sciences",
        "environmental sciences",
        "ecology",
        "zoology",
        "biology",
    }
)

# Contrato de datos compartido (Article Data Contract V1). Import tolerante,
# igual que en openalex_api_client.py.
try:  # pragma: no cover - selección de import según contexto de ejecución
    from ingestion.article_record import ArticleRecord  # type: ignore
    from pipelines._common import norm_title  # type: ignore
except ImportError:  # pragma: no cover
    _REPO_ROOT = Path(__file__).resolve().parents[2]
    _BIBLIO = str(_REPO_ROOT / "bibliometrics")
    if _BIBLIO not in sys.path:
        sys.path.insert(0, _BIBLIO)
    from ingestion.article_record import ArticleRecord  # type: ignore  # noqa: E402
    from pipelines._common import norm_title  # type: ignore  # noqa: E402


# =============================================================================
# FILTRO ESTRICTO DE AVES
# =============================================================================
# Términos de aves (ES/EN/PT) que deben aparecer (sin distinguir acentos ni
# mayúsculas) en título + abstract + keywords para que el artículo cuente como
# del tema. Equivale al ``title_and_abstract.search`` estricto de OpenAlex: si
# NINGÚN término aparece, el artículo se descarta (no entra como "sin dato").
#
# DOS GRUPOS, por cómo deben encajar (clave para no colar falsos positivos):
#
# 1) _TERMINOS_AVES_EXACTOS — PALABRA COMPLETA (frontera a ambos lados, con
#    plural opcional en 's'). Son términos CORTOS/ambiguos que, si se dejaran
#    encajar como prefijo, matchearían palabras no relacionadas: "pato" dentro
#    de "patógeno"/"patología", "ave" dentro de "averrhoa"/"aveskamp", "loro"
#    dentro de "cloro", "owl" dentro de "towel"… Exigir palabra completa lo
#    evita. (Bug detectado en la 1ª cosecha: "pato"→"patógeno" metió decenas de
#    artículos de fitopatología; "ave"→"averrhoa" metió artículos de plantas.)
#
# 2) _TERMINOS_AVES_RAIZ — RAÍZ/PREFIJO (frontera solo al inicio; el sufijo es
#    libre). Son raíces largas e inequívocas que deben capturar sus variantes:
#    "ornitolog" → ornitólogo/ornitología; "avifauna"; "passerin" →
#    passerine/passeriformes. Al ser largas y propias del dominio, no generan
#    falsos positivos aunque el sufijo quede abierto.
_TERMINOS_AVES_EXACTOS = (
    # genéricos (palabra completa; el plural en 's' se añade en el patrón)
    "ave", "bird", "avian", "paseriforme",
    # grupos comunes de aves (señales fuertes)
    "colibri", "hummingbird", "tanager", "tangara", "tucan", "toucan",
    "loro", "parrot", "guacamaya", "macaw", "paujil", "tinamou",
    "rapaz", "raptor", "aguila", "eagle", "halcon", "falcon", "owl", "buho",
    "garza", "heron", "pato", "duck", "waterfowl", "shorebird", "playero",
)
_TERMINOS_AVES_RAIZ = (
    "avifauna", "ornitolog", "ornitholog", "passerin",
)


def _normaliza_para_match(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar términos de forma robusta."""
    import unicodedata

    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


# Patrón precompilado: términos exactos como PALABRA COMPLETA (con 's' opcional
# de plural) O raíces con sufijo libre. ``\b`` delimita palabra sobre el texto
# ya normalizado (solo letras ascii + dígitos).
_PATRON_AVES = re.compile(
    "|".join(
        [r"\b(?:" + "|".join(re.escape(t) for t in _TERMINOS_AVES_EXACTOS) + r")s?\b"]
        + [r"\b(?:" + "|".join(re.escape(t) for t in _TERMINOS_AVES_RAIZ) + r")"]
    )
)


def es_sobre_aves(title: Optional[str], abstract: Optional[str], keywords: Optional[str]) -> bool:
    """¿El artículo trata de aves? Filtro ESTRICTO por términos (no inventa).

    Busca cualquiera de los términos de aves (palabra completa para los cortos,
    raíz+sufijo libre para los largos inequívocos) en el texto combinado de
    título + abstract + keywords, tras normalizar acentos/mayúsculas. Si ninguno
    aparece, devuelve ``False`` (el pipeline lo descarta). Es deliberadamente
    estricto: preferimos un corpus pequeño y limpio a uno grande con ruido
    (steering bibliometrics.md §2, §7.1).
    """
    partes = [p for p in (title, abstract, keywords) if p]
    if not partes:
        return False
    blob = _normaliza_para_match(" ".join(partes))
    return _PATRON_AVES.search(blob) is not None


# =============================================================================
# CAPA HTTP — listar revistas, listar códigos de artículo, bajar un artículo
# =============================================================================
@dataclass(frozen=True)
class ApiConfig:
    """Configuración operativa del cliente HTTP de SciELO.

    :param pace_seconds: pausa entre solicitudes para acotar el ritmo.
    :param max_retries: reintentos ante errores transitorios (429/5xx/red).
    :param backoff_base: base de la espera creciente entre reintentos (s).
    :param page_size: tamaño de página al listar identificadores de artículo.
    :param timeout: timeout por solicitud (s).
    """

    pace_seconds: float = 0.2
    max_retries: int = 4
    backoff_base: float = 1.0
    page_size: int = 100
    timeout: int = 60


def _get_json(session: Any, url: str, config: ApiConfig) -> Any:
    """GET con reintentos y espera creciente; devuelve el JSON decodificado.

    Reintenta ante error de red/timeout o códigos transitorios (429/5xx). Un
    4xx distinto de 429 se propaga de inmediato (permanente). Agotados los
    reintentos, propaga la última excepción para que el pipeline la registre.
    """
    intento = 0
    while True:
        try:
            resp = session.get(url, timeout=config.timeout)
            status = getattr(resp, "status_code", 200)
            if status >= 400:
                transitorio = status == 429 or 500 <= status <= 599
                if not transitorio or intento >= config.max_retries:
                    resp.raise_for_status()
                # transitorio con reintentos restantes → espera y reintenta.
            else:
                return resp.json()
        except Exception:  # noqa: BLE001 — red/decodificación: reintentar o propagar
            if intento >= config.max_retries:
                raise
        espera = config.backoff_base * (intento + 1)
        if espera > 0:
            time.sleep(espera)
        intento += 1


def iter_journal_issns(
    session: Any,
    config: ApiConfig,
    *,
    collection: str = COLOMBIA_COLLECTION,
) -> list[str]:
    """Lista los ISSN de todas las revistas de la colección (p. ej. 'col').

    Capa HTTP pura: devuelve los ``code`` (ISSN) tal como vienen. El filtrado por
    área temática lo hace ``journal_area`` + el pipeline (no aquí).
    """
    url = f"{ARTICLEMETA_BASE_URL}/journal/identifiers/?collection={collection}&limit=1000"
    data = _get_json(session, url, config)
    objetos = data.get("objects") if isinstance(data, dict) else None
    if not isinstance(objetos, list):
        return []
    return [o["code"] for o in objetos if isinstance(o, dict) and o.get("code")]


def journal_metadata(
    session: Any,
    issn: str,
    config: ApiConfig,
    *,
    collection: str = COLOMBIA_COLLECTION,
) -> dict:
    """Metadatos crudos de una revista (incluye área temática v441 y título v100).

    Devuelve ``{}`` si no hay datos. ArticleMeta responde una lista; se toma el
    primer elemento.
    """
    url = f"{ARTICLEMETA_BASE_URL}/journal/?collection={collection}&issn={issn}"
    data = _get_json(session, url, config)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data[0]
    if isinstance(data, dict):
        return data
    return {}


def journal_area(meta: dict) -> Optional[str]:
    """Área temática en inglés (campo v441) de los metadatos de revista.

    Normalizada a minúsculas. ``None`` si no viene.
    """
    area = _v_first(meta, "v441")
    return area.strip().lower() if area else None


def journal_title(meta: dict) -> Optional[str]:
    """Título de la revista (campo v100) de los metadatos de revista."""
    return _v_first(meta, "v100")


def iter_article_codes(
    session: Any,
    issn: str,
    config: ApiConfig,
    *,
    collection: str = COLOMBIA_COLLECTION,
    from_date: Optional[str] = None,
) -> Iterator[str]:
    """Itera los ``code`` (PID) de los artículos de una revista, paginando.

    Usa ``article/identifiers`` con ``issn`` y paginación por ``offset``. Capa
    HTTP pura: entrega los PID crudos; la descarga y el filtro de aves los hace
    el pipeline.

    :param from_date: fecha ``YYYY-MM-DD`` para el parámetro ``from`` de la API,
        que acota por fecha de **procesamiento** (NO por año de publicación). Se
        usa como PRE-FILTRO grueso para no recorrer décadas de artículos
        antiguos: los artículos publicados desde ``year_from`` fueron procesados,
        en general, en fechas recientes. El año de publicación REAL se valida
        igualmente al transformar cada artículo (filtro fino y preciso). Se pasa
        con un margen (p. ej. un año antes de ``year_from``) para no perder
        artículos procesados poco antes de su año de publicación. ``None`` =
        recorrer todo el histórico.
    """
    from_param = f"&from={from_date}" if from_date else ""
    offset = 0
    while True:
        url = (
            f"{ARTICLEMETA_BASE_URL}/article/identifiers/"
            f"?collection={collection}&issn={issn}"
            f"&limit={config.page_size}&offset={offset}{from_param}"
        )
        data = _get_json(session, url, config)
        objetos = data.get("objects") if isinstance(data, dict) else None
        if not isinstance(objetos, list) or not objetos:
            return
        for o in objetos:
            if isinstance(o, dict) and o.get("code"):
                yield o["code"]
        if len(objetos) < config.page_size:
            return
        offset += config.page_size
        if config.pace_seconds > 0:
            time.sleep(config.pace_seconds)


def fetch_article(
    session: Any,
    code: str,
    config: ApiConfig,
    *,
    collection: str = COLOMBIA_COLLECTION,
) -> dict:
    """Baja un artículo completo por su ``code`` (PID). Devuelve el JSON crudo.

    La estructura relevante vive bajo ``payload["article"]`` (campos ``vNN``).
    """
    url = f"{ARTICLEMETA_BASE_URL}/article/?collection={collection}&code={code}&format=json"
    data = _get_json(session, url, config)
    return data if isinstance(data, dict) else {}


# =============================================================================
# CAPA DE TRANSFORMACIÓN — artículo crudo ArticleMeta → ArticleRecord V1
# =============================================================================
def _article_body(payload: dict) -> dict:
    """Devuelve el cuerpo ``article`` (campos vNN) del artículo crudo."""
    body = payload.get("article")
    return body if isinstance(body, dict) else {}


def _v_entries(body: dict, code: str) -> list:
    """Lista de entradas de un campo ``vNN`` (``[]`` si ausente)."""
    val = body.get(code)
    return val if isinstance(val, list) else []


def _v_first(body: dict, code: str) -> Optional[str]:
    """Primer valor ``_`` de un campo ``vNN`` (texto no vacío) o ``None``."""
    for entry in _v_entries(body, code):
        if isinstance(entry, dict):
            s = entry.get("_")
            if isinstance(s, str) and s.strip():
                return s.strip()
    return None


def _clean(s: Any) -> Optional[str]:
    """Texto recortado no vacío o ``None`` (no inventa)."""
    if isinstance(s, str):
        s = s.strip()
        return s or None
    return None


def _pick_by_lang(entries: list, text_key: str) -> Optional[str]:
    """Elige el mejor valor de un campo multilingüe (v12 título, v83 abstract).

    Prioriza español, luego inglés, luego portugués, luego el primero que haya.
    Cada entrada trae ``l`` (lang) y el texto en ``text_key`` (``_`` o ``a``).
    """
    por_lang: dict[str, str] = {}
    primero: Optional[str] = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        texto = entry.get(text_key)
        if not isinstance(texto, str) or not texto.strip():
            continue
        texto = texto.strip()
        if primero is None:
            primero = texto
        lang = (entry.get("l") or "").strip().lower()
        if lang and lang not in por_lang:
            por_lang[lang] = texto
    for lang in ("es", "en", "pt"):
        if lang in por_lang:
            return por_lang[lang]
    return primero


def _extract_title(body: dict) -> Optional[str]:
    """Título (v12, multilingüe). Prioriza ES; respaldo EN/PT/primero."""
    return _pick_by_lang(_v_entries(body, "v12"), "_")


def _extract_abstract(body: dict) -> Optional[str]:
    """Abstract (v83, multilingüe, texto en clave ``a``). Prioriza ES."""
    return _pick_by_lang(_v_entries(body, "v83"), "a")


def _extract_keywords(body: dict) -> Optional[str]:
    """Palabras clave (v85, clave ``k``), unidas por ``; ``. ``None`` si no hay.

    Prioriza las keywords en español; si no hay ES, usa las primeras que haya de
    un mismo idioma. No mezcla idiomas para no duplicar la misma keyword.
    """
    entries = _v_entries(body, "v85")
    por_lang: dict[str, list[str]] = {}
    primero_lang: Optional[str] = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        k = entry.get("k")
        if not isinstance(k, str) or not k.strip():
            continue
        lang = (entry.get("l") or "").strip().lower() or "?"
        por_lang.setdefault(lang, [])
        if primero_lang is None:
            primero_lang = lang
        por_lang[lang].append(k.strip())
    for lang in ("es", "en", "pt"):
        if por_lang.get(lang):
            return "; ".join(por_lang[lang]) or None
    if primero_lang and por_lang.get(primero_lang):
        return "; ".join(por_lang[primero_lang]) or None
    return None


def _extract_year(body: dict) -> Optional[int]:
    """Año de publicación desde v65 (YYYYMMDD) o v43/v64. ``None`` si no es válido.

    v65 viene como "20220800" → 2022. Si no, intenta v64/v43 (fecha). Solo
    devuelve el año si son 4 dígitos plausibles; si no, ``None`` (no inventa).
    """
    for code in ("v65", "v64", "v43"):
        raw = _v_first(body, code)
        if raw and len(raw) >= 4 and raw[:4].isdigit():
            year = int(raw[:4])
            if 1800 <= year <= 2100:
                return year
    # publication_year a veces viene en el payload de nivel superior.
    return None


def _extract_doi(body: dict) -> Optional[str]:
    """DOI (v237), normalizado a minúsculas sin prefijo URL. ``None`` si no hay."""
    doi = _v_first(body, "v237")
    if not doi:
        return None
    low = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
        if low.startswith(prefix):
            low = low[len(prefix):]
            break
    return low or None


def _extract_authors(body: dict) -> tuple[Optional[str], list]:
    """Autores (v10): string unido por "; " y lista individual.

    Cada entrada trae ``n`` (nombre) y ``s`` (apellido). Se arma "Apellido,
    Nombre". ``authors_list`` conserva cada autor por separado. Ambos ``None``/
    vacío si no hay autores utilizables (obligatorio del contrato → el llamador
    marca PENDIENTE_REVISIÓN).
    """
    nombres: list[str] = []
    for entry in _v_entries(body, "v10"):
        if not isinstance(entry, dict):
            continue
        apellido = _clean(entry.get("s"))
        nombre = _clean(entry.get("n"))
        if apellido and nombre:
            nombres.append(f"{apellido}, {nombre}")
        elif apellido:
            nombres.append(apellido)
        elif nombre:
            nombres.append(nombre)
    if not nombres:
        return None, []
    return "; ".join(nombres), list(nombres)


def _extract_authorships(body: dict) -> list:
    """Afiliaciones por autor (v10 + v70), en el mismo formato que OpenAlex.

    v70 lista afiliaciones con ``i`` (id de aff, p. ej. "aff1"), ``_`` (nombre de
    institución) y ``p`` (país, nombre completo p. ej. "Colombia"/"Brazil").
    v10 referencia la aff de cada autor por su campo ``1``.

    Estructura de cada entrada (igual que el conector OpenAlex):
        {"position": "first"|"middle"|"last"|None,
         "institutions": [{"name": str, "country": str|None}, ...]}

    La ``position`` se deriva del orden: primer autor → "first", último →
    "last", el resto → "middle". Si un autor no referencia aff o la aff no
    existe, su lista de instituciones queda vacía (no se inventa).
    """
    # Mapa id_aff -> {"name", "country"} desde v70.
    affs: dict[str, dict] = {}
    for entry in _v_entries(body, "v70"):
        if not isinstance(entry, dict):
            continue
        aid = _clean(entry.get("i"))
        nombre = _clean(entry.get("_"))
        if not nombre:
            continue
        pais = _clean(entry.get("p"))
        if aid:
            affs[aid] = {"name": nombre, "country": _pais_a_codigo(pais)}
        else:
            # Aff sin id: se indexa por su propio nombre para no perderla.
            affs.setdefault(nombre, {"name": nombre, "country": _pais_a_codigo(pais)})

    autores = [e for e in _v_entries(body, "v10") if isinstance(e, dict)]
    salida: list = []
    n = len(autores)
    for idx, autor in enumerate(autores):
        if n == 1:
            position = "first"
        elif idx == 0:
            position = "first"
        elif idx == n - 1:
            position = "last"
        else:
            position = "middle"
        insts: list = []
        ref = _clean(autor.get("1"))
        if ref:
            # El campo ``1`` puede referenciar varias affs separadas por comas.
            for token in re.split(r"[,\s]+", ref):
                token = token.strip()
                if token and token in affs:
                    insts.append(dict(affs[token]))
        salida.append({"position": position, "institutions": insts})
    return salida


# Mapa mínimo de país (nombre completo que usa SciELO) a código ISO-2, para
# alinear con el formato de OpenAlex (``country_code``). Solo los países más
# frecuentes en la red SciELO; uno no mapeado deja el nombre tal cual (no se
# inventa un código). Colombia es el relevante para el alcance solo-Colombia.
_PAIS_A_ISO2 = {
    "colombia": "CO",
    "brazil": "BR",
    "brasil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "mexico": "MX",
    "méxico": "MX",
    "peru": "PE",
    "perú": "PE",
    "ecuador": "EC",
    "venezuela": "VE",
    "bolivia": "BO",
    "uruguay": "UY",
    "paraguay": "PY",
    "costa rica": "CR",
    "panama": "PA",
    "panamá": "PA",
    "cuba": "CU",
    "spain": "ES",
    "españa": "ES",
    "united states": "US",
    "usa": "US",
    "estados unidos": "US",
}


def _pais_a_codigo(nombre: Optional[str]) -> Optional[str]:
    """Convierte el nombre de país de SciELO a código ISO-2 si se conoce.

    Si ya viene como código de 2 letras, se devuelve en mayúsculas. Si es un
    nombre conocido, se traduce. Si no se reconoce, se devuelve el valor original
    (no se inventa un código ni se descarta el dato).
    """
    if not nombre:
        return None
    s = nombre.strip()
    if len(s) == 2 and s.isalpha():
        return s.upper()
    iso = _PAIS_A_ISO2.get(s.lower())
    return iso if iso else s


def _extract_language(body: dict) -> Optional[str]:
    """Idioma principal del artículo (v40). ``None`` si no viene."""
    return _v_first(body, "v40")


def _extract_journal(body: dict) -> Optional[str]:
    """Nombre de la revista (v30). ``None`` si no viene."""
    return _v_first(body, "v30")


def _extract_volume(body: dict) -> Optional[str]:
    return _v_first(body, "v31")


def _extract_issue(body: dict) -> Optional[str]:
    return _v_first(body, "v32")


def _extract_is_open_access(body: dict) -> Optional[bool]:
    """Acceso abierto desde v71 ('oa' = abierto). ``None`` si no viene.

    SciELO es una biblioteca de acceso abierto; v71='oa' lo confirma. Como el
    campo no distingue el estado fino (gold/green/…), ``oa_status`` queda en
    "gold" solo cuando v71='oa' de forma explícita (SciELO publica en la propia
    revista abierta, que es oro), y ``None`` si no hay señal.
    """
    v71 = _v_first(body, "v71")
    if v71 and v71.strip().lower() == "oa":
        return True
    return None


def _extract_oa_status(body: dict) -> Optional[str]:
    """Estado fino de OA. SciELO publica en revista propia de acceso abierto, que
    equivale a 'gold' (no es copia en repositorio). ``None`` si no hay señal OA."""
    if _extract_is_open_access(body) is True:
        return "gold"
    return None


def _hash12(text: str) -> str:
    """Primeros 12 hex del SHA-256 (determinista), igual que los otros conectores."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _make_article_id(doi: Optional[str], title: Optional[str], year: Optional[int]) -> str:
    """Id interno determinista para SciELO (prefijo 'scielo-').

    - Con DOI: ``scielo-<hash12(doi normalizado)>``.
    - Sin DOI: ``scielo-<hash12(norm_title(title) + "|" + año)>``.

    Nota de dedup ENTRE fuentes: la deduplicación global del servicio
    (``_dedup_entre_fuentes``) compara por DOI y por título+año, de modo que un
    mismo artículo presente en OpenAlex y SciELO (con el mismo DOI o el mismo
    título+año) se cuenta UNA sola vez aunque el ``article_id`` tenga distinto
    prefijo. El prefijo distinto es intencional: conserva la trazabilidad de la
    fuente de origen (steering §7.3, dedup por DOI/título).
    """
    if doi:
        return "scielo-" + _hash12(doi.strip().lower())
    base = f"{norm_title(title)}|{year if year is not None else ''}"
    return "scielo-" + _hash12(base)


def article_to_record(payload: dict, *, source_url: Optional[str] = None) -> ArticleRecord:
    """Transforma un artículo crudo de ArticleMeta en ``ArticleRecord`` V1.

    No inventa: campo ausente → ``None``. Si falta un obligatorio del contrato
    (título, autores o año) o el año cae fuera de 2020–2030, marca
    ``inclusion_status = "PENDIENTE_REVISIÓN"`` con nota (el pipeline además
    descarta por año y por filtro de aves ANTES de llamar aquí; esta marca es la
    red de seguridad del contrato).

    :param payload: JSON crudo del artículo (con clave ``article``).
    :param source_url: URL de procedencia opcional (p. ej. el endpoint usado).
    """
    body = _article_body(payload)

    title = _extract_title(body)
    abstract = _extract_abstract(body)
    keywords = _extract_keywords(body)
    year = _extract_year(body)
    doi = _extract_doi(body)
    authors, authors_list = _extract_authors(body)
    authorships = _extract_authorships(body)
    journal = _extract_journal(body)
    language = _extract_language(body)

    article_id = _make_article_id(doi, title, year)
    url = f"https://doi.org/{doi}" if doi else None

    notas: list[str] = []
    inclusion = "PENDIENTE_REVISIÓN"  # V1: relevancia + OFC siempre a revisar.
    if not title:
        notas.append("Sin título detectado (obligatorio del contrato).")
    if not authors:
        notas.append("Sin autores detectados (obligatorio del contrato).")
    if year is None:
        notas.append("Año de publicación no detectado.")
    elif not (PERIODO_MIN <= year <= PERIODO_MAX):
        notas.append(f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}.")

    return ArticleRecord(
        article_id=article_id,
        title=title,
        doi=doi,
        url=url,
        authors=authors,
        authors_list=authors_list,
        publication_year=year,
        journal=journal,
        volume=_extract_volume(body),
        issue=_extract_issue(body),
        pages=None,
        publisher=None,
        language=language,
        document_type="article",  # ArticleMeta no desglosa fino; SciELO = artículos.
        is_open_access=_extract_is_open_access(body),
        oa_status=_extract_oa_status(body),
        authorships=authorships,
        cited_by_count=None,  # ArticleMeta no expone recuento de citas.
        abstract=abstract,
        keywords=keywords,
        source=SCIELO_SOURCE,
        source_url=source_url,
        extraction_date=_dt.date.today().isoformat(),
        extraction_method=SCIELO_EXTRACTION_METHOD,
        processing_status="EXTRAIDO",
        inclusion_status=inclusion,
        notes=" | ".join(notas) if notas else None,
    )
