"""
Utilidades SPARQL para consultar el Knowledge Graph local (rdflib).
Todas las queries usan los prefijos de gamere y filtros de bounding box
para calcular proximidad sin necesidad de GeoSPARQL.
"""

from rdflib import Graph, Namespace
import streamlit as st
import os

GAMERE = Namespace("http://example.org/def/gamere#")

PREFIXES = """
    PREFIX gamere: <http://example.org/def/gamere#>
    PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs:   <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl:    <http://www.w3.org/2002/07/owl#>
    PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
"""

# Mapeado de clases a etiquetas legibles y emojis
TIPO_META = {
    "Praia":                  {"label": "Praia",              "emoji": "🏖️",  "color": "#0077b6"},
    "CastilloEmprazamento":   {"label": "Castelo / Pazo",     "emoji": "🏰",  "color": "#6d4c41"},
    "FervenzaAuga":           {"label": "Fervenza / Río",     "emoji": "💧",  "color": "#0096c7"},
    "IgrexaRelixiosa":        {"label": "Igrexa / Ermida",    "emoji": "⛪",  "color": "#7b2d8b"},
    "ConstrucionTradicional": {"label": "Construción Trad.",  "emoji": "🏚️",  "color": "#795548"},
    "MonasterioCovento":      {"label": "Mosteiro",           "emoji": "🛕",  "color": "#4a148c"},
    "EspazoNatural":          {"label": "Espazo Natural",     "emoji": "🌿",  "color": "#2e7d32"},
    "OutrosPDI":              {"label": "Outros",             "emoji": "📍",  "color": "#546e7a"},
    "Ponte":                  {"label": "Ponte",              "emoji": "🌉",  "color": "#37474f"},
    "XacementoArqueoloxco":   {"label": "Xacemento Arq.",     "emoji": "🏛️",  "color": "#bf360c"},
}


@st.cache_resource(show_spinner="Cargando Knowledge Graph e Ontoloxía...")
def load_graph():
    """
    Carga el KG (N-Triples) y la ontología (Turtle) en el mismo grafo.
    La ontología es necesaria para que rdfs:subClassOf* funcione en las queries.
    """
    g = Graph()
    base_dir = os.getcwd()

    # Datos: Morph-KGC genera N-Triples aunque la extensión sea .ttl
    for fname, fmt in [("output.nt", "nt"), ("output.ttl", "nt")]:
        kg_path = os.path.join(base_dir, "kg", fname)
        if os.path.exists(kg_path):
            g.parse(kg_path, format=fmt)
            break
    else:
        st.error("🚨 No se encontró kg/output.nt ni kg/output.ttl")
        return g

    # Ontología: necesaria para subClassOf*
    onto_path = os.path.join(base_dir, "kg", "ontologia.ttl")
    if os.path.exists(onto_path):
        g.parse(onto_path, format="turtle")
    else:
        st.warning("⚠️ kg/ontologia.ttl no encontrada — pon una copia de tu ontología ahí.")

    return g


def get_all_pdi(graph: Graph, tipo_filter: list = None) -> list[dict]:
    """Devuelve todos los PDI del grafo con sus datos básicos."""
    tipo_clause = ""
    if tipo_filter:
        tipos_sparql = " ".join([f"gamere:{t}" for t in tipo_filter])
        tipo_clause = f"VALUES ?clase {{ {tipos_sparql} }}"

    q = PREFIXES + f"""
    SELECT DISTINCT ?uri ?nombre ?tipo ?lat ?lon ?concello ?url WHERE {{
        {tipo_clause}
        ?uri rdf:type ?clase .
        ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
        BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
        OPTIONAL {{ ?uri gamere:nome ?nombre }}
        OPTIONAL {{ ?uri gamere:nomePraia ?nombre }}
        OPTIONAL {{
            ?uri gamere:estaEn ?ub .
            ?ub gamere:coordenadasX ?lat ;
                gamere:coordenadasY ?lon .
        }}
        OPTIONAL {{
            ?uri gamere:situadaEn ?conc .
            ?conc gamere:nameConcello ?concello .
        }}
        OPTIONAL {{ ?uri gamere:url ?url }}
        OPTIONAL {{ ?uri gamere:urlPDI ?url }}
        FILTER(BOUND(?lat) && BOUND(?lon))
    }}
    ORDER BY ?nombre
    LIMIT 2000
    """
    results = []
    for row in graph.query(q):
        tipo_key = str(row.tipo) if row.tipo else "OutrosPDI"
        meta = TIPO_META.get(tipo_key, {"label": tipo_key, "emoji": "📍", "color": "#546e7a"})
        results.append({
            "uri":      str(row.uri),
            "nombre":   str(row.nombre) if row.nombre else "Sen nome",
            "tipo":     tipo_key,
            "label":    meta["label"],
            "emoji":    meta["emoji"],
            "color":    meta["color"],
            "lat":      float(row.lat),
            "lon":      float(row.lon),
            "concello": str(row.concello) if row.concello else "",
            "url":      str(row.url) if row.url else "",
        })
    return results


