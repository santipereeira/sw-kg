import streamlit as st
import os
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import pandas as pd
from pyproj import Transformer
from rdflib import Graph
import ollama
import numpy as np

# Importamos la lógica existente para LLM
from llm_query_gen import generate_sparql, KG_SCHEMA

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
TAREA_6_DIR = os.path.abspath(os.path.join(SRC_DIR, '..'))
REPO_DIR = os.path.abspath(os.path.join(TAREA_6_DIR, '..'))
DATA_DIR = os.path.join(TAREA_6_DIR, 'data', 'processed')
KG_PATH = os.path.join(REPO_DIR, 'TAREA_4', 'kg', 'output.nt')

st.set_page_config(page_title="Sports KG Explorer", layout="wide")

# Estilos de la app, generado con IA :))))
st.markdown("""
    <style>
    .stApp {
        background-color: #f9f7f0;
        color: #1f2933;
    }
    .main { background-color: #f9f7f0; }
    .stMetric {
        background-color: #fdf5e6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stMetric label, .stMetric [data-testid="stMetricValue"] {
        color: #1f2933;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #3498db;
        color: white;
    }
    div[data-testid="stAlert"] {
        color: #1f2933;
        border-radius: 10px;
    }
    div[data-testid="stAlert"] p {
        color: inherit;
    }
    div[data-testid="stAlert"][kind="success"] {
        background-color: #dff3e4;
    }
    div[data-testid="stAlert"][kind="info"] {
        background-color: #e8f1fb;
    }
    div[data-testid="stAlert"][kind="warning"] {
        background-color: #fff4db;
    }
    div[data-testid="stAlert"][kind="error"] {
        background-color: #fde7e9;
    }
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="input"] input,
    div[data-testid="stCodeBlock"] pre,
    div[data-testid="stDataFrame"] {
        color: #1f2933;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_processed_data():
    # Los ficheros procesados se leen una sola vez y se cachean para evitar recargas innecesarias.
    fields_path = os.path.join(DATA_DIR, 'fields.csv')
    matches_path = os.path.join(DATA_DIR, 'matches.csv')
    if os.path.exists(fields_path) and os.path.exists(matches_path):
        df_fields = pd.read_csv(fields_path)
        df_matches = pd.read_csv(matches_path)
        
        # Convertimos las coordenadas originales a WGS84 para poder pintarlas en el mapa.
        transformer = Transformer.from_crs("epsg:25830", "epsg:4326")
        
        # Copiamos arreglos de numpy para vectorizar operaciones
        x_arr = df_fields['x'].values.copy()
        y_arr = df_fields['y'].values.copy()
        
        # Normalizamos valores mal escalados
        # Si x > 1000000, dividimos por 10 iterativamente
        mask_x_large = x_arr > 1000000
        while mask_x_large.any():
            x_arr[mask_x_large] /= 10.0
            mask_x_large = x_arr > 1000000
            
        mask_x_small = x_arr < 100000
        while mask_x_small.any():
            x_arr[mask_x_small] *= 10.0
            mask_x_small = x_arr < 100000
            
        mask_y_large = y_arr > 10000000
        while mask_y_large.any():
            y_arr[mask_y_large] /= 10.0
            mask_y_large = y_arr > 10000000
            
        mask_y_small = y_arr < 1000000
        while mask_y_small.any():
            y_arr[mask_y_small] *= 10.0
            mask_y_small = y_arr < 1000000
            
        lats, lons = transformer.transform(x_arr, y_arr)
        df_fields['lat'] = lats
        df_fields['lon'] = lons
        
        # Mapeamos deportes disponibles para cada centro (lista limpia)
        sports_map = df_matches.groupby('campoId')['deporte'].unique().apply(list).to_dict()
        df_fields['deportes_disponibles'] = df_fields['id'].map(sports_map)
        # Aseguramos que sea siempre una lista para evitar errores 
        df_fields['deportes_disponibles'] = df_fields['deportes_disponibles'].apply(lambda d: d if isinstance(d, list) else [])
        
        return df_fields, df_matches
    return None, None

@st.cache_resource
def load_kg_for_queries():
    # El grafo RDF también se cachea para reutilizarlo entre ejecuciones.
    g = Graph()
    if os.path.exists(KG_PATH):
        g.parse(KG_PATH, format='nt')
        return g
    return None

def main():
    st.title("Explorador de Knowledge Graph: Competiciones deportivas municipales de deportes colectivos")
    
    df_fields, df_matches = load_processed_data()
    
    if df_fields is None:
        # Si no existen los CSV procesados, la app no puede arrancar con datos.
        st.error("Datos pre-procesados no encontrados. Ejecuta `python src/preprocess.py` primero.")
        return

    st.sidebar.title("Navegación")
    menu = st.sidebar.radio("Ir a:", ["Mapa de campos", "Consultas Sparql"])

    if menu == "Mapa de campos":
        st.header("Localización de Campos Deportivos")
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros")
        search_term = st.sidebar.text_input("Buscar por nombre", placeholder="Introduce el nombre de un campo.")
        
        #valores de distritos y deportes disponibles 
        distritos = sorted(df_fields['distrito'].dropna().unique())
        selected_distrito = st.sidebar.multiselect("Filtrar por Distrito", options=distritos)
        
        todos_deportes = sorted(df_matches['deporte'].dropna().unique())
        selected_deporte = st.sidebar.multiselect("Filtrar por Deporte", options=todos_deportes)
        
        df_display = df_fields.copy()
        # Aplicamos los filtros de distrito,deporte y nombre
        if search_term: df_display = df_display[df_display['nombre'].str.contains(search_term, case=False)]
        if selected_distrito: df_display = df_display[df_display['distrito'].isin(selected_distrito)]
        if selected_deporte:
            #  el centro debe tener al menos uno de los deportes seleccionados
            df_display = df_display[df_display['deportes_disponibles'].apply(lambda x: any(d in selected_deporte for d in x))]

        # Métricas de los datos filtrados
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Centros", len(df_display))
        m2.metric("Distritos Representados", len(df_display['distrito'].unique()))
        m3.metric("Partidos Registrados", len(df_matches[df_matches['campoId'].isin(df_display['id'])]))

        col1, col2 = st.columns([2, 1])
        # Mostramos el mapa y la ficha detallada del centro pulsado.
        with col1: # coordenadas centro de madrid
            m = folium.Map(location=[40.4168, -3.7038], zoom_start=12, tiles='CartoDB positron')
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in df_display.iterrows():
                folium.Marker([row['lat'], row['lon']], popup=row['nombre'], tooltip=row['nombre'], icon=folium.Icon(color='cadetblue', icon='info-sign')).add_to(marker_cluster)
            output = st_folium(m, width="100%", height=600, key="main_map")
        
        with col2:
            st.markdown("### Detalles del Campo")
            # Detectamos qué marcador se ha pulsado para mostrar su ficha detallada.
            last_clicked = output.get('last_object_clicked')
            field_info = None
            if last_clicked:
                match = df_display[np.isclose(df_display['lat'], last_clicked['lat'], atol=0.0001) & np.isclose(df_display['lon'], last_clicked['lng'], atol=0.0001)]
                if not match.empty: field_info = match.iloc[0]

            # Informacion del campo pulsado
            if field_info is not None:
                st.success(f"Centro: {field_info['nombre']}")
                matches = df_matches[df_matches['campoId'] == field_info['id']]
                # Si hay deportes seleccionados en el filtro, resaltamos o filtramos también la tabla de partidos
                if selected_deporte:
                    matches = matches[matches['deporte'].isin(selected_deporte)]
                    st.warning(f"Mostrando solo partidos de: {', '.join(selected_deporte)}")

                # Partidos
                with st.expander(f"Partidos registrados ({len(matches)})", expanded=True):
                    if not matches.empty:
                        st.dataframe(matches[['fecha', 'local', 'visitante', 'resultado', 'deporte']], use_container_width=True, hide_index=True)
                    else:
                        st.write("No hay partidos que coincidan con el filtro.")

                # Informacion del distrito 
                distrito = field_info['distrito'] if pd.notna(field_info['distrito']) else "Distrito no especificado"
                with st.expander(f"Información de {distrito} (Wikidata)", expanded=False):
                    # Poblacion
                    if pd.notna(field_info.get('poblacion')):
                        st.metric("Población del Distrito", f"{int(field_info['poblacion']):,}")
                    # Imagen
                    if pd.notna(field_info.get('distrito_imagen')):
                        st.image(field_info['distrito_imagen'], use_container_width=True)
                    # Wikidata
                    if pd.notna(field_info.get('wdDistrito')):
                        st.markdown(f"[Enlace a Wikidata]({field_info['wdDistrito']})")

                # DEPORTES
                if not matches.empty:
                    unique_sports = matches.drop_duplicates(subset=['deporte'])
                    with st.expander("Deportes", expanded=False):
                        for _, sport_row in unique_sports.iterrows():
                            st.markdown(f"**{sport_row['deporte'].capitalize()}**")
                            desc = sport_row.get('deporte_descripcion')
                            if pd.notna(desc) and desc != "": st.info(desc)
                            else: st.write("Sin descripción en Wikidata -__- .")
                            if pd.notna(sport_row.get('deporte_imagen')): st.image(sport_row['deporte_imagen'], width=200)
                            st.markdown("---")
            else:
                st.info("Selecciona un campo en el mapa.")

        st.markdown("---")
        st.subheader("Distribución de campos por Distrito")
        st.bar_chart(df_display['distrito'].value_counts(), color="#3498db")

    elif menu == "Consultas Inteligentes":
        # Generador de Consultas SPARQL
        st.header("Generador de Consultas SPARQL")
        q_col1, q_col2 = st.columns([1, 2])
        with q_col1:
            # modelo para correr en ollama, necesita estar descargado previamente 
            model = st.selectbox("Modelo local (Ollama)", [
                "phi3:mini", 
                "qwen2.5:3b", 
                "qwen2.5:1.5b",
                "llama3:8b", 
                "mistral"
            ])
            st.subheader("Biblioteca de Consultas")

            libreria = {
                "Seleccionar...": "",
                "Todos los equipos": "\
                    PREFIX ns: <https://example.org/partidos/>\
                    \nSELECT DISTINCT ?nombre WHERE { ?e ns:nombreEquipo ?nombre }",
                "Campos en Chamartín": "\
                    PREFIX ns: <https://example.org/partidos/>\
                    \nSELECT ?nombre WHERE {\n  ?c a ns:Campo .\
                    \n  ?c ns:nombreCampo ?nombre .\
                    \n  ?c ns:localizadoEn ?d .\
                    \n  ?d ns:nombreDistrito \"Chamartín\" .\n}",
                "Equipos en Arganzuela": "\
                    PREFIX ns: <https://example.org/partidos/>\
                    \nSELECT DISTINCT ?nombreEquipo WHERE {\n  ?p ns:tieneEquipoLocal ?e .\
                    \n  ?e ns:nombreEquipo ?nombreEquipo .\
                    \n  ?p ns:ocurreEn ?c .\
                    \n  ?c ns:localizadoEn ?d .\
                    \n  ?d ns:nombreDistrito \"Arganzuela\" .\n}",
                "Conteo de partidos por deporte": "\
                    PREFIX ns: <https://example.org/partidos/>\
                    \nSELECT ?deporte (COUNT(?p) as ?total) WHERE {\n  ?comp ns:tipoDe ?d .\n  ?d ns:nombreDeporte ?deporte .\n  ?comp ns:tieneGrupo/ns:tieneJornada/ns:tienePartido ?p .\n} GROUP BY ?deporte"
            }
            query_seleccionada = st.selectbox("Cargar consulta predefinida:", options=list(libreria.keys()))
            
            st.markdown("---")
            st.subheader("Editor Manual")
            # Si se selecciona una de la librería, se precarga en el area
            query_inicial = libreria[query_seleccionada] if query_seleccionada != "Seleccionar..." else ""
            manual_query = st.text_area("Escribe o edita tu SPARQL", value=query_inicial, height=200)
            
            if st.button("Ejecutar Manual"):
                if manual_query:
                    # Ejecutamos la consulta manual directamente contra el grafo cargado.
                    g = load_kg_for_queries()
                    if g:
                        try:
                            res = g.query(manual_query)
                            data = [{str(var): str(val) for var, val in row.asdict().items()} for row in res]
                            st.dataframe(pd.DataFrame(data), use_container_width=True)
                        except Exception as e: st.error(f"Error: {e}")

        st.markdown("---")
        
        with q_col2:
            st.subheader("Generador por IA")
            question = st.text_area("Escribe tu consulta para la IA", height=100, placeholder="Ej: ¿Cuántos equipos juegan en Retiro?")
            
            if st.button("Generar"):
                if question:
                    col_gen, col_man = st.columns(2)
                    
                    # Generación IA
                    with col_gen:
                        st.info("IA generada")
                        try:
                            # La IA propone la consulta y luego la validamos contra el mismo grafo.
                            gen_query = generate_sparql(question, model=model)
                            st.code(gen_query, language="sparql")
                            g = load_kg_for_queries()
                            res_gen = g.query(gen_query)
                            data_gen = [{str(var): str(val) for var, val in row.asdict().items()} for row in res_gen]
                            st.success(f"Resultados IA: {len(data_gen)}")
                            st.dataframe(pd.DataFrame(data_gen), height=200)
                        except Exception as e: st.error(f"Error IA: {e}")
                    
                    # Ejecución Manual (la que esté en la caja de la izquierda)
                    with col_man:
                        st.info("Manual (Referencia)")
                        if manual_query:
                            st.code(manual_query, language="sparql")
                            try:
                                res_man = g.query(manual_query)
                                data_man = [{str(var): str(val) for var, val in row.asdict().items()} for row in res_man]
                                st.success(f"Resultados Manual: {len(data_man)}")
                                st.dataframe(pd.DataFrame(data_man), height=200)
                            except Exception as e: st.error(f"Error Manual: {e}")
                        else:
                            st.warning("Escribe una consulta en el editor de la izquierda para comparar.")
                else:
                    st.warning("Introduce una pregunta.")

if __name__ == "__main__":
    main()
