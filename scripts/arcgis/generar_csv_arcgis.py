#!/usr/bin/env python3
"""Genera los CSV listos para publicar en ArcGIS Online, desde los datos
definitivos de los pipelines (el snapshot que ya consume la demo).

Es LOCAL: no toca ArcGIS, no consume créditos. Escribe un CSV por tabla en
``outputs/arcgis_migracion/``. Esos CSV son el insumo de la publicación
(scripts/arcgis/publicar_*.py) y el "contrato" de cada capa/tabla de ArcGIS.

Principios (coherentes con el proyecto):
  - Los datos de los pipelines son la FUENTE DE VERDAD; reemplazan las cifras
    (desactualizadas) que el sitio tiene hoy a mano. No se concilia ni se inventa.
  - Se migra TODO lo que muestran las 3 vistas (checklist en
    docs/deployment/arcgis-migration.md §3-ter), para que nada quede como
    "espejismo" visible solo en Vercel.
  - Para el mapa por departamento se añade el código DANE (la capa de límites de
    SAO, muni_depto_runap, usa DANE), además del GADM GID.

Uso (desde la raíz, con el .venv activado):
    python scripts/arcgis/generar_csv_arcgis.py
    python scripts/arcgis/generar_csv_arcgis.py --solo biodiversidad
"""

from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SNAP = _REPO / "frontend" / "public" / "api-snapshot"
_OUT = _REPO / "outputs" / "arcgis_migracion"


# --- Puente DANE <-> departamento (para unir con la capa de límites de SAO) --
# La capa muni_depto_runap usa el código DANE de 2 dígitos del departamento.
# Mapeo oficial nombre canónico (como en nuestros datos) -> código DANE. Son 32
# departamentos + Bogotá D.C. (11). No se infiere: es la codificación DANE
# estándar de Colombia.
_DANE_POR_DEPARTAMENTO = {
    "Amazonas": "91", "Antioquia": "05", "Arauca": "81", "Atlántico": "08",
    "Bogotá, D.C.": "11", "Bolívar": "13", "Boyacá": "15", "Caldas": "17",
    "Caquetá": "18", "Casanare": "85", "Cauca": "19", "Cesar": "20",
    "Chocó": "27", "Córdoba": "23", "Cundinamarca": "25", "Guainía": "94",
    "Guaviare": "95", "Huila": "41", "La Guajira": "44", "Magdalena": "47",
    "Meta": "50", "Nariño": "52", "Norte de Santander": "54", "Putumayo": "86",
    "Quindío": "63", "Risaralda": "66",
    "Archipiélago de San Andrés, Providencia y Santa Catalina": "88",
    "Santander": "68", "Sucre": "70", "Tolima": "73", "Valle del Cauca": "76",
    "Vaupés": "97", "Vichada": "99",
}


def _norm(texto: str) -> str:
    sin = "".join(c for c in unicodedata.normalize("NFKD", texto or "")
                  if not unicodedata.combining(c))
    limpio = sin.lower().replace(",", " ").replace(".", " ")
    return " ".join(limpio.split())


_DANE_NORM = {_norm(k): v for k, v in _DANE_POR_DEPARTAMENTO.items()}


def _dane(departamento: str) -> str:
    """Código DANE del departamento, o '' si no casa (no se inventa)."""
    return _DANE_NORM.get(_norm(departamento), "")


def _leer(ruta_rel: str) -> dict:
    return json.loads((_SNAP / ruta_rel).read_text(encoding="utf-8"))


def _escribir_csv(nombre: str, columnas: list[str], filas: list[dict]) -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    destino = _OUT / f"{nombre}.csv"
    # utf-8-sig para que ArcGIS/Excel respeten acentos al importar.
    with destino.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columnas, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filas)
    print(f"  -> {nombre}.csv  ({len(filas)} filas)")


# --- BIODIVERSIDAD -----------------------------------------------------------

