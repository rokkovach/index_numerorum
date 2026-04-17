import pandas as pd

from index_numerorum.wizard import (
    _classify_dtype,
    inspect_columns,
)


class TestClassifyDtype:
    def test_numeric_column(self):
        series = pd.Series([1, 2, 3, 4, 5])
        assert _classify_dtype(series) == "numeric"

    def test_short_text_category(self):
        series = pd.Series(["red", "blue", "red", "green", "blue", "red", "red", "blue"])
        assert _classify_dtype(series) == "category"

    def test_long_text(self):
        series = pd.Series(
            [
                "This is a very long text that goes on and on and on about something",
                "Another very long description that contains quite a few words here",
                "Yet another long text description with plenty of characters in it",
            ]
        )
        assert _classify_dtype(series) == "text"

    def test_mixed_empty_after_dropna(self):
        series = pd.Series([None, None])
        assert _classify_dtype(series) == "mixed"


class TestInspectColumns:
    def test_returns_column_info(self):
        df = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Alice", "Bob", "Charlie"],
                "Score": [95.5, 87.3, 91.0],
                "Address": ["123 Main St", "456 Oak Ave", "789 Pine Rd"],
                "Company": ["Acme Corp", "Beta Inc", "Gamma LLC"],
            }
        )
        columns = inspect_columns(df)
        assert len(columns) == 5

        id_col = columns[0]
        assert id_col.name == "ID"
        assert id_col.is_likely_key is True
        assert id_col.null_count == 0

    def test_suggests_address_model(self):
        df = pd.DataFrame(
            {
                "Address": ["123 Main St", "456 Oak Ave"],
                "Name": ["Alice", "Bob"],
            }
        )
        columns = inspect_columns(df)
        address_col = columns[0]
        assert address_col.suggested_model == "address"

    def test_suggests_entity_model(self):
        df = pd.DataFrame(
            {
                "Company": ["Acme Corp", "Beta Inc"],
                "Name": ["Alice", "Bob"],
            }
        )
        columns = inspect_columns(df)
        company_col = columns[0]
        assert company_col.suggested_model == "entity"

    def test_suggests_mini_default(self):
        df = pd.DataFrame(
            {
                "Name": ["Alice", "Bob"],
            }
        )
        columns = inspect_columns(df)
        assert columns[0].suggested_model == "mini"

    def test_detects_nulls(self):
        df = pd.DataFrame(
            {
                "ID": [1, 2, None],
                "Name": ["A", "B", "C"],
            }
        )
        columns = inspect_columns(df)
        assert columns[0].null_count == 1
        assert columns[0].is_likely_key is False

    def test_column_indices_are_1_based(self):
        df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
        columns = inspect_columns(df)
        assert [c.index for c in columns] == [1, 2, 3]
