# Data Inventory — SAO ENCA 2030

## 1. Propósito

Este documento registra y clasifica las fuentes de información disponibles para
el proyecto de seguimiento, análisis y gestión de información de la Estrategia
Nacional para la Conservación de las Aves (ENCA 2030).

Su objetivo es:

* Identificar las fuentes de información disponibles.
* Registrar su formato y estructura.
* Identificar posibles entidades y campos.
* Diferenciar datos de aplicación, datos de referencia y documentación.
* Registrar la procedencia de cada fuente.
* Identificar posibles relaciones entre fuentes.
* Identificar información faltante.
* Evitar asumir información que no haya sido confirmada.
* Servir como entrada para el diseño posterior del modelo de datos.
* Servir como referencia para las especificaciones de Kiro.

## 2. Regla fundamental

Este inventario distingue entre:

### Confirmado

Información observada directamente en los archivos proporcionados por SAO.

### Inferido

Relaciones o posibles usos que pueden deducirse razonablemente de la
estructura de los datos, pero que todavía no constituyen requisitos confirmados.

### Pendiente de validación

Información que debe ser confirmada directamente con SAO antes de convertirla
en una regla del sistema.

Kiro no debe transformar información inferida o pendiente en requisitos
obligatorios sin validación.

---

# 3. Fuente original del inventario

## 3.1 Material recibido

Fuente:

`Avances ENCA a 2026-20260928T223101Z-1-001(1).zip`

Tipo:

ZIP

Contenido:

11 archivos.

El material contiene:

* 5 archivos Excel.
* 2 archivos Word relacionados con planificación/documentación.
* 1 archivo Word de peticiones al Comité Ejecutivo.
* 1 archivo PDF sobre ENCA 2030.
* 1 archivo PowerPoint sobre avances de ENCA y EPM.

Los archivos originales deben considerarse material de referencia proporcionado
por SAO.

No modificar los archivos originales.

---

# 4. Clasificación de fuentes

Las fuentes se clasifican en cuatro categorías:

| Categoría        | Descripción                                                         |
| ---------------- | ------------------------------------------------------------------- |
| APPLICATION_DATA | Información potencialmente utilizada directamente por la aplicación |
| REFERENCE_DATA   | Información de referencia o catálogos                               |
| CONTEXT_DOCUMENT | Documentación utilizada para comprender el dominio y el contexto    |
| PENDING          | Información que debe obtenerse o validarse                          |

---

# 5. Inventario general

| ID       | Fuente                                             | Formato | Categoría        | Estado     |
| -------- | -------------------------------------------------- | ------- | ---------------- | ---------- |
| DATA-001 | Tabla Ejes Estratégicos _ENCA2030                  | XLSX    | APPLICATION_DATA | Disponible |
| DATA-002 | Ejes Estratégicos a Enfocar                        | XLSX    | APPLICATION_DATA | Disponible |
| DATA-003 | Ejes estratégicos ENCA                             | XLSX    | APPLICATION_DATA | Disponible |
| DATA-004 | Cosas pendientes                                   | XLSX    | CONTEXT_DOCUMENT | Disponible |
| DATA-005 | Respuesta a invitaciones ENCA                      | XLSX    | REFERENCE_DATA   | Disponible |
| DATA-006 | Plan de trabajo                                    | XLSX    | CONTEXT_DOCUMENT | Disponible |
| DATA-007 | Peticiones específicas a Comité Ejecutivo          | DOCX    | CONTEXT_DOCUMENT | Disponible |
| DATA-008 | Plan de acción                                     | DOCX    | CONTEXT_DOCUMENT | Disponible |
| DATA-009 | ENCA 2030 corto Colombia País de las Aves          | PDF     | CONTEXT_DOCUMENT | Disponible |
| DATA-010 | Informe ENCA — Sociedad Antioqueña de Ornitología  | DOCX    | CONTEXT_DOCUMENT | Disponible |
| DATA-011 | ¿Cómo vamos con la ENCA — EPM?                     | PPTX    | CONTEXT_DOCUMENT | Disponible |
| DATA-012 | Dataset bibliométrico principal                    | TBD     | APPLICATION_DATA | PENDIENTE  |
| DATA-013 | Definiciones de clasificación bibliométrica        | TBD     | REFERENCE_DATA   | PENDIENTE  |
| DATA-014 | Fuente actual de información de la plataforma ENCA | TBD     | APPLICATION_DATA | PENDIENTE  |
| DATA-015 | Base de datos/repositorio ENCA existente           | TBD     | APPLICATION_DATA | PENDIENTE  |

