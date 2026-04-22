# Evaluación De Consultas Asistidas Por LLM

## Objetivo

Esta ampliación opcional prueba cómo un LLM puede ayudar en la creación de consultas SPARQL a partir de preguntas en lenguaje natural. El objetivo no es confiar directamente en la consulta generada, sino usarla como primer borrador y validarla después contra la ontología, los mappings y el KG materializado.

## Método

1. Se escribieron preguntas en lenguaje natural sobre el dominio.
2. Se utilizó un LLM como asistente para proponer consultas SPARQL.
3. Las consultas propuestas se revisaron manualmente.
4. Se aplicaron correcciones para ajustarlas al vocabulario real del proyecto.
5. Las consultas revisadas se ejecutaron con RDFLib sobre el KG local y el grafo de enlaces a Wikidata.

Las consultas revisadas se almacenan en:

```bash
llm/generated_queries.rq
```

Se pueden ejecutar con:

```bash
cd teams/arsero/task6
python llm/evaluate_llm_queries.py
```

## Criterios de revisión

Las consultas generadas se revisaron comprobando:

* uso correcto de namespaces;
* nombres correctos de clases y propiedades según la ontología;
* joins correctos entre `Partido`, `Campo` y `DistritoMunicipal`;
* uso de `COUNT(DISTINCT ?partido)` para evitar agregaciones infladas;
* tratamiento explícito de partidos sin `ta:seJuegaEn`;
* uso de `owl:sameAs` para recursos enlazados con Wikidata.

## Correcciones aplicadas

La corrección más relevante fue evitar nombres de propiedades genéricos o inventados. Por ejemplo, un LLM puede proponer propiedades como `ta:district`, `ta:field` o `ta:playedAt`, pero la ontología real usa:

```sparql
ta:seJuegaEn
ta:estaEn
ta:nombreDistrito
ta:nombreCampo
```

Otra corrección importante fue usar `COUNT(DISTINCT ?partido)`. Sin `DISTINCT`, algunas agregaciones pueden inflarse cuando un recurso tiene varios valores relacionados.

## Resultados

Las consultas asistidas por LLM y revisadas manualmente generaron ficheros CSV en:

```bash
results/query_results/
```

La ampliación produjo:

* un ranking de distritos por número de partidos;
* una lista de partidos sin campo deportivo conocido;
* una lista de campos deportivos enlazados con Wikidata;
* un ranking de campos deportivos según su uso.

## Interpretación

El LLM resultó útil para proponer rápidamente estructuras de consulta a partir de preguntas en lenguaje natural. Sin embargo, las propuestas generadas necesitaron validación manual, porque pequeños errores de vocabulario o joins incompletos pueden hacer que las consultas fallen o produzcan resultados engañosos. Esto confirma que los LLMs son útiles como asistentes, pero que la explotación final debe comprobarse mediante
ejecución sobre el KG.
