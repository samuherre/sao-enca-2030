# ADR-001 — Stack tecnológico inicial

- **Estado:** Aceptada
- **Fecha:** 2026-10-01
- **Ámbito:** Decisiones tecnológicas base del proyecto SAO ENCA 2030
- **Relación:** Supera la conclusión de ADR-000 sobre "stack completamente
  pendiente". Registra formalmente el stack definido en `tech.md` (§3–§10, §21,
  §22, §26, §39).

---

## Contexto

Tras la inicialización neutral del repositorio (ADR-000), el documento de
Steering técnico `tech.md` fue actualizado para definir y validar un stack
tecnológico inicial. Este ADR registra formalmente esas decisiones ya adoptadas,
conforme a `tech.md` §35 (toda decisión arquitectónica relevante debe
documentarse como ADR).

El proyecto debe poder ejecutarse localmente (`product.md` §9, `tech.md` §26) y
cubre dos grandes planos: el núcleo de estrategia ENCA (entidades confirmadas) y
un componente bibliométrico que permanece dependiente de datos aún no provistos.

---

## Problema

Se necesita un stack coherente que:

- Sirva tanto al backend/API como al procesamiento de datos/bibliometría.
- Represente de forma consistente relaciones estructuradas del dominio
  (Eje → Meta → Objetivo → Indicador → Actividad, y regiones/progreso).
- Permita ejecución local y evolución futura sin sobreingeniería (`tech.md` §33, §36).
- No comprometa decisiones que todavía dependen del dataset bibliométrico.

---

## Opciones consideradas (resumen)

El Steering fija las decisiones; a modo de registro, las alternativas típicas
que el stack elegido descarta por ahora:

- **Lenguaje:** Python vs. alternativas (Node/TS full-stack, JVM). Se elige
  Python por su ajuste a procesamiento de datos, análisis y automatización, y
  por unificar backend + bibliometría en un mismo ecosistema (`tech.md` §3).
- **Backend:** FastAPI vs. otros frameworks Python (Django, Flask). FastAPI por
  su integración con Pydantic y validación tipada (`tech.md` §4, §5).
- **Base de datos:** PostgreSQL vs. SQLite / almacenes documentales. PostgreSQL
  por las relaciones estructuradas del dominio (`tech.md` §8).
- **Acceso a datos:** SQLAlchemy + Alembic vs. SQL manual / otros ORM
  (`tech.md` §9, §10).
- **Frontend:** React + TypeScript vs. otros frameworks de UI (`tech.md` §6).

La evaluación detallada de cada alternativa no se amplía aquí porque la decisión
ya está tomada en el Steering; este ADR la documenta sin inventar criterios
adicionales.

---

## Decisión

Se adopta el siguiente stack tecnológico inicial:

| Área                    | Decisión                                             |
| ----------------------- | ---------------------------------------------------- |
| Lenguaje principal      | Python 3.12+                                         |
| Backend / API           | FastAPI                                              |
| Validación              | Pydantic                                             |
| Acceso a datos / ORM    | SQLAlchemy                                            |
| Migraciones             | Alembic                                              |
| Base de datos           | PostgreSQL                                            |
| Frontend                | React + TypeScript                                   |
| Aceleración de UI       | Lovable (no es fuente de verdad de arquitectura)     |
| Procesamiento / biblio. | Python (pandas inicial; Polars solo si el volumen lo justifica) |
| Testing backend         | pytest                                               |
| Control de versiones    | Git                                                  |
| Ejecución inicial       | Local                                                |

Fuente: `tech.md` §3–§11, §21, §22, §39.

---

## Justificación

- **Un solo ecosistema (Python)** para backend y bibliometría reduce la
  fragmentación y aprovecha el instrumental científico/de datos (`tech.md` §3).
- **FastAPI + Pydantic** permiten contratos de API tipados y validación de
  entradas/salidas, alineado con la separación de schemas (`tech.md` §5).
- **PostgreSQL + SQLAlchemy + Alembic** representan y versionan de forma
  consistente las relaciones estructuradas del dominio confirmado (`tech.md` §8).
- **React + TypeScript** cubren la interfaz y el dashboard; **Lovable** acelera
  el prototipado sin convertirse en autoridad arquitectónica (`tech.md` §6, §7).
- **Ejecución local** desde el inicio, coherente con la restricción del producto
  (`product.md` §9, `tech.md` §26).
- Se evita sobreingeniería: sin microservicios, colas, streaming ni lakehouse sin
  evidencia de necesidad (`tech.md` §33).

---

## Consecuencias

### Positivas

- El equipo puede empezar a implementar el núcleo de estrategia ENCA con un
  stack definido y coherente.
- Las decisiones quedan trazables mediante este ADR.
- La estructura de `structure.md` se concreta sobre tecnologías conocidas.

### Negativas / limitaciones

- Introduce dependencias que deben gestionarse (versiones, licencias, seguridad)
  según `tech.md` y buenas prácticas.
- PostgreSQL requiere disponibilidad local del motor (p. ej. instalación o,
  opcionalmente, Docker — Docker sigue `PENDING_VALIDATION`, `tech.md` §27).
- Aún NO existe código: este ADR fija el stack, no implementa funcionalidad.

---

## Decisiones que permanecen pendientes (PENDING_VALIDATION)

Este ADR NO decide, y deben resolverse por separado (con sus propios ADR cuando
corresponda):

- **Bibliometría:** metodología/algoritmo/modelo de clasificación, dataset
  definitivo, cardinalidad Artículo ↔ OFC, deduplicación, métricas, evaluación,
  volumen real (`tech.md` §13, §14, §15, §24, §25).
- **Infraestructura:** uso de Docker, estrategia de despliegue, distribución de
  datasets, estrategia de actualización anual (`tech.md` §27, §34).
- **Producto:** alcance del MVP, indicadores/metas prioritarias, granularidad
  del progreso regional, modelo definitivo de actores, autenticación y roles
  (`tech.md` §30, §34).
- **Testing de frontend:** librería/framework concreto (`tech.md` §22).
- **Procesamiento de datos:** elección entre pandas y Polars según volumen real
  (`tech.md` §11).

Ningún requisito de dominio se inventa en este ADR: las decisiones bibliométricas
dependen de datos que SAO aún no ha proporcionado.
