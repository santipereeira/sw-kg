from pyshacl import validate
import rdflib
import os

# 1. Definir las rutas de los archivos
data_file = "../kg/output.ttl" # Ajusta la ruta a donde tengas tu output
shapes_file = "../shapes/shapes_from_ontology_or_mapping.ttl"
report_file = "report_model_shapes.ttl"

print("Cargando grafos...")
# 2. Cargar los datos y las reglas
data_graph = rdflib.Graph().parse(data_file, format="turtle")
shapes_graph = rdflib.Graph().parse(shapes_file, format="turtle")

print("Ejecutando validación con PySHACL...")
# 3. Ejecutar la validación
conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shapes_graph,
    data_graph_format="turtle",
    shacl_graph_format="turtle",
    inference="rdfs",
    debug=False,
    serialize_report_graph=False
)

# 4. Mostrar resultados por pantalla
print("\n--- RESULTADOS DE LA VALIDACIÓN ---")
print(f"¿El grafo es conforme?: {conforms}")
print("-----------------------------------")
print(results_text)

# 5. Guardar el informe en un archivo TTL
# Esto sacará la ruta de la carpeta donde está el script
ruta_actual = os.path.dirname(os.path.abspath(__file__))
nombre_informe = os.path.join(ruta_actual, "report_model_shapes.ttl")

# Guardamos el grafo de resultados
results_graph.serialize(destination=nombre_informe, format="turtle")

print(f"--- ¡ÉXITO TOTAL! ---")
print(f"El archivo se ha guardado en: {nombre_informe}")
