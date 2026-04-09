from __future__ import annotations

import re
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
from rdflib import Graph
from SPARQLWrapper import JSON, POST, SPARQLWrapper


ROOT = Path(__file__).resolve().parents[1]
KG_PATH = ROOT / "kg" / "output.ttl"
QUERIES_DIR = ROOT / "queries"
RESULTS_DIR = ROOT / "results" / "query_results"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WKT_POINT_RE = re.compile(r"Point\(([-0-9.]+)\s+([-0-9.]+)\)")

LOCAL_QUERY_OUTPUTS = {
    "local_query_1.rq": "local_query_1.csv",
    "local_query_2.rq": "local_query_2.csv",
    "local_query_3.rq": "local_query_3.csv",
}

REMOTE_QUERY_OUTPUTS = {
    "federated_query_1.rq": "federated_query_1.csv",
    "federated_query_2.rq": "federated_query_2.csv",
}


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_query(query_name: str) -> str:
    return (QUERIES_DIR / query_name).read_text(encoding="utf-8")


def convert_rdflib_value(value):
    if value is None:
        return None

    python_value = value.toPython() if hasattr(value, "toPython") else value

    if isinstance(python_value, Decimal):
        return float(python_value)
    if isinstance(python_value, (datetime, date)):
        return python_value.isoformat()
    if isinstance(python_value, (int, float, bool)):
        return python_value
    return str(python_value)


def run_local_query(graph: Graph, query_name: str) -> pd.DataFrame:
    result = graph.query(read_query(query_name))
    columns = [str(var) for var in result.vars]
    rows = []

    for row in result:
        record = {}
        for column in columns:
            record[column] = convert_rdflib_value(row[column])
        rows.append(record)

    dataframe = pd.DataFrame(rows, columns=columns)
    output_name = LOCAL_QUERY_OUTPUTS[query_name]
    dataframe.to_csv(RESULTS_DIR / output_name, index=False)
    print(f"Saved {output_name} with {len(dataframe)} rows.")
    return dataframe


def convert_sparql_binding(binding):
    if binding is None:
        return None

    value = binding["value"]
    datatype = binding.get("datatype", "")

    if datatype.endswith("#integer") or datatype.endswith("#int"):
        return int(value)
    if datatype.endswith("#decimal") or datatype.endswith("#double") or datatype.endswith("#float"):
        return float(value)
    return value


def run_wikidata_query(query_name: str, iris: list[str]) -> pd.DataFrame:
    if not iris:
        dataframe = pd.DataFrame()
        output_name = REMOTE_QUERY_OUTPUTS[query_name]
        dataframe.to_csv(RESULTS_DIR / output_name, index=False)
        print(f"Saved {output_name} with 0 rows.")
        return dataframe

    query_text = read_query(query_name).replace(
        "__VALUES__", " ".join(f"<{iri}>" for iri in sorted(set(iris)))
    )

    client = SPARQLWrapper(
        WIKIDATA_ENDPOINT,
        agent="pezapa-lot4kg/1.0 (https://github.com/Veleiroo)",
    )
    client.setMethod(POST)
    client.setReturnFormat(JSON)
    client.setQuery(query_text)
    payload = client.query().convert()

    rows = []
    for binding in payload["results"]["bindings"]:
        row = {}
        for key, value in binding.items():
            row[key] = convert_sparql_binding(value)
        rows.append(row)

    dataframe = pd.DataFrame(rows)
    output_name = REMOTE_QUERY_OUTPUTS[query_name]
    dataframe.to_csv(RESULTS_DIR / output_name, index=False)
    print(f"Saved {output_name} with {len(dataframe)} rows.")
    time.sleep(1)
    return dataframe


def parse_wkt_point(value):
    if not isinstance(value, str):
        return None, None

    match = WKT_POINT_RE.fullmatch(value.strip())
    if not match:
        return None, None

    lon = float(match.group(1))
    lat = float(match.group(2))
    return lat, lon


def is_missing(value) -> bool:
    return pd.isna(value) or value == ""


def first_non_missing(series: pd.Series):
    for value in series:
        if not is_missing(value):
            return value
    return None


def join_unique_values(series: pd.Series):
    values = []
    for value in series:
        if is_missing(value):
            continue
        text = str(value)
        if text not in values:
            values.append(text)
    return " | ".join(values) if values else None


