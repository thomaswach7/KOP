from creo_mcp.__main__ import normalize_argv


def test_options_without_subcommand_default_to_serve():
    assert normalize_argv(["--transport", "streamable-http"]) == ["serve", "--transport", "streamable-http"]


def test_empty_argv_is_serve():
    assert normalize_argv([]) == ["serve"]


def test_help_and_subcommands_unchanged():
    assert normalize_argv(["--help"]) == ["--help"]
    assert normalize_argv(["demo", "--port", "1"]) == ["demo", "--port", "1"]
