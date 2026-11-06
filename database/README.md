# database/

Elementos relacionados con la persistencia (`structure.md` §16).

## Estado

Motor DEFINIDO (ver `tech.md` §8, §9, §10, §39 y
`docs/decisions/ADR-001-stack-tecnologico.md`):

- Base de datos: **PostgreSQL**
- ORM / acceso a datos: **SQLAlchemy**
- Migraciones versionadas: **Alembic**

Esta carpeta documenta el propósito de la persistencia pero todavía NO contiene
migraciones reales, seeds ni esquemas físicos: la base de datos física no se
inicializa en esta fase (eso corresponde a una Spec posterior). El modelo
conceptual que la guiará está en `docs/data/conceptual-data-model.md`.

## Subcarpetas (conceptuales)

- `migrations/` — cambios versionados del esquema gestionados con Alembic
  (vacío hasta crear el modelo físico en una Spec).
- `seeds/` — datos iniciales mínimos. NO usar seeds para datasets reales grandes
  (`structure.md` §16). Los datos de prueba deben marcarse como `DEMO_DATA`.
- `schemas/` — documentación/definición del modelo de datos.

## Referencia

El modelo conceptual (sin tecnología) está en `docs/data/conceptual-data-model.md`.
