# Migración a ArcGIS Online — SAO ENCA

Guía de referencia para migrar las tres vistas (Seguimiento ENCA, Bibliometría,
Biodiversidad) de la demo de Vercel a la app pública de SAO en ArcGIS Online.

> **Idea central:** no se migra "la app de Vercel". Se migran los **datos** (a
> capas/tablas alojadas de ArcGIS) y los **pipelines de Python** (para
> actualizarlas). La vista se reconstruye con los constructores no-code de
> ArcGIS. Lo ya hecho (datos limpios, llaves estables como `gadm_gid` /
> `taxon_key` / `ofc_id`, scripts reproducibles) es justo el insumo que ArcGIS
> consume. Nada se tira.

## 1. Las 3 piezas de ArcGIS y su equivalencia

| Pieza ArcGIS | Qué es | Equivale a |
| --- | --- | --- |
| Hosted Feature Layer / Hosted Table | El dato alojado, con URL REST (`.../FeatureServer/0`) | Los JSON/CSV del snapshot y de `export_for_arcgis` |
| App builder (Experience Builder / Dashboards / Instant Apps) | La vista (widgets no-code) | El frontend React (las 3 páginas) |
| Notebooks / ArcGIS API for Python | La automatización | Los pipelines (`gbif_bird_counts`, `classify_dataset`, `importar_enca_excel`) |

La app pública (`moacolombia.org/enca/`, montada por jcgomez_dreamgis) ya usa
este modelo: su texto NO está escrito a mano, lo lee de una tabla alojada
(`ContenidoENCA_publico`, visible vía `.../FeatureServer/1/query?...`). Editar
"Polombia"→"Colombia" fue editar una fila de esa tabla. Nuestro trabajo es poblar
capas equivalentes con los datos de las 3 vistas.

## 2. Consumo de créditos (importante)

Saldo de referencia (nov-2026): ~2.584 créditos; ~73 consumidos en 30 días
(casi todo almacenamiento base ya existente).

- **Alojar tablas de datos:** consume créditos de ALMACENAMIENTO, pero es mínimo
  para datos tabulares (cifras/texto, pocas miles de filas). Céntimos.
- **Ver la app / hacer queries a las capas:** NO consume créditos. El uso público
  es gratis.
- **Lo que SÍ gastaría (y NO usamos):** análisis espacial pesado, geocodificación
  masiva, teselas, o Notebooks corriendo mucho tiempo.

Conclusión: mostrar las 3 vistas (tablas + gráficos + un mapa por join) consume
poco y predecible. Para el mapa por departamento NO se suben geometrías: se unen
las cifras por `gadm_gid` con una capa oficial de límites (Living Atlas o las
capas `muni_depto_runap` ya presentes en la organización).

## 3. Flujo de datos de punta a punta

```
Pipelines Python (local o Notebook)
      │  generan datasets/CSV con llaves estables (gadm_gid, taxon_key, ofc_id…)
      ▼
Hosted Feature Layers / Tablas en ArcGIS Online
      │  URL REST (como ContenidoENCA_publico)
      ▼
App en Experience Builder / Dashboard (sección "Resultados" de la app pública)
```

## 4. Qué capa/tabla crear por vista

- **Seguimiento ENCA:** 1 tabla `enca_jerarquia` (fila por elemento: `nivel`,
  `codigo`, `texto`, `padre_id`, `id`). Sale de `importar_enca_excel.py`.
- **Bibliometría:** `biblio_resumen`, `biblio_por_ofc`, y opcional
  `biblio_articulos`. Salen de `bibliometria_service` / el snapshot.
- **Biodiversidad:** tablas de cifras (`biodiv_departamentos`, `..._municipios`,
  `..._familias`, `..._ordenes`, `..._especies_amenazadas`, `..._por_anio`), que
  `export_for_arcgis.py` ya produce como CSV. Los MAPAS se hacen por join con la
  capa de límites usando `gadm_gid`.

## 5. Subir / actualizar datos: truncate + append sobre item EXISTENTE

Patrón ya implementado en `scripts/biodiversity_pilot/publish_to_arcgis.py`:
no se recrea el item (eso rompería la app que lo usa); se vacía y recarga.

```python
from arcgis.gis import GIS
gis = GIS("https://www.arcgis.com", "usuario", "password")   # o GIS(profile=...)
tabla = gis.content.get("ITEM_ID").tables[0]
tabla.delete_features(where="1=1")      # truncate
tabla.edit_features(adds=filas)         # append
```

- **Desde el IDE** (recomendado para iterar): `pip install arcgis`, autenticar,
  publicar. Queda en Git.
- **Desde un Notebook de ArcGIS** (para la actualización periódica/programada):
  `gis = GIS("home")` ya viene autenticado. El Notebook INVOCA el código del
  repo; no se duplica el pipeline dentro.

## 6. La vista (sin rehacer React)

