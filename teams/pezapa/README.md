# Proyecto LOT4KG - Pezapa

## Resumen

Este directorio recoge el trabajo del grupo `pezapa` para las tareas 1 a 6 de la metodologia LOT4KG. El proyecto toma como dominio los teatros y auditorios de Galicia y construye un flujo completo desde la preparacion de datos hasta la explotacion SPARQL del Knowledge Graph con enriquecimiento desde Wikidata.

## Equipo y dataset

### Equipo

- Pablo Perez Rodriguez - <https://github.com/Veleiroo>
- Jaime Jose Zapico Lopez - <https://github.com/jaimezl03>
- Oscar Padin Devesa - <https://github.com/oscarpd13>

### Dataset seleccionado

- Nombre: `Teatros e auditorios`
- Fuente original: <https://abertos.xunta.gal/catalogo/cultura-ocio-deporte/-/dataset/0305/teatros-auditorios>
- Dominio: espacios culturales de Galicia con informacion de ubicacion, contacto y aforamiento

## Estructura de la carpeta

```text
group_info.yml
README.md
data cleaning/
  history.json
  teatros-auditorios.csv
ontology/
  Modelo.png
  ontology.ttl
mappings/
  mappings.yarrrm.yaml
  mapping.rml.ttl
  config.ini
kg/
  output.ttl
queries/
  local_query_1.rq
  local_query_2.rq
  local_query_3.rq
  federated_query_1.rq
  federated_query_2.rq
src/
  run_queries.py
  app.py
results/
  query_results/
    local_query_1.csv
    local_query_2.csv
    local_query_3.csv
    federated_query_1.csv
    federated_query_2.csv
    municipalities_enriched.csv
    linked_spaces_enriched.csv
  figures/
    spaces_by_province.png
    municipalities_spaces_vs_population.png
  maps/
    linked_spaces_map.html
shapes/
  shapes_from_data.ttl
  shapes_from_ontology_or_mappings.ttl
  validation/
    generate_data_shapes.py
    validate_shapes.py
    validate_data_shapes.py
    validate_ontology_or_mappings_shapes.py
    report_data_shapes.ttl
    report_model_shapes.ttl
```

## Tarea 1 - Registro del grupo

La trazabilidad del grupo se deja en `group_info.yml`, donde se recogen:

- los integrantes del equipo
- el dataset elegido
- la URL oficial del recurso
- una descripcion breve del dominio de trabajo

Con esto queda fijado desde el inicio el caso de uso del proyecto y la fuente de datos que se reutiliza en el resto de tareas.

## Tarea 2 - Data preparation con OpenRefine

### Ficheros entregados

- Dataset limpio: `data cleaning/teatros-auditorios.csv`
- Historial reproducible de OpenRefine: `data cleaning/history.json`
- Fuente original del dataset: URL del portal de datos abiertos indicada arriba

### Trabajo realizado

El fichero `history.json` contiene `35` operaciones de OpenRefine. Las transformaciones principales fueron:

- separacion de la columna `ENDEREZO` para extraer `ENDEREZO` y `NUMERO`
- separacion de `COORDENADAS` en `LATITUD` y `LONGUITUD`
- normalizacion de valores como `Avenida` -> `Avda.`
- limpieza de `s/n` y conversion de `NUMERO` a valor numerico cuando fue posible
- conversion de `AFORAMENTO` a numero
- reconciliacion con Wikidata de `CONCELLO`, `PROVINCIA` y varios valores de `ESPAZO`

### Resultado del dataset limpio

El CSV limpio contiene `46` filas. Ademas, la reconciliacion deja columnas con identificadores externos:

- `URL_CONCELLO`: `46/46` filas con enlace
- `URL_PROVINCIA`: `46/46` filas con enlace
- `URL_ESPAZO`: `12/46` filas con enlace

Este resultado deja el dataset listo para el mapping a RDF, con municipios y provincias ya enlazados de forma estable y una parte de los espacios reconciliados contra Wikidata.

## Tarea 3 - Modelado de la ontologia

### Artefactos entregados

- Diagrama del modelo: `ontology/Modelo.png`
- Ontologia en Turtle: `ontology/ontology.ttl`

