import numpy as np
import pytest
from numpy.testing import assert_allclose

from index_numerorum.similarity import (
    compute_pairwise,
    cosine_similarity,
    dot_product,
    euclidean_distance,
    manhattan_distance,
    pairwise_cosine,
    pairwise_dot,
    pairwise_euclidean,
    pairwise_manhattan,
)


class TestCosineSimilarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        assert_allclose(cosine_similarity(a, a), 1.0, rtol=1e-5)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert_allclose(cosine_similarity(a, b), 0.0, rtol=1e-5)

    def test_opposite_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])
        assert_allclose(cosine_similarity(a, b), -1.0, rtol=1e-5)

    def test_known_pair(self):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        expected = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        assert_allclose(cosine_similarity(a, b), expected, rtol=1e-5)

    def test_zero_vector_raises(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        with pytest.raises(ValueError, match="zero vectors"):
            cosine_similarity(a, b)

    def test_batch_matches_pairwise(self):
        matrix = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        result = pairwise_cosine(matrix)
        assert result.shape == (3, 3)
        for i in range(3):
            for j in range(3):
                if i == j:
                    assert_allclose(result[i, j], 1.0, rtol=1e-5)
                else:
                    expected = cosine_similarity(matrix[i], matrix[j])
                    assert_allclose(result[i, j], expected, rtol=1e-5)


class TestEuclideanDistance:
    def test_identical_vectors(self):
        a = np.array([1.0, 2.0, 3.0])
        assert_allclose(euclidean_distance(a, a), 0.0, atol=1e-8)

    def test_known_values(self):
        a = np.array([0.0, 0.0])
        b = np.array([3.0, 4.0])
        assert_allclose(euclidean_distance(a, b), 5.0, rtol=1e-5)

    def test_batch_matches_pairwise(self):
        matrix = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        result = pairwise_euclidean(matrix)
        assert result.shape == (3, 3)
        for i in range(3):
            for j in range(3):
                expected = euclidean_distance(matrix[i], matrix[j])
                assert_allclose(result[i, j], expected, rtol=1e-5)


class TestManhattanDistance:
    def test_identical_vectors(self):
        a = np.array([5.0, -3.0])
        assert_allclose(manhattan_distance(a, a), 0.0, atol=1e-8)

    def test_known_values(self):
        a = np.array([1.0, 2.0])
        b = np.array([4.0, 6.0])
        assert_allclose(manhattan_distance(a, b), 7.0, rtol=1e-5)

    def test_batch_matches_pairwise(self):
        matrix = np.array([[1.0, 2.0], [3.0, 4.0], [0.0, 0.0]])
        result = pairwise_manhattan(matrix)
        assert result.shape == (3, 3)
        for i in range(3):
            for j in range(3):
                expected = manhattan_distance(matrix[i], matrix[j])
                assert_allclose(result[i, j], expected, rtol=1e-5)


class TestDotProduct:
    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert_allclose(dot_product(a, b), 0.0, atol=1e-8)

    def test_known_values(self):
        a = np.array([2.0, 3.0])
        b = np.array([4.0, 5.0])
        assert_allclose(dot_product(a, b), 23.0, rtol=1e-5)

    def test_batch_matches_pairwise(self):
        matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = pairwise_dot(matrix)
        assert result.shape == (2, 2)
        for i in range(2):
            for j in range(2):
                expected = dot_product(matrix[i], matrix[j])
                assert_allclose(result[i, j], expected, rtol=1e-5)


class TestComputePairwise:
    def test_valid_metric(self):
        matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
        result = compute_pairwise(matrix, "cosine")
        assert result.shape == (2, 2)

    def test_invalid_metric_raises(self):
        matrix = np.array([[1.0, 0.0]])
        with pytest.raises(ValueError, match="Unknown metric"):
            compute_pairwise(matrix, "hamming")
