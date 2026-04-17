from typer.testing import CliRunner

from index_numerorum.cli import app

runner = CliRunner()


class TestHelpOutput:
    def test_help_returns_zero(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_mentions_commands(self):
        result = runner.invoke(app, ["--help"])
        assert "embed" in result.output
        assert "neighbors" in result.output
        assert "compare" in result.output
        assert "compose-key" in result.output
        assert "models" in result.output
        assert "demo" in result.output
        assert "doctor" in result.output


class TestVersionFlag:
    def test_version_long(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_version_short(self):
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestEmbedMissingArgs:
    def test_embed_without_args(self):
        result = runner.invoke(app, ["embed"])
        assert result.exit_code != 0

    def test_embed_help_has_examples(self):
        result = runner.invoke(app, ["embed", "--help"])
        assert "Examples" in result.output


class TestNeighborsMissingArgs:
    def test_neighbors_without_args(self):
        result = runner.invoke(app, ["neighbors"])
        assert result.exit_code != 0

    def test_neighbors_help_has_examples(self):
        result = runner.invoke(app, ["neighbors", "--help"])
        assert "Examples" in result.output


class TestCompareItemCount:
    def test_compare_with_no_args(self):
        result = runner.invoke(app, ["compare"])
        assert result.exit_code != 0

    def test_compare_with_wrong_item_count(self):
        result = runner.invoke(app, ["compare", "/tmp/fake.xlsx", "-k", "Name"])
        assert result.exit_code != 0


class TestComposeKey:
    def test_compose_key_help_has_examples(self):
        result = runner.invoke(app, ["compose-key", "--help"])
        assert "Examples" in result.output


class TestModelsCommand:
    def test_models_help(self):
        result = runner.invoke(app, ["models", "--help"])
        assert result.exit_code == 0
