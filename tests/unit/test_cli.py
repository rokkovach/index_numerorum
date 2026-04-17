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


class TestEmbedMissingArgs:
    def test_embed_without_args(self):
        result = runner.invoke(app, ["embed"])
        assert result.exit_code != 0


class TestNeighborsMissingArgs:
    def test_neighbors_without_args(self):
        result = runner.invoke(app, ["neighbors"])
        assert result.exit_code != 0


class TestCompareItemCount:
    def test_compare_with_wrong_item_count(self):
        result = runner.invoke(app, ["compare", "only_one_item"])
        assert result.exit_code != 0
