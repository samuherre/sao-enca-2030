"""Tests de ejemplo / edge cases del Pipeline_Scholar (spec multi-source-bibliometria, tarea 3.6).

A diferencia de las tareas 3.2–3.5 (property-based con hypothesis), esta tarea
cubre con pruebas por EJEMPLO los caminos de borde descritos en la tarea 3.1 del
pipeline ``bibliometrics/pipelines/process_google_scholar.py``:

    1. Carpeta de entrada AUSENTE  → ``main`` finaliza con ÉXITO sin registros
       (mensaje informativo), sin escribir nada.                  (Req 1.4)
    2. Carpeta de entrada VACÍA     → ÉXITO sin registros.          (Req 1.4)
    3. Carpeta con SOLO ``.txt``    → ÉXITO sin registros (no se descubren
       ``.json`` ni ``.csv``).                                     (Req 1.4)
    4. Carpeta con un Export_PoP VÁLIDO (JSON y CSV) → el pipeline escribe
       JSON+CSV en el ``OUTPUT_DIR`` (redirigido a un temporal) y el resumen
       refleja la completitud por campo.                     (Req 5.1, 5.2)

Enfoque (Testing Strategy del design y steering Componente B §4):
    - Todos los datos son SINTÉTICOS (``DEMO_DATA``); nunca se usan los datos
      reales de SAO ni se presentan como reales.
    - Las carpetas de entrada se crean en ``tmp_path`` (sistema de archivos
      temporal), SIEMPRE FUERA de ``data/raw`` (que es inmutable).
    - El atributo de módulo ``OUTPUT_DIR`` se monkeypatchea a un directorio
      temporal para que NADA se escriba en ``data/processed`` real; se restaura
      al terminar cada prueba.
    - Se ejercita la API de función del pipeline (``main`` / ``process_folder``),
      sin UI (Req 5.3).
"""

from __future__ import annotations

import csv
import importlib
import json
import sys
from pathlib import Path

# Permite importar el pipeline desde bibliometrics/ (mismo patrón que el resto
# de pruebas unitarias del Componente B).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BIBLIO = _REPO_ROOT / "bibliometrics"
if str(_BIBLIO) not in sys.path:
    sys.path.insert(0, str(_BIBLIO))

import pytest  # noqa: E402

# Se importa el MÓDULO (no solo las funciones) para poder monkeypatchear su
# atributo OUTPUT_DIR y redirigir la escritura a un directorio temporal.
process_google_scholar = importlib.import_module(
    "pipelines.process_google_scholar"
)


# --- Datos sintéticos (DEMO_DATA) --------------------------------------------
# Un Export_PoP mínimo válido: título, autores, año en rango y una revista. El
# conector mapea PoP 'source' → journal y fija source="Google Scholar".
_DEMO_RECORD_COMPLETO = {
    "title": "Conservación de aves en los Andes (DEMO_DATA)",
    "authors": "Pérez, J.; Gómez, A.",
    "year": "2021",
    "doi": "10.1234/demo.0001",
    "source": "Revista DEMO de Ornitología",
    "abstract": "Resumen sintético de prueba.",
    "keywords": "aves; conservación",
}
# Un segundo registro válido pero con menos campos (sin abstract ni keywords):
# sirve para comprobar que la completitud por campo NO es siempre 100%.
_DEMO_RECORD_PARCIAL = {
    "title": "Aviturismo en humedales (DEMO_DATA)",
    "authors": "Ríos, M.",
    "year": "2022",
    "source": "Boletín DEMO",
}


def _patch_output_dir(monkeypatch: pytest.MonkeyPatch, output_dir: Path) -> None:
    """Redirige OUTPUT_DIR del pipeline a un temporal (nada toca processed real)."""
    monkeypatch.setattr(process_google_scholar, "OUTPUT_DIR", output_dir)


# --- Caso 1: carpeta ausente -------------------------------------------------

def test_main_carpeta_ausente_exito_sin_registros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Carpeta de entrada inexistente → ÉXITO sin registros y sin escribir salidas.

    Validates: Requirements 1.4
    """
    ausente = tmp_path / "no_existe"  # NO se crea: debe estar ausente.
    output_dir = tmp_path / "processed_out"
    _patch_output_dir(monkeypatch, output_dir)

    # Apuntar la entrada por CLI a la carpeta ausente; main no debe lanzar.
    monkeypatch.setattr(sys, "argv", ["prog", "--input", str(ausente)])
    process_google_scholar.main()  # no exception == salida con éxito

    out = capsys.readouterr().out
    assert "no existe" in out or "no es accesible" in out
    assert "sin registros" in out
    # No se escribió ningún artefacto de salida.
    assert not output_dir.exists()


# --- Caso 2: carpeta vacía ---------------------------------------------------

def test_main_carpeta_vacia_exito_sin_registros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Carpeta de entrada vacía → ÉXITO sin registros y sin escribir salidas.

    Validates: Requirements 1.4
    """
    vacia = tmp_path / "raw_vacia"
    vacia.mkdir()
    output_dir = tmp_path / "processed_out"
    _patch_output_dir(monkeypatch, output_dir)

    monkeypatch.setattr(sys, "argv", ["prog", "--input", str(vacia)])
    process_google_scholar.main()

    out = capsys.readouterr().out
    assert "no contiene archivos .json ni .csv" in out
    assert "sin registros" in out
    assert not output_dir.exists()


# --- Caso 3: solo archivos .txt ---------------------------------------------

