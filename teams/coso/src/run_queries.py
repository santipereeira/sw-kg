from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

import folium
import matplotlib.pyplot as plt
import pandas as pd
from rdflib import Graph
from SPARQLWrapper import JSON, SPARQLWrapper


DEP = "http://example.org/def/dep#"
OWL = "http://www.w3.org/2002/07/owl#"

LOCAL_AFTER_2016_QUERY = f"""
PREFIX dep: <{DEP}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?ano (COUNT(DISTINCT ?equipo) AS ?numEquipos)
WHERE {{
  ?equipo a dep:Equipo ;
          dep:dataAlta ?fecha .
  BIND(YEAR(xsd:date(?fecha)) AS ?ano)
  FILTER(?ano > 2016)
}}
GROUP BY ?ano
ORDER BY ?ano
"""


def ensure_dirs(project_root: Path) -> None:
    (project_root / "results" / "query_results").mkdir(parents=True, exist_ok=True)
    (project_root / "results" / "figures").mkdir(parents=True, exist_ok=True)
    (project_root / "results" / "maps").mkdir(parents=True, exist_ok=True)


def load_graph(ttl_path: Path) -> Graph:
    graph = Graph()
    graph.parse(ttl_path)
    return graph


def run_local_query(graph: Graph, query_path: Path) -> pd.DataFrame:
    query = query_path.read_text(encoding="utf-8")
    result = graph.query(query)
    rows = []
    vars_ = [str(v) for v in result.vars]
    for row in result:
        rows.append({vars_[i]: (None if row[i] is None else str(row[i])) for i in range(len(vars_))})
    return pd.DataFrame(rows)


def run_inline_local_query(graph: Graph, query: str) -> pd.DataFrame:
    result = graph.query(query)
    rows = []
    vars_ = [str(v) for v in result.vars]
    for row in result:
        rows.append({vars_[i]: (None if row[i] is None else str(row[i])) for i in range(len(vars_))})
    return pd.DataFrame(rows)


def local_province_wikidata_counts(graph: Graph) -> pd.DataFrame:
    query = f"""
    PREFIX dep: <{DEP}>
    PREFIX owl: <{OWL}>

    SELECT ?provinciaNombre ?wikidata (COUNT(DISTINCT ?equipo) AS ?numEquipos)
    WHERE {{
      ?equipo a dep:Equipo .
      {{
        ?equipo dep:estaEnProvincia ?provincia .
      }}
      UNION
      {{
        ?equipo dep:estaEnMunicipio ?municipio .
        ?municipio dep:estaEnProvincia ?provincia .
      }}

      ?provincia owl:sameAs ?wikidata .
      OPTIONAL {{ ?provincia dep:nome ?provinciaNombre . }}
      BIND(COALESCE(?provinciaNombre, STR(?provincia)) AS ?provinciaNombre)
    }}
    GROUP BY ?provinciaNombre ?wikidata
    ORDER BY DESC(?numEquipos)
    """
    return run_inline_local_query(graph, query)


def local_province_wikidata_uris(graph: Graph) -> pd.DataFrame:
    query = f"""
    PREFIX dep: <{DEP}>
    PREFIX owl: <{OWL}>

    SELECT DISTINCT ?provinciaNombre ?wikidata
    WHERE {{
      ?provincia a dep:Provincia ;
                 owl:sameAs ?wikidata .
      OPTIONAL {{ ?provincia dep:nome ?provinciaNombre . }}
      BIND(COALESCE(?provinciaNombre, STR(?provincia)) AS ?provinciaNombre)
    }}
    ORDER BY ?provinciaNombre
    """
    return run_inline_local_query(graph, query)


def extract_qid(uri: str) -> str:
    path = urlparse(uri).path.rstrip("/")
    return path.split("/")[-1]


def query_wikidata(qids: list[str], want_media: bool = False) -> pd.DataFrame:
    if not qids:
        return pd.DataFrame()

    values = " ".join(f"wd:{qid}" for qid in qids)

    extra = """
      OPTIONAL { ?item wdt:P18 ?imagen . }
      OPTIONAL { ?item wdt:P856 ?web . }
    """ if want_media else ""

    query = f"""
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wikibase: <http://wikiba.se/ontology#>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
    PREFIX ps: <http://www.wikidata.org/prop/statement/>

    SELECT ?item ?itemLabel ?lat ?lon ?poblacion ?imagen ?web
    WHERE {{
      VALUES ?item {{ {values} }}
      OPTIONAL {{
        ?item p:P625 [
          psv:P625 [
            wikibase:geoLatitude ?lat ;
            wikibase:geoLongitude ?lon
          ] ;
          ps:P625 ?coord
        ] .
      }}
      OPTIONAL {{ ?item wdt:P1082 ?poblacion . }}
      {extra}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en". }}
    }}
    """

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.addCustomHttpHeader("User-Agent", "ChatGPT-SPARQL-Project/1.0")

    result = sparql.query().convert()

    rows = []
    for b in result["results"]["bindings"]:
        rows.append({
            "wikidata": b.get("item", {}).get("value"),
            "itemLabel": b.get("itemLabel", {}).get("value"),
            "lat": b.get("lat", {}).get("value"),
            "lon": b.get("lon", {}).get("value"),
            "poblacion": b.get("poblacion", {}).get("value"),
            "imagen": b.get("imagen", {}).get("value"),
            "web": b.get("web", {}).get("value"),
        })

    return pd.DataFrame(rows)


