"""
extract_boletin.py — Extractor piloto de articulos de boletines SAO (Comp. B).

OBJETIVO:
  Tomar un PDF de separata del Boletin SAO (1 PDF = 1 articulo, segun hallazgo
  del piloto) y producir un registro conforme al Article Data Contract V1.

REGLA FUNDAMENTAL (no inventar):
  - Lo que se detecta con alta confianza se rellena.
  - Lo que NO se puede detectar queda en None.
  - Si falta un campo OBLIGATORIO del contrato (title, authors,
    publication_year) o la deteccion es ambigua, inclusion_status pasa a
    PENDIENTE_REVISION. Nunca se inventan valores.

ALCANCE V1:
  - Pensado para las SEPARATAS individuales (1 articulo por PDF).
  - El caso "boletin completo con varios articulos" NO se cubre aqui y queda
    marcado como pendiente de validacion (ver notas del piloto).
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import pdfplumber

# Permite ejecutar como script (python bibliometrics/ingestion/extract_boletin.py)
# resolviendo el import del normalizador por ruta relativa al repo.
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "bibliometrics") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "bibliometrics"))

from preprocessing.text_normalizer import normalize_text  # noqa: E402

# El contrato de datos (ArticleRecord) y sus defaults de fuente viven ahora en
# un módulo compartido, reutilizable por otros conectores. Se re-exportan aquí
# para conservar el comportamiento previo de este extractor.
from ingestion.article_record import (  # noqa: E402
    EXTRACTION_METHOD,
    SOURCE_NAME,
    ArticleRecord,
)

SAMPLES_DIR = _REPO_ROOT / "data" / "samples"
OUTPUT_DIR = _REPO_ROOT / "data" / "interim" / "piloto_boletines"

# --- Patrones sobre la PRIMERA pagina (datos reales del piloto) --------------
# Linea 1: "<autores-corto> Boletín SAO Vol. 34 - 2025".
# Los espacios entre "Boletín", "SAO" y "Vol." son OPCIONALES (\s*) porque en
# algunos PDFs la extraccion los pega: "BoletínSAOVol. 32-2023".
RE_VOL_YEAR = re.compile(
    r"Bolet.?[ií]n\s*SAO\s*Vol\.\s*(\d+)\s*-\s*(\d{4})", re.IGNORECASE
)
# Linea 2: "... Pag: 35-38"  o  "... Páginas: 12-16"
RE_PAGES = re.compile(r"P[aá]g(?:inas)?\.?\s*:?\s*(\d+)\s*[-–]\s*(\d+)", re.IGNORECASE)

PERIODO_MIN, PERIODO_MAX = 2020, 2030


def _extract_first_page_lines(pdf_path: Path) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        raw = pdf.pages[0].extract_text() or ""
    # Normaliza por linea para conservar la estructura visual.
    return [normalize_text(line) for line in raw.split("\n")]


def _parse_vol_year(lines: list[str]) -> tuple[Optional[str], Optional[int]]:
    for line in lines[:3]:
        m = RE_VOL_YEAR.search(line)
        if m:
            return m.group(1), int(m.group(2))
    return None, None


def _parse_pages(lines: list[str]) -> Optional[str]:
    for line in lines[:4]:
        m = RE_PAGES.search(line)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
    return None


# Palabras con las que suele comenzar el TITULO EN INGLES en estos boletines.
# Sirven para delimitar el fin del titulo en espanol.
_ENGLISH_TITLE_STARTERS = (
    "NEW", "FIRST", "ON THE", "IN THE", "A ", "AN ", "THE ", "FISH", "RECORDS",
    "DISTRIBUTION", "NOTES", "OBSERVATIONS", "RANGE", "SECOND", "PRESENCE",
)


def _is_mostly_upper(line: str) -> bool:
    """True si la linea es mayoritariamente MAYUSCULAS, ignorando los nombres
    cientificos entre parentesis (en minuscula/cursiva).

    Elimina parentesis balanceados y tambien parentesis SIN cerrar (desde '('
    hasta fin de linea), porque el nombre cientifico puede partirse en dos
    lineas, p. ej. "... (Tyrannus dominicensis," / "GMELIN 1788) ...".
    """
    sin_parentesis = re.sub(r"\(.*?\)", "", line)   # parentesis balanceados
    sin_parentesis = re.sub(r"\([^)]*$", "", sin_parentesis)  # abierto sin cerrar
    sin_parentesis = re.sub(r"^[^(]*\)", "", sin_parentesis)  # cierre sin apertura
    letters = [c for c in sin_parentesis if c.isalpha()]
    if len(letters) < 3:
        return False
    uppers = [c for c in letters if c.isupper()]
    return (len(uppers) / len(letters)) > 0.75


def _looks_english(line: str) -> bool:
    stripped = line.strip().upper()
    return any(stripped.startswith(s) for s in _ENGLISH_TITLE_STARTERS)


# Inicios tipicos de un TITULO EN INGLES escrito como oracion (minuscula/mixto).
# Si una linea candidata a autores empieza asi, en realidad es titulo ingles.
_ENGLISH_SENTENCE_TITLE_STARTERS = (
    "the ", "a ", "an ", "new ", "first ", "second ", "notes ", "note ",
    "description ", "predation ", "on ", "observations ", "record ", "records ",
    "nesting ", "presence ", "range ",
)


def _looks_like_author_line(line: str) -> bool:
    """True si la linea parece una linea de AUTORES, no de titulo (ES/EN).

    Criterios:
      - NO es mayoritariamente mayuscula (los titulos ES/EN en mayuscula lo son).
      - NO empieza como un titulo ingles en forma de oracion (The/A/New/...).
      - Contiene al menos dos 'nombres propios' (Mayuscula + minusculas).
    """
    s = line.strip()
    if not s or _is_mostly_upper(s):
        return False
    if s.lower().startswith(_ENGLISH_SENTENCE_TITLE_STARTERS):
        return False
    # Nombres propios tipo "Diego", "Aguirre-Alas", "Montoya-Muñoz".
    proper_names = re.findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:-[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?", s)
    return len(proper_names) >= 2


def _clean_author_superscripts(text: str) -> str:
    """Quita superindices numericos de afiliacion y reinserta el espacio que
    esos numeros separaban entre nombres de autores.

    Ej.: 'Chaparro-Herrera1 2 ,3Andrea' -> 'Chaparro-Herrera Andrea'
    """
    # Reemplaza bloques de digitos/comas/espacios (superindices) por un espacio.
    text = re.sub(r"\s*\d+(?:\s*,\s*\d+)*\s*", " ", text)
    # Normaliza separadores: '&' y ',' con espacios correctos.
    text = re.sub(r"\s*&\s*", " & ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    # Corrige 'A´ ngelo' / 'Arias-A´ lvarez' -> junta la mayuscula partida.
    text = re.sub(r"([A-ZÁÉÍÓÚÑ])\s+([a-záéíóúñ])", r"\1\2", text)
    return text.strip(" ,&")


# Conjunciones que separan autores cuando van como palabra suelta entre nombres.
_AUTHOR_CONJUNCTIONS = (" y ", " e ", " and ")


def split_authors(authors: Optional[str]) -> tuple[list[str], bool]:
    """Divide la cadena de autores en una lista, SOLO por separadores explícitos.

    Separadores reconocidos: coma, punto y coma, ``&`` y las conjunciones
    sueltas ``y`` / ``e`` / ``and``. NO se intenta partir nombres "pegados" por
    espacios (p. ej. "Nombre Apellido Nombre2 Apellido2"): adivinar dónde
    termina un autor y empieza otro arriesgaría INVENTAR autores incorrectos
    (principio de no invención, steering bibliometrics.md §4.1).

    Devuelve ``(lista, incierto)``:
      - ``lista``: autores separados y limpios (sin vacíos). Si no hay separador
        explícito, ``[authors]`` (un solo elemento, la cadena tal cual).
      - ``incierto``: ``True`` cuando NO hubo separador explícito pero el texto
        aparenta contener varios autores pegados (heurística: >= 4 palabras con
        inicial mayúscula), de modo que el llamador pueda dejar constancia.
    """
    if not authors or not authors.strip():
        return [], False
    texto = authors.strip()

    # Normaliza las conjunciones a una coma para un split uniforme.
    normalizado = texto
    for conj in _AUTHOR_CONJUNCTIONS:
        normalizado = re.sub(conj, ", ", normalizado, flags=re.IGNORECASE)
    # Divide por coma, punto y coma o '&'.
    partes = [p.strip(" ,;&") for p in re.split(r"[,;&]", normalizado)]
    partes = [p for p in partes if p]

    if len(partes) >= 2:
        return partes, False

    # Sin separador explícito: no partimos nombres. Señalamos incertidumbre si
    # parece haber varios autores pegados por espacios.
    nombres_propios = re.findall(
        r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:-[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?", texto
    )
    incierto = len(nombres_propios) >= 4
    return [texto], incierto


def _find_header_end(lines: list[str]) -> Optional[int]:
    """Indice donde termina el encabezado (titulo + autores) y empieza el
    cuerpo/resumen.

    Preferencia:
      1. La linea exacta 'Resumen' (caso regular).
      2. Si no existe, la primera linea que parece inicio de parrafo del cuerpo:
         texto largo que empieza en minuscula o con 'La/El/Se...' (abstract sin
         la palabra 'Resumen', visto en algun boletin).
    """
    # 1. 'Resumen' o 'Abstract' como marcador exacto (segun el idioma de inicio
    #    del cuerpo; algunos boletines invierten el orden ES/EN).
    for i, l in enumerate(lines):
        if l.strip().lower() in ("resumen", "abstract"):
            return i
    # 2. Fallback: primera linea larga que parece prosa (no titulo, no cita).
    for i, l in enumerate(lines[3:], start=3):
        s = l.strip()
        if len(s) > 60 and not _is_mostly_upper(s):
            return i
    return None


def _parse_title_authors(lines: list[str]) -> tuple[Optional[str], Optional[str], bool]:
    """Detecta titulo (ES) y autores de forma tentativa.

    Devuelve (title, authors, ambiguo). 'ambiguo' = True cuando la deteccion
    no es fiable; en ese caso el llamador marca PENDIENTE_REVISION y NO trata
    los valores como definitivos.
    """
    idx_end = _find_header_end(lines)
    if idx_end is None:
        return None, None, True

    # Zona de encabezado: desde la linea 3 (tras cita y paginas) hasta el fin
    # del encabezado. Se descartan filas de solo acentos sueltos y vacias.
    header_zone = [
        l.strip()
        for l in lines[2:idx_end]
        if l.strip() and set(l.strip()) - {" "} != {"´"}
    ]

    # --- Titulo en espanol: lineas en mayusculas hasta el inicio del ingles.
    title_lines: list[str] = []
    rest_start = 0
    for i, line in enumerate(header_zone):
        if title_lines and _looks_english(line):
            # Empezo el titulo en ingles -> dejamos de acumular ES.
            rest_start = i
            break
        if _is_mostly_upper(line):
            # Linea de titulo (en mayusculas). Un año/numero dentro del titulo,
            # p. ej. "(... GMELIN 1788) EN EL SALVADOR", NO corta el titulo
            # porque la linea sigue siendo mayoritariamente mayuscula.
            title_lines.append(line)
            rest_start = i + 1
            continue
        if title_lines:
            # Ya habia titulo y esta linea dejo de ser mayuscula -> empiezan
            # autores u otra seccion. Fin del titulo.
            rest_start = i
            break
        rest_start = i + 1

    title = " ".join(title_lines).strip() or None
    # Limpia dobles espacios y acentos sueltos remanentes en el titulo.
    if title:
        title = re.sub(r"\s{2,}", " ", title).replace("´", "").strip()

    # --- Autores: tomamos la PRIMERA linea de la zona tras el titulo que parezca
    # nombres de personas, mas una posible segunda linea de continuacion. NO
    # acumulamos todas las lineas (eso arrastraba cuerpo del abstract en PDFs
    # con estructura atipica). Si la primera candidata no es fiable -> None.
    tail = header_zone[rest_start:]
    authors = None
    for i, line in enumerate(tail):
        if _looks_like_author_line(line):
            picked = [line]
            # Segunda linea solo si tambien parece autores (continuacion).
            if i + 1 < len(tail) and _looks_like_author_line(tail[i + 1]):
                picked.append(tail[i + 1])
            authors = _clean_author_superscripts(" ".join(picked)) or None
            break

    # Filtro de sanidad: si el valor de autores arrastra fragmento de titulo
    # ingles (empieza en minuscula o con parentesis/ 'by '/' in '), es poco
    # fiable -> preferimos None (no inventar) y que caiga en PENDIENTE_REVISION.
    if authors:
        first = authors.lstrip()[:1]
        if first and (first.islower() or first == "("):
            authors = None

    ambiguo = title is None or authors is None
    return title, authors, ambiguo


def _parse_abstract_keywords(lines: list[str]) -> tuple[Optional[str], Optional[str]]:
    text = "\n".join(lines)
    abstract = None
    keywords = None

    # Abstract ES: entre 'Resumen' y el primer delimitador siguiente
    # ('Palabras clave', 'Key words' o 'Abstract').
    m_abs = re.search(
        r"\bResumen\b\s*(.+?)\s*(?:\bPalabras\s+clave\b|\bKey\s*words\b|\bAbstract\b)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m_abs:
        abstract = re.sub(r"\s*\n\s*", " ", m_abs.group(1)).strip()

    # Keywords: preferimos 'Palabras clave' (espanol); si no existe, usamos la
    # primera linea 'Key words' como respaldo. Separadores ',' o ';'.
    m_kw = re.search(r"\bPalabras\s+clave\b\s*:?\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if not m_kw:
        m_kw = re.search(r"\bKey\s*words\b\s*:?\s*(.+?)(?:\n|$)", text, re.IGNORECASE)
    if m_kw:
        keywords = m_kw.group(1).strip().rstrip(".")

    return abstract, keywords


def extract_article(pdf_path: Path) -> ArticleRecord:
    lines = _extract_first_page_lines(pdf_path)

    volume, year = _parse_vol_year(lines)
    pages = _parse_pages(lines)
    title, authors, ambiguo = _parse_title_authors(lines)
    abstract, keywords = _parse_abstract_keywords(lines)

    # Separacion de autores en lista (tarea 9): solo por separadores explicitos.
    authors_list, autores_inciertos = split_authors(authors)

    article_id = pdf_path.stem  # p. ej. BSVol34_2025

    notes_parts: list[str] = []
    missing_required: list[str] = []
    if not title:
        missing_required.append("title")
    if not authors:
        missing_required.append("authors")
    if not year:
        missing_required.append("publication_year")

    # Validacion de periodo 2020-2030 (criterio de inclusion V1).
    year_out_of_range = year is not None and not (PERIODO_MIN <= year <= PERIODO_MAX)

    if missing_required:
        inclusion = "PENDIENTE_REVISIÓN"
        notes_parts.append("Faltan campos obligatorios: " + ", ".join(missing_required))
    elif ambiguo:
        inclusion = "PENDIENTE_REVISIÓN"
        notes_parts.append("Titulo/autores detectados de forma tentativa; requieren revision humana.")
    elif year_out_of_range:
        inclusion = "PENDIENTE_REVISIÓN"
        notes_parts.append(f"Año {year} fuera del periodo {PERIODO_MIN}-{PERIODO_MAX}.")
    else:
        # Deteccion completa, pero la relevancia tematica y OFC NO se evaluan
        # automaticamente en V1 -> queda para revision/clasificacion posterior.
        inclusion = "PENDIENTE_REVISIÓN"
        notes_parts.append("Metadata extraida; pendiente de revision de relevancia y clasificacion OFC.")

    # Constancia si no se pudo separar autores con certeza (pegados sin
    # separador explicito): no se parten nombres; se deja la cadena completa.
    if autores_inciertos:
        notes_parts.append(
            "Autores sin separador explicito; authors_list sin dividir "
            "(separacion incierta, requiere revision humana)."
        )

    return ArticleRecord(
        article_id=article_id,
        title=title,
        authors=authors,
        authors_list=authors_list,
        publication_year=year,
        volume=volume,
        pages=pages,
        abstract=abstract,
        keywords=keywords,
        language="es/en",
        extraction_date=_dt.date.today().isoformat(),
        source_url=None,
        inclusion_status=inclusion,
        notes=" | ".join(notes_parts) if notes_parts else None,
    )


def main() -> None:
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en {SAMPLES_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for pdf_path in pdfs:
        rec = extract_article(pdf_path)
        records.append(asdict(rec))
        print("-" * 78)
        print(f"{pdf_path.name}")
        print(f"  title   : {rec.title}")
        print(f"  authors : {rec.authors}")
        print(f"  year    : {rec.publication_year}   volume: {rec.volume}   pages: {rec.pages}")
        print(f"  keywords: {rec.keywords}")
        print(f"  abstract: {(rec.abstract or '')[:120]}...")
        print(f"  status  : {rec.inclusion_status}")
        print(f"  notes   : {rec.notes}")

    out_file = OUTPUT_DIR / "articulos_piloto.json"
    out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "=" * 78)
    print(f"Escrito: {out_file}  ({len(records)} registros)")


if __name__ == "__main__":
    main()
