"""
utils/rag_engine.py
===================
Motor RAG basado en SPARQL.
Flujo:
  1. El LLM analiza la pregunta y devuelve un intent estructurado
  2. build_context() convierte ese intent en una query SPARQL real
  3. El resultado del KG se pasa como contexto al LLM para generar la respuesta

Separado de sparql_queries.py para mantener la lógica de chat aislada.
"""

import re
import json
from rdflib import Graph
from utils.sparql_queries import (
    PREFIXES, get_nearby_pdi, get_stats, run_custom_query, TIPO_META
)

# ── Mapa de intents → queries SPARQL ─────────────────────────────────────────
# Cada intent produce una query parametrizada que se ejecuta contra el KG local.

INTENT_QUERIES = {

    "contar_por_provincia": """
SELECT ?provincia (COUNT(?pdi) AS ?total) WHERE {{
    ?pdi rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    {tipo_filter}
    ?pdi gamere:situadaEn ?conc .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:nameProvincia ?provincia .
    {provincia_filter}
}}
GROUP BY ?provincia
ORDER BY DESC(?total)
""",

    "contar_por_concello": """
SELECT ?concello ?provincia (COUNT(?pdi) AS ?total) WHERE {{
    ?pdi rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    {tipo_filter}
    ?pdi gamere:situadaEn ?conc .
    ?conc gamere:nameConcello ?concello .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:nameProvincia ?provincia .
    {provincia_filter}
}}
GROUP BY ?concello ?provincia
ORDER BY DESC(?total)
LIMIT 20
""",

    "listar_tipo": """
SELECT ?nombre ?concello ?provincia ?lat ?lon WHERE {{
    ?pdi rdf:type {clase} .
    OPTIONAL {{ ?pdi gamere:nome ?nombre }}
    OPTIONAL {{ ?pdi gamere:nomePraia ?nombre }}
    OPTIONAL {{
        ?pdi gamere:situadaEn ?conc .
        ?conc gamere:nameConcello ?concello .
        ?conc gamere:perteneceA ?prov .
        ?prov gamere:nameProvincia ?provincia .
    }}
    OPTIONAL {{
        ?pdi gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
    }}
    {provincia_filter}
}}
ORDER BY ?provincia ?concello ?nombre
LIMIT 30
""",

    "playas_bandera_azul": """
SELECT ?nombre ?concello ?provincia ?tipoArena ?entorno ?lat ?lon WHERE {{
    ?pdi rdf:type gamere:Praia .
    ?pdi gamere:banderaAzul true .
    ?pdi gamere:nomePraia ?nombre .
    OPTIONAL {{ ?pdi gamere:tipoArena ?tipoArena }}
    OPTIONAL {{ ?pdi gamere:entorno ?entorno }}
    OPTIONAL {{
        ?pdi gamere:situadaEn ?conc .
        ?conc gamere:nameConcello ?concello .
        ?conc gamere:perteneceA ?prov .
        ?prov gamere:nameProvincia ?provincia .
    }}
    OPTIONAL {{
        ?pdi gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
    }}
    {provincia_filter}
}}
ORDER BY ?provincia ?concello ?nombre
LIMIT 30
""",

    "stats_generales": """
SELECT ?etiqueta (COUNT(?pdi) AS ?total) WHERE {{
    ?pdi rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    ?clase rdfs:label ?etiqueta .
}}
GROUP BY ?etiqueta
ORDER BY DESC(?total)
""",

    "cercanos": None,  # Se maneja con get_nearby_pdi (bounding box)

    "portugal": """
SELECT ?nombre ?tipo ?concello ?lat ?lon WHERE {{
    ?pdi rdf:type ?clase .
    ?clase rdfs:subClassOf* gamere:PuntoDeInteres .
    BIND(STRAFTER(STR(?clase), STR(gamere:)) AS ?tipo)
    OPTIONAL {{ ?pdi gamere:nome ?nombre }}
    OPTIONAL {{ ?pdi gamere:nomePraia ?nombre }}
    ?pdi gamere:situadaEn ?conc .
    ?conc gamere:nameConcello ?concello .
    ?conc gamere:perteneceA ?prov .
    ?prov gamere:perteneceA ?pais .
    ?pais gamere:namePais "Portugal" .
    OPTIONAL {{
        ?pdi gamere:estaEn ?ub .
        ?ub gamere:coordenadasX ?lat ;
            gamere:coordenadasY ?lon .
    }}
    {tipo_filter}
}}
ORDER BY ?tipo ?nombre
LIMIT 30
""",
}

