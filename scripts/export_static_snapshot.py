"""Genera un snapshot ESTÁTICO de la API para el despliegue de demostración.

Este script recorre la API del backend (que debe estar corriendo localmente) y
"congela" todas sus respuestas como archivos JSON dentro de
``frontend/public/api-snapshot/``. El frontend, cuando se compila en modo
estático (sin backend), lee esos archivos en lugar de llamar a la API.

Propósito (demo para retroalimentación de SAO):
- Permite desplegar SOLO el frontend (estático) en Vercel, sin servidor ni base
  de datos. Los datos mostrados son un corte real tomado del backend local.
- Es un artefacto de DEMO, no la aplicación definitiva (el destino es ArcGIS).

Uso:
    1. Levanta el backend:
         .venv\\Scripts\\python -m uvicorn backend.src.main:app --port 8000
    2. Ejecuta este script:
         .venv\\Scripts\\python scripts/export_static_snapshot.py

El mapeo ruta -> archivo replica la estructura de rutas de la API:
    GET /ejes                               -> ejes.json
    GET /ejes/{id}/arbol                     -> ejes/{id}/arbol.json
    GET /ejes/{id}/metas                     -> ejes/{id}/metas.json
    GET /metas/{id}/objetivos                -> metas/{id}/objetivos.json
    GET /objetivos/{id}/indicadores          -> objetivos/{id}/indicadores.json
    GET /indicadores/{id}/actividades        -> indicadores/{id}/actividades.json
    GET /bibliometria/resumen                -> bibliometria/resumen.json
    GET /bibliometria/resumen/anio/{anio}    -> bibliometria/resumen/anio/{anio}.json
    GET /bibliometria/boletin-sao/resumen    -> bibliometria/boletin-sao/resumen.json
    GET /biodiversidad/gbif/resumen          -> biodiversidad/gbif/resumen.json

También genera los GET individuales por id (ejes/{id}.json, metas/{id}.json,
etc.) para que la navegación directa funcione en el frontend estático.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "http://127.0.0.1:8000"

# Carpeta de salida: dentro de public/ para que Vite la sirva tal cual.
OUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "api-snapshot"


def fetch(path: str) -> object | None:
    """Pide una ruta GET a la API y devuelve el JSON, o None si da 404/error."""
    url = f"{API_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"  [{exc.code}] {path}")
        return None
    except Exception as exc:  # noqa: BLE001 - script de utilidad, reporta y sigue
        print(f"  [ERROR] {path}: {exc}")
        return None


def fetch_text(path: str) -> str | None:
    """Pide una ruta GET y devuelve el cuerpo como TEXTO (p. ej. CSV), o None."""
    url = f"{API_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        print(f"  [{exc.code}] {path}")
        return None
    except Exception as exc:  # noqa: BLE001 - script de utilidad, reporta y sigue
        print(f"  [ERROR] {path}: {exc}")
        return None


def write_json(rel_path: str, data: object) -> None:
    """Escribe ``data`` como JSON en OUT_DIR/rel_path (crea carpetas)."""
    dest = OUT_DIR / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {rel_path}")


def write_text(rel_path: str, contenido: str) -> None:
    """Escribe ``contenido`` tal cual (texto) en OUT_DIR/rel_path (crea carpetas)."""
    dest = OUT_DIR / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contenido, encoding="utf-8")
    print(f"  -> {rel_path}")


def export_hierarchy() -> None:
    """Recorre Eje -> Meta -> Objetivo -> Indicador -> Actividad y congela todo."""
    ejes = fetch("/ejes")
    if ejes is None:
        ejes = []
    write_json("ejes.json", ejes)

    for eje in ejes:
        eje_id = eje["id"]
        write_json(f"ejes/{eje_id}.json", eje)

        arbol = fetch(f"/ejes/{eje_id}/arbol")
        if arbol is not None:
            write_json(f"ejes/{eje_id}/arbol.json", arbol)

        metas = fetch(f"/ejes/{eje_id}/metas") or []
        write_json(f"ejes/{eje_id}/metas.json", metas)

        for meta in metas:
            meta_id = meta["id"]
            write_json(f"metas/{meta_id}.json", meta)

            objetivos = fetch(f"/metas/{meta_id}/objetivos") or []
            write_json(f"metas/{meta_id}/objetivos.json", objetivos)

            for objetivo in objetivos:
                obj_id = objetivo["id"]
                write_json(f"objetivos/{obj_id}.json", objetivo)

                indicadores = fetch(f"/objetivos/{obj_id}/indicadores") or []
                write_json(f"objetivos/{obj_id}/indicadores.json", indicadores)

                for indicador in indicadores:
                    ind_id = indicador["id"]
                    write_json(f"indicadores/{ind_id}.json", indicador)

                    actividades = fetch(f"/indicadores/{ind_id}/actividades") or []
                    write_json(f"indicadores/{ind_id}/actividades.json", actividades)

                    for actividad in actividades:
                        act_id = actividad["id"]
                        write_json(f"actividades/{act_id}.json", actividad)


def export_bibliometria() -> None:
    """Congela los resúmenes bibliométricos (sin base de datos).

    Además del consolidado de "todos los años", genera un archivo por cada año
    disponible (``bibliometria/resumen/anio/{anio}.json``) para que el filtro
    por año del dashboard funcione en la demo estática, donde no hay backend que
    atienda el filtro en vivo. Los años se toman de ``anios_disponibles`` del
    propio consolidado, de modo que el snapshot cubra exactamente los años que
    el frontend ofrecerá en el desplegable.
    """
    consolidado = fetch("/bibliometria/resumen")
    if consolidado is not None:
        write_json("bibliometria/resumen.json", consolidado)
        # Una variante congelada por cada año disponible (filtro del dashboard).
        anios = []
        if isinstance(consolidado, dict):
            anios = consolidado.get("anios_disponibles") or []
        for anio in anios:
            por_anio = fetch(f"/bibliometria/resumen/anio/{anio}")
            if por_anio is not None:
                write_json(f"bibliometria/resumen/anio/{anio}.json", por_anio)

        # CSV descargable del consolidado (todos + uno por año) para la demo.
        csv_todos = fetch_text("/bibliometria/export.csv")
        if csv_todos is not None:
            write_text("bibliometria/export.csv", csv_todos)
        for anio in anios:
            csv_anio = fetch_text(f"/bibliometria/export/anio/{anio}.csv")
            if csv_anio is not None:
                write_text(f"bibliometria/export/anio/{anio}.csv", csv_anio)

        # Por cada OFC presente: listado JSON (acotado) + CSV completo, para
        # que el clic en la barra funcione en la demo estática.
        ofcs = []
        if isinstance(consolidado, dict):
            ofcs = [o.get("ofc_id") for o in (consolidado.get("por_ofc") or []) if o.get("ofc_id")]
        for ofc_id in ofcs:
            lista = fetch(f"/bibliometria/ofc/{ofc_id}/articulos")
            if lista is not None:
                write_json(f"bibliometria/ofc/{ofc_id}/articulos.json", lista)
            csv_ofc = fetch_text(f"/bibliometria/ofc/{ofc_id}/export.csv")
            if csv_ofc is not None:
                write_text(f"bibliometria/ofc/{ofc_id}/export.csv", csv_ofc)

    boletin = fetch("/bibliometria/boletin-sao/resumen")
    if boletin is not None:
        write_json("bibliometria/boletin-sao/resumen.json", boletin)


def export_biodiversidad() -> None:
    """Congela el resumen GBIF almacenado (sin base de datos)."""
    resumen = fetch("/biodiversidad/gbif/resumen")
    if resumen is not None:
        write_json("biodiversidad/gbif/resumen.json", resumen)


def main() -> int:
    # Comprueba que el backend responde antes de empezar.
    if fetch("/ejes") is None:
        print(
            "ERROR: no se pudo contactar el backend en "
            f"{API_BASE}. Levántalo antes de exportar.",
            file=sys.stderr,
        )
        return 1

    print(f"Exportando snapshot estático a: {OUT_DIR}")
    export_hierarchy()
    export_bibliometria()
    export_biodiversidad()
    print("Snapshot estático generado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
