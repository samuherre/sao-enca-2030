# Requirements Document

Documento de Requisitos — Seguimiento de la Estructura ENCA (enca-strategy-tracking)

## Introduction

Esta Spec define el **núcleo funcional** para gestionar y consultar la estructura
de seguimiento de la Estrategia Nacional para la Conservación de las Aves (ENCA
2030), en el contexto del proyecto SAO ENCA 2030.

El alcance se limita estrictamente a las **cinco entidades de dominio confirmadas**
y a la jerarquía confirmada entre ellas:

```text
Eje → Meta → Objetivo SMART → Indicador → Actividad
```

Esta estructura está respaldada por el Steering del proyecto (reglas de dominio
D-001 a D-004) y por el modelo conceptual (`docs/data/conceptual-data-model.md` §2,
§3). La solución debe permitir **registrar** y **consultar** cada entidad, **navegar**
la jerarquía completa y **mantener la integridad referencial** entre niveles.

La estructura debe quedar **preparada** para incorporar posteriormente seguimiento
y evidencias cuando el dominio esté validado, pero esos elementos **no se
implementan en esta Spec**.

El contexto tecnológico (no se reimplementa en este documento) es: backend en
Python 3.12+ con FastAPI, Pydantic, SQLAlchemy, Alembic y PostgreSQL; frontend en
React + TypeScript; pruebas de backend con pytest; separación de capas Routes →
Services → Domain → Repositories/Data Access → Database (`tech.md`, `structure.md`,
ADR-001).

> Principio de no invención: solo se modelan atributos **confirmados** por
> `data-and-domain.md`, `data-inventory.md` y `conceptual-data-model.md`. Todo
> atributo adicional que una entidad pudiera necesitar y que no esté confirmado se
> marca explícitamente como `PENDING_VALIDATION` y **no** se le asigna un valor
> inventado.

---

## Glossary

- **ENCA**: Estrategia Nacional para la Conservación de las Aves (ENCA 2030). Marco
  de dominio del proyecto.
- **Sistema_ENCA**: Nombre del sistema que implementa el seguimiento de la
  estructura ENCA (backend, API y frontend) descrito en esta Spec. Es el `<system>`
  usado en los criterios EARS salvo que se indique un componente más específico.
- **Eje** (Eje estratégico): Línea estratégica de acción de la ENCA 2030. Atributos
  confirmados: identificador, nombre, descripción (opcional). (`conceptual-data-model.md`
  §2.1, D-001.)
- **Meta**: Resultado esperado dentro de un Eje. Atributos confirmados: identificador,
  descripción/enunciado, referencia al Eje. (`conceptual-data-model.md` §2.2, D-001.)
- **Objetivo SMART** (Objetivo): Objetivo específico asociado a una Meta. Atributos
  confirmados: identificador, descripción/enunciado, referencia a la Meta.
  (`conceptual-data-model.md` §2.3, D-002.)
- **Indicador**: Medida de seguimiento asociada a un Objetivo. Atributos confirmados:
  identificador, nombre, descripción, referencia al Objetivo. Otros atributos son
  `PENDING_VALIDATION`. (`conceptual-data-model.md` §2.4, D-003.)
- **Actividad**: Acción propuesta asociada a un Indicador. Atributos confirmados:
  identificador, nombre/descripción, referencia al Indicador. Otros atributos son
  `PENDING_VALIDATION`. (`conceptual-data-model.md` §2.5, D-004.)
- **Jerarquía ENCA**: La relación padre-hijo confirmada Eje → Meta → Objetivo SMART
  → Indicador → Actividad. (`conceptual-data-model.md` §3.)
- **Integridad referencial**: Garantía de que toda entidad hija referencia una
  entidad padre existente y de que no quedan referencias colgantes.
- **OFC** (Objeto Focal de Conservación): Entidad de **referencia del dominio** (11
  OFC definidos por la documentación ENCA). En esta Spec el OFC solo se menciona como
  **referencia futura**; **no** se modela, crea, modifica ni relaciona con otras
  entidades. Su uso y la relación Artículo↔OFC son `PENDING_VALIDATION`.
  (`conceptual-data-model.md` §2.8, §4.3.)
