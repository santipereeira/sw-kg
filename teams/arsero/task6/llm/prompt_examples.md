# Optional LLM-Assisted SPARQL Examples

The exploitation was implemented with manually reviewed SPARQL queries. Following the
course slides on LLMs for Knowledge Engineering, LLM-generated queries should be treated
as suggestions and validated by symbolic tools or human review because LLMs may make
mistakes in joins, datatypes and vocabulary details.

## Example 1

Natural-language question:

```text
Which districts have the highest number of municipal sports matches?
```

Reviewed SPARQL query:

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

## Example 2

Natural-language question:

```text
Which sports fields have a Wikidata link and what external information can be retrieved?
```

Reviewed approach:

1. Query the local KG for resources connected with `owl:sameAs`.
2. Query Wikidata using the linked Q identifiers.
3. Join the local names with Wikidata labels and coordinates in Python.
