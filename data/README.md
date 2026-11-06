# data/

Carpeta crítica del proyecto. Separa los datos según su estado
(`structure.md` §17, `data-and-domain.md` §28, `data-inventory.md` §27).

## Principio fundamental

Los datos originales (`raw/`) NO deben modificarse de forma destructiva.
Los procesos automáticos no deben escribir sobre `raw/`.

Los datasets reales y potencialmente sensibles NO deben incluirse en Git sin
autorización explícita de SAO (`structure.md` §17.1, §23). Por defecto, el
contenido de datos está excluido en `.gitignore`.

## Capas (según structure.md §17)

- `raw/` — datos originales recibidos de SAO o fuentes externas. Inmutables.
- `interim/` — resultados intermedios/temporales regenerables. No es fuente oficial.
- `processed/` — datasets normalizados, deduplicados o clasificados. Reproducibles.
- `external/` — información de fuentes externas (debe registrar procedencia).
- `samples/` — datasets pequeños para desarrollo/pruebas. Marcar como `DEMO_DATA`.
- `exports/` — resultados preparados para compartir (CSV, Excel, JSON, reportes).

## Flujo conceptual (data-and-domain.md §28)

    RAW → INTERIM → PROCESSED → APPLICATION

## Datos de prueba

Cuando se necesiten datos para probar sin dataset real, usar fixtures/datos
sintéticos CLARAMENTE identificados como `DEMO_DATA`. Nunca presentar datos
sintéticos como datos reales de SAO (`product.md` §18, `data-and-domain.md` §37).

## Nota sobre el material ya inventariado

El ZIP `Avances ENCA a 2026...` descrito en `data-inventory.md` contiene fuentes
reales de SAO. Su ubicación local y manejo deben documentarse y NO se versiona
en Git sin autorización. El dataset bibliométrico (DATA-012) sigue PENDIENTE.
