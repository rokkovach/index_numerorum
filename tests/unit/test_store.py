import json

import numpy as np
import pandas as pd
import pytest

from index_numerorum.store import VectorStore, _compute_groups


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "ID": ["1", "2", "3"],
            "Name": ["Widget A", "Widget B", "Gadget X"],
            "Category": ["Electronics", "Electronics", "Tools"],
        }
    )


@pytest.fixture
def sample_embeddings():
    return np.array(
        [[0.1, 0.2, 0.3, 0.4], [0.11, 0.21, 0.31, 0.41], [0.9, 0.8, 0.7, 0.6]],
        dtype=np.float32,
    )


@pytest.fixture
def store(tmp_path, sample_df, sample_embeddings):
    s = VectorStore.create(
        path=tmp_path / "test_store",
        model_id="all-MiniLM-L6-v2",
        dimensions=4,
        key_column="ID",
        embed_columns=["Name"],
    )
    s.insert_rows(sample_df, sample_embeddings, ["1", "2", "3"])
    return s


class TestComputeGroups:
    def test_no_pairs(self):
        assert _compute_groups([]) == {}

    def test_single_pair(self):
        result = _compute_groups([("a", "b")])
        assert result["a"] == result["b"]
        assert result["a"] > 0

    def test_two_separate_groups(self):
        result = _compute_groups([("a", "b"), ("c", "d")])
        assert result["a"] == result["b"]
        assert result["c"] == result["d"]
        assert result["a"] != result["c"]

    def test_transitive_grouping(self):
        result = _compute_groups([("a", "b"), ("b", "c")])
        assert result["a"] == result["b"] == result["c"]

    def test_chain_of_matches(self):
        result = _compute_groups([("a", "b"), ("b", "c"), ("d", "e")])
        assert result["a"] == result["b"] == result["c"]
        assert result["d"] == result["e"]
        assert result["a"] != result["d"]


class TestVectorStoreCreate:
    def test_creates_store(self, tmp_path):
        store = VectorStore.create(
            path=tmp_path / "new_store",
            model_id="test-model",
            dimensions=128,
            key_column="ID",
            embed_columns=["Name"],
        )
        assert store.model_id == "test-model"
        assert store.dimensions == 128
        assert store.key_column == "ID"
        assert store.embed_columns == ["Name"]
        assert store.row_count == 0

    def test_creates_meta_file(self, tmp_path):
        path = tmp_path / "meta_store"
        VectorStore.create(path, "model-x", 64, "ID", ["Text"])
        meta = json.loads((path / "_meta.json").read_text())
        assert meta["model_id"] == "model-x"
        assert meta["dimensions"] == 64

    def test_creates_sidecar_files(self, tmp_path):
        path = tmp_path / "sidecar_store"
        VectorStore.create(path, "model", 32, "ID", ["Text"])
        assert (path / "_keys.json").exists()
        assert (path / "_embeddings.npy").exists()


class TestVectorStoreInsert:
    def test_insert_rows(self, store, sample_df, sample_embeddings):
        assert store.row_count == 3
        assert len(store._keys) == 3

    def test_insert_more_rows(self, store):
        new_df = pd.DataFrame({"ID": ["4"], "Name": ["Thing"], "Category": ["Misc"]})
        new_emb = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float32)
        count = store.insert_rows(new_df, new_emb, ["4"])
        assert count == 1
        assert store.row_count == 4


class TestVectorStoreQuery:
    def test_query_returns_results(self, store):
        results = store.query([0.1, 0.2, 0.3, 0.4], top_k=3)
        assert len(results) == 3
        assert all("id" in r for r in results)
        assert all("similarity" in r for r in results)

    def test_query_most_similar_first(self, store):
        results = store.query([0.1, 0.2, 0.3, 0.4], top_k=3)
        assert results[0]["id"] == "1"
        assert results[0]["similarity"] > 0.9

    def test_query_top_k(self, store):
        results = store.query([0.1, 0.2, 0.3, 0.4], top_k=1)
        assert len(results) == 1


class TestVectorStoreMatch:
    def test_match_finds_similar(self, store):
        result = store.match_all(threshold=0.80)
        assert not result.empty
        assert "query_key" in result.columns
        assert "match_key" in result.columns
        assert "similarity" in result.columns
        assert "group_id" in result.columns

    def test_match_high_threshold_empty(self, store):
        result = store.match_all(threshold=0.99999)
        assert result.empty

    def test_match_group_ids(self, store):
        result = store.match_all(threshold=0.80)
        if not result.empty:
            assert result["group_id"].min() >= 1


class TestVectorStoreAnnotate:
    def test_annotates_dataframe(self, store, sample_df):
        result = store.annotate(sample_df, threshold=0.80)
        assert "_match_count" in result.columns
        assert "_match_ids" in result.columns
        assert "_best_match_id" in result.columns
        assert "_best_match_score" in result.columns
        assert "_group_id" in result.columns

    def test_annotate_preserves_rows(self, store, sample_df):
        result = store.annotate(sample_df, threshold=0.80)
        assert len(result) == len(sample_df)


class TestVectorStoreInfo:
    def test_info_returns_dict(self, store):
        info = store.info()
        assert info["row_count"] == 3
        assert info["model_id"] == "all-MiniLM-L6-v2"
        assert info["dimensions"] == 4
        assert info["key_column"] == "ID"
        assert info["size_on_disk"] > 0


class TestVectorStoreReopen:
    def test_reopen_preserves_data(self, tmp_path, store):
        del store._collection
        store2 = VectorStore(tmp_path / "test_store")
        assert store2.row_count == 3
        assert store2.model_id == "all-MiniLM-L6-v2"
        results = store2.query([0.1, 0.2, 0.3, 0.4], top_k=2)
        assert len(results) == 2
