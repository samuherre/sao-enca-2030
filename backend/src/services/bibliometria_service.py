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

import csv
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from backend.src.domain.exceptions import NotFoundError
from backend.src.schemas.bibliometria import (
    AporteFuente,
    ArticuloItem,
    ArticulosOFC,
    CompletitudCampo,
    ConteoOFC,
    ConteoPorClave,
    DescripcionOFC,
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


# Texto introductorio oficial de los OFC, tomado LITERALMENTE del documento
# ENCA 2030 de SAO (sección "Objetos focales de conservación"). Se expone al
# público en el dashboard para que cualquier visitante entienda qué es un OFC.
# No es texto inventado: es la definición de la fuente oficial.
_OFC_DESCRIPCION = (
    "Los objetos focales son indicadores que nos ayudan a identificar los "
    "avances que vayamos logrando cada año en términos de la conservación de "
    "especies y ecosistemas. Son comparables con los valores objetos de "
    "conservación (VOC) de los planes de manejo de áreas. La ENCA cuenta con 11 "
    "objetos focales representativos de la avifauna residente y migratoria y de "
    "los distintos hábitats que ellas utilizan."
)


def _catalogo_ofc() -> list[dict]:
    """Catálogo público de los 11 OFC: número, id, nombre y definición.

    Se lee del mismo ``ofc_catalog.json`` que usa el clasificador (fuente única
    de verdad, verificada contra el documento ENCA 2030). Solo expone los campos
    descriptivos (no los términos del clasificador). Si el catálogo no existe,
    devuelve lista vacía sin inventar datos.
    """
    if not _OFC_CATALOG.exists():
        return []
    data = json.loads(_OFC_CATALOG.read_text(encoding="utf-8"))
    catalogo: list[dict] = []
    for o in data.get("ofc", []):
        catalogo.append(
            {
                "ofc_id": o["id"],
                "numero": o.get("numero"),
                "nombre": o["nombre"],
                "definicion": o.get("definicion", ""),
            }
        )
    return catalogo


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


# Rango de años considerado PLAUSIBLE para ofrecer como opción de filtro. El
# periodo de inclusión del proyecto es 2020–2030 (steering Componente B §2),
# pero el consolidado puede contener artículos de otras fuentes con años
# distintos; se usa un rango amplio y conservador para no descartar años reales
# y, a la vez, excluir sentinelas erróneos como 0.
_ANIO_MIN_PLAUSIBLE = 1900
_ANIO_MAX_PLAUSIBLE = 2100


def _es_anio_plausible(valor: object) -> bool:
    """True si ``valor`` es un año de publicación real (no un sentinela 0/None).

    No modifica ni inventa datos: solo decide si un año merece aparecer como
    opción en el desplegable de filtro. Un ``publication_year`` ausente, 0 o
    fuera del rango razonable se considera metadata no fiable y no genera opción.
    """
    if valor is None:
        return False
    try:
        anio = int(valor)
    except (TypeError, ValueError):
        return False
    return _ANIO_MIN_PLAUSIBLE <= anio <= _ANIO_MAX_PLAUSIBLE


# Fuentes cuyo campo ``authors`` viene como lista de autores separada de forma
# FIABLE por "; " (p. ej. OpenAlex une ``authorships`` con ese separador). Para
# otras fuentes (p. ej. Boletín SAO) el texto de autores es libre y separar
# nombres no es confiable, por lo que no se cuenta (no se inventa un conteo).
_FUENTES_AUTORIA_FIABLE = {"OpenAlex"}
# Separador explícito con el que esas fuentes unen los nombres de autor.
_SEP_AUTORES_FIABLE = ";"


def _calcular_gc(n: int, f1: int) -> float | None:
    """Grado de Colaboración de Subramanyam (1983): ``GC = 1 - f1/N``.

    :param n: N = número de artículos con autoría contable (del OFC).
    :param f1: f1 = de esos, cuántos son de un solo autor.
    :returns: GC en [0, 1] redondeado a 2 decimales, o ``None`` si ``n == 0``
        (sin artículos contables no hay métrica; no se inventa un 0).

    GC = 0 → toda la producción es de autor único; GC → 1 → predomina la
    coautoría. Solo se calcula sobre artículos con autoría contable de forma
    fiable (ver :func:`_num_autores_fiable`).
    """
    if n <= 0:
        return None
    return round(1 - (f1 / n), 2)


def _num_autores_fiable(registro: dict) -> int | None:
    """Número de autores del artículo, SOLO si el conteo es fiable.

    Devuelve un entero cuando la autoría es contable sin adivinar:
    - Si ``authors_list`` es una lista no vacía, usa su longitud (ya desglosada).
    - Si la fuente une autores por "; " de forma fiable (p. ej. OpenAlex), parte
      el string ``authors`` por ese separador y cuenta los nombres no vacíos.
    En cualquier otro caso devuelve ``None`` (autoría no contable de forma
    confiable: texto libre, separadores ambiguos o sin autores). No se inventa.
    """
    al = registro.get("authors_list")
    if isinstance(al, list):
        nombres = [str(x).strip() for x in al if str(x).strip()]
        if nombres:
            return len(nombres)

    fuente = registro.get("source")
    authors = registro.get("authors")
    if fuente in _FUENTES_AUTORIA_FIABLE and isinstance(authors, str) and authors.strip():
        nombres = [n.strip() for n in authors.split(_SEP_AUTORES_FIABLE) if n.strip()]
        if nombres:
            return len(nombres)

    return None


# Número de revistas con más artículos que se muestran individualmente en la
# distribución por revista; el resto se agrupa bajo "Otros".
_TOP_REVISTAS = 30
# Etiqueta del grupo agregado (el resto de revistas fuera del top).
_ETIQUETA_OTRAS_REVISTAS = "Otros"


# Idiomas que se muestran individualmente en la distribución por idioma; el
# resto (incluidos valores ambiguos o poco frecuentes) se agrupa en "Otros".
# Mapea el código ISO del dato (``language``) a una etiqueta legible. El orden
# define el de las barras; "Otros" se añade al final.
_IDIOMAS_PRINCIPALES: list[tuple[str, str]] = [
    ("en", "Inglés"),
    ("es", "Español"),
    ("pt", "Portugués"),
    ("fr", "Francés"),
]
# "Otros idiomas": idiomas reales distintos de los principales (alemán, ruso…).
_ETIQUETA_OTROS_IDIOMAS = "Otros idiomas"
# "Sin idioma declarado": el artículo llegó sin el dato de idioma. Se separa de
# "Otros idiomas" para no confundir ausencia de dato con un idioma real.
_ETIQUETA_SIN_IDIOMA = "Sin idioma declarado"


def _por_idioma(registros: list[dict]) -> list[ConteoPorClave]:
    """Distribución por idioma: principales + "Otros idiomas" + "Sin idioma declarado".

    Cuenta por el código ``language`` (normalizado a minúsculas). Muestra los
    idiomas de ``_IDIOMAS_PRINCIPALES`` con etiqueta legible, agrupa los demás
    idiomas reales (incluidos códigos ambiguos como "es/en") en "Otros idiomas",
    y cuenta aparte los artículos SIN idioma declarado. Separar ausencia de dato
    de "otro idioma" evita inflar "Otros" y confundir al lector. No se infiere el
    idioma de un artículo que no lo trae (no se inventa).
    """
    principales = {codigo for codigo, _ in _IDIOMAS_PRINCIPALES}
    conteo: Counter = Counter()
    otros_idiomas = 0
    sin_idioma = 0
    for r in registros:
        lang = r.get("language")
        codigo = str(lang).strip().lower() if lang else ""
        if not codigo:
            sin_idioma += 1
        elif codigo in principales:
            conteo[codigo] += 1
        else:
            # Idioma real distinto de los principales (alemán, ruso, etc.).
            otros_idiomas += 1

    resultado = [
        ConteoPorClave(clave=etiqueta, conteo=conteo[codigo])
        for codigo, etiqueta in _IDIOMAS_PRINCIPALES
        if conteo[codigo] > 0
    ]
    if otros_idiomas > 0:
        resultado.append(
            ConteoPorClave(clave=_ETIQUETA_OTROS_IDIOMAS, conteo=otros_idiomas)
        )
    if sin_idioma > 0:
        resultado.append(
            ConteoPorClave(clave=_ETIQUETA_SIN_IDIOMA, conteo=sin_idioma)
        )
    return resultado


def _top_por_revista(registros: list[dict]) -> list[ConteoPorClave]:
    """Distribución por revista: top ``_TOP_REVISTAS`` + "Otros".

    Cuenta los artículos por el campo ``journal`` (reflejado tal cual; los
    registros sin revista no se cuentan ni se inventan). Devuelve las revistas
    con más artículos, ordenadas de mayor a menor, y agrega todo lo demás en una
    única entrada "Otros" al final (solo si hay remanente). Así la gráfica
    resume miles de revistas sin perder la cola larga.
    """
    conteo: Counter = Counter()
    for r in registros:
        journal = r.get("journal")
        if journal:
            conteo[str(journal).strip()] += 1

    top = conteo.most_common(_TOP_REVISTAS)
    resultado = [ConteoPorClave(clave=nombre, conteo=n) for nombre, n in top]

    # Agrupar el resto (revistas fuera del top) bajo "Otros".
    resto = sum(conteo.values()) - sum(n for _, n in top)
    if resto > 0:
        resultado.append(
            ConteoPorClave(clave=_ETIQUETA_OTRAS_REVISTAS, conteo=resto)
        )
    return resultado


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


# Campos del CSV de descarga, en orden. Se eligen los útiles para que SAO
# pueda ubicar cada artículo (título + enlace como mínimo, Req de Julián) sin
# volcar el dataset interno completo. El enlace se resuelve a una URL navegable.
_CAMPOS_EXPORT: list[tuple[str, str]] = [
    ("titulo", "title"),
    ("anio", "publication_year"),
    ("fuente", "source"),
    ("revista", "journal"),
    ("doi", "doi"),
    ("enlace", "url"),
]


def _url_desde_doi(doi: object) -> str | None:
    """URL navegable a partir de un DOI, o ``None`` si no hay DOI utilizable.

    Acepta el DOI crudo ("10.x/...") o ya como URL ("https://doi.org/10.x/...").
    No inventa: si no hay DOI, devuelve ``None``.
    """
    if not doi or not isinstance(doi, str):
        return None
    d = doi.strip()
    if not d:
        return None
    if d.startswith("http://") or d.startswith("https://"):
        return d
    return f"https://doi.org/{d}"


def _combinar_registros_fuente(anio: int | None) -> list[dict]:
    """Combina los registros de TODAS las fuentes (no clasificadas) de
    ``data/processed/``, con la MISMA lógica que el resumen consolidado:
    unión sin exclusión y deduplicación por ``article_id`` dentro de cada fuente.

    Si ``anio`` no es ``None``, filtra por ``publication_year == anio``. No toca
    las carpetas ``*_clasificado`` (esas no aportan artículos al conjunto).
    """
    combinados: list[dict] = []
    for carpeta in _carpetas_procesadas():
        if _es_carpeta_clasificado(carpeta):
            continue
        registros, _fechas = _acumular_json(carpeta)
        combinados.extend(registros)
    if anio is not None:
        combinados = [r for r in combinados if r.get("publication_year") == anio]
    return combinados


def _registros_clasificados_de_ofc(ofc_id: str, anio: int | None) -> list[dict]:
    """Devuelve los artículos clasificados en ``ofc_id`` (multilabel), deduplicados.

    Recorre las carpetas ``*_clasificado`` de ``data/processed/`` y selecciona los
    registros cuyo campo ``ofcs`` contiene ``ofc_id``. Deduplica por ``article_id``
    (gana la corrida más reciente, como el resto del servicio). Si ``anio`` no es
    ``None``, filtra por ``publication_year``. No inventa datos: refleja lo que el
    dataset clasificado contiene.
    """
    por_id: dict[str, dict] = {}
    sin_id: list[dict] = []
    for carpeta in _carpetas_procesadas():
        if not _es_carpeta_clasificado(carpeta):
            continue
        clasificados, _fechas = _acumular_json(carpeta)
        for r in clasificados:
            if ofc_id not in (r.get("ofcs") or []):
                continue
            if anio is not None and r.get("publication_year") != anio:
                continue
            aid = r.get("article_id")
            if aid:
                por_id[aid] = r  # el más reciente gana (acumulación ya ordenada)
            else:
                sin_id.append(r)
    registros = list(por_id.values()) + sin_id
    # Orden legible: por año desc. y luego título.
    registros.sort(
        key=lambda r: (
            -(r.get("publication_year") or 0),
            str(r.get("title") or "").lower(),
        )
    )
    return registros


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

    def resumen_consolidado(self, anio: int | None = None) -> ResumenConsolidado:
        """Calcula el resumen CONSOLIDADO de todas las fuentes procesadas.

        Descubre las subcarpetas bajo ``data/processed/``, agrupa los registros
        por su campo ``source`` y combina el conjunto por UNIÓN SIN EXCLUSIÓN,
        sin deduplicación entre fuentes (Req 6.6): solo cuenta la deduplicación
        básica ya realizada dentro de cada dataset. Sobre el conjunto combinado
        agrega total, distribución por año y por volumen, completitud,
        pendientes de revisión, posibles duplicados y el aporte por fuente
        (Req 6, 7).

        :param anio: si se indica, TODAS las agregaciones (total, OFC,
            completitud, aporte por fuente, etc.) se calculan SOLO sobre los
            artículos de ese año de publicación. ``None`` = todos los años.
            La lista ``anios_disponibles`` se calcula siempre sobre el conjunto
            completo (sin filtrar), de modo que el desplegable del frontend
            ofrezca todos los años aunque ya se haya filtrado por uno.

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

        # --- 2b) Años disponibles (SIEMPRE sobre el conjunto completo) -------
        # Se calcula antes de aplicar el filtro para que el desplegable del
        # frontend liste todos los años aunque ya se haya seleccionado uno.
        # Solo se ofrecen años PLAUSIBLES como opción de filtro: un
        # ``publication_year`` de 0 (o fuera de un rango razonable) es metadata
        # ausente/errónea del origen, no un año real, y no debe aparecer como
        # opción en el desplegable. Esos artículos NO se inventan ni se
        # descartan: siguen contando en el total de "Todos"; solo no generan una
        # opción de año espuria.
        anios_disponibles = sorted(
            {
                int(r["publication_year"])
                for r in combinados
                if _es_anio_plausible(r.get("publication_year"))
            }
        )

        # --- 2c) Filtro por año (si se indicó) -------------------------------
        # Afecta a TODAS las agregaciones: se filtran tanto el conjunto
        # combinado como el desglose por fuente antes de contar nada.
        if anio is not None:
            combinados = [r for r in combinados if r.get("publication_year") == anio]
            por_fuente = defaultdict(
                list,
                {
                    fuente: [r for r in registros if r.get("publication_year") == anio]
                    for fuente, registros in por_fuente.items()
                },
            )

        # --- 3) Agregaciones sobre el conjunto combinado ---------------------
        por_anio = Counter(
            str(r["publication_year"]) for r in combinados if r.get("publication_year")
        )
        # Distribución por revista: las ``_TOP_REVISTAS`` con más artículos y el
        # resto agrupado en "Otros" (Req de visualización pedido por SAO). El
        # nombre de revista se refleja TAL CUAL viene del dato (puede incluir
        # repositorios como GBIF/bioRxiv/Zenodo); no se normaliza ni se inventa.
        por_revista = _top_por_revista(combinados)
        # Distribución por idioma: inglés/español/portugués/francés + "Otros".
        por_idioma = _por_idioma(combinados)
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
        # Grado de Colaboración (Subramanyam 1983) por OFC. Para cada OFC
        # acumulamos, SOLO sobre artículos con autoría contable de forma fiable:
        #   gc_n[ofc]  = N  (artículos del OFC con autoría contable)
        #   gc_f1[ofc] = f1 (de esos, cuántos son de un solo autor)
        #   gc_excluidos[ofc] = artículos del OFC sin autoría contable (transparencia)
        gc_n: Counter = Counter()
        gc_f1: Counter = Counter()
        gc_excluidos: Counter = Counter()
        for carpeta in carpetas_clasificado:
            # Modelo ACUMULATIVO: se combinan TODOS los datasets clasificados de
            # la carpeta, deduplicando por article_id (el más reciente gana), de
            # modo que la distribución por OFC refleje el histórico acumulado y
            # sea coherente con el total acumulado de las fuentes.
            clasificados, _fechas_clasif = _acumular_json(carpeta)
            if not clasificados:
                continue
            # Coherencia con el filtro por año: la distribución por OFC se
            # calcula solo sobre los artículos del año seleccionado.
            if anio is not None:
                clasificados = [
                    r for r in clasificados if r.get("publication_year") == anio
                ]
                if not clasificados:
                    continue
            clasificacion_disponible = True
            for r in clasificados:
                ofcs = r.get("ofcs") or []
                if not ofcs:
                    sin_ofc += 1
                # Autoría del artículo para el GC (una sola vez por artículo).
                num_aut = _num_autores_fiable(r)
                for ofc_id in ofcs:
                    dist[ofc_id] += 1
                    # El artículo cuenta en cada OFC al que pertenece (multilabel).
                    if num_aut is None:
                        gc_excluidos[ofc_id] += 1
                    else:
                        gc_n[ofc_id] += 1
                        if num_aut <= 1:
                            gc_f1[ofc_id] += 1
        if clasificacion_disponible:
            por_ofc = [
                ConteoOFC(
                    ofc_id=ofc_id,
                    nombre=nombres.get(ofc_id, ofc_id),
                    conteo=n,
                    grado_colaboracion=_calcular_gc(gc_n[ofc_id], gc_f1[ofc_id]),
                    gc_articulos_contables=gc_n[ofc_id],
                    gc_articulos_sin_autoria=gc_excluidos[ofc_id],
                )
                for ofc_id, n in sorted(dist.items())
            ]

        return ResumenConsolidado(
            total_articulos=len(combinados),
            por_anio=[
                ConteoPorClave(clave=k, conteo=v) for k, v in sorted(por_anio.items())
            ],
            por_revista=por_revista,
            por_idioma=por_idioma,
            completitud=_completitud(combinados),
            pendientes_revision=pendientes,
            posibles_duplicados=duplicados,
            fechas_dataset=sorted(fechas_dataset),
            anios_disponibles=anios_disponibles,
            anio_seleccionado=anio,
            clasificacion_disponible=clasificacion_disponible,
            por_ofc=por_ofc,
            sin_ofc=sin_ofc,
            ofc_descripcion=_OFC_DESCRIPCION,
            catalogo_ofc=[DescripcionOFC(**o) for o in _catalogo_ofc()],
            aporte_por_fuente=aporte_por_fuente,
        )

    def exportar_consolidado_csv(self, anio: int | None = None) -> str:
        """Genera un CSV descargable del conjunto consolidado de artículos.

        Una fila por artículo (unión sin exclusión, deduplicado por fuente como
        el resumen). Incluye los campos de ``_CAMPOS_EXPORT`` —título y enlace
        como mínimo (Req pedido por SAO)— reflejados tal cual del dato; un campo
        ausente queda vacío (no se inventa). El ``enlace`` usa ``url`` y, si
        falta, construye la URL del DOI (``https://doi.org/<doi>``) para que SAO
        pueda llegar al artículo.

        :param anio: si se indica, exporta solo los artículos de ese año
            (coherente con el filtro del dashboard). ``None`` = todos.
        :returns: el contenido del CSV como texto (UTF-8 con BOM lo añade el
            endpoint; aquí se devuelve el texto plano con encabezado).
        """
        registros = _combinar_registros_fuente(anio)
        # Orden estable y legible: por año desc. y luego título.
        registros.sort(
            key=lambda r: (
                -(r.get("publication_year") or 0),
                str(r.get("title") or "").lower(),
            )
        )

        buffer = io.StringIO()
        # lineterminator="\n": sin esto, csv.writer usa "\r\n" y, al servirse o
        # reabrirse el texto, aparece una línea en blanco entre cada fila.
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow([encabezado for encabezado, _campo in _CAMPOS_EXPORT])
        for r in registros:
            fila = []
            for _encabezado, campo in _CAMPOS_EXPORT:
                if campo == "url":
                    valor = r.get("url") or _url_desde_doi(r.get("doi"))
                else:
                    valor = r.get(campo)
                fila.append("" if valor is None else str(valor))
            writer.writerow(fila)
        return buffer.getvalue()

    def articulos_de_ofc(
        self, ofc_id: str, anio: int | None = None, limite: int | None = None
    ) -> ArticulosOFC:
        """Lista los artículos clasificados en un OFC (para "ver detrás de la barra").

        Devuelve el nombre del OFC, el total de artículos de ese OFC y una lista
        acotada (``limite``) con los campos para mostrar/enlazar: título, año,
        revista y enlace (url o, si falta, el DOI). ``total`` es el conteo real
        aunque ``items`` venga recortado, para que el frontend sepa cuántos hay.

        :param ofc_id: identificador del OFC (p. ej. "OFC-01").
        :param anio: filtro opcional por año de publicación.
        :param limite: máximo de artículos en ``items`` (None = todos).
        """
        registros = _registros_clasificados_de_ofc(ofc_id, anio)
        total = len(registros)
        seleccion = registros if limite is None else registros[:limite]
        items = [
            ArticuloItem(
                titulo=r.get("title") or "(sin título)",
                anio=r.get("publication_year"),
                revista=r.get("journal"),
                enlace=r.get("url") or _url_desde_doi(r.get("doi")),
            )
            for r in seleccion
        ]
        return ArticulosOFC(
            ofc_id=ofc_id,
            nombre=_nombres_ofc().get(ofc_id, ofc_id),
            total=total,
            mostrados=len(items),
            items=items,
        )

    def exportar_articulos_ofc_csv(self, ofc_id: str, anio: int | None = None) -> str:
        """CSV descargable con TODOS los artículos de un OFC (título + enlace...)."""
        registros = _registros_clasificados_de_ofc(ofc_id, anio)
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow([encabezado for encabezado, _campo in _CAMPOS_EXPORT])
        for r in registros:
            fila = []
            for _encabezado, campo in _CAMPOS_EXPORT:
                if campo == "url":
                    valor = r.get("url") or _url_desde_doi(r.get("doi"))
                else:
                    valor = r.get(campo)
                fila.append("" if valor is None else str(valor))
            writer.writerow(fila)
        return buffer.getvalue()
