
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

from index_numerorum.config import METADATA_SHEET
from index_numerorum.io import (
    deserialize_embedding,
    get_column_embeddings,
    get_embedding_columns,
    read_xlsx,
    serialize_embedding,
    validate_columns,
    write_xlsx,
)


class TestReadXlsx:
    def test_valid_file(self, tmp_xlsx):
        df = read_xlsx(tmp_xlsx)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_xlsx(tmp_path / "nonexistent.xlsx")

    def test_non_xlsx_raises(self, tmp_path):
        path = tmp_path / "data.csv"
        path.write_text("a,b\n1,2")
        with pytest.raises(ValueError, match="Unsupported file extension"):
            read_xlsx(path)

    def test_empty_df_raises(self, tmp_path):
        path = tmp_path / "empty.xlsx"
        pd.DataFrame().to_excel(path, engine="openpyxl")
        with pytest.raises(ValueError, match="no data rows"):
            read_xlsx(path)


class TestWriteXlsx:
    def test_writes_successfully(self, tmp_path):
        df = pd.DataFrame({"A": [1, 2]})
        path = tmp_path / "out.xlsx"
        write_xlsx(df, path)
        assert path.exists()

    def test_file_exists_raises(self, tmp_path):
        df = pd.DataFrame({"A": [1]})
        path = tmp_path / "out.xlsx"
        path.touch()
        with pytest.raises(FileExistsError):
            write_xlsx(df, path)

    def test_overwrite_works(self, tmp_path):
        df = pd.DataFrame({"A": [1]})
        path = tmp_path / "out.xlsx"
        write_xlsx(df, path)
        df2 = pd.DataFrame({"B": [2]})
        write_xlsx(df2, path, overwrite=True)
        loaded = pd.read_excel(path, engine="openpyxl")
        assert "B" in loaded.columns

    def test_metadata_sheet_present(self, tmp_path):
        df = pd.DataFrame({"A": [1]})
        path = tmp_path / "out.xlsx"
        write_xlsx(df, path, metadata={"model": "mini"})
        import openpyxl

        wb = openpyxl.load_workbook(path)
        assert METADATA_SHEET in wb.sheetnames
        wb.close()


class TestValidateColumns:
    def test_all_valid(self, sample_df):
        result = validate_columns(sample_df, ["Name", "Category"])
        assert result == ["Name", "Category"]

    def test_missing_raises_with_suggestions(self, sample_df):
        with pytest.raises(ValueError, match="Missing columns"):
            validate_columns(sample_df, ["Name", "Nme"])

    def test_empty_list_ok(self, sample_df):
        result = validate_columns(sample_df, [])
        assert result == []


class TestSerialization:
    def test_roundtrip(self):
        vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        s = serialize_embedding(vec)
        recovered = deserialize_embedding(s)
        assert_allclose(recovered, vec, rtol=1e-5)

    def test_preserves_shape_and_dtype(self):
        vec = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32).flatten()
        s = serialize_embedding(vec)
        recovered = deserialize_embedding(s)
        assert recovered.shape == vec.shape
        assert recovered.dtype == np.float32


class TestGetEmbeddingColumns:
    def test_finds_emb_columns(self, sample_embedded_df):
        cols = get_embedding_columns(sample_embedded_df)
        assert "_emb_Name" in cols
        assert "_emb_Description" in cols

    def test_no_emb_columns(self, sample_df):
        assert get_embedding_columns(sample_df) == []


class TestGetColumnEmbeddings:
    def test_returns_array(self, sample_embedded_df):
        arr = get_column_embeddings(sample_embedded_df, "Name")
        assert arr.shape == (5, 4)

    def test_missing_column_raises(self, sample_df):
        with pytest.raises(ValueError, match="Embedding column"):
            get_column_embeddings(sample_df, "Name")
