"""
src/federated_wikidata.py
=========================
Explotación federada: KG local → Wikidata

Flujo:
  1. Extrae URIs de Wikidata presentes en el KG local (playas, concellos, provincias)
  2. Consulta Wikidata en batches para enriquecer con datos externos
  3. Exporta tablas enriquecidas a results/query_results/
  4. Genera mapas comparativos en results/maps/

Ejecutar desde la raíz del proyecto:
    python src/federated_wikidata.py
"""

import time
import json
from pathlib import Path
from rdflib import Graph
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd

KG_PATH      = Path("kg/output.nt")
ONTO_PATH    = Path("kg/ontologia.ttl")
RESULTS_DIR  = Path("results/query_results")
MAPS_DIR     = Path("results/maps")
FIGURES_DIR  = Path("results/figures")

for d in [RESULTS_DIR, MAPS_DIR, FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
PREFIXES_LOCAL = """
    PREFIX gamere: <http://example.org/def/gamere#>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:    <http://www.w3.org/2002/07/owl#>
    PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
"""


# ── Cargar KG ────────────────────────────────────────────────────────────────

def load_kg() -> Graph:
    g = Graph()
    if KG_PATH.exists():
        g.parse(str(KG_PATH), format="nt")
    if ONTO_PATH.exists():
        g.parse(str(ONTO_PATH), format="turtle")
    print(f"KG cargado: {len(g)} triples")
    return g


# ── Queries locales ───────────────────────────────────────────────────────────

def get_playas_con_wikidata(g: Graph) -> pd.DataFrame:
    """Extrae playas con bandera azul y su URI de Wikidata desde el KG local."""
    q = PREFIXES_LOCAL + """
    SELECT ?nombre ?concello ?provincia ?lat ?lon ?wikidata WHERE {
        ?praia rdf:type gamere:Praia .
        ?praia gamere:banderaAzul true .
        ?praia gamere:nomePraia ?nombre .
        ?praia owl:sameAs ?wikidata .
        FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org"))
        OPTIONAL {
            ?praia gamere:situadaEn ?conc .
            ?conc gamere:nameConcello ?concello .
            ?conc gamere:perteneceA ?prov .
            ?prov gamere:nameProvincia ?provincia .
        }
        OPTIONAL {
            ?praia gamere:estaEn ?ub .
            ?ub gamere:coordenadasX ?lat ;
                gamere:coordenadasY ?lon .
        }
    }
    ORDER BY ?provincia ?concello ?nombre
    """
    rows = []
    for r in g.query(q):
        rows.append({
            "nombre":    str(r.nombre),
            "concello":  str(r.concello)  if r.concello  else "",
            "provincia": str(r.provincia) if r.provincia else "",
            "lat":       float(r.lat)     if r.lat       else None,
            "lon":       float(r.lon)     if r.lon       else None,
            "wikidata":  str(r.wikidata),
            "qid":       str(r.wikidata).split("/")[-1],
        })
    return pd.DataFrame(rows)


def get_concellos_con_wikidata(g: Graph) -> pd.DataFrame:
    """Extrae concellos con URI de Wikidata desde el KG local."""
    q = PREFIXES_LOCAL + """
    SELECT ?nombre ?provincia ?codigo ?wikidata WHERE {
        ?conc rdf:type gamere:Concello .
        ?conc gamere:nameConcello ?nombre .
        ?conc owl:sameAs ?wikidata .
        FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org"))
        OPTIONAL { ?conc gamere:codigoConcello ?codigo }
        OPTIONAL {
            ?conc gamere:perteneceA ?prov .
            ?prov gamere:nameProvincia ?provincia .
        }
    }
    ORDER BY ?provincia ?nombre
    """
    rows = []
    for r in g.query(q):
        rows.append({
            "nombre":    str(r.nombre),
            "provincia": str(r.provincia) if r.provincia else "",
            "codigo":    str(r.codigo)    if r.codigo    else "",
            "wikidata":  str(r.wikidata),
            "qid":       str(r.wikidata).split("/")[-1],
        })
    return pd.DataFrame(rows)


# ── Consultas a Wikidata ──────────────────────────────────────────────────────

def query_wikidata(sparql_query: str, retries: int = 3) -> list[dict]:
    """Ejecuta una query SPARQL en Wikidata con reintentos."""
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", "GaliciaKG-TFG/1.0")
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    for attempt in range(retries):
        try:
            results = sparql.query().convert()
            return results["results"]["bindings"]
        except Exception as e:
            print(f"  Intento {attempt+1} fallido: {e}")
            time.sleep(2 ** attempt)
    return []


def enrich_playas_from_wikidata(df_playas: pd.DataFrame) -> pd.DataFrame:
    """
    Consulta Wikidata para enriquecer playas con:
    - imagen oficial (P18)
    - longitud de la playa en metros (P2043)
    - coordenadas oficiales de Wikidata (P625) para comparar con las del KG
    - etiqueta en gallego (si existe)
    """
    if df_playas.empty:
        return df_playas

    # Batch de hasta 80 QIDs por query
    qids = df_playas["qid"].dropna().unique().tolist()
    results = []

    for i in range(0, len(qids), 80):
        batch = qids[i:i+80]
        values = " ".join(f"wd:{q}" for q in batch)

        query = f"""
        SELECT ?item ?itemLabel ?itemLabelGl ?imagen ?longitud
               ?lat_wd ?lon_wd ?municipioLabel WHERE {{
          VALUES ?item {{ {values} }}
          OPTIONAL {{ ?item wdt:P18 ?imagen }}
          OPTIONAL {{ ?item wdt:P2043 ?longitud }}
          OPTIONAL {{
            ?item wdt:P625 ?coord .
            BIND(geof:latitude(?coord)  AS ?lat_wd)
            BIND(geof:longitude(?coord) AS ?lon_wd)
          }}
          OPTIONAL {{ ?item wdt:P131 ?municipio }}
          OPTIONAL {{
            ?item rdfs:label ?itemLabelGl .
            FILTER(LANG(?itemLabelGl) = "gl")
          }}
          SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "es,gl,en" .
          }}
        }}
        """
        rows = query_wikidata(query)
        for r in rows:
            results.append({
                "qid":          r["item"]["value"].split("/")[-1],
                "label_wd":     r.get("itemLabel",   {}).get("value", ""),
                "label_gl":     r.get("itemLabelGl", {}).get("value", ""),
                "imagen_url":   r.get("imagen",      {}).get("value", ""),
                "longitud_wd":  r.get("longitud",    {}).get("value", ""),
                "lat_wd":       r.get("lat_wd",      {}).get("value", ""),
                "lon_wd":       r.get("lon_wd",      {}).get("value", ""),
                "municipio_wd": r.get("municipioLabel", {}).get("value", ""),
            })
        time.sleep(0.5)  # Respetar rate limit de Wikidata

    df_wd = pd.DataFrame(results).drop_duplicates("qid")
    enriched = df_playas.merge(df_wd, on="qid", how="left")

    # Calcular diferencia de coordenadas (KG vs Wikidata) como indicador de calidad
    enriched["lat_wd"] = pd.to_numeric(enriched["lat_wd"], errors="coerce")
    enriched["lon_wd"] = pd.to_numeric(enriched["lon_wd"], errors="coerce")
    enriched["delta_lat"] = (enriched["lat"] - enriched["lat_wd"]).abs().round(5)
    enriched["delta_lon"] = (enriched["lon"] - enriched["lon_wd"]).abs().round(5)

    return enriched


def enrich_concellos_from_wikidata(df_conc: pd.DataFrame) -> pd.DataFrame:
    """
    Consulta Wikidata para enriquecer concellos con:
    - población (P1082)
    - superficie en km² (P2046)
    - sitio web oficial (P856)
    - imagen (P18)
    """
    if df_conc.empty:
        return df_conc

    qids = df_conc["qid"].dropna().unique().tolist()
    results = []

    for i in range(0, len(qids), 80):
        batch = qids[i:i+80]
        values = " ".join(f"wd:{q}" for q in batch)

        query = f"""
        SELECT ?item ?poblacion ?superficie ?web ?imagen WHERE {{
          VALUES ?item {{ {values} }}
          OPTIONAL {{ ?item wdt:P1082 ?poblacion }}
          OPTIONAL {{ ?item wdt:P2046 ?superficie }}
          OPTIONAL {{ ?item wdt:P856  ?web }}
          OPTIONAL {{ ?item wdt:P18   ?imagen }}
        }}
        """
        rows = query_wikidata(query)
        for r in rows:
            results.append({
                "qid":        r["item"]["value"].split("/")[-1],
                "poblacion":  r.get("poblacion",  {}).get("value", ""),
                "superficie": r.get("superficie", {}).get("value", ""),
                "web":        r.get("web",        {}).get("value", ""),
                "imagen":     r.get("imagen",     {}).get("value", ""),
            })
        time.sleep(0.5)

    df_wd = pd.DataFrame(results).drop_duplicates("qid")
    return df_conc.merge(df_wd, on="qid", how="left")


# ── Mapas ─────────────────────────────────────────────────────────────────────

def generate_map_playas(df: pd.DataFrame, output_path: Path):
    """Genera mapa HTML con marcadores de playas enriquecidas con datos de Wikidata."""
    try:
        import folium
    except ImportError:
        print("  folium no instalado, saltando mapa")
        return

    m = folium.Map(location=[42.88, -8.54], zoom_start=8,
                   tiles="CartoDB Positron", attr="CartoDB")

    for _, row in df.iterrows():
        if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
            continue

        longitud_str = (f"<br>📏 {float(row['longitud_wd']):.0f} m"
                        if row.get("longitud_wd") else "")
        img_str = (f'<br><img src="{row["imagen_url"]}" width="200"/>'
                   if row.get("imagen_url") else "")
        wd_link = f'<br><a href="{row["wikidata"]}" target="_blank">🔗 Wikidata</a>'

        popup_html = (
            f"<div style='font-family:sans-serif;max-width:220px'>"
            f"<b>🏖️ {row['nombre']}</b><br>"
            f"<small>{row.get('concello','')} · {row.get('provincia','')}</small>"
            f"{longitud_str}{wd_link}{img_str}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7, color="#0077b6",
            fill=True, fill_color="#0077b6", fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"🏖️ {row['nombre']}",
        ).add_to(m)

    m.save(str(output_path))
    print(f"  Mapa guardado: {output_path}")


# ── Estadísticas y figuras ────────────────────────────────────────────────────

def generate_stats_chart(df_playas_enrich: pd.DataFrame, df_conc_enrich: pd.DataFrame):
    """Genera gráficos básicos de los datos enriquecidos."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")
    except ImportError:
        print("  matplotlib no instalado, saltando gráficos")
        return

    # Gráfico 1: playas con bandera azul por provincia
    if not df_playas_enrich.empty and "provincia" in df_playas_enrich.columns:
        fig, ax = plt.subplots(figsize=(8, 4))
        df_playas_enrich.groupby("provincia").size().sort_values().plot(
            kind="barh", ax=ax, color="#0077b6"
        )
        ax.set_title("Praias con Bandeira Azul por provincia (KG + Wikidata)")
        ax.set_xlabel("Número de praias")
        fig.tight_layout()
        path = FIGURES_DIR / "praias_por_provincia.png"
        fig.savefig(str(path), dpi=150)
        plt.close(fig)
        print(f"  Gráfico guardado: {path}")

    # Gráfico 2: concellos con más población (Wikidata)
    if not df_conc_enrich.empty and "poblacion" in df_conc_enrich.columns:
        df_pop = df_conc_enrich.copy()
        df_pop["poblacion"] = pd.to_numeric(df_pop["poblacion"], errors="coerce")
        df_pop = df_pop.dropna(subset=["poblacion"]).nlargest(15, "poblacion")
        if not df_pop.empty:
            fig, ax = plt.subplots(figsize=(8, 5))
            df_pop.set_index("nombre")["poblacion"].sort_values().plot(
                kind="barh", ax=ax, color="#2d4a3e"
            )
            ax.set_title("Top 15 concellos por poboación (datos de Wikidata)")
            ax.set_xlabel("Poboación")
            fig.tight_layout()
            path = FIGURES_DIR / "concellos_poblacion.png"
            fig.savefig(str(path), dpi=150)
            plt.close(fig)
            print(f"  Gráfico guardado: {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Explotación federada: KG local → Wikidata")
    print("=" * 60)

    g = load_kg()

    # 1. Extraer datos locales
    print("\n[1] Extrayendo datos del KG local...")
    df_playas = get_playas_con_wikidata(g)
    df_conc   = get_concellos_con_wikidata(g)
    print(f"    Playas con Wikidata: {len(df_playas)}")
    print(f"    Concellos con Wikidata: {len(df_conc)}")

    df_playas.to_csv(RESULTS_DIR / "local_playas_bandera_azul.csv",
                     index=False, encoding="utf-8-sig")
    df_conc.to_csv(RESULTS_DIR / "local_concellos.csv",
                   index=False, encoding="utf-8-sig")

    # 2. Enriquecer desde Wikidata
    print("\n[2] Consultando Wikidata (puede tardar ~30s)...")
    df_playas_enrich = enrich_playas_from_wikidata(df_playas)
    df_conc_enrich   = enrich_concellos_from_wikidata(df_conc)

    df_playas_enrich.to_csv(RESULTS_DIR / "enriched_playas.csv",
                            index=False, encoding="utf-8-sig")
    df_conc_enrich.to_csv(RESULTS_DIR / "enriched_concellos.csv",
                          index=False, encoding="utf-8-sig")

    print(f"    Playas enriquecidas: {len(df_playas_enrich)}")
    print(f"    Concellos enriquecidos: {len(df_conc_enrich)}")

    # 3. Mapa
    print("\n[3] Generando mapa...")
    generate_map_playas(df_playas_enrich, MAPS_DIR / "praias_bandera_azul_enriched.html")

    # 4. Gráficos
    print("\n[4] Generando gráficos...")
    generate_stats_chart(df_playas_enrich, df_conc_enrich)

    # 5. Resumen
    print("\n[5] Resumen de enriquecimiento:")
    if not df_playas_enrich.empty:
        con_imagen = df_playas_enrich["imagen_url"].notna().sum()
        con_long   = df_playas_enrich["longitud_wd"].notna().sum()
        print(f"    Playas con imagen en Wikidata:    {con_imagen}/{len(df_playas_enrich)}")
        print(f"    Playas con longitud en Wikidata:  {con_long}/{len(df_playas_enrich)}")
        delta_ok = df_playas_enrich["delta_lat"].notna().sum()
        if delta_ok > 0:
            mean_d = df_playas_enrich["delta_lat"].mean()
            print(f"    Desviación media lat KG vs WD:    {mean_d:.5f}°")

    print("\n✨ Resultados en results/")
    print("   query_results/enriched_playas.csv")
    print("   query_results/enriched_concellos.csv")
    print("   maps/praias_bandera_azul_enriched.html")
    print("   figures/praias_por_provincia.png")
