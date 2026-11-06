# Implementation Plan

Plan de Implementación — Seguimiento de la Estructura ENCA (enca-strategy-tracking)

## Overview

Este plan convierte el diseño aprobado (`design.md`) en una secuencia de tareas de
código incrementales y verificables. El objetivo es implementar el **núcleo funcional**
de la jerarquía confirmada:

```text
Eje → Meta → Objetivo SMART → Indicador → Actividad
```

con solo tres operaciones por entidad: **Crear**, **Consultar** (individual y por
colección) y **Navegar** la jerarquía. El stack es el fijado por el Steering y ADR-001:
backend en Python 3.12+ con FastAPI, Pydantic, SQLAlchemy, Alembic y PostgreSQL; frontend
en React + TypeScript; pruebas de backend con pytest.

Alcance estricto: **no** se implementa update/delete, bibliometría, clasificación, NLP,
ML, LLM, embeddings, Artículo↔OFC, Regiones, Progreso regional, Actores, autenticación,
roles ni dashboard analítico. Los atributos `PENDING_VALIDATION` de Indicador y Actividad
**no** se implementan ni se exponen. El diseño **no** define una sección de "Correctness
Properties", por lo que las pruebas son unitarias y de integración (sin property-based
testing). El testing de frontend queda `PENDING_VALIDATION` (no se elige framework).

Notas sobre decisiones ya tomadas en `design.md` que las tareas deben respetar:
- `id` = entero autoincremental (PK técnica generada por PostgreSQL).
- Navegación hija→padre vía campo `*_id` en cada `Response`; el Eje raíz no incluye padre.
- Endpoint de árbol anidado completo: `GET /ejes/{id}/arbol`.
- Referencia a padre inexistente → **404**; validación de forma (Pydantic) → **422**.
- Schemas Pydantic con **campos extra prohibidos** (enviar atributos no reconocidos → 422).
- Marcador DEMO_DATA = prefijo textual legible `"[DEMO_DATA] "`.
- Timeout de 30 s en el frontend vía `AbortController`.

---

## Tasks

- [x] 1. Preparación de dependencias y configuración mínima del backend
  - Crear `backend/requirements.txt` (o `pyproject.toml`) con las dependencias confirmadas: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `psycopg[binary]` (driver PostgreSQL) y, para pruebas, `pytest` y `httpx`.
  - Documentar en `.env.example` las variables de entorno necesarias (`DATABASE_URL`, `ENVIRONMENT`, `LOG_LEVEL`) sin secretos reales; no hardcodear credenciales (tech.md §19, §20).
  - Resultado verificable: `pip install` de las dependencias se resuelve sin errores y `.env.example` lista las variables requeridas.
  - _Requisitos: 8.1, 10.1_

- [x] 2. Configuración base del backend (app FastAPI y settings)
  - [x] 2.1 Crear la carga de configuración por variables de entorno
    - Implementar `backend/src/core/config.py` con un objeto de settings (Pydantic Settings) que lea `DATABASE_URL`, `ENVIRONMENT` y `LOG_LEVEL` del entorno; sin valores secretos por defecto.
    - Resultado verificable: importar settings expone `DATABASE_URL` tomada del entorno; falla de forma controlada si falta.
    - _Requisitos: 8.1_
  - [x] 2.2 Crear la aplicación FastAPI y el logging base
    - Implementar `backend/src/main.py` que instancia la app FastAPI y configura logging básico (sin exponer secretos ni trazas al cliente, tech.md §31, §32).
    - Resultado verificable: la app arranca localmente y expone el esquema OpenAPI vacío (sin routers aún).
    - _Requisitos: 7.9_

- [x] 3. Configuración de PostgreSQL (engine y sesión)
  - Implementar `backend/src/core/database.py` con el `engine` de SQLAlchemy creado a partir de `DATABASE_URL`, una factoría de sesiones (`SessionLocal`) y una dependencia `get_db()` para FastAPI que abre y cierra sesión por petición.
  - No inventar credenciales; la conexión usa exclusivamente la variable de entorno (tech.md §19).
  - Resultado verificable: `get_db()` entrega una sesión utilizable y la cierra al terminar; una conexión de prueba a PostgreSQL se establece con `DATABASE_URL` válida.
  - _Requisitos: 8.1_

