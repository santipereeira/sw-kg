"""
Página 3: Explorador SPARQL libre.
"""
import streamlit as st
import pandas as pd
from utils.sparql_queries import load_graph, run_custom_query, PREFIXES, TIPO_META

EJEMPLO_QUERIES = {
    "PDIs por provincia": """
SELECT ?provincia (COUNT(?pdi) AS ?total) WHERE {
    ?pdi rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    ?pdi gamere:situadaEn ?conc .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:nameProvincia ?provincia .
}
GROUP BY ?provincia
ORDER BY DESC(?total)
""",
    "PDIs por tipo": """
SELECT ?etiqueta (COUNT(?uri) AS ?total) WHERE {
    ?uri rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    ?clase rdfs:label ?etiqueta .
}
GROUP BY ?etiqueta
ORDER BY DESC(?total)
""",
    "PDIs por concello (top 20)": """
SELECT ?concello ?provincia (COUNT(?uri) AS ?total) WHERE {
    ?uri rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    ?uri gamere:situadaEn ?conc .
    ?conc gamere:nameConcello ?concello .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:nameProvincia ?provincia .
}
GROUP BY ?concello ?provincia
ORDER BY DESC(?total)
LIMIT 20
""",
    "Praias con bandeira azul": """
SELECT ?nombre ?concello ?provincia ?tipoArena ?lat ?lon WHERE {
    ?uri rdf:type gamere:Praia .
    ?uri gamere:banderaAzul true .
    ?uri gamere:nomePraia ?nombre .
    OPTIONAL { ?uri gamere:tipoArena ?tipoArena }
    OPTIONAL {
        ?uri gamere:situadaEn ?conc .
        ?conc gamere:nameConcello ?concello .
        ?conc gamere:perteneceA ?prov .
        ?prov gamere:nameProvincia ?provincia .
    }
    OPTIONAL {
        ?uri gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
    }
}
ORDER BY ?provincia ?concello ?nombre
""",
    "PDIs en Portugal": """
SELECT ?nombre ?tipo ?concello ?lat ?lon WHERE {
    ?uri rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
    ?uri gamere:nome ?nombre .
    ?uri gamere:situadaEn ?conc .
    ?conc gamere:nameConcello ?concello .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:perteneceA ?pais .
    ?pais gamere:namePais "Portugal" .
    OPTIONAL {
        ?uri gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
    }
}
ORDER BY ?tipo ?nombre
""",
    "Xacementos arqueolóxicos": """
SELECT ?nombre ?concello ?provincia ?lat ?lon WHERE {
    ?uri rdf:type gamere:XacementoArqueoloxco .
    ?uri gamere:nome ?nombre .
    OPTIONAL {
        ?uri gamere:situadaEn ?conc .
        ?conc gamere:nameConcello ?concello .
        ?conc gamere:perteneceA ?prov .
        ?prov gamere:nameProvincia ?provincia .
    }
    ?uri gamere:estaEn ?ub .
    ?ub gamere:coordenadasX ?lat ;
        gamere:coordenadasY ?lon .
}
ORDER BY ?provincia ?nombre
""",
    "PDIs cerca de Compostela (10 km)": """
SELECT ?nombre ?tipo ?concello ?lat ?lon WHERE {
    ?uri rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
    OPTIONAL { ?uri gamere:nome ?nombre }
    OPTIONAL { ?uri gamere:nomePraia ?nombre }
    ?uri gamere:estaEn ?ub .
    ?ub gamere:coordenadasX ?lat ;
        gamere:coordenadasY ?lon .
    OPTIONAL {
        ?uri gamere:situadaEn ?conc .
        ?conc gamere:nameConcello ?concello .
    }
    FILTER(?lat >= 42.79 && ?lat <= 42.97)
    FILTER(?lon >= -8.63 && ?lon <= -8.45)
}
ORDER BY ?tipo ?nombre
""",
    "Wikidata links de praias": """
SELECT ?nombre ?wikidata WHERE {
    ?uri rdf:type gamere:Praia .
    ?uri gamere:nomePraia ?nombre .
    ?uri owl:sameAs ?wikidata .
    FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org"))
}
ORDER BY ?nombre
LIMIT 50
""",

    "¿Cantas praias hai en Pontevedra?": """
    SELECT (COUNT(?pdi) AS ?total) WHERE {
    ?pdi rdf:type gamere:Praia .
    ?pdi gamere:situadaEn ?conc .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:nameProvincia "Pontevedra" .
}
""",
}

