# Especificación de Integración por API key — Componente B (SAO ENCA 2030)

## 1. Objetivo y estado

Este documento especifica **cómo integrar una fuente bibliográfica que requiere
API key** (`Proveedor_API`) en el Componente B. Se estructura en dos partes:

1. Una **plantilla genérica** (§3), aplicable a cualquier `Proveedor_API`, que
   cubre los 12 puntos de especificación exigidos por el Req 6.1.
2. La **instanciación en OpenAlex** (§4), que es el **único `Proveedor_API`
   implementado** en este spec.

Otros proveedores (`Scopus`, `Wiley`, `UNAL OAI-PMH`) se mencionan como
`PENDING_VALIDATION` y **no** se implementan aquí (§5).

> Estado: **Propuesta V1** del Equipo_Proyecto, sujeta a validación por SAO. La
> plantilla genérica y los valores aproximados de cuotas/costos son una
> propuesta técnica; lo no confirmado queda marcado como `PENDING_VALIDATION` y
> listado en `pending-validation.md`.

Este documento se coordina con la **Estrategia de Búsqueda**
(`search-strategy.md`), los **Criterios de inclusión/exclusión**
(`inclusion-exclusion-criteria.md`), el **Contrato de Datos**
(`article-data-contract.md`) y la **Especificación de límites de recuperación**
(`retrieval-limits.md`).

---

## 2. Principio transversal: la API key es un secreto

Para cualquier `Proveedor_API`, la credencial (API key, token u otra
equivalente) se trata como **secreto** y se rige por el steering técnico
(`tech.md §19–§20`) y el del Componente B:

- Se provee **únicamente** por **variable de entorno**.
- **Nunca** se almacena en código fuente, en documentación pública, en el
  frontend ni en el repositorio (ni en archivos versionados como `.env`).
- **Nunca** aparece en mensajes de registro (logs), mensajes de error ni en el
  chat.
- El archivo `.env.example` solo contiene un **placeholder sin valor real**.

---

## 3. Plantilla genérica de integración por API key (`Proveedor_API`)

Para documentar la integración de cualquier `Proveedor_API` deben cubrirse los
**12 puntos** siguientes (Req 6.1). Cada punto describe qué debe especificarse
antes de implementar un conector para esa fuente.

### 3.1. Servicio

Nombre del `Proveedor_API`, URL base del servicio y naturaleza de los datos que
expone (p. ej. metadatos bibliográficos, citaciones, afiliaciones). Debe
indicarse si la fuente entrega **metadatos** o **texto completo** (ver §3.12 y
Req 6.6): una API de metadatos **no** implica acceso al texto completo.

### 3.2. Autenticación requerida

Mecanismo de autenticación (API key, token OAuth, cabecera, parámetro de query,
etc.), si la autenticación es **obligatoria** o **opcional**, y para qué
operaciones se exige (p. ej. solo para ciertos endpoints o para continuar la
paginación).

### 3.3. Variables de entorno

Nombre exacto de la variable de entorno que porta la credencial y de cualquier
variable auxiliar no secreta (p. ej. un correo de cortesía). Debe dejarse claro
cuáles son secretas y cuáles no.

### 3.4. Endpoints

Rutas del servicio que el conector utiliza (p. ej. búsqueda de trabajos,
recuperación por identificador) y el método HTTP correspondiente.

### 3.5. Parámetros de búsqueda

Parámetros que acepta el endpoint de búsqueda (término de búsqueda, operadores,
campos consultables) y cómo se traduce una `Familia_Ecuaciones` de la Estrategia
de Búsqueda a la sintaxis de la fuente (la sintaxis **se adapta a cada fuente**,
sin asumir operadores idénticos).

### 3.6. Filtros por año, idioma y tipo de documento (cuando existan)

Parámetros de filtrado por **año de publicación**, por **idioma** y por **tipo
de documento**, **cuando la fuente los ofrezca**. Si un filtro no existe en la
fuente, debe documentarse su ausencia en lugar de asumirlo.

### 3.7. Paginación

Mecanismo de paginación (cursor, offset, page/limit), parámetro de tamaño de
página, límite máximo por página y condición de fin de la paginación. Debe
indicarse si la paginación completa requiere autenticación.