### Alcance del modelo

La ontologia representa espacios culturales y sus datos minimos de localizacion y contacto. El nucleo del modelo se basa en cinco clases:

- `ta:Espazo`
- `ta:Enderezo`
- `ta:DatoContacto`
- `ta:Concello`
- `ta:Provincia`

Las relaciones principales son:

- `ta:estaen` entre `Espazo` y `Enderezo`
- `ta:tiene` entre `Espazo` y `DatoContacto`
- `ta:pertenece` entre `Enderezo` y `Concello`
- `ta:ubicadoen` entre `Concello` y `Provincia`

Los atributos literales mas relevantes son:

- `ta:label`
- `ta:aforamiento`
- `ta:calle`
- `ta:numero`
- `ta:CP`
- `ta:latitud`
- `ta:longitud`
- `ta:telefono`
- `ta:email`
- `ta:web`
- `ta:nombre`

### Herramienta y decision de modelado

La ontologia se modelo con Chowlk y se exporto a Turtle. En `ontology/ontology.ttl` se conserva la metadata generada, incluyendo `mod:createdWith <https://chowlk.linkeddata.es/>`.

El espacio de nombres funcional usado en clases y propiedades es:

```text
http://example.org/def/teatrosyauditorios#
```

### Nota sobre publicacion

En esta carpeta se conservan el diagrama y el fichero TTL de la ontologia. No se incluye localmente una carpeta de documentacion automatica de OnToology ni una URL publica de GitHub Pages.

## Tarea 4 - Construccion del Knowledge Graph

### Ficheros entregados

- Mapping en YARRRML: `mappings/mappings.yarrrm.yaml`
- Mapping traducido a RML: `mappings/mapping.rml.ttl`
- Configuracion de Morph-KGC: `mappings/config.ini`
- Grafo materializado: `kg/output.ttl`

### Diseno del mapping

El mapping genera cinco tipos de recursos:

- `ex:espazo/{ESPAZO}`
- `ex:enderezo/{ESPAZO}`
- `ex:contacto/{ESPAZO}`
- `ex:concello/{CONCELLO}`
- `ex:provincia/{PROVINCIA}`

La transformacion parte del CSV limpio y crea cinco Triples Maps, uno por entidad principal:

- `ESPAZO`
- `ENDEREZO`
- `DATOCONTACTO`
- `CONCELLO`
- `PROVINCIA`

Las decisiones de modelado mas importantes fueron:

- separar la informacion del espacio, su direccion y su contacto en recursos distintos
- tipar `AFORAMENTO` y `CÓDIGO POSTAL` como enteros y `LATITUD` y `LONGUITUD` como decimales
- enlazar ayuntamientos y provincias mediante URIs propias construidas desde el CSV

Despues de la materializacion base, el KG se enriquece con enlaces normalizados a Wikidata a partir de las columnas reconciliadas del CSV limpio:

- `owl:sameAs` para `Concello` y `Provincia`
- `rdfs:seeAlso` para `Espazo` cuando el enlace externo no es ambiguo

Este paso transforma las URLs `https://www.wikidata.org/wiki/Q...` del CSV en IRIs de entidad `http://www.wikidata.org/entity/Q...`, que son las que se pueden explotar correctamente en consultas federadas.

### Comandos de trabajo

Un flujo compatible con los ficheros entregados es:

```bash
yatter -i mappings/mappings.yarrrm.yaml -o mappings/mapping.rml.ttl
python3 -m morph_kgc mappings/config.ini
```

### Resultado del KG

El Knowledge Graph conservado en `kg/output.ttl` contiene `893` triples y materializa:

- `44` recursos `ta:Espazo`
- `44` recursos `ta:Enderezo`
- `44` recursos `ta:DatoContacto`
- `40` recursos `ta:Concello`
- `4` recursos `ta:Provincia`

Ademas, el KG enriquecido incluye:

- `44` enlaces `owl:sameAs` hacia entidades de Wikidata
- `9` enlaces `rdfs:seeAlso` hacia entidades de Wikidata

