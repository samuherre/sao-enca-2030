# Guía paso a paso: exportar OpenAlex con Publish or Perish (SAO ENCA 2030)

## 0. Qué vas a lograr con esta guía

Al terminar tendrás **uno o varios archivos de resultados de OpenAlex**
(los **Export_PoP_OpenAlex**) guardados en:

    data/raw/openalex/

listos para que el pipeline del proyecto los procese y combine. La guía es
**clic a clic**, desde abrir el navegador para descargar el programa hasta dejar
los archivos reales en su carpeta.

> **Por qué OpenAlex (alto volumen):** a diferencia de Google Scholar (que
> limita el acceso automático y devuelve lotes pequeños sin captcha),
> **OpenAlex** es una base abierta y gratuita de trabajos académicos accesible
> desde *Publish or Perish* (PoP) que permite exportar **lotes grandes** de
> resultados en JSON o CSV, sin captcha. Es la fuente de **alto volumen** del
> proyecto.

> **Obtención manual/asistida (no inventar datos):** la obtención se hace con la
> herramienta externa *Publish or Perish*. En el alcance del proyecto **no** se
> hacen consultas programáticas a la API de OpenAlex ni scraping. No se inventan
> datos: lo que no venga en el export queda vacío.

> **Convenciones de esta guía (PROPUESTA A VALIDAR CON SAO):** las *cadenas de
> búsqueda* (secciones 5 y 8) y los *nombres de archivo* (secciones 7 y 8) son
> una **propuesta del equipo**, no una instrucción oficial de SAO. Están
> marcadas con el rótulo **[PROPUESTA — VALIDAR CON SAO]**. SAO puede ajustarlas;
> el resto del procedimiento (período 2020-2030, formato JSON, carpeta destino,
> inmutabilidad de `data/raw`) sí está definido por el proyecto.

Sistema operativo de referencia: **Windows 10/11**.

---

## 1. Instalar Publish or Perish (clic a clic)

1. Abre tu navegador (Chrome, Edge o Firefox).
2. En la barra de direcciones escribe y entra a:

       https://harzing.com/resources/publish-or-perish

3. En esa página, busca la sección de **descarga** (texto "Download" / "Windows").
4. Haz clic en el enlace del **instalador para Windows** (archivo con extensión
   `.exe`, normalmente llamado algo como `PublishOrPerish_x64_setup.exe`).
5. Cuando termine la descarga, abre el archivo descargado (doble clic en la
   carpeta *Descargas*).