# Clases gamere válidas para validar el intent
CLASES_VALIDAS = set(TIPO_META.keys())

# Provincias gallegas para validar
PROVINCIAS_VALIDAS = {"A Coruña", "Lugo", "Ourense", "Pontevedra",
                      "Viana Do Castelo", "Braga", "Bragança", "Vila Real"}

PROVINCIA_ALIAS = {
    "a coruña": "A Coruña", "la coruña": "A Coruña", "coruña": "A Coruña",
    "lugo": "Lugo",
    "ourense": "Ourense", "orense": "Ourense",
    "pontevedra": "Pontevedra",
    "viana do castelo": "Viana Do Castelo",
}


def _canon_provincia(raw: str) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower()
    return PROVINCIA_ALIAS.get(key, raw.strip().title() if raw.strip().title() in PROVINCIAS_VALIDAS else None)


def _tipo_filter_sparql(tipos: list | None) -> str:
    """Genera la cláusula VALUES para filtrar por tipo de PDI."""
    if not tipos:
        return ""
    valid = [t for t in tipos if t in CLASES_VALIDAS]
    if not valid:
        return ""
    valores = " ".join(f"gamere:{t}" for t in valid)
    return f"VALUES ?clase {{ {valores} }}"


def _provincia_filter_sparql(provincia: str | None) -> str:
    """Genera el FILTER de provincia si se especifica."""
    if not provincia:
        return ""
    return f'FILTER(?provincia = "{provincia}")'


