"""
Página 4: Enriquecemento con Wikidata
Consulta federada: KG local → Wikidata
"""
import time
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from SPARQLWrapper import SPARQLWrapper, JSON
from utils.sparql_queries import load_graph, PREFIXES

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


def get_playas_wikidata_uris(graph):
    q = PREFIXES + """
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
    for r in graph.query(q):
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


def get_concellos_wikidata_uris(graph):
    q = PREFIXES + """
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
    for r in graph.query(q):
        rows.append({
            "nombre":    str(r.nombre),
            "provincia": str(r.provincia) if r.provincia else "",
            "codigo":    str(r.codigo)    if r.codigo    else "",
            "wikidata":  str(r.wikidata),
            "qid":       str(r.wikidata).split("/")[-1],
        })
    return pd.DataFrame(rows)


def query_wikidata_batch(qids: list, query_template: str) -> pd.DataFrame:
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", "GaliciaKG-StreamlitApp/1.0")
    sparql.setReturnFormat(JSON)
    results = []
    for i in range(0, len(qids), 50):
        batch  = qids[i:i+50]
        values = " ".join(f"wd:{q}" for q in batch)
        sparql.setQuery(query_template.format(values=values))
        try:
            data = sparql.query().convert()
            for r in data["results"]["bindings"]:
                row = {k: v["value"] for k, v in r.items()}
                row["qid"] = row.get("item", "").split("/")[-1]
                results.append(row)
        except Exception as e:
            st.warning(f"Erro consultando Wikidata (batch {i//50+1}): {e}")
        time.sleep(0.4)
    return pd.DataFrame(results)


PLAYAS_WD_QUERY = """
SELECT ?item ?longitud ?imagen ?labelGl ?lat_wd ?lon_wd WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wdt:P2043 ?longitud }}
  OPTIONAL {{ ?item wdt:P18   ?imagen }}
  OPTIONAL {{
    ?item rdfs:label ?labelGl .
    FILTER(LANG(?labelGl) = "gl")
  }}
  OPTIONAL {{
    ?item wdt:P625 ?coord .
    BIND(geof:latitude(?coord)  AS ?lat_wd)
    BIND(geof:longitude(?coord) AS ?lon_wd)
  }}
}}
"""

CONCELLOS_WD_QUERY = """
SELECT ?item ?poblacion ?superficie ?web WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wdt:P1082 ?poblacion }}
  OPTIONAL {{ ?item wdt:P2046 ?superficie }}
  OPTIONAL {{ ?item wdt:P856  ?web }}
}}
"""


