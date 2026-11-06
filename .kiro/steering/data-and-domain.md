# Data and Domain — SAO ENCA 2030

## 1. Propósito

Este documento define el dominio de información del proyecto desarrollado para la
Sociedad Antioqueña de Ornitología (SAO) en el contexto de la Estrategia Nacional
para la Conservación de las Aves (ENCA 2030).

Define:

* Los conceptos principales del dominio.
* Las entidades conocidas.
* Las relaciones entre entidades.
* Las fuentes de información.
* Los catálogos y datos de referencia.
* Las reglas de negocio conocidas.
* La estructura conceptual de los datos.
* La relación entre los datos y los objetivos del producto.
* Los vacíos de información conocidos.
* Las decisiones que todavía requieren validación con SAO.

Este documento debe utilizarse como referencia para el diseño de modelos de
datos, pipelines, APIs, funcionalidades y componentes de visualización.

---

# 2. Principio fundamental de confiabilidad

El proyecto debe diferenciar estrictamente entre:

### Confirmado

Información respaldada por documentos entregados por SAO o por una decisión
explícita de los responsables del proyecto.

### Inferido

Interpretaciones o relaciones propuestas a partir de la información disponible.

### Pendiente de validación

Información que todavía debe confirmarse con SAO.

Los elementos inferidos y pendientes NO deben convertirse automáticamente en
reglas de negocio obligatorias.

Cuando una decisión de diseño dependa de información no disponible, debe
marcarse explícitamente como:

`PENDING_VALIDATION`

No inventar datos, relaciones, categorías, campos, indicadores o reglas que no
estén respaldados por las fuentes disponibles.

---

# 3. Contexto del dominio

La ENCA 2030 es una estrategia nacional orientada a la conservación de las
aves y sus hábitats.

El proyecto busca apoyar el seguimiento de la estrategia mediante:

* Organización de información.
* Seguimiento de indicadores.
* Seguimiento de actividades.
* Gestión de información relacionada con actores.
* Visualización de avances.
* Automatización.
* Gestión del conocimiento.
* Análisis de información científica y bibliométrica.

El alcance inicial indicado por SAO se concentra especialmente en los
**Ejes Estratégicos 2 y 5**.

---

# 4. Ejes estratégicos

La ENCA 2030 se estructura mediante ejes estratégicos.

Los datos proporcionados por SAO representan una jerarquía conceptual:

```text
Eje estratégico
    ↓
Meta
    ↓
Objetivo SMART
    ↓
Indicador
    ↓
Actividad
```

Esta estructura aparece en las fuentes Excel de los ejes estratégicos.

---

# 5. Eje estratégico

## Definición

Un eje estratégico representa una línea estratégica de acción dentro de la
ENCA 2030.

## Atributos conceptuales

Un eje puede contener:

* Identificador.
* Nombre.
* Descripción.
* Información adicional.

Los nombres e identificadores definitivos deben provenir de la fuente oficial
de ENCA.

## Relaciones

```text
Eje estratégico
    └── contiene → Meta
```

---

# 6. Meta

## Definición

Una meta representa un resultado esperado dentro de un eje estratégico.

Las fuentes proporcionadas contienen metas asociadas a objetivos SMART,
indicadores y actividades.

## Relaciones

```text
Eje estratégico
    └── tiene → Meta
```

Una meta puede tener uno o varios objetivos SMART.

---

# 7. Objetivo SMART

## Definición

Representa el objetivo específico asociado a una meta de ENCA.

Las fuentes entregadas contienen objetivos SMART vinculados con indicadores y
actividades.

## Relaciones

```text
Meta
    └── tiene → Objetivo SMART
```

---

# 8. Indicador

## Definición

Un indicador representa una medida utilizada para realizar seguimiento al
cumplimiento de una meta u objetivo.

Los indicadores aparecen explícitamente en las fuentes de los ejes estratégicos.

## Atributos conceptuales

Un indicador puede requerir:

* Identificador.
* Nombre.
* Descripción.
* Unidad de medida.
* Valor objetivo.
* Valor actual.
* Fecha de medición.
* Fuente.
* Evidencia.
* Estado.

Sin embargo, no todos estos atributos han sido confirmados en los datos
actuales.

