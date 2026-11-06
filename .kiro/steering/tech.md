# Technical Architecture — SAO ENCA 2030

## 1. Propósito

Este documento define las decisiones técnicas y arquitectónicas del proyecto
SAO | Estrategia de Conservación de Aves en Antioquia.

Debe utilizarse como referencia obligatoria para el desarrollo de:

* Backend.
* Frontend.
* API.
* Base de datos.
* Procesamiento de datos.
* Análisis bibliométrico.
* Automatización.
* Testing.
* Configuración.
* Despliegue.

Las decisiones aquí documentadas deben respetarse durante la implementación.

Cuando una decisión dependa de información que todavía no ha sido proporcionada
por SAO, debe permanecer explícitamente como `PENDING_VALIDATION`.

No se deben inventar requisitos técnicos ni de dominio.

---

# 2. Principios técnicos

## 2.1 No invención

El sistema debe construirse únicamente sobre:

* Requisitos confirmados.
* Datos reales proporcionados por SAO.
* Decisiones documentadas.
* Convenciones técnicas justificadas.

No asumir:

* Campos inexistentes.
* APIs inexistentes.
* Datasets inexistentes.
* Categorías bibliométricas no confirmadas.
* Relaciones de datos no validadas.

---

## 2.2 Separación de responsabilidades

La solución debe separar claramente:

```text
Frontend
    ↓
API / Backend
    ↓
Domain / Application Logic
    ↓
Data Access
    ↓
Database
```

El procesamiento bibliométrico debe mantenerse desacoplado:

```text
Dataset
   ↓
Bibliometric Pipeline
   ↓
Processed Data
   ↓
Backend / API
   ↓
Frontend
```

---

## 2.3 Datos reales vs datos de prueba

Los datos reales de SAO no deben mezclarse con datos sintéticos.

Cuando sean necesarios datos para desarrollo:

```text
DEMO_DATA
```

debe utilizarse como identificación explícita.

Nunca presentar datos sintéticos como resultados reales.

---

# 3. Lenguaje principal

## Decisión

**Python 3.12+**

Python será el lenguaje principal del proyecto.

## Justificación

Python se adapta especialmente bien a:

* Procesamiento de datos.
* Análisis bibliométrico.
* NLP.
* Machine Learning.
* Automatización.
* APIs.
* Integración con herramientas científicas.

Además, permite utilizar el mismo ecosistema para backend y procesamiento
bibliométrico.

La versión exacta de Python debe mantenerse dentro de una versión estable
soportada durante el desarrollo.

---

# 4. Backend

## Decisión

**FastAPI**

FastAPI será utilizado para desarrollar la API backend.

## Responsabilidades

El backend será responsable de:

* Exponer endpoints.
* Validar datos de entrada.
* Aplicar reglas de negocio.
* Consultar la base de datos.
* Exponer información procesada.
* Gestionar filtros y consultas.
* Integrar procesos de análisis.
* Proporcionar servicios al frontend.

El backend NO debe contener lógica específica de presentación.

---

# 5. Validación de datos de API

## Decisión

Utilizar **Pydantic** mediante el ecosistema de FastAPI.

Los schemas de API deben separar:

```text
Request
Response
Persistence Model
Domain Model
```

cuando la complejidad del dominio lo justifique.

No exponer directamente modelos internos de persistencia como contratos públicos
de la API cuando esto genere acoplamiento innecesario.

---

# 6. Frontend

## Decisión

**React + TypeScript**

El frontend será desarrollado utilizando React y TypeScript.

## Responsabilidades

El frontend será responsable de:

* Interfaz de usuario.
* Dashboard.
* Navegación.
* Formularios.
* Tablas.
* Filtros.
* Visualizaciones.
* Estados de interfaz.
* Consumo de la API.

No debe contener lógica de negocio crítica que también deba ejecutarse en
backend.

---

# 7. Lovable

Lovable puede utilizarse como herramienta de aceleración para:

* Prototipado de interfaz.
* Generación inicial de componentes.
* Diseño visual.
* Dashboard.
* Formularios.
* Layouts.
* Componentes React.