Experience Builder o Dashboards: añadir las tablas a un Web Map/experiencia y
arrastrar widgets (tabla, gráfico de barras, lista, texto, mapa). Cada widget
apunta a una capa. Filtros y "ver detrás de la barra" se configuran sin código.
Los enlaces a GBIF (por especie/departamento, con `taxonKey`/`gadmGid`) se
replican como campo calculado con la URL o un widget de enlace.

### Dónde ponerlas — RESUELTO por investigación (sin depender de jcgomez)

El sitio público (`moacolombia.org/enca`) es un **sitio web externo** que lee un
"CMS casero" sobre ArcGIS: la tabla `ContenidoENCA_publico` (servicio PÚBLICO,
consultable sin credenciales por su REST). Su esquema es genérico:
`seccion` + `codigo` (jerárquico, 1.1, 1.2.1…) + `tipo_contenido` + `texto`.
El sitio pinta cada sección filtrando por `seccion` y renderiza según
`tipo_contenido` (Título, Subtítulo, Contenido, Nombre científico, Link…).

Hallazgos (descubiertos leyendo el servicio público, cero créditos):
- Secciones actuales: `Home`, `Eje 1`…`Eje 5`. **No existe aún una sección
  "Resultados"** con contenido → es nuestro hueco.
- `tipo_contenido = "Link"` guarda una URL en `texto` (ej.
  `https://runap.parquesnacionales.gov.co/cifras`): el sitio YA sabe renderizar
  un recurso externo desde una fila de contenido.

Dos caminos, con decisión tomada:
- **Camino 1 (CMS de texto):** meter las vistas como filas en
  `seccion="Resultados"`. Sirve SOLO para texto/enlaces; gráficos, mapas y
  filtros NO caben. DESCARTADO para vistas ricas.
- **Camino 2 (ELEGIDO): app ArcGIS propia embebida.** Montar un Dashboard /
  Experience Builder con nuestras tablas (gráficos, mapas, filtros), publicarlo,
  y que la sección "Resultados" lo embeba con un `Link`/iframe (mecanismo que el
  sitio ya soporta). Conserva toda la interactividad; es 100% nuestro; lo
  construimos y validamos end-to-end. **No requiere que jcgomez programe nada:**
  al final solo hay que añadir UNA fila tipo Link en "Resultados" apuntando a la
  app (un cambio de 2 minutos, o lo hace el admin RNOA).

Por tanto, podemos avanzar TODA la migración por nuestra cuenta; a jcgomez solo
se le pedirá, al final, enlazar la app en "Resultados" (o permiso para hacerlo).

### Esquema de la capa de límites (para mapas de biodiversidad)

`muni_depto_runap_v` (capa de municipios, 1122 polígonos) usa **código DANE**:
`DPTO_CCDGO` (departamento) y `MPIO_CCDGO` (municipio), con `DPTO_CNMBR` /
`MPIO_CNMBR`. NUESTROS datos usan GADM GID (`COL.11_2`). Para el join del mapa
coroplético hay que añadir un **puente DANE ↔ GADM** (33 departamentos; mapeo
pequeño y conocido). Se resuelve en nuestros datos antes de publicar.

## 7. Qué NO hacer (para no quedar en espejismo)

- No copiar el HTML de React en ArcGIS: la vista se reconstruye con widgets.
- No hardcodear cifras en la app: siempre leer de capas.
- No duplicar el pipeline dentro del Notebook: el Notebook invoca el código del repo.
- No recrear el item al actualizar: truncate + append sobre el existente.
- No poner credenciales en el repo ni en el Notebook: entorno / secrets.

## 8. Plan por fases

0. **Inventario (AHORA, cero créditos, cero cambios):**
   `scripts/arcgis/explorar_contenido.py` lista el contenido de la organización
   para ver qué existe (ContenidoENCA_publico, mapas por eje) y cómo está hecha
   la app de "Resultados".
1. **Piloto — Biodiversidad** (la más madura; ya tiene `publish_to_arcgis.py`):
   publicar 1–2 tablas, montar un Dashboard simple, validar el flujo entero.
2. **Mapas por `gadm_gid`:** join de cifras de departamento con la capa de límites.
3. **Bibliometría y Seguimiento ENCA:** publicar tablas y montar vistas.
4. **Automatización:** pipeline en un Notebook programado (mensual/anual).
5. **Publicación y permisos:** compartir capas y app como públicas, con el
   coordinador y jcgomez_dreamgis.

## 9. Autenticación del inventario (paso 0)

`scripts/arcgis/explorar_contenido.py` admite, sin guardar credenciales en el repo:
- Variables de entorno `ARCGIS_URL` / `ARCGIS_USERNAME` / `ARCGIS_PASSWORD`.
- `--perfil <nombre>` (perfil guardado de la ArcGIS API for Python).
- `--home` (si se ejecuta dentro de un Notebook de ArcGIS).

Es de SOLO LECTURA: lista items y, con `--item <id>`, muestra las capas/tablas y
campos de uno concreto. No crea ni modifica nada.
