from pathlib import Path
import gc

from pyshacl import validate
import rdflib


def _guess_rdf_format(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".nt":
        return "nt"
    if suffix == ".ttl":
        return "turtle"
    if suffix == ".n3":
        return "n3"
    if suffix == ".xml" or suffix == ".rdf":
        return "xml"
    if suffix == ".jsonld":
        return "json-ld"
    # Valor por defecto razonable para esta repo.
    return "turtle"

def run_validation(data_graph_path, shacl_graph_path, report_output_path):
    print(f"Validating {data_graph_path} against {shacl_graph_path}...")
    data_graph_format = _guess_rdf_format(data_graph_path)
    shacl_graph_format = _guess_rdf_format(shacl_graph_path)

    conforms, results_graph, _ = validate(
        data_graph=data_graph_path,
        shacl_graph=shacl_graph_path,
        data_graph_format=data_graph_format,
        shacl_graph_format=shacl_graph_format,
        inference="none",  # Evita que el RDFS ensucie los rdf:type de ShexEr
        debug=False,
        abort_on_first=True,
        serialize_report_graph=None,
    )

    # Serializa directamente a fichero para evitar crear un blob grande en memoria.
    if isinstance(results_graph, rdflib.Graph):
        results_graph.serialize(destination=report_output_path, format="turtle")
    elif isinstance(results_graph, bytes):
        with open(report_output_path, "wb") as f:
            f.write(results_graph)
    else:
        with open(report_output_path, "w", encoding="utf-8") as f:
            f.write(str(results_graph))
    
    print(f"Results for {shacl_graph_path}:")
    print(f"Conforms: {conforms}")
    print(f"Report written to: {report_output_path}")
    print("="*60)

    # Liberar referencias explícitamente ayuda con grafos grandes.
    del results_graph
    gc.collect()
    
if __name__ == "__main__":
    run_validation("TAREA_4/kg/output.nt", "TAREA_5/shapes/shapes_from_data.ttl", "TAREA_5/shapes/validation/report_data_shapes.ttl")
    run_validation("TAREA_4/kg/output.nt", "TAREA_5/shapes/shapes_from_ontology.ttl", "TAREA_5/shapes/validation/report_model_shapes.ttl")
