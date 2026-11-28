#!/usr/bin/env python3
"""Publica (o actualiza) en ArcGIS Online las tablas generadas para la migración.

Toma los CSV de ``outputs/arcgis_migracion/`` (creados por
``generar_csv_arcgis.py``) y los sube como **tablas alojadas** en ArcGIS Online,
siguiendo la convención de nombres de SAO (``AU_<nombre>``).

SEGURIDAD Y CRÉDITOS (lee esto):
  - Se ejecuta con TU sesión (variables de entorno / perfil / Notebook). Este
    script NUNCA almacena ni imprime la contraseña.
  - **dry-run por defecto:** sin ``--publicar`` no toca ArcGIS; solo dice qué
    haría. Con ``--publicar`` sí actúa.
  - Las tablas se publican con ``locationType = "none"``: ArcGIS las trata como
    TABLA y NO geocodifica (la geocodificación gastaría créditos; así no).
    Alojar estas tablas (texto/cifras) cuesta céntimos de crédito al mes.
  - Si la tabla ya existe (mismo título ``AU_<nombre>``), se ACTUALIZA por
    truncate + append (no se recrea el item, para no romper apps que la usen).
    Esto habilita la actualización periódica: regenerar CSV -> re-ejecutar.

AUTENTICACIÓN (igual que explorar_contenido.py):
  - Variables de entorno: ARCGIS_URL / ARCGIS_USERNAME / ARCGIS_PASSWORD
  - ``--perfil <nombre>`` (perfil guardado de la ArcGIS API)
  - ``--home`` (dentro de un Notebook de ArcGIS)

USO (desde la raíz, con el .venv activado):
    # Ver qué haría (sin tocar ArcGIS):
    python scripts/arcgis/publicar_tablas.py --tabla biodiv_regiones
    # Publicar/actualizar de verdad una tabla:
    python scripts/arcgis/publicar_tablas.py --tabla biodiv_regiones --publicar
    # Publicar/actualizar TODAS las tablas del directorio:
    python scripts/arcgis/publicar_tablas.py --todas --publicar
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CSV_DIR = _REPO / "outputs" / "arcgis_migracion"
_PREFIJO = "AU_"  # convención de nombres de SAO en la organización.


class PublicacionError(RuntimeError):
    """Error controlado de publicación (sin exponer credenciales)."""


def _conectar(perfil: str | None, usar_home: bool):
    """Crea un GIS autenticado. Importa ``arcgis`` de forma perezosa."""
    try:
        from arcgis.gis import GIS
    except ImportError as error:  # pragma: no cover
        raise PublicacionError(
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
        raise PublicacionError(
            "Faltan credenciales. Usa --home, --perfil <nombre>, o define "
            "ARCGIS_URL / ARCGIS_USERNAME / ARCGIS_PASSWORD."
        )
    return GIS(url, usuario, password)


def _leer_csv(ruta: Path) -> tuple[list[str], list[dict]]:
    with ruta.open(encoding="utf-8-sig", newline="") as handle:
        lector = csv.DictReader(handle)
        filas = list(lector)
        columnas = lector.fieldnames or []
    return columnas, filas


def _buscar_item(gis, titulo: str):
    """Devuelve NUESTRA tabla alojada con ese título EXACTO, o None.

    Coincidencia estricta para no tocar nunca contenido ajeno (p. ej. los web
    maps / capas de la carpeta ENCA): exige (1) título idéntico, (2) que seamos
    el dueño y (3) que el item contenga una tabla (``.tables``), es decir, que
    sea una de las tablas que publica este mismo script. Un Feature Layer con
    geometría (como los de límites) no tiene ``.tables`` y queda descartado.
    """
    usuario = gis.users.me.username
    resultados = gis.content.search(
        query=f'title:"{titulo}" owner:{usuario}',
        item_type="Feature Service",
        max_items=50,
    )
    for it in resultados or []:
        if it.title != titulo:
            continue  # ArcGIS puede traer coincidencias parciales: exigir exacto.
        if getattr(it, "owner", None) != usuario:
            continue  # nunca tocar items de otro propietario.
        try:
            tiene_tabla = bool(it.tables)
        except Exception:  # pragma: no cover - item sin tablas/no accesible
            tiene_tabla = False
        if tiene_tabla:
            return it
    return None


def _filas_tipadas(columnas: list[str], filas: list[dict]) -> list[dict]:
    """Convierte números de texto a int/float cuando toda la columna lo es.

    Mejora el tipo de campo que ArcGIS infiere (numérico vs texto). No fuerza:
    si una columna tiene algún valor no numérico, se deja como texto.
    """
    numericas: dict[str, str] = {}
    for col in columnas:
        valores = [(f.get(col) or "").strip() for f in filas]
        no_vacios = [v for v in valores if v != ""]
        if not no_vacios:
            continue
        if all(_es_entero(v) for v in no_vacios):
            numericas[col] = "int"
        elif all(_es_float(v) for v in no_vacios):
            numericas[col] = "float"
    salida = []
    for f in filas:
        nueva = dict(f)
        for col, tipo in numericas.items():
            v = (f.get(col) or "").strip()
            if v == "":
                nueva[col] = None
            else:
                nueva[col] = int(v) if tipo == "int" else float(v)
        salida.append(nueva)
    return salida


def _es_entero(v: str) -> bool:
    try:
        int(v)
        return True
    except ValueError:
        return False


def _es_float(v: str) -> bool:
    try:
        float(v)
        return True
    except ValueError:
        return False


def _publicar_una(gis, ruta_csv: Path, publicar: bool,
                  carpeta_nombre: str | None = None) -> None:
    nombre = ruta_csv.stem
    titulo = f"{_PREFIJO}{nombre}"
    columnas, filas = _leer_csv(ruta_csv)
    existente = _buscar_item(gis, titulo)

    print(f"\n== {titulo} ==  ({len(filas)} filas, {len(columnas)} columnas)")
    if not publicar:
        accion = "ACTUALIZARÍA (truncate+append)" if existente else "CREARÍA (nueva tabla)"
        print(f"  [dry-run] {accion}. Columnas: {', '.join(columnas)}")
        return

    if existente is not None:
        # Actualizar: truncate + append sobre la tabla existente.
        tabla = existente.tables[0]
        tabla.delete_features(where="1=1")
        filas_tipadas = _filas_tipadas(columnas, filas)
        adds = [{"attributes": f} for f in filas_tipadas]
        res = tabla.edit_features(adds=adds)
        ok = sum(1 for r in res.get("addResults", []) if r.get("success"))
        print(f"  actualizada: {ok}/{len(filas)} filas (item {existente.id})")
        return

    # Crear: subir el CSV como item y publicarlo como TABLA (locationType none).
    # API moderna (arcgis >= 2.x): Folder.add() con ItemProperties. El viejo
    # gis.content.add() está obsoleto y además dispara un bug interno
    # (_is_geoenabled) al intentar detectar datos espaciales en el CSV.
    from arcgis.gis import ItemProperties, ItemTypeEnum

    carpeta = gis.content.folders.get(folder=carpeta_nombre) if carpeta_nombre \
        else gis.content.folders.get()
    props = ItemProperties(
        title=titulo,
        item_type=ItemTypeEnum.CSV,
        tags=["SAO", "ENCA", "migracion"],
    )
    item_csv = carpeta.add(item_properties=props, file=str(ruta_csv)).result()
    # locationType="none": ArcGIS trata el CSV como TABLA y NO geocodifica.
    publicado = item_csv.publish(publish_parameters={"locationType": "none"})
    print(f"  creada: tabla alojada '{publicado.title}' (item {publicado.id})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publica/actualiza las tablas de migración en ArcGIS Online."
    )
    parser.add_argument("--perfil", help="Perfil guardado de la ArcGIS API.")
    parser.add_argument("--home", action="store_true", help="GIS('home') (Notebook).")
    parser.add_argument("--tabla", help="Nombre de un CSV concreto (sin .csv).")
    parser.add_argument("--todas", action="store_true", help="Procesa todos los CSV del directorio.")
    parser.add_argument("--publicar", action="store_true",
                        help="Ejecuta de verdad (por defecto es dry-run).")
    parser.add_argument("--carpeta",
                        help="Carpeta ArcGIS donde crear las tablas nuevas "
                             "(p. ej. 'SAO - Biodiversidad'). Debe existir. "
                             "Por defecto, la raíz del usuario.")
    args = parser.parse_args(argv)

    if not _CSV_DIR.exists():
        print(f"ERROR: no existe {_CSV_DIR}. Ejecuta antes generar_csv_arcgis.py.",
              file=sys.stderr)
        return 1

    if args.tabla:
        rutas = [_CSV_DIR / f"{args.tabla}.csv"]
    elif args.todas:
        rutas = sorted(_CSV_DIR.glob("*.csv"))
    else:
        parser.error("Indica --tabla <nombre> o --todas.")
        return 2

    faltan = [r for r in rutas if not r.exists()]
    if faltan:
        print("ERROR: no existen: " + ", ".join(str(r) for r in faltan), file=sys.stderr)
        return 1

    try:
        gis = _conectar(args.perfil, args.home)
        print(f"Conectado como: {gis.users.me.username}")
        if not args.publicar:
            print("MODO DRY-RUN: no se tocará ArcGIS. Añade --publicar para actuar.")
        for ruta in rutas:
            _publicar_una(gis, ruta, args.publicar, args.carpeta)
    except PublicacionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