- [x] 4. Configuración de SQLAlchemy (Base declarativa)
  - Implementar `backend/src/models/base.py` con la `Base` declarativa de SQLAlchemy compartida por todos los modelos ORM.
  - Resultado verificable: `Base.metadata` existe y puede registrar tablas; los modelos podrán heredar de esta `Base`.
  - _Requisitos: 8.1_

- [x] 5. Configuración de Alembic
  - Inicializar Alembic apuntando el directorio de versiones a `database/migrations/` (structure.md §16) y configurar `env.py` para usar `DATABASE_URL` del entorno y `Base.metadata` como `target_metadata`.
  - No crear SQL manual; el esquema se gestiona solo con migraciones versionadas (tech.md §10).
  - Resultado verificable: `alembic current` y `alembic revision --autogenerate` se ejecutan sin error de configuración (sin generar aún la migración de tablas).
  - _Requisitos: 8.1_

- [x] 6. Entidades de dominio y excepciones (domain/)
  - [x] 6.1 Definir las cinco entidades de dominio puras
    - Implementar en `backend/src/domain/` las entidades `Eje`, `Meta`, `Objetivo`, `Indicador`, `Actividad` como objetos de dominio independientes de framework y ORM (tech.md §28, structure.md §28), con solo sus atributos confirmados y la referencia al padre inmediato (excepto Eje). Sin atributos PENDING_VALIDATION.
    - Resultado verificable: las entidades se instancian sin importar SQLAlchemy/Pydantic/FastAPI.
    - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 4.7, 5.8_
  - [x] 6.2 Definir las excepciones de dominio
    - Implementar en `backend/src/domain/exceptions.py` (o módulo equivalente) `NotFoundError`, `InvalidParentReferenceError`, `MissingParentReferenceError` y, si aplica, `ValidationError` de dominio, según `design.md` (Error Handling).
    - Resultado verificable: las excepciones existen y son importables desde la capa de servicios.
    - _Requisitos: 1.5, 2.2, 2.7, 3.2, 3.7, 4.2, 4.6, 5.2, 5.7, 6.5, 8.2, 8.3_
  - [x] 6.3 Implementar utilidad de normalización de texto
    - Implementar en `backend/src/utils/` una función que recorte espacios y determine si un campo obligatorio queda vacío (cadena nula, vacía o solo espacios → inválido).
    - Resultado verificable: la función clasifica correctamente `None`, `""`, `"   "` como inválidos y `" x "` como válido ("x").
    - _Requisitos: 1.2, 2.3, 3.3, 4.3, 5.3_

- [x] 7. Modelos de persistencia ORM (models/)
  - [x] 7.1 Implementar `EjeModel`
    - En `backend/src/models/eje.py`: tabla `ejes` con `id` PK autoincremental, `nombre` (NOT NULL), `descripcion` (NULL permitido) y relación 1→N con `metas`.
    - Resultado verificable: el modelo se registra en `Base.metadata`.
    - _Requisitos: 1.1, 8.4_
  - [x] 7.2 Implementar `MetaModel`
    - En `backend/src/models/meta.py`: tabla `metas` con `id` PK, `descripcion` (NOT NULL) y `eje_id` FK → `ejes.id` NOT NULL.
    - Resultado verificable: la FK NOT NULL queda definida en el metadata.
    - _Requisitos: 2.1, 8.1, 8.4_
  - [x] 7.3 Implementar `ObjetivoModel`
    - En `backend/src/models/objetivo.py`: tabla `objetivos` con `id` PK, `descripcion` (NOT NULL) y `meta_id` FK → `metas.id` NOT NULL.
    - Resultado verificable: la FK NOT NULL queda definida en el metadata.
    - _Requisitos: 3.1, 8.1, 8.4_
  - [x] 7.4 Implementar `IndicadorModel`
    - En `backend/src/models/indicador.py`: tabla `indicadores` con `id` PK, `nombre` (NOT NULL), `descripcion` (NOT NULL) y `objetivo_id` FK → `objetivos.id` NOT NULL. Sin columnas PENDING_VALIDATION.
    - Resultado verificable: el modelo no contiene atributos PENDING_VALIDATION.
    - _Requisitos: 4.1, 4.7, 8.1, 8.4, 9.1_
  - [x] 7.5 Implementar `ActividadModel`
    - En `backend/src/models/actividad.py`: tabla `actividades` con `id` PK, `descripcion` (NOT NULL) e `indicador_id` FK → `indicadores.id` NOT NULL. Sin columnas PENDING_VALIDATION.
    - Resultado verificable: el modelo no contiene atributos PENDING_VALIDATION.
    - _Requisitos: 5.1, 5.8, 8.1, 8.4, 9.2_