---

# 6. DATA-001 — Tabla Ejes Estratégicos _ENCA2030

## Identificación

Archivo:

`Copia de Tabla Ejes Estratégicos _ENCA2030.xlsx`

Hoja:

`METAS ENCA2030`

Formato:

XLSX

Categoría:

APPLICATION_DATA

Estado:

Disponible.

## Estructura observada

La hoja contiene aproximadamente 99 filas y 8 columnas.

Las columnas observadas corresponden conceptualmente a:

* Línea estratégica ENCA 2030.
* Metas.
* Objetivo SMART.
* Indicadores.
* Actividades.

También existen columnas auxiliares/espacios vacíos derivados de la estructura
del Excel.

## Entidades potenciales

* Eje estratégico.
* Meta.
* Objetivo SMART.
* Indicador.
* Actividad.

## Relación potencial

La estructura observada permite representar:

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

Esta relación es una representación conceptual del contenido observado y debe
validarse antes de convertirse en el esquema definitivo de base de datos.

## Uso potencial

Esta fuente puede constituir una de las principales fuentes de información
para:

* Catálogo de ejes.
* Catálogo de metas.
* Indicadores.
* Actividades.
* Seguimiento del cumplimiento de la ENCA.

---

# 7. DATA-002 — Ejes Estratégicos a Enfocar

## Identificación

Archivo:

`Copia de Ejes Estratégicos a Enfocar.xlsx`

Hoja:

`METAS ENCA2030`

Formato:

XLSX

Categoría:

APPLICATION_DATA

Estado:

Disponible.

## Estructura observada

Presenta una estructura equivalente a la tabla de ejes estratégicos, con
información relacionada con:

* Líneas estratégicas.
* Metas.
* Objetivos SMART.
* Indicadores.
* Actividades.

## Uso potencial

Este archivo parece representar una versión enfocada de la información
estratégica.

Sin embargo, todavía debe confirmarse con SAO:

* Si constituye una versión oficial.
* Si reemplaza al archivo DATA-001.
* Si representa únicamente los ejes priorizados para el proyecto.
* Qué diferencias existen entre esta fuente y DATA-001.

## Regla

No combinar automáticamente DATA-001 y DATA-002.

Primero debe establecerse cuál es la fuente de verdad y cuál es una versión
derivada.

---

# 8. DATA-003 — Ejes estratégicos ENCA

## Identificación

Archivo:

`Copia de Ejes estratégicos ENCA.xlsx`

Hoja:

`Hoja 1`

Formato:

XLSX

Categoría:

APPLICATION_DATA

Estado:

Disponible.

## Estructura observada

La hoja contiene aproximadamente 90 filas y 19 columnas.

Además de la estructura estratégica, contiene columnas relacionadas con progreso
regional.

Columnas observadas:

* Línea estratégica ENCA 2030.
* Meta.
* Objetivo SMART.
* Indicadores.
* Actividades.
* Progreso región Andina.
* Progreso región Caribe.
* Progreso región Insular.
* Progreso región Orinoquía.
* Progreso región Pacífico.
* Progreso región Amazonía.
* Necesitamos aumentar esfuerzos.

También existen columnas auxiliares sin nombre explícito.

## Entidades potenciales

* Eje estratégico.
* Meta.
* Objetivo SMART.
* Indicador.
* Actividad.
* Región.
* Estado/progreso regional.
* Necesidad de aumentar esfuerzos.

## Posible modelo conceptual

```text
Eje
  ↓
Meta
  ↓
Objetivo SMART
  ↓
Indicador
  ↓
Actividad
  ↓
Progreso por región
```

La relación entre actividad e información regional debe validarse.

## Uso potencial

