import numpy as np
import pandas as pd

from .config import DEFAULT_TOP_K
from .io import get_column_embeddings
from .similarity import METRIC_FUNCTIONS, compute_pairwise


def find_neighbors(
    df: pd.DataFrame,
    key_column: str,
    metric: str = "cosine",
    top_k: int = DEFAULT_TOP_K,
) -> pd.DataFrame:
    embeddings = get_column_embeddings(df, key_column)
    pairwise = compute_pairwise(embeddings, metric=metric)
    _, ascending = METRIC_FUNCTIONS[metric]
    keys = df[key_column].astype(str).tolist()
    rows: list[dict] = []
    for i in range(len(df)):
        scores = pairwise[i].copy()
        scores[i] = np.inf if ascending else -np.inf
        order = np.argsort(scores) if ascending else np.argsort(-scores)
        for rank, j in enumerate(order[:top_k], start=1):
            rows.append(
                {
                    "query_key": keys[i],
                    "neighbor_key": keys[j],
                    "rank": rank,
                    "score": pairwise[i, j],
                }
            )
    return pd.DataFrame(rows)


def compare_items(
    df: pd.DataFrame,
    key_column: str,
    item_a: str,
    item_b: str,
) -> dict[str, float]:
    from .similarity import (
        cosine_similarity,
        dot_product,
        euclidean_distance,
        manhattan_distance,
    )

    embeddings = get_column_embeddings(df, key_column)
    keys = df[key_column].astype(str).tolist()

    try:
        idx_a = keys.index(item_a)
    except ValueError:
        similar = [k for k in keys if item_a.lower() in k.lower() or k.lower() in item_a.lower()][
            :5
        ]
        raise ValueError(
            f"'{item_a}' not found in column '{key_column}'. Similar values: {similar}"
        ) from None

    try:
        idx_b = keys.index(item_b)
    except ValueError:
        similar = [k for k in keys if item_b.lower() in k.lower() or k.lower() in item_b.lower()][
            :5
        ]
        raise ValueError(
            f"'{item_b}' not found in column '{key_column}'. Similar values: {similar}"
        ) from None

    vec_a = embeddings[idx_a]
    vec_b = embeddings[idx_b]

    return {
        "cosine": float(cosine_similarity(vec_a, vec_b)),
        "euclidean": float(euclidean_distance(vec_a, vec_b)),
        "manhattan": float(manhattan_distance(vec_a, vec_b)),
        "dot": float(dot_product(vec_a, vec_b)),
    }
