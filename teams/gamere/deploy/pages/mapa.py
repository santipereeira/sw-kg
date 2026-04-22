"""
Página 1: Mapa interactivo + buscador de PDIs cercanos.
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.sparql_queries import load_graph, get_all_pdi, get_nearby_pdi, get_stats, TIPO_META

g = load_graph()
st.markdown("### Mapa interactivo de puntos")

col_filters, col_map, col_stats = st.columns([1, 2.5, 0.8])

# ── Filtros y búsqueda ────────────────────────────────────────────────────
with col_filters:
    st.markdown("#### Filtros")
    todos_tipos = list(TIPO_META.keys())
    tipos_sel = st.multiselect(
        "Tipos de PDI",
        options=todos_tipos,
        default=todos_tipos,
        format_func=lambda t: f"{TIPO_META[t]['emoji']} {TIPO_META[t]['label']}",
    )

    st.markdown("---")
    st.markdown("#### Buscar ao redor")
    modo = st.radio("Modo", ["Seleccionar PDI", "Coordenadas manuais"], horizontal=True, index=1)

    lat_centro, lon_centro, nombre_centro = None, None, None

    if modo == "Seleccionar PDI":
        todos = get_all_pdi(g)
        if todos:
            opciones = {f"{p['emoji']} {p['nombre']} ({p['label']})": p for p in todos}
            sel = st.selectbox("Punto de partida", list(opciones.keys()))
            if sel:
                base = opciones[sel]
                lat_centro, lon_centro, nombre_centro = base["lat"], base["lon"], base["nombre"]
        else:
            st.warning("Non hai PDIs cargados.")
    else:
        lat_centro    = st.number_input("Latitude",  value=42.88, format="%.5f")
        lon_centro    = st.number_input("Lonxitude", value=-8.54, format="%.5f")
        nombre_centro = "Punto seleccionado"

    radio_km = st.slider("Radio (km)", 1, 50, 10)
    buscar   = st.button("🔎 Buscar", width='stretch', type="primary")

# ── Mapa ──────────────────────────────────────────────────────────────────
with col_map:
    tipo_filter = tipos_sel if tipos_sel else []
    pdi_list    = get_all_pdi(g, tipo_filter=tipo_filter) if tipo_filter else []

    center     = [lat_centro, lon_centro] if lat_centro else [42.88, -8.54]
    zoom_start = 11 if lat_centro else 9

    m = folium.Map(location=center, zoom_start=zoom_start,
                    tiles="CartoDB Positron", attr="CartoDB")

    feature_groups = {
        k: folium.FeatureGroup(name=f"{v['emoji']} {v['label']}", show=True)
        for k, v in TIPO_META.items()
    }

    for pdi in pdi_list:
        fg = feature_groups.get(pdi["tipo"], feature_groups["OutrosPDI"])
        url_tag = (f'<br><a href="{pdi["url"]}" target="_blank">🔗 Ver máis</a>'
                    if pdi["url"] else "")
        popup_html = (
            f"<div style='font-family:sans-serif;min-width:180px'>"
            f"<b style='color:{pdi['color']}'>{pdi['emoji']} {pdi['nombre']}</b><br>"
            f"<small style='color:#666'>{pdi['label']}</small>"
            f"{'<br><small>📍 ' + pdi['concello'] + '</small>' if pdi['concello'] else ''}"
            f"{url_tag}</div>"
        )
        folium.CircleMarker(
            location=[pdi["lat"], pdi["lon"]],
            radius=6, color=pdi["color"],
            fill=True, fill_color=pdi["color"],
            fill_opacity=0.75, weight=1.5,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{pdi['emoji']} {pdi['nombre']}",
        ).add_to(fg)

    for fg in feature_groups.values():
        fg.add_to(m)

    cercanos = []
    if buscar and lat_centro:
        cercanos = get_nearby_pdi(g, lat_centro, lon_centro, radio_km)

        folium.Marker(
            location=[lat_centro, lon_centro],
            popup=f"<b>📍 {nombre_centro}</b>",
            icon=folium.Icon(color="red", icon="star", prefix="fa"),
        ).add_to(m)

        folium.Circle(
            location=[lat_centro, lon_centro],
            radius=radio_km * 1000,
            color="#2d4a3e", fill=True,
            fill_opacity=0.05, weight=2, dash_array="6",
        ).add_to(m)

        for p in cercanos:
            folium.CircleMarker(
                location=[p["lat"], p["lon"]],
                radius=9, color=p["color"],
                fill=True, fill_color=p["color"],
                fill_opacity=0.9, weight=2.5,
                popup=folium.Popup(
                    f"<b>{p['emoji']} {p['nombre']}</b><br>"
                    f"<small>{p['label']}</small><br>"
                    f"🗺️ {p['distancia_km']} km",
                    max_width=200,
                ),
                tooltip=f"{p['emoji']} {p['nombre']} — {p['distancia_km']} km",
            ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    st_folium(m, width="100%", height=560, returned_objects=[])

    if cercanos:
        st.markdown(
            f"**{len(cercanos)} sitios** nun radio de {radio_km} km de *{nombre_centro}*"
        )
        cols2 = st.columns(2)
        for i, p in enumerate(cercanos[:20]):
            with cols2[i % 2]:
                st.markdown(
                    f'<div class="pdi-card">'
                    f'<span class="tipo-badge">{p["emoji"]} {p["label"]}</span>'
                    f'<h4>{p["nombre"]}</h4>'
                    f'<p>📍 {p["concello"] or "Galicia"} &nbsp;·&nbsp; 🗺️ {p["distancia_km"]} km</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ── Stats ─────────────────────────────────────────────────────────────────
with col_stats:
    st.markdown("#### Knowledge Graph")
    stats = get_stats(g)
    total = sum(v["total"] for v in stats.values())
    
    # Usamos markdown con una sola línea para evitar el padding extra de st.text
    # Opción ultra-compacta si el markdown estándar sigue pareciendo muy separado
    st.markdown(f"<div style='margin-top:-15px; font-weight:bold;'>Total PDIs: {total}</div>", unsafe_allow_html=True)
    
    for tipo, info in stats.items():
        st.markdown(
            f"<div style='font-size:0.82rem;padding:2px 0'>"
            f"{info['emoji']} <b>{info['label']}</b>: {info['total']}</div>",
            unsafe_allow_html=True,
        )