Lovable no será considerado la fuente de verdad de la arquitectura del
sistema.

La arquitectura, contratos de API, modelos de dominio y reglas de negocio
deben mantenerse documentados en el repositorio.

Todo código generado mediante Lovable debe revisarse antes de integrarse.

---

# 8. Base de datos

## Decisión

**PostgreSQL**

PostgreSQL será el motor principal de base de datos.

## Justificación

El dominio contiene relaciones estructuradas entre:

* Ejes.
* Metas.
* Objetivos.
* Indicadores.
* Actividades.
* Regiones.
* Organizaciones.
* Personas.
* Evidencias.
* Fuentes.
* Datasets.

PostgreSQL permite representar estas relaciones de manera consistente y
proporciona una base adecuada para una aplicación que pueda crecer
posteriormente.

---

# 9. ORM

## Decisión

**SQLAlchemy**

SQLAlchemy será utilizado como capa de acceso ORM para PostgreSQL.

Debe evitarse acoplar la lógica de negocio directamente a consultas específicas
cuando una abstracción de dominio sea más apropiada.

Las consultas complejas pueden utilizar SQL explícito cuando exista una
justificación técnica.

---

# 10. Migraciones

## Decisión

**Alembic**

Alembic será utilizado para administrar cambios estructurales de la base de
datos.

Los cambios de esquema deben realizarse mediante migraciones versionadas.

No modificar manualmente el esquema de producción sin registrar el cambio en
una migración.

---

# 11. Procesamiento de datos

Python será utilizado para los procesos de:

* Ingesta.
* Limpieza.
* Transformación.
* Normalización.
* Validación.
* Análisis.
* Exportación.

Las herramientas concretas de procesamiento se seleccionarán según las
características reales de los datasets.

## Estado

El uso de pandas es una opción inicial.

El uso de Polars puede evaluarse si el volumen real de datos justifica su
incorporación.

No introducir herramientas adicionales innecesariamente.

---

# 12. Arquitectura bibliométrica

El componente bibliométrico será independiente del frontend y desacoplado del
backend tanto como sea razonablemente posible.

Arquitectura conceptual:

```text
                    DATASET
                       │
                       ▼
                   INGESTION
                       │
                       ▼
                 PREPROCESSING
                       │
                       ▼
                 DEDUPLICATION
                       │
                       ▼
                  CLASSIFICATION
                       │
                       ▼
                    ANALYSIS
                       │
                       ▼
               PROCESSED DATA
                       │
                       ▼
                    BACKEND
                       │
                       ▼
                   FRONTEND
```

No asumir que todos estos pasos serán necesarios en la versión final.

---

# 13. Clasificación bibliométrica

## Estado

`PENDING_VALIDATION`

Todavía no se ha definido:

* Tipo de clasificador.
* Dataset de entrenamiento.
* Dataset objetivo.
* Variables de entrada.
* Categorías.
* Etiquetas.
* Método de evaluación.
* Métricas.
* Modelo.
* Uso de LLM.
* Uso de embeddings.
* Clasificación supervisada.
* Clasificación basada en reglas.

Estas decisiones deben tomarse después de analizar el dataset real y validar
los requerimientos con SAO.

---

# 14. Relación Artículo — OFC

## Estado

`PENDING_VALIDATION`

No asumir que:

```text
Artículo → 1 OFC
```

ni que:

```text
Artículo → N OFC
```

La cardinalidad y método de clasificación deben determinarse posteriormente.

---

# 15. Análisis bibliométrico

El sistema debe permitir incorporar análisis bibliométrico sobre el dataset
real.

Las métricas definitivas permanecen:

`PENDING_VALIDATION`

Posibles dimensiones de análisis incluyen:

* Evolución temporal.
* Producción científica.
* Autores.
* Instituciones.
* Países.
* Revistas.
* Palabras clave.
* Citaciones.
* Temáticas.
* OFC.
* Redes de colaboración.

