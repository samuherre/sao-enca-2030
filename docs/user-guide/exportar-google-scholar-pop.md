# Guía paso a paso: exportar Google Scholar con Publish or Perish (SAO ENCA 2030)

## 0. Qué vas a lograr con esta guía

Al terminar tendrás **uno o varios archivos de resultados de Google Scholar**
(los **Export_PoP**) guardados en:

    data/raw/google_scholar/

listos para que el pipeline del proyecto los procese y combine. La guía es
**clic a clic**, desde abrir el navegador para descargar el programa hasta dejar
los archivos reales en su carpeta.

> **Importante (no inventar datos):** Google Scholar **NO tiene API pública**.
> La obtención es **manual/asistida** con la herramienta externa *Publish or
> Perish* (PoP). No hay descarga automática ni scraping en el alcance del
> proyecto.

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

> La versión exacta de PoP no afecta al proyecto, siempre que permita **exportar
> en JSON o CSV**. Usa una versión reciente.

---

## 2. Entender la ventana de Publish or Perish (una sola vez)

Al abrir PoP verás, a grandes rasgos:

- Una **columna izquierda** con las fuentes de datos (data sources): Google
  Scholar, Crossref, etc.
- Un **panel de consulta** (arriba) donde se escriben los términos y los filtros
  (años).
- Una **tabla de resultados** (centro) que se llena tras lanzar la búsqueda.
- Una **barra de botones / menú** con las opciones de buscar y **exportar**.

No necesitas tocar nada todavía; en las secciones siguientes se indica dónde
hacer clic.

---

## 3. Crear una nueva consulta de Google Scholar

1. En la columna izquierda, localiza **Google Scholar**.
2. Haz clic en **Google Scholar** (o usa el botón/menú **New query → Google
   Scholar Query**, según tu versión).
3. Se abrirá un formulario de consulta de Google Scholar con campos para
   términos y para el rango de años.

> Si tu versión de PoP muestra un aviso de que Google Scholar puede pedir
> resolver un *captcha*, resuélvelo en la ventana que aparezca; es el
> comportamiento normal de la obtención asistida.

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

Reglas de oro para que Google Scholar devuelva MUCHOS resultados (ver también la
sección 8):

- **Menos es más.** Cadenas cortas (2-3 palabras) traen muchos más resultados
  que cadenas largas con muchos `AND`.
- **Evita paréntesis anidados y tildes.** Google Scholar no maneja bien
  `(a OR b) AND (c OR d)` y las tildes (`conservación`, `hábitat`) pueden partir
  la búsqueda. Prefiere `birds conservation` o `aves conservacion`.
- El espacio equivale a **AND**; `OR` debe ir en **mayúsculas**; las comillas
  fuerzan frase exacta.

> ⚠️ Una cadena como
> `(aves OR birds OR avian) AND (conservación OR conservation OR hábitat ...)`
> suele devolver **muy pocos** resultados (decenas) porque es demasiado
> restrictiva. Si te pasa eso, NO es que no exista literatura: es la cadena. Usa
> la estrategia de varias consultas de la sección 8.

Mantén la cadena **documentada** (punto 4) para repetir la búsqueda en años
futuros. Estos términos son **propuesta del equipo**: SAO debe validarlos.

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
   resultados de Google Scholar).
3. Si aparece un *captcha* de Google, resuélvelo en la ventana emergente y
   vuelve a pulsar **Search** si es necesario.
4. Mira el contador **"Papers"** (arriba): te dice cuántos resultados trajo.

### ¿Cuántos resultados esperar?

Para "conservación de aves" en 2020-2030 deberían ser **cientos o miles** en
total (sumando varias consultas). Si una sola consulta te devuelve **decenas**
(p. ej. 18), la cadena es demasiado restrictiva: acórtala (sección 5) o reparte
la búsqueda en varias consultas (sección 8).

> **Tope de Google Scholar:** PoP recupera como máximo ~**1000 resultados por
> consulta**. Por eso la estrategia correcta NO es "una consulta perfecta que lo
> traiga todo", sino **varias consultas complementarias** (sección 8).

---

## 8. Estrategia de cobertura: varias consultas complementarias (recomendado)

**[PROPUESTA — VALIDAR CON SAO]**

