# Piloto de biodiversidad — Visión general (SiB Colombia + GBIF)

> Estado del documento: **diagnóstico preliminar**. Esta línea de trabajo es
> **exploratoria** y **separada** del MVP de seguimiento ENCA. Nada de lo aquí
> descrito constituye un requisito aprobado por SAO.

---

## 1. Contexto

El MVP existente del proyecto SAO cubre el seguimiento de la jerarquía
ENCA 2030: Eje → Meta → Objetivo SMART → Indicador → Actividad. Esa
funcionalidad está implementada y se ejecuta localmente, y **no debe alterarse**
por este piloto.

De forma independiente, se pidió **explorar** una posible funcionalidad de
datos de biodiversidad a partir de dos fuentes públicas:

- **GBIF** (Global Biodiversity Information Facility).
- **SiB Colombia** (Sistema de Información sobre Biodiversidad de Colombia).

## 2. Motivación y alcance (validado por SAO — 2026-10-21)

Objetivo: construir un sitio que **compile y muestre cifras de registros de
aves** de Colombia a partir de fuentes públicas, con énfasis en el **número de
registros** y, cuando sea posible, los **publicadores**. El modelo de referencia
es [Biodiversidad en Cifras — SiB Colombia](https://cifras.biodiversidad.co/colombia),
pero enfocado exclusivamente en **aves**. No se busca otra enciclopedia de aves.

Decisiones confirmadas:

| # | Decisión | Valor validado |
| --- | --- | --- |
| 1 | Alcance taxonómico | **Solo aves** |
| 2 | Qué mostrar | **Conteos de registros** y, si es posible, **publicadores** (estilo "Biodiversidad en Cifras") |
| 3 | Cobertura geográfica | **Nacional (Colombia)** |
| 4 | Frecuencia de actualización | **Mensual, programada** |
| 5 | Plataforma objetivo | **ArcGIS Online** (aloja el sitio de SAO); datos GBIF/SiB son públicos, sin problema de licencia/publicación |
| 6 | Relación con bibliometría | **Ninguna** — es un proyecto distinto al análisis bibliométrico |
| 7 | Licencias de datos | **Sin restricción** para el uso previsto |

Decisión de secuencia: **empezar solo con GBIF**. SiB puede añadirse después
como fuente adicional, pero su indisponibilidad actual **no debe bloquear** el
avance.

## 3. Alcance de esta fase

Lo que se hizo en esta fase:

- Pruebas piloto exploratorias (muestras pequeñas) contra las APIs.
- Inventario de scripts y archivos generados.
- Análisis estático de un repositorio externo de referencia.
- Documentación del diagnóstico.

Lo que **no** se hizo todavía (siguientes fases, ya con alcance validado):

- Conteos agregados de registros de aves a escala nacional (objetivo del sitio).
- Actualización mensual programada.
- Publicación/visualización en ArcGIS Online.
- Incorporación de SiB como segunda fuente.
- Modificaciones al MVP ENCA (permanece intacto; es un proyecto distinto).

## 4. Distinción entre tipos de dato observados

Conviene no confundir estos conceptos, porque las fuentes los tratan distinto:

| Concepto | Qué es | Fuente observada en el piloto |
| --- | --- | --- |
| Ocurrencia | Observación/registro georreferenciado de un organismo en fecha/lugar | GBIF (funcional); SiB (no accesible, ver pilot-status) |
| Especie (taxón) | Ficha taxonómica/descriptiva de una especie | GBIF (enriquecimiento); SiB Catálogo (funcional) |

Mantener **GBIF y SiB como fuentes diferenciadas**, conservando la procedencia
y la fecha de consulta de cada registro.

## 5. Preguntas resueltas y puntos aún por precisar

Las 7 preguntas del alcance fueron **respondidas por SAO** (ver §2). Quedan
puntos **técnicos** menores por precisar durante la implementación:

1. Desglose de los conteos a mostrar: ¿total nacional, por departamento, por
   publicador, por año? (El endpoint de GBIF permite todos; definir el mínimo.)
2. Mecanismo de actualización mensual en el contexto de ArcGIS Online
   (programador propio vs. ArcGIS Notebooks/automatización). `PENDING_VALIDATION`.
3. Formato de entrega a ArcGIS Online (CSV/GeoJSON/Feature Layer).
4. Si se reportará el conteo total "vivo" desde GBIF o un corte mensual
   almacenado (para tener histórico comparable mes a mes).

## 6. Plan acordado (fases)

Secuencia validada: **GBIF primero**, SiB después como fuente adicional opcional.

- **Fase 1 — Cifras GBIF de aves (en curso).** Script de recolección que pide a
  GBIF **conteos agregados** (`limit=0` + facetas), no registros masivos:
  total nacional de aves y ranking de publicadores. Salida a CSV con fuente y
  fecha de corte. Ejecutable localmente, sin tocar el MVP ENCA.
- **Fase 2 — Corte mensual + histórico.** Guardar un corte con fecha cada mes
  para comparar en el tiempo. Definir el programador (ver §5 punto 2).
- **Fase 3 — Publicación en ArcGIS Online.** Entregar el artefacto (CSV/GeoJSON/
  Feature Layer) al sitio de SAO en ArcGIS. No se publica nada hasta validar
  formato y procedimiento.
- **Fase 4 (opcional) — SiB como segunda fuente.** Solo si se confirma un
  servicio de cifras vigente. Mantener GBIF y SiB **separadas** (no sumar sin
  estudiar solapamiento).

## 7. Decisión de arquitectura por resolver (`PENDING_VALIDATION`)

SAO indicó que el desarrollo debe basarse en **ArcGIS Online** (plataforma del
sitio de SAO). El `tech.md` del proyecto define un stack Python/FastAPI/
PostgreSQL + React de ejecución local. Esto es una decisión de arquitectura en
tensión que **no debe resolverse arbitrariamente** (`tech.md` §37.4).

- El **MVP ENCA** permanece en su stack actual, intacto.
- Este sitio de cifras es **un proyecto distinto** (respuesta SAO #6).
- Propuesta de bajo riesgo a validar: **recolección en Python** (reutiliza los
  pilotos) que produce un artefacto de datos, y **ArcGIS Online como capa de
  publicación/visualización** que lo consume. Así ArcGIS es la plataforma del
  sitio sin reescribir la recolección.

Esta decisión debe documentarse como ADR cuando se confirme.

## 8. Documentos relacionados

- `docs/biodiversity/pilot-status.md` — estado verificado de las pruebas.
- `docs/biodiversity/explorer-reference.md` — análisis del repositorio externo.