Esta fuente es especialmente relevante para el futuro dashboard porque
contiene información que podría utilizarse para visualizar:

* Avance por eje.
* Avance por meta.
* Avance por actividad.
* Información por región.
* Necesidades de aumentar esfuerzos.

---

# 9. DATA-004 — Cosas pendientes

## Identificación

Archivo:

`Copia de Cosas pendientes.xlsx`

Hojas:

* `Sheet1`
* `Notas - Reuniones`

Formato:

XLSX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Hoja `Sheet1`

Columnas:

* Pendiente.
* ¿Para cuándo?
* ¿Dónde?

Contiene aproximadamente 88 registros.

## Hoja `Notas - Reuniones`

Columnas:

* Reunión.
* Fecha.
* Notas.

Contiene aproximadamente 12 registros.

## Uso

Este archivo debe considerarse principalmente documentación de gestión y
contexto.

No cargar automáticamente estos registros como datos de producción.

## Riesgo

Los pendientes y notas pueden estar desactualizados.

Antes de utilizar alguna información como requisito vigente debe verificarse
con SAO.

---

# 10. DATA-005 — Respuesta a invitaciones ENCA

## Identificación

Archivo:

`Copia de Respuesta a invitaciones ENCA.xlsx`

Hojas:

* `Comité ejecutivo`
* `Academia`

Formato:

XLSX

Categoría:

REFERENCE_DATA

Estado:

Disponible.

## Hoja Comité ejecutivo

Campos observados:

* Nombre.
* Correo.
* Respuesta positiva.

## Hoja Academia

Campos observados:

* Nombre.
* Correo.
* Respuesta positiva.

También aparecen estados relacionados con:

* Respuesta positiva.
* Respuesta negativa.
* Sin respuesta.

## Entidades potenciales

* Persona.
* Organización/institución.
* Grupo de actores.
* Estado de respuesta.
* Contacto.

## Uso potencial

Puede servir como fuente inicial para el componente de actores y contactos.

## Advertencia

No asumir que:

```text
persona = organización
```

ni que el estado de respuesta representa necesariamente el estado actual de
vinculación a la ENCA.

Debe definirse con SAO el modelo oficial de actores.

---

# 11. DATA-006 — Plan de trabajo

## Identificación

Archivo:

`Copia de Plan de trabajo.xlsx`

Hojas:

* `Plan de trabajo`
* `Cronograma`
* `Hoja 3`

Formato:

XLSX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Hoja Plan de trabajo

Campos observados:

* Fecha.
* Actividad.
* Responsable.
* Descripción general.
* Actividades específicas a realizar.

## Actividades identificadas

Entre otras:

* Encuesta y Línea Base.
* Revisión de la Plataforma y Contactos Sectoriales.
* Incorporación de Contenidos.
* Búsqueda de Recursos y Grants.

## Hoja Cronograma

Representa la planificación semanal de las actividades.

## Hoja Hoja 3

Representa una planificación mensual.

## Uso

Principalmente contextual.

Puede servir para comprender el proceso que originó los datos actuales.

No asumir que este cronograma representa el cronograma actual del software.

---

# 12. DATA-007 — Peticiones específicas a Comité Ejecutivo

## Identificación

Archivo:

`Copia de Peticiones especificas a Comité Ejecutivo.docx`

Formato:

DOCX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Contenido observado

Contiene solicitudes y líneas de trabajo relacionadas con diferentes actores.

Entre los temas aparecen:

* Colombia BirdFair.
* Aviturismo.
* Universidad Javeriana.
* Investigación.
* Prioridades de investigación.
* Vacíos de conocimiento.
* Publicaciones científicas.
* Especies amenazadas.
* Información necesaria para decisiones de conservación.
* Sectores productivos.
* Articulación con actores.

## Importancia

Este documento es particularmente relevante para comprender las necesidades
del Eje 2 y Eje 5.

También contiene una pregunta explícita sobre cómo medir la cantidad de
publicaciones científicas.

## Uso

Debe utilizarse como fuente de contexto para definir requisitos, no como
dataset estructurado de producción.

---

# 13. DATA-008 — Plan de acción

## Identificación

Archivo:

