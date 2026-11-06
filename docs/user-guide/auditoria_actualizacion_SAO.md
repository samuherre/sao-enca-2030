# Auditoría y actualización del estado actual del proyecto SAO – Inmersión de Talento EAFIT

## 1. Contexto

Estoy desarrollando un proyecto para la Sociedad Antioqueña de Ornitología (SAO), en el marco de la Inmersión de Talento EAFIT, relacionado con la Estrategia Nacional para la Conservación de las Aves (ENCA 2030).

El proyecto ha involucrado diferentes frentes de trabajo:

1. **Seguimiento de la estructura ENCA:** gestión y consulta de ejes, metas, objetivos, indicadores y actividades.
2. **Análisis bibliométrico:** procesamiento y análisis de artículos científicos relacionados con la conservación de aves y los 11 Objetos Focales de Conservación (OFC).
3. **Obtención de datos de biodiversidad:** consultas y extracción de información desde fuentes como GBIF y SiB Colombia.
4. **Integración y publicación:** exploración de ArcGIS como posible herramienta para integrar, visualizar o publicar resultados de SAO.

Estos son antecedentes generales. No debes asumir que todos estos componentes están implementados, que su estado sigue siendo el mismo o que sus requisitos funcionales ya están confirmados.

Necesito actualizar mi contexto sobre el estado REAL del proyecto para revisar los avances con mi asesor y preparar una demostración visual.

## 2. Tu tarea

Realiza una auditoría de solo lectura del proyecto que tienes abierto.

Inspecciona los archivos, carpetas, documentación, especificaciones, tareas de Kiro, código fuente, configuraciones y pruebas disponibles para reconstruir el estado actual del desarrollo.

Quiero conocer tanto los cambios recientes como el estado general de los componentes relevantes, sin perder las decisiones técnicas y funcionales anteriores que sigan vigentes.

### Restricciones obligatorias

- No modifiques, crees, elimines ni renombres archivos.
- No implementes funcionalidades ni corrijas errores.
- No ejecutes migraciones, procesos de scraping, consultas externas, scripts que escriban archivos ni operaciones destructivas.
- No instales dependencias ni cambies configuraciones.
- No muestres secretos, contraseñas, tokens, claves API ni valores sensibles de archivos `.env`. Puedes indicar qué variables de entorno se requieren, pero no revelar sus valores.
- No supongas que un archivo existente implica que la funcionalidad está terminada.
- No afirmes que una prueba pasó si no encuentras evidencia verificable de su ejecución.
- No inventes cambios recientes, resultados, datos reales ni requisitos de SAO.
- Si no puedes verificar un dato, escribe expresamente **“No verificado”** o **“No hay evidencia suficiente”**.
- Distingue los requisitos documentados de las decisiones técnicas propuestas por el desarrollador.
- No te limites a leer el README: inspecciona el código y las pruebas pertinentes.

## 3. Información que debes recopilar

### A. Estado general y cambios recientes

Identifica:

- Estructura actual de carpetas y módulos relevantes.
- Tecnologías, lenguajes, frameworks, bases de datos y herramientas utilizadas.
- Archivos principales de frontend, backend, procesamiento de datos y configuración.
- Especificaciones, documentos de arquitectura, ADR, archivos de tareas y reglas de Kiro que existan.
- Cambios recientes que puedas identificar de manera fiable mediante Git, historial disponible u otras evidencias locales.
- Diferencias entre el estado documentado y el código actual.
- Si hay archivos sin seguimiento, cambios pendientes o discrepancias visibles en Git, cuando esta información esté disponible.

No uses las fechas de modificación de los archivos como única prueba de que una funcionalidad se implementó recientemente.

### B. Frente 1: Seguimiento de la estructura ENCA

Inspecciona el frontend, el backend, los modelos, los esquemas de validación, los endpoints, las migraciones, las pruebas y la configuración relacionada.

Determina, con evidencia:

- Qué entidades están implementadas.
- Qué operaciones permite cada entidad: crear, consultar individualmente, consultar colecciones, navegar, actualizar o eliminar.
- Qué endpoints existen realmente y qué hacen.
- Qué validaciones de datos están implementadas.
- Cómo se conectan el frontend, el backend y la base de datos.
- Qué pantallas o flujos visuales están disponibles.
- Qué datos iniciales o datos de demostración existen.
- Qué partes están completas, parciales, pendientes o sin verificar.
- Qué funcionalidades aparecen en las especificaciones, pero no están implementadas en el código.

No asumas que se implementaron actualizaciones o eliminaciones simplemente porque el proyecto se describa como CRUD.

### C. Frente 2: Análisis bibliométrico

Inspecciona los módulos y scripts relacionados con la bibliometría, incluyendo, cuando existan:

- Ingesta de artículos.
- Preprocesamiento.
- Normalización y deduplicación.
- Clasificación por categorías u OFC.
- Modelos, reglas o algoritmos de clasificación.
- Evaluación y métricas.
- Análisis y generación de resultados.
- Orquestación de pipelines.
- Pruebas y datos de entrada o salida.

Indica qué existe en el código y qué se ha validado realmente.

Si hay resultados generados, identifica sus archivos y resume qué contienen, sin inventar interpretaciones que no se desprendan de la evidencia.

Diferencia claramente entre un pipeline implementado, uno que se ha ejecutado y uno cuyos resultados han sido evaluados.

### D. Frente 3: Obtención de datos de biodiversidad

Busca los componentes relacionados con GBIF, SiB Colombia y otras fuentes de biodiversidad que aparezcan en el proyecto.

Identifica:

