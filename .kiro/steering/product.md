# Product Steering — SAO ENCA 2030

## 1. Contexto del proyecto

Este proyecto se desarrolla en el marco de una Inmersión de Talento EAFIT con la Sociedad Antioqueña de Ornitología (SAO), con el propósito de apoyar el seguimiento y análisis de la Estrategia Nacional para la Conservación de las Aves (ENCA), con énfasis en las estrategias y líneas de trabajo definidas por SAO para Antioquia.

La solución debe apoyar procesos de organización, actualización, análisis, clasificación y visualización de información relacionada con la conservación de aves.

El proyecto debe partir de la información, documentos, indicadores, fuentes y criterios proporcionados por SAO. No se deben inventar datos, indicadores, categorías, relaciones, resultados ni interpretaciones que no estén respaldadas por información proporcionada o validada por SAO.

---

## 2. Problema que se busca resolver

SAO trabaja con grandes cantidades de información proveniente de diferentes fuentes, documentos, organizaciones y publicaciones científicas.

Actualmente existe la necesidad de:

- Consolidar información relevante en estructuras organizadas.
- Facilitar la actualización periódica de la información.
- Analizar grandes volúmenes de información científica.
- Clasificar artículos científicos de acuerdo con criterios relacionados con la conservación de aves.
- Relacionar información científica con los Objetos Focales de Conservación (OFC).
- Facilitar la consulta y análisis de los resultados.
- Reducir tareas manuales y repetitivas mediante automatización.
- Mantener trazabilidad sobre el origen de los datos y los resultados obtenidos.

La solución debe permitir que el proceso sea reproducible y que pueda actualizarse periódicamente, especialmente cuando se incorporen nuevos datos o publicaciones en años posteriores.

---

## 3. Objetivo general del producto

Desarrollar una herramienta que permita a SAO organizar, procesar, analizar, clasificar y visualizar información relevante para el seguimiento de la conservación de aves, apoyando particularmente el análisis bibliométrico y la clasificación de publicaciones científicas relacionadas con los Objetos Focales de Conservación.

La herramienta debe reducir el trabajo manual, facilitar la actualización anual de la información y proporcionar resultados trazables que puedan ser revisados y utilizados por el equipo de SAO.

---

## 4. Objetivos específicos

La solución debe buscar:

1. Organizar los datos proporcionados por SAO en estructuras consistentes y consultables.

2. Facilitar la incorporación de nuevos datos sin necesidad de reconstruir todo el proceso.

3. Procesar grandes volúmenes de publicaciones científicas de manera eficiente.

4. Automatizar, en la medida técnicamente viable, la clasificación de artículos científicos.

5. Clasificar las publicaciones utilizando los criterios definidos y validados por SAO.

6. Utilizar los 11 Objetos Focales de Conservación (OFC) como categorías de clasificación cuando corresponda según la definición proporcionada por SAO.

7. Mantener información suficiente para conocer por qué y con qué criterios un artículo fue clasificado.

8. Permitir revisión y corrección humana de resultados cuando sea necesario.

9. Facilitar la generación de estadísticas y visualizaciones útiles para el análisis.

10. Permitir actualizar el sistema periódicamente, incluyendo nuevas publicaciones y nuevos datos.

11. Mantener separación entre los datos originales, los datos procesados y los resultados generados.

12. Facilitar la trazabilidad de las fuentes de información utilizadas.

---

## 5. Alcance inicial

El alcance inicial contempla dos componentes principales.

### 5.1. Seguimiento y organización de información ENCA

La solución debe contemplar la posibilidad de organizar información relacionada con:

- Estrategias de la ENCA.
- Líneas estratégicas.
- Metas.
- Objetivos.
- Indicadores.
- Actividades.
- Organizaciones o actores relacionados.
- Evidencias.
- Fuentes de información.
- Periodos de seguimiento.
- Estado o avance de los indicadores, cuando exista una metodología validada para calcularlo.

El sistema debe utilizar como fuente de verdad la información oficial proporcionada o validada por SAO.

### 5.2. Análisis bibliométrico

La solución debe apoyar el procesamiento de grandes conjuntos de publicaciones científicas.

