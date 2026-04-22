from validator_common import build_parser, run_validation


if __name__ == "__main__":
    parser = build_parser("Valida el KG con las shapes generadas desde la ontología o los mappings")
    parser.set_defaults(
        shapes="shapes_from_ontology_or_mappings.ttl",
        output="validation/report_model_shapes.ttl",
    )
    args = parser.parse_args()
    run_validation(args.data, args.shapes, args.output)
