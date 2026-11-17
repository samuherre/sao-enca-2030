#!/usr/bin/env python3
"""
Fase 1 — Cifras de registros de AVES en Colombia desde GBIF.

Objetivo (alcance validado por SAO, ver docs/biodiversity/overview.md §2, §6):
  1. Total nacional de registros de aves en Colombia.
  2. Ranking de publicadores con sus conteos.
  3. Nombre del publicador resuelto a partir de su orgKey, cuando sea posible.
  4. Fuente, parámetros de consulta y fecha/hora de extracción (UTC).

Principios (steering del proyecto):
  - Consultas AGREGADAS de GBIF (limit=0 + facet). NO se descargan ocurrencias
    individuales (tech.md §25: sin optimización/volumen prematuro).
  - No inventar cifras ni nombres: si una consulta falla, se registra el error
    y el nombre del publicador queda en null (product.md §15 "no invención").
  - Solo biblioteca estándar de Python: no añade dependencias ni toca el MVP
    ENCA ni sus requirements (tech.md §33, §2.2).
  - No sobrescribe los artefactos del piloto anterior: escribe archivos nuevos
    con prefijo 'bird_record_counts' y marca de tiempo.

Uso:
    python scripts/biodiversity_pilot/gbif_bird_counts.py
    python scripts/biodiversity_pilot/gbif_bird_counts.py --facet-limit 15
    python scripts/biodiversity_pilot/gbif_bird_counts.py --dry-run

Este script NO implementa todavía la actualización mensual automática ni la
publicación en ArcGIS Online (fases 2 y 3).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Constantes de la fuente -------------------------------------------------

GBIF_BASE_URL = "https://api.gbif.org/v1"
OCCURRENCE_SEARCH = f"{GBIF_BASE_URL}/occurrence/search"
ORGANIZATION = f"{GBIF_BASE_URL}/organization"

COUNTRY = "CO"            # Colombia
AVES_TAXON_KEY = 212      # taxonKey de la clase Aves en el backbone de GBIF
DEFAULT_FACET_LIMIT = 10  # nº de publicadores en el ranking
DEFAULT_TIMEOUT = 40      # segundos

# Salidas: carpeta del piloto GBIF existente, con nombres NUEVOS.
OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "outputs"
    / "biodiversity_pilot"
    / "gbif"
)

USER_AGENT = "SAO-ENCA-biodiversity-pilot/0.1 (+contacto: SAO)"


class GbifError(RuntimeError):
    """Error controlado al consultar GBIF."""


# --- Acceso HTTP (solo stdlib) -----------------------------------------------

def _get_json(url: str, params: dict[str, Any], timeout: int) -> Any:
    """GET a una URL con querystring y respuesta JSON.

    Lanza GbifError con un mensaje claro ante error HTTP, de red, timeout o
    respuesta que no sea JSON válido.
    """
    query = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{url}?{query}"
    request = urllib.request.Request(full_url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read().decode(charset)
    except urllib.error.HTTPError as error:
        raise GbifError(f"HTTP {error.code} en {full_url}") from error
    except urllib.error.URLError as error:
        # Incluye fallos de DNS y timeouts (socket.timeout envuelto en URLError).
        raise GbifError(f"Error de red/timeout en {full_url}: {error.reason}") from error
    except TimeoutError as error:  # noqa: PERF203 - timeout directo de socket
        raise GbifError(f"Timeout en {full_url}") from error

    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        preview = raw[:200].replace("\n", " ")
        raise GbifError(
            f"Respuesta no es JSON válido en {full_url}: {preview!r}"
        ) from error


# --- Consultas de alto nivel -------------------------------------------------

def fetch_total_count(timeout: int) -> tuple[int, dict[str, Any]]:
    """Total nacional de registros de aves en Colombia (agregado, limit=0)."""
    params = {
        "country": COUNTRY,
        "taxonKey": AVES_TAXON_KEY,
        "limit": 0,
    }
    payload = _get_json(OCCURRENCE_SEARCH, params, timeout)
    if not isinstance(payload, dict) or "count" not in payload:
        raise GbifError("Respuesta inesperada: falta el campo 'count'.")
    count = payload["count"]
    if not isinstance(count, int):
        raise GbifError(f"Campo 'count' no es entero: {count!r}")
    return count, params


def fetch_publisher_facet(
    facet_limit: int, timeout: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Ranking de publicadores (faceta publishingOrg) con sus conteos."""
    params = {
        "country": COUNTRY,
        "taxonKey": AVES_TAXON_KEY,
        "limit": 0,
        "facet": "publishingOrg",
        "facetLimit": facet_limit,
    }
    payload = _get_json(OCCURRENCE_SEARCH, params, timeout)
    if not isinstance(payload, dict):
        raise GbifError("Respuesta inesperada al solicitar facetas.")

    facets = payload.get("facets") or []
    if not facets:
        # Respuesta válida pero sin facetas: no se inventa nada.
        return [], params

    counts = facets[0].get("counts") or []
    ranking: list[dict[str, Any]] = []
    for item in counts:
        org_key = item.get("name")
        occ = item.get("count")
        if org_key is None or not isinstance(occ, int):
            # Entrada malformada: se omite, no se inventa.
            continue
        ranking.append({"org_key": org_key, "occurrence_count": occ})
    return ranking, params