def render():
    st.markdown("### Enriquecemento con Wikidata")
    st.markdown(
        "A consulta parte dos enlaces `owl:sameAs` do KG local "
        "e enriquece os datos con información externa de Wikidata."
    )

    graph = load_graph()

    tab_playas, tab_concellos = st.tabs([
        "Praias con Bandeira Azul", "Concellos"
    ])

    # ── TAB 1: PLAYAS ─────────────────────────────────────────────────────────
    with tab_playas:
        st.markdown("##### Paso 1 — Datos do KG local")
        with st.spinner("Consultando KG local..."):
            df_local = get_playas_wikidata_uris(graph)

        if df_local.empty:
            st.error("Non se atoparon praias con owl:sameAs no KG.")
        else:
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Praias no KG", len(df_local))
            col_b.metric("Con URI Wikidata", df_local["qid"].notna().sum())
            col_c.metric("Provincias", df_local["provincia"].nunique())

            with st.expander("Ver datos locais (KG)"):
                st.dataframe(
                    df_local[["nombre", "concello", "provincia", "lat", "lon", "wikidata"]],
                    width=True,
                )

            st.markdown("##### Paso 2 — Enriquecemento dende Wikidata")
            st.caption("Recupera: nome en galego, lonxitude oficial, imaxe e coordenadas de Wikidata.")

            if st.button("Consultar Wikidata (praias)", type="primary"):
                qids = df_local["qid"].dropna().tolist()
                with st.spinner(f"Consultando Wikidata para {len(qids)} praias..."):
                    df_wd = query_wikidata_batch(qids, PLAYAS_WD_QUERY)
                if not df_wd.empty:
                    df_merged = df_local.merge(df_wd, on="qid", how="left")
                    df_merged["lat_wd"] = pd.to_numeric(
                        df_merged.get("lat_wd", pd.Series(dtype=float)), errors="coerce"
                    )
                    df_merged["lon_wd"] = pd.to_numeric(
                        df_merged.get("lon_wd", pd.Series(dtype=float)), errors="coerce"
                    )
                    df_merged["delta_coord"] = (
                        (df_merged["lat"] - df_merged["lat_wd"]).abs() +
                        (df_merged["lon"] - df_merged["lon_wd"]).abs()
                    ).round(5)
                    st.session_state["wd_praias_result"] = df_merged
                else:
                    st.warning("Wikidata non devolveu resultados.")

            df_merged = st.session_state.get("wd_praias_result")
            if df_merged is not None:
                st.success(f"✅ {len(df_merged)} praias enriquecidas")

                c1, c2, c3 = st.columns(3)
                c1.metric("Con lonxitude (Wikidata)",
                          df_merged["longitud"].notna().sum() if "longitud" in df_merged.columns else 0)
                c2.metric("Con imaxe (Wikidata)",
                          df_merged["imagen"].notna().sum() if "imagen" in df_merged.columns else 0)
                c3.metric("Con nome en galego",
                          df_merged["labelGl"].notna().sum() if "labelGl" in df_merged.columns else 0)

                cols_show = ["nombre", "concello", "provincia"]
                for c in ["labelGl", "longitud", "delta_coord"]:
                    if c in df_merged.columns:
                        cols_show.append(c)
                cols_show.append("wikidata")
                st.dataframe(df_merged[cols_show], width='stretch', height=300)

                st.markdown("##### Mapa — Praias Bandeira Azul (datos enriquecidos)")
                m = folium.Map(location=[42.88, -8.54], zoom_start=8,
                               tiles="CartoDB Positron", attr="CartoDB")
                for _, row in df_merged.iterrows():
                    if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
                        continue
                    long_str = ""
                    if pd.notna(row.get("longitud")):
                        try:
                            long_str = f"<br>📏 {float(row['longitud']):.0f} m"
                        except Exception:
                            pass
                    img_str = ""
                    if pd.notna(row.get("imagen")):
                        img_str = f'<br><img src="{row["imagen"]}" width="180"/>'
                    label = row.get("labelGl") or row["nombre"]
                    popup_html = (
                        f"<div style='font-family:sans-serif;max-width:200px'>"
                        f"<b>🏖️ {label}</b><br>"
                        f"<small>{row['concello']} · {row['provincia']}</small>"
                        f"{long_str}"
                        f'<br><a href="{row["wikidata"]}" target="_blank">🔗 Wikidata</a>'
                        f"{img_str}</div>"
                    )
                    folium.CircleMarker(
                        location=[row["lat"], row["lon"]],
                        radius=7, color="#0077b6",
                        fill=True, fill_color="#0077b6", fill_opacity=0.85,
                        popup=folium.Popup(popup_html, max_width=220),
                        tooltip=f"🏖️ {label}",
                    ).add_to(m)
                st_folium(m, width="100%", height=420, returned_objects=[])

                st.download_button(
                    "⬇ Descargar CSV enriquecido",
                    data=df_merged.to_csv(index=False).encode("utf-8"),
                    file_name="praias_enriquecidas_wikidata.csv",
                    mime="text/csv",
                )

    # ── TAB 2: CONCELLOS ──────────────────────────────────────────────────────
    with tab_concellos:
        st.markdown("##### Paso 1 — Concellos con URI Wikidata no KG")
        with st.spinner("Consultando KG local..."):
            df_conc = get_concellos_wikidata_uris(graph)

        if df_conc.empty:
            st.error("Non se atoparon concellos con owl:sameAs no KG.")
        else:
            col_a, col_b = st.columns(2)
            col_a.metric("Concellos no KG", len(df_conc))
            col_b.metric("Con URI Wikidata", df_conc["qid"].notna().sum())

            with st.expander("Ver concellos locais"):
                st.dataframe(
                    df_conc[["nombre", "provincia", "codigo", "wikidata"]],
                    width='stretch',
                )

            st.markdown("##### Paso 2 — Enriquecemento desde Wikidata")
            st.caption("Recupera: poboación, superficie e sitio web oficial.")

            if st.button("Consultar Wikidata (concellos)", type="primary"):
                qids = df_conc["qid"].dropna().tolist()
                with st.spinner(f"Consultando Wikidata para {len(qids)} concellos..."):
                    df_wd = query_wikidata_batch(qids, CONCELLOS_WD_QUERY)
                if not df_wd.empty:
                    df_merged_c = df_conc.merge(df_wd, on="qid", how="left")
                    df_merged_c["poblacion"]  = pd.to_numeric(
                        df_merged_c.get("poblacion",  pd.Series(dtype=float)), errors="coerce"
                    )
                    df_merged_c["superficie"] = pd.to_numeric(
                        df_merged_c.get("superficie", pd.Series(dtype=float)), errors="coerce"
                    )
                    st.session_state["wd_concellos_result"] = df_merged_c
                else:
                    st.warning("Wikidata non devolveu resultados.")

            df_merged_c = st.session_state.get("wd_concellos_result")
            if df_merged_c is not None:
                st.success(f"✅ {len(df_merged_c)} concellos enriquecidos")

                c1, c2 = st.columns(2)
                c1.metric("Con poboación",  df_merged_c["poblacion"].notna().sum())
                c2.metric("Con superficie", df_merged_c["superficie"].notna().sum())

                df_top = (
                    df_merged_c.dropna(subset=["poblacion"])
                    .nlargest(15, "poblacion")
                    [["nombre", "provincia", "poblacion", "superficie", "web"]]
                )
                st.markdown("**Top 15 concellos por poboación (Wikidata)**")
                st.dataframe(df_top, width='stretch')

                st.download_button(
                    "⬇ Descargar CSV enriquecido",
                    data=df_merged_c.to_csv(index=False).encode("utf-8"),
                    file_name="concellos_enriquecidos_wikidata.csv",
                    mime="text/csv",
                )

render()
