from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
QUERY_RESULTS_DIR = ROOT / "results" / "query_results"
FIGURES_DIR = ROOT / "results" / "figures"
MAPS_DIR = ROOT / "results" / "maps"


def load_csv(name: str) -> pd.DataFrame:
    path = QUERY_RESULTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python3 src/run_queries.py` first."
        )
    return pd.read_csv(path)


def normalized(value):
    return None if pd.isna(value) else value


def plot_spaces_by_province(dataframe: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(8, 5))
    colors = ["#274c77", "#6096ba", "#a3cef1", "#8b8c89"]
    axis.bar(
        dataframe["provinceName"],
        dataframe["numSpaces"],
        color=colors[: len(dataframe)],
        edgecolor="#1b263b",
    )
    axis.set_title("Spaces per province in the local KG")
    axis.set_xlabel("Province")
    axis.set_ylabel("Number of spaces")
    axis.grid(axis="y", linestyle="--", alpha=0.35)
    figure.tight_layout()
    output_path = FIGURES_DIR / "spaces_by_province.png"
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    print(f"Saved {output_path.name}.")


def plot_municipalities_spaces_vs_population(dataframe: pd.DataFrame) -> None:
    filtered = dataframe.dropna(subset=["population", "numSpaces", "avgCapacity"]).copy()
    filtered["population"] = pd.to_numeric(filtered["population"])
    filtered["numSpaces"] = pd.to_numeric(filtered["numSpaces"])
    filtered["avgCapacity"] = pd.to_numeric(filtered["avgCapacity"])

    figure, axis = plt.subplots(figsize=(9, 6))
    scatter = axis.scatter(
        filtered["population"],
        filtered["numSpaces"],
        s=filtered["avgCapacity"] * 0.7,
        c=filtered["avgCapacity"],
        cmap="Blues",
        alpha=0.8,
        edgecolor="#1b263b",
        linewidth=0.5,
    )

    labels = filtered.sort_values(
        ["numSpaces", "avgCapacity"], ascending=[False, False]
    ).head(8)
    for row in labels.itertuples():
        axis.annotate(
            row.municipalityName,
            (row.population, row.numSpaces),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    axis.set_title("Local spaces vs Wikidata population")
    axis.set_xlabel("Population from Wikidata")
    axis.set_ylabel("Number of local spaces")
    axis.grid(linestyle="--", alpha=0.35)
    colorbar = figure.colorbar(scatter, ax=axis)
    colorbar.set_label("Average capacity")
    figure.tight_layout()
    output_path = FIGURES_DIR / "municipalities_spaces_vs_population.png"
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    print(f"Saved {output_path.name}.")


def plot_province_spaces_per_million(dataframe: pd.DataFrame) -> None:
    filtered = dataframe.dropna(subset=["spacesPerMillion"]).copy()
    filtered["spacesPerMillion"] = pd.to_numeric(filtered["spacesPerMillion"])

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.barh(
        filtered["provinceName"],
        filtered["spacesPerMillion"],
        color="#e76f51",
        edgecolor="#1d3557",
    )
    axis.set_title("Spaces per million inhabitants by province")
    axis.set_xlabel("Spaces per million inhabitants")
    axis.set_ylabel("Province")
    axis.grid(axis="x", linestyle="--", alpha=0.35)
    figure.tight_layout()
    output_path = FIGURES_DIR / "province_spaces_per_million.png"
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    print(f"Saved {output_path.name}.")


def plot_top_spaces_by_capacity(dataframe: pd.DataFrame) -> None:
    # The source query surfaces duplicated rows for merged resources such as
    # "Auditorio Rocio Jurado", so collapse by local resource before plotting.
    collapsed = (
        dataframe.sort_values(["capacity", "spaceName"], ascending=[False, True])
        .drop_duplicates(subset=["space"], keep="first")
        .head(8)
        .copy()
    )
    collapsed["label"] = (
        collapsed["spaceName"] + " (" + collapsed["municipalityName"] + ")"
    )
    collapsed = collapsed.sort_values("capacity", ascending=True)

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(
        collapsed["label"],
        collapsed["capacity"],
        color="#2a9d8f",
        edgecolor="#1d3557",
    )
    axis.set_title("Largest spaces by seating capacity")
    axis.set_xlabel("Capacity")
    axis.set_ylabel("Space")
    axis.grid(axis="x", linestyle="--", alpha=0.35)
    figure.tight_layout()
    output_path = FIGURES_DIR / "top_spaces_by_capacity.png"
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    print(f"Saved {output_path.name}.")


def build_popup(point: dict[str, object]) -> str:
    website = normalized(point.get("officialWebsite"))
    website_html = (
        f'<a href="{website}" target="_blank" rel="noreferrer">official website</a>'
        if website
        else "No official website"
    )
    wikidata_label = normalized(point.get("wikidataLabel")) or point["municipalityName"]
    return (
        f"<strong>{point['municipalityName']}</strong><br>"
        f"Wikidata label: {wikidata_label}<br>"
        f"Province: {point['provinceName']}<br>"
        f"Local spaces: {int(point['numSpaces'])}<br>"
        f"Average capacity: {round(float(point['avgCapacity']), 2)}<br>"
        f"Population: {int(float(point['population'])) if normalized(point.get('population')) else 'Unknown'}<br>"
        f"{website_html}"
    )


def build_map(municipalities: pd.DataFrame) -> None:
    valid = municipalities.dropna(subset=["wikidataLat", "wikidataLon"]).copy()
    valid["wikidataLat"] = pd.to_numeric(valid["wikidataLat"])
    valid["wikidataLon"] = pd.to_numeric(valid["wikidataLon"])

    points = []
    for row in valid.itertuples():
        record = row._asdict()
        record["popup"] = build_popup(record)
        points.append(record)

    center_lat = sum(point["wikidataLat"] for point in points) / len(points)
    center_lon = sum(point["wikidataLon"] for point in points) / len(points)
    payload = json.dumps(points, ensure_ascii=False)

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pezapa KG municipalities</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  >
  <style>
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(135deg, #f7ede2, #fff1e6);
      color: #1d3557;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 320px 1fr;
      min-height: 100vh;
    }}
    .panel {{
      padding: 28px 24px;
      border-right: 1px solid rgba(29, 53, 87, 0.15);
      background: rgba(255, 255, 255, 0.72);
      backdrop-filter: blur(10px);
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.8rem;
      color: #b56576;
      margin-bottom: 12px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 2rem;
      line-height: 1.1;
    }}
    p {{
      line-height: 1.5;
    }}
    .metric {{
      margin-top: 18px;
      padding-top: 18px;
      border-top: 1px solid rgba(29, 53, 87, 0.15);
    }}
    #map {{
      height: 100vh;
      width: 100%;
    }}
    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
      .panel {{
        border-right: 0;
        border-bottom: 1px solid rgba(29, 53, 87, 0.15);
      }}
      #map {{
        height: 70vh;
      }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <section class="panel">
      <div class="eyebrow">LOT4KG Task 6</div>
      <h1>Municipalities linked to Wikidata</h1>
      <p>
        This map starts from the local Pezapa KG and uses municipality links
        materialized in the mappings to recover population, coordinates and
        website information from Wikidata.
      </p>
      <div class="metric"><strong>{len(points)}</strong> municipalities enriched and mapped.</div>
      <div class="metric">
        Marker size reflects the number of local spaces represented in each
        municipality.
      </div>
    </section>
    <div id="map"></div>
  </div>
  <script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""
  ></script>
  <script>
    const points = {payload};
    const map = L.map("map").setView([{center_lat:.6f}, {center_lon:.6f}], 7);
    L.tileLayer("https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }}).addTo(map);

    points.forEach((point) => {{
      L.circleMarker([point.wikidataLat, point.wikidataLon], {{
        radius: 6 + Math.min(point.numSpaces * 2, 10),
        color: "#1d3557",
        weight: 1,
        fillColor: "#e76f51",
        fillOpacity: 0.85
      }})
        .bindPopup(point.popup)
        .addTo(map);
    }});
  </script>
</body>
</html>
"""

    output_path = MAPS_DIR / "municipalities_map.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Saved {output_path.name}.")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    province_df = load_csv("local_query_1.csv")
    municipalities_df = load_csv("municipalities_enriched.csv")
    provinces_df = load_csv("provinces_enriched.csv")
    top_spaces_df = load_csv("local_query_3.csv")

    plot_spaces_by_province(province_df)
    plot_municipalities_spaces_vs_population(municipalities_df)
    plot_province_spaces_per_million(provinces_df)
    plot_top_spaces_by_capacity(top_spaces_df)
    build_map(municipalities_df)


if __name__ == "__main__":
    main()
