# scripts/

Scripts ejecutables para tareas operativas (`structure.md` §18).

## Estado

Stack definido: **Python** (`tech.md` §3, §11, ADR-001); los scripts operativos
se escribirán en Python. Las subcarpetas están vacías: no hay scripts todavía
porque aún no hay código ni pipeline que operar (se añadirán vía Specs). Las
fuentes/dataset bibliométrico siguen `PENDING_VALIDATION`.

## Subcarpetas (conceptuales, según structure.md §18)

- `setup/` — inicialización del entorno.
- `data/` — carga de datos.
- `database/` — operaciones de base de datos.
- `processing/` — ejecución de pipelines.
- `maintenance/` — mantenimiento.

## Regla

Los scripts deben ser pequeños y de responsabilidad específica. No duplicar
lógica de negocio: deben invocar servicios o funciones existentes.
