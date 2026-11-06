# backend/

Lógica de aplicación y servicios de acceso a datos.

## Estado

Stack DEFINIDO (ver `tech.md` §3–§10, §39 y `docs/decisions/ADR-001-stack-tecnologico.md`):

- Lenguaje: **Python 3.12+**
- Framework API: **FastAPI**
- Validación: **Pydantic**
- Acceso a datos / ORM: **SQLAlchemy**
- Migraciones: **Alembic**
- Testing backend: **pytest**

Esta carpeta está reservada como esqueleto conceptual según `structure.md` §6.
Todavía NO contiene código funcional: en esta fase solo se ha definido el stack,
no se han creado endpoints ni modelos (eso corresponde a una Spec posterior).

## Responsabilidades (conceptuales, según structure.md §6)

- API.
- Validación.
- Reglas de negocio.
- Servicios.
- Acceso a datos.
- Gestión de entidades.
- Orquestación de procesos.

## Pendiente antes de implementar

- Definir contratos de API concretos con SAO (dimensiones del dashboard, filtros).
- Definir requisitos de autenticación y roles (`tech.md` §30) — `PENDING_VALIDATION`.
- La implementación debe hacerse mediante una Spec; empezar por el núcleo de
  estrategia ENCA (entidades confirmadas), no por bibliometría (bloqueada por el
  dataset P0).