Los atributos adicionales deben considerarse:

`PENDING_VALIDATION`

## Relaciones

```text
Objetivo SMART
    └── tiene → Indicador
```

---

# 9. Actividad

## Definición

Una actividad representa una acción propuesta para contribuir al cumplimiento
de una meta u objetivo.

Las fuentes proporcionadas contienen actividades asociadas a los indicadores.

## Atributos conceptuales

Una actividad puede contener:

* Identificador.
* Nombre.
* Descripción.
* Responsable.
* Fecha.
* Estado.
* Evidencia.
* Fuente.
* Región.

No todos estos atributos están presentes de forma uniforme en las fuentes.

## Relaciones

```text
Indicador
    └── se implementa mediante → Actividad
```

La relación exacta entre actividad e indicador debe validarse si una actividad
puede contribuir a múltiples indicadores.

---

# 10. Regiones

La información proporcionada incluye seguimiento regional.

Se identifican:

* Región Andina.
* Región Caribe.
* Región Insular.
* Región Orinoquía.
* Región Pacífico.
* Región Amazonía.

Estas regiones aparecen asociadas a información de progreso en una de las
fuentes de ejes estratégicos.

## Relación conceptual

```text
Actividad / Indicador
        ↓
     Región
        ↓
  Estado / Progreso
```

La granularidad definitiva del progreso regional debe validarse.

---

# 11. Progreso

El archivo `Ejes estratégicos ENCA.xlsx` contiene información de progreso
asociada a regiones.

También aparece una categoría:

`Necesitamos aumentar esfuerzos`

El significado exacto de esta clasificación debe conservarse según la fuente
original y validarse con SAO antes de convertirla en una enumeración técnica.

## Estado

`CONFIRMED_AS_SOURCE_DATA`

## Pendiente

Debe definirse:

* Qué representa exactamente "progreso".
* Si es porcentaje.
* Si es estado cualitativo.
* Si corresponde a una evaluación manual.
* Quién lo actualiza.
* Con qué periodicidad se actualiza.
* Qué evidencia respalda el progreso.

---

# 12. Objetos Focales de Conservación (OFC)

Los Objetos Focales de Conservación son categorías de referencia utilizadas
dentro del dominio de conservación de aves.

Se identifican 11 OFC en la documentación proporcionada:

1. Aves marinas, insulares, costeras y de manglar.
2. Aves de humedales interiores de agua dulce.
3. Aves de sabanas y pastizales.
4. Aves de bosques y matorrales secos.
5. Aves de bosques húmedos de tierras bajas.
6. Aves de bosques premontanos y montanos.
7. Aves de ecosistemas de alta montaña.
8. Aves en sistemas urbanos.
9. Aves en agroecosistemas.
10. Sistemas culturales asociados a la apreciación de las aves.
11. Aviturismo.

## Estado

`CONFIRMED_AS_DOMAIN_REFERENCE`

## Uso potencial

Los OFC podrían utilizarse para:

* Clasificación de información.
* Clasificación de publicaciones.
* Filtros.
* Agrupación de resultados.
* Visualizaciones.
* Análisis de conocimiento.

## Regla importante

No asumir automáticamente que los 11 OFC constituyen las clases definitivas del
modelo de clasificación bibliométrica.

La relación:

```text
Artículo → OFC
```

está:

`PENDING_VALIDATION`

---

# 13. Actores

Los documentos entregados contienen información relacionada con diferentes
actores de la ENCA.

Entre ellos aparecen:

* Comité Ejecutivo.
* Academia.
* Grupos de investigación.
* Instituciones.
* Sectores productivos.
* Organizaciones.
* Otros actores relacionados con conservación.

## Entidad conceptual

Un actor representa una persona, organización o institución que participa,
apoya, ejecuta o se relaciona con actividades de la ENCA.

## Posibles atributos

* ID.
* Nombre.
* Tipo de actor.
* Organización.
* Sector.
* Región.
* Correo.
* Estado de vinculación.
* Fuente.
* Fecha de actualización.

Estos atributos deben validarse antes de implementarse.

---

# 14. Personas y contactos