# Normalización de nombres de departamento (campo stateProvince de GBIF).
#
# GBIF expone ``stateProvince`` como TEXTO LIBRE: el mismo departamento llega con
# variantes de tildes, mayúsculas o formas (p. ej. "Narino"/"Nariño",
# "Valle Del Cauca"/"Valle del Cauca", y Bogotá como "Bogotá, D.C." o
# "Distrito Capital de Bogotá"). Para no mostrar duplicados, se canonizan las
# variantes OBSERVADAS a un nombre oficial. No se inventan departamentos: una
# variante no contemplada se conserva tal cual (no se descarta ni se renombra a
# algo no verificado).
_DEPARTAMENTO_CANONICO = {
    "narino": "Nariño",
    "nariño": "Nariño",
    "choco": "Chocó",
    "chocó": "Chocó",
    "bolivar": "Bolívar",
    "bolívar": "Bolívar",
    "caqueta": "Caquetá",
    "caquetá": "Caquetá",
    "valle del cauca": "Valle del Cauca",
    "bogota, d.c.": "Bogotá, D.C.",
    "bogotá, d.c.": "Bogotá, D.C.",
    "distrito capital de bogota": "Bogotá, D.C.",
    "distrito capital de bogotá": "Bogotá, D.C.",
    "san andres providencia y santa catalina": (
        "Archipiélago de San Andrés, Providencia y Santa Catalina"
    ),
    "san andrés providencia y santa catalina": (
        "Archipiélago de San Andrés, Providencia y Santa Catalina"
    ),
    "archipiélago de san andrés, providencia y santa catalina": (
        "Archipiélago de San Andrés, Providencia y Santa Catalina"
    ),
}


def _canonizar_departamento(nombre: str) -> str:
    """Devuelve el nombre oficial de un departamento a partir de una variante.

    Si la variante no está contemplada, devuelve el nombre original sin cambios
    (no se inventa ni se descarta un valor no verificado).
    """
    clave = nombre.strip().casefold()
    return _DEPARTAMENTO_CANONICO.get(clave, nombre.strip())


