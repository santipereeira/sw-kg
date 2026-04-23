from validator_common import build_parser, run_validation


if __name__ == "__main__":
    parser = build_parser("Valida el KG con las shapes generadas desde los datos")
    parser.set_defaults(
        shapes="shapes_from_data.ttl",
        output="validation/report_data_shapes.ttl",
    )
    args = parser.parse_args()
    run_validation(args.data, args.shapes, args.output)
