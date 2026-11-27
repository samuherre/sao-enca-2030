"""Resuelve la clave COL XR (nuevo backbone de GBIF) de cada especie amenazada
del snapshot de biodiversidad y la guarda como ``gbif_portal_key``.

CONTEXTO DEL BUG
----------------
El portal web actual de GBIF (gbif.org/occurrence/search) migró su taxonomía al
"Catalogue of Life Extended Release" (COL XR), que identifica los taxones con
claves ALFANUMÉRICAS cortas (p. ej. Aves = "V2", Sericossypha albocristata =
"6YJKF"), NO con las claves numéricas del backbone antiguo ("212", "2488675").

Los enlaces "Ver registros en GBIF" de la vista de biodiversidad usaban la clave
numérica legacy como ``taxonKey``. El portal nuevo no la reconoce: la trata como
texto, muestra el chip "Scientific name : 2488675" y devuelve 0 resultados.

La forma correcta para el portal es ``taxonKey=<clave COL XR>``. Este script
obtiene esa clave para cada especie por su nombre científico, consultando el
endpoint de match de GBIF contra el checklist COL XR, y la añade al snapshot que
consume el frontend estático.

FUENTE DE LA CLAVE
------------------
GET https://api.gbif.org/v2/species/match
      ?scientificName=<nombre>
      &checklistKey=7ddf754f-d193-4cc9-b351-99906754a03b   (COL XR, por defecto)
    -> usage.key   (p. ej. "6YJKF")

El checklistKey de COL XR es público y es el que usa el portal nuevo por defecto
(ver guía de migración de rgbif, "COL XR as Default").

USO
---
    .venv\\Scripts\\python scripts/data/resolver_claves_gbif_portal.py

Es idempotente: re-ejecutarlo vuelve a resolver y reescribe ``gbif_portal_key``.
No inventa datos: si una especie no hace match, deja ``gbif_portal_key`` en null
y lo reporta; el frontend entonces cae al enlace solo-país para esa especie.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# checklistKey del Catalogue of Life Extended Release (backbone del portal nuevo).
COL_XR_CHECKLIST_KEY = "7ddf754f-d193-4cc9-b351-99906754a03b"
MATCH_URL = "https://api.gbif.org/v2/species/match"

SNAPSHOT = (
    Path(__file__).resolve().parent.parent.parent
    / "frontend"
    / "public"
    / "api-snapshot"
    / "biodiversidad"
    / "gbif"
    / "resumen.json"
)


def resolver_clave_col(nombre_cientifico: str) -> str | None:
    """Devuelve la clave COL XR (``usage.key``) de un nombre científico, o None.

    Solo acepta coincidencias reales (``matchType`` distinto de ``NONE``) para no
    inventar una clave cuando GBIF no reconoce el nombre.
    """
    params = urllib.parse.urlencode(
        {"scientificName": nombre_cientifico, "checklistKey": COL_XR_CHECKLIST_KEY}
    )
    url = f"{MATCH_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        print(f"  [ERROR red] {nombre_cientifico}: {exc}")
        return None

    diagnostico = data.get("diagnostics") or {}
    if diagnostico.get("matchType") in (None, "NONE"):
        return None
    usage = data.get("usage") or {}
    clave = usage.get("key")
    return clave if isinstance(clave, str) and clave else None


def main() -> int:
    if not SNAPSHOT.exists():
        print(f"ERROR: no existe el snapshot {SNAPSHOT}", file=sys.stderr)
        return 1

    datos = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    especies = datos.get("especies_amenazadas") or []
    if not especies:
        print("No hay especies_amenazadas en el snapshot; nada que resolver.")
        return 0

    print(f"Resolviendo clave COL XR de {len(especies)} especies...")
    resueltas = 0
    sin_match: list[str] = []
    for esp in especies:
        nombre = esp.get("nombre_cientifico")
        if not isinstance(nombre, str) or not nombre.strip():
            esp["gbif_portal_key"] = None
            sin_match.append(f"(sin nombre, rank {esp.get('rank')})")
            continue
        clave = resolver_clave_col(nombre.strip())
        esp["gbif_portal_key"] = clave
        if clave:
            resueltas += 1
            print(f"  ok  {nombre} -> {clave}")
        else:
            sin_match.append(nombre)
            print(f"  --  {nombre}: sin coincidencia (gbif_portal_key=null)")
        time.sleep(0.1)  # cortesía con la API pública

    SNAPSHOT.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nResueltas {resueltas}/{len(especies)}. Snapshot actualizado.")
    if sin_match:
        print(f"Sin coincidencia ({len(sin_match)}): {', '.join(sin_match)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
