import streamlit as st
from dotenv import load_dotenv # Añade esto
import os # Añade esto
load_dotenv()

st.set_page_config(
    page_title="KG de Galicia",
    layout="wide",
    initial_sidebar_state="expanded"
)

p_mapa = st.Page("pages/mapa.py", title="Mapa & Buscador", default=True)
p_chat = st.Page("pages/chat.py", title="Asistente IA")
p_sparql = st.Page("pages/sparql.py", title="Explorador SPARQL")
p_wiki = st.Page("pages/wikidata.py", title="WikiData")

pg = st.navigation({"Opcións de búsqueda": [p_mapa, p_chat, p_sparql, p_wiki]})

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
    }
    .stApp {
        background-color: #f5f0e8;
    }
    .main-header {
        background: linear-gradient(135deg, #2d4a3e 0%, #1a2e26 100%);
        color: #f5f0e8;
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 {
        font-size: 2.2rem;
        margin: 0;
        color: #d4af7a;
        letter-spacing: 1px;
    }
    .main-header p {
        margin: 0.3rem 0 0;
        color: #a8c5b5;
        font-size: 1rem;
    }
    .pdi-card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        border-left: 4px solid #2d4a3e;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .pdi-card h4 {
        margin: 0 0 0.2rem;
        color: #2d4a3e;
        font-family: 'Playfair Display', serif;
        font-size: 1rem;
    }
    .pdi-card p {
        margin: 0;
        color: #666;
        font-size: 0.85rem;
    }
    .tipo-badge {
        display: inline-block;
        background: #2d4a3e;
        color: #d4af7a;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .chat-msg-user {
        background: #2d4a3e;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 0.8rem 1.1rem;
        margin: 0.5rem 0;
        margin-left: 20%;
        font-size: 0.95rem;
    }
    .chat-msg-bot {
        background: white;
        color: #1a2e26;
        border-radius: 18px 18px 18px 4px;
        padding: 0.8rem 1.1rem;
        margin: 0.5rem 0;
        margin-right: 20%;
        font-size: 0.95rem;
        border: 1px solid #ddd;
    }
    .stButton > button {
        background: #2d4a3e;
        color: #d4af7a;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
    .stButton > button:hover {
        background: #1a2e26;
        color: #d4af7a;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Playfair Display', serif;
        color: #2d4a3e;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>Knowledge Graph de Galicia</h1>
    <p>Patrimonio e espazos naturais integrados e dispoñibles para consulta</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### Sobre o proxecto:")
st.sidebar.markdown(
    "Knowledge Graph de Galicia construído con RDF/OWL, mapeado con YARRRML + Morph-KGC "
    "e validado con SHACL."
    "\nDatos extraídos de fontes abertas como Turismo de Galicia, OpenStreetMap e WikiData."
    "\n\nProxecto asociado ao Grao en Intelixencia Artificial da Universidade de Santiago de Compostela, "
    "asignatura de Web Semántica e Grafos de Coñecemento (2025-2026)."
)

# 6. Ejecutar la página correspondiente
pg.run()
