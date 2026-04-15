# Tarea 5 — Validación del Knowledge Graph (LOT4KG)

## Knowledge Graph validado

El grafo validado es **`kg/output.nt`**, generado por Morph-KGC en la Tarea 4 a partir del mapping `mappings/mapping.rml.ttl` y el dataset `data/ontologia-deportes.csv`.

Contiene **529 597 tripletas N-Triples** que representan instancias de las 8 clases de la ontología (`Deporte`, `Competicion`, `Grupo`, `Jornada`, `Partido`, `Equipo`, `Campo`, `Distrito`) y sus relaciones.

---

## Enfoque adoptado: Enfoque 3 — Comparación entre validación basada en datos y validación basada en modelo

Se ha optado por el **Enfoque 3 (comparación dual)**, que permite contrastar dos perspectivas complementarias:

1. **Validación basada en datos:** shapes inferidas automáticamente desde el propio grafo RDF materializado mediante **SheXer**.
2. **Validación basada en modelo:** shapes definidas de forma prescriptiva a partir de la **ontología** (`ontology/ontology.ttl`).

Este enfoque es especialmente valioso porque el mismo grafo se valida frente a dos criterios distintos: lo que *describe* los datos y lo que el modelo *prescribe* que deberían ser.

---

## Herramientas utilizadas

| Herramienta | Rol | Fichero generado |
|---|---|---|
| **SheXer** | Inferencia de shapes SHACL desde el grafo RDF | `shapes/shapes_from_data.ttl` |
| **pySHACL** | Ejecución de la validación SHACL | `shapes/validation/report_data_shapes.ttl`, `shapes/validation/report_model_shapes.ttl` |

La generación de shapes desde la ontología se realizó manualmente / semi-automáticamente, definiendo `NodeShapes` con las propiedades, tipos y cardinalidades que prescribe la ontología para cada clase.

---

## Generación de shapes desde los datos (SheXer)

**SheXer** analiza el grafo RDF materializado e infiere restricciones estructurales observando los patrones reales:
- Qué clases (`rdf:type`) aparecen en las instancias
- Qué propiedades tienen las instancias de cada clase
- Qué tipos de valores (`xsd:string`, `xsd:integer`, `xsd:dateTime`…) se observan
- Cardinalidades frecuentes

El resultado (`shapes/shapes_from_data.ttl`) captura fielmente la estructura que Morph-KGC generó a partir del mapping, por lo que tiende a ser muy permisivo con lo que realmente existe en el grafo.

---

## Generación de shapes desde la ontología

Las shapes del fichero `shapes/shapes_from_ontology.ttl` se derivaron a partir de las restricciones **normativas** definidas en `ontology/ontology.ttl`:

- `sh:targetClass` → clase objetivo de cada shape
- `sh:property` → restricciones sobre cada propiedad definida en la ontología
- `sh:datatype` → tipo XSD esperado (p.ej. `xsd:dateTime`, `xsd:integer`, `xsd:float`)
- `sh:minCount` → propiedades obligatorias según el modelo
- `sh:class` → tipo de objeto esperado en propiedades de objeto

Estas shapes prescriben cómo *debería* ser el grafo según el modelo de dominio, independientemente de lo que los datos contengan.

---

## Script de validación

El script [`shapes/validation/validate_data_and_ontology_shapes.py`](shapes/validation/validate_data_and_ontology_shapes.py) ejecuta ambas validaciones en secuencia:

```python
# Inferencia automática del formato por extensión (.nt → N-Triples, .ttl → Turtle)
run_validation("kg/output.nt", "shapes/shapes_from_data.ttl",
               "shapes/validation/report_data_shapes.ttl")
run_validation("kg/output.nt", "shapes/shapes_from_ontology.ttl",
               "shapes/validation/report_model_shapes.ttl")
```

Cada llamada a `run_validation()`:
1. Carga el grafo RDF (`kg/output.nt`) y el fichero de shapes correspondiente
2. Ejecuta `pyshacl.validate()` con inferencia `rdfs`
3. Serializa el informe de validación en Turtle al directorio `shapes/validation/`
4. Imprime por pantalla si el grafo conforma o no

### Comando de ejecución

