import argparse
from pathlib import Path

from pyshacl import validate
from rdflib import Graph


# Shared team paths used by both the CLI entry point and the thin wrapper scripts.
TEAM_DIR = Path(__file__).resolve().parents[2]
KG_FILE = TEAM_DIR / "kg" / "output.ttl"
ONTOLOGY_FILE = TEAM_DIR / "ontology" / "ontology.ttl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the KG against a SHACL shapes graph.")
    parser.add_argument("--shapes", required=True, help="Path to the SHACL shapes file.")
    parser.add_argument("--report", required=True, help="Path where the validation report will be saved.")
    parser.add_argument(
        "--label",
        default="validation",
        help="Short label printed in stdout to identify the validation run.",
    )
    parser.add_argument(
        "--with-ontology",
        action="store_true",
        help="Load the ontology graph and enable RDFS inference during validation.",
    )
    return parser.parse_args()


def run_validation(shapes_path: Path, report_path: Path, label: str, with_ontology: bool = False) -> None:
    data_graph = Graph().parse(KG_FILE, format="turtle")
    shacl_graph = Graph().parse(shapes_path, format="turtle")
    ontology_graph = None
    inference = "none"

    # Ontology loading is optional because RDFS inference is useful for some checks but can also add noise.
    if with_ontology:
        ontology_graph = Graph().parse(ONTOLOGY_FILE, format="turtle")
        inference = "rdfs"

    conforms, report_graph, report_text = validate(
        data_graph=data_graph,
        shacl_graph=shacl_graph,
        ont_graph=ontology_graph,
        inference=inference,
    )

    # Keep the full report in RDF so the delivery contains machine-readable validation evidence.
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_graph.serialize(format="turtle"), encoding="utf-8")

    print(f"[{label}] conforms={conforms}")
    print(f"[{label}] report={report_path}")
    print(report_text)


def main() -> None:
    args = parse_args()
    run_validation(
        shapes_path=Path(args.shapes).resolve(),
        report_path=Path(args.report).resolve(),
        label=args.label,
        with_ontology=args.with_ontology,
    )


if __name__ == "__main__":
    main()