def fetch_department_facet(
    facet_limit: int, timeout: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Ranking de departamentos (faceta stateProvince) con sus conteos.

    Los conteos de variantes del MISMO departamento se SUMAN tras canonizar el
    nombre, de modo que no aparezcan filas duplicadas. El resultado se ordena de
    mayor a menor conteo.
    """
    params = {
        "country": COUNTRY,
        "taxonKey": AVES_TAXON_KEY,
        "limit": 0,
        "facet": "stateProvince",
        "facetLimit": facet_limit,
    }
    payload = _get_json(OCCURRENCE_SEARCH, params, timeout)
    if not isinstance(payload, dict):
        raise GbifError("Respuesta inesperada al solicitar facetas de departamento.")

    facets = payload.get("facets") or []
    if not facets:
        return [], params

    counts = facets[0].get("counts") or []
    acumulado: dict[str, int] = {}
    for item in counts:
        nombre = item.get("name")
        occ = item.get("count")
        if not isinstance(nombre, str) or not isinstance(occ, int):
            # Entrada malformada o sin departamento: se omite, no se inventa.
            continue
        canonico = _canonizar_departamento(nombre)
        acumulado[canonico] = acumulado.get(canonico, 0) + occ

    ranking = [
        {"departamento": nombre, "occurrence_count": occ}
        for nombre, occ in sorted(acumulado.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return ranking, params


# Las SEIS regiones de la ENCA (data-and-domain.md §10) coinciden con las
# regiones naturales de Colombia.
REGIONES_ENCA = ("Andina", "Caribe", "Pacífico", "Orinoquía", "Amazonía", "Insular")

# Asignación departamento -> región ENCA PREDOMINANTE (una región por
# departamento). Criterio: región natural predominante del departamento según la
# división geográfica estándar de Colombia.
#
# IMPORTANTE (product.md §15, data-and-domain.md §2): esto es una PROPUESTA del
# equipo, NO un mapeo oficial de SAO. Varios departamentos son fronterizos y
# admiten más de una región (p. ej. Antioquia tiene costa Caribe y vertiente
# Pacífica; Cauca/Nariño/Valle son andino-pacíficos); aquí se asigna la
# predominante. La UI lo etiqueta como "propuesta, pendiente de confirmación de
# SAO". El nombre del departamento es el canónico (ver _DEPARTAMENTO_CANONICO).
_REGION_POR_DEPARTAMENTO = {
    # --- Andina ---
    "Antioquia": "Andina",
    "Caldas": "Andina",
    "Cundinamarca": "Andina",
    "Risaralda": "Andina",
    "Quindío": "Andina",
    "Tolima": "Andina",
    "Santander": "Andina",
    "Norte de Santander": "Andina",
    "Boyacá": "Andina",
    "Huila": "Andina",
    "Bogotá, D.C.": "Andina",
    # --- Caribe ---
    "Atlántico": "Caribe",
    "Bolívar": "Caribe",
    "Cesar": "Caribe",
    "Córdoba": "Caribe",
    "La Guajira": "Caribe",
    "Magdalena": "Caribe",
    "Sucre": "Caribe",
    # --- Pacífico ---
    "Chocó": "Pacífico",
    "Valle del Cauca": "Pacífico",
    "Cauca": "Pacífico",
    "Nariño": "Pacífico",
    # --- Orinoquía ---
    "Arauca": "Orinoquía",
    "Casanare": "Orinoquía",
    "Meta": "Orinoquía",
    "Vichada": "Orinoquía",
    # --- Amazonía ---
    "Amazonas": "Amazonía",
    "Caquetá": "Amazonía",
    "Guainía": "Amazonía",
    "Guaviare": "Amazonía",
    "Putumayo": "Amazonía",
    "Vaupés": "Amazonía",
    # --- Insular ---
    "Archipiélago de San Andrés, Providencia y Santa Catalina": "Insular",
}


def agrupar_por_region(
    department_ranking: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Agrupa el ranking de departamentos en las regiones ENCA (predominante).

    Devuelve (ranking_region, departamentos_sin_region). Un departamento no
    contemplado en el mapeo NO se asigna a ninguna región (se reporta aparte, no
    se inventa su pertenencia). Las regiones sin registros no aparecen.
    """
    acumulado: dict[str, int] = {}
    sin_region: list[str] = []
    for fila in department_ranking:
        nombre = fila.get("departamento")
        occ = fila.get("occurrence_count")
        if not isinstance(nombre, str) or not isinstance(occ, int):
            continue
        region = _REGION_POR_DEPARTAMENTO.get(nombre)
        if region is None:
            sin_region.append(nombre)
            continue
        acumulado[region] = acumulado.get(region, 0) + occ

    ranking = [
        {"region": region, "occurrence_count": occ}
        for region, occ in sorted(acumulado.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return ranking, sin_region


def fetch_taxon_facet(
    facet: str, facet_limit: int, timeout: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Ranking taxonómico por ``facet`` (orderKey o familyKey) con sus conteos.

    GBIF devuelve CLAVES del backbone (numéricas), no nombres; la resolución a
    nombre se hace aparte (``resolve_taxon_name``). Las entradas malformadas se
    omiten (no se inventan).
    """
    params = {
        "country": COUNTRY,
        "taxonKey": AVES_TAXON_KEY,
        "limit": 0,
        "facet": facet,
        "facetLimit": facet_limit,
    }
    payload = _get_json(OCCURRENCE_SEARCH, params, timeout)
    if not isinstance(payload, dict):
        raise GbifError(f"Respuesta inesperada al solicitar facetas de {facet}.")

    facets = payload.get("facets") or []
    if not facets:
        return [], params

    counts = facets[0].get("counts") or []
    ranking: list[dict[str, Any]] = []
    for item in counts:
        key = item.get("name")
        occ = item.get("count")
        if key is None or not isinstance(occ, int):
            continue
        ranking.append({"taxon_key": key, "occurrence_count": occ})
    return ranking, params


def resolve_taxon_name(taxon_key: str, timeout: int) -> str | None:
    """Resuelve una clave del backbone -> nombre científico (canonicalName).

    Devuelve ``None`` si no se puede resolver (no se inventa).
    """
    try:
        payload = _get_json(f"{GBIF_BASE_URL}/species/{taxon_key}", {}, timeout)
    except GbifError:
        return None
    if isinstance(payload, dict):
        for campo in ("canonicalName", "scientificName"):
            valor = payload.get(campo)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()
    return None


def _resolver_nombres_taxon(
    ranking: list[dict[str, Any]], resolve_names: bool, timeout: int
) -> None:
    """Añade ``name`` a cada entrada del ranking taxonómico (in place)."""
    for fila in ranking:
        fila["name"] = (
            resolve_taxon_name(str(fila["taxon_key"]), timeout) if resolve_names else None
        )


def resolve_publisher_name(org_key: str, timeout: int) -> str | None:
    """Resuelve orgKey -> título del publicador. None si no se puede."""
    try:
        payload = _get_json(f"{ORGANIZATION}/{org_key}", {}, timeout)
    except GbifError:
        return None
    if isinstance(payload, dict):
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
    return None


# --- Escritura de resultados -------------------------------------------------

def _timestamp_for_filename(now: datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ")


def write_outputs(
    output_dir: Path,
    now: datetime,
    report: dict[str, Any],
    ranking: list[dict[str, Any]],
) -> dict[str, str]:
    """Escribe CSV (ranking) y JSON (resumen completo). No sobrescribe el piloto."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = _timestamp_for_filename(now)

    csv_path = output_dir / f"bird_record_counts_{stamp}.csv"
    json_path = output_dir / f"bird_record_counts_{stamp}.json"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["rank", "org_key", "publisher_name", "occurrence_count"])
        for position, row in enumerate(ranking, start=1):
            writer.writerow(
                [
                    position,
                    row["org_key"],
                    row.get("publisher_name") or "",
                    row["occurrence_count"],
                ]
            )

    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"csv": str(csv_path), "json": str(json_path)}


# --- Orquestación ------------------------------------------------------------

def run(
    facet_limit: int,
    timeout: int,
    resolve_names: bool,
    department_facet_limit: int = 40,
    taxon_facet_limit: int = 15,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    errors: list[str] = []

    total_count: int | None = None
    total_params: dict[str, Any] = {}
    try:
        total_count, total_params = fetch_total_count(timeout)
    except GbifError as error:
        errors.append(f"total_count: {error}")

    ranking: list[dict[str, Any]] = []
    facet_params: dict[str, Any] = {}
    try:
        ranking, facet_params = fetch_publisher_facet(facet_limit, timeout)
    except GbifError as error:
        errors.append(f"publisher_facet: {error}")

    department_ranking: list[dict[str, Any]] = []
    department_params: dict[str, Any] = {}
    if department_facet_limit > 0:
        try:
            department_ranking, department_params = fetch_department_facet(
                department_facet_limit, timeout
            )
        except GbifError as error:
            errors.append(f"department_facet: {error}")

    # Agregación por región ENCA (predominante) a partir del ranking de
    # departamentos. Es un cálculo local, no otra consulta a GBIF.
    region_ranking, departments_without_region = agrupar_por_region(department_ranking)

    # Desglose taxonómico: top órdenes y top familias. GBIF devuelve claves; los
    # nombres se resuelven luego contra /species/{key}.
    order_ranking: list[dict[str, Any]] = []
    order_params: dict[str, Any] = {}
    family_ranking: list[dict[str, Any]] = []
    family_params: dict[str, Any] = {}
    if taxon_facet_limit > 0:
        try:
            order_ranking, order_params = fetch_taxon_facet(
                "orderKey", taxon_facet_limit, timeout
            )
        except GbifError as error:
            errors.append(f"order_facet: {error}")
        try:
            family_ranking, family_params = fetch_taxon_facet(
                "familyKey", taxon_facet_limit, timeout
            )
        except GbifError as error:
            errors.append(f"family_facet: {error}")

    names_resolved = 0
    if resolve_names:
        for row in ranking:
            name = resolve_publisher_name(row["org_key"], timeout)
            row["publisher_name"] = name  # None si no se pudo (no se inventa)
            if name is not None:
                names_resolved += 1
    else:
        for row in ranking:
            row["publisher_name"] = None

    # Nombres de órdenes y familias (key -> canonicalName).
    _resolver_nombres_taxon(order_ranking, resolve_names, timeout)
    _resolver_nombres_taxon(family_ranking, resolve_names, timeout)

    finished_at = datetime.now(timezone.utc)

    status = "completed" if not errors else "completed_with_errors"

    report = {
        "source": "GBIF Occurrence API",
        "source_base_url": GBIF_BASE_URL,
        "scope": "Registros de aves (Aves, taxonKey=212) en Colombia (country=CO)",
        "extracted_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "query_params": {
            "total_count": total_params,
            "publisher_facet": facet_params,
            "department_facet": department_params,
            "order_facet": order_params,
            "family_facet": family_params,
        },
        "total_bird_records_colombia": total_count,
        "publisher_ranking": ranking,
        "publishers_in_ranking": len(ranking),
        "publisher_names_resolved": names_resolved,
        "department_ranking": department_ranking,
        "departments_in_ranking": len(department_ranking),
        "region_ranking": region_ranking,
        "regions_in_ranking": len(region_ranking),
        "departments_without_region": departments_without_region,
        "order_ranking": order_ranking,
        "orders_in_ranking": len(order_ranking),
        "family_ranking": family_ranking,
        "families_in_ranking": len(family_ranking),
        "region_mapping_note": (
            "Agrupación por región ENCA usando la región predominante de cada "
            "departamento. Propuesta del equipo, pendiente de confirmación por SAO."
        ),
        "errors": errors,
        "status": status,
        "notes": (
            "Conteos agregados de GBIF (limit=0 + facet); no se descargaron "
            "ocurrencias individuales. 'count' es el total vivo al momento de la "
            "consulta. Cifras y nombres no detectados se dejan como null. El "
            "desglose por departamento usa el campo stateProvince (texto libre "
            "de GBIF); las variantes de un mismo departamento se suman tras "
            "canonizar el nombre. Los registros sin departamento no aparecen, por "
            "lo que la suma por departamento puede ser menor que el total nacional."
        ),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fase 1: cifras de registros de aves de Colombia en GBIF "
            "(total + ranking de publicadores)."
        )
    )
    parser.add_argument(
        "--facet-limit",
        type=int,
        default=DEFAULT_FACET_LIMIT,
        help=f"Nº de publicadores en el ranking (por defecto {DEFAULT_FACET_LIMIT}).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout por consulta en segundos (por defecto {DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--no-resolve-names",
        action="store_true",
        help="No resolver orgKey -> nombre del publicador (menos llamadas).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Carpeta de salida (por defecto outputs/biodiversity_pilot/gbif).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecuta las consultas y muestra el resumen, pero no escribe archivos.",
    )
    args = parser.parse_args(argv)

    if args.facet_limit < 0:
        parser.error("--facet-limit no puede ser negativo.")

    now = datetime.now(timezone.utc)
    report = run(
        facet_limit=args.facet_limit,
        timeout=args.timeout,
        resolve_names=not args.no_resolve_names,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("\n[dry-run] No se escribieron archivos.", file=sys.stderr)
    else:
        paths = write_outputs(args.output_dir, now, report, report["publisher_ranking"])
        print(f"\nArchivos generados:\n  CSV:  {paths['csv']}\n  JSON: {paths['json']}",
              file=sys.stderr)

    # Código de salida: 0 si hubo al menos el total; 1 si todo falló.
    if report["total_bird_records_colombia"] is None and not report["publisher_ranking"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