- [x] 8. Repositories (repositories/)
  - [x] 8.1 Implementar `EjeRepository`
    - En `backend/src/repositories/eje_repository.py`: `crear(eje)`, `obtener_por_id(id)`, `listar_todos()`.
    - Resultado verificable: crea y recupera un Eje; `listar_todos()` devuelve `[]` cuando no hay Ejes.
    - _Requisitos: 1.1, 1.3, 1.4_
  - [x] 8.2 Implementar `MetaRepository`
    - En `backend/src/repositories/meta_repository.py`: `crear(meta)`, `obtener_por_id(id)`, `listar_por_padre(eje_id)`, `padre_existe(eje_id)`.
    - Resultado verificable: lista Metas por Eje (incluye `[]`); `padre_existe` detecta Eje inexistente.
    - _Requisitos: 2.1, 2.4, 2.5, 2.6, 8.1_
  - [x] 8.3 Implementar `ObjetivoRepository`
    - En `backend/src/repositories/objetivo_repository.py`: `crear`, `obtener_por_id`, `listar_por_padre(meta_id)`, `padre_existe(meta_id)`.
    - Resultado verificable: lista Objetivos por Meta (incluye `[]`); detecta Meta inexistente.
    - _Requisitos: 3.1, 3.4, 3.6, 8.1_
  - [x] 8.4 Implementar `IndicadorRepository`
    - En `backend/src/repositories/indicador_repository.py`: `crear`, `obtener_por_id`, `listar_por_padre(objetivo_id)`, `padre_existe(objetivo_id)`.
    - Resultado verificable: lista Indicadores por Objetivo (incluye `[]`); detecta Objetivo inexistente.
    - _Requisitos: 4.1, 4.4, 4.5, 8.1_
  - [x] 8.5 Implementar `ActividadRepository`
    - En `backend/src/repositories/actividad_repository.py`: `crear`, `obtener_por_id`, `listar_por_padre(indicador_id)`, `padre_existe(indicador_id)`.
    - Resultado verificable: lista Actividades por Indicador (incluye `[]`); detecta Indicador inexistente.
    - _Requisitos: 5.1, 5.4, 5.5, 5.6, 8.1_