def collapse_remote_rows(
    dataframe: pd.DataFrame,
    key_column: str,
    join_columns: set[str] | None = None,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    join_columns = join_columns or set()
    aggregations = {}

    for column in dataframe.columns:
        if column == key_column:
            continue
        aggregations[column] = (
            join_unique_values if column in join_columns else first_non_missing
        )

    return dataframe.groupby(key_column, as_index=False, dropna=False).agg(aggregations)


def enrich_with_coordinates(dataframe: pd.DataFrame, coord_column: str) -> pd.DataFrame:
    enriched = dataframe.copy()
    latitudes = []
    longitudes = []

    for value in enriched.get(coord_column, pd.Series(dtype=str)):
        lat, lon = parse_wkt_point(value)
        latitudes.append(lat)
        longitudes.append(lon)

    enriched["wikidataLat"] = latitudes
    enriched["wikidataLon"] = longitudes
    return enriched


def build_municipalities_dataset(local_df: pd.DataFrame, remote_df: pd.DataFrame) -> pd.DataFrame:
    remote_df = collapse_remote_rows(
        remote_df,
        "item",
        join_columns={"officialWebsite"},
    )
    remote_df = enrich_with_coordinates(remote_df, "coord").rename(
        columns={"item": "wd", "itemLabel": "wikidataLabel"}
    )
    merged = local_df.merge(remote_df, on="wd", how="left")
    merged["spacesPer100k"] = (
        merged["numSpaces"] / merged["population"] * 100000
    ).where(merged["population"].notna())
    output_path = RESULTS_DIR / "municipalities_enriched.csv"
    merged.to_csv(output_path, index=False)
    print(f"Saved {output_path.name} with {len(merged)} rows.")
    return merged


def build_spaces_dataset(local_df: pd.DataFrame, remote_df: pd.DataFrame) -> pd.DataFrame:
    remote_df = collapse_remote_rows(
        remote_df,
        "item",
        join_columns={"instanceOfLabel", "officialWebsite"},
    )
    remote_df = enrich_with_coordinates(remote_df, "coord").rename(
        columns={"item": "wd", "itemLabel": "wikidataLabel"}
    )
    merged = local_df.merge(remote_df, on="wd", how="left")
    output_path = RESULTS_DIR / "linked_spaces_enriched.csv"
    merged.to_csv(output_path, index=False)
    print(f"Saved {output_path.name} with {len(merged)} rows.")
    return merged


def print_summary(provinces: pd.DataFrame, municipalities: pd.DataFrame, spaces: pd.DataFrame) -> None:
    top_province = provinces.iloc[0]
    top_municipality = municipalities.iloc[0]
    top_space = spaces.iloc[0]

    print()
    print("Local KG summary")
    print(
        f"- Province with more spaces: {top_province['provinceName']} ({int(top_province['numSpaces'])})"
    )
    print(
        f"- Municipality with more spaces: {top_municipality['municipalityName']} ({int(top_municipality['numSpaces'])})"
    )
    print(
        f"- Largest linked space: {top_space['spaceName']} ({int(top_space['capacity'])} seats)"
    )


def main() -> None:
    ensure_results_dir()

    graph = Graph()
    graph.parse(KG_PATH, format="turtle")
    print(f"Loaded local KG from {KG_PATH} with {len(graph)} triples.")

    province_df = run_local_query(graph, "local_query_1.rq")
    municipality_df = run_local_query(graph, "local_query_2.rq")
    linked_spaces_df = run_local_query(graph, "local_query_3.rq")

    municipality_wikidata_df = run_wikidata_query(
        "federated_query_1.rq",
        municipality_df["wd"].dropna().astype(str).tolist(),
    )
    linked_spaces_wikidata_df = run_wikidata_query(
        "federated_query_2.rq",
        linked_spaces_df["wd"].dropna().astype(str).tolist(),
    )

    municipalities_enriched = build_municipalities_dataset(
        municipality_df, municipality_wikidata_df
    )
    linked_spaces_enriched = build_spaces_dataset(
        linked_spaces_df, linked_spaces_wikidata_df
    )

    print_summary(province_df, municipalities_enriched, linked_spaces_enriched)


if __name__ == "__main__":
    main()
