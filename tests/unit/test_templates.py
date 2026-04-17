import pandas as pd
import pytest
from typer.testing import CliRunner

from index_numerorum.cli import app
from index_numerorum.templates import TEMPLATES, copy_template, get_template, list_templates

runner = CliRunner()


class TestTemplateRegistry:
    def test_five_templates_exist(self):
        assert len(TEMPLATES) == 5

    def test_all_have_required_fields(self):
        for t in TEMPLATES:
            assert t.id
            assert t.name
            assert t.description
            assert t.industry
            assert len(t.columns) >= 2
            assert t.key_column in t.columns
            for ec in t.embed_columns:
                assert ec in t.columns
            assert t.suggested_model in (
                "mini",
                "bge-large",
                "nomic",
                "gte",
                "e5",
                "address",
                "entity",
            )
            assert len(t.rows) >= 10
            assert len(t.steps) >= 3

    def test_unique_ids(self):
        ids = [t.id for t in TEMPLATES]
        assert len(ids) == len(set(ids))

    def test_template_ids(self):
        expected = {
            "vendor-dedup",
            "address-cleansing",
            "product-catalog",
            "lead-dedup",
            "counterparty-screening",
        }
        assert set(t.id for t in TEMPLATES) == expected

    def test_get_template_found(self):
        t = get_template("vendor-dedup")
        assert t is not None
        assert t.name == "Vendor Deduplication After Merger"

    def test_get_template_not_found(self):
        assert get_template("nonexistent") is None

    def test_list_templates_returns_all(self):
        assert len(list_templates()) == 5


class TestTemplateCopy:
    def test_copy_creates_xlsx(self, tmp_path):
        dest = copy_template("vendor-dedup", dest=tmp_path)
        assert dest.exists()
        assert dest.name == "vendor-dedup.xlsx"

    def test_copy_has_correct_data(self, tmp_path):
        dest = copy_template("product-catalog", dest=tmp_path)
        df = pd.read_excel(dest, sheet_name="data", engine="openpyxl")
        template = get_template("product-catalog")
        assert len(df) == len(template.rows)
        assert list(df.columns) == template.columns

    def test_copy_has_metadata(self, tmp_path):
        dest = copy_template("address-cleansing", dest=tmp_path)
        meta = pd.read_excel(dest, sheet_name="_metadata", engine="openpyxl")
        params = dict(zip(meta["Parameter"], meta["Value"], strict=True))
        assert params["template"] == "address-cleansing"
        assert params["suggested_model"] == "address"

    def test_copy_unknown_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown template"):
            copy_template("nope", dest=tmp_path)

    def test_copy_overwrites_existing(self, tmp_path):
        copy_template("vendor-dedup", dest=tmp_path)
        dest = copy_template("vendor-dedup", dest=tmp_path)
        assert dest.exists()

    def test_copy_all_templates(self, tmp_path):
        for t in TEMPLATES:
            dest = copy_template(t.id, dest=tmp_path)
            assert dest.exists()
            df = pd.read_excel(dest, sheet_name="data", engine="openpyxl")
            assert len(df) == len(t.rows)


class TestTemplatesCLI:
    def test_templates_list(self):
        result = runner.invoke(app, ["templates"])
        assert result.exit_code == 0
        assert "vendor-dedup" in result.output
        assert "address-cleansing" in result.output
        assert "product-catalog" in result.output
        assert "lead-dedup" in result.output
        assert "counterparty" in result.output

    def test_templates_show(self):
        result = runner.invoke(app, ["templates", "--show", "vendor-dedup"])
        assert result.exit_code == 0
        assert "Vendor Deduplication" in result.output
        assert "Procurement" in result.output
        assert "Steps:" in result.output

    def test_templates_show_unknown(self):
        result = runner.invoke(app, ["templates", "--show", "nope"])
        assert result.exit_code == 1
        assert "Unknown template" in result.output

    def test_templates_use_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["templates", "--use", "vendor-dedup"])
        assert result.exit_code == 0
        assert (tmp_path / "input" / "vendor-dedup.xlsx").exists()

    def test_templates_use_unknown(self):
        result = runner.invoke(app, ["templates", "--use", "nope"])
        assert result.exit_code == 1
        assert "Unknown template" in result.output