- **DEMO_DATA**: Datos sintéticos usados exclusivamente para desarrollo y pruebas,
  marcados explícitamente como tales. Nunca se presentan como información oficial de
  SAO. (`tech.md` §2.3, `data-and-domain.md` §37.)
- **PENDING_VALIDATION**: Marca explícita para información, atributos o reglas que
  todavía deben confirmarse con SAO y que no deben convertirse en reglas rígidas ni
  recibir valores inventados.

---

## Requirements

### Requisito 1: Gestión de Ejes

**Historia de usuario:** Como analista de SAO, quiero registrar y consultar Ejes estratégicos, para disponer del nivel superior de la estructura de seguimiento ENCA.

#### Criterios de aceptación

1. WHEN un usuario envía los datos de un Eje con un nombre no nulo que, tras eliminar los espacios en blanco al inicio y al final, no queda vacío, THE Sistema_ENCA SHALL crear el Eje asignándole un identificador único, almacenar el nombre y la descripción opcional.
2. IF un usuario envía la solicitud de creación de un Eje sin nombre, con nombre vacío o compuesto únicamente por espacios en blanco, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ningún Eje y devolver un error de validación que identifique el campo nombre como faltante.
3. WHEN un usuario solicita la lista de Ejes, THE Sistema_ENCA SHALL devolver todos los Ejes registrados con sus campos confirmados, o una colección vacía si no hay Ejes registrados.
4. WHEN un usuario solicita un Eje por su identificador existente, THE Sistema_ENCA SHALL devolver el Eje con sus campos confirmados.
5. IF un usuario solicita un Eje con un identificador que no corresponde a ningún Eje existente, THEN THE Sistema_ENCA SHALL devolver un error de recurso no encontrado.

### Requisito 2: Gestión de Metas asociadas a un Eje

**Historia de usuario:** Como analista de SAO, quiero registrar y consultar Metas asociadas a un Eje, para desglosar cada Eje en los resultados esperados.

#### Criterios de aceptación

1. WHEN un usuario envía los datos de una Meta con una descripción no nula que, tras eliminar los espacios en blanco al inicio y al final, no queda vacía, y una referencia a un Eje existente, THE Sistema_ENCA SHALL crear la Meta, generar un identificador único no reutilizable, asociarla al Eje referenciado y devolver el identificador generado junto con sus campos confirmados.
2. IF un usuario intenta crear una Meta referenciando un identificador de Eje que no corresponde a ningún Eje existente, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ninguna Meta y devolver un error que indique que la referencia al Eje es inválida.
3. IF un usuario envía la solicitud de creación de una Meta sin el campo descripción o con una descripción vacía o compuesta únicamente por espacios en blanco, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ninguna Meta y devolver un error de validación que identifique el campo descripción como faltante o inválido.
4. WHEN un usuario solicita las Metas de un Eje existente, THE Sistema_ENCA SHALL devolver todas las Metas asociadas a ese Eje, cada una con su identificador, su descripción y la referencia a su Eje.
5. IF un usuario solicita las Metas de un Eje existente que no tiene Metas asociadas, THEN THE Sistema_ENCA SHALL devolver una colección vacía sin generar un error.
6. WHEN un usuario solicita una Meta por un identificador existente, THE Sistema_ENCA SHALL devolver la Meta con su identificador, su descripción y la referencia a su Eje.
7. IF un usuario solicita una Meta con un identificador que no corresponde a ninguna Meta existente, THEN THE Sistema_ENCA SHALL rechazar la solicitud y devolver un error que indique que el recurso no fue encontrado.

### Requisito 3: Gestión de Objetivos SMART asociados a una Meta

**Historia de usuario:** Como analista de SAO, quiero registrar y consultar Objetivos SMART asociados a una Meta, para especificar los objetivos concretos de cada Meta.

#### Criterios de aceptación

