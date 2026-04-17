import pytest

from index_numerorum.config import resolve_model
from index_numerorum.embed import embed_columns, load_model
from index_numerorum.io import read_xlsx
from index_numerorum.neighbors import compare_items, find_neighbors


@pytest.mark.integration
@pytest.mark.slow
class TestNeighborPipeline:
    def test_find_neighbors_output_shape(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        embedded = embed_columns(df, ["Name"], model)
        result = find_neighbors(embedded, "Name", top_k=3)
        assert len(result) == 5 * 3
        assert set(result.columns) == {"query_key", "neighbor_key", "rank", "score"}

    def test_ranks_start_at_one(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        embedded = embed_columns(df, ["Name"], model)
        result = find_neighbors(embedded, "Name", top_k=3)
        assert result["rank"].min() == 1


@pytest.mark.integration
@pytest.mark.slow
class TestCompareItems:
    def test_all_four_metrics_returned(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        model_info = resolve_model("mini")
        model = load_model(model_info)
        embedded = embed_columns(df, ["Name"], model)
        result = compare_items(embedded, "Name", "Alpha", "Beta")
        assert set(result.keys()) == {"cosine", "euclidean", "manhattan", "dot"}
        for v in result.values():
            assert isinstance(v, float)
