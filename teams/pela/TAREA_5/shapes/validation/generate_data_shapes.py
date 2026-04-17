import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from shexer.shaper import Shaper
from shexer.consts import NT, SHACL_TURTLE

target_classes = [
    "https://example.org/partidos/Deporte",
    "https://example.org/partidos/Competicion",
    "https://example.org/partidos/Grupo",
    "https://example.org/partidos/Jornada",
    "https://example.org/partidos/Partido",
    "https://example.org/partidos/Equipo",
    "https://example.org/partidos/Campo",
    "https://example.org/partidos/Distrito"
]

shaper = Shaper(target_classes=target_classes,
                graph_file_input="TAREA_4/kg/output.nt",
                input_format=NT,
                namespaces_dict={"ns": "https://example.org/partidos/",
                                 "xsd": "http://www.w3.org/2001/XMLSchema#"},
                instantiation_property="http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

shaper.shex_graph(output_file="TAREA_5/shapes/shapes_from_data.ttl", output_format=SHACL_TURTLE)

# Post-procesamiento para flexibilizar la validación del rdf:type
import rdflib
from rdflib.namespace import RDF
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

g = rdflib.Graph()
g.parse("TAREA_5/shapes/shapes_from_data.ttl", format="turtle")

# Buscamos todas las restricciones sobre la ruta rdf:type
for prop in g.subjects(SH.path, RDF.type):
    # 1. Transformar sh:in (lista) en sh:hasValue (valor individual)
    in_list = g.value(prop, SH["in"])
    if in_list:
        coll = rdflib.collection.Collection(g, in_list)
        if len(coll) > 0:
            g.add((prop, SH.hasValue, coll[0]))
            g.remove((prop, SH["in"], in_list))
    
    # 2. Eliminar sh:maxCount 1 para permitir tipos auxiliares (como rdfs:Resource)
    g.remove((prop, SH.maxCount, None))

g.serialize(destination="TAREA_5/shapes/shapes_from_data.ttl", format="turtle")

print("Shapes from data extracted and post-processed successfully.")
