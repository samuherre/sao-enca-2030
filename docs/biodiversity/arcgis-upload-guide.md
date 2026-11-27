# Guía de carga manual a ArcGIS Online — cifras de aves (Fase 3)

> Guía paso a paso para **subir manualmente** las cifras de aves a ArcGIS Online
> de forma **segura y aislada**. Pensada para alguien que usa ArcGIS por primera
> vez. Nada de esta guía automatiza nada: tú controlas cada paso desde el portal.

## 0. Antes de empezar

- Avisa al **coordinador de SAO** de que vas a crear items **privados de prueba**
  en tu cuenta. No afecta la página pública, pero es su organización.
- Ten a mano los dos CSV generados localmente:
  - `outputs/biodiversity_pilot/gbif/arcgis/national_total_arcgis.csv`
  - `outputs/biodiversity_pilot/gbif/arcgis/publisher_counts_arcgis.csv`
- Genera/actualiza esos CSV con:
  ```
  python scripts/biodiversity_pilot/export_for_arcgis.py
  ```

## 1. Por qué es seguro

- **Subir un CSV crea un item NUEVO.** No sobrescribe nada existente.
- El nivel de compartición por defecto es **privado (Owner)**: solo tú lo ves.
- Mientras solo crees items nuevos tuyos, el sitio público de SAO no cambia.
- Para dañar algo tendrías que entrar a un item existente y borrarlo/sobrescribirlo
  a propósito. Esta guía no hace eso.

Regla de oro: **no toques** la pestaña *Organization*, ni items de otras personas,
ni el contenido que alimenta la página principal.

## 2. Aislamiento: tu "espacio de pruebas"

ArcGIS Online no tiene un servidor de pruebas aparte, pero se logra el mismo
efecto con tres medidas combinadas:

1. **Carpeta propia.** *Content > My Content > New folder* →
   `pruebas-aves-biodiversidad`. Todo lo tuyo queda agrupado ahí.
2. **Privado.** Deja la compartición en *Owner* hasta que SAO apruebe.
3. **Prefijo TEST.** Nombra los items `TEST_aves_total_nacional`,
   `TEST_aves_publicadores`.

Si algo sale mal: borras el item (o la carpeta entera) y no pasó nada.

## 3. Subir el primer CSV (tabla, sin mapa)

Estas cifras son **agregados**, no puntos en un mapa. ArcGIS las publicará como
**tabla alojada** (hosted table), que es lo correcto. No añadimos coordenadas.

