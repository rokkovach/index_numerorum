from collections.abc import Callable

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError("Cosine similarity is undefined for zero vectors.")
    return float(np.dot(a, b) / (norm_a * norm_b))


def euclidean_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def manhattan_distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sum(np.abs(a - b)))


def dot_product(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def pairwise_cosine(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, np.finfo(float).eps, norms)
    normalized = matrix / norms
    return normalized @ normalized.T


def pairwise_euclidean(matrix: np.ndarray) -> np.ndarray:
    sq_norms = np.sum(matrix**2, axis=1, keepdims=True)
    return np.sqrt(np.maximum(sq_norms + sq_norms.T - 2.0 * (matrix @ matrix.T), 0.0))


def pairwise_manhattan(matrix: np.ndarray) -> np.ndarray:
    diff = matrix[:, np.newaxis, :] - matrix[np.newaxis, :, :]
    return np.sum(np.abs(diff), axis=2)


def pairwise_dot(matrix: np.ndarray) -> np.ndarray:
    return matrix @ matrix.T


METRIC_FUNCTIONS: dict[str, tuple[Callable, bool]] = {
    "cosine": (pairwise_cosine, False),
    "euclidean": (pairwise_euclidean, True),
    "manhattan": (pairwise_manhattan, True),
    "dot": (pairwise_dot, False),
}


def compute_pairwise(matrix: np.ndarray, metric: str = "cosine") -> np.ndarray:
    if metric not in METRIC_FUNCTIONS:
        raise ValueError(f"Unknown metric '{metric}'. Available: {list(METRIC_FUNCTIONS.keys())}")
    pairwise_fn, _ = METRIC_FUNCTIONS[metric]
    return pairwise_fn(matrix)
