# Validación del Knowledge Graph (Tarea 5)

El proceso de validación del Knowledge Graph (KG) generado en las tareas anteriores asegura que el grafo materializado cumple con los patrones observados en los datos y con las restricciones de la ontología.

## Descripción del Knowledge Graph Validado

- **Deportes** y sus enlaces a Wikidata.
- **Competiciones**, **Grupos**, **Jornadas** y **Partidos**.
- **Resultados**, equipos (local/visitante) y ubicaciones geográficas (**Campos** y **Distritos**).

El grafo consta de **518.641 triplas** en formato N-Triples (`TAREA_4/kg/output.nt`).

## Metodología de Validación

Se ha optado por validar el KG desde dos perspectivas distintas:

### 1. Validación basada en Datos
- **Fuente:** Grafo RDF `TAREA_4/kg/output.nt`.  
Utilizamos `shexer` para la inferencia de patrones estructurales.
- **Resultado:** `shapes_from_data.ttl`. Esta validación analiza si el grafo es consistente con la topología inferida.

~~~bash
python3 TAREA_5/shapes/validation/generate_data_shapes.py
~~~


### 2. Validación basada en el Modelo
- **Fuente:** Ontología del dominio.
Definimos manualmente las shapes basadas en los requisitos de la ontología.
- **Resultado:** `shapes_from_ontology.ttl`. 

## Ejecución de Validación
`validate.py` utiliza `pySHACL` para validar el grafo contra ambos ficheros de shapes y genera informes detallados (`report_data_shapes.ttl` y `report_model_shapes.ttl`).

```bash
python3 TAREA_5/shapes/validation/validate.py
```

## Interpretación de Resultados

Tras las iteraciones de corrección, los resultados actuales son:

`report_data_shapes.ttl`
~~~
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms true .
~~~

`report_model_shapes.ttl`
~~~ 
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

[] a sh:ValidationReport ;
    sh:conforms true .
~~~
Esto significa que el grafo es conforme con las shapes, tanto las inferidas como las manuales.

### Hallazgos y Resoluciones Importantes:

1.  **Duplicidad de Datos (Resuelto):** Inicialmente se detectaron colisiones de IRIs entre diferentes sistemas de competición. Se solucionó actualizando el mapping YARRRML para incluir la columna específica de la fase en la construcción de URIs, garantizando que cada partido sea un recurso único.
2.  **Restricciones de Ontología:** Se ajustaron las propiedades `sameAs` para usar `sh:nodeKind sh:IRI` en lugar de `sh:datatype`. Así se asegura que los enlaces a Wikidata sean recursos y no literales, evitando errores de validación.