- [x] 9. Services (services/)
  - [x] 9.1 Implementar `EjeService`
    - En `backend/src/services/eje_service.py`: `crear(datos)`, `obtener(id)` (lanza `NotFoundError` si no existe), `listar()`.
    - Resultado verificable: crear devuelve entidad con id; `obtener` de id inexistente lanza `NotFoundError`.
    - _Requisitos: 1.1, 1.3, 1.4, 1.5_
  - [x] 9.2 Implementar `MetaService`
    - En `backend/src/services/meta_service.py`: antes de crear verifica que el Eje padre existe (lanza `InvalidParentReferenceError` si no); `obtener(id)`, `listar_por_eje(eje_id)` (lanza `NotFoundError` si el Eje no existe).
    - Resultado verificable: crear bajo Eje inexistente lanza `InvalidParentReferenceError`; `obtener` id inexistente lanza `NotFoundError`.
    - _Requisitos: 2.1, 2.2, 2.4, 2.5, 2.6, 2.7, 8.2_
  - [x] 9.3 Implementar `ObjetivoService`
    - En `backend/src/services/objetivo_service.py`: verifica Meta padre antes de crear; `obtener`, `listar_por_meta` (lanza `NotFoundError` si la Meta no existe).
    - Resultado verificable: crear bajo Meta inexistente lanza `InvalidParentReferenceError`.
    - _Requisitos: 3.1, 3.2, 3.4, 3.5, 3.6, 3.7, 8.2_
  - [x] 9.4 Implementar `IndicadorService`
    - En `backend/src/services/indicador_service.py`: verifica Objetivo padre antes de crear; `obtener`, `listar_por_objetivo`.
    - Resultado verificable: crear bajo Objetivo inexistente lanza `InvalidParentReferenceError`.
    - _Requisitos: 4.1, 4.2, 4.4, 4.5, 4.6, 8.2_
  - [x] 9.5 Implementar `ActividadService`
    - En `backend/src/services/actividad_service.py`: verifica Indicador padre antes de crear; `obtener`, `listar_por_indicador`.
    - Resultado verificable: crear bajo Indicador inexistente lanza `InvalidParentReferenceError`.
    - _Requisitos: 5.1, 5.2, 5.4, 5.5, 5.6, 5.7, 8.2_
  - [x] 9.6 Implementar `HierarchyService` (árbol anidado)
    - En `backend/src/services/hierarchy_service.py`: `obtener_arbol(eje_id)` que, si el Eje no existe lanza `NotFoundError`; en caso contrario ensambla el árbol de 5 niveles reutilizando los repositorios, con listas vacías `[]` para nodos sin hijos y sin referencia a padre en el Eje raíz.
    - Resultado verificable: árbol de un Eje con hijos refleja la estructura; nodos sin hijos exponen `[]`; Eje inexistente lanza `NotFoundError`.
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 10. Schemas Pydantic (schemas/)
  - [x] 10.1 Configurar base de schemas con campos extra prohibidos
    - En `backend/src/schemas/` definir una base/config Pydantic que **prohíba campos extra** (enviar atributos no reconocidos, incluidos PENDING_VALIDATION, produce 422) y un validador reutilizable para campos obligatorios de texto (no nulo, no vacío tras `strip`).
    - Resultado verificable: un cuerpo con un campo no declarado es rechazado por el contrato.
    - _Requisitos: 4.7, 5.8, 9.4, 1.2, 2.3, 3.3, 4.3, 5.3_
  - [x] 10.2 Schemas de Eje
    - En `backend/src/schemas/eje.py`: `EjeCreate` (`nombre` obligatorio, `descripcion` opcional) y `EjeResponse` (`id`, `nombre`, `descripcion`, **sin** referencia a padre).
    - Resultado verificable: `EjeResponse` no incluye `*_id` de padre.
    - _Requisitos: 1.1, 6.3_
  - [x] 10.3 Schemas de Meta
    - En `backend/src/schemas/meta.py`: `MetaCreate` (`descripcion` obligatorio; sin `eje_id` en el cuerpo) y `MetaResponse` (`id`, `descripcion`, `eje_id`).
    - Resultado verificable: `MetaResponse` incluye `eje_id`; `MetaCreate` no acepta `eje_id` en el cuerpo.
    - _Requisitos: 2.1, 2.6, 6.2_
  - [x] 10.4 Schemas de Objetivo
    - En `backend/src/schemas/objetivo.py`: `ObjetivoCreate` (`descripcion` obligatorio) y `ObjetivoResponse` (`id`, `descripcion`, `meta_id`).
    - Resultado verificable: contratos conformes al diseño.
    - _Requisitos: 3.1, 3.6, 6.2_
  - [x] 10.5 Schemas de Indicador (sin atributos PENDING_VALIDATION)
    - En `backend/src/schemas/indicador.py`: `IndicadorCreate` (`nombre` y `descripcion` obligatorios) e `IndicadorResponse` (`id`, `nombre`, `descripcion`, `objetivo_id`), sin unidad de medida/valor objetivo/valor actual/fecha/fuente/estado.
    - Resultado verificable: `IndicadorResponse` no expone ningún atributo PENDING_VALIDATION.
    - _Requisitos: 4.1, 4.5, 4.7, 9.1, 6.2_
  - [x] 10.6 Schemas de Actividad (sin atributos PENDING_VALIDATION)
    - En `backend/src/schemas/actividad.py`: `ActividadCreate` (`descripcion` obligatorio) y `ActividadResponse` (`id`, `descripcion`, `indicador_id`), sin responsable/fecha/estado/evidencia/región.
    - Resultado verificable: `ActividadResponse` no expone ningún atributo PENDING_VALIDATION.
    - _Requisitos: 5.1, 5.6, 5.8, 9.2, 6.2_
  - [x] 10.7 Schemas del árbol jerárquico
    - En `backend/src/schemas/arbol.py`: `EjeArbolResponse`, `MetaArbol`, `ObjetivoArbol`, `IndicadorArbol`, `ActividadArbol` con listas de hijos (que pueden ser `[]`) y sin `*_id` de padre en los nodos anidados.
    - Resultado verificable: la estructura anidada representa los cinco niveles.
    - _Requisitos: 6.1, 6.4_