Como Google Scholar limita cada consulta a ~1000 resultados y una sola cadena
nunca cubre todo el tema, la forma correcta de lograr buena cobertura es hacer
**varias búsquedas por subtema** y **guardar un archivo por cada una** en
`data/raw/google_scholar/`. El pipeline del proyecto **procesa todos los
archivos de la carpeta, los combina (unión) y marca los duplicados por título**
automáticamente, así que no hay que unir nada a mano ni preocuparse si un
artículo aparece en dos consultas.

### Cómo hacerlo: repite este ciclo por cada consulta

Para **cada** fila de la tabla de abajo:

1. En PoP pulsa **New ▾ → Google Scholar query** (consulta nueva y limpia), o
   usa **Clear All** y reescribe el campo Keywords.
2. Pega la cadena de **Keywords** de esa fila.
3. Deja **Years: 2020 – 2030** (no lo cambies).
4. Pulsa **Search**; resuelve el captcha si aparece.
5. `Ctrl + A` en la tabla de resultados para seleccionar todo.
6. **File → Save Results As…** (o botón **Save Results**), tipo **JSON**.
7. Guarda en `data/raw/google_scholar/` con el **nombre de archivo** de esa fila.

### Consultas propuestas (ajústalas con SAO)

| # | Keywords (pégalo tal cual) | Nombre de archivo |
|---|-----------------------------|-------------------|
| 1 | `birds conservation` | `scholar_birds-conservation_2020-2030.json` |
| 2 | `aves conservacion` | `scholar_aves-conservacion_2020-2030.json` |
| 3 | `bird habitat` | `scholar_bird-habitat_2020-2030.json` |
| 4 | `avian biodiversity` | `scholar_avian-biodiversity_2020-2030.json` |
| 5 | `bird monitoring population` | `scholar_bird-monitoring_2020-2030.json` |
| 6 | `aves Colombia conservacion` | `scholar_aves-colombia_2020-2030.json` |
| 7 | `bird species climate change` | `scholar_birds-climate_2020-2030.json` |
| 8 | `aviturismo OR birdwatching` | `scholar_aviturismo_2020-2030.json` |

Sugerencias prácticas:

- Empieza con las **4-5 primeras** y mira cuántos resultados trae cada una
  (contador "Papers").
- Si una consulta trae ~1000 (el tope), **divídela** en subtemas más
  específicos para no perder resultados por el límite.
- Si una trae muy pocos, **acorta** la cadena (quita términos/paréntesis).
- Puedes añadir subtemas propios alineados con los criterios de inclusión
  (amenazas, pérdida de hábitat, especies invasoras, cacería, políticas de
  conservación, ecosistemas específicos, etc.).

> **Sobre duplicados entre archivos:** es normal y esperado que varias consultas
> traigan artículos repetidos. El pipeline los detecta por título normalizado y
> marca `is_duplicate = true` (apuntando al primero) **sin borrarlos**; no
> inflan el conteo real. Es preferible que sobren a que falten.

> **Convención de nombre [PROPUESTA]:** `scholar_<subtema>_<añoInicio>-<añoFin>.json`.
> Mantén un archivo por consulta; no los fusiones a mano.

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

         C:\Users\Samuel Herrera\OneDrive\Documentos\SAO\data\raw\google_scholar\

     (si la carpeta `google_scholar` no existiera, créala con **Nueva carpeta**).
   - **Nombre del archivo:** usa el de la tabla de la sección 8 (o, para una sola
     consulta, `scholar_aves_2020-2030.json`) **[PROPUESTA — VALIDAR CON SAO]**.
4. Pulsa **Guardar / Save**.

### Por qué JSON (y no CSV)

- **Conserva mejor la metadata**: JSON preserva con más fidelidad la estructura
  y los campos de cada resultado.
- **Incluye el resumen abreviado**: JSON conserva el resumen corto que Google
  Scholar ofrece por resultado, útil para el análisis.

> **CSV también es admitido** por el pipeline (la detección es por extensión,
> sin importar mayúsculas/minúsculas). Si por alguna razón exportas en CSV,
> elige `CSV (*.csv)` y usa el mismo nombre con extensión `.csv`. Aun así, se
> recomienda **JSON**.

---

## 10. Verificar que los archivos quedaron en su sitio

1. Abre el Explorador de archivos de Windows.
2. Ve a:

       C:\Users\Samuel Herrera\OneDrive\Documentos\SAO\data\raw\google_scholar\

3. Confirma que ves tus archivos (uno por consulta), cada uno con tamaño mayor a
   0 KB.