`Copia de Plan de acción.docx`

Formato:

DOCX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Contenido observado

El documento describe actividades de coordinación de la actualización de la
ENCA 2030.

Entre ellas:

### Encuesta y Línea Base

Incluye:

* Definir línea base.
* Actualizar información de la plataforma.
* Encuesta.
* Mapeo.
* Análisis utilizando Antioquia como modelo.
* Revisión de Valores Objeto de Conservación.
* Mapear guías de aves publicadas.
* Compilar patrocinadores y financiadores.
* Identificar vacíos en el cumplimiento.
* Definir periodicidad de actualización.
* Actualizar organizaciones aliadas.
* Contactar sectores productivos.

### Revisión de plataforma y contactos sectoriales

Incluye:

* Detectar fallos de la plataforma.
* Contactar actores.
* Organizar talleres.
* Grupos de investigación.
* Museos.
* Colecciones ornitológicas.
* Semilleros de investigación.
* Grupos de investigación enfocados en ornitología.

## Importancia

Este documento evidencia que la plataforma ENCA ya tenía un proceso de
actualización y que existen múltiples tipos de información relacionados.

---

# 14. DATA-009 — ENCA 2030

## Identificación

Archivo:

`Copia de ENCA 2030 corto COLOMBIA PAIS DE LAS AVES.pdf`

Formato:

PDF

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Uso

Documento de referencia para comprender:

* ENCA 2030.
* Objetivos.
* Ejes estratégicos.
* Objetos Focales de Conservación.
* Contexto nacional.
* Conservación de aves.

## Objetos Focales de Conservación

El proyecto debe manejar los 11 OFC definidos por la documentación de ENCA.

La lista debe considerarse información de referencia del dominio y no debe
alterarse sin consultar una fuente oficial.

Los 11 OFC identificados en la documentación son:

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

## Uso potencial

Los OFC pueden constituir una entidad de referencia para:

* Clasificación de artículos.
* Clasificación de investigaciones.
* Análisis bibliométrico.
* Filtros.
* Dashboard.
* Análisis de conocimiento.

Sin embargo, la relación:

```text
Artículo → OFC
```

todavía debe ser confirmada como requisito oficial del sistema.

---

# 15. DATA-010 — Informe ENCA — Sociedad Antioqueña de Ornitología

## Identificación

Archivo:

`Copia de Informe ENCA - Sociedad Antioqueña de Ornitología.docx`

Formato:

DOCX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Contenido

El documento describe el trabajo de coordinación de la ENCA realizado por SAO.

Contiene información sobre:

* Historia de la ENCA.
* ENCA 2030.
* Participación de actores.
* Coordinación.
* Recopilación de información.
* Divulgación.
* Diálogos intersectoriales.
* Actividades de SAO.
* Avances.
* Línea base.
* Actores.
* Plataforma.
* Información de conservación.

## Importancia

Es una de las principales fuentes de contexto del proyecto.

Debe utilizarse para comprender el dominio y validar interpretaciones realizadas
sobre otros archivos.

---

# 16. DATA-011 — ¿Cómo vamos con la ENCA — EPM?

## Identificación

Archivo:

`¿Como vamos con la ENCA - EPM.pptx`

Formato:

PPTX

Categoría:

CONTEXT_DOCUMENT

Estado:

Disponible.

## Contenido relevante

La presentación describe:

* ENCA.
* Ejes estratégicos.
* Cronología de la estrategia.
* Línea base.
* Actividades.
* Contactos sectoriales.
* Información recopilada.
* Actualización de plataforma.
* Integración de información de EPM.

## Integración de información

La presentación plantea integrar información de EPM a un repositorio ENCA.

Aparecen conceptos relacionados con:

* Monitoreos.
* Estudios de fauna.
* Informes.
* Georreferenciación.
* Métodos.
* Periodicidad.
* Unidades.
* Control de calidad.
* Metadatos.
* Plantillas.
* Repositorio común.
* Puntos focales de información.

## Importancia

Esto constituye una evidencia importante de que la arquitectura de datos debe
considerar la procedencia y los metadatos de la información.

---

# 17. DATA-012 — Dataset bibliométrico principal