El flujo esperado conceptualmente es:

    Fuente de datos
          ↓
    Ingesta de publicaciones
          ↓
    Validación y limpieza
          ↓
    Procesamiento
          ↓
    Clasificación
          ↓
    Asociación con OFC
          ↓
    Almacenamiento de resultados
          ↓
    Análisis y visualización

El volumen de datos puede ser considerable. Durante las reuniones iniciales se mencionó la existencia de conjuntos de datos de cientos de miles de artículos, por lo que la solución debe considerar eficiencia y escalabilidad del procesamiento.

---

## 6. Clasificación de publicaciones

Uno de los componentes principales del proyecto es desarrollar o apoyar un mecanismo automatizado de clasificación de artículos científicos.

La clasificación debe utilizar criterios definidos por SAO.

Los 11 Objetos Focales de Conservación (OFC) constituyen una parte fundamental del dominio y deben utilizarse como categorías de clasificación cuando así lo establezca la metodología validada por SAO.

### Reglas importantes

- Los nombres y definiciones de los OFC deben provenir de fuentes proporcionadas o validadas por SAO.
- No se deben crear nuevos OFC.
- No se deben modificar las definiciones de los OFC sin autorización.
- El sistema no debe asumir automáticamente si un artículo puede pertenecer a uno o múltiples OFC hasta que esta regla sea confirmada por SAO.
- El sistema no debe asumir una metodología de clasificación que no haya sido definida o validada.
- Si existe incertidumbre en la clasificación, esta debe poder identificarse y, cuando corresponda, someterse a revisión humana.
- Las decisiones de clasificación deben poder rastrearse hasta los datos y criterios utilizados.

---

## 7. Automatización

La automatización es un objetivo importante del producto.

Se busca reducir actividades manuales y repetitivas relacionadas con:

- Importación de información.
- Limpieza y preparación de datos.
- Identificación de duplicados.
- Procesamiento de publicaciones.
- Clasificación de artículos.
- Actualización de resultados.
- Generación de estadísticas.
- Preparación de información para visualización.

La automatización debe ser reproducible.

Un usuario autorizado debería poder ejecutar nuevamente el proceso cuando se incorporen nuevos datos, sin tener que reconstruir manualmente todo el flujo.

---

## 8. Actualización periódica

La solución debe diseñarse considerando que la información será actualizada periódicamente.

Durante las reuniones con SAO se planteó específicamente la necesidad de poder utilizar la herramienta y actualizarla cada año.

Por lo tanto, el sistema debe evitar diseños que dependan exclusivamente de un dataset estático.

Conceptualmente, el flujo esperado es:

    Datos actuales
          ↓
    Nueva información
          ↓
    Proceso de actualización
          ↓
    Validación
          ↓
    Nuevos resultados
          ↓
    Actualización de estadísticas y visualizaciones

La incorporación de nuevos datos no debe eliminar ni sobrescribir de manera irreversible los datos históricos.

---

## 9. Ejecución local

Una de las restricciones identificadas durante las reuniones es que la solución debe poder ejecutarse localmente.

La arquitectura definitiva debe determinarse posteriormente, pero el producto debe contemplar:

- Ejecución local.
- Procesamiento local de los datos cuando corresponda.
- Acceso controlado a los datasets.
- Persistencia local de la información cuando sea necesario.
- Reproducibilidad del proceso.
- Facilidad para configurar y ejecutar el sistema en otro equipo autorizado.

No asumir que el producto debe depender obligatoriamente de servicios externos o infraestructura cloud.

Las decisiones tecnológicas específicas deben documentarse en el steering técnico y en los documentos de arquitectura.

---

## 10. Visualización y consulta

La solución debe proporcionar mecanismos para explorar los resultados obtenidos.

La interfaz debe priorizar la utilidad para SAO sobre elementos visuales innecesarios.

Entre las posibles funcionalidades se encuentran:

- Dashboard general.
- Estadísticas de publicaciones.
- Distribución por OFC.
- Evolución temporal.
- Filtros.
- Búsqueda de artículos.
- Consulta de información individual.
- Estado de clasificación.
- Resultados pendientes de revisión.
- Indicadores ENCA.
- Seguimiento de metas.
- Información por organización, región o línea estratégica cuando corresponda.

