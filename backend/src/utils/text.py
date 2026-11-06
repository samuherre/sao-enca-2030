"""Normalización de texto para la validación de campos obligatorios.

Tarea 6.3 (tasks.md): implementa una utilidad **pura** que recorta los espacios
en blanco al inicio y al final de un valor de texto y determina si un campo
obligatorio queda vacío. Según la regla de validación común de la Spec
(`design.md`, "Contratos Pydantic"; requirements.md Req 1.2, 2.3, 3.3, 4.3,
5.3), un campo obligatorio es **inválido** cuando es nulo (``None``), vacío
(``""``) o está compuesto únicamente por espacios en blanco (p. ej. ``"   "``);
y es **válido** cuando, tras recortar los espacios, queda al menos un carácter
(p. ej. ``" x "`` → ``"x"``).

Esta función es independiente de framework y de ORM (tech.md §28, structure.md
§28): no importa Pydantic, FastAPI ni SQLAlchemy; solo usa la biblioteca
estándar de Python. Las capas superiores (schemas Pydantic en la tarea 10, o
servicios/dominio) pueden reutilizarla para aplicar la regla de forma
consistente.

Nota sobre "espacios en blanco": se usa ``str.strip()`` sin argumentos, que
elimina todo el espacio en blanco Unicode al inicio y al final (espacios,
tabuladores, saltos de línea, etc.), de modo que una cadena compuesta solo por
cualquier combinación de espacios en blanco se considera vacía.
"""

from __future__ import annotations


def normalizar_texto(valor: str | None) -> str | None:
    """Recorta los espacios de un texto, preservando ``None``.

    Aplica ``str.strip()`` cuando ``valor`` es una cadena; si ``valor`` es
    ``None`` lo devuelve tal cual (``None``). No convierte ``None`` en cadena
    vacía ni viceversa: solo normaliza los espacios de los textos existentes.

    :param valor: Texto a normalizar, o ``None``.
    :return: El texto sin espacios al inicio ni al final, o ``None`` si la
        entrada era ``None``.

    Ejemplos:
        >>> normalizar_texto(" x ")
        'x'
        >>> normalizar_texto("   ")
        ''
        >>> normalizar_texto(None) is None
        True
    """

    if valor is None:
        return None
    return valor.strip()


def es_texto_vacio(valor: str | None) -> bool:
    """Indica si un valor es inválido como campo obligatorio.

    Un valor se considera **vacío** (y, por tanto, inválido para un campo
    obligatorio) cuando es ``None``, la cadena vacía ``""`` o una cadena
    compuesta únicamente por espacios en blanco (``"   "``). Devuelve ``False``
    cuando, tras recortar los espacios, queda al menos un carácter.

    :param valor: Texto a evaluar, o ``None``.
    :return: ``True`` si el valor es nulo, vacío o solo espacios; ``False`` en
        caso contrario.

    Ejemplos:
        >>> es_texto_vacio(None)
        True
        >>> es_texto_vacio("")
        True
        >>> es_texto_vacio("   ")
        True
        >>> es_texto_vacio(" x ")
        False
    """

    normalizado = normalizar_texto(valor)
    return normalizado is None or normalizado == ""


def normalizar_texto_requerido(valor: str | None) -> str | None:
    """Normaliza un campo obligatorio y devuelve ``None`` si queda vacío.

    Función de conveniencia que combina :func:`normalizar_texto` y
    :func:`es_texto_vacio`: recorta los espacios y devuelve el texto resultante
    solo si es válido (al menos un carácter). Si el valor es nulo, vacío o solo
    espacios, devuelve ``None`` para que la capa que la invoque trate el campo
    como ausente/ inválido.

    :param valor: Texto del campo obligatorio, o ``None``.
    :return: El texto recortado si es válido; ``None`` si el campo queda vacío.

    Ejemplos:
        >>> normalizar_texto_requerido(" x ")
        'x'
        >>> normalizar_texto_requerido("   ") is None
        True
        >>> normalizar_texto_requerido(None) is None
        True
    """

    if es_texto_vacio(valor):
        return None
    # es_texto_vacio garantiza que, llegados aquí, el valor no es None.
    return normalizar_texto(valor)