6. Si Windows muestra un aviso de seguridad ("¿Quieres permitir que esta
   aplicación realice cambios?"), pulsa **Sí**.
7. En el asistente de instalación: **Next → Acepta los términos → Next → Install
   → Finish**. Deja las opciones por defecto.
8. Abre el programa: menú **Inicio → escribe "Publish or Perish" → Enter**.
9. Verifica que la ventana principal del programa abre correctamente.

> La versión exacta de PoP no afecta al proyecto, siempre que ofrezca **OpenAlex**
> como fuente de datos y permita **exportar en JSON o CSV**. Usa una versión
> reciente (OpenAlex se añadió como fuente en versiones modernas de PoP).

---

## 2. Entender la ventana de Publish or Perish (una sola vez)

Al abrir PoP verás, a grandes rasgos:

- Una **columna izquierda** con las fuentes de datos (data sources): Google
  Scholar, Crossref, **OpenAlex**, etc.
- Un **panel de consulta** (arriba) donde se escriben los términos y los filtros
  (años).
- Una **tabla de resultados** (centro) que se llena tras lanzar la búsqueda.
- Una **barra de botones / menú** con las opciones de buscar y **exportar**.

No necesitas tocar nada todavía; en las secciones siguientes se indica dónde
hacer clic.

---

## 3. Crear una nueva consulta de OpenAlex

1. En la columna izquierda, localiza **OpenAlex**.
2. Haz clic en **OpenAlex** (o usa el botón/menú **New query → OpenAlex Query**,
   según tu versión).
3. Se abrirá un formulario de consulta de OpenAlex con campos para términos y
   para el rango de años.

> A diferencia de Google Scholar, **OpenAlex no pide captcha** y admite lotes
> grandes. Si tu versión de PoP no muestra OpenAlex en la lista de fuentes,
> actualiza PoP a una versión reciente.

---

## 4. (Opcional recomendado) Documentar la búsqueda antes de lanzarla

Antes de ejecutar, anota en un bloc de notas los términos exactos que vas a usar
y la fecha en que haces la búsqueda. Esto hace el proceso **reproducible** para
las actualizaciones anuales.

---

## 5. Escribir la cadena de búsqueda

**[PROPUESTA — VALIDAR CON SAO]**

En el campo de términos ("Keywords" / "Query words") escribe una cadena alineada
con los criterios de inclusión del proyecto
(`docs/bibliometrics/inclusion-exclusion-criteria.md`), sobre **aves** y su
**conservación**. Para una primera prueba simple:

    birds conservation

Notas prácticas para OpenAlex:

- OpenAlex indexa un volumen muy grande de trabajos, así que una cadena corta
  como `birds conservation` puede traer **miles** de resultados.
- Si una sola consulta trae demasiados para el límite de exportación de tu
  versión de PoP, no fuerces una cadena única: usa **varias consultas
  complementarias** por subtema (sección 8) para cubrir el tema sin perder
  resultados.
- El espacio suele comportarse como **AND**; `OR` en **mayúsculas**; las comillas
  fuerzan frase exacta. El comportamiento fino de operadores depende de la
  versión de PoP y de la fuente; valida con una búsqueda de prueba.

Mantén la cadena **documentada** (punto 4) para repetir la búsqueda en años
futuros. Estos términos son **propuesta del equipo**: SAO debe validarlos; no
son el criterio oficial de SAO.

---

## 6. Acotar el período de publicación a 2020-2030

1. En el formulario de la consulta, localiza los campos de **años**: "Years"
   (o "Year from" / "Year to").
2. Año de inicio: `2020`
3. Año de fin: `2030`

> El **Período de inclusión 2020-2030** sí está definido por el proyecto (no es
> propuesta). Hoy en la práctica solo existirán publicaciones hasta el año en
> curso; dejar 2030 como tope deja la consulta lista para años siguientes.

> El pipeline **no descarta** por sí solo lo que quede fuera de 2020-2030: lo
> marca como `PENDIENTE_REVISIÓN`. Acotar aquí reduce ruido desde el origen.

---

## 7. Lanzar la búsqueda y revisar resultados

1. Pulsa el botón **Search** (Buscar) del formulario.
2. Espera a que la **tabla de resultados** se llene (PoP recupera un lote de
   resultados de OpenAlex; por ser alto volumen puede tardar un poco más).
3. Mira el contador **"Papers"** (arriba): te dice cuántos resultados trajo.

### ¿Cuántos resultados esperar?

Para "conservación de aves" en 2020-2030, OpenAlex debería devolver **cientos o
miles** de trabajos. Si una consulta trae muy pocos, la cadena es demasiado
restrictiva: acórtala (sección 5). Si una consulta trae un volumen enorme,
repártela en subtemas (sección 8) para no toparte con el límite de exportación
de tu versión de PoP.

---

## 8. Estrategia de cobertura: varias consultas complementarias (recomendado)

**[PROPUESTA — VALIDAR CON SAO]**

Aunque OpenAlex es de alto volumen, una sola cadena nunca cubre todo el tema. La
forma correcta de lograr buena cobertura es hacer **varias búsquedas por
subtema** y **guardar un archivo por cada una** en `data/raw/openalex/`. El
pipeline del proyecto **procesa todos los archivos de la carpeta, los combina
(unión) y marca los duplicados por título** automáticamente, así que no hay que
unir nada a mano ni preocuparse si un artículo aparece en dos consultas.

### Cómo hacerlo: repite este ciclo por cada consulta

Para **cada** fila de la tabla de abajo:

1. En PoP pulsa **New ▾ → OpenAlex query** (consulta nueva y limpia), o usa
   **Clear All** y reescribe el campo Keywords.
2. Pega la cadena de **Keywords** de esa fila.
3. Deja **Years: 2020 – 2030** (no lo cambies).
4. Pulsa **Search**.
5. `Ctrl + A` en la tabla de resultados para seleccionar todo.
6. **File → Save Results As…** (o botón **Save Results**), tipo **JSON**.
7. Guarda en `data/raw/openalex/` con el **nombre de archivo** de esa fila.

### Consultas propuestas (ajústalas con SAO)

| # | Keywords (pégalo tal cual) | Nombre de archivo |
|---|-----------------------------|-------------------|
| 1 | `birds conservation` | `openalex_birds-conservation_2020-2030.json` |
| 2 | `aves conservacion` | `openalex_aves-conservacion_2020-2030.json` |
| 3 | `bird habitat` | `openalex_bird-habitat_2020-2030.json` |
| 4 | `avian biodiversity` | `openalex_avian-biodiversity_2020-2030.json` |
| 5 | `bird monitoring population` | `openalex_bird-monitoring_2020-2030.json` |
| 6 | `aves Colombia conservacion` | `openalex_aves-colombia_2020-2030.json` |
| 7 | `bird species climate change` | `openalex_birds-climate_2020-2030.json` |
| 8 | `aviturismo OR birdwatching` | `openalex_aviturismo_2020-2030.json` |

Sugerencias prácticas:

- Empieza con las **4-5 primeras** y mira cuántos resultados trae cada una
  (contador "Papers").
- Si una consulta trae un volumen muy alto que supera el límite de exportación
  de tu versión de PoP, **divídela** en subtemas más específicos para no perder
  resultados.
- Si una trae muy pocos, **acorta** la cadena (quita términos).
- Puedes añadir subtemas propios alineados con los criterios de inclusión
  (amenazas, pérdida de hábitat, especies invasoras, cacería, políticas de
  conservación, ecosistemas específicos, etc.).

> **Sobre duplicados entre archivos:** es normal y esperado que varias consultas
> traigan artículos repetidos. El pipeline los detecta por título normalizado y
> marca `is_duplicate = true` (apuntando al primero) **sin borrarlos**; no
> inflan el conteo real. Es preferible que sobren a que falten.

> **Convención de nombre [PROPUESTA]:** `openalex_<subtema>_<añoInicio>-<añoFin>.json`.
> Mantén un archivo por consulta; no los fusiones a mano. Usa el prefijo
> `openalex_` para no confundir estos archivos con los de Google Scholar.

---

## 9. Exportar en formato JSON (recomendado)

Detalle del paso de exportación (aplica a cada consulta de la sección 8):

1. Selecciona los resultados. Para exportar **todos**: clic en la tabla y
   **Ctrl + A** (o menú **Edit → Select All**).
2. Abre la opción de exportar: menú **File → Save Results As…**
   (en algunas versiones: botón **Save Results**, o clic derecho → **Save As…**).
3. En el cuadro de diálogo de guardado:
   - **Tipo / "Save as type":** elige **JSON** (`JSON Data (*.json)`).
   - **Carpeta destino:**

         C:\Users\Samuel Herrera\OneDrive\Documentos\SAO\data\raw\openalex\

     (si la carpeta `openalex` no existiera, créala con **Nueva carpeta**).
   - **Nombre del archivo:** usa el de la tabla de la sección 8 (o, para una sola
     consulta, `openalex_aves_2020-2030.json`) **[PROPUESTA — VALIDAR CON SAO]**.
4. Pulsa **Guardar / Save**.

### Por qué JSON (y no CSV)

- **Conserva mejor la metadata**: JSON preserva con más fidelidad la estructura
  y los campos de cada resultado de OpenAlex (incluidos campos propios como los
  *concepts* y el identificador del *work*).
- **Incluye el resumen**: JSON conserva mejor el resumen/abstract del trabajo,
  útil para el análisis.

> **CSV también es admitido** por el pipeline (la detección es por extensión,
> sin importar mayúsculas/minúsculas). Si por alguna razón exportas en CSV,
> elige `CSV (*.csv)` y usa el mismo nombre con extensión `.csv`. Aun así, se
> recomienda **JSON**.

---

## 10. Verificar que los archivos quedaron en su sitio

1. Abre el Explorador de archivos de Windows.
2. Ve a:

       C:\Users\Samuel Herrera\OneDrive\Documentos\SAO\data\raw\openalex\

3. Confirma que ves tus archivos (uno por consulta), cada uno con tamaño mayor a
   0 KB.

> **Inmutabilidad de `data/raw` (regla del proyecto):** una vez guardados, **no
> edites, no renombres ni muevas** esos archivos a mano. El pipeline los trata
> como datos originales e inmutables; todo lo que genere lo escribe en otra
> carpeta (`data/processed/openalex/`).

> **No falsear el origen:** guarda los exports de OpenAlex **solo** en
> `data/raw/openalex/`. No los coloques en `data/raw/google_scholar/` ni los
> etiquetes como Google Scholar; cada fuente conserva su propia carpeta y su
> propia etiqueta.

---

## 11. Procesar los export (dejar los datos reales listos)

Con los archivos ya en `data/raw/openalex/`, ejecuta el pipeline del proyecto
(un solo comando, sin interfaz gráfica; procesa **todos** los archivos de la
carpeta de una vez). En una terminal, en la raíz del repositorio y con el
entorno de Python del proyecto activado:

    python bibliometrics/pipelines/process_openalex.py

Qué hace ese comando:

- recorre **todos** los `.json` y `.csv` de `data/raw/openalex/` y los combina en
  un único conjunto;
- convierte cada registro al contrato de datos del proyecto (Article Data
  Contract V1), fijando `source = "OpenAlex"`;
- valida el período 2020-2030 (lo que quede fuera se marca
  `PENDIENTE_REVISIÓN`, no se borra);
- marca posibles duplicados por título dentro de la fuente (incluidos los
  repetidos entre consultas);
- escribe el dataset procesado en `data/processed/openalex/` (un `.json` y un
  `.csv` con la fecha), e imprime un resumen: leídos / procesados / descartados
  + completitud por campo.

Si la carpeta está vacía o no tiene `.json` ni `.csv`, el pipeline termina con
éxito e informa que no hay nada que procesar (no falla).

---

## 12. Ver los resultados

Una vez procesado, puedes visualizar el análisis:

- **Frontend (dashboard):** levanta el backend y el frontend y abre la pestaña
  **Bibliometría** en `http://localhost:5173`. OpenAlex aparecerá sumado al
  consolidado y en la sección "Aporte por fuente".
- **Backend (API):** `GET http://localhost:8000/bibliometria/resumen` (o
  explóralo en `http://localhost:8000/docs`).

Los comandos para levantar backend/frontend están en el README y en
`docs/development/`.

---

## 13. Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | Descargar e instalar Publish or Perish desde harzing.com. |
| 2 | Abrir PoP y crear una **New query → OpenAlex**. |
| 3 | Escribir una cadena de búsqueda sobre conservación de aves **[PROPUESTA — VALIDAR CON SAO]**. |
| 4 | Fijar **Years = 2020 – 2030**. |
| 5 | **Search** (sin captcha); revisar el contador "Papers". |
| 6 | Repetir por subtema (sección 8): una consulta → un archivo JSON. |
| 7 | **Ctrl+A** → **File → Save Results As…** → tipo **JSON** en `data/raw/openalex/`. |
| 8 | Verificar los archivos en el Explorador (no editarlos nunca). |
| 9 | Ejecutar `python bibliometrics/pipelines/process_openalex.py`. |
| 10 | Ver resultados en la pestaña **Bibliometría** del frontend o en `GET /bibliometria/resumen`. |

> Recordatorio: la obtención de OpenAlex es **manual/asistida** con Publish or
> Perish (no hay API programática ni scraping en el alcance). Las cadenas de
> búsqueda y los nombres de archivo son **propuesta del equipo, a validar con
> SAO**.

---

## 14. Problemas frecuentes

- **No veo OpenAlex en la lista de fuentes:** actualiza PoP a una versión
  reciente; OpenAlex se añadió como fuente en versiones modernas.
- **Me salieron muy pocos resultados:** la cadena es demasiado restrictiva.
  Acórtala (p. ej. `birds conservation` en vez de una cadena con muchos `AND`),
  quita las tildes, y reparte la búsqueda en varias consultas (sección 8). No es
  que falte literatura: es la consulta.
- **Una consulta trae un volumen enorme:** divídela en subtemas más específicos
  para no perder resultados por el límite de exportación de tu versión de PoP.
- **"Save as type" no muestra JSON:** actualiza PoP a una versión reciente;
  mientras tanto, exporta en **CSV** (también admitido) con extensión `.csv`.
- **El dashboard no muestra OpenAlex:** confirma que ejecutaste el pipeline
  (paso 11) y que `data/processed/openalex/` contiene un `.json`.
- **No encuentro la carpeta `openalex`:** créala dentro de `data/raw/`. El
  repositorio ya la incluye con un archivo `.gitkeep`.
