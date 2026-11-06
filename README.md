# SAO ENCA 2030 — Estrategia de Conservación de Aves en Antioquia

Herramienta de apoyo para el seguimiento, organización, análisis, clasificación
y visualización de información relacionada con la Estrategia Nacional para la
Conservación de las Aves (ENCA 2030), con énfasis en las líneas de trabajo
definidas por la Sociedad Antioqueña de Ornitología (SAO) para Antioquia.

Proyecto desarrollado en el marco de una Inmersión de Talento EAFIT con SAO.

> La fuente de verdad del proyecto son los documentos de Steering en
> `.kiro/steering/` (`product.md`, `tech.md`, `structure.md`,
> `data-and-domain.md`) y el inventario `docs/data/data-inventory.md`.

---

## Estado del proyecto

Fase: **inicialización técnica (descubrimiento)**.

Este repositorio contiene actualmente el **esqueleto estructural** del proyecto
y un **stack tecnológico inicial ya definido**. El esqueleto se creó de forma
neutral (ADR-000) y, posteriormente, se definió y validó el stack (ADR-001).
Todavía NO se ha escrito código de aplicación.

Stack definido: **Python 3.12+ / FastAPI / Pydantic / SQLAlchemy / Alembic /
PostgreSQL** (backend y datos), **React + TypeScript** (frontend, con Lovable
como acelerador de UI), **pytest** (testing backend), **Git**, ejecución
**local**.

Ver `docs/decisions/ADR-000-initializacion.md` (inicialización neutral,
histórica) y `docs/decisions/ADR-001-stack-tecnologico.md` (stack adoptado).

### Qué existe hoy

- Estructura de carpetas de referencia (`structure.md`) con documentación de
  propósito por carpeta.
- Arquitectura conceptual: `docs/architecture/initial-architecture.md`.
- Modelo de datos conceptual (solo entidades confirmadas):
  `docs/data/conceptual-data-model.md`.
- Registro de decisiones: `docs/decisions/`.

### Qué NO existe todavía

- Código funcional de frontend, backend o API (se implementará mediante Specs).
- Base de datos física, migraciones o seeds reales.
- Componente bibliométrico (ingesta real, preprocesamiento, clasificación).

### Qué sigue `PENDING_VALIDATION`

- Dataset bibliométrico de artículos y definiciones de clasificación
  (`data-inventory.md` DATA-012/013, P0).
- Metodología/modelo de clasificación y cardinalidad Artículo ↔ OFC
  (`tech.md` §13, §14).
- Deduplicación, métricas bibliométricas, volumen real (`tech.md` §15, §24, §25).
- Testing de frontend (`tech.md` §22), Docker/despliegue (`tech.md` §27, §34),
  autenticación y roles (`tech.md` §30), actualización anual (`tech.md` §34).
- Alcance del MVP, indicadores/metas prioritarias, modelo definitivo de actores.

---

## Principios no negociables

- **No inventar** datos, campos, categorías bibliométricas, indicadores ni
  reglas de dominio no confirmadas (`product.md` §22, `data-and-domain.md` §33).
- **Trazabilidad** del origen de los datos sobre conveniencia.
- **Reproducibilidad** de los procesos.
- **Datos reales vs ficticios**: los datos de demostración deben marcarse como
  `DEMO_DATA` y nunca presentarse como datos reales de SAO.
- **Ejecución local**: la solución debe poder ejecutarse localmente
  (`tech.md` §2); no se asume infraestructura cloud obligatoria.

---

## Estructura del repositorio

Ver `structure.md` para el detalle. Resumen:

    .kiro/          Steering y specs (fuente de verdad)
    frontend/       Interfaz de usuario (pendiente de stack)
    backend/        Lógica de aplicación y API (pendiente de stack)
    bibliometrics/  Pipeline bibliométrico, desacoplado (pendiente de dataset)
    database/       Persistencia (pendiente de motor)
    data/           raw / interim / processed / external / samples / exports
    scripts/        Scripts operativos (pendiente de stack)
    tests/          Pruebas (pendiente de stack)
    docs/           Documentación (dominio, arquitectura, datos, decisiones)
    config/         Configuración no sensible

---

## Cómo ejecutar el proyecto localmente

Todavía no es posible ejecutar la aplicación porque **aún no se ha escrito
código** (esta fase es solo estructura + stack). El stack ya está definido, pero
los comandos concretos se añadirán cuando exista implementación (vía Spec).

El flujo de ejecución local objetivo (conceptual, `structure.md` §31) con el
stack definido será:

    1. Clonar el repositorio
    2. Instalar dependencias            (Python: entorno virtual + deps; frontend: gestor de paquetes React)
    3. Configurar el entorno            (copiar .env.example -> .env)
    4. Inicializar la base de datos     (PostgreSQL + migraciones Alembic)
    5. Cargar los datos requeridos      (fuentes/dataset: parcialmente PENDING_VALIDATION)
    6. Ejecutar el backend              (FastAPI)
    7. Ejecutar el frontend             (React + TypeScript)
    8. Usar la aplicación

Los comandos exactos se documentarán aquí y en `docs/development/` cuando se
implemente el proyecto. El dataset bibliométrico sigue `PENDING_VALIDATION`.

---

## Configuración sensible

Copiar `.env.example` a `.env` y completar los valores reales localmente.
Nunca versionar `.env` ni credenciales (`tech.md` §21, §24).

---

## Documentación relacionada

- `.kiro/steering/product.md` — qué se construye y para quién.
- `.kiro/steering/tech.md` — principios técnicos y decisiones pendientes.
- `.kiro/steering/structure.md` — organización del código.
- `.kiro/steering/data-and-domain.md` — significado del dominio.
- `docs/data/data-inventory.md` — fuentes de información disponibles.
