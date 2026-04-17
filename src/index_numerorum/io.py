from __future__ import annotations

import difflib
import json
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

from .config import EMBEDDING_COLUMN_PREFIX, METADATA_SHEET


def read_xlsx(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() != ".xlsx":
        raise ValueError(f"Unsupported file extension '{path.suffix}'. Valid formats: .xlsx")
    df = pd.read_excel(path, engine="openpyxl")
    if df.empty:
        raise ValueError("The file contains no data rows.")
    return df


def write_xlsx(
    df: pd.DataFrame,
    path: Path,
    metadata: dict[str, str] | None = None,
    overwrite: bool = False,
) -> None:
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {path}. Use overwrite=True to replace it.")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="data", index=False)
        if metadata:
            meta_df = pd.DataFrame(
                {"Parameter": list(metadata.keys()), "Value": list(metadata.values())}
            )
            meta_df.to_excel(writer, sheet_name=METADATA_SHEET, index=False)
    wb = openpyxl.load_workbook(path)
    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
    wb.save(path)
    wb.close()


def column_exists(df: pd.DataFrame, column: str) -> bool:
    return column in df.columns


def validate_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        suggestions: dict[str, list[str]] = {}
        for col in missing:
            suggestions[col] = difflib.get_close_matches(col, df.columns)
        raise ValueError(
            f"Missing columns: {missing}\n"
            f"Close matches: {suggestions}\n"
            f"Available columns: {list(df.columns)}"
        )
    return columns


def serialize_embedding(vec: np.ndarray) -> str:
    return json.dumps(vec.tolist())


def deserialize_embedding(s: str) -> np.ndarray:
    return np.array(json.loads(s), dtype=np.float32)


def get_embedding_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(EMBEDDING_COLUMN_PREFIX)]


def get_column_embeddings(df: pd.DataFrame, column: str) -> np.ndarray:
    emb_col = f"{EMBEDDING_COLUMN_PREFIX}{column}"
    if emb_col not in df.columns:
        raise ValueError(
            f"Embedding column '{emb_col}' not found. Run embed first to generate embeddings."
        )
    return np.stack(df[emb_col].apply(deserialize_embedding).values)
