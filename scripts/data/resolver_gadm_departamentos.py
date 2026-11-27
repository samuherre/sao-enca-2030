"""Resuelve el GADM GID (identificador geográfico del portal GBIF) de cada
departamento de las tablas de biodiversidad y lo guarda como ``gadm_gid``.

POR QUÉ GADM Y NO EL NOMBRE (stateProvince)
-------------------------------------------
El portal web de GBIF filtra por departamento con el parámetro ``gadmGid`` y un
identificador de área administrativa estable (p. ej. Cauca = ``COL.11_2``), NO
con el texto del campo ``stateProvince``. GBIF deriva el GADM de las coordenadas,
así que agrupa el departamento completo sin depender de cómo esté escrito el
nombre (Nariño/Narino, Valle/Valle del Cauca...). Esto:

  - hace que el enlace cuadre con el departamento completo (no una variante);
  - es el identificador que recomienda GBIF (el filtro por State/province excluye
    registros sin ese campo de texto);
  - se alinea con el destino del producto (ArcGIS), que trabaja con códigos y
    geometría administrativa, no con cadenas de texto libre.

FUENTE DEL MAPEO (oficial, no inventado)
----------------------------------------
GET https://api.gbif.org/v1/geocode/gadm/COL/subdivisions
    -> lista de departamentos nivel 1 con su ``id`` (GID), ``name`` canónico y
       ``variantName`` (sinónimos). Se casa el nombre de nuestra tabla contra
       ``name`` + ``variantName`` normalizando acentos y puntuación. Dos nombres
       DANE que no coinciden textualmente con GADM se mapean con alias explícito.

USO
---
    .venv\\Scripts\\python scripts/data/resolver_gadm_departamentos.py

Idempotente. No inventa: si un departamento no casa con ningún GID de GADM, deja
``gadm_gid`` en null y lo reporta; el frontend entonces no muestra enlace para
esa fila (en vez de un enlace roto).

NOTA — PUENTE TEMPORAL (el pipeline ya resuelve el GID de departamentos)
------------------------------------------------------------------------
El pipeline (``scripts/biodiversity_pilot/gbif_bird_counts.py`` ->
``fetch_department_facet``) YA resuelve el ``gadm_gid`` de departamentos y lo
incluye en el report y en los CSV de ArcGIS (ver
``docs/biodiversity/arcgis-upload-guide.md`` §11). Sin embargo, el CORTE GBIF que
sirve la demo hoy se generó ANTES de ese cambio y no trae el ``gadm_gid`` en
departamentos; por eso este post-proceso sigue siendo necesario para que el
snapshot de la demo tenga los GID. Cuando se regenere el corte con el pipeline
actual (``gbif_bird_counts_history.py``), el ``gadm_gid`` llegará nativo desde el
backend y este script podrá retirarse de ``regenerar_snapshot_demo.py``.
"""

from __future__ import annotations

import json
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

GADM_URL = "https://api.gbif.org/v1/geocode/gadm/COL/subdivisions"

SNAPSHOT = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend"
    / "public"
    / "api-snapshot"
    / "biodiversidad"
    / "gbif"
    / "resumen.json"
)

# Alias explícitos: nombre de NUESTRA tabla (forma DANE) -> nombre con el que
# GADM lo registra. Solo para los casos que no casan por texto ni por variante.
# No se inventan: se verificaron contra la respuesta de GADM. Las claves se
# comparan ya NORMALIZADAS (ver gid_de), así que aquí van en texto llano.
ALIAS_A_GADM = {
    "Bogotá, D.C.": "Bogotá D.C.",
    "Archipiélago de San Andrés, Providencia y Santa Catalina": "San Andrés y Providencia",
}


def _norm(texto: str) -> str:
    """Normaliza para comparar: sin acentos, sin puntuación suave, minúsculas."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    limpio = sin_acentos.lower()
    for ch in ",.":
        limpio = limpio.replace(ch, " ")
    return " ".join(limpio.split())


def cargar_mapa_gadm() -> dict[str, str]:
    """Descarga el mapeo normalizado {nombre o variante -> GID} de GADM COL."""
    with urllib.request.urlopen(GADM_URL, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    mapa: dict[str, str] = {}
    for sub in data:
        gid = sub.get("id")
        if not isinstance(gid, str):
            continue
        nombres = [sub.get("name")] + list(sub.get("variantName") or [])
        for nombre in nombres:
            if isinstance(nombre, str) and nombre.strip():
                mapa[_norm(nombre)] = gid
    return mapa


def gid_de(nombre: str, mapa: dict[str, str]) -> str | None:
    """Devuelve el GID de un nombre de departamento, o None si no casa."""
    clave = _norm(nombre)
    if clave in mapa:
        return mapa[clave]
    # Alias: se comparan las claves del dict ya normalizadas, igual que ``clave``.
    for alias_origen, alias_gadm in ALIAS_A_GADM.items():
        if _norm(alias_origen) == clave:
            return mapa.get(_norm(alias_gadm))
    return None


def main() -> int:
    if not SNAPSHOT.exists():
        print(f"ERROR: no existe el snapshot {SNAPSHOT}", file=sys.stderr)
        return 1

    try:
        mapa = cargar_mapa_gadm()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        print(f"ERROR: no se pudo obtener el mapeo GADM: {exc}", file=sys.stderr)
        return 1
    print(f"GADM: {len(mapa)} nombres/variantes de departamento cargados.")

    datos = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    sin_match: set[str] = set()
    total = 0
    resueltos = 0

    for clave_lista in ("departamentos", "riqueza_departamentos"):
        for fila in datos.get(clave_lista) or []:
            nombre = fila.get("departamento")
            total += 1
            if not isinstance(nombre, str) or not nombre.strip():
                fila["gadm_gid"] = None
                continue
            gid = gid_de(nombre, mapa)
            fila["gadm_gid"] = gid
            if gid:
                resueltos += 1
            else:
                sin_match.add(nombre)

    SNAPSHOT.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Resueltos {resueltos}/{total} (incluye ambas tablas). Snapshot actualizado.")
    if sin_match:
        print(f"Sin GID GADM ({len(sin_match)}): {', '.join(sorted(sin_match))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
