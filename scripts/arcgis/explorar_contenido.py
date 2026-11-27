#!/usr/bin/env python3
"""Inventario de SOLO LECTURA del contenido de ArcGIS Online.

Primer paso de la migración a ArcGIS (ver docs/deployment/arcgis-migration.md).
Este script NO crea, NI modifica, NI borra nada: solo LISTA los elementos de la
organización para entender qué capas, tablas y apps ya existen (p. ej.
``ContenidoENCA_publico`` y los mapas por eje montados por jcgomez_dreamgis),
decidir qué reutilizar y qué crear, y dónde encajar las tres vistas de SAO.

CRÉDITOS: listar contenido y leer metadatos NO consume créditos de ArcGIS
(los créditos se gastan en almacenamiento, análisis, geocodificación o teselas,
nada de lo cual hace este script). Es seguro ejecutarlo cuantas veces quieras.

AUTENTICACIÓN (elige UNA; nunca se escriben credenciales en el repo):
  1) Variables de entorno (mismas que publish_to_arcgis.py):
       ARCGIS_URL, ARCGIS_USERNAME, ARCGIS_PASSWORD
  2) Perfil guardado de la ArcGIS API for Python:  --perfil <nombre>
  3) Si ejecutas DENTRO de un Notebook de ArcGIS:  --home  (usa GIS("home"))

REQUISITO: el paquete ``arcgis`` instalado en el entorno:
    pip install arcgis

USO (desde la raíz, con el .venv activado):
    # con variables de entorno:
    python scripts/arcgis/explorar_contenido.py
    # con un perfil guardado:
    python scripts/arcgis/explorar_contenido.py --perfil sao_admin
    # filtrar por texto (p. ej. solo lo de ENCA):
    python scripts/arcgis/explorar_contenido.py --buscar ENCA
    # ver los campos/URL REST de un item concreto (una capa/tabla):
    python scripts/arcgis/explorar_contenido.py --item <ITEM_ID>
"""

from __future__ import annotations

import argparse
import json
import os
import sys


class ExploracionError(RuntimeError):
    """Error controlado del inventario (sin exponer credenciales)."""


def _conectar(perfil: str | None, usar_home: bool):
    """Crea un GIS autenticado. Importa ``arcgis`` de forma perezosa.

    Prioridad: --home > --perfil > variables de entorno. No imprime nunca la
    contraseña.
    """
    try:
        from arcgis.gis import GIS  # import perezoso (dependencia opcional)
    except ImportError as error:  # pragma: no cover - depende del entorno
        raise ExploracionError(
            "El paquete 'arcgis' no está instalado. Instálalo en tu .venv: "
            "pip install arcgis"
        ) from error

    if usar_home:
        return GIS("home")
    if perfil:
        return GIS(profile=perfil)

    url = os.environ.get("ARCGIS_URL")
    usuario = os.environ.get("ARCGIS_USERNAME")
    password = os.environ.get("ARCGIS_PASSWORD")
    if not (url and usuario and password):
        raise ExploracionError(
            "Faltan credenciales. Usa --home (dentro de un Notebook), --perfil "
            "<nombre>, o define ARCGIS_URL / ARCGIS_USERNAME / ARCGIS_PASSWORD."
        )
    return GIS(url, usuario, password)


def _listar_contenido(gis, buscar: str | None, limite: int) -> None:
    """Lista los items del usuario autenticado (y de su organización)."""
    usuario = gis.users.me
    print(f"Conectado como: {usuario.username}  (rol: {getattr(usuario, 'role', '?')})")
    print(f"Organización:   {gis.properties.get('name', '?')}")
    print("-" * 70)

    vistos: dict[str, object] = {}

    # 1) Contenido propio del usuario. ``items()`` puede devolver un generador en
    #    algunas versiones del paquete; se normaliza a lista. Las carpetas se
    #    recorren por nombre.
    def _a_lista(resultado) -> list:
        return list(resultado) if resultado is not None else []

    for item in _a_lista(usuario.items(max_items=1000)):
        vistos[item.id] = item
    for carpeta in _a_lista(usuario.folders):
        nombre_carpeta = carpeta.get("title") if isinstance(carpeta, dict) else str(carpeta)
        if not nombre_carpeta:
            continue
        for item in _a_lista(usuario.items(folder=nombre_carpeta, max_items=1000)):
            vistos[item.id] = item

    # 2) Búsqueda amplia en la organización (incluye items de otros usuarios, p.
    #    ej. jcgomez_dreamgis). Con filtro de texto usa title; sin filtro trae lo
    #    accesible mas reciente (acotado por ``limite``).
    consulta = f"title:{buscar}" if buscar else ""
    for item in _a_lista(gis.content.search(query=consulta, max_items=limite)):
        vistos[item.id] = item

    filas = sorted(vistos.values(), key=lambda it: (it.type, (it.title or "").lower()))
    if buscar:
        filas = [it for it in filas if buscar.lower() in (it.title or "").lower()]

    print(f"Items accesibles: {len(filas)}"
          + (f"  (filtro: '{buscar}')" if buscar else ""))
    print("-" * 70)
    tipo_actual = None
    for it in filas:
        if it.type != tipo_actual:
            tipo_actual = it.type
            print(f"\n== {tipo_actual} ==")
        print(f"  • {it.title}")
        print(f"      id={it.id}  owner={it.owner}")
        if it.url:
            print(f"      url={it.url}")


def _inspeccionar_item(gis, item_id: str) -> None:
    """Muestra detalle de un item: capas, tablas, campos y URL REST (sin tocar)."""
    item = gis.content.get(item_id)
    if item is None:
        raise ExploracionError(f"No se encontró el item con id={item_id}")
    print(f"Item: {item.title}")
    print(f"  tipo:  {item.type}")
    print(f"  owner: {item.owner}")
    print(f"  url:   {item.url}")

    # Si es una capa/tabla alojada, lista sus capas y tablas con sus campos.
    capas = getattr(item, "layers", None) or []
    tablas = getattr(item, "tables", None) or []
    for grupo, elementos in (("CAPA", capas), ("TABLA", tablas)):
        for elem in elementos:
            props = elem.properties
            print(f"\n  [{grupo}] {props.get('name', '?')}  "
                  f"(url={elem.url})")
            print(f"      nº de registros: {elem.query(return_count_only=True)}")
            campos = props.get("fields", []) or []
            print("      campos:")
            for campo in campos:
                print(f"        - {campo.get('name')}  ({campo.get('type')})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inventario de SOLO LECTURA del contenido de ArcGIS Online."
    )
    parser.add_argument("--perfil", help="Nombre de un perfil guardado de la ArcGIS API.")
    parser.add_argument("--home", action="store_true",
                        help="Usar GIS('home') (dentro de un Notebook de ArcGIS).")
    parser.add_argument("--buscar", help="Filtra los items cuyo título contenga este texto.")
    parser.add_argument("--item", help="Inspecciona un item concreto (capas, tablas, campos).")
    parser.add_argument("--limite", type=int, default=200,
                        help="Máximo de items a traer de la organización (def. 200).")
    args = parser.parse_args(argv)

    try:
        gis = _conectar(args.perfil, args.home)
        if args.item:
            _inspeccionar_item(gis, args.item)
        else:
            _listar_contenido(gis, args.buscar, args.limite)
    except ExploracionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
