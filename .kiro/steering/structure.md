# Project Structure — SAO ENCA 2030

## 1. Propósito

Este documento define la estructura organizacional del repositorio del
proyecto SAO ENCA 2030.

La estructura debe facilitar:

- Mantenibilidad.
- Separación de responsabilidades.
- Reproducibilidad.
- Trazabilidad.
- Pruebas.
- Desarrollo independiente de componentes.
- Procesamiento de grandes datasets.
- Ejecución local.
- Documentación.
- Evolución futura del sistema.

La estructura propuesta es una guía inicial y puede evolucionar durante la
fase de diseño siempre que los cambios estén justificados y documentados.

---

## 2. Principio general de organización

El proyecto debe separar conceptualmente:

1. Interfaz de usuario.
2. Backend y lógica de aplicación.
3. Procesamiento de datos.
4. Pipeline bibliométrico.
5. Modelos y clasificación.
6. Persistencia.
7. Scripts de ejecución y actualización.
8. Datos.
9. Pruebas.
10. Documentación.
11. Configuración.

No mezclar lógica de negocio, procesamiento de datos y componentes visuales en
un mismo módulo.

---

## 3. Estructura raíz propuesta

La estructura inicial del repositorio debe seguir este esquema:

    /
    ├── .kiro/
    ├── frontend/
    ├── backend/
    ├── bibliometrics/
    ├── database/
    ├── data/
    ├── scripts/
    ├── tests/
    ├── docs/
    ├── config/
    ├── .gitignore
    ├── README.md
    └── LICENSE

No todas las carpetas deben contener código desde el primer momento.

Las carpetas deben utilizarse únicamente cuando exista una necesidad real.

---

# 4. `.kiro/`

Contiene la configuración y contexto específico utilizado por Kiro.

    .kiro/
    ├── steering/
    │   ├── product.md
    │   ├── tech.md
    │   └── structure.md
    │
    └── specs/

### steering/

Contiene reglas y contexto permanente del proyecto.

Los archivos de steering deben describir:

- Producto.
- Principios técnicos.
- Estructura.
- Dominio.
- Convenciones relevantes.

### specs/

Contiene las especificaciones de funcionalidades desarrolladas mediante
el enfoque Spec-driven Development.

Ejemplo:

    .kiro/
    └── specs/
        ├── 01-bibliometric-pipeline/
        ├── 02-article-classification/
        ├── 03-data-management/
        └── 04-dashboard/

Las Specs deben organizarse por funcionalidad y no por archivo de código.

---

# 5. `frontend/`

Contiene exclusivamente la interfaz de usuario.

Responsabilidades:

- Presentación de información.
- Navegación.
- Formularios.
- Filtros.
- Tablas.
- Gráficos.
- Dashboard.
- Estados de carga.
- Mensajes de error.
- Interacción con la API.

No debe contener:

- Consultas directas a la base de datos.
- Lógica de clasificación.
- Procesamiento masivo de artículos.
- Reglas críticas de negocio que deban mantenerse en el backend.

El framework del frontend está DEFINIDO: **React + TypeScript** (`tech.md` §6,
§39). Lovable puede utilizarse como herramienta de aceleración de UI, no como
fuente de verdad de la arquitectura (`tech.md` §7). La librería/framework
concreto de testing del frontend permanece `PENDING_VALIDATION` (`tech.md` §22).

Una estructura conceptual posible es:

    frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── layouts/
    │   ├── services/
    │   ├── hooks/
    │   ├── types/
    │   └── utils/
    │
    ├── public/
    ├── tests/
    └── README.md

Esta estructura conceptual se concreta con la convención de React + TypeScript.

---

# 6. `backend/`

Contiene la lógica de aplicación y los servicios que permiten acceder a los
datos y ejecutar funcionalidades del sistema.

Responsabilidades:

- API.
- Validación.
- Reglas de negocio.
- Servicios.
- Acceso a datos.
- Gestión de entidades.
- Orquestación de procesos.
- Comunicación con otros componentes.

Una estructura conceptual posible:

    backend/
    ├── src/
    │   ├── api/
    │   ├── domain/
    │   ├── services/
    │   ├── repositories/
    │   ├── models/
    │   ├── schemas/
    │   ├── core/
    │   └── utils/
    │
    ├── tests/
    └── README.md

