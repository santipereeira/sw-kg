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

def generate_sparql(question, model="llama3"):
    # Construimos un prompt con el esquema del grafo y las reglas de generación.
    prompt = f"""
Eres un experto en SPARQL. Genera una consulta para este Knowledge Graph:

{KG_SCHEMA}

Reglas:
1. Responde SOLO con el código SPARQL.
2. Usa el prefijo 'ns:' para todo lo que no sea rdfs o xsd.
3. Para nombres de distritos o equipos, usa comparaciones de texto exactas si es posible.
4. Si buscas equipos, selecciona ?nombreEquipo (ns:nombreEquipo).
5. Asume que el usuario quiere resultados específicos, no genéricos. 

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
