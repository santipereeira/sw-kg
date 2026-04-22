from pathlib import Path

from pyshacl import validate


BASE_DIR = Path(__file__).resolve().parents[3]
TASK5_DIR = BASE_DIR / "task5"

DATA_GRAPH = BASE_DIR / "task4" / "kg" / "output.nt"
SHAPES_GRAPH = TASK5_DIR / "shapes" / "shapes_from_model.ttl"
REPORT_PATH = Path(__file__).resolve().parent / "report_model_shapes.ttl"


conforms, report_graph, report_text = validate(
    data_graph=str(DATA_GRAPH),
    data_graph_format="nt",
    shacl_graph=str(SHAPES_GRAPH),
    shacl_graph_format="turtle",
    inference="none",
    serialize_report_graph="turtle",
)

print("Conforms:", conforms)
print(report_text)

REPORT_PATH.write_bytes(report_graph)