La tecnología del backend está DEFINIDA: **Python 3.12+** con **FastAPI**,
validación mediante **Pydantic**, acceso a datos con **SQLAlchemy** y
migraciones con **Alembic** (`tech.md` §3, §4, §5, §9, §10, §39). Las pruebas
de backend usan **pytest** (`tech.md` §22). La estructura interna concreta se
organiza sobre este stack.

---

# 7. `bibliometrics/`

Contiene el procesamiento específico relacionado con el análisis
bibliométrico.

Esta carpeta debe estar separada del backend porque el procesamiento
bibliométrico puede ejecutarse independientemente de la interfaz.

Responsabilidades:

- Ingesta de publicaciones.
- Limpieza.
- Normalización.
- Extracción de información.
- Deduplicación.
- Preprocesamiento de texto.
- Preparación de datasets.
- Clasificación.
- Evaluación de resultados.
- Generación de estadísticas.
- Procesamiento incremental.

Estructura conceptual:

    bibliometrics/
    ├── ingestion/
    ├── preprocessing/
    ├── deduplication/
    ├── classification/
    ├── evaluation/
    ├── analysis/
    ├── pipelines/
    ├── models/
    └── README.md

Cada módulo debe tener una responsabilidad clara.

---

# 8. `bibliometrics/ingestion/`

Responsable de incorporar nuevos datasets al sistema.

Debe contemplar:

- Lectura de archivos.
- Validación inicial.
- Identificación de columnas.
- Normalización inicial.
- Registro de fuente.
- Identificación del dataset.
- Preparación para almacenamiento.

No debe realizar directamente la clasificación.

---

# 9. `bibliometrics/preprocessing/`

Responsable de preparar los artículos antes del análisis o clasificación.

Puede incluir:

- Limpieza de texto.
- Normalización.
- Eliminación de caracteres problemáticos.
- Normalización de campos.
- Procesamiento de títulos.
- Procesamiento de resúmenes.
- Procesamiento de palabras clave.

No debe modificar destructivamente los datos originales.

---

# 10. `bibliometrics/deduplication/`

Responsable de identificar posibles publicaciones duplicadas.

Debe considerar identificadores disponibles, como:

- DOI.
- Identificadores de publicación.
- Combinaciones de metadatos.

Los duplicados detectados deben conservar trazabilidad.

No eliminar registros automáticamente si la regla de deduplicación no ha sido
definida y validada.

---

# 11. `bibliometrics/classification/`

Contiene la lógica relacionada con la clasificación de artículos.

Debe mantenerse separada de la interfaz.

Puede contener conceptualmente:

    classification/
    ├── classifiers/
    ├── rules/
    ├── features/
    ├── prompts/
    ├── schemas/
    ├── evaluation/
    └── README.md

La estructura final dependerá del método de clasificación seleccionado.

No asumir todavía si se utilizarán:

- reglas;
- machine learning;
- embeddings;
- modelos de lenguaje;
- clasificación híbrida.

La metodología debe definirse posteriormente.

---

# 12. `bibliometrics/models/`

Contiene modelos o componentes relacionados con los métodos utilizados para
procesar o clasificar información bibliométrica.

Debe permitir manejar versiones de modelos cuando corresponda.

Ejemplo conceptual:

    models/
    ├── README.md
    ├── model_config/
    └── evaluation/

Los modelos pesados o archivos binarios no deben almacenarse en Git sin una
justificación explícita.

---

# 13. `bibliometrics/evaluation/`

Contiene herramientas para evaluar la calidad de la clasificación y del
procesamiento.

Puede incluir:

- Métricas.
- Matrices de confusión.
- Precision.
- Recall.
- F1-score.
- Accuracy cuando sea apropiada.
- Evaluación por OFC.
- Conjuntos de validación.
- Comparación entre versiones.

Las métricas concretas dependerán de la metodología de clasificación.

No utilizar métricas inadecuadas para el tipo de problema.

---

# 14. `bibliometrics/analysis/`

Contiene procesos de análisis sobre los resultados.

Puede incluir:

- Estadísticas.
- Distribución por OFC.
- Evolución temporal.
- Conteos.
- Tendencias.
- Agregaciones.
- Análisis bibliométricos adicionales.

Los procesos de análisis no deben modificar los datos originales ni las
clasificaciones almacenadas.

---

# 15. `bibliometrics/pipelines/`

Contiene procesos que coordinan varias etapas.

Ejemplo conceptual:

    dataset
       ↓
    ingestion
       ↓
    preprocessing
       ↓
    deduplication
       ↓
    classification
       ↓
    persistence
       ↓
    analysis

Los pipelines deben ser reproducibles y permitir registrar:

