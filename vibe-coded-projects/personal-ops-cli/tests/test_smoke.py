from personal_ops_cli.cli import _build_parser


def test_parser_builds() -> None:
    parser = _build_parser()
    assert parser.prog == "ops"