def test_main_solo_txt_exito_sin_registros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Carpeta con solo ``.txt`` → ÉXITO sin registros (no hay .json ni .csv).

    Validates: Requirements 1.4
    """
    solo_txt = tmp_path / "raw_solo_txt"
    solo_txt.mkdir()
    (solo_txt / "notas.txt").write_text("contenido irrelevante", encoding="utf-8")
    (solo_txt / "LEEME.TXT").write_text("otro txt", encoding="utf-8")
    output_dir = tmp_path / "processed_out"
    _patch_output_dir(monkeypatch, output_dir)

    monkeypatch.setattr(sys, "argv", ["prog", "--input", str(solo_txt)])
    process_google_scholar.main()

    out = capsys.readouterr().out
    assert "no contiene archivos .json ni .csv" in out
    assert "sin registros" in out
    assert not output_dir.exists()


def test_process_folder_solo_txt_no_descubre_registros(tmp_path: Path) -> None:
    """``process_folder`` sobre una carpeta de solo ``.txt`` no produce registros.

    Comprueba directamente la ruta de descubrimiento (case-insensitive) del
    pipeline: los ``.txt`` no se consideran Export_PoP.

    Validates: Requirements 1.4
    """
    solo_txt = tmp_path / "raw_solo_txt"
    solo_txt.mkdir()
    (solo_txt / "a.txt").write_text("x", encoding="utf-8")

    records, leidos, procesados, descartados = (
        process_google_scholar.process_folder(solo_txt)
    )
    assert records == []
    assert (leidos, procesados, descartados) == (0, 0, 0)


# --- Caso 4: Export_PoP válido → escribe JSON+CSV + resumen de completitud ----

def _escribir_export_json(path: Path, registros: list[dict]) -> None:
    """Escribe un Export_PoP JSON sintético (lista de objetos)."""
    path.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")


def _escribir_export_csv(path: Path, registros: list[dict]) -> None:
    """Escribe un Export_PoP CSV sintético con cabecera = unión de claves."""
    campos: list[str] = []
    for reg in registros:
        for k in reg:
            if k not in campos:
                campos.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        for reg in registros:
            writer.writerow(reg)


@pytest.mark.parametrize("formato", ["json", "csv"])
def test_main_export_valido_escribe_json_csv_y_resumen(
    formato: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Export_PoP válido → el pipeline escribe JSON+CSV y el resumen de completitud.

    Se puebla la entrada con dos registros sintéticos (uno completo y uno
    parcial), se redirige ``OUTPUT_DIR`` a un temporal y se ejecuta ``main``.
    Luego se verifica que:
      - existen los archivos de salida ``.json`` y ``.csv`` en el OUTPUT_DIR;
      - el JSON de salida contiene exactamente los 2 registros producidos, con
        ``source == "Google Scholar"``;
      - el CSV tiene la cabecera del contrato y 2 filas de datos;
      - el resumen por consola refleja la completitud por campo (2/2 con título
        y autores; 1/2 con abstract y keywords — no siempre 100%).

    Validates: Requirements 5.1, 5.2
    """
    registros = [dict(_DEMO_RECORD_COMPLETO), dict(_DEMO_RECORD_PARCIAL)]

    raw_dir = tmp_path / "raw_input"
    raw_dir.mkdir()
    if formato == "json":
        _escribir_export_json(raw_dir / "export.json", registros)
    else:
        _escribir_export_csv(raw_dir / "export.csv", registros)

    output_dir = tmp_path / "processed_out"
    _patch_output_dir(monkeypatch, output_dir)

    monkeypatch.setattr(sys, "argv", ["prog", "--input", str(raw_dir)])
    process_google_scholar.main()

    out = capsys.readouterr().out

    # --- Se escribieron JSON + CSV en el OUTPUT_DIR temporal -----------------
    assert output_dir.exists(), "El pipeline debió crear el directorio de salida."
    json_files = list(output_dir.glob("google_scholar_dataset_*.json"))
    csv_files = list(output_dir.glob("google_scholar_dataset_*.csv"))
    assert len(json_files) == 1, f"Se esperaba 1 JSON de salida, hay {len(json_files)}."
    assert len(csv_files) == 1, f"Se esperaba 1 CSV de salida, hay {len(csv_files)}."

    # --- El JSON de salida contiene los 2 registros producidos ---------------
    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 2
    assert all(r["source"] == "Google Scholar" for r in data)
    titulos = {r["title"] for r in data}
    assert titulos == {
        _DEMO_RECORD_COMPLETO["title"],
        _DEMO_RECORD_PARCIAL["title"],
    }

    # --- El CSV de salida tiene cabecera del contrato V1 y 2 filas -----------
    with csv_files[0].open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        filas = list(reader)
        assert reader.fieldnames is not None
        assert "article_id" in reader.fieldnames
        assert "source" in reader.fieldnames
    assert len(filas) == 2
    assert all(f["source"] == "Google Scholar" for f in filas)

    # --- El resumen por consola refleja la completitud por campo (Req 5.2) ---
    assert "RESUMEN DE INGESTA" in out
    assert "RESUMEN DE EXTRACCION" in out
    # 2 registros en total; título y autores presentes en ambos.
    assert "Con titulo          : 2/2 (100%)" in out
    assert "Con autores         : 2/2 (100%)" in out
    # abstract y keywords solo en el registro completo → 1/2 (50%).
    assert "Con abstract        : 1/2 (50%)" in out
    assert "Con keywords        : 1/2 (50%)" in out
