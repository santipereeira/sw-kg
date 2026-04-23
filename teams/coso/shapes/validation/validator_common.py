import argparse
import re
from pathlib import Path
from urllib.parse import unquote

from rdflib import Graph
from pyshacl import validate


XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"
XSD_STRING_WRONG_1 = "http://www.w3.org/2001/XMLSchema#String"
XSD_STRING_WRONG_2 = "http://www.w3.org/2001/XMLSchema#str"
XSD_INT = "http://www.w3.org/2001/XMLSchema#int"


def clean_common_datatype_issues(text: str) -> str:
    """Normaliza errores frecuentes de datatype en shapes o datos."""
    text = text.replace(XSD_STRING_WRONG_1, XSD_STRING)
    text = text.replace(XSD_STRING_WRONG_2, XSD_STRING)

    # Corrige enteros mal escritos como "15880."^^xsd:int -> "15880"^^xsd:int
    text = re.sub(
        rf'"(\d+)\."\^\^<{re.escape(XSD_INT)}>',
        rf'"\1"^^<{XSD_INT}>',
        text,
    )
    return text


def clean_iris_selectively(text: str) -> str:
    """
    Corrige solo IRIs claramente problemáticas, sin decodificar las IRIs válidas
    que ya vienen percent-encoded en N-Triples/N3/Turtle.

    Ejemplo que sí corregimos:
      <http%3A%2F%2Fwww.wikidata.org%2Fentity%2FQ42 >
      -> <http://www.wikidata.org/entity/Q42>

    Ejemplo que NO debemos tocar:
      <http://example.org/resource/equipo/MOTO%20CLUB%20CORU%C3%91A%2FESCUDER%C3%8DA%20CENTOLLO>
    """

    def fix_iri(match: re.Match) -> str:
        iri = match.group(1).strip()

        # Solo decodificamos si TODA la IRI está codificada desde el esquema.
        # Así evitamos romper IRIs válidas que contienen %20, %2F, etc.
        if iri.startswith("http%3A") or iri.startswith("https%3A"):
            iri = unquote(iri).strip()

        return f"<{iri}>"

    return re.sub(r"<([^<>]+)>", fix_iri, text)


def clean_text(text: str) -> str:
    text = clean_common_datatype_issues(text)
    text = clean_iris_selectively(text)
    return text


def guess_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".nt":
        return "nt"
    if suffix == ".ttl":
        return "turtle"
    if suffix == ".n3":
        return "n3"
    if suffix == ".rdf":
        return "xml"
    return "turtle"



def load_graph_from_path(path: str, label: str) -> Graph:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    cleaned = clean_text(text)

    g = Graph()
    rdf_format = guess_format(file_path)
    g.parse(data=cleaned, format=rdf_format)
    print(f"[{label}] Grafo cargado correctamente con {len(g)} triples.")
    return g



def run_validation(data_path: str, shapes_path: str, output_path: str | None = None) -> None:
    data_graph = load_graph_from_path(data_path, "data")
    shapes_graph = load_graph_from_path(shapes_path, "shapes")

    conforms, results_graph, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        advanced=True,
        debug=False,
    )

    print("\n===================================")
    print("RESULTADO VALIDACIÓN SHACL")
    print("===================================")
    print(f"Conforma: {conforms}")
    print("\n--- Detalles ---")
    print(results_text)

    if output_path:
        results_graph.serialize(destination=output_path, format="turtle")
        print(f"\nInforme guardado en: {output_path}")



def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--data", required=True, help="Ruta al grafo RDF de datos")
    parser.add_argument("--shapes", required=True, help="Ruta al fichero de shapes SHACL")
    parser.add_argument("--output", required=False, help="Ruta para guardar el informe RDF")
    return parser
