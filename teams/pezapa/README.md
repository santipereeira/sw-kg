# Tarea 5 - Validacion del Knowledge Graph

## Resumen

En esta tarea se ha validado el Knowledge Graph generado en `kg/output.ttl` a partir del dataset de teatros y auditorios de Galicia. La validacion se ha planteado desde dos enfoques:

- uno basado en los datos materializados, generando shapes con SheXer
- otro basado en el modelo del proyecto, a partir de la ontologia y del mapping RML

El objetivo no era solo ejecutar `pyshacl`, sino comprobar si el KG cumple las restricciones que se observan en los datos y las restricciones que deberia cumplir segun el modelo.

## Recursos utilizados

- KG materializado: `kg/output.ttl`
- Ontologia: `ontology/ontology.ttl`
- Mapping RML: `mappings/mapping.rml.ttl`

Las clases principales del grafo son `ta:Espazo`, `ta:Enderezo`, `ta:DatoContacto`, `ta:Concello` y `ta:Provincia`.

## Estructura de entrega

- `shapes/shapes_from_data.ttl`
- `shapes/shapes_from_ontology_or_mappings.ttl`
- `shapes/validation/generate_data_shapes.py`
- `shapes/validation/validate_shapes.py`
- `shapes/validation/validate_data_shapes.py`
- `shapes/validation/validate_ontology_or_mappings_shapes.py`
- `shapes/validation/report_data_shapes.ttl`
- `shapes/validation/report_model_shapes.ttl`

## Metodologia seguida

### 1. Shapes a partir del RDF materializado

Se ha utilizado SheXer para inferir shapes SHACL directamente desde `kg/output.ttl`. El script `shapes/validation/generate_data_shapes.py` genera el fichero `shapes/shapes_from_data.ttl`.

Decisiones relevantes:

- se ha usado `all_classes_mode=True` para cubrir todas las clases con instancias en el KG
- se ha configurado la extraccion de forma relativamente estricta para que afloren recursos fusionados y cardinalidades anomales
- se ha corregido la salida de SheXer de `sh:dataType` a `sh:datatype` para asegurar compatibilidad con `pyshacl`

### 2. Shapes a partir de ontologia y mappings

Se ha construido un segundo conjunto de shapes en `shapes/shapes_from_ontology_or_mappings.ttl`, derivado de:

- las clases y propiedades definidas en `ontology/ontology.ttl`
- los datatypes y rangos del modelo
- las cardinalidades que se desprenden del `mapping.rml.ttl`

No se ha usado una herramienta automatica tipo SCOOP. En su lugar, se han definido shapes manuales y razonadas, lo cual sigue cumpliendo el objetivo de validar el KG contra restricciones del modelo.

Decision relevante:

- `ta:numero` se ha dejado como propiedad opcional porque en el dataset hay muchos registros sin ese valor

### 3. Validacion con pySHACL

La validacion se ha hecho con `pyshacl` mediante:

- `shapes/validation/validate_data_shapes.py`
- `shapes/validation/validate_ontology_or_mappings_shapes.py`

Ambos scripts reutilizan `shapes/validation/validate_shapes.py`, que:

- carga el KG
- carga el fichero de shapes correspondiente
- ejecuta la validacion
- muestra por pantalla si el grafo conforma o no
- guarda el informe de validacion en RDF

No se ha activado inferencia RDFS en la validacion final por defecto, para evitar que los tipos inferidos desde la ontologia distorsionen la lectura de los informes.

## Comandos ejecutados

Los siguientes comandos se ejecutan desde la carpeta `teams/pezapa`:

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

## Resultados de validacion

### Validacion con shapes inferidas desde datos

Resultado:

- `Conforms: False`
- resumen textual de `pyshacl`: `22` violaciones
- informe RDF: `shapes/validation/report_data_shapes.ttl`

Interpretacion:

- casi todas las violaciones son de `sh:maxCount`
- los recursos mas problematicos son `Auditorio Rocio Jurado` y `Teatro Principal`
- aparecen multiples valores en propiedades que deberian ser unicas: `aforamiento`, `calle`, `CP`, `latitud`, `longitud`, `telefono`, `email`, `web` y `pertenece`

### Validacion con shapes del modelo

Resultado:

- `Conforms: False`
- resumen textual de `pyshacl`: `111` violaciones
- informe RDF: `shapes/validation/report_model_shapes.ttl`

Interpretacion:

- se mantienen las violaciones de cardinalidad asociadas a recursos fusionados
- ademas aparecen muchas violaciones de datatype en `ta:telefono`
- la ontologia define `ta:telefono` con rango `xsd:integer`, pero el KG contiene literales como `"981 716 001"`

Nota:

- en los informes RDF aparecen mas nodos `sh:ValidationResult` que en el resumen textual porque `pyshacl` serializa tambien detalles anidados de las violaciones por `sh:node`

## Problemas detectados

### 1. Colision de URIs en el mapping

La principal fuente de errores parece estar en el mapping. Varias URIs se construyen solo con `{ESPAZO}`, por ejemplo para:

- `Espazo`
- `Enderezo`
- `DatoContacto`

Esto provoca que dos filas distintas con el mismo nombre de espacio acaben materializadas como un unico recurso RDF. Como consecuencia, ese recurso acumula varios valores en propiedades que conceptualmente deberian ser unicas.

### 2. Inconsistencia entre modelo y datos

En la ontologia, `ta:telefono` esta modelado como `xsd:integer`, pero en el KG se genera como string con espacios. La validacion basada en modelo detecta esta inconsistencia de forma inmediata.

## Relacion con los puntos de la Tarea 5

### Punto 1

Generar shapes SHACL a partir del RDF materializado.

- Cumplido con `shapes/shapes_from_data.ttl`

### Punto 2

Generar otro conjunto de shapes a partir de la ontologia y/o de los mappings.

- Cumplido con `shapes/shapes_from_ontology_or_mappings.ttl`

### Punto 3

Revisar y ajustar las shapes generadas automaticamente.

- Cumplido
- se ha corregido la salida de SheXer para hacerla valida para `pyshacl`
- se han ajustado manualmente restricciones del modelo donde hacia falta

### Punto 4

Validar el grafo con `pyshacl`.

- Cumplido con los scripts de validacion y los informes RDF generados

### Punto 5

Analizar el resultado e identificar errores o inconsistencias.

- Cumplido
- se han identificado problemas reales en el mapping y en el datatype de `ta:telefono`

## Conclusiones

La Tarea 5 esta bien resuelta como entrega. Hay dos conjuntos de shapes, hay scripts reproducibles, hay informes de validacion y hay una interpretacion clara de los resultados.

El hecho de que el grafo no conforme no significa que la tarea este mal hecha. Al contrario, la validacion ha servido para localizar errores reales del KG, que era precisamente el objetivo de la practica.

## Trabajo futuro

Si se quisiera mejorar el KG despues de esta entrega, los siguientes pasos razonables serian:

- corregir el mapping para evitar colisiones de URIs
- normalizar el telefono antes de materializar el grafo
- regenerar `kg/output.ttl`
- repetir la validacion para comprobar si disminuyen las violaciones