- Fecha de ejecución.
- Dataset utilizado.
- Configuración.
- Versión del código.
- Modelo utilizado.
- Resultado.
- Errores.

---

# 16. `database/`

Contiene elementos relacionados con la persistencia.

Puede incluir:

    database/
    ├── migrations/
    ├── seeds/
    ├── schemas/
    ├── queries/
    └── README.md

### migrations/

Cambios versionados del esquema de la base de datos.

### seeds/

Datos iniciales únicamente cuando sean necesarios.

No utilizar seeds para almacenar datasets reales de gran tamaño.

### schemas/

Documentación o definición del modelo de datos cuando corresponda.

El motor de base de datos está DEFINIDO: **PostgreSQL**, con **SQLAlchemy** como
ORM y **Alembic** para migraciones versionadas (`tech.md` §8, §9, §10, §39). El
modelo de datos físico se derivará del modelo conceptual
(`docs/data/conceptual-data-model.md`) únicamente para las entidades
confirmadas.

---

# 17. `data/`

Esta carpeta es crítica para el proyecto.

Debe separar claramente los datos según su estado.

    data/
    ├── raw/
    ├── interim/
    ├── processed/
    ├── external/
    ├── samples/
    └── exports/

---

## 17.1 `data/raw/`

Contiene datos originales.

Ejemplos:

- Datasets entregados por SAO.
- Archivos originales de publicaciones.
- Información original de fuentes.

Regla:

> Los procesos automáticos no deben modificar los archivos originales de
> `raw/`.

Los datos reales y potencialmente sensibles no deben incluirse en Git sin
autorización explícita.

---

## 17.2 `data/interim/`

Contiene resultados intermedios generados durante el procesamiento.

Estos archivos pueden ser temporales o regenerables.

Ejemplos:

- Datos después de una limpieza inicial.
- Resultados intermedios de procesamiento.
- Archivos temporales de transformación.

No deben considerarse fuente oficial.

---

## 17.3 `data/processed/`

Contiene datasets procesados y estructurados.

Ejemplos:

- Artículos normalizados.
- Artículos deduplicados.
- Resultados de clasificación.
- Datos preparados para análisis.

Los procesos que generan estos datos deben ser reproducibles.

---

## 17.4 `data/external/`

Contiene información obtenida de fuentes externas cuando sea necesario.

Cada conjunto debe registrar su procedencia.

Debe conservarse información como:

- Fuente.
- Fecha de obtención.
- Versión.
- Licencia o restricciones conocidas.

---

## 17.5 `data/samples/`

Contiene datasets pequeños destinados a:

- Desarrollo.
- Pruebas.
- Debugging.
- Demostraciones.

Los samples deben ser suficientemente pequeños para permitir desarrollo
rápido.

No deben confundirse con los datasets reales completos.

---

## 17.6 `data/exports/`

Contiene resultados preparados para ser exportados.

Ejemplos:

- CSV.
- Excel.
- JSON.
- Reportes.
- Resultados de análisis.

Los archivos exportados deben indicar claramente:

- Fecha.
- Versión.
- Fuente.
- Tipo de resultado.

---

# 18. `scripts/`

Contiene scripts ejecutables para tareas operativas.

Ejemplos:

    scripts/
    ├── setup/
    ├── data/
    ├── database/
    ├── processing/
    └── maintenance/

Pueden incluir:

- Inicialización del entorno.
- Carga de datos.
- Actualización anual.
- Ejecución de pipelines.
- Generación de exports.
- Mantenimiento.

Los scripts deben ser pequeños y tener responsabilidades específicas.

No duplicar lógica de negocio dentro de scripts.

Cuando sea posible, los scripts deben invocar servicios o funciones existentes.

---

# 19. `tests/`

Contiene pruebas del proyecto.

Estructura conceptual:

    tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    ├── data/
    └── fixtures/

---

## 19.1 `unit/`

Prueba componentes individuales.

Ejemplos:

- Validadores.
- Funciones de transformación.
- Clasificadores.
- Cálculos.

---

## 19.2 `integration/`

Prueba interacción entre componentes.

Ejemplos:

- API + base de datos.
- Pipeline + persistencia.
- Clasificación + almacenamiento.

---

## 19.3 `e2e/`

Pruebas de flujos completos.

Ejemplo:

    importar dataset
        ↓
    procesar
        ↓
    clasificar
        ↓
    almacenar
        ↓
    consultar resultado

---

## 19.4 `fixtures/`

