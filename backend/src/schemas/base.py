"""Base y utilidades comunes para los contratos Pydantic de la API.

Tarea 10.1 (tasks.md): define una **base de schemas** que fija la configuración
compartida por todos los contratos Pydantic de ``backend/src/schemas/`` y un
**validador reutilizable** para campos obligatorios de texto.

Decisiones técnicas aplicadas (``design.md``: "Contratos Pydantic", "Columnas
futuras no implementadas"; requirements.md Req 4.7, 5.8, 9.4, 1.2, 2.3, 3.3,
4.3, 5.3):

- **Campos extra prohibidos** (``extra="forbid"``): enviar un atributo no
  declarado en el contrato —incluidos los atributos ``PENDING_VALIDATION`` de
  Indicador/Actividad— no se acepta silenciosamente, sino que produce un error
  de validación que la capa de rutas traduce a **422** (Req 9.4). Esto evita
  que el cliente escriba información no soportada en esta versión.
- **Regla de texto obligatorio**: un campo obligatorio es válido solo si **no
  es nulo y no queda vacío tras recortar espacios** (``strip``). Una cadena
  nula, vacía o compuesta solo por espacios se rechaza (→ 422). La regla se
  implementa reutilizando :func:`backend.src.utils.text.es_texto_vacio` y
  :func:`backend.src.utils.text.normalizar_texto`, de modo que coincida con la
  utilidad pura de dominio (tarea 6.3) y se aplique de forma consistente.

Esta base es específica de la capa de contrato (Pydantic/FastAPI); por eso vive
en ``schemas/`` y no en ``utils/`` ni en ``domain/``, que permanecen libres de
dependencias de framework (tech.md §28, structure.md §28).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict

from backend.src.utils.text import es_texto_vacio, normalizar_texto


class SchemaBase(BaseModel):
    """Base común de todos los contratos Pydantic de la API.

    Fija ``extra="forbid"`` para que cualquier campo no declarado en un contrato
    concreto haga fallar la validación (traducida a 422 en la capa de rutas),
    en lugar de ignorarse en silencio. Todos los schemas Create/Response de la
    Spec deben heredar de esta clase para compartir esta política.
    """

    model_config = ConfigDict(extra="forbid")


def _validar_texto_requerido(valor: str) -> str:
    """Normaliza y valida un campo de texto obligatorio.

    Recorta los espacios del valor y exige que quede al menos un carácter. Si el
    valor es nulo, vacío o solo espacios, lanza ``ValueError`` para que Pydantic
    lo reporte como error de validación (→ 422). En caso válido devuelve el texto
    ya normalizado (sin espacios al inicio ni al final), de modo que el valor
    persistido y expuesto sea el recortado.

    :param valor: Texto recibido para el campo obligatorio.
    :return: El texto recortado cuando es válido.
    :raises ValueError: Si el valor es nulo, vacío o solo espacios.
    """

    if es_texto_vacio(valor):
        raise ValueError("El campo es obligatorio: no puede ser nulo, vacío ni solo espacios.")
    # es_texto_vacio garantiza que, llegados aquí, normalizar_texto no es None.
    return normalizar_texto(valor)  # type: ignore[return-value]


# Tipo reutilizable para campos de texto obligatorios en los contratos Create.
# Uso: ``nombre: TextoRequerido`` / ``descripcion: TextoRequerido``.
# El valor se normaliza (strip) y se rechaza si queda vacío.
TextoRequerido = Annotated[str, AfterValidator(_validar_texto_requerido)]
