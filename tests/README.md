# tests/

Pruebas del proyecto (`structure.md` §19, `tech.md` §22).

## Estado

Testing de **backend** DEFINIDO: **pytest** (`tech.md` §22, ADR-001).
Testing de **frontend**: `PENDING_VALIDATION` — la librería concreta se
seleccionará al configurar React (`tech.md` §22).

Las subcarpetas están vacías: aún no hay código que probar; las pruebas se
añadirán junto con la implementación en Specs posteriores.

## Subcarpetas (conceptuales, según structure.md §19)

- `unit/` — componentes individuales (validadores, transformaciones, cálculos).
- `integration/` — interacción entre componentes (p. ej. pipeline + persistencia).
- `e2e/` — flujos completos.
- `fixtures/` — datos pequeños y controlados para pruebas. Nunca datasets reales grandes.

## Reglas

- Las pruebas no deben depender exclusivamente de datos reales de SAO (`tech.md` §22).
- El pipeline debe poder probarse con datasets pequeños antes de ejecutarse sobre
  datasets grandes.
- Los datos de prueba deben marcarse como `DEMO_DATA`.
