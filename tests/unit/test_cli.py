from typer.testing import CliRunner

from index_numerorum.cli import _format_elapsed, _score_bar, app

runner = CliRunner()


class TestHelpers:
    def test_score_bar_cosine_perfect(self):
        bar = _score_bar(1.0, "cosine")
        assert "\u2588" in bar

    def test_score_bar_cosine_zero(self):
        bar = _score_bar(-1.0, "cosine")
        assert "\u2591" in bar

    def test_score_bar_non_cosine_empty(self):
        assert _score_bar(5.0, "euclidean") == ""

    def test_format_elapsed_ms(self):
        assert "ms" in _format_elapsed(0.5)

    def test_format_elapsed_s(self):
        assert "s" in _format_elapsed(5.0)

    def test_format_elapsed_min(self):
        assert "min" in _format_elapsed(120.0)


class TestHelpOutput:
    def test_help_returns_zero(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_has_command_descriptions(self):
        result = runner.invoke(app, ["--help"])
        assert "Generate embeddings" in result.output
        assert "Find nearest" in result.output
        assert "Compare two" in result.output
        assert "composite key" in result.output.lower()

    def test_help_mentions_all_commands(self):
        result = runner.invoke(app, ["--help"])
        for cmd in ["embed", "neighbors", "compare", "compose-key", "models", "demo", "doctor"]:
            assert cmd in result.output


class TestVersionFlag:
    def test_version_long(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_version_short(self):
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCommandHelp:
    def test_embed_help_has_examples(self):
        result = runner.invoke(app, ["embed", "--help"])
        assert "Examples" in result.output
        assert "Single column" in result.output

    def test_neighbors_help_has_examples(self):
        result = runner.invoke(app, ["neighbors", "--help"])
        assert "Examples" in result.output

    def test_compare_help_has_examples(self):
        result = runner.invoke(app, ["compare", "--help"])
        assert "Examples" in result.output

    def test_compose_key_help_has_examples(self):
        result = runner.invoke(app, ["compose-key", "--help"])
        assert "Examples" in result.output

    def test_models_help_has_examples(self):
        result = runner.invoke(app, ["models", "--help"])
        assert "Examples" in result.output

    def test_embed_help_has_description(self):
        result = runner.invoke(app, ["embed", "--help"])
        assert "Generate embeddings" in result.output

    def test_neighbors_help_has_description(self):
        result = runner.invoke(app, ["neighbors", "--help"])
        assert "Find nearest" in result.output


class TestMissingArgs:
    def test_embed_without_args(self):
        result = runner.invoke(app, ["embed"])
        assert result.exit_code != 0

    def test_neighbors_without_args(self):
        result = runner.invoke(app, ["neighbors"])
        assert result.exit_code != 0

    def test_compare_with_no_args(self):
        result = runner.invoke(app, ["compare"])
        assert result.exit_code != 0

    def test_compare_with_wrong_item_count(self):
        result = runner.invoke(app, ["compare", "/tmp/fake.xlsx", "-k", "Name"])
        assert result.exit_code != 0


class TestErrorPanels:
    def test_bad_model_shows_error_panel(self):
        result = runner.invoke(app, ["embed", "/tmp/fake.xlsx", "-c", "X", "-m", "nope"])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_bad_column_shows_error_panel(self):
        result = runner.invoke(
            app, ["embed", "/tmp/test_data.xlsx", "-c", "Nonexistent", "-m", "mini"]
        )
        assert result.exit_code != 0
        assert "Error" in result.output