1. WHEN un usuario envía los datos de un Objetivo SMART con una descripción no nula que, tras eliminar los espacios en blanco al inicio y al final, no queda vacía, y con una referencia a una Meta existente, THE Sistema_ENCA SHALL crear el Objetivo con un identificador único asociado a esa Meta y devolver el identificador generado.
2. IF un usuario intenta crear un Objetivo SMART referenciando una Meta que no existe, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ningún Objetivo y devolver un error que indique referencia a Meta inválida.
3. IF un usuario envía la solicitud de creación de un Objetivo SMART sin el campo descripción, o con una descripción que tras eliminar espacios en blanco iniciales y finales queda vacía, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ningún Objetivo y devolver un error de validación que identifique el campo descripción como faltante o vacío.
4. WHEN un usuario solicita los Objetivos SMART de una Meta existente, THE Sistema_ENCA SHALL devolver todos los Objetivos asociados a esa Meta, cada uno con sus campos confirmados (identificador, descripción y referencia a la Meta), y devolver una colección vacía si la Meta no tiene Objetivos asociados.
5. IF un usuario solicita los Objetivos SMART de una Meta cuyo identificador no existe, THEN THE Sistema_ENCA SHALL rechazar la solicitud y devolver un error de recurso no encontrado para la Meta.
6. WHEN un usuario solicita un Objetivo SMART por su identificador existente, THE Sistema_ENCA SHALL devolver el Objetivo con sus campos confirmados (identificador, descripción y referencia a su Meta).
7. IF un usuario solicita un Objetivo SMART con un identificador que no existe, THEN THE Sistema_ENCA SHALL devolver un error de recurso no encontrado.

### Requisito 4: Gestión de Indicadores asociados a un Objetivo

**Historia de usuario:** Como analista de SAO, quiero registrar y consultar Indicadores asociados a un Objetivo SMART, para disponer de las medidas de seguimiento de cada Objetivo.

#### Criterios de aceptación

1. WHEN un usuario envía los datos de un Indicador con un nombre no nulo que, tras eliminar los espacios en blanco al inicio y al final, no queda vacío, y una referencia a un Objetivo SMART existente, THE Sistema_ENCA SHALL crear el Indicador asignándole un identificador único asociado a ese Objetivo y almacenar el nombre y la descripción.
2. IF un usuario intenta crear un Indicador referenciando un Objetivo SMART que no existe, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ningún Indicador y devolver un error que indique que la referencia al Objetivo es inválida.
3. IF un usuario envía la solicitud de creación de un Indicador sin nombre, con nombre vacío o compuesto únicamente por espacios en blanco, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no crear ningún Indicador y devolver un error de validación que identifique el campo nombre como faltante.
4. WHEN un usuario solicita los Indicadores de un Objetivo SMART existente, THE Sistema_ENCA SHALL devolver todos los Indicadores asociados a ese Objetivo con sus campos confirmados, o una colección vacía si el Objetivo no tiene Indicadores asociados.
5. WHEN un usuario solicita un Indicador por su identificador existente, THE Sistema_ENCA SHALL devolver el Indicador con sus campos confirmados y la referencia a su Objetivo.
6. IF un usuario solicita un Indicador con un identificador que no existe, THEN THE Sistema_ENCA SHALL devolver un error de recurso no encontrado.
7. THE Sistema_ENCA SHALL omitir del contrato de datos del Indicador los atributos marcados como PENDING_VALIDATION (unidad de medida, valor objetivo, valor actual, fecha de medición, fuente/evidencia, estado) mientras no estén validados por SAO.

### Requisito 5: Gestión de Actividades asociadas a un Indicador

**Historia de usuario:** Como analista de SAO, quiero registrar y consultar Actividades asociadas a un Indicador, para registrar las acciones que implementan el seguimiento de cada Indicador.

#### Criterios de aceptación