El CSV limpio tiene `46` filas, pero el KG solo contiene `44` espacios porque hay nombres duplicados que generan colisiones de URI al usar `ESPAZO` como identificador:

- `Auditorio Rocio Jurado`
- `Teatro Principal`

En ambos casos, filas de municipios distintos acaban fusionadas en un mismo recurso RDF.

### Observacion sobre la salida

El fichero `mappings/config.ini` queda alineado con la entrega final y materializa directamente en `kg/output.ttl` con formato Turtle. El KG conservado en la carpeta ya incluye enlaces a Wikidata listos para su explotacion en la tarea 6.

## Tarea 5 - Validacion del Knowledge Graph

### Artefactos entregados

- Shapes desde datos: `shapes/shapes_from_data.ttl`
- Shapes desde ontologia y mappings: `shapes/shapes_from_ontology_or_mappings.ttl`
- Script generico de validacion: `shapes/validation/validate_shapes.py`
- Scripts especificos:
  - `shapes/validation/validate_data_shapes.py`
  - `shapes/validation/validate_ontology_or_mappings_shapes.py`
- Informes RDF:
  - `shapes/validation/report_data_shapes.ttl`
  - `shapes/validation/report_model_shapes.ttl`

### Enfoque seguido

La validacion se planteo comparando dos perspectivas:

1. validacion basada en datos, con shapes inferidas desde el RDF materializado mediante SheXer
2. validacion basada en modelo, con shapes definidas a partir de la ontologia y del mapping RML

### Shapes desde datos

Para inferir shapes desde el KG se uso `SheXer`. El script `shapes/validation/generate_data_shapes.py`:

- toma como entrada `kg/output.ttl`
- genera `shapes/shapes_from_data.ttl`
- usa una configuracion relativamente estricta
- corrige la serializacion `sh:dataType` a `sh:datatype` para que sea compatible con `pyshacl`

### Shapes desde modelo y mappings

El fichero `shapes/shapes_from_ontology_or_mappings.ttl` se definio manualmente a partir de:

- las clases y propiedades de `ontology/ontology.ttl`
- los datatypes esperados por el modelo
- las cardinalidades sugeridas por `mapping.rml.ttl`

Como decision concreta, `ta:numero` se dejo opcional porque el dataset contiene muchos registros sin ese valor.

### Ejecucion de la validacion

Los scripts se ejecutan desde `teams/pezapa` con:

```bash
python3 -m pip install --user shexer pyshacl
python3 shapes/validation/generate_data_shapes.py
python3 shapes/validation/validate_data_shapes.py
python3 shapes/validation/validate_ontology_or_mappings_shapes.py
```

Tambien puede usarse el script generico:

```bash
python3 shapes/validation/validate_shapes.py \
  --label data-shapes \
  --shapes shapes/shapes_from_data.ttl \
  --report shapes/validation/report_data_shapes.ttl

python3 shapes/validation/validate_shapes.py \
  --label model-shapes \
  --shapes shapes/shapes_from_ontology_or_mappings.ttl \
  --report shapes/validation/report_model_shapes.ttl
```

### Resultados

#### Validacion con shapes inferidas desde datos

- `Conforms: False`
- `22` resultados en el resumen textual de pySHACL
- informe RDF: `shapes/validation/report_data_shapes.ttl`

Interpretacion:

- predominan violaciones de `sh:maxCount`
- los recursos mas conflictivos son `Auditorio Rocio Jurado` y `Teatro Principal`
- aparecen multiples valores donde el modelo esperado es unico: `aforamiento`, `calle`, `CP`, `latitud`, `longitud`, `telefono`, `email`, `web` y `pertenece`
- los enlaces a Wikidata anadidos en `Concello`, `Provincia` y parte de `Espazo` no introducen errores nuevos en esta validacion, porque el conflicto principal sigue estando en la fusion de recursos por URI

#### Validacion con shapes del modelo

- `Conforms: False`
- `111` resultados en el resumen textual de pySHACL
- informe RDF: `shapes/validation/report_model_shapes.ttl`

Interpretacion:

- se mantienen las colisiones de URI detectadas con las shapes inferidas desde datos
- se anaden muchas violaciones de datatype en `ta:telefono`
- la ontologia define `ta:telefono` con rango `xsd:integer`, pero el KG contiene literales como `"981 716 001"` o `"986 304 108"`
- los enlaces externos anadidos para preparar la explotacion con Wikidata no cambian el numero de violaciones, porque las shapes del modelo no cierran el grafo sobre propiedades adicionales

## Problemas detectados y decisiones de diseno

### 1. Colisiones de URI en el mapping

El uso de `{ESPAZO}` como identificador para `Espazo`, `Enderezo` y `DatoContacto` provoca fusiones de recursos cuando dos filas distintas comparten nombre. Esto ocurre al menos con:

- `Auditorio Rocio Jurado`
- `Teatro Principal`

Una mejora natural seria construir las URIs con mas contexto, por ejemplo combinando nombre y municipio o reutilizando identificadores externos cuando existan.

### 2. Desajuste entre ontologia y datos

La ontologia modela `ta:telefono` como `xsd:integer`, mientras que el CSV limpio conserva telefonos con espacios y el mapping los materializa como cadenas. La validacion basada en modelo detecta este problema de forma inmediata.

### 3. Cobertura desigual de reconciliacion

Municipios y provincias quedaron completamente enlazados, pero la reconciliacion de espacios fue parcial (`12/46`). Esto no impide construir el KG, pero limita la interlinking externa del recurso principal.

### 4. Integracion de enlaces externos en el flujo

El CSV limpio ya contenia URLs a Wikidata, pero el mapping base no las materializaba en el KG. Para dejar el grafo preparado para explotacion federada, se incorporo un paso reproducible de enriquecimiento posterior a la materializacion.

## Tarea 6 - Explotacion del Knowledge Graph

### Artefactos entregados

- Consultas locales:
  - `queries/local_query_1.rq`
  - `queries/local_query_2.rq`
  - `queries/local_query_3.rq`
- Consultas a Wikidata:
  - `queries/federated_query_1.rq`
  - `queries/federated_query_2.rq`
- Script de ejecucion de consultas: `src/run_queries.py`
- Script de visualizacion: `src/app.py`
- Resultados tabulares: `results/query_results/`
- Figuras: `results/figures/`
- Mapa HTML: `results/maps/linked_spaces_map.html`

### Objetivo de la explotacion

La tarea 6 se planteo como una pequena exploracion analitica del KG de teatros y auditorios de Galicia con dos capas:

1. consulta del KG local para obtener rankings y subconjuntos relevantes
2. enriquecimiento con Wikidata a partir de los enlaces presentes en `owl:sameAs` y `rdfs:seeAlso`

Con esto se cubren los minimos obligatorios del enunciado:

- uso de SPARQL sobre el KG propio
- uso de Wikidata como fuente externa
- explotacion posterior mediante una pequena aplicacion Python que genera tablas, figuras y un mapa

### Consultas SPARQL locales

Las consultas locales se ejecutan con `RDFLib` sobre `kg/output.ttl`:

- `local_query_1.rq`: cuenta cuantos espacios culturales hay por provincia
- `local_query_2.rq`: obtiene estadisticas por municipio enlazado con Wikidata (`numSpaces`, `avgCapacity`)
- `local_query_3.rq`: selecciona los espacios con enlace directo a Wikidata y coordenadas consistentes

Estas consultas generan:

- `results/query_results/local_query_1.csv`
- `results/query_results/local_query_2.csv`
- `results/query_results/local_query_3.csv`

### Consultas a Wikidata

Las consultas federadas se apoyan en los enlaces ya presentes en el KG:

- `owl:sameAs` para municipios
- `rdfs:seeAlso` para espacios culturales enlazados

Para garantizar reproducibilidad en este entorno, la federacion se implemento en dos pasos:

1. se extraen del KG local los IRIs de Wikidata con SPARQL
2. `src/run_queries.py` ejecuta las consultas `federated_query_1.rq` y `federated_query_2.rq` contra el endpoint de Wikidata usando `VALUES`

Este enfoque sigue explotando el KG como punto de partida y evita depender de `SERVICE`, que dio problemas de ejecucion con `RDFLib` en local.

