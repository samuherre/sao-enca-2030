Samuel: "Volviendo al tema de la Bibliometría una de las funcionalidades que quiere SAO en su pagina, segun todo el contexto de los chats que hemos tenido, SAO quiere realizar este analisis de todos los articulos posibles que hayan en Colombia que hablen sobre conservacion de aves? esto lo pregunto para saber que keywords debe tener la consulta que se haga cuando se esten recaudando los datos y que sean todos los posibles verdad? por ejemplo, si se ponen de keywords coservation y birds y sale que hay 200.000 resultados la idea es que todos los 200.000 esten en el analisis bibliometrico?"

Respuesta chatGPT: Sí, estás entendiendo la intención general, pero hay una distinción muy importante que debemos hacer antes de definir las palabras clave y construir el mecanismo de recolección bibliográfica.

La idea es recuperar la mayor cantidad posible de publicaciones relevantes para la conservación de aves, no limitar artificialmente la búsqueda a unos pocos documentos. Sin embargo, eso no significa que todos los resultados que devuelva una consulta deban entrar automáticamente al análisis bibliométrico.

Te explico cómo entiendo el alcance que hemos definido para SAO y cómo deberíamos llevarlo a la práctica.
1. ¿Qué quiere analizar realmente SAO?
Al revisar el contexto de nuestras conversaciones, hay una decisión de alcance que ya habíamos documentado y aceptado como versión inicial:

Criterio	Alcance acordado
Periodo	2020–2030
Cobertura geográfica	No limitarse a Colombia; priorizar Colombia e incluir publicaciones internacionales relevantes
Temática	Aves y conservación
Tipos de documentos	Artículos científicos, revisiones, tesis, informes y documentos institucionales
Fuentes previstas	Google Scholar, Elsevier, Wiley-Blackwell, repositorios UNAL y Boletín SAO
Clasificación	Relación de las publicaciones con los 11 Objetos Focales de Conservación (OFC)
Estado de inclusión	INCLUIDO, EXCLUIDO o PENDIENTE_REVISIÓN

Por tanto, hay algo importante que quiero corregir de tu interpretación:

El proyecto no se planteó exclusivamente para encontrar artículos publicados en Colombia. Se planteó para identificar publicaciones relevantes para la conservación de aves, dando prioridad a Colombia, pero incluyendo también investigaciones internacionales que puedan aportar al análisis de SAO.

Esto significa que un artículo sobre conservación de aves en Brasil, Ecuador o cualquier otro país podría ser relevante, dependiendo de su contenido y de los criterios de inclusión.
2. ¿Qué pasa si buscamos conservation AND birds y aparecen 200.000 resultados?
Aquí está la diferencia fundamental entre recuperar información y construir el corpus bibliométrico.

Imagina este escenario:

Etapa 1. Recuperación de publicaciones
200.000
Resultados candidatos devueltos por diferentes consultas y fuentes bibliográficas.
Corpus bruto

Etapa 2. Depuración
- Identificar publicaciones repetidas.
- Normalizar títulos, autores y fechas.
- Identificar registros incompletos.
- Consolidar resultados de diferentes fuentes.

Etapa 3. Evaluación de relevancia
- ¿El documento realmente trata sobre aves?
- ¿Tiene relación con conservación?
- ¿Está dentro del periodo establecido?
- ¿Aporta información útil para el análisis?

Etapa 4. Corpus bibliométrico
Corpus depurado
Publicaciones que cumplen los criterios de inclusión, con las dudosas pendientes de revisión humana.
Corpus analizable

Los 200.000 resultados no deberían descartarse simplemente porque sean demasiados. Pero tampoco deberíamos asumir que los 200.000 son relevantes.

Por ejemplo, una búsqueda con conservation AND birds podría recuperar:
- Estudios sobre conservación de aves.
- Estudios sobre comportamiento de aves sin relación directa con conservación.
- Artículos sobre conservación de ecosistemas que mencionan aves incidentalmente.
- Investigaciones sobre especies amenazadas.
- Publicaciones sobre restauración de hábitats.
- Documentos duplicados.
- Investigaciones internacionales que no necesariamente aportan a los objetivos de SAO.
La consulta debe intentar recuperar ampliamente y el proceso posterior debe determinar qué publicaciones realmente pertenecen al corpus.
3. ¿Qué palabras clave deberíamos utilizar?
No recomendaría depender únicamente de conservation y birds. Esas dos palabras pueden ser un punto de partida, pero una estrategia bibliográfica robusta debe contemplar sinónimos, expresiones relacionadas y diferentes idiomas.