## Estado

PENDIENTE.

No se identificó dentro del ZIP un dataset estructurado que permita confirmar
el conjunto de artículos mencionado verbalmente en las reuniones.

## Información que falta

Se debe obtener:

* Archivo o ubicación del dataset.
* Fuente original.
* Tamaño.
* Formato.
* Fecha de actualización.
* Cobertura temporal.
* Campos disponibles.
* Identificadores.
* Criterios de selección.
* Posibles duplicados.
* Idiomas.
* Fuentes bibliográficas.

## Campos que deben verificarse

No asumir que todos existen.

Posibles campos:

* ID.
* Título.
* Abstract/resumen.
* Autores.
* Año.
* DOI.
* Revista.
* Palabras clave.
* Fuente bibliográfica.
* País.
* Región.
* Institución.
* Citaciones.
* Categorías existentes.

---

# 18. DATA-013 — Definiciones de clasificación bibliométrica

## Estado

PENDIENTE.

Durante la reunión se mencionó verbalmente la clasificación de artículos y
categorías como:

* macro;
* aproximadamente 200.000;
* aproximadamente 30.000;
* ecología.

Estas categorías no deben convertirse todavía en entidades o reglas del
sistema porque su significado exacto no está documentado en las fuentes
analizadas.

## Información requerida

SAO debe confirmar:

1. ¿Qué significa "macro"?
2. ¿Qué representa el conjunto de aproximadamente 200.000 artículos?
3. ¿Qué representa el conjunto de aproximadamente 30.000 artículos?
4. ¿Qué significa "ecología"?
5. ¿Son categorías jerárquicas?
6. ¿Son datasets independientes?
7. ¿Son filtros?
8. ¿Son etapas del pipeline?
9. ¿Un artículo puede pertenecer a múltiples categorías?
10. ¿Cuál es la clasificación final esperada?

---

# 19. DATA-014 — Información actual de la plataforma ENCA

## Estado

PENDIENTE.

Los documentos analizados mencionan una plataforma ENCA y su actualización,
pero no se dispone todavía de la estructura técnica completa de la plataforma.

## Información requerida

Se debe obtener, si existe:

* URL.
* Acceso.
* Base de datos.
* API.
* Exportaciones.
* Esquema de datos.
* Formatos.
* Catálogos.
* Periodicidad de actualización.
* Responsable.
* Información que actualmente contiene.
* Información que debe migrarse.
* Información que debe mantenerse únicamente como referencia.

## Regla

No recrear información de la plataforma ENCA desde cero si existe una fuente
estructurada reutilizable.

Primero debe evaluarse la posibilidad de integrar o importar la información
existente.

---

# 20. DATA-015 — Base de datos/repositorio ENCA existente

## Estado

PENDIENTE.

Los documentos mencionan información agrupada y un repositorio/plataforma ENCA,
pero no se ha confirmado técnicamente:

* Tecnología.
* Motor de base de datos.
* Estructura.
* Ubicación.
* Responsable.
* Acceso.
* Formatos de exportación.

## Información requerida

Preguntar a SAO:

> ¿Existe actualmente una base de datos estructurada detrás de la plataforma
> ENCA?

Si existe:

* ¿Qué motor utiliza?
* ¿Podemos acceder a un dump?
* ¿Existe una API?
* ¿Existe exportación CSV/Excel/JSON?
* ¿Qué tablas/entidades contiene?
* ¿Cuál es la fuente de verdad?

---

# 21. Entidades identificadas hasta el momento

A partir del material disponible se identifican las siguientes entidades
potenciales.

## Entidades de estrategia

* Eje estratégico.
* Meta.
* Objetivo SMART.
* Indicador.
* Actividad.

## Entidades geográficas

* Región.
* Departamento.
* Posiblemente área protegida.

## Entidades de conservación

* Objeto Focal de Conservación.
* Especie.
* Hábitat/ecosistema.
* Valor Objeto de Conservación.

## Entidades de actores

* Organización.
* Persona/contacto.
* Sector.
* Grupo de investigación.
* Institución académica.
* Comité.
* Actor regional.

## Entidades de conocimiento

