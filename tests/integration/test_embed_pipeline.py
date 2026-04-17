import pytest

from index_numerorum.config import resolve_model
from index_numerorum.embed import embed_columns, load_model
from index_numerorum.io import get_embedding_columns, read_xlsx


@pytest.mark.integration
@pytest.mark.slow
class TestEmbedPipeline:
    def test_embed_creates_columns(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        result = embed_columns(df, ["Name", "Description"], model)
        emb_cols = get_embedding_columns(result)
        assert "_emb_Name" in emb_cols
        assert "_emb_Description" in emb_cols

    def test_embedding_dimensions(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        result = embed_columns(df, ["Name"], model)
        from index_numerorum.io import deserialize_embedding

        vec = deserialize_embedding(result["_emb_Name"].iloc[0])
        assert vec.shape[0] == model_info.dim
