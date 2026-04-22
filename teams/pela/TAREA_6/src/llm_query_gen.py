import ollama

# Esquema del Knowledge Graph detallado
KG_SCHEMA = """
Prefixes:
PREFIX ns: <https://example.org/partidos/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

Clases y Propiedades Principales:
- ns:Equipo: ns:nombreEquipo (Literal)
- ns:Campo: ns:nombreCampo (Literal), ns:localizadoEn (hacia ns:Distrito)
- ns:Distrito: ns:nombreDistrito (Literal, ej: "Chamartín")
- ns:Partido: 
    - ns:tieneEquipoLocal (hacia ns:Equipo)
    - ns:tieneEquipoVisitante (hacia ns:Equipo)
    - ns:ocurreEn (hacia ns:Campo)
    - ns:resultado1, ns:resultado2 (Goles)
- ns:Deporte: ns:nombreDeporte (ej: "futsal")

Rutas de Relación (Path):
1. Equipos en un Distrito: 
   ?partido ns:tieneEquipoLocal ?equipo . 
   ?partido ns:ocurreEn ?campo . 
   ?campo ns:localizadoEn ?distrito . 
   ?distrito ns:nombreDistrito "Nombre" .
2. Deporte de una Competición:
   ?competicion ns:tipoDe ?deporte . ?deporte ns:nombreDeporte "futsal" .
3. Jerarquía de Partidos:
   ?competicion ns:tieneGrupo ?grupo . ?grupo ns:tieneJornada ?jornada . ?jornada ns:tienePartido ?partido .
"""

def generate_sparql(question, model="qwen2.5:1.5b"):
    # Construimos un prompt con el esquema del grafo y las reglas de generación.
    prompt = f"""
Eres un experto en SPARQL. Genera una consulta válida para este Knowledge Graph local.

{KG_SCHEMA}

Prefijos válidos:
PREFIX ns: <https://example.org/partidos/>

Solo debes usar el prefijo 'ns:' y los predicados definidos para este KG.
No uses ningún otro prefijo externo como wd:, wdt:, schema:, rdf:, owl:, o cualquier otro.

Propiedades disponibles:
- ?partido ns:ocurreEn ?campo .
- ?campo ns:localizadoEn ?distrito .
- ?distrito ns:nombreDistrito "Retiro" .
- ?partido ns:tieneEquipoLocal ?equipo .
- ?partido ns:tieneEquipoVisitante ?equipo .
- ?partido ns:tipoDe ?deporte .
- ?deporte ns:nombreDeporte "futsal" .

Reglas:
1. Responde SOLO con la consulta SPARQL válida.
2. Incluye siempre el PREFIX ns: al principio.
3. No incluyas explicaciones ni texto adicional.
4. No inventes predicados ni prefijos fuera del esquema proporcionado.
5. Para contar, usa SELECT (COUNT(?variable) AS ?count) WHERE { ... }
6. No uses FILTER para comparar propiedades; usa tripletas directas como ?variable ns:propiedad "valor" .
7. NO uses sintaxis SQL como 'NOT IN (SELECT ...)'. Para exclusiones en SPARQL usa siempre 'FILTER NOT EXISTS { ... }' o 'MINUS { ... }'.
8. Usa distinct en tus consultas cuando sea necesario (siempre que no sea un count).

Ejemplo válido:
PREFIX ns: <https://example.org/partidos/>
SELECT ?equipo WHERE {{
  ?partido ns:tieneEquipoLocal ?equipo .
  ?partido ns:ocurreEn ?campo .
  ?campo ns:nombreDistrito "Retiro" .
}}

Ejemplo con COUNT:
PREFIX ns: <https://example.org/partidos/>
SELECT (COUNT(?partido) AS ?total)
WHERE {{
  ?partido ns:ocurreEn ?campo .
  ?campo ns:localizadoEn ?distrito .
  ?distrito ns:nombreDistrito "Chamartín" .
}}

Pregunta: {question}
"""
    print(f"Pregunta: '{question}' con modelo '{model}'...")
    response = ollama.generate(model=model, prompt=prompt)
    query = response['response'].strip()
    
    # Limpieza robusta: si el modelo devuelve un bloque Markdown, extraemos solo la consulta.
    if "```" in query:
        # Buscamos el bloque que contenga una consulta SPARQL válida.
        parts = query.split("```")
        for part in parts:
            if "SELECT" in part.upper() or "ASK" in part.upper():
                query = part.replace("sparql", "").strip()
                break
    
    return query

if __name__ == "__main__":
    # Ejemplo local para probar la generación de consultas desde consola.
    pregunta = "¿Cuántos partidos se han jugado en el distrito de Chamartín?"
    query = generate_sparql(pregunta)
    print("\n--- Consulta Generada ---\n")
    print(query)
    print("\n--------------------------\n")
