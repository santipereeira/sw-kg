from pathlib import Path

from shexer.consts import SHACL_TURTLE, TURTLE_ITER
from shexer.shaper import Shaper


# Resolve every path from the team folder so the script works from any cwd.
TEAM_DIR = Path(__file__).resolve().parents[2]
KG_FILE = TEAM_DIR / "kg" / "output.ttl"
OUTPUT_FILE = TEAM_DIR / "shapes" / "shapes_from_data.ttl"

NAMESPACES = {
    "http://example.org/def/teatrosyauditorios#": "ta",
    "http://example.org/resource/": "ex",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2001/XMLSchema#": "xsd",
    "http://www.w3.org/ns/shacl#": "sh",
}


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Keep the extraction fairly strict so duplicated merged resources still surface later in validation.
    shaper = Shaper(
        graph_file_input=str(KG_FILE),
        input_format=TURTLE_ITER,
        all_classes_mode=True,
        namespaces_dict=NAMESPACES,
        all_instances_are_compliant_mode=False,
        keep_less_specific=False,
    )

    shaper.shex_graph(
        output_file=str(OUTPUT_FILE),
        output_format=SHACL_TURTLE,
        acceptance_threshold=0.9,
        verbose=True,
    )

    # sheXer serializes sh:dataType, but pySHACL expects the standard sh:datatype.
    text = OUTPUT_FILE.read_text(encoding="utf-8")
    OUTPUT_FILE.write_text(text.replace("sh:dataType", "sh:datatype"), encoding="utf-8")

    print(f"Generated SHACL shapes in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
