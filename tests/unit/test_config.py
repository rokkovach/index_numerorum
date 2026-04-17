import pytest

from index_numerorum.config import (
    DEFAULT_METRIC,
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    resolve_model,
)


class TestModelRegistry:
    def test_all_shortcuts_present(self):
        expected = {"mini", "bge-large", "nomic", "gte", "e5", "address", "entity"}
        assert set(MODEL_REGISTRY.keys()) == expected

    def test_shortcuts_map_to_correct_ids(self):
        assert MODEL_REGISTRY["mini"].id == "all-MiniLM-L6-v2"
        assert MODEL_REGISTRY["bge-large"].id == "BAAI/bge-large-en-v1.5"
        assert MODEL_REGISTRY["nomic"].id == "nomic-ai/nomic-embed-text-v1.5"
        assert MODEL_REGISTRY["gte"].id == "Alibaba-NLP/gte-large-en-v1.5"
        assert MODEL_REGISTRY["e5"].id == "intfloat/e5-large-v2"


class TestResolveModel:
    def test_by_shortcut(self):
        info = resolve_model("mini")
        assert info.id == "all-MiniLM-L6-v2"

    def test_by_full_id(self):
        info = resolve_model("all-MiniLM-L6-v2")
        assert info.shortcut == "mini"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            resolve_model("nonexistent-model")


class TestConstants:
    def test_default_model(self):
        assert DEFAULT_MODEL == "mini"

    def test_default_metric(self):
        assert DEFAULT_METRIC == "cosine"


class TestModelInfo:
    def test_frozen(self):
        info = resolve_model("mini")
        with pytest.raises(AttributeError):
            info.id = "changed"