La fuente `Respuesta a invitaciones ENCA.xlsx` contiene información de personas,
correos y respuestas.

Por lo tanto, el dominio debe distinguir conceptualmente:

```text
Organización / Institución
        ↓
     Persona
        ↓
     Contacto
```

No asumir que una persona representa siempre a una única organización.

El modelo definitivo debe permitir representar múltiples relaciones si SAO lo
requiere.

---

# 15. Sectores productivos

El Eje 2 está relacionado con sectores productivos y de servicios estratégicos.

El dominio contempla potencialmente:

* Sector productivo.
* Organización.
* Actor.
* Iniciativa de conservación.
* Buenas prácticas.
* Región.

La lista oficial de sectores y su clasificación deben obtenerse de la fuente
oficial de ENCA.

No crear un catálogo arbitrario de sectores.

---

# 16. Iniciativas y proyectos

Los documentos hacen referencia a iniciativas, proyectos y acciones relacionadas
con conservación.

Conceptualmente:

```text
Organización
      ↓
Iniciativa / Proyecto
      ↓
Actividad
      ↓
Indicador
```

Esta estructura es una propuesta conceptual.

Debe validarse con SAO:

* Si iniciativa y proyecto son conceptos diferentes.
* Qué atributos deben tener.
* Cómo se relacionan con los indicadores.
* Cómo se relacionan con los actores.

---

# 17. Conocimiento científico

El Eje 5 está relacionado con la generación, gestión y difusión de conocimiento
para la conservación de las aves.

Dentro de la documentación aparecen conceptos como:

* Investigación.
* Publicaciones científicas.
* Prioridades de investigación.
* Vacíos de conocimiento.
* Recopilación.
* Documentación.
* Almacenamiento.
* Procesamiento.
* Difusión.

Estos conceptos constituyen el dominio conceptual del componente de
conocimiento.

---

# 18. Artículo científico

Un artículo científico representa una publicación potencialmente utilizada en
el análisis bibliométrico.

## Estado

`PENDING_DATA_SOURCE`

El dataset real de artículos todavía no ha sido proporcionado.

## Campos potenciales

Los siguientes campos son únicamente candidatos y deben verificarse cuando se
obtenga el dataset:

* ID.
* Título.
* Abstract.
* Autores.
* Año.
* DOI.
* Revista.
* Palabras clave.
* Instituciones.
* País.
* Citaciones.
* Fuente bibliográfica.

No asumir que estos campos existen.

## Regla

El sistema debe adaptar el modelo a la estructura real del dataset recibido.

No generar artificialmente valores faltantes.

---

# 19. Clasificación bibliométrica

Durante la primera reunión se indicó verbalmente la necesidad de utilizar un
bot para clasificar artículos.

También se mencionaron expresiones como:

* "macro".
* "200 mil".
* "30 mil".
* "ecología".

Actualmente no existe suficiente información para establecer su significado
formal.

## Estado

`PENDING_VALIDATION`

No implementar estas expresiones como categorías del sistema hasta recibir
una definición de SAO.

---

# 20. Clasificación mediante OFC

Una hipótesis de trabajo es que los artículos podrían clasificarse según los
11 Objetos Focales de Conservación.

Conceptualmente:

```text
Artículo científico
       ↓
Clasificador
       ↓
OFC
```

Sin embargo, también son posibles otras estructuras:

```text
Artículo
   ↓
Categoría temática
   ↓
OFC
```

o:

```text
Artículo
   ↓
Múltiples OFC
```

Por esta razón:

`Artículo → OFC = PENDING_VALIDATION`

---

# 21. Análisis bibliométrico

El proyecto contempla análisis bibliométrico sobre un conjunto grande de
información científica.

## Objetivo conceptual

El análisis debe ayudar a comprender la distribución y evolución del
conocimiento relacionado con la conservación de aves.

## Posibles dimensiones

Podrían incluir:

* Evolución temporal.
* Publicaciones por tema.
* Publicaciones por OFC.
* Autores.
* Instituciones.
* Países.
* Revistas.
* Palabras clave.
* Citaciones.
* Colaboraciones.
* Vacíos de conocimiento.

Estas dimensiones son posibilidades y no requisitos confirmados.

## Regla

