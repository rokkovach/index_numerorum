from __future__ import annotations

import contextlib
import io
import logging
import warnings

import numpy as np
import pandas as pd
from rich.console import Console
from sentence_transformers import SentenceTransformer

from .config import DEFAULT_BATCH_SIZE, EMBEDDING_COLUMN_PREFIX, ModelInfo, resolve_model
from .io import serialize_embedding

console = Console()


def load_model(model_info: ModelInfo) -> SentenceTransformer:
    buf = io.StringIO()
    transformers_logger = logging.getLogger("transformers")
    sentence_transformers_logger = logging.getLogger("sentence_transformers")
    hf_hub_logger = logging.getLogger("huggingface_hub")
    prev_levels = {
        "transformers": transformers_logger.level,
        "sentence_transformers": sentence_transformers_logger.level,
        "huggingface_hub": hf_hub_logger.level,
    }
    transformers_logger.setLevel(logging.CRITICAL)
    sentence_transformers_logger.setLevel(logging.CRITICAL)
    hf_hub_logger.setLevel(logging.CRITICAL)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            model = SentenceTransformer(model_info.id, device="cpu")
    transformers_logger.setLevel(prev_levels["transformers"])
    sentence_transformers_logger.setLevel(prev_levels["sentence_transformers"])
    hf_hub_logger.setLevel(prev_levels["huggingface_hub"])
    return model


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
            console.print(
                f"[dim]Skipping '{column}' (already embedded). Use --force to overwrite.[/dim]"
            )
            continue

        texts = df[column].astype(str).fillna("").tolist()
        embeddings = generate_embeddings(texts, model, batch_size=batch_size)
        df[embedding_col] = [serialize_embedding(e) for e in embeddings]

    return df


def get_model_info(shortcut_or_id: str) -> ModelInfo:
    model_info = resolve_model(shortcut_or_id)
    console.print(
        f"Using model: {model_info.id} (dimensions={model_info.dim}, size={model_info.size_mb}MB)"
    )
    return model_info