* Artículo científico.
* Publicación.
* Investigación.
* Prioridad de investigación.
* Vacío de conocimiento.

## Entidades de gestión

* Iniciativa.
* Proyecto.
* Actividad.
* Evento.
* Webinar.
* Congreso.
* Festival.
* Reunión.

## Entidades de datos

* Dataset.
* Fuente.
* Metadato.
* Importación.
* Versión.
* Fecha de actualización.

Estas entidades son una lista de descubrimiento y NO representan todavía el
modelo definitivo de base de datos.

---

# 22. Relaciones potenciales

Las siguientes relaciones son hipótesis de modelado que deben validarse.

```text
Eje
 └── contiene → Meta
       └── tiene → Objetivo SMART
             └── se mide mediante → Indicador
                   └── se implementa mediante → Actividad
```

```text
Actividad
 └── puede estar relacionada con → Organización
                         └── Persona/contacto
```

```text
Actividad
 └── puede tener → Región
```

```text
Artículo
 └── puede relacionarse con → OFC
```

```text
Artículo
 └── puede pertenecer a → Prioridad de investigación
```

```text
Artículo
 └── puede aportar evidencia para → Vacío de conocimiento
```

```text
Dataset
 └── contiene → Artículos
```

```text
Dataset
 └── proviene de → Fuente
```

```text
Fuente
 └── tiene → Metadatos
```

Estas relaciones no deben implementarse como reglas obligatorias hasta ser
validadas.

---

# 23. Arquitectura conceptual de datos

La información actualmente disponible sugiere separar las fuentes en capas.

```text
FUENTES ORIGINALES
        │
        ├── Excel
        ├── Word
        ├── PDF
        ├── PowerPoint
        └── Futuras fuentes bibliográficas
                │
                ↓
          INGESTA / RAW
                │
                ↓
       NORMALIZACIÓN
                │
                ↓
       DATOS PROCESADOS
                │
                ├── ENCA
                ├── Actores
                ├── Regiones
                ├── Indicadores
                ├── Actividades
                └── Bibliometría
                        │
                        ↓
                  BASE DE DATOS
                        │
                        ↓
                     API
                        │
                        ↓
                   DASHBOARD
```

Esta arquitectura es conceptual.

No implica todavía la adopción de una tecnología específica de Data Lake,
Lakehouse o base de datos.

---

# 24. Fuentes de verdad

Todavía no se ha definido una fuente de verdad única para cada dominio.

Debe establecerse posteriormente:

| Dominio                     | Fuente actual                | Fuente de verdad          |
| --------------------------- | ---------------------------- | ------------------------- |
| Ejes ENCA                   | Excel                        | PENDIENTE                 |
| Metas                       | Excel                        | PENDIENTE                 |
| Indicadores                 | Excel                        | PENDIENTE                 |
| Actividades                 | Excel/Plan de acción         | PENDIENTE                 |
| Progreso regional           | Excel                        | PENDIENTE                 |
| Actores                     | Excel/documentos             | PENDIENTE                 |
| OFC                         | Documento ENCA 2030          | PENDIENTE DE CONFIRMACIÓN |
| Artículos                   | No identificado              | PENDIENTE                 |
| Clasificación bibliométrica | No identificado              | PENDIENTE                 |
| Plataforma ENCA             | Plataforma existente         | PENDIENTE                 |
| Repositorio ENCA            | No identificado técnicamente | PENDIENTE                 |

---

# 25. Requisitos de trazabilidad

Cada dato incorporado al sistema debería poder asociarse, cuando sea posible,
con su procedencia.

Conceptualmente:

```text
Dato
 │
 ├── Fuente
 ├── Dataset
 ├── Fecha de incorporación
 ├── Fecha de actualización
 └── Versión
```

Para información procesada:

```text
Resultado
 │
 ├── Dataset original
 ├── Pipeline utilizado
 ├── Versión del pipeline
 ├── Fecha de procesamiento
 └── Configuración/modelo utilizado
```

Esto es especialmente importante para el análisis bibliométrico.

---

# 26. Actualización anual

Durante las reuniones se indicó que la herramienta debe poder utilizarse para
actualizar la información cada año.

