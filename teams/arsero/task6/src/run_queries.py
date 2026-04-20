from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from rdflib import Graph, Namespace, URIRef
from SPARQLWrapper import JSON, SPARQLWrapper


TASK6_DIR = Path(__file__).resolve().parents[1]
TEAM_DIR = TASK6_DIR.parent
KG_PATH = TEAM_DIR / "task4" / "kg" / "output.nt"
LINKS_PATH = TASK6_DIR / "data" / "wikidata_links.ttl"
QUERIES_DIR = TASK6_DIR / "queries"
RESULTS_DIR = TASK6_DIR / "results" / "query_results"
MAPS_DIR = TASK6_DIR / "results" / "maps"

TA = Namespace("http://example.org/def/juegosdeportivosmunicipalesmadrid#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
WD = "http://www.wikidata.org/entity/"


LOCAL_QUERIES = [
    "local_01_count_matches_by_district.rq",
    "local_02_top_fields_by_matches.rq",
    "local_03_matches_by_status_and_district.rq",
    "local_04_fields_with_coordinates.rq",
    "local_05_wikidata_links.rq",
]


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)


def load_graph() -> Graph:
    graph = Graph()
    graph.parse(KG_PATH, format="nt")
    graph.parse(LINKS_PATH, format="turtle")
    return graph


def term_to_text(value) -> str:
    if value is None:
        return ""
    return str(value)