1. WHEN un usuario envía los datos de una Actividad con un nombre/descripción no nulo que, tras eliminar los espacios en blanco al inicio y al final, no queda vacío, y una referencia a un Indicador existente, THE Sistema_ENCA SHALL crear la Actividad asignándole un identificador distinto del de cualquier otra Actividad existente y asociarla a ese Indicador.
2. IF un usuario intenta crear una Actividad referenciando un Indicador que no existe, THEN THE Sistema_ENCA SHALL rechazar la solicitud sin crear ninguna Actividad y devolver una respuesta de error que indique que la referencia al Indicador es inválida.
3. IF un usuario envía la solicitud de creación de una Actividad con el nombre/descripción ausente o compuesto únicamente por espacios en blanco, THEN THE Sistema_ENCA SHALL rechazar la solicitud sin crear ninguna Actividad y devolver una respuesta de error de validación que identifique el campo nombre/descripción como faltante.
4. WHEN un usuario solicita las Actividades de un Indicador existente que tiene al menos una Actividad asociada, THE Sistema_ENCA SHALL devolver todas las Actividades asociadas a ese Indicador, cada una con su identificador, su nombre/descripción y la referencia a su Indicador.
5. WHEN un usuario solicita las Actividades de un Indicador existente que no tiene Actividades asociadas, THE Sistema_ENCA SHALL devolver una colección vacía sin devolver un error.
6. WHEN un usuario solicita una Actividad por un identificador que corresponde a una Actividad existente, THE Sistema_ENCA SHALL devolver esa Actividad con su identificador, su nombre/descripción y la referencia a su Indicador.
7. IF un usuario solicita una Actividad con un identificador que no corresponde a ninguna Actividad existente, THEN THE Sistema_ENCA SHALL devolver una respuesta de error que indique que el recurso no fue encontrado.
8. THE Sistema_ENCA SHALL omitir del contrato de datos de la Actividad los atributos marcados como PENDING_VALIDATION (responsable, fecha, estado, evidencia/fuente, región) mientras no estén validados por SAO.

### Requisito 6: Navegación de la jerarquía completa

**Historia de usuario:** Como analista de SAO, quiero navegar la jerarquía completa desde un Eje hasta sus Actividades, para explorar la estructura de seguimiento ENCA de forma coherente.

#### Criterios de aceptación

1. WHEN un usuario solicita la estructura jerárquica de un Eje existente, THE Sistema_ENCA SHALL devolver el Eje junto con sus Metas, Objetivos SMART, Indicadores y Actividades anidados según la relación Eje → Meta → Objetivo SMART → Indicador → Actividad, abarcando los cinco niveles confirmados.
2. WHEN un usuario navega desde una entidad hija hacia su entidad padre, THE Sistema_ENCA SHALL devolver la referencia al padre inmediato correspondiente en la jerarquía.
3. WHERE la entidad consultada es un Eje (nivel raíz) sin entidad padre, THE Sistema_ENCA SHALL indicar que no existe entidad padre en lugar de devolver un error.
4. WHERE una entidad de la jerarquía no tiene entidades hijas registradas, THE Sistema_ENCA SHALL devolver una colección de hijas vacía para esa entidad.
5. IF un usuario solicita la estructura jerárquica de un Eje con un identificador que no corresponde a ningún Eje existente, THEN THE Sistema_ENCA SHALL devolver un error de recurso no encontrado.

### Requisito 7: Visualización y navegación en el frontend

**Historia de usuario:** Como usuario de SAO, quiero visualizar y navegar la estructura jerárquica en una interfaz sencilla, para consultar Ejes, Metas, Objetivos, Indicadores y Actividades sin usar herramientas técnicas.

#### Criterios de aceptación

1. WHEN un usuario abre la vista inicial, THE Frontend SHALL solicitar la lista de Ejes a la API del Sistema_ENCA y mostrar cada Eje devuelto en una lista.
2. IF la API no devuelve ningún Eje, THEN THE Frontend SHALL mostrar un mensaje indicando que no hay Ejes disponibles, en lugar de una lista vacía sin contexto.
3. WHEN un usuario selecciona una entidad en la interfaz, THE Frontend SHALL mostrar las entidades hijas del nivel inmediatamente inferior según la Jerarquía ENCA (Eje → Meta → Objetivo SMART → Indicador → Actividad).
4. WHEN un usuario selecciona una entidad que no tiene entidades hijas en el nivel inmediatamente inferior, THE Frontend SHALL mostrar un mensaje indicando que no existen entidades hijas para esa entidad.
5. WHEN un usuario selecciona una entidad en la interfaz, THE Frontend SHALL mostrar los campos confirmados de esa entidad obtenidos desde la API, y SHALL mostrar la indicación "Sin información" para cada campo confirmado cuyo valor sea nulo o vacío.
6. THE Frontend SHALL permitir al usuario navegar entre los niveles Eje, Meta, Objetivo SMART, Indicador y Actividad, incluyendo el regreso a un nivel superior previamente visitado.
7. WHILE la interfaz espera la respuesta de la API, THE Frontend SHALL mostrar un indicador de estado de carga hasta que la respuesta se reciba o se cumpla un tiempo límite de 30 segundos.
8. IF la API no responde dentro del tiempo límite de 30 segundos, THEN THE Frontend SHALL interrumpir la espera y mostrar un mensaje de error que indique que la consulta no pudo completarse, conservando la última vista válida mostrada al usuario.
9. IF la API devuelve un error, THEN THE Frontend SHALL mostrar un mensaje de error comprensible que indique que la operación falló, sin exponer trazas de pila, identificadores internos ni detalles técnicos de implementación.