Por lo tanto, la arquitectura debe evitar procesos destructivos.

No sobrescribir automáticamente los datos históricos.

Preferir:

```text
Dataset 2026
Dataset 2027
Dataset 2028
...
```

o un modelo versionado equivalente.

La estrategia definitiva de versionamiento debe definirse posteriormente.

---

# 27. Datos originales vs datos procesados

Debe mantenerse una separación clara:

```text
RAW
│
└── Información original proporcionada por SAO
        ↓
INTERIM
│
└── Información transformada temporalmente
        ↓
PROCESSED
│
└── Información normalizada y procesada
        ↓
CURATED / APPLICATION
│
└── Información preparada para consultas y dashboard
```

Los datos RAW no deben modificarse.

---

# 28. Información que NO debe inventarse

El sistema y sus agentes de desarrollo no deben asumir sin evidencia:

* significado de categorías bibliométricas;
* tamaño exacto de datasets no entregados;
* campos que no hayan sido observados;
* relación automática entre artículos y OFC;
* algoritmo de clasificación;
* fuente bibliográfica;
* frecuencia de actualización;
* estructura de la plataforma ENCA;
* arquitectura de la base de datos existente;
* definición exacta de "macro";
* significado de "200 mil";
* significado de "30 mil";
* significado de "ecología".

Cuando una especificación no esté confirmada debe marcarse como:

`PENDING_VALIDATION`

---

# 29. Preguntas prioritarias para SAO

## 29.1 Dataset bibliométrico

1. ¿Dónde está el dataset de artículos que se mencionó en la reunión?
2. ¿Qué representa el conjunto de aproximadamente 200.000 registros?
3. ¿Qué representa el conjunto de aproximadamente 30.000 registros?
4. ¿Cuál es la fuente de estos artículos?
5. ¿Son artículos científicos, documentos, publicaciones u otro tipo de
   registro?
6. ¿Qué período temporal cubren?
7. ¿Qué campos contiene cada registro?
8. ¿Existe DOI?
9. ¿Existe resumen/abstract?
10. ¿Existen palabras clave?
11. ¿Existen autores?
12. ¿Existe información de revista?
13. ¿Existe información de citaciones?
14. ¿Existen registros duplicados?

## 29.2 Clasificación

15. ¿Qué significa exactamente "macro"?
16. ¿Qué significa "ecología"?
17. ¿Las categorías son jerárquicas?
18. ¿Un artículo puede pertenecer a múltiples categorías?
19. ¿Quién define la clasificación correcta?
20. ¿Existe un conjunto de artículos ya clasificados manualmente?
21. ¿Existe un dataset de entrenamiento/validación?
22. ¿Los 11 OFC son las categorías finales del clasificador?
23. ¿Un artículo puede pertenecer a varios OFC?
24. ¿Qué debe devolver exactamente el bot?

## 29.3 Bibliometría

25. ¿Qué preguntas de negocio debe responder el análisis bibliométrico?
26. ¿Qué métricas necesita SAO?
27. ¿Necesitan analizar evolución temporal?
28. ¿Necesitan analizar autores?
29. ¿Necesitan analizar instituciones?
30. ¿Necesitan analizar revistas?
31. ¿Necesitan analizar redes de colaboración?
32. ¿Necesitan analizar palabras clave?
33. ¿Necesitan identificar vacíos de conocimiento?
34. ¿Cómo se determina que existe un vacío de conocimiento?

## 29.4 ENCA y plataforma

35. ¿Cuál es actualmente la plataforma ENCA?
36. ¿Dónde está alojada?
37. ¿Existe una base de datos detrás de ella?
38. ¿Existe API?
39. ¿Existe exportación?
40. ¿Podemos acceder a la estructura de datos existente?
41. ¿Qué información debe reutilizarse?
42. ¿Qué información debe actualizarse?
43. ¿Qué información debe permanecer histórica?

## 29.5 Ejes 2 y 5