def write_rows(path: Path, vars_: Iterable[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(vars_), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_local_query(graph: Graph, query_name: str) -> Path:
    query_path = QUERIES_DIR / query_name
    query = query_path.read_text(encoding="utf-8")
    result = graph.query(query)
    vars_ = [str(var) for var in result.vars]
    rows = [
        {var: term_to_text(row.get(var)) for var in vars_}
        for row in result
    ]
    out_path = RESULTS_DIR / query_name.replace(".rq", ".csv")
    write_rows(out_path, vars_, rows)
    return out_path


def qid_from_uri(uri: URIRef) -> str:
    text = str(uri)
    if not text.startswith(WD):
        return ""
    return text.removeprefix(WD)


def linked_resources(graph: Graph, rdf_type: URIRef) -> list[tuple[str, str, str]]:
    name_property = TA.nombreDistrito if rdf_type == TA.DistritoMunicipal else TA.nombreCampo
    query = f"""
    PREFIX ta: <{TA}>
    PREFIX owl: <{OWL}>

    SELECT ?resource ?name ?wikidata
    WHERE {{
      ?resource a <{rdf_type}> ;
                <{name_property}> ?name ;
                owl:sameAs ?wikidata .
    }}
    ORDER BY ?name
    """
    rows = []
    for row in graph.query(query):
        rows.append((str(row.resource), str(row.name), qid_from_uri(row.wikidata)))
    return rows


def wikidata_query(qids: list[str], entity_kind: str) -> str:
    values = " ".join(f"wd:{qid}" for qid in sorted(set(qids)) if qid)
    if entity_kind == "district":
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX bd: <http://www.bigdata.com/rdf#>

        SELECT ?item ?itemLabel ?population ?area ?coords
        WHERE {{
          VALUES ?item {{ {values} }}
          OPTIONAL {{ ?item wdt:P1082 ?population . }}
          OPTIONAL {{ ?item wdt:P2046 ?area . }}
          OPTIONAL {{ ?item wdt:P625 ?coords . }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en" . }}
        }}
        """
    return f"""
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wikibase: <http://wikiba.se/ontology#>
    PREFIX bd: <http://www.bigdata.com/rdf#>

    SELECT ?item ?itemLabel ?coords ?streetAddress
    WHERE {{
      VALUES ?item {{ {values} }}
      OPTIONAL {{ ?item wdt:P625 ?coords . }}
      OPTIONAL {{ ?item wdt:P6375 ?streetAddress . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en" . }}
    }}
    """


def run_wikidata(query: str) -> dict[str, dict[str, str]]:
    endpoint = SPARQLWrapper("https://query.wikidata.org/sparql")
    endpoint.addCustomHttpHeader(
        "User-Agent",
        "WebSemantica-Arsero-Task6/1.0 (academic project)",
    )
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    response = endpoint.query().convert()
    results: dict[str, dict[str, str]] = {}
    for binding in response["results"]["bindings"]:
        item = binding["item"]["value"]
        qid = item.removeprefix(WD)
        results[qid] = {
            key: value["value"]
            for key, value in binding.items()
            if key != "item"
        }
    return results


def enrich_with_wikidata(graph: Graph, rdf_type: URIRef, entity_kind: str, out_name: str) -> Path:
    local_links = linked_resources(graph, rdf_type)
    qids = [qid for _, _, qid in local_links]
    external = run_wikidata(wikidata_query(qids, entity_kind))

    columns = ["localResource", "localName", "wikidata", "wikidataLabel"]
    if entity_kind == "district":
        columns.extend(["population", "area", "coords"])
    else:
        columns.extend(["coords", "streetAddress"])

    rows = []
    for resource, name, qid in local_links:
        ext = external.get(qid, {})
        rows.append({
            "localResource": resource,
            "localName": name,
            "wikidata": f"{WD}{qid}",
            "wikidataLabel": ext.get("itemLabel", ""),
            "population": ext.get("population", ""),
            "area": ext.get("area", ""),
            "coords": ext.get("coords", ""),
            "streetAddress": ext.get("streetAddress", ""),
        })

    out_path = RESULTS_DIR / out_name
    write_rows(out_path, columns, rows)
    return out_path


def parse_decimal(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed != 0 else None


def make_fields_map() -> Path:
    csv_path = RESULTS_DIR / "local_04_fields_with_coordinates.csv"
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lon = parse_decimal(row["coordX"])
            lat = parse_decimal(row["coordY"])
            if lat is None or lon is None:
                continue
            rows.append({
                "name": row["nombreCampo"],
                "district": row["nombreDistrito"],
                "lat": lat,
                "lon": lon,
            })

    points = json.dumps(rows, ensure_ascii=False)
    map_path = MAPS_DIR / "fields_map.html"
    html_content = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Campos deportivos municipales</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    svg {{ border: 1px solid #ccc; max-width: 100%; height: auto; }}
    circle {{ fill: #1565c0; opacity: .72; }}
    circle:hover {{ fill: #c62828; opacity: 1; }}
    .tooltip {{ margin-top: 12px; min-height: 40px; }}
  </style>
</head>
<body>
  <h1>Campos deportivos municipales con coordenadas</h1>
  <p>Visualización simple generada desde el Knowledge Graph local.</p>
  <svg id="map" width="900" height="620" role="img" aria-label="Mapa esquemático de campos deportivos"></svg>
  <div class="tooltip" id="tooltip">Pasa el cursor por un punto para ver el campo y distrito.</div>
  <script>
    const points = {points};
    const svg = document.getElementById("map");
    const tooltip = document.getElementById("tooltip");
    const width = 900, height = 620, padding = 40;
    const lons = points.map(p => p.lon);
    const lats = points.map(p => p.lat);
    const minLon = Math.min(...lons), maxLon = Math.max(...lons);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats);
    function x(lon) {{ return padding + (lon - minLon) / (maxLon - minLon) * (width - 2 * padding); }}
    function y(lat) {{ return height - padding - (lat - minLat) / (maxLat - minLat) * (height - 2 * padding); }}
    for (const p of points) {{
      const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      c.setAttribute("cx", x(p.lon));
      c.setAttribute("cy", y(p.lat));
      c.setAttribute("r", 5);
      c.addEventListener("mouseenter", () => {{
        tooltip.innerHTML = `<strong>${{p.name}}</strong><br>${{p.district}}`;
      }});
      svg.appendChild(c);
    }}
  </script>
</body>
</html>
"""
    map_path.write_text(html_content, encoding="utf-8")
    return map_path


def main() -> None:
    ensure_dirs()
    graph = load_graph()
    print(f"Loaded graph with {len(graph)} triples")

    for query_name in LOCAL_QUERIES:
        out = run_local_query(graph, query_name)
        print(f"Local query written: {out.relative_to(TASK6_DIR)}")

    district_out = enrich_with_wikidata(
        graph,
        TA.DistritoMunicipal,
        "district",
        "federated_01_district_wikidata_info.csv",
    )
    print(f"Wikidata district enrichment written: {district_out.relative_to(TASK6_DIR)}")

    field_out = enrich_with_wikidata(
        graph,
        TA.Campo,
        "field",
        "federated_02_field_wikidata_info.csv",
    )
    print(f"Wikidata field enrichment written: {field_out.relative_to(TASK6_DIR)}")

    map_path = make_fields_map()
    print(f"Map written: {map_path.relative_to(TASK6_DIR)}")


if __name__ == "__main__":
    main()