- [x] 11. Endpoints FastAPI (api/) y mapeo de errores a HTTP
  - [x] 11.1 Implementar manejadores de excepciones de dominio → HTTP
    - En `backend/src/api/` (p. ej. `error_handlers.py`) mapear `NotFoundError`→404, `InvalidParentReferenceError`→404, `MissingParentReferenceError`→422 y errores de validación Pydantic→422, con cuerpo JSON uniforme `{ "detail", "error" }` sin trazas (tech.md §32).
    - Resultado verificable: las excepciones producen el código y cuerpo esperados sin exponer trazas.
    - _Requisitos: 1.5, 2.2, 2.7, 3.2, 3.7, 4.2, 4.6, 5.2, 5.7, 6.5, 7.9, 8.2, 8.3_
  - [x] 11.2 Router de Ejes
    - En `backend/src/api/ejes.py`: `POST /ejes`, `GET /ejes`, `GET /ejes/{id}`.
    - Resultado verificable: crear devuelve 201; listar devuelve 200 (posible `[]`); id inexistente devuelve 404.
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 11.3 Router de Metas
    - En `backend/src/api/metas.py`: `POST /ejes/{eje_id}/metas`, `GET /ejes/{eje_id}/metas`, `GET /metas/{id}`.
    - Resultado verificable: crear bajo Eje inexistente → 404; validación → 422; listar devuelve 200 (posible `[]`).
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 8.2, 8.3_
  - [x] 11.4 Router de Objetivos
    - En `backend/src/api/objetivos.py`: `POST /metas/{meta_id}/objetivos`, `GET /metas/{meta_id}/objetivos`, `GET /objetivos/{id}`.
    - Resultado verificable: comportamiento equivalente al router de Metas respecto a 201/200/404/422.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.2, 8.3_
  - [x] 11.5 Router de Indicadores
    - En `backend/src/api/indicadores.py`: `POST /objetivos/{objetivo_id}/indicadores`, `GET /objetivos/{objetivo_id}/indicadores`, `GET /indicadores/{id}`.
    - Resultado verificable: contratos sin atributos PENDING_VALIDATION; códigos 201/200/404/422 correctos.
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 8.2, 8.3_
  - [x] 11.6 Router de Actividades
    - En `backend/src/api/actividades.py`: `POST /indicadores/{indicador_id}/actividades`, `GET /indicadores/{indicador_id}/actividades`, `GET /actividades/{id}`.
    - Resultado verificable: contratos sin atributos PENDING_VALIDATION; códigos 201/200/404/422 correctos.
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 8.2, 8.3_
  - [x] 11.7 Router de jerarquía (árbol)
    - En `backend/src/api/jerarquia.py`: `GET /ejes/{eje_id}/arbol` que devuelve `EjeArbolResponse` (200) o 404 si el Eje no existe.
    - Resultado verificable: árbol de 5 niveles con `[]` en nodos sin hijos; Eje inexistente → 404.
    - _Requisitos: 6.1, 6.4, 6.5_
  - [x] 11.8 Registrar routers y manejadores en la app
    - En `backend/src/main.py`: incluir todos los routers y registrar los manejadores de excepciones.
    - Resultado verificable: el OpenAPI lista todos los endpoints y la app responde a cada ruta.
    - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_

- [x] 12. Migración inicial de Alembic
  - Generar la primera migración versionada en `database/migrations/` que cree las cinco tablas con sus PK autoincrementales, columnas confirmadas y FKs NOT NULL en orden de dependencia (ejes → metas → objetivos → indicadores → actividades). No incluir columnas PENDING_VALIDATION. No crear SQL manual (tech.md §10).
  - Resultado verificable: `alembic upgrade head` crea el esquema completo en una base PostgreSQL limpia y `alembic downgrade` lo revierte.
  - _Requisitos: 8.1, 8.4, 9.1, 9.2_

- [x] 13. Datos de desarrollo DEMO_DATA (seed)
  - Crear un script de seed de desarrollo en `scripts/data/` (o `database/seeds/`) que inserte una jerarquía de ejemplo completa (Eje→Meta→Objetivo→Indicador→Actividad) con el prefijo textual legible `"[DEMO_DATA] "` al inicio de cada nombre/descripción. No usar datos que puedan confundirse con información oficial de SAO.
  - Resultado verificable: tras ejecutar el seed, las entabas contienen entidades cuyos campos de texto comienzan con `[DEMO_DATA]`.
  - _Requisitos: 10.1, 10.2, 10.3_