44. ¿El proyecto debe cubrir exclusivamente Eje 2 y Eje 5?
45. ¿Qué parte exacta del Eje 2 se debe implementar?
46. ¿Qué parte exacta del Eje 5 se debe implementar?
47. ¿Qué indicadores específicos son prioritarios?
48. ¿Qué metas deben aparecer en el dashboard?
49. ¿Qué actividades deben poder registrarse?
50. ¿Qué información regional debe visualizarse?

## 29.6 Actores

51. ¿Qué se considera un actor vinculado a la ENCA?
52. ¿Qué diferencia existe entre organización, institución, persona y sector?
53. ¿Qué información mínima debe almacenarse de cada actor?
54. ¿Debe registrarse el estado de vinculación?
55. ¿Debe registrarse el historial de contactos?
56. ¿Debe registrarse la participación en actividades?

---

# 30. Prioridad de adquisición de datos

La información faltante debe priorizarse de la siguiente manera:

## Prioridad P0 — Bloqueante

Sin esta información no se puede diseñar correctamente el componente
bibliométrico:

* Dataset de artículos.
* Definición de categorías.
* Definición del resultado esperado del clasificador.
* Definición de la relación artículo ↔ OFC.

## Prioridad P1 — Alta

Necesaria para diseñar el dashboard:

* Indicadores prioritarios.
* Metas prioritarias.
* Ejes 2 y 5 definitivos.
* Definición de progreso.
* Estructura regional.

## Prioridad P2 — Media

Necesaria para el módulo de actores:

* Modelo de organización.
* Modelo de contactos.
* Estado de vinculación.
* Historial de actividades.

## Prioridad P3 — Posterior

Información que puede incorporarse durante fases posteriores:

* Integraciones externas.
* Automatizaciones avanzadas.
* Fuentes adicionales.
* Funcionalidades de colaboración.

---

# 31. Estado actual del conocimiento

## Confirmado

* Existe la ENCA 2030.
* Existen ejes estratégicos.
* Existen metas.
* Existen objetivos SMART.
* Existen indicadores.
* Existen actividades.
* Existen datos de progreso regional en una de las fuentes.
* Existen actores/contactos.
* Existe documentación de línea base.
* Existe una plataforma ENCA mencionada en los documentos.
* Existe información relacionada con investigación y publicaciones.
* Existen 11 Objetos Focales de Conservación.
* Los Ejes 2 y 5 son relevantes para el trabajo indicado en las reuniones.

## Inferido

* Puede ser útil modelar ejes, metas, indicadores y actividades como entidades
  relacionadas.
* Los OFC podrían utilizarse en la clasificación bibliométrica.
* El dashboard podría visualizar progreso regional.
* Los actores podrían convertirse en entidades estructuradas.
* La trazabilidad de fuentes será importante.
* El procesamiento bibliométrico debería estar separado de la interfaz.

## Pendiente

* Dataset bibliométrico.
* Definición de clasificación.
* Relación artículo-OFC.
* Métricas bibliométricas.
* Fuente de verdad de la plataforma.
* Arquitectura actual del repositorio ENCA.
* Alcance definitivo del MVP.
* Indicadores prioritarios.
* Modelo definitivo de actores.

---

# 32. Decisión provisional de arquitectura de datos

No se adoptará todavía una arquitectura Lakehouse específica.

Primero deben completarse:

1. Inventario de datos.
2. Acceso al dataset bibliométrico.
3. Identificación de fuentes de verdad.
4. Definición del volumen real.
5. Identificación de formatos.
6. Requisitos de actualización.
7. Requisitos de consulta.
8. Requisitos de procesamiento.

Después de completar estas actividades se evaluarán alternativas como:

* Base de datos relacional.
* DuckDB.
* Parquet.
* PostgreSQL.
* Data Lake.
* Lakehouse.
* Arquitectura híbrida.

La decisión debe basarse en los requisitos reales y no en la adopción
anticipada de una tecnología.

---

# 33. Próximo paso

Una vez validada la información faltante con SAO, este inventario debe utilizarse
como entrada para construir:

```text
data-and-domain.md
        ↓
Modelo conceptual
        ↓
Modelo de datos
        ↓
Arquitectura
        ↓
Specs de Kiro
```

No implementar el modelo definitivo de base de datos hasta resolver las
preguntas P0 y P1.
