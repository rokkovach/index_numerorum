import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from index_numerorum.config import COMPOSITE_KEY_COLUMN
from index_numerorum.keys import (
    average_embeddings,
    build_composite_key,
    concatenate_columns,
    parse_weighted_columns,
)


class TestConcatenateColumns:
    def test_two_columns_joined(self):
        df = pd.DataFrame({"A": ["x", "y"], "B": ["1", "2"]})
        result = concatenate_columns(df, ["A", "B"])
        assert result.tolist() == ["x 1", "y 2"]

    def test_custom_separator(self):
        df = pd.DataFrame({"A": ["x"], "B": ["1"]})
        result = concatenate_columns(df, ["A", "B"], separator="-")
        assert result.iloc[0] == "x-1"

    def test_handles_nan(self):
        df = pd.DataFrame({"A": ["hello", "world"], "B": [None, "test"]})
        result = concatenate_columns(df, ["A", "B"])
        assert result.iloc[0] == "hello "
        assert result.iloc[1] == "world test"

    def test_three_columns(self):
        df = pd.DataFrame({"A": ["a"], "B": ["b"], "C": ["c"]})
        result = concatenate_columns(df, ["A", "B", "C"])
        assert result.iloc[0] == "a b c"

    def test_result_name(self):
        df = pd.DataFrame({"A": ["x"], "B": ["1"]})
        result = concatenate_columns(df, ["A", "B"])
        assert result.name == COMPOSITE_KEY_COLUMN


class TestAverageEmbeddings:
    def test_two_equal_vectors(self):
        vec = np.array([[1.0, 2.0], [3.0, 4.0]])
        embeddings = {"a": vec, "b": vec}
        result = average_embeddings(embeddings)
        assert_allclose(result, vec, rtol=1e-5)

    def test_two_different_mean(self):
        a = np.array([[1.0, 0.0]])
        b = np.array([[0.0, 1.0]])
        result = average_embeddings({"a": a, "b": b})
        expected = np.array([[0.5, 0.5]])
        assert_allclose(result, expected, rtol=1e-5)

    def test_single_embedding(self):
        vec = np.array([[3.0, 4.0]])
        result = average_embeddings({"only": vec})
        assert_allclose(result, vec, rtol=1e-5)

    def test_weights_normalize(self):
        a = np.array([[2.0, 0.0]])
        b = np.array([[0.0, 2.0]])
        result = average_embeddings({"a": a, "b": b}, weights={"a": 3.0, "b": 1.0})
        expected = np.array([[1.5, 0.5]])
        assert_allclose(result, expected, rtol=1e-5)

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            average_embeddings({})


class TestParseWeightedColumns:
    def test_with_weights(self):
        cols = ["Name:2.0", "Category:1.0"]
        names, weights = parse_weighted_columns(cols)
        assert names == ["Name", "Category"]
        assert weights == {"Name": 2.0, "Category": 1.0}

    def test_without_weights(self):
        cols = ["Name", "Category"]
        names, weights = parse_weighted_columns(cols)
        assert names == ["Name", "Category"]
        assert weights == {"Name": 1.0, "Category": 1.0}

    def test_invalid_weight(self):
        with pytest.raises(ValueError, match="Invalid weight"):
            parse_weighted_columns(["Name:abc"])

    def test_negative_weight(self):
        with pytest.raises(ValueError, match="Negative weight"):
            parse_weighted_columns(["Name:-1.0"])


class TestBuildCompositeKey:
    def test_concatenate_strategy(self):
        df = pd.DataFrame({"A": ["hello"], "B": ["world"]})
        result = build_composite_key(df, ["A", "B"], strategy="concatenate")
        assert result.iloc[0] == "hello world"

    def test_invalid_strategy_raises(self):
        df = pd.DataFrame({"A": ["x"]})
        with pytest.raises(ValueError, match="Unknown strategy"):
            build_composite_key(df, ["A"], strategy="unknown")