Contiene datos pequeños y controlados para pruebas.

Nunca utilizar datasets reales gigantes como fixtures de pruebas unitarias.

---

# 20. `docs/`

Contiene documentación general del proyecto.

Estructura inicial:

    docs/
    ├── domain/
    ├── architecture/
    ├── data/
    ├── bibliometrics/
    ├── decisions/
    ├── user-guide/
    └── development/

---

## 20.1 `docs/domain/`

Documentación del dominio.

Puede incluir:

- ENCA.
- Estrategias.
- Metas.
- Indicadores.
- OFC.
- Definiciones proporcionadas por SAO.

---

## 20.2 `docs/architecture/`

Documentación de arquitectura.

Puede incluir:

- Arquitectura general.
- Diagramas.
- Componentes.
- Flujo de datos.
- Decisiones de infraestructura.

---

## 20.3 `docs/data/`

Documentación relacionada con los datos.

Debe incluir, cuando corresponda:

- Diccionario de datos.
- Fuentes.
- Formatos.
- Reglas de validación.
- Relaciones.
- Procesamiento.

---

## 20.4 `docs/bibliometrics/`

Documentación específica del análisis bibliométrico.

Puede incluir:

- Metodología.
- Pipeline.
- Clasificación.
- Evaluación.
- Métricas.
- Actualización anual.

---

## 20.5 `docs/decisions/`

Registro de decisiones técnicas importantes.

Cada decisión puede documentarse como:

    decision/
    ├── ADR-001-database.md
    ├── ADR-002-classification.md
    └── ADR-003-local-execution.md

No todas las decisiones requieren un ADR.

Debe utilizarse para decisiones que afecten significativamente la arquitectura
o el funcionamiento del sistema.

---

## 20.6 `docs/user-guide/`

Documentación para usuarios de SAO.

Debe explicar:

- Instalación.
- Inicio de la aplicación.
- Importación de datos.
- Ejecución de procesos.
- Revisión de clasificaciones.
- Consulta de resultados.
- Actualización anual.

---

## 20.7 `docs/development/`

Documentación para desarrolladores.

Debe explicar:

- Configuración del entorno.
- Instalación de dependencias.
- Ejecución local.
- Pruebas.
- Estructura del código.
- Convenciones.

---

# 21. `config/`

Contiene configuración no sensible del sistema.

Ejemplos:

- Configuración de procesamiento.
- Parámetros.
- Valores por defecto.
- Configuración de entornos.

No almacenar:

- Contraseñas.
- Tokens.
- API keys.
- Credenciales.

Los secretos deben utilizar variables de entorno u otros mecanismos seguros.

---

# 22. Archivos de configuración raíz

La raíz puede contener archivos como:

    .gitignore
    README.md
    LICENSE
    .env.example

### `.gitignore`

Debe excluir:

- Entornos virtuales.
- Dependencias locales.
- Logs.
- Archivos temporales.
- Datasets privados.
- Archivos generados.
- Credenciales.
- Archivos específicos del sistema operativo.

### `.env.example`

Debe documentar las variables necesarias sin incluir secretos reales.

### `README.md`

Debe proporcionar una introducción y explicar cómo iniciar el proyecto.

---

# 23. Datasets grandes

Los datasets de gran tamaño no deben almacenarse directamente en el repositorio
Git salvo autorización explícita y justificación.

El repositorio debe contener:

- Scripts de ingestión.
- Esquemas.
- Datasets pequeños de prueba.
- Documentación.
- Metadatos.

Los datasets grandes deben mantenerse en la ubicación definida para el entorno
local de SAO y su ubicación/configuración debe documentarse.

---

# 24. Modelos de IA grandes

Los modelos de inteligencia artificial que ocupen grandes cantidades de
espacio no deben almacenarse directamente en Git sin una decisión explícita.

La solución debe documentar:

- Modelo.
- Versión.
- Fuente.
- Requisitos.
- Método de instalación.
- Ubicación local.
- Configuración.
- Compatibilidad.

Cuando un modelo sea necesario para ejecutar la aplicación, debe existir un
proceso documentado para instalarlo o configurarlo.

---

# 25. Archivos temporales

Los archivos temporales deben mantenerse fuera de las carpetas destinadas a
datos oficiales.

Ejemplo:

    temp/
    cache/
    logs/

Si estos directorios son necesarios, deben incluirse en `.gitignore`.

Los archivos temporales deben poder eliminarse y regenerarse sin perder
información oficial.

---

# 26. Separación entre código y datos

