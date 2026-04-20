from pathlib import Path

from validate_shapes import run_validation


TEAM_DIR = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    # Convenience entry point for the shapes inferred from the RDF data.
    run_validation(
        shapes_path=TEAM_DIR / "shapes" / "shapes_from_data.ttl",
        report_path=TEAM_DIR / "shapes" / "validation" / "report_data_shapes.ttl",
        label="data-shapes",
    )