Estas funcionalidades deben implementarse únicamente cuando estén respaldadas por los requisitos reales del proyecto.

---

## 11. Trazabilidad

La trazabilidad es un requisito fundamental.

Para cada dato relevante, el sistema debe permitir identificar, cuando sea posible:

- Fuente.
- Fecha.
- Dataset de origen.
- Proceso mediante el cual fue transformado.
- Resultado generado.
- Versión del proceso o modelo utilizado.
- Usuario que realizó una modificación manual, si aplica.

Los datos procesados no deben perder la relación con los datos originales.

En particular, una clasificación automática debe poder relacionarse con el artículo original y con los criterios utilizados para producirla.

---

## 12. Datos originales y datos procesados

El sistema debe diferenciar claramente entre:

### Datos originales

Información recibida directamente de fuentes externas o proporcionada por SAO.

### Datos procesados

Información transformada mediante limpieza, normalización, extracción o procesamiento.

### Resultados

Información generada por algoritmos, modelos o procesos de clasificación.

### Correcciones humanas

Modificaciones realizadas por un usuario autorizado sobre resultados generados automáticamente.

Los datos originales deben conservarse sin modificaciones destructivas siempre que sea técnicamente posible.

---

## 13. Revisión humana

La automatización no debe considerarse automáticamente infalible.

El sistema debe permitir contemplar procesos de revisión humana cuando:

- La clasificación tenga baja confianza.
- Existan categorías ambiguas.
- Se detecten errores.
- SAO requiera validar resultados.
- El resultado automático deba ser corregido.

Las correcciones humanas deben diferenciarse de las clasificaciones automáticas.

No se debe presentar un resultado generado automáticamente como una verdad absoluta sin indicar su naturaleza.

---

## 14. Calidad de los datos

El sistema debe implementar mecanismos para detectar problemas como:

- Datos incompletos.
- Registros duplicados.
- Formatos inconsistentes.
- Valores inválidos.
- Fuentes faltantes.
- Artículos sin información suficiente para clasificar.
- Indicadores sin datos de actualización.
- Relaciones inconsistentes.

Cuando un dato no pueda ser procesado correctamente, el sistema debe registrar el problema y evitar generar resultados engañosos.

---

## 15. Principio de no invención

La solución debe seguir estrictamente un principio de integridad de información:

> Si un dato no está disponible, no debe inventarse.

Esto aplica tanto a la aplicación como a cualquier componente automatizado o basado en inteligencia artificial.

El sistema debe preferir estados como:

- "Sin información".
- "Pendiente de revisión".
- "No disponible".
- "No clasificado".
- "Fuente no encontrada".

antes que generar información no respaldada.

---

## 16. Usuarios

El usuario principal de la solución será el equipo de SAO encargado de analizar, actualizar y utilizar la información relacionada con la conservación de aves.

La solución debe priorizar:

- Facilidad de uso.
- Claridad.
- Trazabilidad.
- Confiabilidad.
- Facilidad de actualización.
- Comprensión de los resultados.

No asumir roles, permisos o niveles de acceso específicos hasta que estos sean definidos con SAO.

---

## 17. Principios de experiencia de usuario

La interfaz debe:

- Presentar información de manera clara.
- Evitar sobrecargar al usuario con información innecesaria.
- Permitir encontrar rápidamente información relevante.
- Mostrar el estado de los procesos.
- Diferenciar claramente datos, resultados automáticos y resultados validados.
- Mostrar mensajes de error comprensibles.
- Evitar presentar estimaciones o resultados automáticos como datos oficiales sin contexto.
- Priorizar herramientas de análisis y seguimiento sobre elementos puramente decorativos.

---

## 18. Principios de producto

El producto debe cumplir los siguientes principios:

### Trazabilidad sobre conveniencia

Es preferible conservar el origen de un dato antes que simplificar el sistema eliminando información relevante.

### Reproducibilidad sobre procesos manuales

Los procesos importantes deben poder ejecutarse nuevamente con nuevos datos.

### Datos reales sobre datos ficticios

Los datos de demostración deben estar claramente identificados y nunca confundirse con información real de SAO.

### Validación sobre suposición

Cuando una regla del dominio no esté definida, debe marcarse como pendiente de validación.

### Automatización con supervisión