Por ejemplo:
Grupo	Palabras clave en inglés
Aves	birds, avian, bird species, wild birds
Conservación	conservation, bird conservation, species conservation
Amenazas	threatened species, endangered birds, habitat loss
Ecosistemas	habitat restoration, ecosystem restoration, forest conservation
Biodiversidad	biodiversity, avian biodiversity, species diversity
Investigación	population monitoring, species distribution, ecology

También debemos considerar términos en español y portugués:
Español	Portugués
Conservación de aves	Conservação de aves
Aves amenazadas	Aves ameaçadas
Biodiversidad	Biodiversidade
Restauración de hábitats	Restauração de habitats
Especies en peligro	Espécies ameaçadas

Pero hay una consideración: no todas estas palabras deberían utilizarse necesariamente en una única consulta con operadores AND. Podríamos excluir investigaciones importantes si exigimos que cada documento contenga todos los términos.

Lo correcto sería diseñar varias consultas complementarias, combinando sinónimos con operadores booleanos AND, OR y, cuando corresponda, NOT.
4. ¿Cómo debería funcionar el sistema que estamos construyendo?
Mi recomendación es que la recolección bibliográfica tenga dos objetivos separados:
Objetivo 1. Maximizar la recuperación
Obtener la mayor cantidad posible de publicaciones candidatas desde las fuentes disponibles.
- Consultas temáticas amplias.
- Variaciones de palabras clave.
- Consultas por idioma.
- Consultas por fuente.
- Registro de la consulta utilizada y su fecha.
Priorizar cobertura

Objetivo 2. Garantizar la calidad del corpus
Evaluar los resultados para determinar cuáles realmente sirven para el análisis.
- Deduplicación.
- Validación del periodo.
- Evaluación temática.
- Clasificación por OFC.
- Revisión humana de casos dudosos.
Priorizar relevancia y trazabilidad

Esto también tiene una implicación para nuestro clasificador de los 11 OFC: no deberíamos confundir la clasificación temática con la decisión de inclusión.

Por ejemplo:
- Una publicación puede ser relevante para la conservación de aves y todavía no tener un OFC identificado.
- Una publicación puede estar relacionada con varios OFC.
- Una publicación puede mencionar aves, pero no aportar realmente a la conservación.
- Una publicación puede necesitar revisión humana porque sus metadatos son insuficientes.
Por eso debemos conservar los estados INCLUIDO, EXCLUIDO y PENDIENTE_REVISIÓN que habíamos definido.
5. ¿Entonces debemos analizar los 200.000 artículos?
Mi respuesta sería:

Debemos intentar recuperar todos los resultados que podamos obtener legítimamente de las fuentes disponibles, pero debemos analizar bibliométricamente el corpus que resulte después de aplicar los criterios de inclusión y depuración.

Hay tres consideraciones adicionales:
1. Limitaciones de las fuentes: Google Scholar, por ejemplo, tiene restricciones de consulta y no permite asumir que podemos extraer masivamente todos sus resultados. En conversaciones anteriores habíamos identificado un límite práctico de aproximadamente 1.000 resultados por consulta. Por eso necesitamos varias fuentes y mecanismos de extracción compatibles con cada una.
2. Capacidad de procesamiento: 200.000 registros no son necesariamente imposibles de procesar, pero requieren una arquitectura de ingestión por lotes, almacenamiento, deduplicación y procesamiento escalable.
3. Trazabilidad: debemos poder explicar de dónde salió cada publicación, qué consulta la recuperó, cuándo se obtuvo y por qué fue incluida o excluida.
No debemos prometer que encontraremos absolutamente todas las publicaciones existentes: ninguna combinación de fuentes garantiza una cobertura universal.

6. ¿Cuál debería ser el propósito principal del corpus bibliométrico?

A. Panorama amplio de investigación sobre conservación de aves

Incluir publicaciones nacionales e internacionales relevantes, priorizando Colombia.

7. ¿Qué periodo debemos considerar?

2020–2030

Mi recomendación es construir un único corpus bibliográfico maestro, con dos perspectivas de análisis independientes:
1. Perspectiva Colombia: publicaciones que investigan la conservación de aves en Colombia, independientemente del país donde fueron publicadas.
2. Perspectiva internacional: publicaciones de cualquier país que aporten conocimiento sobre conservación de aves y puedan relacionarse con los Objetos Focales de Conservación (OFC).
Ambas perspectivas compartirán los mismos registros, pero cada publicación tendrá atributos que permitan identificar su alcance geográfico. Así evitamos mantener dos bases de datos desconectadas y podemos ofrecer filtros en el dashboard.