def generar_biodiversidad() -> None:
    d = _leer("biodiversidad/gbif/resumen.json")
    print("Biodiversidad:")

    # Resumen (1 fila): cifras clave que el sitio muestra hoy a mano.
    amenazadas = d.get("especies_amenazadas", [])
    endemicas = sum(1 for e in amenazadas if e.get("endemica"))
    _escribir_csv("biodiv_resumen", [
        "total_registros_ocurrencia", "n_especies", "n_especies_amenazadas",
        "n_especies_endemicas", "n_familias", "n_ordenes", "extraido_utc",
    ], [{
        "total_registros_ocurrencia": d.get("total_registros_ocurrencia"),
        "n_especies": len(d.get("especies", [])),
        "n_especies_amenazadas": len(amenazadas),
        "n_especies_endemicas": endemicas,
        "n_familias": len(d.get("familias", [])),
        "n_ordenes": len(d.get("ordenes", [])),
        "extraido_utc": d.get("extraido_utc"),
    }])

    # Registros por departamento (+ DANE y GADM para el mapa).
    _escribir_csv("biodiv_departamentos",
                  ["rank", "departamento", "dane_depto", "gadm_gid", "registros_ocurrencia"],
                  [{**f, "dane_depto": _dane(f.get("departamento", ""))}
                   for f in d.get("departamentos", [])])

    # Riqueza de especies por departamento (+ DANE y GADM).
    _escribir_csv("biodiv_riqueza_departamentos",
                  ["rank", "departamento", "dane_depto", "gadm_gid", "especies"],
                  [{**f, "dane_depto": _dane(f.get("departamento", ""))}
                   for f in d.get("riqueza_departamentos", [])])

    _escribir_csv("biodiv_regiones", ["rank", "region", "registros_ocurrencia"],
                  d.get("regiones", []))
    _escribir_csv("biodiv_municipios", ["rank", "gadm_gid", "nombre", "registros_ocurrencia"],
                  d.get("municipios", []))
    _escribir_csv("biodiv_anios", ["anio", "registros_ocurrencia"], d.get("anios", []))
    _escribir_csv("biodiv_tipos_registro", ["rank", "codigo", "etiqueta", "registros_ocurrencia"],
                  d.get("tipos_registro", []))
    _escribir_csv("biodiv_iucn_categorias", ["rank", "codigo", "etiqueta", "registros_ocurrencia"],
                  d.get("iucn_categorias", []))

    # Especies amenazadas (una fila por especie; la serie por año va aparte).
    _escribir_csv("biodiv_especies_amenazadas", [
        "rank", "species_key", "gbif_portal_key", "nombre_cientifico",
        "nombre_comun", "iucn_codigo", "iucn_etiqueta", "registros_ocurrencia",
        "endemica",
    ], d.get("especies_amenazadas", []))

    # Serie (especie x año) en formato largo: 1 fila por (especie, año).
    serie = []
    for e in amenazadas:
        for p in e.get("por_anio", []) or []:
            serie.append({
                "species_key": e.get("species_key"),
                "nombre_cientifico": e.get("nombre_cientifico"),
                "anio": p.get("anio"),
                "registros_ocurrencia": p.get("registros_ocurrencia"),
            })
    _escribir_csv("biodiv_especies_amenazadas_por_anio",
                  ["species_key", "nombre_cientifico", "anio", "registros_ocurrencia"], serie)

    _escribir_csv("biodiv_ordenes", ["rank", "taxon_key", "gbif_portal_key", "nombre", "registros_ocurrencia"],
                  d.get("ordenes", []))
    _escribir_csv("biodiv_familias", ["rank", "taxon_key", "gbif_portal_key", "nombre", "registros_ocurrencia"],
                  d.get("familias", []))
    _escribir_csv("biodiv_especies", ["rank", "taxon_key", "gbif_portal_key", "nombre", "registros_ocurrencia"],
                  d.get("especies", []))
    _escribir_csv("biodiv_publicadores", ["rank", "org_key", "nombre", "registros_ocurrencia"],
                  d.get("publicadores", []))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera CSV listos para ArcGIS desde los datos de los pipelines."
    )
    parser.add_argument("--solo", choices=["biodiversidad"],
                        help="Genera solo un bloque (por defecto: todo lo disponible).")
    args = parser.parse_args(argv)

    print(f"Generando CSV en: {_OUT}")
    if args.solo in (None, "biodiversidad"):
        generar_biodiversidad()
    # (bibliometría y ENCA se añadirán en los siguientes pasos de la migración.)
    print("Listo. Revisa los CSV antes de publicarlos en ArcGIS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
