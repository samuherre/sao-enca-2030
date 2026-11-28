#!/usr/bin/env python3
"""Organiza en ArcGIS Online las tablas de la migración: carpeta + compartir.

Mueve nuestras tablas (prefijo ``AU_``, de las 3 vistas) a una carpeta propia y
ajusta su nivel de compartición. Reproducible e idempotente: volver a correrlo
no crea duplicados ni rompe nada.

SEGURIDAD Y CRÉDITOS:
  - Mover de carpeta y compartir NO consumen créditos.
  - **dry-run por defecto:** sin ``--aplicar`` solo informa qué haría.
  - Solo toca items de los que eres dueño cuyo título empieza por los prefijos
    de las 3 vistas (``AU_biodiv_``, ``AU_biblio_``, ``AU_enca_``). Nunca toca
    el contenido de Juan Camilo (otros títulos / web maps / capas de límites).

AUTENTICACIÓN (igual que los otros scripts):
  --perfil <nombre> | --home | o ARCGIS_URL / ARCGIS_USERNAME / ARCGIS_PASSWORD

USO (desde la raíz, con el .venv):
    # Ver qué haría:
    python scripts/arcgis/organizar_tablas.py --perfil sao_rnoa
    # Aplicar: mover a carpeta y compartir a nivel organización:
    python scripts/arcgis/organizar_tablas.py --perfil sao_rnoa --aplicar
    # Compartir públicamente (hazlo solo al final, con el dashboard listo):
    python scripts/arcgis/organizar_tablas.py --perfil sao_rnoa --nivel public --aplicar
"""

from __future__ import annotations

import argparse
import os
import sys

_CARPETA_DEFECTO = "SAO - Observatorio"
_PREFIJOS = ("AU_biodiv_", "AU_biblio_", "AU_enca_")


class OrganizacionError(RuntimeError):
    """Error controlado (sin exponer credenciales)."""


def _conectar(perfil: str | None, usar_home: bool):
    try:
        from arcgis.gis import GIS
    except ImportError as error:  # pragma: no cover
        raise OrganizacionError(
            "El paquete 'arcgis' no está instalado: pip install arcgis"
        ) from error
    if usar_home:
        return GIS("home")
    if perfil:
        return GIS(profile=perfil)
    url = os.environ.get("ARCGIS_URL")
    usuario = os.environ.get("ARCGIS_USERNAME")
    password = os.environ.get("ARCGIS_PASSWORD")
    if not (url and usuario and password):
        raise OrganizacionError(
            "Faltan credenciales. Usa --home, --perfil <nombre>, o define "
            "ARCGIS_URL / ARCGIS_USERNAME / ARCGIS_PASSWORD."
        )
    return GIS(url, usuario, password)


def _nuestras_tablas(gis) -> list:
    """Items Feature Service nuestros cuyo título empieza por los prefijos."""
    usuario = gis.users.me.username
    items = gis.content.search(
        query=f"owner:{usuario}", item_type="Feature Service", max_items=400
    )
    return sorted(
        (i for i in items if i.title.startswith(_PREFIJOS)),
        key=lambda x: x.title,
    )


def _nivel_enum(gis, nivel: str):
    """Devuelve el miembro de SharingLevel pedido.

    En vez de importar desde una ruta privada (que cambia entre versiones de
    'arcgis'), toma el enum desde un item real y busca el miembro por su valor.
    """
    usuario = gis.users.me.username
    muestra = gis.content.search(
        query=f"owner:{usuario}", item_type="Feature Service", max_items=1
    )
    if not muestra:
        raise OrganizacionError("No hay items para resolver SharingLevel.")
    enum_cls = type(muestra[0].sharing.sharing_level)
    objetivo = {"org": "ORGANIZATION", "public": "EVERYONE", "private": "PRIVATE"}[nivel]
    for miembro in enum_cls:
        if miembro.value == objetivo or miembro.name == objetivo:
            return miembro
    raise OrganizacionError(f"No se encontró SharingLevel para '{nivel}'.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mueve a carpeta y comparte las tablas de la migración."
    )
    parser.add_argument("--perfil", help="Perfil guardado de la ArcGIS API.")
    parser.add_argument("--home", action="store_true", help="GIS('home').")
    parser.add_argument("--carpeta", default=_CARPETA_DEFECTO,
                        help=f"Carpeta destino (defecto: '{_CARPETA_DEFECTO}').")
    parser.add_argument("--nivel", choices=("org", "public", "private"),
                        default="org", help="Nivel de compartición (defecto: org).")
    parser.add_argument("--aplicar", action="store_true",
                        help="Ejecuta de verdad (por defecto es dry-run).")
    args = parser.parse_args(argv)

    try:
        gis = _conectar(args.perfil, args.home)
        print(f"Conectado como: {gis.users.me.username}")
        tablas = _nuestras_tablas(gis)
        if not tablas:
            print("No se encontraron tablas AU_ de las 3 vistas.")
            return 0
        print(f"Tablas a organizar: {len(tablas)}")
        if not args.aplicar:
            print("MODO DRY-RUN: no se tocará ArcGIS. Añade --aplicar para actuar.")
            print(f"  carpeta destino: '{args.carpeta}'  |  nivel: {args.nivel}")
            for it in tablas:
                print(f"  - {it.title:42} (carpeta={it.ownerFolder or 'raíz'}, "
                      f"compartir={it.access})")
            return 0

        # Crear carpeta destino (idempotente).
        gis.content.folders.create(folder=args.carpeta, exist_ok=True)
        nivel = _nivel_enum(gis, args.nivel)

        movidas = compartidas = 0
        for it in tablas:
            try:
                it.move(folder=args.carpeta)
                movidas += 1
            except Exception as err:  # pragma: no cover
                print(f"  AVISO: no se pudo mover {it.title}: {err}", file=sys.stderr)
            try:
                it.sharing.sharing_level = nivel
                compartidas += 1
            except Exception as err:  # pragma: no cover
                print(f"  AVISO: no se pudo compartir {it.title}: {err}",
                      file=sys.stderr)
            print(f"  OK {it.title:42} -> carpeta '{args.carpeta}', nivel {args.nivel}")
        print(f"\nResumen: movidas {movidas}/{len(tablas)}, "
              f"compartidas {compartidas}/{len(tablas)}.")
    except OrganizacionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