El código nunca debe depender de rutas absolutas específicas de un único
computador.

Evitar:

    C:\Users\Nombre\Desktop\SAO\data.csv

Preferir configuración relativa o variables de entorno.

La aplicación debe permitir configurar las rutas de datos.

---

# 27. Convenciones de nombres

Utilizar nombres descriptivos y consistentes.

Preferir:

    article_classifier.py

sobre:

    classifier2.py

Preferir:

    article_repository.py

sobre:

    repo.py

El lenguaje principal está DEFINIDO: **Python 3.12+** (backend y bibliometría) y
**TypeScript** (frontend) (`tech.md` §3, §6, §39). Las convenciones específicas
de cada lenguaje (p. ej. `snake_case` en Python, `camelCase`/`PascalCase` en
TypeScript) deben seguir las convenciones estándar de cada ecosistema y
documentarse en `docs/development/` cuando se configure el proyecto.

---

# 28. Separación entre dominio y framework

La lógica central del dominio debe mantenerse lo más independiente posible
del framework utilizado.

Por ejemplo:

    ENCA rules
    Indicator calculations
    Classification rules
    Data validation

no deberían depender innecesariamente de componentes específicos de la
interfaz.

Esto facilita pruebas, mantenimiento y futuros cambios tecnológicos.

---

# 29. Flujo conceptual de dependencias

La dirección de dependencias debería aproximarse a:

    Frontend
        ↓
    API / Application
        ↓
    Domain / Services
        ↓
    Repositories
        ↓
    Database

Y de manera independiente:

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

El frontend no debe depender directamente del pipeline interno.

---

# 30. Independencia del pipeline bibliométrico

El pipeline bibliométrico debe poder ejecutarse sin necesidad de abrir la
interfaz gráfica.

Esto permitirá:

- Procesar datasets grandes.
- Automatizar actualizaciones.
- Ejecutar procesos en segundo plano.
- Realizar pruebas.
- Reprocesar datos.
- Ejecutar actualizaciones anuales.

La interfaz debe consultar los resultados almacenados en lugar de ejecutar
procesamientos pesados cada vez que el usuario abre una página.

---

# 31. Ejecución local

La estructura debe permitir una experiencia de ejecución local clara.

Conceptualmente:

    Clone repository
          ↓
    Install dependencies
          ↓
    Configure environment
          ↓
    Initialize database
          ↓
    Load required data
          ↓
    Run backend
          ↓
    Run frontend
          ↓
    Use application

Los comandos concretos deben documentarse posteriormente en el README.

---

# 32. Evolución de la estructura

No crear carpetas únicamente porque estén definidas en este documento.

La estructura debe crecer junto con el proyecto.

Si una carpeta deja de ser necesaria, puede eliminarse.

Si aparece una nueva responsabilidad claramente diferenciada, puede crearse una
nueva carpeta.

Los cambios estructurales importantes deben quedar documentados.

---

# 33. Estructura objetivo de referencia

La estructura completa de referencia puede visualizarse así:

    SAO-ENCA/
    │
    ├── .kiro/
    │   ├── steering/
    │   │   ├── product.md
    │   │   ├── tech.md
    │   │   └── structure.md
    │   │
    │   └── specs/
    │
    ├── frontend/
    │
    ├── backend/
    │
    ├── bibliometrics/
    │   ├── ingestion/
    │   ├── preprocessing/
    │   ├── deduplication/
    │   ├── classification/
    │   ├── evaluation/
    │   ├── analysis/
    │   ├── pipelines/
    │   └── models/
    │
    ├── database/
    │   ├── migrations/
    │   ├── seeds/
    │   └── schemas/
    │
    ├── data/
    │   ├── raw/
    │   ├── interim/
    │   ├── processed/
    │   ├── external/
    │   ├── samples/
    │   └── exports/
    │
    ├── scripts/
    │   ├── setup/
    │   ├── data/
    │   ├── database/
    │   ├── processing/
    │   └── maintenance/
    │
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   ├── e2e/
    │   └── fixtures/
    │
    ├── docs/
    │   ├── domain/
    │   ├── architecture/
    │   ├── data/
    │   ├── bibliometrics/
    │   ├── decisions/
    │   ├── user-guide/
    │   └── development/
    │
    ├── config/
    │
    ├── .gitignore
    ├── .env.example
    ├── README.md
    └── LICENSE

Esta estructura es una referencia inicial y no debe considerarse una
obligación de crear todos los directorios inmediatamente.