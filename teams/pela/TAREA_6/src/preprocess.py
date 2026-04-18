import os
import pandas as pd
from rdflib import Graph
import requests
import time

def get_wikidata_info(wd_uris, query_template):
    url = 'https://query.wikidata.org/sparql'
    results_map = {}
    uris_list = list(set([u for u in wd_uris if u]))
    if not uris_list: return results_map
    
    batch_size = 10
    headers = {'User-Agent': 'SportsKGExplorer/1.0 (mateo@example.org)'}
    
    for i in range(0, len(uris_list), batch_size):
        batch = uris_list[i:i+batch_size]
        values = " ".join([f"<{uri}>" for uri in batch])
        query = query_template.replace("{{VALUES}}", values)
        
        for attempt in range(3):
            try:
                r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    for result in data['results']['bindings']:
                        item_uri = result['item']['value']
                        results_map[item_uri] = {k: v['value'] for k, v in result.items() if k != 'item'}
                    break
                else:
                    print(f"Wikidata error {r.status_code}, retrying...")
                    time.sleep(2)
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                time.sleep(2)
    return results_map

def preprocess():
    g = Graph()
    kg_path = 'kg/output.nt'
    print(f"Loading {kg_path}...")
    g.parse(kg_path, format='nt')
    print("Extracting local data...")

    # Query 1: Fields
    q_fields = "PREFIX ns: <https://example.org/partidos/> SELECT ?id ?nombre ?x ?y ?distrito ?wdDistrito WHERE { ?id a ns:Campo . ?id ns:nombreCampo ?nombre . ?id ns:coorX ?x . ?id ns:coorY ?y . ?id ns:localizadoEn ?d . ?d ns:nombreDistrito ?distrito . OPTIONAL { ?d ns:sameAsDistrito ?wdDistrito . } }"
    df_fields = pd.DataFrame([{ 'id': str(r.id), 'nombre': str(r.nombre), 'x': float(r.x), 'y': float(r.y), 'distrito': str(r.distrito), 'wdDistrito': str(r.wdDistrito) if r.wdDistrito else None } for r in g.query(q_fields)])

    # Query 2: Matches
    print("Extracting matches...")
    q_matches = "PREFIX ns: <https://example.org/partidos/> SELECT ?partido ?campoId ?local ?visitante ?res1 ?res2 ?fecha WHERE { ?partido ns:ocurreEn ?campoId . ?partido ns:tieneEquipoLocal ?el . ?el ns:nombreEquipo ?local . ?partido ns:tieneEquipoVisitante ?ev . ?ev ns:nombreEquipo ?visitante . ?partido ns:resultado1 ?res1 . ?partido ns:resultado2 ?res2 . ?partido ns:hora ?fecha . }"
    df_matches = pd.DataFrame([{ 'partido': str(r.partido), 'campoId': str(r.campoId), 'local': str(r.local), 'visitante': str(r.visitante), 'resultado': f"{r.res1}-{r.res2}", 'fecha': str(r.fecha)[:10] } for r in g.query(q_matches)])

    # Query 3: Match to Sport
    print("Linking matches to sports...")
    q_ms = "PREFIX ns: <https://example.org/partidos/> SELECT ?partido ?nombreDeporte ?wdDeporte WHERE { ?jornada ns:tienePartido ?partido . ?grupo ns:tieneJornada ?jornada . ?competicion ns:tieneGrupo ?grupo . ?competicion ns:tipoDe ?deporte . ?deporte ns:nombreDeporte ?nombreDeporte . OPTIONAL { ?deporte ns:sameAsDeporte ?wdDeporte . } }"
    df_ms = pd.DataFrame([{ 'partido': str(r.partido), 'deporte': str(r.nombreDeporte), 'wdDeporte': str(r.wdDeporte) if r.wdDeporte else None } for r in g.query(q_ms)])
    df_matches = df_matches.merge(df_ms, on='partido', how='left')

    print("Fetching Wikidata info for districts...")
    dq = "SELECT ?item ?poblacion ?imagen WHERE { VALUES ?item { {{VALUES}} } OPTIONAL { ?item wdt:P1082 ?poblacion . } OPTIONAL { ?item wdt:P18 ?imagen . } }"
    wd_dist_info = get_wikidata_info(df_fields['wdDistrito'].unique(), dq)
    
    df_fields['poblacion'] = None
    df_fields['distrito_imagen'] = None
    for i, row in df_fields.iterrows():
        if row['wdDistrito'] in wd_dist_info:
            df_fields.at[i, 'poblacion'] = wd_dist_info[row['wdDistrito']].get('poblacion')
            df_fields.at[i, 'distrito_imagen'] = wd_dist_info[row['wdDistrito']].get('imagen')

    print("Fetching Wikidata descriptions for sports...")
    # Usamos schema:description para una descripción real, no solo el label
    sq = """
    SELECT ?item ?descripcion ?imagen WHERE { 
      VALUES ?item { {{VALUES}} } 
      OPTIONAL { 
        ?item schema:description ?descripcion . 
        FILTER(LANG(?descripcion) = 'es') 
      } 
      OPTIONAL { ?item wdt:P18 ?imagen . } 
    }
    """
    wd_sport_info = get_wikidata_info(df_matches['wdDeporte'].unique(), sq)
    
    df_matches['deporte_descripcion'] = None
    df_matches['deporte_imagen'] = None
    for i, row in df_matches.iterrows():
        if row['wdDeporte'] in wd_sport_info:
            df_matches.at[i, 'deporte_descripcion'] = wd_sport_info[row['wdDeporte']].get('descripcion')
            df_matches.at[i, 'deporte_imagen'] = wd_sport_info[row['wdDeporte']].get('imagen')

    os.makedirs('data/processed', exist_ok=True)
    df_fields.to_csv('data/processed/fields.csv', index=False)
    df_matches.to_csv('data/processed/matches.csv', index=False)
    print("Done.")

if __name__ == "__main__":
    preprocess()
