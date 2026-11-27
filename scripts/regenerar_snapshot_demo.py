"""Regenera el snapshot estático de la demo COMPLETO y en el orden correcto.

PROBLEMA QUE RESUELVE
---------------------
``export_static_snapshot.py`` congela las respuestas del backend en
``frontend/public/api-snapshot/``. Pero el backend NO conoce dos conjuntos de
campos de la vista de biodiversidad, que se resuelven por API externa en
post-proceso sobre el propio snapshot:

  - ``gbif_portal_key`` (clave COL XR del portal GBIF) en especies amenazadas,
    familias y órdenes  -> scripts/data/resolver_claves_gbif_portal.py
  - ``gadm_gid`` (área administrativa GADM) en departamentos y riqueza por
    departamento  -> scripts/data/resolver_gadm_departamentos.py

Como el export sobrescribe el snapshot ÍNTEGRO, cada vez que se ejecuta BORRA
esos campos (el backend los deja en null). Si no se re-ejecutan los dos scripts
de post-proceso, los enlaces a GBIF por taxón y por departamento dejan de
funcionar en la demo.

Este orquestador hace el flujo completo en el ORDEN correcto, para que nadie
tenga que recordarlo:

    1. export_static_snapshot.py        (congela backend -> snapshot)
    2. resolver_claves_gbif_portal.py   (reañade gbif_portal_key)
    3. resolver_gadm_departamentos.py   (reañade gadm_gid de departamentos)

REQUISITO: el backend debe estar corriendo en http://127.0.0.1:8000 antes de
ejecutar (igual que export_static_snapshot.py). Los pasos 2 y 3 consultan la API
pública de GBIF (requieren internet).

USO
---
    1. Levanta el backend:
         .venv\\Scripts\\python -m uvicorn backend.src.main:app --port 8000
    2. Ejecuta este script:
         .venv\\Scripts\\python scripts/regenerar_snapshot_demo.py

Tras terminar, revisa y commitea frontend/public/api-snapshot/ y redespliega.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_PASOS = [
    ("Exportar snapshot desde el backend", _SCRIPTS_DIR / "export_static_snapshot.py"),
    ("Reañadir claves COL XR de GBIF (taxones)", _SCRIPTS_DIR / "data" / "resolver_claves_gbif_portal.py"),
    ("Reañadir GADM GID (departamentos)", _SCRIPTS_DIR / "data" / "resolver_gadm_departamentos.py"),
]


def main() -> int:
    for titulo, script in _PASOS:
        print(f"\n=== {titulo} ===\n  ({script.name})")
        if not script.exists():
            print(f"ERROR: no existe {script}", file=sys.stderr)
            return 1
        resultado = subprocess.run([sys.executable, str(script)], check=False)
        if resultado.returncode != 0:
            print(
                f"\nERROR: el paso '{titulo}' falló (código {resultado.returncode}). "
                "Se detiene la regeneración para no dejar el snapshot a medias.",
                file=sys.stderr,
            )
            return resultado.returncode

    print(
        "\nSnapshot de demo regenerado por completo (backend + post-proceso GBIF/GADM).\n"
        "Revisa y commitea frontend/public/api-snapshot/ y redespliega el frontend."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
