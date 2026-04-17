import numpy as np
import pandas as pd
import pytest

from index_numerorum.io import serialize_embedding


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Name": ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"],
            "Category": ["A", "B", "A", "C", "B"],
            "Description": [
                "First item",
                "Second thing",
                "Third element",
                "Fourth piece",
                "Fifth object",
            ],
        }
    )


@pytest.fixture
def sample_vectors():
    base = np.eye(4, dtype=np.float32)
    extra = np.array([[0.5, 0.5, 0.5, 0.5]], dtype=np.float32)
    return np.vstack([base, extra])


@pytest.fixture
def sample_embedded_df(sample_df, sample_vectors):
    df = sample_df.copy()
    for col in ("Name", "Category", "Description"):
        df[f"_emb_{col}"] = [serialize_embedding(v) for v in sample_vectors]
    return df


@pytest.fixture
def tmp_xlsx(tmp_path, sample_df):
    path = tmp_path / "data.xlsx"
    sample_df.to_excel(path, index=False, engine="openpyxl")
    return path


@pytest.fixture
def tmp_embedded_xlsx(tmp_path, sample_embedded_df):
    path = tmp_path / "embedded_data.xlsx"
    sample_embedded_df.to_excel(path, index=False, engine="openpyxl")
    return path