1. Entra a [arcgis.com](https://www.arcgis.com) con la cuenta de SAO.
2. *Content* → abre la carpeta `pruebas-aves-biodiversidad`.
3. *New item* → *Your device* → selecciona `publisher_counts_arcgis.csv`.
4. Cuando pregunte cómo añadirlo, elige crear una **hosted feature layer / table**.
   Como el CSV no tiene campos de ubicación, ArcGIS debería ofrecer
   **"None / As a table"** (sin ubicación). Elige esa opción.
   - Si te ofrece ubicar por coordenadas o direcciones, **NO** lo hagas: estas
     filas no son lugares. Déjalo como tabla.
5. Revisa el mapeo de campos y tipos (ver sección 5). Ajusta si hace falta.
6. Título: `TEST_aves_publicadores`. Deja *Share* en **Owner** (privado).
7. Crea el item. Ábrelo y revisa la tabla de atributos.
8. Repite con `national_total_arcgis.csv` → `TEST_aves_total_nacional`.

## 4. Verificación rápida

- Abre cada tabla y confirma que el número de filas coincide con el CSV.
- `publisher_counts`: 5 filas por corte (top 5), con `org_key` y `occurrence_count`.
- `national_total`: 1 fila por corte, con `total_bird_records` y `run_status`.
- Comprueba que `snapshot_date` se reconoce como fecha.

## 5. Esquema esperado de las tablas

**`national_total_arcgis.csv`**

| Campo | Tipo sugerido | Nota |
| --- | --- | --- |
| `snapshot_date` | Date | Fecha del corte (UTC), `YYYY-MM-DD`. |
| `extracted_at_utc` | String | Timestamp original completo (trazabilidad). |
| `source` | String | "GBIF Occurrence API". |
| `country` | String | `CO`. |
| `taxon_key` | Integer/String | `212` (clase Aves). |
| `total_bird_records` | Long (entero) | **Vacío si la consulta falló; nunca 0.** |
| `publishers_in_ranking` | Integer | Nº de publicadores del corte. |
| `run_status` | String | `completed` / `completed_with_errors`. |

**`publisher_counts_arcgis.csv`**

| Campo | Tipo sugerido | Nota |
| --- | --- | --- |
| `snapshot_date` | Date | Fecha del corte. |
| `extracted_at_utc` | String | Timestamp original. |
| `org_key` | String | **Identificador estable** del publicador (clave). |
| `publisher_name` | String | Puede cambiar entre cortes; no es clave. |
| `rank` | Integer | Posición 1..5 en el corte. |
| `occurrence_count` | Long (entero) | Registros del publicador. |
| `run_status` | String | Estado de la corrida. |

> Si ArcGIS detecta mal un tipo (p. ej. el entero como texto), corrígelo en el
> diálogo de importación antes de crear la tabla.

## 6. Actualizaciones futuras (sin duplicar ni mezclar)

Mientras el histórico sea pequeño, lo más simple y seguro:

- **Reemplazo completo (recomendado por ahora).** Cuando haya nuevos cortes,
  vuelve a generar los CSV con el exportador y usa *Update Data > Overwrite
  entire layer* en el item ya creado. Como el histórico es acumulativo
  (append-only) y cada corte tiene su `snapshot_date`, al reemplazar no se
  duplica ni se pierde histórico.
- **Append incremental** (más adelante): subir solo cortes nuevos requiere
  definir una clave única en la capa (`extracted_at_utc`, o
  `org_key + extracted_at_utc`). Más eficiente, más configuración.

Nunca edites a mano cifras de cortes pasados: cada cifra pertenece a su fecha.

## 7. Qué necesita permiso y qué no

| Acción | ¿Autorización de SAO? |
| --- | --- |
| Generar los CSV en local | No |
| Crear carpeta e items **privados** de prueba | No (pero avisa) |
| Compartir un item con la organización o el público | **Sí** |
| Sobrescribir un item existente que no sea tuyo | **Sí** |
| Habilitar acceso por API/token para automatizar | **Sí** |
| Cambiar configuración de la organización | **Sí (evitar)** |

## 8. Pendiente de confirmar en la cuenta de SAO

No verificable desde el código; revísalo en el portal o con el coordinador:

- Tipo de suscripción y **créditos** disponibles (alojar tablas consume créditos).
- Que tu usuario tenga rol con **privilegio de publicación**.
- Si la organización permite acceso por **API/token** (para una futura automatización).
- Visibilidad final del item (privado / organización / público).

## 9. Automatización mensual (Camino 3)

La actualización mensual está **codificada** pero requiere una configuración
inicial que haces una sola vez. El flujo automático: un workflow de GitHub
Actions se ejecuta el día 1 de cada mes, corre
`scripts/biodiversity_pilot/publish_to_arcgis.py`, que extrae de GBIF, regenera
los CSV y **reemplaza el contenido** de las dos tablas de ArcGIS ya creadas.

> Importante: el código de publicación está probado con un ArcGIS **simulado**
> (pruebas sin red). La subida real contra la cuenta de SAO la verificas tú la
> primera vez, con los secrets configurados. No se ha ejecutado contra el tenant.

### 9.1. Qué debes preparar en ArcGIS Online (una sola vez)

1. **Crear las dos tablas** siguiendo las secciones 2–5 (súbelas una vez de forma
   manual). Anota el **item id** de cada una (está en la URL del item, el valor
   después de `id=`, o en la página del item). Necesitarás:
   - item id de la tabla de **total nacional**;
   - item id de la tabla de **publicadores**.
2. **Crear un usuario-app** (o usar uno dedicado) con **rol que permita publicar**.
   Recomendado: un usuario específico para automatización, no tu usuario admin
   personal. Decide esto con el coordinador: es una credencial de la organización.

### 9.2. Dónde van las credenciales (nunca en el repositorio)

En GitHub: *Settings > Secrets and variables > Actions > New repository secret*.
Crea estos 5 secrets (los nombres deben coincidir exactamente):

| Secret | Qué es |
| --- | --- |
| `ARCGIS_URL` | `https://www.arcgis.com` o el portal de SAO |
| `ARCGIS_USERNAME` | usuario-app con privilegio de publicación |
| `ARCGIS_PASSWORD` | contraseña del usuario-app |
| `ARCGIS_NATIONAL_TABLE_ID` | item id de la tabla de total nacional |
| `ARCGIS_PUBLISHER_TABLE_ID` | item id de la tabla de publicadores |

Los secrets están cifrados y no son visibles tras guardarlos. **No** los pongas
en archivos del repositorio ni en el código.

### 9.3. Cómo probarlo sin riesgo

1. Primero, en tu equipo, modo seguro (no publica nada):
   ```
   python scripts/biodiversity_pilot/publish_to_arcgis.py --dry-run
   ```
   Extrae, exporta y registra en `arcgis/run_log.csv`, pero no toca ArcGIS.
2. En GitHub, lanza el workflow manualmente (*Actions > Cifras de aves (mensual)
   > Run workflow*) dejando **dry_run = true**. Debe terminar en verde sin publicar.
3. Cuando el coordinador apruebe, vuelve a lanzarlo con **dry_run = false** para
   la primera publicación real. Revisa en ArcGIS que las tablas se actualizaron.
4. A partir de ahí corre solo, el día 1 de cada mes.

### 9.4. Cómo se registran los resultados de cada ejecución

Cada corrida añade una fila a
`outputs/biodiversity_pilot/gbif/arcgis/run_log.csv` con: fecha UTC, estado de la
extracción, total, nº de publicadores, si se publicó y el detalle. Una corrida
que falla al publicar **se registra igual** (como `published=no`) y no borra
cifras válidas previas.

### 9.5. Costo (pendiente de confirmar con SAO)

- GitHub Actions: gratis para este uso (una ejecución mensual breve).
- ArcGIS Online: el **alojamiento** de las tablas consume créditos de SAO; es el
  mismo costo tanto si subes manual como automático. El Camino 3 **no** añade el
  costo de cómputo que tendrían los ArcGIS Notebooks. Confirma el detalle con el
  coordinador.

## 10. Lo que todavía NO hacemos

- No publicamos datos reales hasta que el coordinador apruebe (prueba en dry-run).
- No hay desglose por departamento ni mapas (las cifras son agregados).

## 11. PENDIENTE PRIORITARIO — llaves GADM en el pipeline (clave para ArcGIS)

> **Prioridad ALTA para la migración a ArcGIS.** No afecta la demo web actual
> (ahí los enlaces ya funcionan), pero SÍ bloquea el mapa coroplético por
> departamento en ArcGIS. Resolver antes de montar las capas geográficas.

### Problema

En ArcGIS, un mapa por departamento se arma uniendo (join) los conteos con una
capa de polígonos de departamentos **por un código estable** (GADM GID, p. ej.
Cauca = `COL.11_2`). Hoy ese código:

- **Municipios:** SÍ lo produce el pipeline (`gbif_bird_counts.py`,
  `fetch_municipality_facet` → `gadm_gid`) y SÍ lo exporta ArcGIS
  (`export_for_arcgis.py`, `by_municipality.csv`). ✅
- **Departamentos:** NO. El pipeline solo guarda `{"departamento": <nombre>,
  "occurrence_count": ...}` sin `gadm_gid` (`fetch_department_facet`), y el
  export `by_department.csv` sale sin la llave. El `gadm_gid` de departamentos
  hoy existe **únicamente** en el snapshot de la demo, porque lo inyecta el
  post-proceso `scripts/data/resolver_gadm_departamentos.py` sobre el JSON del
  frontend — no llega ni al report del pipeline ni a los CSV de ArcGIS.

Consecuencia: al montar ArcGIS, la capa de departamentos (y la de riqueza por
departamento) no tendría su llave de unión GADM, a diferencia de municipios.

### Qué hay que hacer (una sola pasada en el pipeline)

1. En `scripts/biodiversity_pilot/gbif_bird_counts.py`, que
   `fetch_department_facet` resuelva y añada `gadm_gid` a cada departamento
   (y la riqueza por departamento, `species_by_department_ranking`). La fuente
   oficial del mapeo nombre→GID es `GET /v1/geocode/gadm/COL/subdivisions`
   (misma lógica ya probada en `scripts/data/resolver_gadm_departamentos.py`:
   normalizar acentos/puntuación + alias para "Bogotá D.C." y "San Andrés y
   Providencia"). Idealmente mover esa lógica a una función reutilizable.
2. El backend ya propaga `gadm_gid` de departamentos si el report lo trae
   (`biodiversidad_service._departamentos_desde_report` /
   `_riqueza_departamentos_desde_report`), así que no requiere cambios.
3. Añadir `gadm_gid` a los campos de `by_department.csv` (y crear el export de
   riqueza por departamento, hoy inexistente) en
   `export_for_arcgis.py` → `BREAKDOWN_EXPORTS`.
4. Una vez el report traiga la llave, el post-proceso
   `resolver_gadm_departamentos.py` se vuelve redundante y se puede retirar
   (la demo tomaría el `gadm_gid` directo del backend, igual que municipios).

### Nota sobre los taxones (menor prioridad)

La clave COL XR del portal (`gbif_portal_key`, p. ej. Thraupidae = `H87`) que
resuelve `scripts/data/resolver_claves_gbif_portal.py` es **solo para el enlace
al portal web de GBIF**. ArcGIS mostrará taxones por nombre/geometría, no por esa
clave, así que NO es necesaria en el pipeline de ArcGIS. Puede quedarse como
post-proceso del snapshot de la demo.
