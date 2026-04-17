# Construcción del Knowledge Graph (Tarea 4)

## Dataset Utilizado

Se ha utilizado el dataset `ontologia-deportes.csv`, que contiene información detallada sobre los Juegos Deportivos Municipales de Madrid:
- **Entidades:** Deportes, Competiciones, Grupos, Jornadas, Partidos, Equipos, Campos y Distritos.
- **Atributos:** Resultados, fechas (normalizadas a `xsd:dateTime`), estados de los partidos y coordenadas geográficas.
- **Enlaces Externos:** Identificadores de Wikidata para deportes y distritos de Madrid.

## Modelado de la Transformación (Mappings)

### Estructura del Mapping:
- **Sujetos:** Para los partidos se utiliza una combinación de Fase, Deporte, Grupo, Jornada y Partido para evitar colisiones: `ns:partido/$(Nombre_fase)_$(Nombre_deporte)_$(Codigo_grupo)_$(Jornada)_$(Partido)`.
- **Predicados y Objetos:**
    - Asignación de clases (`rdf:type`) según la ontología.
    - Mapeo de literales con datatypes específicos (`xsd:string`, `xsd:integer`, `xsd:dateTime`, `xsd:float`).
    - Enlaces a Wikidata mediante `ns:sameAsDeporte` y `ns:sameAsDistrito`.
- **Relaciones (Joins):** Conexiones semánticas entre entidades (ej: un Partido `ns:ocurreEn` un Campo).

## Instrucciones de Ejecución

El proceso de generación mediante scripts:

### 1. Traducción de YARRRML a RML
Utilizamos `yatter` para convertir las reglas humanas a lenguaje RML ejecutable:
```bash
python3 TAREA_4/mappings/yarrml_a_rml.py
```

### 2. Generación del Knowledge Graph (Materialización)
Utilizamos `Morph-KGC` configurado mediante config.ini:
```bash
python3 -m morph_kgc TAREA_4/mappings/config.ini
```
~~~ini
[CONFIGURATION]
na_values=NA,N/A,null
output_file=TAREA_4/kg/output.nt
output_format=N-TRIPLES

[DataSource]
mappings=TAREA_4/mappings/mapping.rml.ttl 
~~~

El resultado se genera en formato N-Triples en `TAREA_4/kg/output.nt`.

## Decisiones de Diseño y Observaciones

- **Unicidad de IRIs:** Se descubrió que la columna `SISTEMA_COMPETICION` era demasiado genérica para actuar como clave primaria de la competición. Se optó por usar `Nombre_fase` en los templates de IRIs para garantizar la integridad referencial y evitar que datos de partidos distintos se fusionaran en el mismo nodo.
- **Manejo de Caracteres Especiales:** Se emplea la directiva `~iri` en las plantillas de YARRRML para asegurar que los nombres de los deportes o distritos con espacios o acentos se codifiquen correctamente en las URIs.
- **Limpieza Previa:** Tuvmos que alterar el pre-procesamiento del CSV para normalizar el formato de las fechas, asegurando que el validador SHACL reconozca los tipos de datos como válidos. El formato de las horas esperaba HH:MM:SS y cuando un partido ocurría por la mañana (ej: 9:00) se escribía como T9:00:00Z, lo cual no es válido para xsd:dateTime. Se corrigió añadiendo un cero a la izquierda de la hora.
