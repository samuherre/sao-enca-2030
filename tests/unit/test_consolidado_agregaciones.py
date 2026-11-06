"""Property test del Servicio_Consolidado (spec multi-source-bibliometria, tarea 6.3).

Property 11 del design.md — "Agregaciones bien formadas":

    Para todo resumen consolidado, se cumple: ``total_articulos >= 0``; la suma
    de conteos de ``por_anio`` (sobre registros con año) no excede
    ``total_articulos``; cada porcentaje de ``completitud`` está en ``[0, 100]``;
    y ``pendientes_revision`` y ``posibles_duplicados`` están en
    ``[0, total_articulos]``.

    **Validates: Requirements 6.2**

Enfoque (Testing Strategy del design): se generan datasets de fuente SINTÉTICOS
en carpetas temporales bajo un ``data/processed/`` de prueba. Para aislar el
servicio del repo real, se monkeypatch-ea el ``_PROCESSED_DIR`` del módulo a un
directorio temporal por ejemplo, que se limpia al terminar cada ejemplo. Los
registros tienen ``publication_year`` variado (algunos ``None``), ``volume``,
``inclusion_status`` (algunos "PENDIENTE_REVISIÓN"), ``is_duplicate`` y los
campos de completitud (title/authors/abstract/keywords/doi) presentes o no.

``completitud`` se expone como ``CompletitudCampo(campo, con_dato, total)``; el
porcentaje es ``con_dato/total*100``. Verificar ``0 <= con_dato <= total`` y
``total == total_articulos`` garantiza que el porcentaje derivado cae en
``[0, 100]`` (y evita dividir por cero cuando no hay registros).

Los datos generados por hypothesis son SINTÉTICOS (datos de prueba, no reales).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from backend.src.services import bibliometria_service as svc

# Nombres de fuente sintéticos para repartir registros en >= 1 carpetas.
_FUENTES = ["Fuente Alfa", "Fuente Beta", "Fuente Gamma"]

# Valores posibles de inclusion_status (uno marca pendiente de revisión).
_INCLUSION = ["INCLUIDO", "PENDIENTE_REVISIÓN", None]


@st.composite
def registro_sintetico(draw: st.DrawFn) -> dict:
    """Genera un registro bibliométrico sintético conforme (parcial) al contrato.

    Varía los campos relevantes para las invariantes de Property 11: año (a
    veces None), volumen (a veces None), estado de inclusión, marca de duplicado
    y presencia/ausencia de los campos de completitud.
    """
    record: dict = {"source": draw(st.sampled_from(_FUENTES))}

    # publication_year: a veces presente (int), a veces None.
    year = draw(st.one_of(st.none(), st.integers(min_value=1900, max_value=2100)))
    record["publication_year"] = year

    # volume: a veces presente, a veces None, numérico o texto.
    volume = draw(
        st.one_of(
            st.none(),
            st.integers(min_value=1, max_value=99).map(str),
            st.text(min_size=1, max_size=5),
        )
    )
    record["volume"] = volume

    record["inclusion_status"] = draw(st.sampled_from(_INCLUSION))
    record["is_duplicate"] = draw(st.booleans())

    # Campos de completitud: presentes (texto no vacío) o ausentes/None.
    for campo in ("title", "authors", "abstract", "keywords", "doi"):
        presente = draw(st.booleans())
        if presente:
            record[campo] = draw(st.text(min_size=1, max_size=10))
        else:
            # Ausente o vacío: el servicio usa `r.get(campo)` (falsy => sin dato).
            record[campo] = draw(st.sampled_from([None, ""]))

    return record


@st.composite
def datasets_por_fuente(draw: st.DrawFn) -> dict[str, list[dict]]:
    """Genera un mapa fuente_carpeta -> lista de registros sintéticos.

    Puede producir cero fuentes (conjunto vacío, resumen vacío coherente) o
    varias, cada una con cero o más registros. El nombre de la carpeta es
    independiente del campo ``source`` del registro (el servicio agrupa por
    ``source``), lo que no afecta las invariantes agregadas.
    """
    n_fuentes = draw(st.integers(min_value=0, max_value=3))
    resultado: dict[str, list[dict]] = {}
    for i in range(n_fuentes):
        carpeta = f"fuente_{i}"
        registros = draw(st.lists(registro_sintetico(), min_size=0, max_size=8))
        resultado[carpeta] = registros
    return resultado


# Feature: multi-source-bibliometria, Property 11: Agregaciones bien formadas
@settings(max_examples=150, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(datos=datasets_por_fuente())
def test_agregaciones_bien_formadas(datos: dict[str, list[dict]]) -> None:
    """Todas las invariantes de rango del resumen consolidado se cumplen.

    Validates: Requirements 6.2

    Nota: no se usan fixtures function-scoped (``tmp_path``/``monkeypatch``)
    porque hypothesis no las reinicia entre ejemplos de ``@given``. En su lugar
    se crea un directorio temporal propio por ejemplo y se restaura el
    ``_PROCESSED_DIR`` del módulo en un ``finally`` (limpieza por ejemplo).
    """
    # --- Montar un data/processed/ temporal con los datasets sintéticos. -----
    processed_dir = Path(tempfile.mkdtemp(prefix="sao_processed_"))
    original_processed_dir = svc._PROCESSED_DIR
    try:
        for carpeta, registros in datos.items():
            carpeta_dir = processed_dir / carpeta
            carpeta_dir.mkdir(parents=True, exist_ok=True)
            # Nombre con fecha YYYY-MM-DD para que _ultimo_json /
            # _fecha_desde_nombre funcionen como en producción (DEMO_DATA,
            # datos sintéticos de prueba).
            archivo = carpeta_dir / f"{carpeta}_dataset_2024-01-01.json"
            archivo.write_text(
                json.dumps(registros, ensure_ascii=False), encoding="utf-8"
            )

        # Aislar el servicio: apuntar su _PROCESSED_DIR al directorio temporal.
        svc._PROCESSED_DIR = processed_dir

        resumen = svc.BibliometriaService().resumen_consolidado()
    finally:
        # Restaurar estado del módulo y limpiar el directorio temporal.
        svc._PROCESSED_DIR = original_processed_dir
        shutil.rmtree(processed_dir, ignore_errors=True)

    total = resumen.total_articulos

    # 1) total_articulos >= 0
    assert total >= 0, f"total_articulos negativo: {total}"

    # 2) suma de conteos de por_anio (registros con año) no excede total.
    suma_anios = sum(c.conteo for c in resumen.por_anio)
    assert suma_anios <= total, (
        f"suma de por_anio ({suma_anios}) excede total_articulos ({total})"
    )
    # Cada conteo por año es un entero positivo (distribución bien formada).
    for c in resumen.por_anio:
        assert c.conteo >= 1, f"conteo por año no positivo: {c.conteo}"

    # 3) cada completitud tiene 0 <= con_dato <= total == total_articulos,
    #    de modo que el porcentaje con_dato/total*100 cae en [0, 100].
    for comp in resumen.completitud:
        assert comp.total == total, (
            f"completitud.total ({comp.total}) != total_articulos ({total}) "
            f"para campo {comp.campo}"
        )
        assert 0 <= comp.con_dato <= comp.total, (
            f"con_dato fuera de [0, total] para {comp.campo}: "
            f"con_dato={comp.con_dato}, total={comp.total}"
        )
        if comp.total > 0:
            porcentaje = comp.con_dato / comp.total * 100
            assert 0 <= porcentaje <= 100, (
                f"porcentaje de completitud fuera de [0,100] para "
                f"{comp.campo}: {porcentaje}"
            )

    # 4) pendientes_revision y posibles_duplicados en [0, total_articulos].
    assert 0 <= resumen.pendientes_revision <= total, (
        f"pendientes_revision fuera de [0, {total}]: {resumen.pendientes_revision}"
    )
    assert 0 <= resumen.posibles_duplicados <= total, (
        f"posibles_duplicados fuera de [0, {total}]: {resumen.posibles_duplicados}"
    )