No implementar métricas bibliométricas específicas hasta conocer las preguntas
que SAO desea responder y los campos disponibles en el dataset.

---

# 22. Dataset

Un dataset representa un conjunto de información utilizado por el sistema.

Debe existir una separación conceptual entre:

```text
Dataset
   ↓
Registros
   ↓
Procesamiento
   ↓
Resultados
```

## Posibles atributos

* ID.
* Nombre.
* Descripción.
* Fuente.
* Fecha de adquisición.
* Fecha de actualización.
* Versión.
* Formato.
* Número de registros.
* Estado.
* Tipo de datos.

La estructura definitiva debe depender de los datasets reales.

---

# 23. Fuente de información

Una fuente identifica el origen de un conjunto de datos.

Ejemplos actuales:

* Documento ENCA 2030.
* Excel de ejes estratégicos.
* Plan de trabajo.
* Plataforma ENCA.
* Futuras fuentes bibliográficas.

## Relación

```text
Fuente
   ↓
Dataset
   ↓
Registros
```

La trazabilidad debe conservarse siempre que sea técnicamente posible.

---

# 24. Metadatos

La documentación sobre integración de información de EPM menciona la necesidad
de considerar metadatos.

Los metadatos pueden incluir:

* Fuente.
* Fecha.
* Método de recopilación.
* Periodicidad.
* Unidad.
* Método.
* Georreferenciación.
* Control de calidad.

No todos estos campos deben convertirse automáticamente en campos obligatorios.

Su implementación depende de los requerimientos finales de integración.

---

# 25. Evidencia

Los indicadores y actividades pueden requerir evidencia para demostrar avances.

La evidencia podría ser:

* Documento.
* Archivo.
* Enlace.
* Registro.
* Informe.
* Publicación.
* Otro soporte.

## Estado

`PENDING_VALIDATION`

Debe definirse con SAO:

* Qué se considera evidencia.
* Cómo se almacena.
* Quién la valida.
* Si debe tener fecha.
* Si debe tener fuente.
* Si debe tener responsable.

---

# 26. Procedencia de datos

La aplicación debe conservar la procedencia de la información siempre que sea
posible.

Conceptualmente:

```text
Dato
 ├── Fuente
 ├── Dataset
 ├── Fecha de incorporación
 ├── Fecha de actualización
 └── Versión
```

Para datos procesados:

```text
Resultado
 ├── Dataset origen
 ├── Pipeline
 ├── Versión del pipeline
 ├── Fecha de procesamiento
 └── Configuración utilizada
```

Esto es especialmente importante para información bibliométrica generada por
procesos automatizados o modelos de IA.

---

# 27. Actualización temporal

La solución debe permitir actualizar información periódicamente y, según lo
indicado en las reuniones, debe ser posible realizar actualizaciones anuales.

La actualización no debe destruir automáticamente los datos históricos.

Conceptualmente:

```text
Información 2026
Información 2027
Información 2028
...
```

La estrategia exacta de versionamiento queda:

`PENDING_VALIDATION`

---

# 28. Capas conceptuales de datos

La solución debe separar los datos originales de los datos transformados.

```text
RAW
 │
 └── Datos originales
       │
       ↓
INTERMEDIATE
 │
 └── Datos temporalmente transformados
       │
       ↓
PROCESSED
 │
 └── Datos normalizados
       │
       ↓
APPLICATION
 │
 └── Datos utilizados por la aplicación
```

La implementación física de estas capas depende de la arquitectura definida
en `tech.md`.

---

# 29. Dashboard

El dashboard debe consumir datos procesados y no depender directamente de los
archivos originales.

Conceptualmente:

```text
Fuentes
   ↓
Ingesta
   ↓
Procesamiento
   ↓
Datos normalizados
   ↓
API / consultas
   ↓
Dashboard
```

## Dimensiones potenciales

El dashboard puede requerir visualización por:

* Eje.
* Meta.
* Indicador.
* Actividad.
* Región.
* Organización.
* OFC.
* Tiempo.

Las dimensiones definitivas dependen del alcance validado con SAO.

---

# 30. Eje 2 — Dominio

El Eje 2 está relacionado con la incidencia en sectores productivos y de
servicios estratégicos.

