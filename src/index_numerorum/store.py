from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import DEFAULT_DECIMALS
from .similarity import pairwise_cosine


def _atomic_write_json(path: Path, data: object) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


try:
    import zvec
except ImportError:
    zvec = None


def _require_zvec() -> None:
    if zvec is None:
        raise ImportError("zvec required. pip install index-numerorum[vec]")


def _compute_groups(pairs: list[tuple[str, str]]) -> dict[str, int]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        if x not in parent:
            parent[x] = x
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in pairs:
        union(a, b)

    roots: dict[str, int] = {}
    counter = 1
    result: dict[str, int] = {}
    for a, b in pairs:
        for k in (a, b):
            if k not in result:
                root = find(k)
                if root not in roots:
                    roots[root] = counter
                    counter += 1
                result[k] = roots[root]
    return result


class VectorStore:
    EMB_FIELD: str = "embedding"

    def __init__(self, path: Path, read_only: bool = False) -> None:
        _require_zvec()
        self.path: Path = Path(path)
        option = zvec.CollectionOption(read_only=read_only, enable_mmap=True)
        self._collection = zvec.open(path=str(self.path), option=option)
        meta_path = self.path / "_meta.json"
        if meta_path.exists():
            self._schema_meta: dict = json.loads(meta_path.read_text())
        else:
            self._schema_meta = {}
        keys_path = self.path / "_keys.json"
        if keys_path.exists():
            self._keys: list[str] = json.loads(keys_path.read_text())
        else:
            self._keys = []
        emb_path = self.path / "_embeddings.npy"
        if emb_path.exists():
            self._embeddings: np.ndarray = np.load(str(emb_path), allow_pickle=False)
        else:
            dims = self._schema_meta.get("dimensions", 0)
            self._embeddings = np.empty((0, dims), dtype=np.float32)

    @classmethod
    def create(
        cls,
        path: Path,
        model_id: str,
        dimensions: int,
        key_column: str,
        embed_columns: list[str],
    ) -> VectorStore:
        _require_zvec()
        path = Path(path)
        schema = zvec.CollectionSchema(
            name="index_numerorum",
            vectors=zvec.VectorSchema(
                cls.EMB_FIELD,
                zvec.DataType.VECTOR_FP32,
                dimensions,
                index_param=zvec.HnswIndexParam(metric_type=zvec.MetricType.COSINE),
            ),
            fields=[
                zvec.FieldSchema("_key", zvec.DataType.STRING),
                zvec.FieldSchema("_row_data", zvec.DataType.STRING),
            ],
        )
        collection = zvec.create_and_open(path=str(path), schema=schema)
        meta = {
            "model_id": model_id,
            "dimensions": dimensions,
            "key_column": key_column,
            "embed_columns": embed_columns,
        }
        _atomic_write_json(path / "_meta.json", meta)
        _atomic_write_json(path / "_keys.json", [])
        np.save(str(path / "_embeddings"), np.empty((0, dimensions), dtype=np.float32))
        store = cls.__new__(cls)
        store.path = path
        store._collection = collection
        store._schema_meta = meta
        store._keys = []
        store._embeddings = np.empty((0, dimensions), dtype=np.float32)
        return store

    @property
    def model_id(self) -> str:
        return self._schema_meta.get("model_id", "")

    @property
    def dimensions(self) -> int:
        return self._schema_meta.get("dimensions", 0)

    @property
    def key_column(self) -> str:
        return self._schema_meta.get("key_column", "")

    @property
    def embed_columns(self) -> list[str]:
        return self._schema_meta.get("embed_columns", [])

    @property
    def row_count(self) -> int:
        return len(self._keys)

    def insert_rows(
        self,
        df: pd.DataFrame,
        embeddings: np.ndarray,
        key_values: list[str],
    ) -> int:
        docs = []
        for i in range(len(df)):
            row_data = json.dumps(df.iloc[i].to_dict(), default=str)
            docs.append(
                zvec.Doc(
                    id=str(key_values[i]),
                    vectors={self.EMB_FIELD: embeddings[i].tolist()},
                    fields={
                        "_key": str(key_values[i]),
                        "_row_data": row_data,
                    },
                )
            )
        self._collection.insert(docs)
        self._keys.extend(key_values)
        _atomic_write_json(self.path / "_keys.json", self._keys)
        if self._embeddings.shape[0] == 0:
            self._embeddings = np.array(embeddings, dtype=np.float32)
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings]).astype(np.float32)
        tmp = self.path / "_embeddings.tmp"
        np.save(str(tmp), self._embeddings)
        (self.path / "_embeddings.tmp.npy").replace(self.path / "_embeddings.npy")
        return len(docs)

    def query(
        self, vector: list[float], top_k: int = 10, decimals: int = DEFAULT_DECIMALS
    ) -> list[dict]:
        results = self._collection.query(
            vectors=zvec.VectorQuery(self.EMB_FIELD, vector=vector), topk=top_k
        )
        output: list[dict] = []
        for r in results:
            fields = r.fields or {}
            row_data = json.loads(fields.get("_row_data", "{}"))
            sim = 1.0 - (r.score if r.score is not None else 1.0)
            output.append(
                {
                    "id": r.id,
                    "similarity": round(sim, decimals),
                    "fields": row_data,
                }
            )
        return output

    def query_by_text(self, text: str, sentence_model: object, top_k: int = 10) -> list[dict]:
        vec = sentence_model.encode([text], show_progress_bar=False)[0].tolist()
        return self.query(vec, top_k)

    def match_all(self, threshold: float, decimals: int = DEFAULT_DECIMALS) -> pd.DataFrame:
        if self._embeddings.shape[0] < 2:
            return pd.DataFrame(columns=["query_key", "match_key", "similarity", "group_id"])
        sim_matrix = pairwise_cosine(self._embeddings)
        matches: list[dict] = []
        seen: set[tuple[str, str]] = set()
        n = len(self._keys)
        for i in range(n):
            for j in range(i + 1, n):
                sim = float(sim_matrix[i, j])
                if sim >= threshold:
                    a, b = self._keys[i], self._keys[j]
                    pair = (min(a, b), max(a, b))
                    if pair not in seen:
                        seen.add(pair)
                        matches.append(
                            {
                                "query_key": a,
                                "match_key": b,
                                "similarity": round(sim, decimals),
                            }
                        )
        if not matches:
            return pd.DataFrame(columns=["query_key", "match_key", "similarity", "group_id"])
        df = pd.DataFrame(matches)
        pairs = list(zip(df["query_key"].tolist(), df["match_key"].tolist(), strict=False))
        group_map = _compute_groups(pairs)
        all_keys = set(df["query_key"].tolist() + df["match_key"].tolist())
        group_map = {k: v for k, v in group_map.items() if k in all_keys}
        df["group_id"] = df["query_key"].map(group_map)
        return df.sort_values(["group_id", "similarity"], ascending=[True, False]).reset_index(
            drop=True
        )

    def annotate(
        self, input_df: pd.DataFrame, threshold: float, decimals: int = DEFAULT_DECIMALS
    ) -> pd.DataFrame:
        matches = self.match_all(threshold, decimals=decimals)
        result = input_df.copy()
        result["_match_count"] = 0
        result["_match_ids"] = [list() for _ in range(len(result))]
        result["_best_match_id"] = None
        result["_best_match_score"] = np.nan
        result["_group_id"] = 0

        if matches.empty:
            return result

        by_query: dict[str, list[dict]] = {}
        by_match: dict[str, list[dict]] = {}
        for rec in matches.to_dict("records"):
            by_query.setdefault(rec["query_key"], []).append(rec)
            by_match.setdefault(rec["match_key"], []).append(rec)

        groups_by_query = dict(
            zip(
                matches["query_key"].tolist(),
                matches["group_id"].tolist(),
                strict=False,
            )
        )
        groups_by_match = dict(
            zip(
                matches["match_key"].tolist(),
                matches["group_id"].tolist(),
                strict=False,
            )
        )

        key_col = self.key_column
        for idx in result.index:
            key = str(result.at[idx, key_col])
            related = by_query.get(key, []) + by_match.get(key, [])
            if not related:
                continue
            match_ids = []
            best_id = None
            best_score = -1.0
            for r in related:
                other = r["match_key"] if r["query_key"] == key else r["query_key"]
                match_ids.append(other)
                if r["similarity"] > best_score:
                    best_score = r["similarity"]
                    best_id = other
            result.at[idx, "_match_count"] = len(match_ids)
            result.at[idx, "_match_ids"] = match_ids
            result.at[idx, "_best_match_id"] = best_id
            result.at[idx, "_best_match_score"] = best_score
            result.at[idx, "_group_id"] = groups_by_query.get(key, groups_by_match.get(key, 0))

        return result

    def info(self) -> dict:
        size = sum(f.stat().st_size for f in self.path.rglob("*") if f.is_file())
        return {
            "path": str(self.path),
            "row_count": self.row_count,
            "model_id": self.model_id,
            "dimensions": self.dimensions,
            "key_column": self.key_column,
            "embed_columns": self.embed_columns,
            "size_on_disk": size,
        }