- [x] 14. Checkpoint — Verificar backend básico
  - Ejecutar `alembic upgrade head` + arranque de la app y una llamada manual mínima; asegurarse de que no haya errores de configuración. Ensure all tests pass, ask the user if questions arise.
  - _Requisitos: 1.1, 6.1, 8.1_

- [x] 15. Pruebas unitarias de servicios y contratos (tests/unit)
  - [x] 15.1* Configurar pytest y fixtures de unidad
    - En `tests/unit/`: configurar `pytest` y fixtures con repositorios en memoria/dobles o sesión aislada, según `structure.md` §19.
    - Resultado verificable: `pytest tests/unit` se ejecuta (aunque sin casos aún).
    - _Requisitos: 1.1_
  - [x] 15.2* Pruebas de creación de cada entidad con datos válidos
    - Verificar creación correcta de Eje, Meta, Objetivo, Indicador y Actividad y asociación hija→padre correcta.
    - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 8.1_
  - [x] 15.3* Pruebas de consulta individual y por colección (incluida colección vacía)
    - Obtener por id existente; listar hijos de un padre; listar todos los Ejes; confirmar `[]` sin error.
    - _Requisitos: 1.3, 1.4, 2.4, 2.5, 2.6, 3.4, 3.6, 4.4, 4.5, 5.4, 5.5, 5.6_
  - [x] 15.4* Pruebas de validación de campos obligatorios (nulo/vacío/solo espacios)
    - Para cada campo obligatorio, un valor nulo/vacío/solo espacios se rechaza (422) y no persiste nada.
    - _Requisitos: 1.2, 2.3, 3.3, 4.3, 5.3_
  - [x] 15.5* Pruebas de rechazo de referencia a padre inexistente
    - Crear hija bajo id de padre inexistente se rechaza (404) y no persiste la hija.
    - _Requisitos: 2.2, 3.2, 4.2, 5.2, 8.2_
  - [x] 15.6* Pruebas de navegación jerárquica (árbol)
    - El árbol refleja la estructura creada; nodos sin hijos exponen `[]`; el Eje raíz no incluye referencia a padre y no produce error.
    - _Requisitos: 6.1, 6.2, 6.3, 6.4_
  - [x] 15.7* Pruebas de omisión de atributos PENDING_VALIDATION en contratos
    - Los `Response` de Indicador y Actividad no contienen atributos PENDING_VALIDATION, y un cuerpo que los incluya es rechazado (422 por campos extra).
    - _Requisitos: 4.7, 5.8, 9.1, 9.2, 9.4_
  - [x] 15.8* Pruebas de respuestas de error HTTP (404 y 422)
    - Consulta por id inexistente → 404 en cada entidad y en el árbol; cuerpos inválidos → 422; sin trazas en la respuesta.
    - _Requisitos: 1.5, 2.7, 3.7, 4.6, 5.7, 6.5, 7.9, 8.3_

- [x] 16. Pruebas de integración con PostgreSQL (tests/integration)
  - [x] 16.1* Configurar fixtures de integración (PostgreSQL de prueba)
    - En `tests/integration/`: fixtures que ejecuten las migraciones Alembic sobre una base de prueba y usen sesión transaccional con rollback para aislamiento (`structure.md` §19).
    - Resultado verificable: `pytest tests/integration` prepara y limpia el esquema entre pruebas.
    - _Requisitos: 8.1_
  - [x] 16.2* Prueba de integridad referencial por FK
    - Confirmar que la FK NOT NULL impide referencias colgantes de entidades hijas a nivel de base de datos.
    - _Requisitos: 8.1, 8.2_
  - [x] 16.3* Prueba de flujo extremo a extremo (crear jerarquía y recuperar árbol)
    - A través de los endpoints: crear Eje→Meta→Objetivo→Indicador→Actividad y recuperar el árbol anidado del Eje.
    - _Requisitos: 6.1, 2.1, 3.1, 4.1, 5.1_
  - [x] 16.4* Prueba del seed DEMO_DATA
    - Tras ejecutar el seed, las entidades sembradas conservan el marcador `[DEMO_DATA]` en sus campos de texto.
    - _Requisitos: 10.1, 10.2, 10.3_

- [x] 17. Checkpoint — Backend completo y probado
  - Ensure all tests pass, ask the user if questions arise.
  - _Requisitos: 1.1, 6.1, 8.1_