Hay una precisión importante: el periodo 2020–2030 debe aplicarse a la fecha de publicación. Como estamos en octubre de 2026, los años 2027–2030 representan una ventana futura. El sistema debe permitir incorporar publicaciones conforme vayan apareciendo, sin asumir que ya existen.
1. Definición del alcance bibliométrico
Propongo formalizarlo así:
Corpus bibliométrico SAO
Periodo de publicación
2020–2030

Cobertura temática
Conservación de aves

Cobertura geográfica
Colombia + internacional

Fuentes
Multifuente

Clasificación
11 OFC


Dos perspectivas de análisis
Colombia

Investigaciones sobre especies, ecosistemas y problemáticas colombianas.


Internacional

Investigaciones de otros países relevantes para la conservación de aves.




Una publicación colombiana también puede pertenecer al análisis internacional. No son categorías necesariamente excluyentes.
2. Diseño de las consultas bibliográficas
No recomiendo utilizar una sola consulta como:
conservation AND birds


Es demasiado general y puede recuperar muchos documentos que mencionan ambos conceptos sin estudiar realmente la conservación de aves.

Tampoco recomiendo una consulta como:
Colombia AND conservation AND birds


como única estrategia, porque excluiría investigaciones sobre Colombia que no mencionen explícitamente el país en sus metadatos.

Lo correcto es utilizar una estrategia de consultas por bloques temáticos.
Bloque A. Concepto central: aves
Inglés	Español	Portugués
bird*	ave*	ave*
avian	ornitología	avifauna
wild bird*	aves silvestres	aves silvestres
bird species	especies de aves	espécies de aves
waterbird*	aves acuáticas	aves aquáticas

Bloque B. Conservación
Inglés	Español	Portugués
conservation	conservación	conservação
protection	protección	proteção
threatened species	especies amenazadas	espécies ameaçadas
endangered species	especies en peligro	espécies ameaçadas
habitat restoration	restauración de hábitats	restauração de habitats
biodiversity conservation	conservación de biodiversidad	conservação da biodiversidade

Bloque C. Temáticas complementarias
Este bloque permite recuperar publicaciones que trabajan problemas de conservación sin utilizar necesariamente la palabra conservation.
Categoría	Términos
Amenazas	habitat loss, deforestation, fragmentation, climate change
Ecología	bird ecology, population ecology, species distribution
Restauración	ecological restoration, habitat restoration
Monitoreo	bird monitoring, population monitoring, species monitoring
Protección	protected areas, wildlife management, conservation planning
Especies	endemic birds, migratory birds, threatened birds

Importante: estos términos complementarios no deben utilizarse indiscriminadamente. Por ejemplo, un estudio de distribución de especies no necesariamente es un estudio de conservación. Debe pasar por los criterios de inclusión.
3. Consultas concretas que recomiendo implementar
La siguiente es una propuesta inicial de consultas. Cada fuente deberá adaptar su sintaxis, porque no todas soportan los mismos campos ni operadores.
Consulta 1. Conservación de aves (principal)

Inglés
(bird* OR avian OR "bird species")
AND
(conservation OR protection OR "threatened species")


Prioridad alta

Consulta 2. Conservación de aves en Colombia
(bird* OR avian OR "bird species")
AND
(conservation OR protection OR "habitat restoration")
AND
(Colombia OR Colombian OR Andes OR "Neotropical region")


Prioridad alta

Consulta 3. Amenazas y pérdida de hábitat
(bird* OR avian)
AND
("habitat loss" OR deforestation OR fragmentation
OR "climate change" OR pollution)


Complementaria

Consulta 4. Conservación y biodiversidad
(bird* OR avian OR avifauna)
AND
("biodiversity conservation" OR "protected areas"
OR "ecological restoration" OR "conservation planning")


Complementaria

Consulta 5. Especies amenazadas y monitoreo
(bird* OR "bird species")
AND
("threatened species" OR "endangered birds"
OR "population monitoring" OR "species monitoring")


Complementaria

Estas cinco consultas no representan todavía una estrategia bibliográfica validada. Son una propuesta para probar cobertura y relevancia en las fuentes seleccionadas.

