# Trabajo Final: Construcción de un Knowledge Graph — Grupo *pela*

> **Integrantes:** Santiago Pereira Olmeda · Gonzalo Landeira Rodríguez · Mateo Fraguas Abal  
> **Dataset:** Competiciones deportivas municipales de deportes colectivos — Temporada 2014/2015  
> **Fuente:** [datos.gob.es](https://datos.gob.es/es/catalogo/l01280796-deportes-competiciones-deportivas-municipales-de-deportes-colectivos-temporadas-anteriores)

---

## Descripción del dataset

El dataset utilizado recoge los **partidos de competición local del Ayuntamiento de Madrid** correspondientes a la temporada 2014–2015. Incluye información sobre:

- Deporte y sistema de competición (liga, liguilla, copa…)
- Grupos, categorías, fases y jornadas
- Equipos locales y visitantes, con sus códigos numéricos
- Resultados (goles/puntos de cada equipo)
- Estado del partido (finalizado, aplazado, suspendido, no jugado…)
- Campo de juego con coordenadas geográficas y distrito

El archivo original contiene **43 596 filas** y más de 20 columnas con datos parcialmente sucios (fechas en distintos formatos, códigos concatenados, campos de hora separados, valores de estado inconsistentes, etc.).

---

## Resumen de tareas (metodología LOT4KG)

| Tarea | Descripción | Herramienta principal |
|-------|-----------|-----------------------|
| [TAREA 1](TAREA_1/1-groups.md) | Registro del grupo y selección del dataset | GitHub |
| [TAREA 2](TAREA_2/README.md) | Limpieza y preparación de datos | OpenRefine |
| [TAREA 3](TAREA_3/README.md) | Modelado y publicación de la ontología | Chowlk + OnToology |
| [TAREA 4](TAREA_4/README.md) | Construcción del Knowledge Graph | YARRRML + Yatter + Morph-KGC |
| [TAREA 5](TAREA_5/README.md) | Validación del Knowledge Graph | SheXer + pySHACL |

---

## Cómo se ha modelado la transformación

1. **Limpieza (TAREA 2):** OpenRefine transforma el CSV original eliminando columnas irrelevantes, normalizando fechas y horas, tipando los campos numéricos, unificando los valores de estado y realizando reconciliación de entidades (deportes y distritos) contra Wikidata. El resultado es `TAREA_2/data/ontologia-deportes.csv` (también copiado en `TAREA_4/data/`) con ~43 596 filas depuradas.

2. **Ontología (TAREA 3):** Se diseña con Chowlk una ontología con 8 clases (`Deporte`, `Competicion`, `Grupo`, `Jornada`, `Partido`, `Equipo`, `Campo`, `Distrito`) y sus propiedades de objeto y de datos. Se exporta a `TAREA_3/ontology/ontology.ttl` y se publica con OnToology (documentación HTML, diagramas, informe OOPS!).

3. **Mapping y KGC (TAREA 4):** Los mappings se definen en YARRRML (`TAREA_4/mappings/mapping.yarrrml.yaml`), se traducen a RML con Yatter y se llevan a cabo con Morph-KGC, produciendo el grafo RDF `TAREA_4/kg/output.nt` (~529 597 tripletas).

4. **Validación (TAREA 5):** Se generan shapes SHACL desde los datos (SheXer → `TAREA_5/shapes/shapes_from_data.ttl`) y desde la ontología (`TAREA_5/shapes/shapes_from_ontology.ttl`). Se valida con pySHACL: la validación basada en datos muestra alta estabilidad estructural; la basada en ontología detecta problemas de tipado literal (timestamps mal formados en el dataset de origen).

---

## Comandos principales

```bash
# Instalación de dependencias
pip install yatter morph-kgc pyshacl shexer rdflib

# Traducción de YARRRML a RML
python3 TAREA_4/mappings/yarrml_a_rml.py

# Generación del Knowledge Graph
python3 -m morph_kgc TAREA_4/mappings/config.ini

# Validación SHACL
python3 TAREA_5/shapes/validation/validate_data_and_ontology_shapes.py
```

---

## Observaciones y decisiones de diseño relevantes

- Se priorizó el uso de **identificadores numéricos del CSV** (`Codigo_grupo`, `Jornada`, `Partido`, etc.) para construir URIs estables y sin colisiones.
- La columna `Fecha_Hora` se construyó en OpenRefine combinando `Fecha` y `Hora` en un timestamp ISO 8601 (`YYYY-MM-DDTHH:MM:00Z`), necesario para el tipado `xsd:dateTime` en el mapping.
- La directiva `~iri` en YARRRML se utilizó sistemáticamente en los joins para evitar codificación incorrecta de barras, espacios u otros caracteres especiales en las URIs.
- Los deportes y distritos fueron **reconciliados contra Wikidata** en OpenRefine, añadiendo columnas `Deporte_ID` y `Distrito_ID` que luego se mapean como `owl:sameAs` en el grafo.
- Se detectó que algunos timestamps del CSV original presentaban hora de un solo dígito (`T9:00:00Z` en lugar de `T09:00:00Z`), causando violaciones en la validación basada en ontología. Esto constituye un problema de calidad de datos en el origen.