### 3.8. Límites de solicitudes y de resultados

Límite de solicitudes por unidad de tiempo (rate limit) y límite de resultados
por búsqueda o por página que impone la fuente. Se relaciona con el
`Limite_Recuperacion` operativo por corrida (ver `retrieval-limits.md`), que es
un control propio del Componente B y **no** un límite de la fuente.

### 3.9. Cuotas y posibles costos

Cuotas diarias/mensuales y posibles **costos** asociados al uso de la API, con o
sin credencial. Las cifras deben provenir de la documentación oficial del
proveedor; lo no confirmado se marca `PENDING_VALIDATION` y **no se inventan
cifras**.

### 3.10. Manejo de errores, reintentos y límites de velocidad

Códigos de error relevantes (autenticación, cuota agotada, rate limit, errores
del servidor), política de reintentos (qué errores son transitorios), espera
creciente (backoff) y comportamiento ante falta de conectividad. La credencial
**nunca** debe aparecer en los mensajes de error.

### 3.11. Campos bibliográficos devueltos

Esquema de los registros que devuelve la fuente y su **mapeo al Article Data
Contract V1** (`article-data-contract.md`). Un campo ausente en la fuente se
mapea a `None` (no se inventa).

### 3.12. Condiciones de uso y restricciones de almacenamiento

Licencia y condiciones de uso de los datos, restricciones sobre
almacenamiento/redistribución y si la API entrega solo metadatos o también texto
completo (Req 6.6). No se atribuyen a la fuente capacidades no confirmadas
(Req 10.4).

---

## 4. Instanciación en OpenAlex (único `Proveedor_API` implementado)

OpenAlex es el único `Proveedor_API` integrado en este spec (Req 6.2). El
conector ya existe (`bibliometrics/ingestion/openalex_api_client.py` y
`bibliometrics/pipelines/process_openalex_api.py`); esta sección especifica la
integración por API key que habilita la paginación por cursor completa.

### 4.1. Servicio

- **Proveedor_API**: OpenAlex (`https://api.openalex.org`).
- **Endpoint usado por el conector**: `https://api.openalex.org/works`.
- **Naturaleza de los datos**: catálogo abierto de **metadatos** bibliográficos
  (trabajos, autores, fuentes, instituciones, conceptos). Es una fuente de
  **metadatos**, no de texto completo (ver §4.12).

### 4.2. Autenticación requerida

- La autenticación por API key es **opcional para la primera página** de una
  búsqueda, pero **obligatoria para continuar la paginación por cursor** más
  allá de la primera página (ver §4.7).
- La API key gratuita de OpenAlex se obtiene desde el sitio del proveedor
  (openalex.org → Settings → API key), según su documentación oficial.

### 4.3. Variables de entorno

| Variable | ¿Secreto? | Rol |
|----------|-----------|-----|
| `OPENALEX_API_KEY` | **Sí** (secreto) | API key que habilita la paginación por cursor completa (Req 6.3). Solo por variable de entorno; **nunca** en código, documentación pública, frontend ni repositorio (Req 6.4). |
| `OPENALEX_MAILTO` | No | Correo de cortesía del "polite pool". Opcional, **no** es secreto. Ya soportado por el conector; se conserva sin cambios. |

La API key se pasa a OpenAlex como **parámetro de query `api_key`** en cada
solicitud (solo si la variable está definida con un valor no vacío). El conector
lee el valor **únicamente del entorno del proceso**, nunca de un archivo
versionado.

### 4.4. Endpoints

- `GET https://api.openalex.org/works` — búsqueda y recuperación paginada de
  trabajos (`work`). Es el único endpoint que usa el conector.

### 4.5. Parámetros de búsqueda

El conector construye, por página, los parámetros de query:

- `search`: el término de la `Consulta` (una `Familia_Ecuaciones` de la
  Estrategia de Búsqueda instanciada en OpenAlex).
- `filter`: acota el período con `publication_year:{año_desde}-{año_hasta}`
  (por defecto `2020-2030`).
