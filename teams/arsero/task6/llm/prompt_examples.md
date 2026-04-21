# Ejemplos de SPARQL asistido por LLM

La explotación principal se implementó con consultas SPARQL revisadas manualmente. Como ampliación opcional, utilizamos un LLM como asistente para proponer consultas SPARQL a partir de preguntas en lenguaje natural.

Las propuestas generadas no se usaron directamente sin revisión. Antes de ejecutarlas, se contrastaron con la ontología, los mappings y el KG materializado, ya que los LLMs pueden cometer errores en los joins, los tipos de datos o los nombres exactos del vocabulario.

## Ejemplo 1

Pregunta en lenguaje natural:

```text
¿Qué distritos tienen el mayor número de partidos deportivos municipales?
```

Consulta SPARQL revisada:

```sparql
PREFIX ta: <http://example.org/def/juegosdeportivosmunicipalesmadrid#>

SELECT ?nombreDistrito (COUNT(?partido) AS ?totalPartidos)
WHERE {
  ?partido a ta:Partido ;
           ta:seJuegaEn ?campo .
  ?campo ta:estaEn ?distrito .
  ?distrito ta:nombreDistrito ?nombreDistrito .
}
GROUP BY ?nombreDistrito
ORDER BY DESC(?totalPartidos)
```

## Ejemplo 2

Pregunta en lenguaje natural:

```text
¿Qué campos deportivos tienen enlace a Wikidata y qué información externa se puede recuperar?
```

Enfoque revisado:

1. Consultar el KG local para obtener recursos conectados mediante `owl:sameAs`.
2. Consultar Wikidata usando los identificadores Q enlazados.
3. Unir en Python los nombres locales con las etiquetas y coordenadas obtenidas de Wikidata.

## Ejemplo 3

Pregunta en lenguaje natural:

```text
¿Qué partidos no tienen un campo deportivo conocido?
```

Consulta SPARQL revisada:

```sparql
PREFIX ta: <http://example.org/def/juegosdeportivosmunicipalesmadrid#>

SELECT ?partido ?fecha ?hora ?estado
WHERE {
  ?partido a ta:Partido ;
           ta:fecha ?fecha ;
           ta:hora ?hora ;
           ta:estado ?estado .
  FILTER NOT EXISTS { ?partido ta:seJuegaEn ?campo . }
}
ORDER BY ?fecha ?hora
LIMIT 20
```
