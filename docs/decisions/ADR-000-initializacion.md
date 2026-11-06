# ADR-000 — Inicialización técnica neutral del proyecto

- **Estado:** Aceptada (histórica). La parte relativa al stack tecnológico fue
  **superada por ADR-001** (ver `docs/decisions/ADR-001-stack-tecnologico.md`).
- **Fecha:** 2026-10-01
- **Ámbito:** Inicialización del repositorio SAO ENCA 2030
- **Decisión tomada por:** Equipo de desarrollo, confirmada explícitamente por
  el responsable del proyecto.

> **Nota de vigencia:** Este ADR documenta la **fase de inicialización neutral**
> y conserva su valor histórico. Posteriormente se definió y validó un stack
> tecnológico inicial, por lo que el stack **ya NO está completamente
> pendiente** (ver sección "Evolución posterior" y ADR-001). Este ADR-000 NO
> debe utilizarse como autoridad por encima del `tech.md` vigente ni para
> reintroducir el estado "stack completamente PENDING_VALIDATION".

---

## Contexto

El proyecto SAO ENCA 2030 se encuentra en fase inicial de descubrimiento
(`product.md` §23). Al iniciar, el repositorio solo contenía los documentos de
Steering (`.kiro/steering/`) y el inventario de datos
(`docs/data/data-inventory.md`).

El Steering técnico (`tech.md` §34) mantiene explícitamente como decisiones
**pendientes** prácticamente todo el stack tecnológico: lenguaje principal,
framework de frontend, framework de backend, motor de base de datos, ORM,
arquitectura exacta, formato de datasets, estrategia de procesamiento de grandes
volúmenes, algoritmo de clasificación, estrategia de ejecución local del modelo,
actualización anual, deduplicación, autenticación, visualización, respaldo y
empaquetado.

Además, el Steering prohíbe inventar decisiones no validadas (`tech.md` §2,
`product.md` §22, `data-and-domain.md` §33) y recomienda evitar sobreingeniería
temprana (`tech.md` §36, `structure.md` §32).

Existe también una tensión documentada: `structure.md` describe carpetas
(`frontend/`, `backend/`, `bibliometrics/`, etc.) que conceptualmente presuponen
un stack, mientras `tech.md` §34 mantiene ese stack sin definir. El propio
`structure.md` (§2, §32) resuelve la tensión indicando que las carpetas se usan
"únicamente cuando exista una necesidad real" y que la estructura "debe crecer
junto con el proyecto".

---

## Decisión

Se adopta una **inicialización técnica NEUTRAL**:

1. Se crea la **estructura de carpetas de referencia** de `structure.md`
   usando `README.md` y `.gitkeep` para documentar el propósito de cada
   directorio.
2. **No se elige ni implementa** ningún lenguaje, framework, motor de base de
   datos, ORM ni arquitectura tecnológica concreta.
3. **No se crea código funcional** de frontend, backend, API, base de datos
   física ni componente bibliométrico.
4. El **componente bibliométrico queda desacoplado y vacío**, listo para
   incorporar el dataset real cuando SAO lo provea.
5. El **modelo de datos** se documenta solo a nivel **conceptual** y únicamente
   para las entidades **confirmadas** en `data-and-domain.md` (reglas D-001 a
   D-010).
6. Todo elemento no confirmado se marca como `PENDING_VALIDATION`.

Se crean en esta fase: `README.md`, `.gitignore`, `.env.example`,
`docs/architecture/initial-architecture.md`, este ADR y
`docs/data/conceptual-data-model.md`. **No** se crea `LICENSE` porque la
licencia aún no ha sido definida por SAO.

---

## Justificación

- Elegir un stack ahora violaría el principio de no invención, dado que
  `tech.md` §34 lo mantiene como `PENDING_VALIDATION`.
- Una inicialización neutral deja el proyecto listo para comenzar sin
  comprometer decisiones que requieren validación con SAO y evaluación de
  requisitos reales (`tech.md` §35).
- Respeta la restricción de ejecución local y la regla de evolución de
  arquitectura (`tech.md` §2, §36).
- Mantiene el componente bibliométrico desacoplado, como exige `structure.md`
  §7 y §30, permitiendo incorporar el dataset real sin reescritura.

---

## Alternativas consideradas

- **Elegir un stack por defecto (p. ej. un lenguaje + un motor de BD).**
  Rechazada: contradice `tech.md` §34 y el principio de no invención.
- **Crear código de aplicación mínimo funcional.** Rechazada: requiere elegir
  stack; prematuro y fuera del alcance de esta fase.
- **No crear ninguna estructura hasta validar el stack.** Rechazada: el equipo
  puede avanzar en estructura y documentación conceptual sin comprometer
  decisiones técnicas, lo que aporta valor sin violar el Steering.

---

## Consecuencias

### Positivas

- El repositorio queda organizado, documentado y alineado con `structure.md`.
- No se compromete ninguna decisión técnica no validada.
- El componente bibliométrico queda preparado para el dataset real.

### Negativas / limitaciones (en el momento de la inicialización)

- En el momento de esta decisión, las carpetas de código estaban vacías (solo
  documentación/placeholder) y no era posible ejecutar la aplicación por no
  haber stack definido.

> Estas limitaciones se refieren al estado inicial. Ver "Evolución posterior".

---

## Evolución posterior (stack definido)

Después de esta inicialización neutral, `tech.md` fue actualizado para definir y
validar un **stack tecnológico inicial**. En consecuencia, el stack **ya NO está
completamente pendiente**.

Stack adoptado (registrado formalmente en **ADR-001**):

- Lenguaje principal: Python 3.12+ (backend y bibliometría).
- Backend: FastAPI; validación con Pydantic.
- Acceso a datos: SQLAlchemy; migraciones: Alembic.
- Base de datos: PostgreSQL.
- Frontend: React + TypeScript (Lovable como acelerador de UI, no fuente de verdad).
- Testing backend: pytest.
- Control de versiones: Git.
- Ejecución inicial: local.

Este ADR-000 conserva su valor **histórico** (justificación de iniciar de forma
neutral) pero su conclusión de "stack completamente pendiente" quedó **superada
por ADR-001** y por el `tech.md` vigente.

---

## Decisiones que permanecen PENDING_VALIDATION

Siguen pendientes, principalmente, las decisiones bibliométricas y de
infraestructura (`tech.md` §34):

- Bibliometría: clasificador, modelo de IA/ML, dataset definitivo, relación
  Artículo ↔ OFC, deduplicación, métricas, volumen real, evaluación.
- Infraestructura: Docker, estrategia de despliegue, distribución de datasets,
  estrategia definitiva de actualización anual.
- Producto: alcance del MVP, indicadores/metas prioritarias, granularidad del
  progreso regional, modelo definitivo de actores, autenticación y roles.
- Testing específico del frontend (`tech.md` §22).

Bloqueantes de dominio (P0) que deben resolverse con SAO antes del componente
bibliométrico: dataset de artículos, definición de categorías, resultado
esperado del clasificador y relación artículo ↔ OFC
(`data-inventory.md` §30, `data-and-domain.md` §36).