- `per_page`: tamaño de página (máximo admitido por OpenAlex: 200).
- `cursor`: cursor de paginación (inicia en `*`).
- `mailto`: solo si `OPENALEX_MAILTO` está definido (polite pool, opcional).
- `api_key`: solo si `OPENALEX_API_KEY` está definido con valor no vacío.

### 4.6. Filtros por año, idioma y tipo de documento

- **Año**: soportado y usado por el conector vía
  `filter=publication_year:{desde}-{hasta}`.
- **Idioma**: OpenAlex expone el idioma del trabajo (campo `language`). El
  conector lo **mapea** al registro, pero el **filtrado por idioma** a nivel de
  consulta queda como `PENDING_VALIDATION` (los idiomas objetivo español, inglés
  y portugués se documentan en la Estrategia de Búsqueda; su aplicación concreta
  como filtro de OpenAlex no se confirma en este spec).
- **Tipo de documento**: OpenAlex expone un tipo de trabajo; su uso como filtro
  de consulta y su mapeo al campo propuesto `document_type` del contrato quedan
  como `PENDING_VALIDATION` (ver `article-data-contract.md` y
  `pending-validation.md`).

### 4.7. Paginación

- OpenAlex pagina por **cursor** (`cursor=*` para iniciar; cada respuesta trae
  `meta.next_cursor`). La paginación termina cuando `next_cursor` es `None` o la
  página vuelve vacía.
- **Hallazgo técnico clave**: sin API key, iniciar la paginación por cursor
  funciona, pero **seguir `next_cursor` para pasar de la primera página devuelve
  HTTP 401**. Por eso el conector, sin key, recupera aproximadamente una página
  (del orden de ~200 registros por búsqueda con `per_page=200`).
- **Con `OPENALEX_API_KEY` presente**, el parámetro `api_key` se envía en cada
  solicitud y la paginación por cursor continúa más allá de la primera página
  (desaparece el 401). **Esta es la razón del único cambio de código del spec.**

### 4.8. Límites de solicitudes y de resultados

- `per_page` máximo: **200** (límite de OpenAlex).
- Límite de **resultados por corrida**: lo controla el Componente B mediante el
  `Limite_Recuperacion` (control operativo por corrida, valor recomendado 5.000;
  ver `retrieval-limits.md`), **no** es un límite de la fuente.
- El rate limit exacto de solicitudes por segundo de OpenAlex no se fija aquí;
  el conector aplica una pausa configurable entre páginas (`pace_seconds`) y
  reintentos con espera creciente. El valor exacto del rate limit del proveedor
  queda `PENDING_VALIDATION`.

### 4.9. Cuotas y posibles costos

Valores **aproximados según el proveedor** (OpenAlex). No se inventan cifras
exactas; lo no confirmado se marca `PENDING_VALIDATION`:

- **Sin API key**: cuota diaria **más limitada**, compartida por dirección IP.
- **Con API key gratuita**: cuota diaria **mayor** y habilitación de la
  paginación por cursor completa. OpenAlex ofrece una key **gratuita**; no se
  requiere pago para el uso contemplado en este spec.
- OpenAlex ofrece además planes de pago para volúmenes mayores
  (`PENDING_VALIDATION`: aplicabilidad, cuotas numéricas exactas y costos para el
  uso de SAO).

> Las cifras numéricas exactas de cuota diaria (con y sin key) y de cualquier
> costo quedan `PENDING_VALIDATION`: deben verificarse contra la documentación
> oficial vigente antes de depender de ellas (Req 10.5).

### 4.10. Manejo de errores, reintentos y límites de velocidad

El conector ya maneja los errores HTTP; esta integración añade el manejo
relativo a la API key:

- **HTTP 401 al paginar sin key**: al seguir `next_cursor` sin `api_key`,
  OpenAlex responde **401**. El conector lo trata como error **permanente** (no
  es 429 ni 5xx): registra la `Consulta` y la página afectada, **conserva lo ya
  recuperado** y el mensaje sugiere configurar `OPENALEX_API_KEY`, **sin exponer**
  ningún valor de key.
- **429 / rate limit / cuota diaria**: se trata como error **transitorio**; se
  reintenta hasta `max_retries` con espera creciente (`backoff`). Agotados los
  reintentos, se registra el error por página y la corrida continúa/termina
  conservando lo recuperado.