def make_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, out_path: Path, top_n: int = 20) -> None:
    data = df.copy()
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.sort_values(y_col, ascending=False).head(top_n)

    plt.figure(figsize=(10, 6))
    plt.bar(data[x_col], data[y_col])
    plt.xticks(rotation=45, ha="right")
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close()


def make_map(df: pd.DataFrame, out_path: Path) -> None:
    map_df = df.copy()
    map_df["lat"] = pd.to_numeric(map_df["lat"], errors="coerce")
    map_df["lon"] = pd.to_numeric(map_df["lon"], errors="coerce")
    map_df["numEquipos"] = pd.to_numeric(map_df["numEquipos"], errors="coerce")
    map_df = map_df.dropna(subset=["lat", "lon"])

    if map_df.empty:
        return

    center_lat = map_df["lat"].mean()
    center_lon = map_df["lon"].mean()
    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=7)

    for _, row in map_df.iterrows():
        popup = (
            f"<b>{row.get('provinciaNombre', 'Provincia')}</b><br>"
            f"Equipos: {int(row.get('numEquipos', 0)) if pd.notna(row.get('numEquipos')) else 'N/D'}<br>"
            f"Población: {row.get('poblacion', 'N/D')}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(6, min(18, float(row.get("numEquipos", 1)) / 5 + 5)),
            popup=popup,
            fill=True,
        ).add_to(fmap)

    fmap.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta consultas SPARQL locales y enriquecimiento con Wikidata.")
    parser.add_argument("--ttl", required=True, help="Ruta al archivo TTL local.")
    args = parser.parse_args()

    ttl_path = Path(args.ttl).resolve()
    project_root = Path(__file__).resolve().parent.parent
    ensure_dirs(project_root)

    graph = load_graph(ttl_path)
    queries_dir = project_root / "queries"
    results_dir = project_root / "results" / "query_results"
    figures_dir = project_root / "results" / "figures"
    maps_dir = project_root / "results" / "maps"

    df_local_1 = run_local_query(graph, queries_dir / "local_query_1.rq")
    df_local_2 = run_local_query(graph, queries_dir / "local_query_2.rq")
    df_after_2016 = run_inline_local_query(graph, LOCAL_AFTER_2016_QUERY)

    df_local_1.to_csv(results_dir / "local_query_1.csv", index=False)
    df_local_2.to_csv(results_dir / "local_query_2.csv", index=False)
    df_after_2016.to_csv(results_dir / "after_2016_by_year.csv", index=False)

    if not df_local_1.empty:
        make_bar_chart(df_local_1, "provinciaNombre", "numEquipos", "Equipos por provincia", figures_dir / "equipos_por_provincia.png")
    if not df_local_2.empty:
        make_bar_chart(df_local_2, "deporteNombre", "numEquipos", "Equipos por deporte", figures_dir / "equipos_por_deporte.png")
    if not df_after_2016.empty:
        make_bar_chart(df_after_2016, "ano", "numEquipos", "Equipos dados de alta después de 2016", figures_dir / "equipos_despues_2016.png")

    df_local_wd_counts = local_province_wikidata_counts(graph)
    if not df_local_wd_counts.empty:
        qids = [extract_qid(u) for u in df_local_wd_counts["wikidata"].dropna().tolist()]
        df_wikidata_geo = query_wikidata(qids, want_media=False)
        df_fed_1 = df_local_wd_counts.merge(df_wikidata_geo, on="wikidata", how="left")
        df_fed_1.to_csv(results_dir / "federated_query_1.csv", index=False)
        make_map(df_fed_1, maps_dir / "map_provincias.html")
    else:
        df_fed_1 = pd.DataFrame()

    df_local_wd_uris = local_province_wikidata_uris(graph)
    if not df_local_wd_uris.empty:
        qids = [extract_qid(u) for u in df_local_wd_uris["wikidata"].dropna().tolist()]
        df_wikidata_media = query_wikidata(qids, want_media=True)
        df_fed_2 = df_local_wd_uris.merge(df_wikidata_media, on="wikidata", how="left")
        df_fed_2.to_csv(results_dir / "federated_query_2.csv", index=False)
    else:
        df_fed_2 = pd.DataFrame()

    print("\nResultados generados en:")
    print(results_dir)
    print(figures_dir)
    print(maps_dir)
    print("\nResumen:")
    print(f"- Local 1: {len(df_local_1)} filas")
    print(f"- Local 2: {len(df_local_2)} filas")
    print(f"- After 2016: {len(df_after_2016)} filas")
    print(f"- Federated 1: {len(df_fed_1)} filas")
    print(f"- Federated 2: {len(df_fed_2)} filas")


if __name__ == "__main__":
    main()