Además, conviene construir sus equivalentes en español y portugués, especialmente para repositorios latinoamericanos.
4. Dónde y cómo ejecutar las consultas
No todas las fuentes bibliográficas funcionan igual. Por eso debemos diseñar un mecanismo de búsqueda que se adapte a cada proveedor.
Fuente	Estrategia recomendada
Google Scholar	Consultas separadas por combinación de términos y año; controlar límites de resultados.
Elsevier / Scopus	Buscar en título, resumen y palabras clave; aplicar filtro de año.
Wiley Online Library	Consultas temáticas y filtros de fecha disponibles.
Repositorios UNAL	Búsquedas en español e inglés, incluyendo tesis y documentos académicos.
Boletín SAO	Extracción de los PDF y metadatos disponibles.

Una precisión: en el contexto inicial del proyecto habíamos mencionado Elsevier y Wiley-Blackwell, pero no habíamos confirmado que todas las fuentes ofrecieran acceso automatizado o extracción masiva. Hay que revisar sus condiciones de acceso y las interfaces disponibles antes de construir los conectores.

Campos de búsqueda recomendados:
1. Título.
2. Resumen.
3. Palabras clave del autor.
4. Palabras clave de indexación, cuando estén disponibles.
Es mejor que la consulta busque en estos campos y no solamente en el título. Un artículo puede tratar sobre conservación de aves sin incluir esas palabras exactas en su título.

También aplicaría el periodo 2020–2030 como filtro de publicación, no como una palabra clave.
5. Criterios de inclusión y exclusión
Esta es la parte más importante. Las palabras clave recuperan candidatos; los criterios determinan cuáles pertenecen al corpus.

Te propongo formalizar una primera versión:
Criterios de inclusión
ID	Criterio	Condición
INC-01	Periodo	Publicación entre 2020 y 2030.
INC-02	Grupo biológico	El documento estudia aves, especies de aves o aspectos relevantes de su conservación.
INC-03	Relevancia temática	Aborda conservación, amenazas, protección, gestión, restauración, monitoreo o problemáticas que afecten a las aves.
INC-04	Relevancia geográfica	Puede estudiar Colombia o cualquier otro territorio, siempre que sea relevante para la temática del proyecto.
INC-05	Tipo documental	Artículo de investigación, artículo de revisión, tesis, informe técnico o publicación institucional con contenido científico o técnico pertinente.
INC-06	Información verificable	Tiene metadatos suficientes para identificar la publicación y evaluar su relevancia.

Criterios de exclusión
ID	Criterio	Condición
EXC-01	Fuera del periodo	Publicado antes de 2020 o después de 2030.
EXC-02	Sin relación con aves	El documento no estudia aves ni aporta información relevante sobre ellas.
EXC-03	Sin relación con conservación	Menciona aves incidentalmente, pero no aborda conservación ni una problemática relevante para ella.
EXC-04	Duplicado	Es el mismo documento recuperado desde otra fuente.
EXC-05	Documento no elegible	Es una noticia, opinión, contenido divulgativo sin sustento técnico o un registro que no corresponde a una publicación.
EXC-06	Información insuficiente	No existe información suficiente para verificar su identidad o relevancia, después de los intentos de recuperación de metadatos.

Hay un matiz importante con EXC-06: no descartaría automáticamente un documento porque no tenga resumen. Si el título, las palabras clave y otros metadatos permiten determinar su relevancia, podría incluirse. Si no es posible decidir, lo enviaría a revisión.
Criterios de clasificación geográfica
La clasificación geográfica debe ser independiente de la inclusión.
Categoría	Regla
COLOMBIA	La investigación estudia especies, ecosistemas, territorios o problemáticas de Colombia.
INTERNACIONAL	La investigación estudia otros territorios.
MULTIPAÍS	Incluye Colombia y otros países.
SIN_DETERMINAR	Los metadatos no permiten identificar el alcance geográfico.

No debemos utilizar la afiliación del autor como único indicador geográfico. Que un investigador trabaje en una universidad colombiana no significa que su artículo estudie Colombia.
6. Cómo debería funcionar el procesamiento en Kiro
Te propongo este flujo:
1. Estrategia de búsqueda

Consultas por tema, idioma, fuente y periodo


2. Recolección multifuente

Google Scholar, Elsevier, Wiley, repositorios y Boletín SAO


3. Normalización y deduplicación

DOI, título, autores, año y fuente


4. Evaluación de inclusión

Reglas automáticas + revisión humana de casos dudosos


5. Corpus bibliométrico consolidado

Publicaciones incluidas, excluidas y pendientes de revisión


6. Clasificación por OFC

Uno o varios de los 11 Objetos Focales de Conservación


7. Análisis bibliométrico

Tendencias, autores, instituciones, territorios, fuentes y OFC


Una decisión de diseño que te recomiendo
No guardes solamente el resultado final de cada búsqueda. Guarda también la procedencia de cada registro.