La automatización debe facilitar el trabajo humano, no ocultar incertidumbres ni impedir la revisión.

### Simplicidad

La solución debe ser tan sencilla como sea posible, sin sacrificar las capacidades necesarias para resolver el problema.

---

## 19. Información que todavía debe validarse con SAO

Las siguientes decisiones no deben ser inventadas ni asumidas por el equipo de desarrollo:

1. Definición exacta de cada uno de los 11 Objetos Focales de Conservación.
2. Criterios exactos para determinar si un artículo pertenece a un OFC.
3. Determinar si un artículo puede pertenecer a uno o varios OFC.
4. Campos mínimos requeridos para clasificar un artículo.
5. Metodología de clasificación automática.
6. Si se utilizará un modelo de inteligencia artificial y cuál.
7. Definición de los niveles de confianza.
8. Umbral de confianza requerido para aceptar una clasificación automática.
9. Proceso de revisión humana.
10. Indicadores exactos que deben calcularse.
11. Fórmula o metodología de cálculo de cada indicador.
12. Fuentes oficiales que deben considerarse válidas.
13. Frecuencia exacta de actualización.
14. Usuarios y permisos.
15. Formatos de entrada que SAO utilizará en futuras actualizaciones.
16. Volumen esperado de nuevos datos por periodo.
17. Restricciones de hardware para la ejecución local.
18. Requisitos específicos de privacidad o seguridad.
19. Formato final de los entregables esperados.
20. Qué funcionalidades deben considerarse MVP.

Estas preguntas deben resolverse mediante información proporcionada por SAO antes de convertirlas en reglas rígidas del sistema.

---

## 20. Criterios generales de éxito

El producto será considerado exitoso si permite a SAO:

1. Organizar información de manera estructurada.
2. Procesar grandes cantidades de publicaciones de forma reproducible.
3. Reducir trabajo manual.
4. Clasificar publicaciones utilizando criterios definidos por SAO.
5. Consultar y analizar los resultados.
6. Identificar resultados que requieren revisión.
7. Actualizar la información periódicamente.
8. Mantener trazabilidad de los datos.
9. Conservar los datos históricos.
10. Ejecutar el sistema localmente.
11. Comprender y mantener la solución después de finalizar la Inmersión de Talento.
12. Utilizar la información generada como apoyo para el seguimiento y análisis de la conservación de aves.

---

## 21. Fuentes de verdad

La información del producto debe basarse prioritariamente en:

1. Documentación oficial proporcionada por SAO.
2. Documentación oficial relacionada con la ENCA.
3. Datos proporcionados directamente por SAO.
4. Criterios y definiciones validados explícitamente por SAO.
5. Decisiones tomadas durante reuniones del proyecto y documentadas posteriormente.

Cuando exista conflicto entre una suposición del equipo de desarrollo y una definición proporcionada por SAO, debe prevalecer la información validada por SAO.

---

## 22. Regla fundamental para agentes de IA

Los agentes de inteligencia artificial utilizados durante el desarrollo del proyecto deben:

- No inventar datos.
- No inventar definiciones de la ENCA.
- No inventar los OFC.
- No inventar indicadores.
- No asumir reglas de clasificación no confirmadas.
- Identificar explícitamente información faltante.
- Preguntar o marcar como pendiente cualquier decisión de dominio no definida.
- Diferenciar hechos proporcionados de propuestas técnicas.
- No modificar datos reales sin una instrucción explícita.
- Mantener la trazabilidad de las decisiones importantes.

Cuando exista incertidumbre sobre una regla de negocio, el agente debe indicarla como incertidumbre en lugar de convertirla automáticamente en una regla del sistema.

---

## 23. Estado actual del producto

El proyecto se encuentra en fase inicial de descubrimiento y definición.

Por lo tanto:

- Los requisitos pueden evolucionar.
- La arquitectura todavía no debe considerarse definitiva.
- Las tecnologías pueden cambiar.
- Las reglas de clasificación deben validarse.
- Las funcionalidades deben priorizarse antes de implementarse.
- Las decisiones importantes deben quedar documentadas.

El objetivo de esta etapa es construir una solución técnicamente sólida y alineada con las necesidades reales de SAO, evitando comenzar la implementación basándose en supuestos no validados.