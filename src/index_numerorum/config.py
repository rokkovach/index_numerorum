from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    id: str
    dim: int
    size_mb: int
    description: str
    shortcut: str


MODEL_REGISTRY: dict[str, ModelInfo] = {
    "mini": ModelInfo(
        id="all-MiniLM-L6-v2",
        dim=384,
        size_mb=80,
        description="Fast & lightweight, great for quick exploration",
        shortcut="mini",
    ),
    "bge-large": ModelInfo(
        id="BAAI/bge-large-en-v1.5",
        dim=1024,
        size_mb=1300,
        description="Top MTEB scores, excellent quality",
        shortcut="bge-large",
    ),
    "nomic": ModelInfo(
        id="nomic-ai/nomic-embed-text-v1.5",
        dim=768,
        size_mb=550,
        description="State-of-the-art, long context (8192 tokens)",
        shortcut="nomic",
    ),
    "gte": ModelInfo(
        id="Alibaba-NLP/gte-large-en-v1.5",
        dim=1024,
        size_mb=1300,
        description="Cutting-edge, top MTEB rankings",
        shortcut="gte",
    ),
    "e5": ModelInfo(
        id="intfloat/e5-large-v2",
        dim=1024,
        size_mb=1300,
        description="Strong performer, well-tested",
        shortcut="e5",
    ),
}

METRICS: dict[str, dict[str, object]] = {
    "cosine": {"sort_ascending": False, "range": "[-1, 1]"},
    "euclidean": {"sort_ascending": True, "range": "[0, inf)"},
    "manhattan": {"sort_ascending": True, "range": "[0, inf)"},
    "dot": {"sort_ascending": False, "range": "(-inf, inf)"},
}

DEFAULT_MODEL: str = "mini"
DEFAULT_METRIC: str = "cosine"
DEFAULT_TOP_K: int = 10
DEFAULT_BATCH_SIZE: int = 64
EMBEDDING_COLUMN_PREFIX: str = "_emb_"
COMPOSITE_KEY_COLUMN: str = "_composite_key"
METADATA_SHEET: str = "_metadata"
STATS_SHEET: str = "_stats"


def resolve_model(shortcut_or_id: str) -> ModelInfo:
    if shortcut_or_id in MODEL_REGISTRY:
        return MODEL_REGISTRY[shortcut_or_id]
    for model in MODEL_REGISTRY.values():
        if model.id == shortcut_or_id:
            return model
    shortcuts = ", ".join(sorted(MODEL_REGISTRY))
    raise ValueError(f"Unknown model '{shortcut_or_id}'. Available shortcuts: {shortcuts}")