> **Inmutabilidad de `data/raw` (regla del proyecto):** una vez guardados, **no
> edites, no renombres ni muevas** esos archivos a mano. El pipeline los trata
> como datos originales e inmutables; todo lo que genere lo escribe en otra
> carpeta (`data/processed/google_scholar/`).

---

## 11. Procesar los export (dejar los datos reales listos)

Con los archivos ya en `data/raw/google_scholar/`, ejecuta el pipeline del
proyecto (un solo comando, sin interfaz gráfica; procesa **todos** los archivos
de la carpeta de una vez). En una terminal, en la raíz del repositorio y con el
entorno de Python del proyecto activado:

    python bibliometrics/pipelines/process_google_scholar.py

Qué hace ese comando:

- recorre **todos** los `.json` y `.csv` de `data/raw/google_scholar/` y los
  combina en un único conjunto;
- convierte cada registro al contrato de datos del proyecto (Article Data
  Contract V1), fijando `source = "Google Scholar"`;
- valida el período 2020-2030 (lo que quede fuera se marca
  `PENDIENTE_REVISIÓN`, no se borra);
- marca posibles duplicados por título dentro de la fuente (incluidos los
  repetidos entre consultas);
- escribe el dataset procesado en `data/processed/google_scholar/` (un `.json`
  y un `.csv` con la fecha), e imprime un resumen: leídos / procesados /
  descartados + completitud por campo.

Si la carpeta está vacía o no tiene `.json` ni `.csv`, el pipeline termina con
éxito e informa que no hay nada que procesar (no falla).

---

## 12. Ver los resultados

Una vez procesado, puedes visualizar el análisis:

- **Frontend (dashboard):** levanta el backend y el frontend y abre la pestaña
  **Bibliometría** en `http://localhost:5173`. Google Scholar aparecerá sumado
  al consolidado y en la sección "Aporte por fuente".
- **Backend (API):** `GET http://localhost:8000/bibliometria/resumen` (o
  explóralo en `http://localhost:8000/docs`).

Los comandos para levantar backend/frontend están en el README y en
`docs/development/`.

---

## 13. Resumen rápido

| Paso | Acción |
|------|--------|
| 1 | Descargar e instalar Publish or Perish desde harzing.com. |
| 2 | Abrir PoP y crear una **New query → Google Scholar**. |
| 3 | Escribir una cadena de búsqueda **corta** **[PROPUESTA — VALIDAR CON SAO]**. |
| 4 | Fijar **Years = 2020 – 2030**. |
| 5 | **Search** y resolver captcha si aparece; revisar el contador "Papers". |
| 6 | Repetir por subtema (sección 8): una consulta → un archivo JSON. |
| 7 | **Ctrl+A** → **File → Save Results As…** → tipo **JSON** en `data/raw/google_scholar/`. |
| 8 | Verificar los archivos en el Explorador (no editarlos nunca). |
| 9 | Ejecutar `python bibliometrics/pipelines/process_google_scholar.py`. |
| 10 | Ver resultados en la pestaña **Bibliometría** del frontend o en `GET /bibliometria/resumen`. |

> Recordatorio: Google Scholar **no tiene API**; la obtención es
> **manual/asistida** con Publish or Perish. Las cadenas de búsqueda y los
> nombres de archivo son **propuesta del equipo, a validar con SAO**.

---

## 14. Problemas frecuentes

- **Me salieron muy pocos resultados (decenas):** la cadena es demasiado
  restrictiva. Acórtala (p. ej. `birds conservation` en vez de una cadena con
  muchos `AND` y paréntesis), quita las tildes, y reparte la búsqueda en varias
  consultas (sección 8). No es que falte literatura: es la consulta.
- **Una consulta trae ~1000 (el tope):** divídela en subtemas más específicos
  para no perder resultados por el límite de Google Scholar.
- **Aparece un captcha repetido:** es normal en Google Scholar. Resuélvelo en la
  ventana de PoP; si persiste, espera unos minutos y reintenta.
- **"Save as type" no muestra JSON:** actualiza PoP a una versión reciente;
  mientras tanto, exporta en **CSV** (también admitido) con extensión `.csv`.
- **El dashboard no muestra Google Scholar:** confirma que ejecutaste el
  pipeline (paso 11) y que `data/processed/google_scholar/` contiene un `.json`.
- **No encuentro la carpeta `google_scholar`:** créala dentro de `data/raw/`.
  El repositorio ya la incluye con un archivo `.gitkeep`.