### Requisito 8: Integridad referencial de la jerarquía

**Historia de usuario:** Como responsable de datos de SAO, quiero que las relaciones entre entidades se mantengan íntegras, para evitar referencias inconsistentes o colgantes en la estructura de seguimiento.

#### Criterios de aceptación

1. THE Sistema_ENCA SHALL asociar cada Meta a exactamente un Eje existente, cada Objetivo SMART a exactamente una Meta existente, cada Indicador a exactamente un Objetivo SMART existente y cada Actividad a exactamente un Indicador existente.
2. IF una solicitud intenta crear una entidad hija con una referencia a un padre inexistente, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no persistir ningún cambio en la entidad hija y devolver un error que indique que la referencia al padre es inválida, identificando el tipo de entidad padre esperado.
3. IF una solicitud intenta crear una entidad hija cuya referencia al padre es nula o está ausente, THEN THE Sistema_ENCA SHALL rechazar la solicitud, no persistir ningún cambio en la entidad hija y devolver un error que indique que la referencia al padre es obligatoria.
4. THE Sistema_ENCA SHALL asignar a cada entidad creada un identificador único dentro de su tipo de entidad.

### Requisito 9: Preparación para seguimiento y evidencias futuros

**Historia de usuario:** Como arquitecto del proyecto, quiero que la estructura quede preparada para incorporar seguimiento y evidencias cuando el dominio esté validado, para evitar rediseños mayores sin introducir funcionalidad no confirmada.

#### Criterios de aceptación

1. THE Sistema_ENCA SHALL registrar en su documentación de dominio, como PENDING_VALIDATION, los atributos de seguimiento y evidencia del Indicador (unidad de medida, valor objetivo, valor actual, fecha de medición, fuente/evidencia, estado) sin asignarles valores ni exponerlos en los contratos de datos.
2. THE Sistema_ENCA SHALL registrar en su documentación de dominio, como PENDING_VALIDATION, los atributos de seguimiento y evidencia de la Actividad (responsable, fecha, estado, evidencia/fuente, región) sin asignarles valores ni exponerlos en los contratos de datos.
3. WHILE los atributos de seguimiento, progreso y evidencia permanezcan PENDING_VALIDATION, THE Sistema_ENCA SHALL excluir del comportamiento implementado toda lógica de seguimiento, cálculo de progreso o gestión de evidencias.
4. IF una solicitud intenta leer o escribir un atributo PENDING_VALIDATION del Indicador o de la Actividad, THEN THE Sistema_ENCA SHALL rechazar la operación sobre ese atributo e indicar que no está disponible en esta versión.

### Requisito 10: Datos de desarrollo identificados (DEMO_DATA)

**Historia de usuario:** Como desarrollador del proyecto, quiero usar datos de prueba claramente identificados, para desarrollar y verificar la funcionalidad sin confundirlos con información oficial de SAO.

#### Criterios de aceptación

1. WHERE se requieran datos para desarrollo o pruebas, THE Sistema_ENCA SHALL marcar esos datos con una indicación DEMO_DATA legible.
2. WHEN el Sistema_ENCA presenta o exporta datos marcados como DEMO_DATA, THE Sistema_ENCA SHALL indicar que son datos de demostración y no información oficial de SAO.
3. THE Sistema_ENCA SHALL evitar presentar datos DEMO_DATA como información oficial de SAO.

---

## Verificación y pruebas (criterios verificables)

Las siguientes capacidades deben ser verificables mediante pruebas automatizadas de
backend con **pytest**, cubriendo progresivamente pruebas unitarias, de integración
y de API (`tech.md` §22):