st.markdown("### Explorador SPARQL")

col_info, col_q, col_res = st.columns([0.8, 1.2, 1.8])

with col_info:
    st.markdown("**Clases**")
    for clase, meta in TIPO_META.items():
        st.markdown(
            f"<div style='font-size:0.78rem;padding:2px 0'>"
            f"{meta['emoji']} <code>gamere:{clase}</code></div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.markdown("**Propiedades**")
    props = [
        ("nome", "nome do PDI"),
        ("nomePraia", "nome praia"),
        ("banderaAzul", "boolean"),
        ("tipoArena", "area / cantos"),
        ("entorno", "urbano / natural"),
        ("lonxitude", "metros"),
        ("url", "Turgalicia"),
        ("fuenteDatos", "CSV orixe"),
        ("situadaEn", "→ Concello"),
        ("estaEn", "→ Ubicacion"),
        ("perteneceA", "→ Provincia/País"),
        ("coordenadasX", "latitude"),
        ("coordenadasY", "lonxitude"),
        ("nameConcello", "nome concello"),
        ("nameProvincia", "nome provincia"),
        ("namePais", "nome país"),
        ("owl:sameAs", "URI Wikidata"),
    ]
    for prop, desc in props:
        prefix = "" if prop.startswith("owl:") else "gamere:"
        st.markdown(
            f"<div style='font-size:0.74rem;padding:1px 0'>"
            f"<code>{prefix}{prop}</code>"
            f"<span style='color:#999;font-size:0.68rem'> {desc}</span></div>",
            unsafe_allow_html=True,
        )

with col_q:
    ejemplo = st.selectbox(
        "Exemplos",
        ["— Selecciona —"] + list(EJEMPLO_QUERIES.keys()),
    )
    query_inicial = ""
    if ejemplo != "— Selecciona —":
        query_inicial = EJEMPLO_QUERIES[ejemplo].strip()

    query = st.text_area(
        "Query SPARQL",
        value=query_inicial,
        height=340,
        placeholder="SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
    )
    st.caption("Prefixos `gamere:` `rdf:` `rdfs:` `owl:` `xsd:` xa declarados.")
    ejecutar = st.button("▶ Executar", width='stretch', type="primary")

with col_res:
    if ejecutar and query.strip():
        graph = load_graph()
        try:
            with st.spinner("Executando..."):
                cols, rows = run_custom_query(graph, query)

            if rows:
                df = pd.DataFrame(rows, columns=cols)
                st.success(f"**{len(rows)}** resultados")
                st.dataframe(df, width='stretch', height=280)
                st.download_button(
                    "⬇ Descargar CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="sparql_results.csv",
                    mime="text/csv",
                )

                if "lat" in cols and "lon" in cols:
                    import folium
                    from streamlit_folium import st_folium

                    st.markdown("**Mapa dos resultados**")
                    m = folium.Map(
                        location=[42.88, -8.54], zoom_start=8,
                        tiles="CartoDB Positron", attr="CartoDB",
                    )
                    nombre_col = next(
                        (c for c in ["nombre", "nome", "name"] if c in cols), None
                    )
                    for row in rows[:500]:
                        rd = dict(zip(cols, row))
                        try:
                            lat = float(rd["lat"])
                            lon = float(rd["lon"])
                            label = rd.get(nombre_col, "PDI") if nombre_col else "PDI"
                            folium.CircleMarker(
                                [lat, lon], radius=5,
                                color="#2d4a3e", fill=True, fill_opacity=0.75,
                                tooltip=label,
                            ).add_to(m)
                        except (ValueError, TypeError, KeyError):
                            pass
                    st_folium(m, width="100%", height=280, returned_objects=[])
            else:
                st.info("A query non devolveu resultados.")

        except Exception as e:
            st.error(f"**Error na query:** {e}")

    elif ejecutar:
        st.warning("Escribe unha query antes de executar.")
    else:
        st.markdown(
            "<div style='text-align:center;padding:4rem 1rem;color:#aaa'>"
            "<div style='font-size:2rem'>✦</div>"
            "<p style='margin-top:0.5rem'>Selecciona un exemplo ou escribe a túa query</p>"
            "</div>",
            unsafe_allow_html=True,
        )