- [x] 18. Configuración inicial del frontend React + TypeScript
  - Inicializar el proyecto en `frontend/` (React + TypeScript) con la estructura de `structure.md` §5 (`src/components`, `src/pages`, `src/layouts`, `src/services`, `src/hooks`, `src/types`, `src/utils`). Configurar la URL base de la API vía variable de entorno (`API_URL`), sin rutas absolutas de máquina (structure.md §26).
  - Resultado verificable: `npm install` resuelve dependencias y la app arranca mostrando una página base.
  - _Requisitos: 7.1_

- [x] 19. Tipos y capa de servicios tipada del frontend
  - [x] 19.1 Definir tipos de los contratos de la API
    - En `frontend/src/types/`: tipos `Eje`, `Meta`, `Objetivo`, `Indicador`, `Actividad` y los del árbol, reflejando los `Response` del backend (Indicador/Actividad **sin** atributos PENDING_VALIDATION).
    - Resultado verificable: los tipos no incluyen atributos PENDING_VALIDATION.
    - _Requisitos: 4.7, 5.8_
  - [x] 19.2 Implementar el cliente API con timeout de 30 s
    - En `frontend/src/services/`: cliente tipado que consume los endpoints (crear/consultar por entidad y árbol) usando `AbortController` con límite de **30 segundos**; mapea el campo `error` del backend a información para la UI.
    - Resultado verificable: una petición que supera 30 s se aborta y propaga un error de timeout manejable.
    - _Requisitos: 7.1, 7.3, 7.7, 7.8, 7.9_
  - [x] 19.3 Implementar hooks de carga de datos
    - En `frontend/src/hooks/`: hooks como `useEjes`, `useMetas(ejeId)`, etc., que encapsulan carga y estados (cargando/vacío/error) por nivel.
    - Resultado verificable: cada hook expone estado de carga, datos y error.
    - _Requisitos: 7.1, 7.3, 7.7_

- [x] 20. Componentes reutilizables de estados y DEMO_DATA
  - [x] 20.1 Implementar estados de carga, vacío y error
    - En `frontend/src/components/`: `LoadingIndicator`, `EmptyState`, `ErrorBanner`. `ErrorBanner` muestra mensajes comprensibles sin trazas ni ids internos; incluye el caso de timeout (mensaje que conserva la última vista válida); `EntityDetail` muestra "Sin información" para campos confirmados nulos/vacíos.
    - Resultado verificable: cada estado se renderiza con su mensaje; el error no expone detalles técnicos.
    - _Requisitos: 7.2, 7.4, 7.5, 7.7, 7.8, 7.9_
  - [x] 20.2 Implementar `DemoDataBadge`
    - En `frontend/src/components/`: componente que, al detectar el marcador `[DEMO_DATA]` en un campo, muestra "Datos de demostración — no es información oficial de SAO".
    - Resultado verificable: una entidad con prefijo `[DEMO_DATA]` muestra el badge.
    - _Requisitos: 10.2, 10.3_

- [x] 21. Vistas por nivel con drill-down, regreso y formularios de creación
  - [x] 21.1 `EjesPage` (vista inicial) + crear Eje
    - En `frontend/src/pages/`: lista de Ejes (usa `EntityList`); si la API no devuelve Ejes, muestra mensaje contextual (no lista vacía sin contexto); formulario `CreateEntityForm` para crear Eje.
    - Resultado verificable: al abrir, solicita y lista Ejes; colección vacía muestra mensaje; crear añade un Eje.
    - _Requisitos: 7.1, 7.2, 7.6_
  - [x] 21.2 `MetasPage` (de un Eje) + crear Meta
    - Lista de Metas del Eje con drill-down desde `EjesPage` y regreso al nivel superior; muestra mensaje si no hay Metas; formulario de creación de Meta.
    - Resultado verificable: navegación Eje→Metas y regreso; crear añade una Meta bajo el Eje.
    - _Requisitos: 7.3, 7.4, 7.5, 7.6_
  - [x] 21.3 `ObjetivosPage` (de una Meta) + crear Objetivo
    - Lista de Objetivos de la Meta con drill-down y regreso; mensaje si no hay Objetivos; formulario de creación.
    - Resultado verificable: navegación Meta→Objetivos y regreso; crear añade un Objetivo.
    - _Requisitos: 7.3, 7.4, 7.5, 7.6_
  - [x] 21.4 `IndicadoresPage` (de un Objetivo) + crear Indicador
    - Lista de Indicadores del Objetivo con drill-down y regreso; mensaje si no hay Indicadores; formulario de creación. No muestra atributos PENDING_VALIDATION.
    - Resultado verificable: navegación Objetivo→Indicadores y regreso; crear añade un Indicador; no se muestran atributos PENDING_VALIDATION.
    - _Requisitos: 7.3, 7.4, 7.5, 7.6, 4.7_
  - [x] 21.5 `ActividadesPage` (de un Indicador) + crear Actividad
    - Lista de Actividades del Indicador con drill-down y regreso; mensaje si no hay Actividades; formulario de creación. No muestra atributos PENDING_VALIDATION.
    - Resultado verificable: navegación Indicador→Actividades y regreso; crear añade una Actividad; no se muestran atributos PENDING_VALIDATION.
    - _Requisitos: 7.3, 7.4, 7.5, 7.6, 5.8_

