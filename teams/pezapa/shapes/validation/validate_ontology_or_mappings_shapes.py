from pathlib import Path

from validate_shapes import run_validation


TEAM_DIR = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    # Convenience entry point for the manually curated shapes derived from model and mappings.
    run_validation(
        shapes_path=TEAM_DIR / "shapes" / "shapes_from_ontology_or_mappings.ttl",
        report_path=TEAM_DIR / "shapes" / "validation" / "report_model_shapes.ttl",
        label="model-shapes",
    )