def get_nearby_pdi(graph: Graph, lat: float, lon: float, radius_km: float = 10.0) -> list[dict]:
    """
    Devuelve PDIs dentro de un bounding box centrado en (lat, lon).
    1 grado lat ≈ 111 km | 1 grado lon ≈ 111 * cos(lat) km
    """
    import math
    delta_lat = radius_km / 111.0
    delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))

    lat_min, lat_max = lat - delta_lat, lat + delta_lat
    lon_min, lon_max = lon - delta_lon, lon + delta_lon

    q = PREFIXES + f"""
    SELECT DISTINCT ?uri ?nombre ?tipo ?lat ?lon ?concello WHERE {{
        ?uri rdf:type ?clase .
        ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
        BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
        OPTIONAL {{ ?uri gamere:nome ?nombre }}
        OPTIONAL {{ ?uri gamere:nomePraia ?nombre }}
        ?uri gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
        OPTIONAL {{
            ?uri gamere:situadaEn ?conc .
            ?conc gamere:nameConcello ?concello .
        }}
        FILTER(?lat >= {lat_min} && ?lat <= {lat_max})
        FILTER(?lon >= {lon_min} && ?lon <= {lon_max})
    }}
    ORDER BY ?nombre
    """
    results = []
    for row in graph.query(q):
        tipo_key = str(row.tipo) if row.tipo else "OutrosPDI"
        meta = TIPO_META.get(tipo_key, {"label": tipo_key, "emoji": "📍", "color": "#546e7a"})
        dist = haversine(lat, lon, float(row.lat), float(row.lon))
        results.append({
            "uri":      str(row.uri),
            "nombre":   str(row.nombre) if row.nombre else "Sen nome",
            "tipo":     tipo_key,
            "label":    meta["label"],
            "emoji":    meta["emoji"],
            "color":    meta["color"],
            "lat":      float(row.lat),
            "lon":      float(row.lon),
            "concello": str(row.concello) if row.concello else "",
            "distancia_km": round(dist, 2),
        })
    results.sort(key=lambda x: x["distancia_km"])
    return results


def get_stats(graph: Graph) -> dict:
    """Estadísticas generales del KG."""
    q = PREFIXES + """
    SELECT ?tipo (COUNT(?uri) AS ?total) WHERE {
        ?uri rdf:type ?clase .
        ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
        BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
    }
    GROUP BY ?tipo
    ORDER BY DESC(?total)
    """
    stats = {}
    for row in graph.query(q):
        tipo_key = str(row.tipo)
        meta = TIPO_META.get(tipo_key, {"label": tipo_key, "emoji": "📍"})
        stats[tipo_key] = {
            "label": meta["label"],
            "emoji": meta["emoji"],
            "total": int(row.total),
        }
    return stats


def run_custom_query(graph: Graph, query: str) -> tuple[list, list]:
    """Ejecuta una query SPARQL libre y devuelve (columnas, filas)."""
    full_query = PREFIXES + query
    results = graph.query(full_query)
    cols = [str(v) for v in results.vars]
    rows = []
    for row in results:
        rows.append([str(v) if v is not None else "" for v in row])
    return cols, rows


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distancia en km entre dos puntos geográficos."""
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))
