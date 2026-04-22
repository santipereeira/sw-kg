import os
from rdflib import Graph
import pandas as pd

def run_query(graph, query_path, results_dir):
    with open(query_path, 'r') as f:
        query = f.read()
    
    results = graph.query(query)
    
    data = [{str(var): str(val) for var, val in row.asdict().items()} for row in results]
    
    df = pd.DataFrame(data)
    output_name = os.path.basename(query_path).replace('.rq', '.csv')
    output_path = os.path.join(results_dir, output_name)
    os.makedirs(results_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")
    return df

def main():
    # Cargamos el grafo local y lanzamos todas las consultas definidas en la lista.
    g = Graph()
    src_dir = os.path.dirname(os.path.abspath(__file__))
    tarea_6_dir = os.path.abspath(os.path.join(src_dir, '..'))
    repo_dir = os.path.abspath(os.path.join(tarea_6_dir, '..'))
    kg_path = os.path.join(repo_dir, 'TAREA_4', 'kg', 'output.nt')
    queries_dir = os.path.join(tarea_6_dir, 'queries')
    results_dir = os.path.join(tarea_6_dir, 'results', 'query_results')

    
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
        os.path.join(queries_dir, 'local_query_1.rq'),
        os.path.join(queries_dir, 'local_query_2.rq'),
        os.path.join(queries_dir, 'federated_query_1.rq'),
        os.path.join(queries_dir, 'federated_query_2.rq')
    ]

    for q in queries:
        try:
            run_query(g, q, results_dir)
        except Exception as e:
            # Si una consulta falla, seguimos con las siguientes.
            print(f"Error executing {q}: {e}")

if __name__ == "__main__":
    main()
