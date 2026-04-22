import os
from rdflib import Graph
import pandas as pd

def run_query(graph, query_path):
    # Ejecuta una consulta SPARQL leída desde disco y devuelve el resultado como DataFrame.
    print(f"Executing {query_path}...")
    with open(query_path, 'r') as f:
        query = f.read()
    
    results = graph.query(query)
    
    # Convertimos las filas devueltas por RDFlib en una estructura compatible con pandas.
    data = []
    for row in results:
        data.append({str(var): str(val) for var, val in row.asdict().items()})
    
    df = pd.DataFrame(data)
    output_name = os.path.basename(query_path).replace('.rq', '.csv')
    output_path = os.path.join('results', 'query_results', output_name)
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")
    return df

def main():
    # Cargamos el grafo local y lanzamos todas las consultas definidas en la lista.
    g = Graph()
    kg_path = os.path.join('kg', 'output.nt')
    
    if not os.path.exists(kg_path):
        # Si no existe el grafo, no tiene sentido continuar.
        print(f"Error: Knowledge Graph not found at {kg_path}")
        return

    # El archivo NT puede ser grande, por eso avisamos antes de cargarlo.
    print(f"Loading Knowledge Graph from {kg_path} (this may take a minute)...")
    g.parse(kg_path, format='nt')
    print(f"Loaded {len(g)} triples.")

    # Relación de consultas locales y federadas a ejecutar.
    queries = [
        'queries/local_query_1.rq',
        'queries/local_query_2.rq',
        'queries/federated_query_1.rq',
        'queries/federated_query_2.rq'
    ]

    for q in queries:
        try:
            run_query(g, q)
        except Exception as e:
            # Si una consulta falla, seguimos con las siguientes.
            print(f"Error executing {q}: {e}")

if __name__ == "__main__":
    main()