- Scripts, módulos y consultas disponibles.
- Parámetros y filtros relevantes.
- Formatos de salida.
- Manejo de errores y registros de ejecución, si existen.
- Resultados guardados y su ubicación.
- Si hay evidencia de ejecuciones reales o solo código preparado.
- Qué resultados se obtuvieron y qué puede afirmarse a partir de ellos.
- Dependencias externas y limitaciones conocidas.

No vuelvas a ejecutar consultas externas ni procesos de extracción para esta auditoría.

### E. ArcGIS e integración

Busca referencias a ArcGIS, ArcGIS Online, ArcGIS Hub, Experience Builder, Dashboards, mapas, capas, servicios o APIs relacionadas.

Informa únicamente sobre lo que encuentres en el proyecto local.

Distingue entre:

- Integraciones ya implementadas y verificables.
- Configuraciones o experimentos parciales.
- Documentación o propuestas de arquitectura.
- Posibilidades que aún no se han implementado.
- Decisiones que requieren confirmación por parte de SAO.

No supongas que ArcGIS debe reemplazar el frontend, el backend o los scripts actuales. Tampoco asumas que existe una integración funcional por el simple hecho de que haya referencias a ArcGIS.

### F. Datos y entorno de ejecución

Determina, hasta donde sea posible sin modificar el proyecto:

- Qué base de datos se espera utilizar.
- Qué variables de entorno son necesarias, mostrando únicamente sus nombres.
- Qué instrucciones existen para ejecutar frontend y backend.
- Qué servicios externos son necesarios.
- Qué conjuntos de datos reales, de demostración o de prueba están disponibles.
- Qué evidencia existe de que la aplicación funciona localmente.
- Qué dependencias, errores o limitaciones podrían impedir una demostración.

No reveles secretos ni valores sensibles.

### G. Pruebas y evidencia de funcionamiento

Inspecciona las pruebas automatizadas y los registros disponibles.

Presenta los resultados usando estas categorías:

- **Verificado por código:** la implementación puede observarse directamente en el código.
- **Verificado por pruebas:** existe evidencia de que una prueba se ejecutó y pasó.
- **Ejecución documentada:** existe un registro o reporte de ejecución, pero no necesariamente puedes reproducirlo.
- **Declarado en documentación:** el README, las tareas o los documentos indican que existe, sin evidencia adicional suficiente.
- **No verificado:** no se encontró evidencia suficiente.

Si no puedes conocer el resultado real de una ejecución anterior, no lo deduzcas a partir de la existencia de los archivos.

## 4. Formato obligatorio del informe

Entrega un informe en español con las siguientes secciones:

### 1. Resumen ejecutivo
Explica brevemente el estado actual del proyecto, los principales avances verificables y las incertidumbres más importantes.

### 2. Arquitectura actual
Describe la estructura del sistema y las tecnologías utilizadas. Incluye las relaciones entre frontend, backend, base de datos, scripts y herramientas externas, siempre que estén respaldadas por evidencia.

### 3. Inventario de avances por frente
Utiliza una tabla con estas columnas:

| Frente | Componente o funcionalidad | Estado | Evidencia encontrada | Pendiente o limitación |
|---|---|---|---|---|

Incluye los tres frentes principales y ArcGIS como frente transversal cuando corresponda.

Usa estados como: implementado en código, probado, parcial, documentado, pendiente o no verificado. No marques una funcionalidad como probada sin evidencia.

### 4. Archivos y cambios relevantes
Enumera los archivos más importantes, su función y los cambios recientes que puedas respaldar.

Incluye rutas relativas al directorio raíz del proyecto. Evita enumerar archivos irrelevantes o generar un inventario indiscriminado de todo el repositorio.

### 5. Funcionalidades visuales disponibles
Identifica las páginas, pantallas, formularios, tablas, vistas de detalle, mapas o dashboards que realmente estén implementados.

Indica cómo se accede a ellos según la documentación o configuración existente. No inventes rutas, puertos ni instrucciones de ejecución.

### 6. Pruebas y validaciones
Resume las pruebas existentes, los resultados verificables, las ejecuciones documentadas y los aspectos que todavía no se han validado.

### 7. Problemas, riesgos e incertidumbres
Prioriza los problemas que podrían afectar el funcionamiento, la calidad de los resultados o la alineación con las necesidades de SAO.

Separa errores confirmados de riesgos potenciales y preguntas abiertas.

### 8. Preguntas pendientes de validación con SAO
Identifica únicamente las decisiones funcionales o técnicas que no puedan resolverse inspeccionando el código y la documentación local.

Distingue entre requisitos confirmados, supuestos y propuestas.

### 9. Resumen de contexto para continuar trabajando con ChatGPT
Crea un bloque final autocontenido que pueda copiar y pegar en una conversación con ChatGPT.

Debe incluir:
- Estado actual de cada frente.
- Arquitectura y tecnologías.
- Funcionalidades implementadas y probadas.
- Archivos principales.
- Datos disponibles y pendientes.
- Cambios recientes verificables.
- Limitaciones y errores conocidos.
- Decisiones tomadas.
- Preguntas abiertas.
- Próximos pasos que ya estén documentados, sin inventar prioridades nuevas.

## 5. Nivel de detalle y calidad

Sé específico. Prefiero saber que un endpoint concreto existe y qué hace, a leer una frase general como “el backend está implementado”.

Cuando sea útil, incluye nombres de archivos, clases, funciones, rutas HTTP, comandos documentados y nombres de pruebas. No pegues archivos enteros ni grandes bloques de código.

Si el repositorio es demasiado grande para inspeccionarlo por completo, prioriza los componentes anteriores y declara expresamente qué áreas no alcanzaste a revisar.

No cambies el proyecto durante esta tarea.

Al finalizar, entrega únicamente el informe solicitado y el bloque de contexto listo para copiar. No implementes ninguna mejora ni comiences una segunda tarea.