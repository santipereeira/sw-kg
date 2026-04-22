# Explotación del Knowledge Graph

## Descripción

Esta tarea explota el Knowledge Graph de los Juegos Deportivos Municipales de Madrid generado en la Tarea 4. El objetivo es demostrar que el grafo puede consultarse con SPARQL, enriquecerse con Wikidata y producir resultados útiles para análisis y visualización.

Grafo base:

```bash
../task4/kg/output.nt
```

El grafo contiene 298.653 triples RDF. Para esta tarea se carga también un pequeño grafo de enlaces a Wikidata:

```bash
data/wikidata_links.ttl
```

Estos enlaces proceden del historial de reconciliación de OpenRefine y conectan recursos locales de distritos y campos deportivos con entidades Wikidata mediante `owl:sameAs`.

---

## Estructura

```bash
task6/
  data/
    wikidata_links.ttl
  queries/
    local_01_count_matches_by_district.rq
    local_02_top_fields_by_matches.rq
    local_03_matches_by_status_and_district.rq
    local_04_fields_with_coordinates.rq
    local_05_wikidata_links.rq
    federated_01_district_wikidata_info.rq
    federated_02_field_wikidata_info.rq
  src/
    run_queries.py
  results/
    query_results/
    maps/
  llm/
    prompt_examples.md
    generated_queries.rq
    evaluate_llm_queries.py
    llm_evaluation.md
```

---

## Consultas SPARQL locales

Las consultas locales se ejecutan con RDFLib sobre el KG local y el grafo de enlaces:

* `local_01_count_matches_by_district.rq`: cuenta partidos por distrito.
* `local_02_top_fields_by_matches.rq`: obtiene los campos con más partidos.
* `local_03_matches_by_status_and_district.rq`: resume partidos por estado y distrito.
* `local_04_fields_with_coordinates.rq`: extrae campos con coordenadas válidas.
* `local_05_wikidata_links.rq`: lista los recursos locales conectados con Wikidata.

Estas consultas usan patrones SPARQL vistos en clase: `SELECT`, `WHERE`, `FILTER`,`COUNT`, `GROUP BY`, `ORDER BY` y `LIMIT`.

---

## Consultas a Wikidata

La explotación incluye consultas a Wikidata a partir de enlaces presentes en el grafo cargado en esta tarea. Los enlaces se representan con `owl:sameAs`, por ejemplo:

```turtle
<http://example.org/resource/Distrito/Latina>
    owl:sameAs <http://www.wikidata.org/entity/Q794954> .
```

Se entregan dos consultas federadas:

* `federated_01_district_wikidata_info.rq`: recupera etiqueta, población, área y coordenadas de los distritos enlazados.
* `federated_02_field_wikidata_info.rq`: recupera etiqueta, coordenadas y dirección cuando están disponibles para campos deportivos enlazados.

En el script se ejecuta la federación en dos pasos: primero se consultan los enlaces en el KG local y después se consulta Wikidata con `SPARQLWrapper`. Esto evita depender de que RDFLib ejecute `SERVICE` remoto, pero mantiene la misma lógica de explotación federada.

---

## Ejecución

Desde la carpeta de la tarea:

```bash
cd teams/arsero/task6
python src/run_queries.py
```

El script:

1. carga `../task4/kg/output.nt`;
2. carga `data/wikidata_links.ttl`;
3. ejecuta las consultas SPARQL locales;
4. consulta Wikidata usando los QIDs enlazados;
5. guarda resultados en CSV;
6. genera una visualización HTML sencilla de campos con coordenadas.

Dependencias principales:

```bash
rdflib
SPARQLWrapper
```

El mapa se genera con HTML y JavaScript básico, sin depender de librerías externas.

---

## Resultados Generados

Resultados tabulares:

```bash
results/query_results/local_01_count_matches_by_district.csv
results/query_results/local_02_top_fields_by_matches.csv
results/query_results/local_03_matches_by_status_and_district.csv
results/query_results/local_04_fields_with_coordinates.csv
results/query_results/local_05_wikidata_links.csv
results/query_results/federated_01_district_wikidata_info.csv
results/query_results/federated_02_field_wikidata_info.csv
```

Visualización:

```bash
results/maps/fields_map.html
```

Ejemplos de resultados:

* El ranking de partidos por distrito sitúa a Salamanca, Latina y Chamartín entre los distritos con mayor número de partidos registrados.
* La consulta de campos con coordenadas produce 314 registros, utilizados para construir el mapa HTML.
* La consulta federada de distritos enriquece el KG con etiquetas, población, área y coordenadas procedentes de Wikidata.
* La consulta federada de campos añade etiquetas externas y, cuando Wikidata lo ofrece, direcciones o coordenadas.

---

## Valor de usar SPARQL

El uso de SPARQL permite responder preguntas analíticas sobre el KG local:

* qué distritos concentran más partidos;
* qué campos deportivos tienen mayor uso;
* cómo se distribuyen los estados de los partidos por distrito;
* qué campos tienen coordenadas reutilizables para visualización.

La integración con Wikidata aporta contexto externo que no estaba materializado en el KG local, como población, área, etiquetas normalizadas, coordenadas externas y direcciones.
Así, el KG local sirve como punto de partida y Wikidata actúa como fuente de enriquecimiento.

---

## Uso opcional de LLMs

La carpeta `llm/` incluye una ampliación opcional basada en LLMs para generar borradores de consultas SPARQL desde preguntas en lenguaje natural.

El proceso seguido fue:

1. plantear preguntas sobre el KG en lenguaje natural;
2. usar un LLM como asistente para proponer consultas SPARQL;
3. revisar manualmente las consultas según la ontología, los mappings y el KG generado;
4. ejecutar las consultas revisadas con RDFLib;
5. guardar los resultados en CSV.

Archivos de la ampliación:

```bash
llm/prompt_examples.md
llm/generated_queries.rq
llm/evaluate_llm_queries.py
llm/llm_evaluation.md
```

Para ejecutar las consultas revisadas:

```bash
cd teams/arsero/task6
python llm/evaluate_llm_queries.py
```

Esta ampliación muestra que el LLM es útil para generar borradores, pero que las consultas deben validarse manualmente porque puede inventar nombres de propiedades, omitir joins o producir agregaciones engañosas.

---

## Limitaciones

* No todos los distritos y campos tienen enlace a Wikidata; solo se enlazaron recursos con reconciliación disponible y razonablemente fiable.
* Algunos nombres locales están normalizados sin tildes por la limpieza previa (`Chamartan`, `Chambera`, `Tetuan`).
* Algunos partidos tienen campo desconocido en origen (`codigoCampo=0`) y no generan relación `ta:seJuegaEn`.
* Wikidata no siempre contiene todas las propiedades externas para cada campo deportivo.

---

## Conclusión

La tarea usa SPARQL, consulta el KG local, explota enlaces a
Wikidata y genera una pequeña explotación reproducible con resultados tabulares y una visualización HTML. Esto muestra que el Knowledge Graph puede funcionar como base para análisis local y enriquecimiento externo.