El dominio incluye potencialmente:

```text
Eje 2
 │
 ├── Metas
 │    └── Indicadores
 │         └── Actividades
 │
 ├── Sectores
 │
 ├── Organizaciones
 │
 ├── Iniciativas
 │
 └── Regiones
```

El alcance exacto que debe implementarse para el Eje 2 está:

`PENDING_VALIDATION`

---

# 31. Eje 5 — Dominio

El Eje 5 está relacionado con:

* Generación de conocimiento.
* Gestión del conocimiento.
* Difusión.
* Investigación.
* Publicaciones.
* Prioridades de investigación.
* Vacíos de conocimiento.

Conceptualmente:

```text
Eje 5
 │
 ├── Investigación
 │
 ├── Publicaciones
 │
 ├── Prioridades
 │
 ├── Vacíos de conocimiento
 │
 └── Gestión de conocimiento
          │
          ↓
    Análisis bibliométrico
```

La relación exacta entre estos elementos debe validarse.

---

# 32. Relación conceptual general

La visión actual del dominio puede representarse como:

```text
                         ENCA 2030
                             │
              ┌──────────────┴──────────────┐
              │                             │
           EJE 2                          EJE 5
              │                             │
      Sectores / Actores              Conocimiento
              │                             │
      Organizaciones                  Investigación
              │                             │
       Iniciativas                    Publicaciones
              │                             │
         Actividades                 Bibliometría
              │                             │
              └──────────────┬──────────────┘
                             │
                       Indicadores
                             │
                         Progreso
                             │
                      ┌──────┴──────┐
                      │             │
                   Región          OFC
```

Este diagrama es conceptual y no representa todavía un esquema físico de
base de datos.

---

# 33. Modelo conceptual simplificado

Las entidades principales identificadas hasta ahora son:

```text
Eje
 └── Meta
      └── Objetivo
           └── Indicador
                └── Actividad

Actividad
 ├── Región
 ├── Organización
 └── Evidencia

Organización
 └── Persona / Contacto

Dataset
 ├── Fuente
 └── Registros

Artículo
 ├── Dataset
 ├── OFC ? 
 ├── Categoría ?
 └── Investigación ?

Investigación
 ├── Prioridad ?
 └── Vacío de conocimiento ?
```

Los elementos marcados con `?` requieren validación.

---

# 34. Reglas de dominio conocidas

## Regla D-001

Los ejes estratégicos contienen metas.

**Estado:** CONFIRMADO.

## Regla D-002

Las metas están asociadas a objetivos SMART.

**Estado:** CONFIRMADO.

## Regla D-003

Los objetivos/elementos estratégicos están asociados con indicadores.

**Estado:** CONFIRMADO.

## Regla D-004

Las actividades forman parte de la estructura de implementación de la ENCA.

**Estado:** CONFIRMADO.

## Regla D-005

La información de progreso puede estar asociada a regiones.

**Estado:** CONFIRMADO COMO ESTRUCTURA DE FUENTE.

## Regla D-006

La ENCA contempla 11 Objetos Focales de Conservación.

**Estado:** CONFIRMADO.

## Regla D-007

Los Ejes 2 y 5 son prioritarios para el alcance actual indicado por SAO.

**Estado:** CONFIRMADO POR REUNIÓN.

## Regla D-008

El proyecto requiere automatización y actualización de información.

**Estado:** CONFIRMADO POR EL RETO Y LAS REUNIONES.

## Regla D-009

El análisis bibliométrico forma parte del trabajo esperado.

**Estado:** CONFIRMADO POR REUNIÓN.

## Regla D-010

La solución debe poder actualizarse periódicamente.

**Estado:** CONFIRMADO COMO OBJETIVO DE DISEÑO.

---

# 35. Reglas que NO están confirmadas

No asumir que:

* Cada artículo pertenece a un único OFC.
* Los OFC son las únicas categorías del clasificador.
* Los 11 OFC constituyen las clases de entrenamiento.
* El dataset contiene 200.000 artículos.
* El dataset contiene 30.000 artículos.
* "200 mil" y "30 mil" representan datasets.
* "Ecología" es una categoría.
* Los artículos contienen abstracts.
* Los artículos tienen DOI.
* Los artículos tienen palabras clave.
* El clasificador utilizará IA generativa.
* El clasificador utilizará machine learning tradicional.
* El procesamiento será exclusivamente local.
* El dashboard tendrá únicamente información bibliométrica.
* La base de datos actual de SAO puede reemplazarse.
* La plataforma ENCA debe reconstruirse.
* Todos los datos del ZIP deben cargarse en la aplicación.

---

# 36. Datos actualmente faltantes

## P0 — Bloqueantes para bibliometría

* Dataset de artículos.
* Fuente del dataset.
* Estructura de registros.
* Definición de categorías.
* Definición de "macro".
* Definición de "200 mil".
* Definición de "30 mil".
* Definición de "ecología".
* Reglas de clasificación.
* Resultado esperado del bot.

## P1 — Necesarios para dashboard

* Indicadores prioritarios.
* Metas prioritarias.
* Definición oficial de progreso.
* Alcance definitivo de Eje 2.
* Alcance definitivo de Eje 5.
* Requisitos de visualización.

## P2 — Necesarios para actores

* Modelo oficial de actores.
* Tipos de organización.
* Sectores.
* Estados de vinculación.
* Historial de interacción.

## P3 — Integraciones

* Plataforma ENCA.
* Base de datos existente.
* API.
* Repositorios externos.
* Fuentes futuras.

---

# 37. Estrategia frente a datos faltantes

La ausencia actual del dataset bibliométrico NO bloquea el desarrollo inicial.

El sistema debe desarrollarse utilizando:

* Datos reales actualmente disponibles.
* Datos de prueba claramente identificados.
* Esquemas flexibles.
* Interfaces desacopladas.
* Contratos de datos explícitos.

No utilizar datos ficticios como si fueran datos reales de SAO.

Cuando se necesite probar una funcionalidad sin datos reales, utilizar fixtures o
datasets sintéticos claramente marcados como:

`DEMO_DATA`

No presentar datos sintéticos como resultados reales.

---

# 38. Estado del dominio

## Confirmado

* ENCA 2030.
* Ejes estratégicos.
* Metas.
* Objetivos SMART.
* Indicadores.
* Actividades.
* Regiones.
* Progreso regional en las fuentes disponibles.
* Actores.
* Información de investigación.
* Publicaciones científicas como parte del contexto del Eje 5.
* 11 OFC.
* Relevancia de Eje 2 y Eje 5.
* Necesidad de automatización.
* Necesidad de actualización periódica.
* Necesidad de análisis bibliométrico.

## Inferido

* Posible relación artículo → OFC.
* Posible uso de OFC como clasificación.
* Posible visualización por región.
* Posible modelado estructurado de actores.
* Posible versionamiento anual.
* Necesidad de trazabilidad de datos.

## Pendiente

* Dataset bibliométrico.
* Clasificación bibliométrica.
* Métricas.
* Fuente oficial de artículos.
* Plataforma ENCA.
* Repositorio existente.
* Modelo definitivo de actores.
* Indicadores prioritarios.
* Alcance exacto del MVP.

---

# 39. Dependencias con otros documentos de Kiro

Este documento debe utilizarse conjuntamente con:

* `product.md`
* `tech.md`
* `structure.md`
* `data-inventory.md`

## Responsabilidades

### product.md

Define:

**Qué producto se está construyendo y para quién.**

### data-inventory.md

Define:

**Qué fuentes de información existen actualmente.**

### data-and-domain.md

Define:

**Qué significa esa información y cómo se relaciona.**

### tech.md

Define:

**Con qué tecnologías se implementará.**

### structure.md

Define:

**Cómo se organiza el código y los componentes del sistema.**

---

# 40. Próxima actualización

Este documento debe actualizarse cuando SAO proporcione:

1. Dataset bibliométrico.
2. Definiciones de clasificación.
3. Acceso a la plataforma ENCA.
4. Información sobre el repositorio existente.
5. Indicadores prioritarios.
6. Alcance definitivo de Ejes 2 y 5.

La actualización debe conservar las decisiones anteriores y documentar los
cambios importantes.

No eliminar información histórica sin justificar el cambio.