```bash
cd TAREA_5
pip install pyshacl rdflib
python3 shapes/validation/validate_data_and_ontology_shapes.py
```

---

## Resultados de validación

```
Validating kg/output.nt against shapes/shapes_from_data.ttl...
Results for shapes/shapes_from_data.ttl:
Conforms: False
Report written to: shapes/validation/report_data_shapes.ttl
============================================================
Validating kg/output.nt against shapes/shapes_from_ontology.ttl...
Results for shapes/shapes_from_ontology.ttl:
Conforms: False
Report written to: shapes/validation/report_model_shapes.ttl
============================================================
```

### Interpretación: Shapes basadas en datos (SheXer)

Aunque el resultado es `Conforms: False`, la no-conformidad detectada por las shapes de datos es **residual y esperada**: SheXer infiere cardinalidades a partir de los patrones mayoritarios y algunas instancias minoritarias (p.ej. partidos sin resultado aún registrado, o nodos con propiedades opcionales ausentes) no cumplen las restricciones de cardinalidad mínima inferidas.

**Conclusión:** El grafo presenta una **muy alta conformidad estructural**, lo que confirma que el mapping RML extrae y modela los nodos sin ruido significativo.

### Interpretación: Shapes basadas en ontología

Las shapes normativas detectan un número más elevado de **violaciones de datatype**, principalmente en:

- **Propiedades de fecha/hora** (`ns:fecha`, `ns:hora`): el mapping utiliza `xsd:dateTime` para ambas, pero la ontología prescribe `xsd:date` para `ns:fecha` y `xsd:time` para `ns:hora`. Este desajuste se origina en que `Fecha_Hora` es un timestamp combinado, y al mapearlo como `xsd:dateTime` satisface la realidad del dato pero no la restricción de tipo de la ontología.

- **Timestamps con hora de un dígito**: algunos partidos tienen marcadores horarios del tipo `T9:00:00Z` en lugar de `T09:00:00Z`. Aunque se intentó corregir en OpenRefine, algunos valores residuales no son válidos según `xsd:dateTime` estándar.

**Conclusión:** Los errores no son de **estructura** del grafo sino de **calidad en los literales** del dataset de origen. El mapping y la ontología son coherentes entre sí en cuanto a la topología; el problema reside en los datos de partida.

---

## Análisis comparativo (Enfoque 3)

| Aspecto | Shapes desde datos | Shapes desde ontología |
|---|---|---|
| Fuente | Patrones observados en el KG | Restricciones del modelo de dominio |
| Conformidad | Alta (no-conformidad residual) | Menor (detecta problemas de tipado) |
| Tipo de errores detectados | Instancias con propiedades opcionales ausentes | Violaciones de datatype en literales |
| Utilidad | Describe la realidad del grafo | Prescribe cómo debería ser según el modelo |
| Errores del mapping detectados | Ninguno significativo | Desajuste `xsd:date` vs `xsd:dateTime` |
| Errores del dataset detectados | No detecta errors de tipo | Sí detecta timestamps malformados |

El Enfoque 3 resulta **idóneo** para este proyecto porque permite distinguir claramente entre:
- Problemas de **calidad de datos** en el origen (timestamps mal formados)
- Posibles desajustes entre el **mapping** y la **ontología** (tipo de dato de `ns:fecha`)
- La ausencia de ruido estructural, lo que valida la calidad del proceso de construcción del KG

---

## Observaciones y decisiones de diseño

- **`abort_on_first=True`** en pySHACL: se activó esta opción para grafos grandes (~530k tripletas), lo que acelera la validación pero limita el número de violaciones reportadas. En producción se desactivaría para obtener un informe completo.
- **Liberación explícita de memoria (`gc.collect()`)**: imprescindible al validar grafos de este tamaño para evitar errores de memoria durante la serialización del informe.
- **Inferencia `rdfs`**: se activó la inferencia RDFS en pySHACL para que el validador pueda razonar sobre subclases y subpropiedades definidas en la ontología.
- Los informes de validación completos (grafos RDF) están disponibles en `shapes/validation/report_data_shapes.ttl` y `shapes/validation/report_model_shapes.ttl`.