1. **Creación** de cada entidad (Eje, Meta, Objetivo SMART, Indicador, Actividad)
   con datos válidos.
2. **Consulta** individual y por colección de cada entidad, incluyendo el caso de
   colección vacía.
3. **Validación** de campos obligatorios confirmados (nombre/descripción según
   entidad).
4. **Casos inválidos**: creación sin campos obligatorios, referencia a un padre
   inexistente y consulta de un identificador inexistente.
5. **Relaciones entre entidades**: asociación correcta hija→padre y mantenimiento de
   la integridad referencial a lo largo de la Jerarquía ENCA.
6. **Endpoints principales** de la API para registrar y consultar cada entidad y
   para navegar la jerarquía.

> Nota: no se definen aún métricas ni pruebas sobre atributos PENDING_VALIDATION ni
> sobre funcionalidad fuera de alcance.

---

## Atributos PENDING_VALIDATION por entidad

Estos atributos **no se implementan** en esta Spec y **no reciben valores inventados**.
Se registran para preparar la evolución del dominio (`conceptual-data-model.md` §2.4,
§2.5; `data-and-domain.md` §8, §9).

- **Eje**: ninguno pendiente conocido (identificador, nombre, descripción opcional
  son los atributos confirmados).
- **Meta**: ninguno pendiente conocido (identificador, descripción/enunciado y
  referencia al Eje son los atributos confirmados).
- **Objetivo SMART**: ninguno pendiente conocido (identificador, descripción/enunciado
  y referencia a la Meta son los atributos confirmados).
- **Indicador** — PENDING_VALIDATION:
  - Unidad de medida
  - Valor objetivo
  - Valor actual
  - Fecha de medición
  - Fuente / evidencia
  - Estado
- **Actividad** — PENDING_VALIDATION:
  - Responsable
  - Fecha
  - Estado
  - Evidencia / fuente
  - Región

> Cualquier otro atributo que surja durante el diseño y que no esté confirmado en
> `data-and-domain.md`, `data-inventory.md` o `conceptual-data-model.md` debe
> añadirse aquí como PENDING_VALIDATION en lugar de inventarse.

---

## Fuera de alcance (Out of Scope)

Las siguientes capacidades **no forman parte** de esta Spec. Se listan explícitamente
para evitar sobreingeniería y suposiciones no validadas:

- Ingestión de artículos científicos.
- Clasificación bibliométrica.
- Procesamiento de lenguaje natural (NLP).
- Machine Learning.
- Modelos de lenguaje (LLM).
- Embeddings.
- Deduplicación bibliográfica.
- Análisis bibliométrico y métricas bibliométricas.
- Relación Artículo ↔ OFC (el OFC solo se menciona como **referencia futura**; no se
  modela ni se relaciona en esta Spec).
- Dashboard bibliométrico y visualizaciones analíticas complejas.
- Despliegue / infraestructura de producción.
- Autenticación y autorización, roles y permisos de usuario.
- Modelado de Región, Progreso regional, OFC y Actores/Organizaciones/Personas como
  parte de esta Spec.
- Seguimiento, cálculo de progreso y gestión de evidencias (los atributos quedan
  PENDING_VALIDATION; la estructura solo queda preparada para su futura
  incorporación).
- Actualización (update) y eliminación (delete) de entidades — podrán considerarse
  en una Spec futura; esta Spec cubre únicamente creación y consulta.

---

## Decisiones técnicas provisionales (no son reglas de SAO)

Las siguientes son **decisiones técnicas abiertas**, no reglas de negocio confirmadas
por SAO. Se documentan para evitar que supuestos de implementación se interpreten como
requisitos del dominio:

- Cualquier **límite de longitud** que se aplique a los campos de texto (por ejemplo,
  nombres o descripciones) durante la implementación es una **decisión técnica
  provisional de validación**, no una regla de negocio confirmada por SAO.
- En estos requisitos **no se inventan límites específicos** de longitud. Los criterios
  de aceptación funcionales se centran en que los campos obligatorios no sean nulos ni
  vacíos (ni compuestos únicamente por espacios en blanco).
- Los límites concretos, si se consideran necesarios, **podrán definirse en la fase de
  diseño o de implementación** y deberán **revisarse con SAO** antes de tratarse como
  reglas del dominio.
