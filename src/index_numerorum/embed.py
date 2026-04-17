from __future__ import annotations

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from .config import DEFAULT_BATCH_SIZE, EMBEDDING_COLUMN_PREFIX, ModelInfo, resolve_model
from .io import serialize_embedding


def load_model(model_info: ModelInfo) -> SentenceTransformer:
    return SentenceTransformer(model_info.id, device="cpu")


def generate_embeddings(
    texts: list[str],
    model: SentenceTransformer,
    batch_size: int = 64,
    progress_callback: callable | None = None,
) -> np.ndarray:
    if progress_callback is not None:
        progress_callback(0, len(texts))

    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
    )

    if progress_callback is not None:
        progress_callback(len(texts), len(texts))

    return embeddings


def embed_columns(
    df: pd.DataFrame,
    columns: list[str],
    model: SentenceTransformer,
    batch_size: int = DEFAULT_BATCH_SIZE,
    force: bool = False,
) -> pd.DataFrame:
    for column in columns:
        embedding_col = f"{EMBEDDING_COLUMN_PREFIX}{column}"
        if embedding_col in df.columns and not force:
            print(
                f"Embedding column '{embedding_col}' already exists. "
                "Skipping (use force=True to overwrite)."
            )
            continue

        texts = df[column].astype(str).fillna("").tolist()
        embeddings = generate_embeddings(texts, model, batch_size=batch_size)
        df[embedding_col] = [serialize_embedding(e) for e in embeddings]

    return df


def get_model_info(shortcut_or_id: str) -> ModelInfo:
    model_info = resolve_model(shortcut_or_id)
    print(
        f"Using model: {model_info.id} (dimensions={model_info.dim}, size={model_info.size_mb}MB)"
    )
    return model_info