- **5xx del servidor**: transitorios, misma política de reintentos.
- **Sin conectividad** (error de red/DNS): se propaga para que el pipeline lo
  distinga y no escriba un dataset vacío en la primera solicitud.
- **Regla transversal**: el valor de `OPENALEX_API_KEY` **nunca** aparece en
  logs ni en mensajes de error (Req 6.4; verificado por property test del cambio
  de código).

### 4.11. Campos bibliográficos devueltos

OpenAlex devuelve el esquema nativo de `work`, que el conector **ya mapea** al
Article Data Contract V1 (`article-data-contract.md`). El mapeo cubre, entre
otros: título, autores (`authorships`), año (`publication_year`), DOI, resumen
(reconstruido desde `abstract_inverted_index`), palabras clave/conceptos,
revista/fuente, editorial, volumen, número, páginas, idioma (`language`) e
identificador del trabajo (`id`). Un campo ausente en el `work` se mapea a
`None` (no se inventa).

### 4.12. Condiciones de uso y restricciones de almacenamiento

- OpenAlex es un catálogo **abierto** de metadatos; según su documentación los
  datos se publican bajo una licencia abierta (dominio público / CC0). La
  verificación de la licencia vigente y de cualquier restricción de
  redistribución queda `PENDING_VALIDATION`.
- **Metadatos ≠ texto completo** (Req 6.6): OpenAlex entrega **metadatos** (y un
  resumen reconstruible desde un índice invertido), **no** el texto completo de
  las publicaciones. No se atribuye a la fuente acceso a texto completo ni otras
  capacidades no confirmadas (Req 10.4).

---

## 5. Otros proveedores — `PENDING_VALIDATION` (no implementados)

Los siguientes `Proveedor_API` **no** se implementan en este spec y se registran
como `PENDING_VALIDATION` (Req 6.5; ver `pending-validation.md`). Para cada uno,
su integración requeriría completar la plantilla genérica (§3) y confirmar
acceso, credenciales, cuotas y condiciones de uso antes de implementar:

| Proveedor_API | Estado | Nota |
|---------------|--------|------|
| **Scopus / Elsevier** | `PENDING_VALIDATION` | Requiere API key institucional; cuotas, costos y condiciones por confirmar. No implementado. |
| **Wiley** | `PENDING_VALIDATION` | Vía TDM API sujeta a acceso; por confirmar. No implementado. |
| **UNAL OAI-PMH** | `PENDING_VALIDATION` | Protocolo OAI-PMH (no API key); mecanismo y endpoint por confirmar. No implementado. |

La estrategia de **deduplicación entre fuentes** cuando se incorporen nuevos
proveedores también es `PENDING_VALIDATION` (ver `pending-validation.md`).

---

## 6. Fuentes consultadas

Documentación oficial de OpenAlex (Help Center / docs oficiales, consultadas
para este documento):

- [OpenAlex — Authentication](https://help.openalex.org/api/authentication/)
- [OpenAlex — Paging](https://help.openalex.org/api/paging/)
- [OpenAlex — Quickstart](https://help.openalex.org/quickstart/)

> **Nota de licencia**: el contenido de estas fuentes fue **reformulado y
> resumido** para cumplir con las restricciones de licencia; no se reproduce
> texto literal. Las cifras exactas de cuotas y costos no se transcriben y
> quedan `PENDING_VALIDATION` hasta su verificación contra la documentación
> oficial vigente.

---

## 7. Propuesta V1 y evolución futura

Este documento es la **propuesta inicial (V1)** del Equipo_Proyecto para la
integración de fuentes por API key. Podrá evolucionar tras:

- confirmar con SAO el alcance de fuentes autenticadas adicionales
  (Scopus/Wiley/UNAL) — `PENDING_VALIDATION`;
- verificar contra la documentación oficial vigente las cuotas y costos exactos
  de OpenAlex (con y sin key);
- confirmar el uso de filtros de idioma y tipo de documento a nivel de consulta.

Los puntos pendientes se consolidan en `pending-validation.md`.
