import pytest

from index_numerorum.config import resolve_model
from index_numerorum.embed import embed_columns, load_model
from index_numerorum.io import read_xlsx
from index_numerorum.keys import build_composite_key


@pytest.mark.integration
class TestComposeKeyPipeline:
    def test_composite_key_from_two_columns(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        embedded = embed_columns(df, ["Name"], model)
        result = build_composite_key(embedded, ["Name", "Category"])
        assert result.name == "_composite_key"
        assert len(result) == 5
        assert result.iloc[0] == "Alpha A"
