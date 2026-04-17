import numpy as np
import pandas as pd

from .config import COMPOSITE_KEY_COLUMN


def concatenate_columns(df: pd.DataFrame, columns: list[str], separator: str = " ") -> pd.Series:
    selected = df[columns].fillna("")
    result = selected.apply(lambda row: separator.join(row.astype(str)), axis=1)
    result.name = COMPOSITE_KEY_COLUMN
    return result


def average_embeddings(
    embeddings: dict[str, np.ndarray],
    weights: dict[str, float] | None = None,
) -> np.ndarray:
    arrays = list(embeddings.values())
    if len(arrays) == 0:
        raise ValueError("embeddings must not be empty")

    n = arrays[0].shape[0]
    dim = arrays[0].shape[1]
    for name, arr in embeddings.items():
        if arr.shape[0] != n or arr.shape[1] != dim:
            raise ValueError(f"Array for '{name}' has shape {arr.shape}, expected ({n}, {dim})")

    if weights is None:
        return np.mean(arrays, axis=0)

    total = sum(weights.values())
    normalized_weights = {k: v / total for k, v in weights.items()}
    stacked = np.stack([normalized_weights[name] * arr for name, arr in embeddings.items()], axis=0)
    return np.sum(stacked, axis=0)


def parse_weighted_columns(
    columns: list[str],
) -> tuple[list[str], dict[str, float]]:
    column_names: list[str] = []
    weights: dict[str, float] = {}

    for col in columns:
        if ":" in col:
            name, weight_str = col.rsplit(":", 1)
            try:
                w = float(weight_str)
            except ValueError:
                raise ValueError(f"Invalid weight '{weight_str}' for column '{name}'") from None
            if w < 0:
                raise ValueError(f"Negative weight {w} for column '{name}'")
            column_names.append(name)
            weights[name] = w
        else:
            column_names.append(col)
            weights[col] = 1.0

    return column_names, weights


def build_composite_key(
    df: pd.DataFrame,
    columns: list[str],
    strategy: str = "concatenate",
    separator: str = " ",
) -> pd.Series:
    valid_strategies = ("concatenate", "average", "weighted-average")
    if strategy not in valid_strategies:
        raise ValueError(
            f"Unknown strategy '{strategy}'. Valid strategies: {list(valid_strategies)}"
        )

    return concatenate_columns(df, columns, separator=separator)
