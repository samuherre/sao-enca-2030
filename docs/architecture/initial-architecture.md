# Arquitectura Inicial — SAO ENCA 2030

Estado del documento: **inicial**
Fase del proyecto: **estructura + stack definido, sin código**

Este documento describe la arquitectura **conceptual** derivada de los documentos
de Steering (`product.md`, `tech.md`, `structure.md`, `data-and-domain.md`) y del
inventario (`docs/data/data-inventory.md`), e incorpora el **stack tecnológico ya
definido** (`tech.md` §3–§10, §39; `docs/decisions/ADR-001-stack-tecnologico.md`).

> Regla aplicada: no se inventan requisitos ni decisiones de dominio. El stack ya
> está decidido (ver ADR-001); lo que sigue abierto (bibliometría, infraestructura,
> alcance) se mantiene como `PENDING_VALIDATION` (`tech.md` §2, `product.md` §22).

---

## 1. Separación entre arquitectura conceptual y decisiones tecnológicas

Este documento distingue dos planos que NO deben mezclarse:

- **Arquitectura conceptual** — responsabilidades, separación de componentes y
  flujo de datos. Se deriva del Steering y es relativamente estable.
- **Decisiones tecnológicas** — lenguaje, frameworks, motor de base de datos.
  El stack base ya está **DEFINIDO** (`tech.md` §39, ADR-001). Las decisiones
  tecnológicas que siguen abiertas son las bibliométricas y de infraestructura
  (`tech.md` §13, §14, §24, §25, §27, §30, §34).

La arquitectura conceptual y el stack base están definidos. Lo que falta es el
método bibliométrico (dependiente del dataset) y el detalle de infraestructura.

---

## 2. Arquitectura conceptual (derivada del Steering)

### 2.1 Separación de componentes (tech.md §4, structure.md §2)

    Frontend
        ↓
    API / Application Layer
        ↓
    Business Logic (Domain / Services)
        ↓
    Data Access Layer
        ↓
    Database

### 2.2 Dirección conceptual de dependencias (structure.md §29)

    Frontend → API/Application → Domain/Services → Repositories → Database

Y de forma independiente, el pipeline de datos:

    Raw Data
        ↓
    Bibliometric Pipeline
        ↓
    Processing / Classification
        ↓
    Database / Processed Data
        ↓
    API
        ↓
    Frontend

Regla clave (`structure.md` §29–§30): **el frontend no depende directamente del
pipeline interno**; consulta resultados ya almacenados. El pipeline
bibliométrico debe poder ejecutarse sin abrir la interfaz gráfica.

### 2.3 Componentes conceptuales

| Componente        | Responsabilidad (conceptual)                              | Stack / Estado                         |
| ----------------- | --------------------------------------------------------- | -------------------------------------- |
| Frontend          | Presentación, navegación, dashboard, filtros              | React + TypeScript (Lovable acel.) / sin código |
| API / Application | Contratos, validación, orquestación                       | FastAPI + Pydantic / sin código        |
| Domain / Services | Reglas de negocio ENCA independientes del framework       | Python / conceptual                    |
| Data Access       | Acceso a persistencia                                     | SQLAlchemy / sin código                |
| Database          | Persistencia                                              | PostgreSQL (Alembic) / sin esquema físico |
| Bibliometrics     | Pipeline bibliométrico desacoplado                        | Python / DESACOPLADO · método y dataset PENDING |

### 2.4 Pipeline de datos conceptual (tech.md §7, data-and-domain.md §28)

    Datos originales (RAW)
          ↓ Ingesta
          ↓ Validación
          ↓ Limpieza
          ↓ Normalización
          ↓ Procesamiento
          ↓ Clasificación        <-- PENDING_VALIDATION (metodología no definida)
          ↓ Validación / revisión humana
          ↓ Persistencia
          ↓ Visualización

Capas de datos (`structure.md` §17, `data-and-domain.md` §28):

    RAW → INTERIM → PROCESSED → APPLICATION

