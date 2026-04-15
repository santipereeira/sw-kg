## Validación del Knowledge Graph (Tarea 5)
Se ha optado por implementar el **Enfoque 3 (Comparación entre ambos)**:
1. **Validación basada en datos**: Extracción automática del patrón existente en el grafo generado usando `shexer`.
2. **Validación basada en modelo**: Definición prescriptiva de `NodeShapes` y propiedades según la Ontología provista.

### Herramientas utilizadas
- `shexer`: para inferir la topología real del Knowledge Graph a partir de las `529.597` sentencias N-Triples materializadas en `kg/output.ttl`. Fichero: `shapes/shapes_from_data.ttl`
- `pyshacl`: Ejecutor SHACL por defecto utilizado para cotejar el Output frente a las Shapes inferidas y frente a las Shapes normativas. Fichero de automatización: `shapes/validation/validate.py`

### Análisis y Resoluciones
La validación arroja los siguientes contrastes:
- **Shapes basadas en Datos (Shexer)**: Alcanza una altísima conformidad, demostrando consistencia en los tipos que emitió Morph-KGC en base a los URIs semánticos. 
- **Shapes basadas en Ontología**: Al someter el dataset al validador contra normativas restrictivas, salta una importante ráfaga de inconsistencias en los datatypes literales, específicamente en los campos de fecha originarios de `ontologia-deportes.csv`: muchos timestamps de los partidos usan marcadores horarios comprimidos (ej: `T9:00:00Z` en vez de `T09:00:00Z`). Dichas restricciones fallan contra los validadores xsd estándar de RDFS generados. 

El Enfoque 3 resulta idóneo porque nos corrobora que, estructuralmente, el mapeo RML extrae y modela los nodos sin ruido, pero advierte que el *dataset de entrada* contiene problemas de conformidad de literales que sólo podemos evidenciar contrastando con una ontología fuertemente tipada.

## Comandos de ejecución
Para generar el RML con Yatter y generar el RDF:
```bash
pip install yatter morph-kgc
yatter -i mappings/mapping.yarrrml.yaml -o mappings/mapping.rml.ttl
python3 -m morph_kgc mappings/config.ini
```

Adicionalmente, si la salida que genera Morph-KGC incluye cabeceras `nt` puede ser renombrada a formato `ttl`:
```bash
mv kg/output.nt kg/output.ttl
```

## Observaciones
El archivo `mappings/mapping.yarrrml.yaml` construye URI consistentes (`ns:competicion/LIGA_2014/2015_futsal`, etc.). Hemos evitado usar URI conflictivas mediante la directiva `~iri` en todos los joins para que las slashes (`/`), espacios u otros caracteres se codifiquen adecuadamente.