Estas dimensiones no constituyen requisitos definitivos hasta ser validadas.

---

# 16. Datos

La estructura física de datos seguirá conceptualmente:

```text
data/
├── raw/
├── interim/
├── processed/
├── external/
├── samples/
└── exports/
```

## raw

Datos originales sin modificaciones.

## interim

Datos temporalmente transformados durante procesos intermedios.

## processed

Datos limpios y transformados para consumo de aplicaciones o análisis.

## external

Datos obtenidos de fuentes externas.

## samples

Subconjuntos utilizados exclusivamente para desarrollo y pruebas.

## exports

Datos exportados por la aplicación o pipelines.

---

# 17. Regla de inmutabilidad de RAW

Los archivos originales almacenados en `data/raw/` deben considerarse
inmutables.

Las transformaciones deben generar nuevos artefactos.

```text
RAW
 ↓
INTERIM
 ↓
PROCESSED
```

No modificar silenciosamente los datos originales.

---

# 18. Trazabilidad

Los procesos de datos deben intentar conservar:

* Fuente.
* Dataset.
* Fecha de adquisición.
* Fecha de procesamiento.
* Versión.
* Pipeline utilizado.
* Estado.

La trazabilidad es especialmente importante para los resultados bibliométricos.

---

# 19. Configuración

La configuración debe separarse del código.

Las variables sensibles o dependientes del entorno deben manejarse mediante
variables de entorno.

Ejemplo conceptual:

```text
DATABASE_URL
API_URL
ENVIRONMENT
LOG_LEVEL
```

No almacenar secretos reales en Git.

El archivo `.env.example` puede contener placeholders.

---

# 20. Gestión de secretos

Nunca almacenar:

* Contraseñas.
* API keys.
* Tokens.
* Credenciales.
* Secretos de servicios.

en el repositorio.

Los secretos deben proporcionarse mediante variables de entorno o mecanismos
seguros equivalentes.

---

# 21. Control de versiones

## Decisión

**Git**

El proyecto utilizará Git para control de versiones.

El repositorio remoto puede utilizar GitHub o GitLab según las necesidades de
SAO/EAFIT.

## Reglas

Los commits deben ser:

* Pequeños cuando sea razonable.
* Descriptivos.
* Relacionados con una funcionalidad o cambio concreto.

---

# 22. Testing

## Backend

Utilizar:

**pytest**

Las pruebas deben cubrir progresivamente:

* Unitarias.
* Integración.
* API.
* Procesamiento de datos.

## Frontend

El framework/librería exacta de testing del frontend queda:

`PENDING_VALIDATION`

Debe seleccionarse cuando se configure el proyecto React.

---

# 23. Calidad de datos

Antes de procesar datos deben realizarse validaciones apropiadas.

Como mínimo:

* Existencia de campos requeridos.
* Tipos de datos.
* Valores nulos.
* Duplicados.
* Consistencia.
* Formatos.
* Procedencia.

Las reglas específicas dependen del dataset real.

---

# 24. Deduplicación bibliográfica

## Estado

`PENDING_VALIDATION`

El método definitivo dependerá de:

* Identificadores disponibles.
* DOI.
* Título.
* Autores.
* Año.
* Fuente.
* Calidad de los metadatos.

No implementar reglas de deduplicación antes de analizar los datos reales.

---

# 25. Volumen de datos

Durante las reuniones se mencionaron volúmenes grandes de información,
incluyendo referencias a "200 mil" y "30 mil".

Estos valores no se consideran todavía volúmenes oficiales del dataset.

## Estado

`PENDING_VALIDATION`

La arquitectura deberá ser capaz de evolucionar si el volumen real supera la
capacidad de procesamiento de una solución local sencilla.

No realizar optimizaciones prematuras.

---

# 26. Ejecución local

La primera versión debe poder ejecutarse localmente.

Esto es coherente con la indicación recibida durante la reunión de que el
procesamiento debe correr localmente.

La estrategia definitiva para distribución o despliegue queda:

`PENDING_VALIDATION`

---

# 27. Docker

## Estado