Los datos RAW son inmutables.

---

## 3. Principios arquitectónicos aplicados (tech.md §3)

- Separación de responsabilidades, modularidad, mantenibilidad.
- Reproducibilidad y trazabilidad.
- Testabilidad.
- Simplicidad; evitar sobreingeniería temprana (`tech.md` §36).
- Facilidad de ejecución local (`tech.md` §2).

### Restricción principal: ejecución local (tech.md §2)

La solución debe poder ejecutarse localmente, sin depender obligatoriamente de
infraestructura cloud. No se asume arquitectura cloud. Cualquier servicio
externo debe justificarse y evaluar su compatibilidad con la ejecución local.

---

## 4. Desacoplamiento del componente bibliométrico

El componente bibliométrico se mantiene **desacoplado e independiente** de la
interfaz (`structure.md` §7, §30). Esto permite incorporar posteriormente el
dataset real de artículos (`data-inventory.md` DATA-012) sin reescribir el
sistema.

El lenguaje del componente ya está definido (**Python**, `tech.md` §11), pero el
método sigue **sin implementar** y `PENDING_VALIDATION`. No se asume:

- Metodología/algoritmo/modelo de clasificación (reglas, ML, embeddings, LLM,
  híbrido) — `tech.md` §13.
- Relación artículo ↔ OFC y su cardinalidad (uno o varios OFC) — `tech.md` §14;
  `data-and-domain.md` §12, §20.
- Confianza/umbrales, deduplicación y métricas — `tech.md` §15, §24.

El contrato de datos del artículo debe adaptarse a la estructura real del
dataset cuando se reciba (`data-and-domain.md` §18).

---

## 5. Estado de las decisiones tecnológicas

### 5.1 Decisiones ya cerradas (ADR-001, `tech.md` §39)

Lenguaje principal (Python 3.12+), backend (FastAPI), validación (Pydantic),
ORM (SQLAlchemy), migraciones (Alembic), base de datos (PostgreSQL), frontend
(React + TypeScript; Lovable como acelerador), testing backend (pytest), control
de versiones (Git), ejecución inicial local.

### 5.2 Decisiones que siguen PENDING_VALIDATION (`tech.md` §34)

Se listan para trazabilidad:

1. Formato definitivo de los datasets.
2. Estrategia de procesamiento de grandes volúmenes (si el volumen lo exige).
3. Algoritmo o modelo de clasificación bibliométrica.
4. Relación/cardinalidad Artículo ↔ OFC.
5. Estrategia de deduplicación.
6. Métricas y dimensiones del análisis bibliométrico.
7. Estrategia de actualización anual / versionamiento.
8. Uso de Docker, despliegue y distribución local.
9. Autenticación, autorización y roles (si se requieren).
10. Herramientas de visualización concretas.
11. Librería de testing del frontend.
12. pandas vs. Polars según volumen real.

Criterio de selección cuando llegue el momento: `tech.md` §35 (requisitos del
producto, ejecución local, volumen, rendimiento, mantenibilidad, etc. — no la
tecnología más moderna por sí misma).

---

## 6. Regla de evolución (tech.md §36, structure.md §32)

Primero construir una solución mínima que demuestre:

    Datos → Procesamiento → Clasificación → Persistencia → Consulta

y agregar visualización, automatización y optimización según necesidades
reales. No crear carpetas o capas que no aporten beneficio real todavía.

---

## 7. Qué falta para avanzar

- El stack ya permite escribir código: la primera Spec debería cubrir el **núcleo
  de estrategia ENCA** (entidades confirmadas), no la bibliometría.
- Recibir el dataset bibliométrico y sus definiciones (`data-inventory.md`
  DATA-012, DATA-013; prioridad P0) antes de implementar el componente biblio.
- Definir alcance del MVP e indicadores prioritarios (`data-inventory.md` P1).

Cada decisión relevante que se tome debe registrarse como un ADR en
`docs/decisions/`.