def build_context(graph: Graph, intent: dict) -> tuple[str, str]:
    """
    Ejecuta la query SPARQL adecuada según el intent y devuelve:
    - context_text: texto para el LLM
    - query_used:   query ejecutada (para mostrar en el expander)
    """
    tipo        = intent.get("tipo", "general")
    tipos_pdi   = intent.get("tipos_pdi")        # lista de clases o None
    lat         = intent.get("lat")
    lon         = intent.get("lon")
    radio_km    = intent.get("radio_km") or 15
    provincia   = _canon_provincia(intent.get("provincia", ""))
    bandera_azul = intent.get("bandera_azul", False)
    portugal    = intent.get("portugal", False)

    tipo_filter     = _tipo_filter_sparql(tipos_pdi)
    provincia_filter = _provincia_filter_sparql(provincia)

    lines = []
    query_used = ""

    # ── Cercanos ──────────────────────────────────────────────────────────────
    if tipo == "cercanos" and lat and lon:
        cercanos = get_nearby_pdi(graph, lat, lon, radio_km)[:20]
        if tipos_pdi:
            cercanos = [c for c in cercanos if c["tipo"] in tipos_pdi]
        if cercanos:
            lines.append(f"Sitios nun radio de {radio_km} km:")
            for p in cercanos:
                partes = [f"{p['emoji']} {p['nombre']} ({p['label']})"]
                if p["concello"]:
                    partes.append(p["concello"])
                partes.append(f"{p['distancia_km']} km")
                lines.append("  - " + " — ".join(partes))
        else:
            lines.append(f"Non se atoparon sitios nun radio de {radio_km} km.")
        query_used = f"# Bounding box ±{radio_km} km desde ({lat}, {lon})"

    # ── Playas bandera azul ───────────────────────────────────────────────────
    elif bandera_azul or tipo == "bandera_azul":
        q = PREFIXES + INTENT_QUERIES["playas_bandera_azul"].format(
            provincia_filter=provincia_filter
        )
        query_used = q
        cols, rows = run_custom_query(graph, INTENT_QUERIES["playas_bandera_azul"].format(
            provincia_filter=provincia_filter
        ))
        if rows:
            ctx_prov = f" en {provincia}" if provincia else ""
            lines.append(f"Praias con Bandeira Azul{ctx_prov} ({len(rows)} resultados):")
            for r in rows:
                rd = dict(zip(cols, r))
                partes = [f"🏖️ {rd.get('nombre','?')}"]
                if rd.get("concello"): partes.append(rd["concello"])
                if rd.get("tipoArena"): partes.append(rd["tipoArena"])
                lines.append("  - " + " — ".join(partes))
        else:
            lines.append("Non se atoparon praias con Bandeira Azul.")

    # ── Portugal ──────────────────────────────────────────────────────────────
    elif portugal or tipo == "portugal":
        q_body = INTENT_QUERIES["portugal"].format(
            tipo_filter=tipo_filter if tipos_pdi else ""
        )
        cols, rows = run_custom_query(graph, q_body)
        query_used = q_body
        if rows:
            lines.append(f"Elementos en Portugal ({len(rows)} resultados):")
            for r in rows:
                rd = dict(zip(cols, r))
                lines.append(f"  - {rd.get('nombre','?')} ({rd.get('tipo','')}) — {rd.get('concello','')}")
        else:
            lines.append("Non se atoparon elementos en Portugal no KG.")

    # ── Contar por provincia ──────────────────────────────────────────────────
    elif tipo in ("contar", "count") and not tipos_pdi and not provincia:
        q_body = INTENT_QUERIES["contar_por_provincia"].format(
            tipo_filter="", provincia_filter=""
        )
        cols, rows = run_custom_query(graph, q_body)
        query_used = q_body
        if rows:
            total = sum(int(r[1]) for r in rows)
            lines.append(f"Total PDIs no KG: {total}")
            for r in rows:
                rd = dict(zip(cols, r))
                lines.append(f"  - {rd['provincia']}: {rd['total']}")
        else:
            lines.append("Non se atoparon datos.")

    # ── Contar tipo en provincia ──────────────────────────────────────────────
    elif tipo in ("contar", "count", "listar"):
        q_body = INTENT_QUERIES["contar_por_provincia"].format(
            tipo_filter=tipo_filter,
            provincia_filter=provincia_filter
        )
        cols, rows = run_custom_query(graph, q_body)
        query_used = q_body

        if rows:
            tipo_label = TIPO_META.get(tipos_pdi[0], {}).get("label", "PDIs") if tipos_pdi else "PDIs"
            ctx_prov = f" en {provincia}" if provincia else " en Galicia"
            total = sum(int(r[1]) for r in rows)
            lines.append(f"Hai {total} {tipo_label}{ctx_prov}:")
            for r in rows:
                rd = dict(zip(cols, r))
                lines.append(f"  - {rd['provincia']}: {rd['total']}")
        else:
            lines.append("Non se atoparon resultados.")

        # Si además quieren ver la lista, añadirla
        if tipo == "listar" and tipos_pdi:
            clase = f"gamere:{tipos_pdi[0]}"
            q2 = INTENT_QUERIES["listar_tipo"].format(
                clase=clase,
                provincia_filter=provincia_filter
            )
            cols2, rows2 = run_custom_query(graph, q2)
            if rows2:
                lines.append("")
                lines.append("Exemplos:")
                for r in rows2[:15]:
                    rd = dict(zip(cols2, r))
                    partes = [f"  - {rd.get('nombre','?')}"]
                    if rd.get("concello"): partes.append(rd["concello"])
                    if rd.get("provincia"): partes.append(rd["provincia"])
                    lines.append(" — ".join(partes))

    # ── Stats generales ───────────────────────────────────────────────────────
    else:
        q_body = INTENT_QUERIES["stats_generales"]
        cols, rows = run_custom_query(graph, q_body)
        query_used = q_body
        if rows:
            total = sum(int(r[1]) for r in rows)
            lines.append(f"O KG ten {total} puntos de interese en Galicia e norte de Portugal:")
            for r in rows:
                rd = dict(zip(cols, r))
                lines.append(f"  - {rd['etiqueta']}: {rd['total']}")
        else:
            stats = get_stats(graph)
            total = sum(v["total"] for v in stats.values())
            lines.append(f"O KG ten {total} puntos de interese:")
            for t, info in stats.items():
                lines.append(f"  - {info['emoji']} {info['label']}: {info['total']}")

    return "\n".join(lines), query_used