`OPTIONAL / PENDING_VALIDATION`

Docker puede incorporarse para:

* PostgreSQL local.
* Backend.
* Frontend.
* Reproducibilidad.
* Configuración del entorno.

No introducir Docker si aumenta innecesariamente la complejidad inicial.

La necesidad debe evaluarse durante la implementación.

---

# 28. API

La API debe seguir una separación lógica entre:

```text
Routes
    ↓
Services
    ↓
Domain
    ↓
Repositories / Data Access
    ↓
Database
```

La estructura exacta puede evolucionar según la complejidad real.

No implementar una arquitectura excesivamente compleja para funcionalidades
simples.

---

# 29. Dashboard

El dashboard será implementado en React y consumirá datos mediante la API.

Debe permitir eventualmente visualizar información relacionada con:

* Ejes.
* Metas.
* Indicadores.
* Actividades.
* Regiones.
* Organizaciones.
* Progreso.
* Información bibliométrica.

Las visualizaciones definitivas deben definirse a partir de los requerimientos
de SAO.

---

# 30. Seguridad

Como mínimo:

* No exponer secretos.
* Validar inputs.
* Validar archivos cargados.
* Controlar acceso a endpoints cuando sea necesario.
* Evitar ejecución arbitraria de archivos.
* Registrar errores sin exponer información sensible.

El sistema de autenticación y autorización queda:

`PENDING_VALIDATION`

hasta determinar si el producto requiere usuarios autenticados y cuáles serán
sus roles.

---

# 31. Logging

El backend y los pipelines deben generar logs suficientes para diagnosticar:

* Errores.
* Procesamientos.
* Importaciones.
* Fallos de validación.
* Cambios relevantes.
* Ejecuciones de pipelines.

Los logs no deben contener secretos.

---

# 32. Manejo de errores

Los errores deben ser:

* Detectables.
* Registrados.
* Comprensibles.
* Separados entre errores internos y errores comunicables al usuario.

La API no debe exponer stack traces ni información sensible en producción.

---

# 33. Evolución de arquitectura

La arquitectura debe mantenerse simple mientras el proyecto se encuentra en
etapas tempranas.

No implementar:

* Microservicios.
* Colas distribuidas.
* Sistemas de streaming.
* Lakehouse complejo.
* Infraestructura cloud avanzada.

sin evidencia de que sean necesarios.

La arquitectura debe evolucionar a partir de necesidades reales del dataset y
del producto.

---

# 34. Decisiones pendientes

Las siguientes decisiones permanecen abiertas porque requieren información
adicional:

### Bibliometría

* Dataset definitivo.
* Fuente de artículos.
* Campos disponibles.
* Volumen real.
* Estrategia de deduplicación.
* Clasificación.
* Relación Artículo ↔ OFC.
* Métricas bibliométricas.
* Modelo de IA/ML.
* Estrategia de evaluación.

### Producto

* Alcance exacto del MVP.
* Indicadores prioritarios.
* Metas prioritarias.
* Granularidad del progreso regional.
* Modelo definitivo de actores.
* Requisitos de autenticación.
* Roles de usuario.

### Infraestructura

* Estrategia de despliegue.
* Uso definitivo de Docker.
* Repositorio remoto.
* Estrategia de actualización anual.
* Mecanismo de distribución de datasets.

Estas decisiones deben registrarse mediante ADR cuando sean tomadas.

---

# 35. ADRs

Las decisiones arquitectónicas relevantes deben documentarse en:

```text
docs/decisions/
```

Cada ADR debe contener como mínimo:

* Contexto.
* Problema.
* Opciones consideradas.
* Decisión.
* Justificación.
* Consecuencias.
* Estado.

No utilizar ADRs para decisiones triviales.

---

# 36. Regla para agentes de IA

Los agentes de IA utilizados durante el desarrollo deben:

1. Leer los archivos de `.kiro/steering/` antes de realizar cambios relevantes.
2. Respetar las decisiones técnicas documentadas.
3. No inventar datos.
4. No convertir hipótesis en requisitos.
5. Marcar información faltante como `PENDING_VALIDATION`.
6. No modificar archivos de Steering sin indicación explícita.
7. Explicar cualquier conflicto entre documentos antes de implementar una
   decisión contradictoria.
8. Evitar sobreingeniería.
9. Mantener trazabilidad de decisiones importantes.
10. No utilizar datos sintéticos como datos reales.

---

# 37. Prioridad de fuentes

La prioridad depende del TIPO de decisión en conflicto. Debe aplicarse la regla
que corresponda al dominio del conflicto.

## 37.1 Decisiones de producto y de dominio

Para requisitos de producto, reglas de negocio, significado del dominio,
entidades, campos, categorías, relaciones y datos, prevalecen en este orden:

```text
1. Requisitos confirmados por SAO
2. Decisiones documentadas en ADRs vigentes
3. product.md
4. data-and-domain.md
5. data-inventory.md
6. tech.md
7. structure.md
8. Inferencias del agente
```

## 37.2 Decisiones técnicas

Para decisiones estrictamente técnicas (lenguaje, frameworks, motor de base de
datos, ORM, migraciones, testing, estructura de código, arquitectura de la
solución), la autoridad técnica principal es:

```text
1. Requisitos confirmados por SAO que impongan una restricción técnica
2. ADRs técnicos vigentes (p. ej. ADR-001)
3. tech.md  (autoridad técnica principal)
4. structure.md
5. Inferencias del agente
```

`product.md`, `data-and-domain.md` y `data-inventory.md` siguen siendo la fuente
de verdad del QUÉ y del PORQUÉ; `tech.md` es la autoridad del CON QUÉ y del CÓMO
técnico.

## 37.3 Rol de los ADR

Los ADR documentan decisiones concretas y NO deben contradecir los documentos de
Steering vigentes. Si un ADR entra en conflicto con el Steering actual, el ADR
debe revisarse o marcarse como superado; no puede usarse para anular una regla
de Steering vigente.

## 37.4 Conflicto irresoluble

Si existe un conflicto entre documentos que esta regla no permita resolver con
claridad, NO debe elegirse una opción de forma arbitraria. El conflicto debe
marcarse explícitamente como `PENDING_VALIDATION`, documentarse y escalarse para
validación antes de implementar cualquier decisión dependiente.

## 37.5 Regla transversal

Las inferencias del agente nunca deben sobreescribir decisiones confirmadas ni
decisiones documentadas en Steering o ADRs vigentes.

---

# 38. Estado actual

## Implementado

* Estructura inicial del proyecto.
* Documentación de producto.
* Inventario de datos.
* Modelo conceptual de dominio.
* Arquitectura técnica inicial.
* Definición del stack base.

## Pendiente

* Dataset bibliométrico.
* Clasificador.
* Análisis bibliométrico definitivo.
* Indicadores prioritarios.
* Requerimientos definitivos del dashboard.
* Modelo definitivo de actores.
* Despliegue.
* Autenticación.

---

# 39. Stack tecnológico resumido

```text
Lenguaje principal:
Python 3.12+

Backend:
FastAPI

Validación:
Pydantic

ORM:
SQLAlchemy

Base de datos:
PostgreSQL

Migraciones:
Alembic

Frontend:
React + TypeScript

UI / Prototipado:
Lovable

Testing backend:
pytest

Control de versiones:
Git

Ejecución inicial:
Local

Docker:
Opcional / Pendiente de validación

Bibliometría:
Python

Clasificación:
PENDING_VALIDATION

Modelo de IA:
PENDING_VALIDATION

Despliegue:
PENDING_VALIDATION
```

---

# 40. Regla final

La tecnología debe servir al problema, no al contrario.

Las decisiones futuras deben justificarse mediante:

* Requisitos.
* Volumen de datos.
* Complejidad.
* Mantenibilidad.
* Reproducibilidad.
* Facilidad de operación para SAO.
* Experiencia del equipo.
* Costos.

No incorporar una tecnología únicamente porque sea popular o moderna.
