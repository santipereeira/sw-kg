from __future__ import annotations

import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError

import pandas as pd
from rdflib import Graph
from SPARQLWrapper import JSON, POST, SPARQLWrapper


ROOT = Path(__file__).resolve().parents[1]
KG_PATH = ROOT / "kg" / "output.ttl"
QUERIES_DIR = ROOT / "queries"
RESULTS_DIR = ROOT / "results" / "query_results"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

LOCAL_OUTPUTS = {
    "local_query_1.rq": "local_query_1.csv",
    "local_query_2.rq": "local_query_2.csv",
    "local_query_3.rq": "local_query_3.csv",
    "local_query_4.rq": "local_query_4.csv",
}

REMOTE_OUTPUTS = {
    "federated_query_1.rq": "federated_query_1.csv",
    "federated_query_2.rq": "federated_query_2.csv",
}


def ensure_results_dir() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_query(name: str) -> str:
    return (QUERIES_DIR / name).read_text(encoding="utf-8")


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
    output_name = LOCAL_OUTPUTS[query_name]
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


def run_wikidata_query(query_name: str, iris: list[str], retries: int = 4) -> pd.DataFrame:
    output_name = REMOTE_OUTPUTS[query_name]
    if not iris:
        dataframe = pd.DataFrame()
        dataframe.to_csv(RESULTS_DIR / output_name, index=False)
        print(f"Saved {output_name} with 0 rows.")
        return dataframe

    query_text = read_query(query_name).replace(
        "__VALUES__", " ".join(f"<{iri}>" for iri in sorted(set(iris)))
    )

    last_error = None
    for attempt in range(1, retries + 1):
        try:
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
            dataframe.to_csv(RESULTS_DIR / output_name, index=False)
            print(f"Saved {output_name} with {len(dataframe)} rows.")
            time.sleep(1)
            return dataframe
        except (HTTPError, URLError) as error:
            last_error = error
            if attempt == retries:
                break
            wait_seconds = attempt * 2
            print(
                f"Wikidata query {query_name} failed on attempt {attempt}/{retries} ({error}). "
                f"Retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

    raise RuntimeError(f"Could not execute {query_name} against Wikidata.") from last_error


def parse_wkt_point(value):
    if not isinstance(value, str):
        return None, None

    if not value.startswith("Point(") or not value.endswith(")"):
        return None, None

    lon_lat = value[len("Point(") : -1].split()
    if len(lon_lat) != 2:
        return None, None

    lon = float(lon_lat[0])
    lat = float(lon_lat[1])
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


def build_provinces_dataset(local_df: pd.DataFrame, remote_df: pd.DataFrame) -> pd.DataFrame:
    remote_df = collapse_remote_rows(
        remote_df,
        "item",
        join_columns={"capitalLabel"},
    ).rename(columns={"item": "wd", "itemLabel": "wikidataLabel"})
    merged = local_df.merge(remote_df, on="wd", how="left")
    merged["spacesPerMillion"] = (
        merged["numSpaces"] / merged["population"] * 1_000_000
    ).where(merged["population"].notna())
    output_path = RESULTS_DIR / "provinces_enriched.csv"
    merged.to_csv(output_path, index=False)
    print(f"Saved {output_path.name} with {len(merged)} rows.")
    return merged


def print_summary(
    provinces: pd.DataFrame,
    municipalities: pd.DataFrame,
    top_spaces: pd.DataFrame,
) -> None:
    top_province = provinces.iloc[0]
    top_municipality = municipalities.iloc[0]
    top_space = top_spaces.iloc[0]

    print()
    print("Local KG summary")
    print(
        f"- Province with more spaces: {top_province['provinceName']} ({int(top_province['numSpaces'])})"
    )
    print(
        f"- Municipality with more spaces: {top_municipality['municipalityName']} ({int(top_municipality['numSpaces'])})"
    )
    print(
        f"- Largest local space: {top_space['spaceName']} ({int(top_space['capacity'])} seats)"
    )


def main() -> None:
    ensure_results_dir()

    graph = Graph()
    graph.parse(KG_PATH, format="turtle")
    print(f"Loaded local KG from {KG_PATH} with {len(graph)} triples.")

    province_df = run_local_query(graph, "local_query_1.rq")
    municipality_df = run_local_query(graph, "local_query_2.rq")
    top_spaces_df = run_local_query(graph, "local_query_3.rq")
    province_links = run_local_query(graph, "local_query_4.rq")

    municipality_wikidata_df = run_wikidata_query(
        "federated_query_1.rq",
        municipality_df["wd"].dropna().astype(str).tolist(),
    )

    province_wikidata_df = run_wikidata_query(
        "federated_query_2.rq",
        province_links["wd"].dropna().astype(str).tolist(),
    )

    municipalities_enriched = build_municipalities_dataset(
        municipality_df, municipality_wikidata_df
    )
    provinces_enriched = build_provinces_dataset(
        province_links, province_wikidata_df
    )

    print_summary(province_df, municipalities_enriched, top_spaces_df)
    print(
        f"- Municipalities enriched with Wikidata: {len(municipalities_enriched)}"
    )
    print(f"- Provinces enriched with Wikidata: {len(provinces_enriched)}")


if __name__ == "__main__":
    main()