# ── Prompt de detección de intent ─────────────────────────────────────────────

INTENT_SYSTEM = """Eres un analizador de intents para un chatbot turístico de Galicia.
Debes responder SOLO con un JSON válido, sin texto adicional, sin markdown, sin explicaciones.

Campos del JSON:
- "tipo": "cercanos" | "contar" | "listar" | "bandera_azul" | "portugal" | "general"
- "lat": float o null — latitud aproximada si se menciona un lugar concreto de Galicia
- "lon": float o null — longitud aproximada
- "radio_km": int — radio en km (default 15)
- "nombre_lugar": string o null
- "provincia": string o null — una de: "A Coruña", "Lugo", "Ourense", "Pontevedra"
- "tipos_pdi": lista o null — clases gamere: Praia, CastilloEmprazamento, FervenzaAuga,
  IgrexaRelixiosa, ConstrucionTradicional, MonasterioCovento, EspazoNatural,
  OutrosPDI, Ponte, XacementoArqueoloxco
- "bandera_azul": boolean — true si pregunta específicamente por playas bandera azul
- "portugal": boolean — true si pregunta por elementos en Portugal

Reglas:
- Si pregunta "¿cuántas X hay en Y provincia?" → tipo=contar, tipos_pdi=[X], provincia=Y
- Si pregunta "¿qué hay cerca de Z?" → tipo=cercanos, lat/lon de Z
- Si pregunta por playas bandera azul → bandera_azul=true
- Si pregunta por elementos en Portugal → portugal=true
- Coordenadas aproximadas de referencia: Santiago=42.88/-8.54, Vigo=42.23/-8.72,
  Coruña=43.37/-8.40, Lugo=43.01/-7.56, Ourense=42.34/-7.86, Pontevedra=42.43/-8.64,
  Carnota=42.87/-9.10, Ribadeo=43.54/-7.04

Ejemplos:
"¿Cuántas playas hay en Pontevedra?" → {"tipo":"contar","lat":null,"lon":null,"radio_km":15,"nombre_lugar":null,"provincia":"Pontevedra","tipos_pdi":["Praia"],"bandera_azul":false,"portugal":false}
"Monasterios cerca de Ourense" → {"tipo":"cercanos","lat":42.34,"lon":-7.86,"radio_km":20,"nombre_lugar":"Ourense","provincia":null,"tipos_pdi":["MonasterioCovento"],"bandera_azul":false,"portugal":false}
"Playas con bandera azul en A Coruña" → {"tipo":"bandera_azul","lat":null,"lon":null,"radio_km":15,"nombre_lugar":null,"provincia":"A Coruña","tipos_pdi":["Praia"],"bandera_azul":true,"portugal":false}
"Resúmeme el KG" → {"tipo":"general","lat":null,"lon":null,"radio_km":15,"nombre_lugar":null,"provincia":null,"tipos_pdi":null,"bandera_azul":false,"portugal":false}
"""


def detect_intent(client, model: str, user_input: str) -> dict:
    """Llama al LLM para detectar el intent de la pregunta."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM},
                {"role": "user",   "content": user_input},
            ],
            temperature=0,
            max_tokens=300,
        )
        raw = resp.choices[0].message.content
        # Limpiar posibles bloques markdown
        raw = re.sub(r"```json|```", "", raw).strip()
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[intent] Error: {e}")
    return {"tipo": "general"}