Por ejemplo, una publicación puede aparecer en tres consultas y dos fuentes. Debería existir un único registro bibliográfico, pero conservar sus distintas procedencias.

Para eso sugiero separar conceptualmente:
- articles: publicación bibliográfica única.
- search_runs: ejecución de una consulta.
- article_sources: fuentes en las que apareció cada publicación.
- article_classifications: clasificación temática y OFC.
- article_screening: decisión de inclusión, exclusión o revisión, con justificación.
Esto permite responder preguntas como:
- ¿Cuántas publicaciones se encontraron en cada fuente?
- ¿Cuántas fueron recuperadas por cada consulta?
- ¿Cuántas eran duplicados?
- ¿Cuántas se incluyeron finalmente?
- ¿Qué publicaciones fueron clasificadas en cada OFC?
- ¿Cuántas necesitan revisión humana?
7. Campos que debería guardar cada publicación
Partiendo del contrato de datos que ya habíamos definido para el proyecto, propongo mantener los campos existentes y ampliarlos gradualmente.
Campo	Propósito
article_id	Identificador interno único.
title	Título de la publicación.
authors	Autores.
publication_year	Año de publicación.
source	Fuente de recuperación.
doi	Identificador DOI, si existe.
abstract	Resumen, si está disponible.
keywords	Palabras clave.
document_type	Tipo documental.
geographic_scope	Colombia, internacional, multipaís o sin determinar.
country_studied	País o países estudiados, cuando puedan identificarse.
search_query_id	Referencia a la consulta que recuperó el registro, mediante la relación de procedencia.
extraction_date	Fecha de recuperación.
processing_status	Estado del procesamiento.
is_duplicate	Indicador de duplicación, conservado por compatibilidad con el contrato actual.
inclusion_status	Incluido, excluido o pendiente de revisión.
exclusion_reason	Justificación de exclusión.
ofc_classification	Uno o varios OFC asignados.

No es necesario que todos los campos estén disponibles desde la primera fuente. Debemos permitir valores desconocidos sin inventarlos.
8. Cómo validar si las consultas están funcionando
Antes de recolectar cientos de miles de registros, haría una prueba piloto.

Mi propuesta:
1. Ejecutar las cinco consultas principales en una o dos fuentes accesibles.
2. Recuperar una muestra de resultados de cada consulta.
3. Unificar los registros.
4. Identificar duplicados.
5. Revisar manualmente una muestra de publicaciones relevantes y no relevantes.
6. Medir cuántas publicaciones verdaderamente relacionadas con conservación de aves recupera cada consulta.
7. Ajustar los términos y repetir.
Aquí necesitamos evaluar dos cosas:
- Cobertura: si las consultas están encontrando publicaciones importantes que conocemos o que identificamos en búsquedas de referencia.
- Precisión: qué proporción de los resultados recuperados realmente cumple los criterios de inclusión.
No podemos afirmar que una búsqueda recuperó toda la literatura existente solo porque obtuvo muchos resultados.
9. Qué cambiaría en la documentación actual del proyecto
Recuerda que ya tienes article-data-contract.md e inclusion-exclusion-criteria.md. No empezaría desde cero ni reemplazaría sus decisiones sin trazabilidad.

Actualizaría esos documentos con una nueva versión de alcance, incorporando:
- Corpus único con dos perspectivas geográficas.
- Consultas multilingües y complementarias.
- Criterios de inclusión y exclusión anteriores.
- Registro de las consultas y fuentes de recuperación.
- Clasificación geográfica independiente de la clasificación OFC.
- Evaluación de cobertura y precisión de las búsquedas.

Mi recomendación final
Hay algo que considero especialmente importante para el éxito de este proyecto: no debemos medir el éxito del sistema por la cantidad de artículos recolectados, sino por la capacidad de recuperar publicaciones relevantes, justificar su inclusión y clasificarlas correctamente.

Por ejemplo, recuperar 200.000 registros y terminar con 40.000 publicaciones relevantes puede ser un resultado mucho más valioso que recuperar 200.000 y clasificarlas todas automáticamente sin validar su pertinencia.

Antes de convertir esta propuesta en una especificación definitiva, hay una decisión que convendría validar con SAO: si quieren que el corpus incluya exclusivamente literatura científica y técnica o también documentos de divulgación y otros materiales institucionales. Esa decisión puede cambiar considerablemente el volumen de resultados.

La estrategia debe conservar lo que ya construiste: los 35 documentos del Boletín SAO son un primer conjunto real sobre el cual podemos seguir probando la extracción, deduplicación y clasificación.