- [x] 22. Integración frontend–backend
  - Conectar las vistas y formularios a la capa de servicios y hooks reales contra el backend; cablear la navegación entre los cinco niveles con regreso; asegurar que los estados de carga/vacío/error (timeout 30 s, "Sin información") y el `DemoDataBadge` se activan con datos reales de la API.
  - Resultado verificable: con el backend y el seed DEMO_DATA en ejecución local, el usuario navega Eje→…→Actividad, crea entidades y ve los estados y el badge correctamente.
  - _Requisitos: 7.1, 7.3, 7.5, 7.6, 7.7, 7.8, 7.9, 10.2_

- [x] 23. Pruebas de frontend (PENDING_VALIDATION)
  - [x] 23.1* Preparar pruebas de las vistas y componentes React
    - El framework/librería de testing de frontend permanece `PENDING_VALIDATION` (tech.md §22). Esta subtarea queda **bloqueada** hasta que SAO/el equipo seleccionen el framework; no elegir uno por suposición. Cuando se decida, cubrir Req 7.x (listas, estados de carga/vacío/error, timeout, "Sin información", DemoDataBadge, drill-down y regreso).
    - Resultado verificable: una vez seleccionado el framework, las pruebas de las vistas se ejecutan localmente.
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

- [x] 24. Validación final contra Requisitos
  - Revisar que cada endpoint y vista implementados satisfacen sus criterios de aceptación referenciados; confirmar que no se implementó funcionalidad fuera de alcance ni atributos PENDING_VALIDATION. Ensure all tests pass, ask the user if questions arise.
  - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 9.2, 10.1_

## Notes

- Las subtareas marcadas con `*` son de pruebas y pueden omitirse para un MVP más rápido; las tareas de implementación nunca se marcan como opcionales.
- La subtarea 23.1 depende de una decisión `PENDING_VALIDATION` (framework de testing de frontend) y **no** debe resolverse eligiendo un framework por suposición.
- Cada tarea referencia sus requisitos para trazabilidad.
- Los checkpoints (14, 17, 24) aseguran validación incremental.
- El diseño no define "Correctness Properties"; por eso se usan solo pruebas unitarias y de integración (sin property-based testing).
- No se incluyen tareas de despliegue, métricas de usuario ni documentación externa (fuera de alcance / no son tareas de código).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1", "2.1", "2.2", "4"] },
    { "id": 1, "tasks": ["3", "5", "6.1", "6.2", "6.3"] },
    { "id": 2, "tasks": ["7.1", "7.2", "7.3", "7.4", "7.5", "10.1"] },
    { "id": 3, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "12"] },
    { "id": 4, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "11.1", "13"] },
    { "id": 5, "tasks": ["11.2", "11.3", "11.4", "11.5", "11.6", "11.7"] },
    { "id": 6, "tasks": ["11.8", "18"] },
    { "id": 7, "tasks": ["15.1", "16.1", "19.1"] },
    { "id": 8, "tasks": ["15.2", "15.3", "15.4", "15.5", "15.6", "15.7", "15.8", "16.2", "16.3", "16.4", "19.2", "19.3"] },
    { "id": 9, "tasks": ["20.1", "20.2"] },
    { "id": 10, "tasks": ["21.1", "21.2", "21.3", "21.4", "21.5"] },
    { "id": 11, "tasks": ["22"] },
    { "id": 12, "tasks": ["23.1"] }
  ]
}
```