Las consultas remotas recuperan:

- para municipios: `population`, `coord` y `officialWebsite`
- para espacios: `instanceOfLabel`, `inception`, `coord` y `officialWebsite`

Los resultados se guardan en:

- `results/query_results/federated_query_1.csv`
- `results/query_results/federated_query_2.csv`
- `results/query_results/municipalities_enriched.csv`
- `results/query_results/linked_spaces_enriched.csv`

### Script de explotacion y visualizacion

El flujo reproducible es:

```bash
python3 -m pip install --user rdflib pandas matplotlib SPARQLWrapper
python3 src/run_queries.py
python3 src/app.py
```

`src/run_queries.py`:

- carga el KG local
- ejecuta las consultas SPARQL locales
- reutiliza los enlaces a Wikidata extraidos del propio grafo
- consulta Wikidata y fusiona los resultados externos con los locales

`src/app.py`:

- genera la figura `results/figures/spaces_by_province.png`
- genera la figura `results/figures/municipalities_spaces_vs_population.png`
- genera el mapa `results/maps/linked_spaces_map.html`

### Resultados obtenidos

#### Consulta local por provincia

La distribucion de espacios culturales por provincia es:

- `A Coruña Province`: `22`
- `Pontevedra Province`: `13`
- `Lugo Province`: `6`
- `Ourense`: `5`

Este resultado queda visualizado en `results/figures/spaces_by_province.png`.

#### Enriquecimiento de municipios con Wikidata

Tras fusionar los resultados locales con Wikidata, `municipalities_enriched.csv` contiene `40` municipios enlazados. Algunos resultados destacados son:

- `Ourense`: `3` espacios y capacidad media `572.67`
- `Santiago de Compostela`: `3` espacios y capacidad media `355.33`
- `Cangas`: `2` espacios y `7.49` espacios por cada `100000` habitantes

La figura `results/figures/municipalities_spaces_vs_population.png` combina:

- numero de espacios locales
- poblacion obtenida de Wikidata
- capacidad media de los espacios

### Espacios enlazados y mapa

El KG contiene `8` espacios culturales con enlace directo a Wikidata y coordenadas consistentes tras filtrar recursos ambiguos o fusionados. El mas grande es:

- `Pazo da Cultura de Narón`: `900` plazas

El mapa `results/maps/linked_spaces_map.html` representa estos espacios con:

- coordenadas del KG local
- tipo e informacion temporal desde Wikidata
- enlace a sitio oficial cuando esta disponible

### Interpretacion

La explotacion confirma que los enlaces a Wikidata aportan valor practico al KG:

- permiten cruzar estadisticas locales con poblacion y metadatos externos
- facilitan visualizaciones mas ricas que una consulta aislada sobre el RDF local
- muestran que el KG puede servir como base para exploracion y analisis reproducibles

Tambien aparecen dos limitaciones del dataset y del modelado:

- la interlinking de espacios sigue siendo parcial (`8` casos explotables de forma limpia)
- las colisiones de URI detectadas en la tarea 5 obligan a filtrar algunos recursos antes de explotarlos

## Conclusiones

El proyecto cubre el flujo completo de LOT4KG para este caso de uso:

- seleccion del dominio y registro del grupo
- limpieza y enriquecimiento del dataset con OpenRefine
- modelado de una ontologia propia
- definicion de mappings YARRRML/RML y materializacion del KG
- enriquecimiento reproducible del KG con enlaces a Wikidata
- validacion SHACL desde datos y desde modelo
- explotacion del grafo mediante SPARQL, enriquecimiento con Wikidata y visualizacion

La validacion final fue especialmente util para detectar dos problemas reales del proyecto:

- la construccion de URIs con colisiones por nombres no unicos
- la incoherencia entre el datatype definido para `ta:telefono` y los valores que llegan desde los datos

Estos resultados muestran la diferencia entre describir como son los datos, prescribir como deberian ser segun el modelo y explotarlos despues con fuentes externas. Ese encadenamiento entre tareas era precisamente uno de los objetivos de LOT4KG en este proyecto.
