# Guía de uso: consultar OpenAlex por API (SAO ENCA 2030)

## 0. Qué vas a lograr con esta guía

Al terminar sabrás ejecutar, con **un único comando de línea de comandos**, el
**Pipeline OpenAlex por API**, que consulta directamente la API pública y
gratuita de OpenAlex (https://api.openalex.org), pagina los resultados, los
convierte al contrato de datos del proyecto (Article Data Contract V1) y escribe
el dataset procesado en:

    data/processed/openalex/

Ese dataset aparece automáticamente en el análisis consolidado (pestaña
**Bibliometría** del frontend y `GET /bibliometria/resumen`), **sin pasos
manuales** de exportación.

Sistema operativo de referencia: **Windows 10/11** (los comandos son equivalentes
en macOS/Linux).

> **API de OpenAlex pública y gratuita.** El conector funciona **sin API key**:
> recupera aproximadamente la **primera página** de cada búsqueda (del orden de
> ~200 registros con `per_page=200`). Para recorrer **todas** las páginas por
> cursor necesitas una **API key gratuita** de OpenAlex, que se configura por
> variable de entorno y **no** se guarda en el repositorio (ver sección 4).

> **No inventar datos (regla del proyecto).** Lo que la API no entregue queda
> vacío (`null`). Los registros se etiquetan siempre como `OpenAlex`, nunca como
> otra fuente.

---

## 1. Relación con la vía manual (Publish or Perish)

Existen **dos vías** para incorporar OpenAlex al proyecto, y ambas producen el
**mismo `Dataset_Procesado`** en la misma carpeta `data/processed/openalex/`, con
el mismo `source = "OpenAlex"` y el mismo esquema de identificador (`article_id`
con prefijo `oa-`):

| Vía | Cómo se obtiene | Guía |
|-----|-----------------|------|
| **Manual / asistida** | Exportación a mano con *Publish or Perish* (PoP) a `data/raw/openalex/`, luego `process_openalex.py`. | `docs/user-guide/exportar-openalex-pop.md` |
| **Por API (esta guía)** | Un único comando consulta la API de OpenAlex y escribe directo a `data/processed/openalex/`. | este documento |

**La vía por API reemplaza el paso manual** de PoP: no necesitas instalar PoP ni
exportar archivos a mano. Como ambas vías escriben en la misma carpeta, con el
mismo `source` y el mismo esquema de `article_id`, los registros obtenidos por
API y por PoP **cuentan como una sola fuente** y se deduplican juntos (el mismo
trabajo produce el mismo `article_id` por cualquiera de las dos rutas). Puedes
usar una u otra según te convenga; la vía por API es más **reproducible** porque
no depende de que una persona repita la misma consulta en PoP.

> La vía por API **no toca** `data/raw/`. Solo escribe en
> `data/processed/openalex/`.

---

## 2. Requisitos previos

1. Tener el repositorio del proyecto clonado y el entorno de Python del proyecto
   activado (Python 3.12+). Los pasos para preparar el entorno están en el
   `README.md` y en `docs/development/`.
2. Tener instaladas las dependencias del componente bibliométrico (incluye el
   cliente HTTP que usa el conector). Desde la raíz del repositorio:

       pip install -r bibliometrics/requirements.txt

3. Tener conexión a Internet (el conector consulta la API de OpenAlex en vivo).

> Si al iniciar no hay conectividad con la API, el pipeline **no** escribe un
> dataset vacío: registra un mensaje de error comprensible y termina, para que un
> dataset a medias no se confunda con un resultado real.

---

## 3. Ejecutar el pipeline (un solo comando)

Desde la **raíz del repositorio**, con el entorno de Python activado:

    python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

Qué hace ese comando:

- consulta el endpoint de trabajos (`works`) de la API de OpenAlex (usa la
  `OPENALEX_API_KEY` si está definida; ver sección 4);
- **pagina** por cursor hasta recuperar todos los resultados de la consulta (o
  hasta el límite máximo configurado). **Sin API key** solo recupera la primera
  página; **con `OPENALEX_API_KEY`** recorre todas las páginas (ver sección 4);
- aplica un **ritmo de solicitudes** acotado y **reintenta** los errores
  transitorios (p. ej. límite de tasa) con espera creciente, para no abusar del
  servicio ni abortar por un fallo pasajero;
- convierte cada trabajo al Article Data Contract V1 fijando
  `source = "OpenAlex"`; lo que la API no entregue queda en `null`;
- valida el **Período de inclusión 2020–2030** (lo que quede fuera se marca
  `PENDIENTE_REVISIÓN`, no se borra);
- marca posibles **duplicados** por título dentro de la fuente, incluidos los
  repetidos entre varias consultas;
- escribe el dataset procesado en `data/processed/openalex/` (un `.json` y un
  `.csv` con la fecha) e imprime un **resumen**: trabajos recuperados / páginas
  consultadas / errores encontrados + registros procesados y completitud por
  campo.

### 3.1 Varias consultas en una misma corrida

Una sola cadena nunca cubre todo el tema. Puedes pasar **varios términos** en la
misma corrida; el pipeline **combina** los resultados en un único dataset y
**deduplica** sobre el conjunto combinado:

    python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation" --term "aves conservacion" --term "avian biodiversity"

> El orden y la forma exacta de pasar varias consultas (varios `--term`, un
> archivo de configuración, etc.) se fija en la implementación del pipeline; lo
> importante es que el pipeline admite **1..N consultas** en una corrida y las
> combina en un solo `Dataset_Procesado`.

---

## 4. Variable de entorno `OPENALEX_API_KEY` (habilita la paginación completa)

La API de OpenAlex funciona **sin API key**, pero en ese caso al seguir el cursor
para pasar de la **primera página** la API responde con un error de autenticación
(HTTP 401). Por eso, sin key, el conector recupera aproximadamente **una sola
página** por búsqueda (del orden de ~200 registros con `per_page=200`).

Con la variable de entorno:

    OPENALEX_API_KEY

el conector envía la key en cada solicitud y la **paginación por cursor continúa
más allá de la primera página**, recuperando todos los resultados de la consulta
(o hasta el `max_results` configurado).

### 4.1 Cómo obtener la API key gratuita

La key es **gratuita**. Según la documentación oficial de OpenAlex, se obtiene en
el sitio del proveedor:

1. Entra en **openalex.org**.
2. Abre **Settings** (ajustes de tu cuenta).
3. Busca la opción **API key** y genera/copia tu key.

> Detalle: la Especificación de integración por API key
> (`docs/bibliometrics/api-key-integration.md`) documenta que la key habilita la
> paginación por cursor completa (desaparece el 401 al paginar), las cuotas
> aproximadas con y sin key y las fuentes oficiales consultadas. Las cifras
> exactas de cuotas/costos quedan `PENDING_VALIDATION` hasta verificarse contra
> la documentación oficial vigente.

### 4.2 La API key es un secreto: nunca se versiona

A diferencia de `OPENALEX_MAILTO` (que es un correo de cortesía y **no** es un
secreto, ver sección 5), la **`OPENALEX_API_KEY` es un secreto** y se trata como
tal:

- Se provee **únicamente** por **variable de entorno**.
- **Nunca** se guarda en el código, en documentación pública, en el frontend ni
  en el repositorio. En `.env.example` solo hay un **placeholder comentado sin
  valor real** (p. ej. `# OPENALEX_API_KEY=`); el valor real, si lo usas, va en
  tu `.env` local, que **nunca** se versiona.
- **Nunca** aparece en los logs, en los mensajes de error ni en el resumen que
  imprime el pipeline.

> **No pegues tu key en este documento, en el chat ni en un commit.** Si crees
> que una key quedó expuesta, revócala desde openalex.org y genera una nueva.

### 4.3 Cómo definirla para una corrida (sin tocar el código)

Reemplaza `TU_API_KEY` por tu key real (no la escribas dentro del repositorio):

- **PowerShell (Windows):**

      $env:OPENALEX_API_KEY = "TU_API_KEY"
      python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

- **CMD (Windows):**

      set OPENALEX_API_KEY=TU_API_KEY
      python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

- **bash (macOS/Linux):**

      export OPENALEX_API_KEY="TU_API_KEY"
      python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

Recomendado: defínela una vez en tu `.env` local (copiado de `.env.example`).
El pipeline **carga el `.env` automáticamente** al iniciar (python-dotenv), por
lo que **no necesitas exportarla en cada terminal**. Si además la exportas en la
terminal, ese valor tiene prioridad sobre el `.env`.

### 4.4 Límite recomendado al recuperar todas las páginas

Con la key, una consulta amplia puede recuperar muchos resultados. La
Especificación de límites de recuperación
(`docs/bibliometrics/retrieval-limits.md`) recomienda un `Limite_Recuperacion`
de **5.000 resultados por corrida**, que se aplica pasando el flag
`--max-results` de forma explícita:

    python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation" --max-results 5000

> Ese **5.000** es un **valor recomendado** del flag, no el valor por defecto del
> código (hoy `--max-results` es `None`, sin límite). El valor definitivo queda
> `PENDING_VALIDATION` a la espera de confirmación por SAO.

---

## 5. Variable de entorno `OPENALEX_MAILTO` (opcional, no es un secreto)

OpenAlex ofrece un **"polite pool"**: si envías un correo de cortesía en las
solicitudes, obtienes mejor servicio y límites más holgados. El conector lo toma
de la variable de entorno:

    OPENALEX_MAILTO

Puntos clave:

- **Es opcional.** Si **no** la defines, el conector **funciona igual** (sin
  polite pool). No es obligatoria para nada.
- **No es un secreto.** Es solo un correo de contacto de cortesía; no es una
  credencial ni una API key. Aun así, **no versiones un valor real**: en el
  repositorio solo debe quedar un **placeholder comentado** en `.env.example`
  (p. ej. `# OPENALEX_MAILTO=tu-correo@ejemplo.org`), y el valor real, si lo
  usas, va en tu `.env` local (que nunca se versiona).

Cómo definirla para una corrida (sin tocar el código):

- **PowerShell (Windows):**

      $env:OPENALEX_MAILTO = "tu-correo@ejemplo.org"
      python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

- **CMD (Windows):**

      set OPENALEX_MAILTO=tu-correo@ejemplo.org
      python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

- **bash (macOS/Linux):**

      OPENALEX_MAILTO="tu-correo@ejemplo.org" python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"

O bien, defínela una vez en tu `.env` local (copiado de `.env.example`).

---

## 6. Parámetros de la Consulta

Cada **Consulta** se compone de un término de búsqueda y un rango de años que
acota el Período de inclusión:

| Parámetro | Qué es | Valor |
|-----------|--------|-------|
| `term` | Término o expresión de búsqueda enviada a la API. | **[PROPUESTA — VALIDAR CON SAO]** (ver sección 7) |
| `year_from` | Año de inicio del filtro de año de la API. | `2020` por defecto |
| `year_to` | Año de fin del filtro de año de la API. | `2030` por defecto |

Además, el conector admite parámetros **operativos** (configurables) para
adaptarse a los límites de la API sin reescribir código:

| Parámetro operativo | Para qué sirve |
|---------------------|----------------|
| `per_page` | Tamaño de página al paginar (máximo 200, que es lo que admite OpenAlex). |
| `max_results` | Límite máximo de resultados a recuperar por consulta (opcional). |
| `pace_seconds` | Pausa entre páginas para respetar el ritmo de la API. |
| `max_retries` | Número máximo de reintentos ante errores transitorios. |
| `backoff_base` | Base de la espera creciente entre reintentos. |
| `mailto` | Correo de cortesía del polite pool (normalmente se toma de `OPENALEX_MAILTO`, sección 5). |
| `api_key` | API key de OpenAlex para habilitar la paginación completa (normalmente se toma de `OPENALEX_API_KEY`, sección 4). |

Para ver la lista exacta de banderas y sus valores por defecto en tu versión del
pipeline:

    python bibliometrics/pipelines/process_openalex_api.py --help

### 6.1 Período de inclusión 2020–2030

El **Período de inclusión 2020–2030** está **definido por el proyecto** (no es
propuesta). El pipeline acota la consulta a ese rango usando los filtros de año de
la API. Hoy, en la práctica, solo existirán publicaciones hasta el año en curso;
dejar `2030` como tope deja la consulta lista para años siguientes.

> El pipeline **no descarta** por sí solo lo que quede fuera de 2020–2030: lo
> marca como `PENDIENTE_REVISIÓN`. Acotar el año en la consulta reduce ruido desde
> el origen.

---

## 7. Términos de búsqueda: propuesta del equipo (validar con SAO)

**[PROPUESTA — VALIDAR CON SAO]**

Los términos de búsqueda son una **propuesta del equipo del proyecto**, **no** un
criterio oficial de SAO. SAO debe validarlos y puede ajustarlos. No los presentes
ni los uses como el criterio definitivo de SAO.

Términos propuestos como punto de partida (alineados con los criterios de
inclusión del proyecto sobre **aves** y su **conservación**; puedes añadir o
quitar según valide SAO):

| # | Término (`--term`) |
|---|--------------------|
| 1 | `birds conservation` |
| 2 | `aves conservacion` |
| 3 | `bird habitat` |
| 4 | `avian biodiversity` |
| 5 | `bird monitoring population` |
| 6 | `aves Colombia conservacion` |
| 7 | `bird species climate change` |
| 8 | `aviturismo OR birdwatching` |

Sugerencias prácticas:

- Empieza con 4–5 términos y revisa el resumen que imprime el pipeline (trabajos
  recuperados por consulta).
- Si una consulta trae un volumen enorme, usa `max_results` o repártela en
  subtemas más específicos.
- Documenta los términos usados y la fecha de la corrida para poder **repetir** la
  obtención en las actualizaciones anuales.

> Lo definido por el proyecto (período 2020–2030, carpeta de salida, contrato de
> datos, etiqueta `OpenAlex`) **no** es propuesta. Lo que es propuesta a validar
> con SAO son **los términos de búsqueda**.

---

## 8. Dónde queda la salida

El pipeline escribe **únicamente** en:

    data/processed/openalex/

con dos archivos por corrida (un `.json` y un `.csv`, con la fecha en el nombre,
p. ej. `openalex_dataset_YYYY-MM-DD.json`). El pipeline **no** altera
`data/raw/` ni sobrescribe de forma destructiva datasets históricos; la estrategia
de versionado por fecha es coherente con la de las demás fuentes del componente
bibliométrico.

---

## 9. Ver los resultados

Una vez ejecutado el pipeline:

- **Frontend (dashboard):** levanta el backend y el frontend y abre la pestaña
  **Bibliometría** en `http://localhost:5173`. OpenAlex aparecerá sumado al
  consolidado y en la sección "Aporte por fuente".
- **Backend (API):** `GET http://localhost:8000/bibliometria/resumen` (o
  explóralo en `http://localhost:8000/docs`).

Los comandos para levantar backend/frontend están en el `README.md` y en
`docs/development/`.

---

## 10. Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | Activar el entorno de Python del proyecto e instalar `bibliometrics/requirements.txt`. |
| 2 | (Recomendado) Definir `OPENALEX_API_KEY` para habilitar la paginación completa (sección 4). Es un **secreto**: nunca se versiona. |
| 3 | (Opcional) Definir `OPENALEX_MAILTO` para el polite pool (no es obligatoria, no es un secreto). |
| 4 | Ejecutar `python bibliometrics/pipelines/process_openalex_api.py --term "birds conservation"`. |
| 5 | (Opcional) Pasar varios `--term` para cubrir más subtemas en una sola corrida. |
| 6 | (Recomendado) Acotar con `--max-results 5000` (ver sección 4.4). |
| 7 | Revisar el resumen impreso (recuperados / páginas / errores + completitud). |
| 8 | Confirmar la salida en `data/processed/openalex/`. |
| 9 | Ver el consolidado en la pestaña **Bibliometría** o en `GET /bibliometria/resumen`. |

> Recordatorio: la vía por API **reemplaza** la exportación manual con Publish or
> Perish; ambas producen el **mismo `Dataset_Procesado`** de OpenAlex. Los
> **términos de búsqueda** son **propuesta del equipo, a validar con SAO**. El
> **período 2020–2030** y la carpeta de salida sí están definidos por el proyecto.

---

## 11. Problemas frecuentes

- **Error de conectividad al iniciar:** revisa tu conexión a Internet. El pipeline
  **no** escribe un dataset vacío en ese caso; termina con un mensaje de error
  comprensible.
- **Solo recupero ~200 registros / el resumen sugiere configurar la API key:**
  sin `OPENALEX_API_KEY`, OpenAlex responde 401 al pasar de la primera página y el
  conector solo recupera ~una página por búsqueda. Define `OPENALEX_API_KEY`
  (sección 4) para habilitar la paginación por cursor completa.
- **No quiero usar API key:** el conector funciona igual sin ella, pero recuperará
  solo aproximadamente la primera página de cada búsqueda.
- **El resumen reporta errores en algunas páginas:** si se agotan los reintentos
  de una página, el pipeline registra la consulta y la página afectada, **conserva
  lo ya recuperado** y continúa con el resto; el dataset se escribe con lo
  recuperado y el resumen deja constancia de los errores.
- **Una consulta trae demasiados resultados:** usa `max_results` o divide el
  término en subtemas más específicos.
- **El dashboard no muestra OpenAlex:** confirma que el pipeline terminó y que
  `data/processed/openalex/` contiene un `.json`.
- **No quiero usar el polite pool:** simplemente no definas `OPENALEX_MAILTO`; el
  conector funciona igual sin ella.
- **¿Puedo seguir usando Publish or Perish?** Sí. Ambas vías coexisten y producen
  el mismo `Dataset_Procesado`; elige la que te convenga (la vía por API es más
  reproducible).
